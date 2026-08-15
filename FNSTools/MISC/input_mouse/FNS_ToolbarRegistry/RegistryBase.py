

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

from TDStoreTools import StorageManager

class RegistryBase:
	EXT_NAME = 'RegistryBase'
	SHORTCUT = None
	REGISTRY_NAME = 'Registry'
	HOST_PAGE_NAME = 'Registration'

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		# BEFORE CustomParHelper touches the pars: a dangling BIND (tool
		# Registry page gone) raises on any access and would kill init
		self._repairDanglingHostBinds()
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self._preInit()
		storedItems = [
			{'name': 'PaneRegistry', 'default': {}, 'property': True, 'readOnly': True},
			{'name': 'HostCanonical', 'default': '', 'property': True, 'readOnly': True},
			{'name': 'GroupVisibility', 'default': {}, 'property': True, 'readOnly': True},
		]
		self.stored = StorageManager(self, ownerComp, storedItems)
		self._pane_sync_queued = False
		self._registry_watch_armed = False
		self.postInit()

	def onDestroyTD(self):
		"""Unregister host entry when this registry COMP is deleted.

		The /sys global registry does not own a host entry; it only stops
		arming further watch ticks (in-flight run() no-ops on invalid owner).
		"""
		self._registry_watch_armed = False
		if self._is_sys_global():
			return
		try:
			# onDestroyTD ALSO fires on extension REINIT -- removing the tool
			# page then would orphan the host's bound Registration pars and
			# kill the next init. Only clean up on real COMP destruction.
			if not self.ownerComp.valid:
				self._removeToolRegistryPage()
		except Exception as e:
			debug(f'{self.REGISTRY_NAME} onDestroyTD page cleanup: {e}')
		try:
			self._clearHostRegistration()
		except Exception as e:
			debug(f'{self.REGISTRY_NAME} onDestroyTD: {e}')

	# --- tool-facing 'Registry' page (bound proxy pars on the parent tool) ---

	TOOL_PAGE_NAME = 'Registry'
	TOOL_PAGE_PREFIX = None      # subclass sets a short unique prefix, e.g. 'Tb'
	TOOL_PAGE_LABEL = None       # section header label; defaults to REGISTRY_NAME
	TOOL_PAGE_PARS = ()          # host Registration par names to proxy

	# In-project host cloning. Subclasses set the guarded clone expression
	# hosts carry; masters are depth-1 packages of the toolkit root, so it
	# resolves through the root's FNS shortcut --
	#   CLONE_EXPR = "op.FNS.op('XRegistry') if hasattr(op, 'FNS') else None"
	# With it set, the base provides _healHostClones and StampHost.
	CLONE_EXPR = None

	def _ensureToolRegistryPage(self):
		"""Standardized 'Registry' page on the host's PARENT tool: key
		Registration pars mirrored onto the tool, so registration is
		configured on the tool itself without opening the host. The TOOL
		pars are the bind MASTERS -- they hold and persist the values with
		the tool -- and the host's Registration pars BIND to them, following
		whatever the tool ships with. Prefixed par names let multiple
		registries (toolbar + navbar) share the one page. Created
		programmatically on every successful registration -- the whole fleet
		standardizes itself, and drop-to-register stamps inherit it with
		zero per-tool work."""
		if not self.TOOL_PAGE_PREFIX or not self.TOOL_PAGE_PARS:
			return
		if self._is_sys_global() or self._isUnderSysOrUi():
			return
		# Opt-out for shippers: Promotepars off = no proxy page on the tool
		# (and an existing section is withdrawn). Missing par = on.
		if not self._parBool('Promotepars', True):
			self._removeToolRegistryPage()
			return
		tool = self.ownerComp.parent()
		if tool is None or not tool.valid or tool.path == '/':
			return
		page = next((pg for pg in tool.customPages if pg.name == self.TOOL_PAGE_NAME), None)
		if page is None:
			page = tool.appendCustomPage(self.TOOL_PAGE_NAME)
		self._orderToolRegistryPage(tool)
		head_name = self.TOOL_PAGE_PREFIX + 'section'
		hpar = getattr(tool.par, head_name, None)
		if hpar is None:
			page.appendHeader(head_name,
							  label=self.TOOL_PAGE_LABEL or self.REGISTRY_NAME)
		else:
			self._reclaimToolPar(hpar, page)
		appenders = {'Toggle': page.appendToggle, 'Pulse': page.appendPulse,
					 'Str': page.appendStr, 'Int': page.appendInt,
					 'Float': page.appendFloat, 'Menu': page.appendMenu}
		for name in self.TOOL_PAGE_PARS:
			src = getattr(self.ownerComp.par, name, None)
			if src is None:
				continue
			tname = self.TOOL_PAGE_PREFIX + name.lower()
			# host value BEFORE any bind changes -- it seeds a fresh tool par
			try:
				cur = src.eval() if src.style != 'Pulse' else None
			except Exception:
				cur = None
			tpar = getattr(tool.par, tname, None)
			if tpar is not None:
				self._reclaimToolPar(tpar, page)
			if tpar is None:
				append = appenders.get(src.style)
				if append is None:
					continue
				try:
					tpar = append(tname, label=src.label)[0]
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: tool page par {tname}: {e}')
					continue
				tpar.help = src.help
				if src.style == 'Menu':
					tpar.menuNames = src.menuNames
					tpar.menuLabels = src.menuLabels
				if src.style in ('Int', 'Float'):
					tpar.normMin, tpar.normMax = src.normMin, src.normMax
				if src.readOnly:
					tpar.readOnly = True
				try:
					tpar.default = src.default
				except Exception:
					pass
				if cur is not None:
					tpar.val = cur
			elif tpar.mode == ParMode.BIND:
				# migrate from the earlier (reversed) direction: the tool par
				# becomes the master, seeded with the live value
				try:
					tpar.mode = ParMode.CONSTANT
					if cur is not None:
						tpar.val = cur
				except Exception:
					pass
			# keep presentation in sync with the host par -- labels were once
			# copied only at creation, so a corrected host label never reached
			# the tools that had already been promoted
			try:
				if tpar.label != src.label:
					tpar.label = src.label
				if tpar.help != src.help:
					tpar.help = src.help
			except Exception:
				pass
			# the HOST par follows the tool par
			try:
				expr = f"parent().par.{tname}"
				if src.bindExpr != expr or src.mode != ParMode.BIND:
					src.bindExpr = expr
					src.mode = ParMode.BIND
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: host bind {name}: {e}')
		self._orderToolSection(tool)

	def _reclaimToolPar(self, tpar, page):
		"""Move a section par back onto the Registry page. TD relocates a
		destroyed page's pars onto another page instead of destroying them,
		so after any page churn our pars can be stranded on About/Version
		Ctrl -- ensure() heals that instead of skipping them as 'existing'."""
		try:
			if tpar.page != page:
				tpar.page = page
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: reclaim {tpar.name}: {e}')

	def _sectionParNames(self):
		return ([self.TOOL_PAGE_PREFIX + 'section'] +
				[self.TOOL_PAGE_PREFIX + n.lower() for n in self.TOOL_PAGE_PARS])

	def _orderToolSection(self, tool):
		"""Keep this registry's section contiguous and in declared order on
		the Registry page (reclaimed strays land wherever TD appends them)."""
		try:
			ours = [getattr(tool.par, n, None) for n in self._sectionParNames()]
			ours = [p for p in ours if p is not None]
			orders = [p.order for p in ours]
			if len(ours) < 2 or orders == sorted(orders):
				return
			base = min(orders)
			for i, p in enumerate(ours):
				p.order = base + i * 0.001
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: section ordering: {e}')

	# meta pages the Registry page must come BEFORE
	TOOL_PAGE_BEFORE = ('About', 'Common', 'Version Ctrl')

	def _orderToolRegistryPage(self, tool):
		"""Keep the Registry page ahead of the meta pages: the tool's own
		pages first, then Registry, then About / Common / Version Ctrl."""
		try:
			names = [pg.name for pg in tool.customPages]
			if self.TOOL_PAGE_NAME not in names:
				return
			metas = [n for n in names if n in self.TOOL_PAGE_BEFORE]
			rest = [n for n in names
					if n != self.TOOL_PAGE_NAME and n not in self.TOOL_PAGE_BEFORE]
			desired = rest + [self.TOOL_PAGE_NAME] + metas
			if names != desired and hasattr(tool, 'sortCustomPages'):
				tool.sortCustomPages(*desired)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: Registry page ordering: {e}')

	def onParPromotepars(self, _par, _val, _prev):
		"""Toggle the tool-facing Registry page on the fly. Turning it off
		unbinds the host pars first (their masters are about to go away)."""
		ext = self._hostExtFromPar(_par)
		if ext._parBool('Promotepars', True):
			ext._ensureToolRegistryPage()
		else:
			for pg in ext.ownerComp.customPages:
				if pg.name != ext.HOST_PAGE_NAME:
					continue
				for p in pg.pars:
					try:
						if p.mode == ParMode.BIND:
							p.mode = ParMode.CONSTANT
					except Exception:
						pass
			ext._removeToolRegistryPage()

	def _repairDanglingHostBinds(self):
		"""Registration pars bound to a tool Registry page that no longer
		exists (page removed, host copied somewhere without one) raise on
		every eval and would kill extension init. Fall back to CONSTANT --
		the par's constant slot still holds its pre-bind value."""
		page = next((pg for pg in self.ownerComp.customPages
					 if pg.name == self.HOST_PAGE_NAME), None)
		if page is None:
			return
		for p in page.pars:
			try:
				if p.mode != ParMode.BIND:
					continue
				master = None
				try:
					master = p.bindMaster
				except Exception:
					master = None
				if master is None:
					p.mode = ParMode.CONSTANT
					continue
				if p.style != 'Pulse':
					p.eval()
			except Exception:
				try:
					p.mode = ParMode.CONSTANT
				except Exception:
					pass

	def _removeToolRegistryPage(self):
		"""Drop this registry's section from the tool's Registry page (and
		the page itself once no section remains)."""
		if not self.TOOL_PAGE_PREFIX:
			return
		tool = self.ownerComp.parent()
		if tool is None or not tool.valid:
			return
		# destroy by exact name wherever the pars sit -- page churn can have
		# stranded them on another page (TD relocates, never destroys, the
		# pars of a destroyed page)
		for pname in self._sectionParNames():
			p = getattr(tool.par, pname, None)
			if p is not None:
				try:
					p.destroy()
				except Exception:
					pass
		for page in list(tool.customPages):
			if page.name == self.TOOL_PAGE_NAME and not list(page.pars):
				try:
					page.destroy()
				except Exception:
					pass

	# --- surface hooks (overridden by surface-specific subclasses) ---

	def _preInit(self):
		pass

	def _syncSurface(self, attempts=40):
		pass

	def _sanitizeStoredRegistry(self):
		pass

	def _ensureSelectionExecuteRole(self):
		pass

	def _resyncRegisteredMenuRows(self):
		self._syncSurface()

	def _normalize_action(self, value):
		return value

	def postInit(self):
		if self._is_sys_global():
			if self.ownerComp.fetch('post_update', False):
				for name, info in self.ownerComp.fetch('PaneRegistry', {}).items():
					if name not in self.stored['PaneRegistry']:
						self.stored['PaneRegistry'][name] = info
				self.ownerComp.unstore('post_update')
			self._sanitizeStoredRegistry()
			self.ownerComp.par.opshortcut = self.SHORTCUT
			self._neutralizeHostParameters()
			self._syncSurface()
			self._armRegistryWatch()
			self._ensureSelectionExecuteRole()
			return

		self._sanitizeStoredRegistry()
		self._installGlobalRegistry()
		self._release_shipped_shortcut()
		self._applyHostRegistration()
		self._ensureSelectionExecuteRole()

	def _neutralizeHostParameters(self):
		"""The global /sys instance is pure infrastructure -- host-publisher
		parameters (Registration page) are meaningless on it. Keep the page
		(copies stay structurally identical to hosts) but reset every par to
		its inert default so no stale host state rides on the global."""
		for page in list(self.ownerComp.customPages):
			if page.name != self.HOST_PAGE_NAME:
				continue
			for p in page.pars:
				try:
					if p.style == 'Pulse':
						continue
					# a promoted host copy may carry Registration pars BOUND
					# to a tool's Registry page that does not exist up here
					if p.mode != ParMode.CONSTANT:
						p.mode = ParMode.CONSTANT
					p.val = p.default
				except Exception:
					pass
		self._setRegStatus('Idle (global)')

	# --- host auto-registration (Registration page) ---

	def _isUnderSysOrUi(self):
		path = self.ownerComp.path
		return path == '/sys' or path.startswith('/sys/') or path == '/ui' or path.startswith('/ui/')

	def _hostComp(self):
		"""COMP to register as the pane owner. Defaults to parent (..)."""
		comp_par = getattr(self.ownerComp.par, 'Comp', None)
		if comp_par is None:
			# Back-compat with older Panel parameter name.
			comp_par = getattr(self.ownerComp.par, 'Panel', None)
		if comp_par is not None:
			comp = comp_par.eval()
			if comp:
				return comp
		parent = self.ownerComp.parent()
		if parent and parent.path not in ('/',):
			return parent
		return None

	def _isAutoRegister(self):
		if hasattr(self.ownerComp.par, 'Autoregister'):
			return bool(self.ownerComp.par.Autoregister.eval())
		return False

	def _parBool(self, name, default=False):
		if hasattr(self.ownerComp.par, name):
			return bool(getattr(self.ownerComp.par, name).eval())
		return default

	def _hostRecallFlags(self):
		"""Orthogonal recall flags from the Registration page."""
		return {
			'set_owner': self._parBool('Setowner', True),
			'change_type': self._parBool('Changetype', True),
			'maximize': self._parBool('Maximize', False),
			'tear_away': self._parBool('Tearaway', False),
			'float': self._parBool('Float', False),
			'open_parameters': self._parBool('Openparameters', False),
		}

	def _hostCallbackDat(self):
		if hasattr(self.ownerComp.par, 'Callback'):
			cb = self.ownerComp.par.Callback.eval()
			if cb is not None:
				return cb
		return None

	def _hostCanonicalName(self):
		name = ''
		if hasattr(self.ownerComp.par, 'Canonicalname'):
			name = str(self.ownerComp.par.Canonicalname.eval() or '').strip()
		if name:
			return name
		host = self._hostComp()
		return host.name if host else ''

	def _registryApi(self):
		"""Live registry that owns the panebar menu (prefer global /sys copy)."""
		if self._is_sys_global():
			return self
		global_reg = self._global_registry()
		if global_reg and global_reg.valid and global_reg.extensionsReady:
			if hasattr(global_reg.ext, self.EXT_NAME):
				return getattr(global_reg.ext, self.EXT_NAME)
		return self

	def _setRegStatus(self, status):
		if hasattr(self.ownerComp.par, 'Regstatus'):
			self.ownerComp.par.Regstatus.val = status

	def _hostMenuOrder(self):
		"""Read Registration Menuorder par; None means default append."""
		if not hasattr(self.ownerComp.par, 'Menuorder'):
			return None
		return self._normalizeMenuOrder(self.ownerComp.par.Menuorder.eval())

	def _applyHostRegistration(self, force=False):
		"""Register or unregister the host COMP based on Auto-register + location.

		force=True (Register pulse) registers even when Auto-register is off.
		"""
		if self._is_sys_global():
			# Global /sys copy is infrastructure — never auto-registers a host.
			self._setRegStatus('Idle (global)')
			return

		if self._isUnderSysOrUi():
			self._clearHostRegistration()
			self._setRegStatus('Skipped (/sys or /ui)')
			return

		if not force and not self._isAutoRegister():
			self._clearHostRegistration()
			self._setRegStatus('Idle')
			return

		host = self._hostComp()
		if not host:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus('Error: no host COMP')
			return

		canonical = self._hostCanonicalName()
		if not canonical:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus('Error: empty canonical name')
			return

		pane_type = self.ownerComp.par.Panetype.eval() if hasattr(self.ownerComp.par, 'Panetype') else 'PANEL'
		flags = self._hostRecallFlags()
		callback = self._hostCallbackDat()

		err = self._validateHostForPaneType(host, pane_type)
		if err:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus(f'Error: {err}')
			return

		prev = self.stored['HostCanonical']
		api = self._registryApi()
		# Only drop prev if THIS registry owns that global entry.
		# Copied host templates inherit HostCanonical from the source and must
		# not unregister the template's live menu name (e.g. project1 -> button1).
		if prev and prev != canonical:
			self._unregisterOwnedMenuName(prev, api=api)

		api.RegisterPanel(
			host, canonical, pane_type=pane_type,
			set_owner=flags['set_owner'],
			change_type=flags['change_type'],
			maximize=flags['maximize'],
			tear_away=flags['tear_away'],
			float_pane=flags['float'],
			open_parameters=flags['open_parameters'],
			callback=callback,
			source_registry=self.ownerComp,
			menu_order=self._hostMenuOrder(),
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {host.path}')
		self._ensureToolRegistryPage()

	def _ownsGlobalMenuName(self, canonical, api=None):
		"""True if the global menu entry for canonical was published by this registry."""
		if not canonical:
			return False
		api = api or self._registryApi()
		if api is None:
			return False
		try:
			info = api.stored['PaneRegistry'].get(canonical)
		except Exception:
			info = None
		if not info:
			return False
		src_id = info.get('source_registry_id')
		if src_id is not None:
			try:
				if int(src_id) == int(self.ownerComp.id):
					return True
			except Exception:
				pass
		return info.get('source_registry') == self.ownerComp.path

	def _unregisterOwnedMenuName(self, canonical, api=None):
		"""Unregister a menu name only when this host registry owns it."""
		if not canonical:
			return False
		api = api or self._registryApi()
		if api is None:
			return False
		if not self._ownsGlobalMenuName(canonical, api=api):
			return False
		api.UnregisterPanel(canonical)
		return True

	def _clearHostRegistration(self):
		prev = self.stored['HostCanonical']
		if not prev:
			return
		api = self._registryApi()
		self._unregisterOwnedMenuName(prev, api=api)
		self.stored['HostCanonical'] = ''

	def _hostExtFromPar(self, _par):
		"""Resolve the registry extension that owns this parameter.

		CustomParHelper keeps a class-level EXT_SELF, so with a shipped
		registry plus a /sys global copy the wrong instance can receive
		callbacks. Always go through the parameter's owner.
		"""
		owner = _par.owner if _par is not None else self.ownerComp
		if owner and owner.valid and owner.extensionsReady:
			if hasattr(owner.ext, self.EXT_NAME):
				return getattr(owner.ext, self.EXT_NAME)
		return self

	# --- global registry lifecycle ---

	def _sys_comp(self):
		return op('/sys')

	def _is_in_sys(self, registry_comp=None):
		comp = registry_comp or self.ownerComp
		sys_comp = self._sys_comp()
		return bool(sys_comp and comp and comp.valid and comp.parent() == sys_comp)

	def _global_registry(self):
		if hasattr(op, self.SHORTCUT):
			reg = getattr(op, self.SHORTCUT)
			if reg and reg.valid and self._is_global_registry(reg):
				return reg
		sys_comp = self._sys_comp()
		if not sys_comp:
			return None
		for child in sys_comp.findChildren(name=self.REGISTRY_NAME + '*', depth=1):
			if self._is_global_registry(child):
				return child
		return None

	def _installGlobalRegistry(self):
		if self._is_sys_global(self.ownerComp):
			self.ownerComp.par.opshortcut = self.SHORTCUT
			return

		global_registry = self._global_registry()
		if global_registry and global_registry != self.ownerComp:
			if self._check_version_against(global_registry):
				return
			self._replace_global_registry(global_registry)
			return

		if not self._reconcile_parked_sys_registries():
			return

		self._become_global_registry()

	def _release_shipped_shortcut(self):
		if self._is_in_sys():
			return
		if hasattr(self.ownerComp.par, 'opshortcut'):
			self.ownerComp.par.opshortcut = ''

	def _is_global_registry(self, registry_comp):
		return self._has_global_shortcut(registry_comp)

	def _is_sys_global(self, registry_comp=None):
		comp = registry_comp or self.ownerComp
		return self._is_in_sys(comp) and self._is_global_registry(comp)

	def _has_global_shortcut(self, registry_comp):
		if not registry_comp or not registry_comp.valid:
			return False
		if hasattr(op, self.SHORTCUT) and getattr(op, self.SHORTCUT) == registry_comp:
			return True
		if hasattr(registry_comp.par, 'opshortcut'):
			return registry_comp.par.opshortcut.eval() == self.SHORTCUT
		return False

	def _find_parked_sys_registries(self):
		sys_comp = self._sys_comp()
		if not sys_comp:
			return []
		parked = []
		for child in sys_comp.findChildren(name=self.REGISTRY_NAME + '*', depth=1):
			if child == self.ownerComp:
				continue
			if not self._is_global_registry(child):
				parked.append(child)
		return parked

	def _reconcile_parked_sys_registries(self):
		parked = self._find_parked_sys_registries()
		if not parked:
			return True

		winner = parked[0]
		for reg in parked[1:]:
			new_winner = self._compare_versions(reg, winner)
			if new_winner == reg:
				self._merge_into_registry(reg, winner)
				winner.destroy()
				winner = reg
			else:
				self._merge_into_registry(winner, reg)
				reg.destroy()

		if self._compare_versions(winner, self.ownerComp) == winner:
			self._merge_into_registry(winner, self.ownerComp)
			self._promote_to_global(winner)
			return False

		self._merge_pane_registry_from(winner)
		winner.destroy()
		return True

	def _merge_into_registry(self, target_registry, source_registry):
		if target_registry == source_registry:
			return
		if hasattr(target_registry, 'ext') and hasattr(target_registry.ext, self.EXT_NAME):
			getattr(target_registry.ext, self.EXT_NAME)._merge_pane_registry_from(source_registry)

	def _compare_versions(self, comp_a, comp_b):
		ver_a = self._parse_version(self._get_version(comp_a))
		ver_b = self._parse_version(self._get_version(comp_b))

		if ver_a is None and ver_b is None:
			return comp_b if self._is_in_sys(comp_b) else comp_a
		if ver_a is None:
			return comp_b
		if ver_b is None:
			return comp_a

		if ver_a[0] != ver_b[0]:
			a_str = '.'.join(str(x) for x in ver_a)
			b_str = '.'.join(str(x) for x in ver_b)
			choice = ui.messageBox(
				f'{self.REGISTRY_NAME} Version Conflict',
				f'Multiple {self.REGISTRY_NAME} versions detected.\n\n'
				f'Existing: v{b_str} at {comp_b.path}\n'
				f'New: v{a_str} at {comp_a.path}\n\n'
				f'Which version should be used?',
				buttons=['Use New', 'Keep Existing']
			)
			return comp_b if choice != 0 else comp_a

		return comp_b if ver_b >= ver_a else comp_a

	def _promote_to_global(self, registry_comp):
		if not registry_comp or not registry_comp.valid:
			return
		registry_comp.par.opshortcut = self.SHORTCUT
		if hasattr(registry_comp, 'ext') and hasattr(registry_comp.ext, self.EXT_NAME):
			ext = getattr(registry_comp.ext, self.EXT_NAME)
			ext._neutralizeHostParameters()
			ext._syncSurface()
			# The copy's own postInit ran BEFORE the shortcut existed (host
			# branch), so the healing watch was never armed there. Arm it now
			# that the comp is the sys-global -- without this, a first-compile
			# success promotes a global with no heal loop.
			ext._armRegistryWatch()

	def _destroy_other_globals(self, keep=None):
		keep = keep or self.ownerComp
		security_counter = 10
		while security_counter:
			security_counter -= 1
			for candidate in self._find_sys_registries():
				if candidate == keep:
					continue
				if self._is_global_registry(candidate):
					candidate.destroy()

	def _find_sys_registries(self):
		sys_comp = self._sys_comp()
		if not sys_comp:
			return []
		return list(sys_comp.findChildren(name=self.REGISTRY_NAME + '*', depth=1))

	def _retryGlobalExtensionInit(self, registry_comp, attempts_left=20):
		"""Re-init /sys copy when ExtUtils dock lagged behind first extension compile."""
		if not registry_comp or not registry_comp.valid:
			return
		has_ext = (
			hasattr(registry_comp, 'ext')
			and hasattr(registry_comp.ext, self.EXT_NAME)
		)
		if has_ext:
			if self.ownerComp and self.ownerComp.valid:
				self._merge_into_registry(registry_comp, self.ownerComp)
			self._promote_to_global(registry_comp)
			return
		ext_dat = registry_comp.op(self.EXT_NAME)
		docked_n = len(ext_dat.docked) if ext_dat else -1
		eu = registry_comp.op('ExtUtils')
		debug(
			f'{self.REGISTRY_NAME}: retry global ext init attempts={attempts_left} '
			f'docked={docked_n} eu={eu.path if eu else None}'
		)
		if hasattr(registry_comp.par, 'reinitextensions'):
			registry_comp.par.reinitextensions.pulse()
		if attempts_left > 0:
			run(
				lambda c=registry_comp, n=attempts_left - 1: self._retryGlobalExtensionInit(c, n),
				delayFrames=3,
			)

	def _become_global_registry(self):
		if self._is_in_sys():
			self._destroy_other_globals()
			self.ownerComp.par.opshortcut = self.SHORTCUT
			self._syncSurface()
			self._armRegistryWatch()
			return

		sys_comp = self._sys_comp()
		if not sys_comp:
			debug(f'{self.REGISTRY_NAME}: /sys not found, cannot become global registry.')
			return

		if not self._reconcile_parked_sys_registries():
			return

		self._destroy_other_globals()

		new_registry = sys_comp.copy(self.ownerComp, name=self.REGISTRY_NAME)
		new_registry.allowCooking = True
		# The /sys global is STANDALONE: the copy inherits whatever clone
		# binding the master carries (dev masters are clone-bound for
		# hot-propagation), but a global cloned to an in-project master
		# dangles the moment an update destroys and reloads that master.
		# Promotion is the handover; from here the global owns itself.
		try:
			new_registry.par.clone = ''
			new_registry.par.enablecloning = False
		except Exception:
			pass

		anchor_comp = sys_comp.op('OpFamRegistry') or sys_comp.op('TDDialogs')
		if anchor_comp:
			new_registry.nodeX = anchor_comp.nodeX
			new_registry.nodeY = anchor_comp.nodeY - 300

		# The copy's extension initializes DURING copy() (initextonstart),
		# before it has our shortcut or data -- hand both over explicitly.
		if hasattr(new_registry, 'ext') and hasattr(new_registry.ext, self.EXT_NAME):
			self._merge_into_registry(new_registry, self.ownerComp)
		else:
			# Extension often fails first compile: me.docked empty until network cooks.
			# Sibling ExtUtils already exists — import fallback + delayed reinit recovers.
			new_registry.store('post_update', True)
			new_registry.store('PaneRegistry', dict(self.stored['PaneRegistry']))
			run(lambda c=new_registry: self._retryGlobalExtensionInit(c), delayFrames=1)
		self._promote_to_global(new_registry)

		self._release_shipped_shortcut()
		return new_registry

	def _replace_global_registry(self, old_registry):
		if self._check_version_against(old_registry):
			return
		self._merge_pane_registry_from(old_registry)
		if self._is_global_registry(old_registry):
			old_registry.destroy()
		self._become_global_registry()

	def _merge_pane_registry_from(self, other_registry):
		other_data = self._get_pane_registry_data(other_registry)
		for name, info in other_data.items():
			if name not in self.stored['PaneRegistry']:
				try:
					info = dict(info)
					info['action'] = self._normalize_action(info.get('action'))
				except (TypeError, AttributeError):
					pass
				self.stored['PaneRegistry'][name] = info

	def _get_pane_registry_data(self, registry_comp):
		if hasattr(registry_comp, 'ext') and hasattr(registry_comp.ext, self.EXT_NAME):
			return dict(getattr(registry_comp.ext, self.EXT_NAME).stored['PaneRegistry'])
		return dict(registry_comp.fetch('PaneRegistry', {}))

	def _check_version_against(self, other_registry):
		our_version = self._parse_version(self._get_version(self.ownerComp))
		their_version = self._parse_version(self._get_version(other_registry))

		if our_version is None:
			return True
		if their_version is None:
			return False

		if our_version[0] != their_version[0]:
			our_str = '.'.join(str(x) for x in our_version)
			their_str = '.'.join(str(x) for x in their_version)
			choice = ui.messageBox(
				f'{self.REGISTRY_NAME} Version Conflict',
				f'Multiple {self.REGISTRY_NAME} versions detected.\n\n'
				f'Existing: v{their_str} at {other_registry.path}\n'
				f'New: v{our_str} at {self.ownerComp.path}\n\n'
				f'Which version should be used?',
				buttons=['Use New', 'Keep Existing']
			)
			return choice != 0

		return their_version >= our_version

	def _get_version(self, comp):
		if comp and hasattr(comp.par, 'Version'):
			return str(comp.par.Version.eval())
		return None

	def _parse_version(self, ver_string):
		if not ver_string:
			return None
		try:
			ver_string = ver_string.lstrip('vV')
			return tuple(int(x) for x in ver_string.split('.'))
		except:
			return None

	# --- entry resolution ---

	def _resolveByIdOrPath(self, op_id, path):
		"""Resolve an OP by session id first (survives rename), then by path."""
		if op_id is not None:
			try:
				found = op(int(op_id))
			except Exception:
				found = None
			if found is not None and getattr(found, 'valid', False):
				return found
		if path:
			found = op(path)
			if found is not None and getattr(found, 'valid', False):
				return found
		return None

	def _resolvePanelOp(self, info):
		if not info:
			return None
		return self._resolveByIdOrPath(info.get('panel_id'), info.get('panel_path'))

	def _resolveSourceRegistry(self, info):
		if not info:
			return None
		return self._resolveByIdOrPath(
			info.get('source_registry_id'), info.get('source_registry')
		)

	def _resolveCallbackDat(self, info):
		if not info:
			return None
		return self._resolveByIdOrPath(
			info.get('callback_id'), info.get('callback_path')
		)

	# --- registry watch / heal ---

	def _armRegistryWatch(self):
		"""Periodic heal/prune loop — only on the /sys global registry."""
		if not self._is_sys_global():
			return
		if self._registry_watch_armed:
			return
		self._registry_watch_armed = True
		run(
			"args[0].valid and args[0].extensionsReady and "
			f"args[0].ext.{self.EXT_NAME}._registryWatchTick()",
			self.ownerComp,
			delayFrames=120,
			delayRef=op.TDResources,
		)

	def _registryWatchTick(self):
		self._registry_watch_armed = False
		if not self.ownerComp.valid or not self._is_sys_global():
			return
		try:
			self._healRegistryEntries()
		except Exception as e:
			debug(self.REGISTRY_NAME + ' watch: ' + str(e))
		self._armRegistryWatch()

	def _healRegistryEntries(self):
		"""Update renamed paths; drop entries whose COMP or source registry is gone."""
		for name, info in list(self.stored['PaneRegistry'].items()):
			if info.get('virtual') == '1':
				continue  # virtual entries (dividers) have no backing op by design
			try:
				info = dict(info)
			except (TypeError, AttributeError):
				continue

			panel = self._resolvePanelOp(info)
			source = self._resolveSourceRegistry(info)
			had_source = bool(info.get('source_registry') or info.get('source_registry_id'))

			if panel is None and source is not None and source.extensionsReady:
				src_ext = getattr(source.ext, self.EXT_NAME, None)
				if src_ext is not None:
					if src_ext._isAutoRegister() or src_ext.stored.get('HostCanonical') == name:
						src_ext._applyHostRegistration(
							force=bool(src_ext.stored.get('HostCanonical') == name)
						)
						info = dict(self.stored['PaneRegistry'].get(name, {}))
						panel = self._resolvePanelOp(info)
						source = self._resolveSourceRegistry(info)

			if panel is None:
				self.UnregisterPanel(name)
				continue

			if had_source and source is None:
				self.UnregisterPanel(name)
				continue

			changed = False
			if info.get('panel_path') != panel.path or info.get('panel_id') != panel.id:
				info['panel_path'] = panel.path
				info['panel_id'] = int(panel.id)
				changed = True
			if source is not None:
				if info.get('source_registry') != source.path or info.get('source_registry_id') != source.id:
					info['source_registry'] = source.path
					info['source_registry_id'] = int(source.id)
					changed = True
			cb = self._resolveCallbackDat(info)
			if cb is not None:
				if info.get('callback_path') != cb.path or info.get('callback_id') != cb.id:
					info['callback_path'] = cb.path
					info['callback_id'] = int(cb.id)
					changed = True
			if changed:
				self.stored['PaneRegistry'][name] = info
		# fleet-wide, surface-independent repairs -- every registry gets the
		# boot re-publish window and clone healing for free
		self._reapplyAutoregisterHosts()
		self._healHostClones()

	# Boot window: how many heal ticks re-sweep for unpublished hosts.
	# /sys does NOT save with the project, so on every open (and after any
	# extension reinit wave) the global comes up empty while hosts believe
	# they are registered -- their Autoregister ran at ext init, which can
	# predate the global being ready. The sweep is bounded because it is a
	# project-wide search: it fixes the boot window, then stops.
	BOOT_SWEEPS = 6

	def _reapplyAutoregisterHosts(self):
		"""Ask live Autoregister hosts that the global has no entry for to
		republish. Without this a cold boot leaves the surface unaugmented
		until someone touches a Register pulse."""
		if not self._is_sys_global():
			return
		if getattr(self, '_boot_sweeps_left', None) is None:
			self._boot_sweeps_left = self.BOOT_SWEEPS
		if self._boot_sweeps_left <= 0:
			return
		self._boot_sweeps_left -= 1
		published = set()
		for info in self.stored['PaneRegistry'].values():
			src = self._resolveSourceRegistry(info)
			if src is not None:
				published.add(src.path)
		try:
			# NO depth argument: TD's findChildren depth is an EXACT depth,
			# not a maximum -- passing one silently matches nothing.
			candidates = op('/').findChildren(name=self.REGISTRY_NAME)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: host sweep: {e}')
			return
		for host in candidates:
			if host is self.ownerComp or host.path in published:
				continue
			path = host.path
			if path.startswith('/sys') or path.startswith('/ui'):
				continue
			if not host.valid or not host.extensionsReady:
				continue
			ext = getattr(host.ext, self.EXT_NAME, None)
			if ext is None or not ext._isAutoRegister():
				continue
			try:
				ext._applyHostRegistration()
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: re-apply {path}: {e}')

	def _masterComp(self):
		"""The in-project master this registry's hosts clone from.

		Masters are depth-1 packages of the toolkit root (the raw
		registry IS the package -- required, promoted to /sys, cloneable
		by anyone extending the toolkit), so resolution rides the root's
		`FNS` global shortcut, which every install ships. None where
		absent."""
		root = getattr(op, 'FNS', None)
		if root is None or not root.valid:
			return None
		return root.op(self.REGISTRY_NAME)

	def _healHostClones(self):
		"""Re-assert in-project cloning on tool hosts. Release flows scrub the
		clone par on shipped copies (pre_release); if a release flow scrubbed
		the LIVE host instead of a staged copy, this restores it."""
		if not self._is_sys_global() or not self.CLONE_EXPR:
			return
		master = self._masterComp()
		if master is None:
			return
		for info in self.stored['PaneRegistry'].values():
			src_reg = self._resolveSourceRegistry(info)
			if src_reg is None or src_reg is master or src_reg is self.ownerComp:
				continue
			try:
				p = src_reg.par.clone
				if p.mode != ParMode.EXPRESSION or p.expr != self.CLONE_EXPR:
					if not p.eval():
						p.expr = self.CLONE_EXPR
			except Exception:
				pass

	# --- host stamping (the ONE blessed copy recipe) ---

	def StampHost(self, target_comp, canonical_name=None, autoregister=True,
				  promote_pars=True, par_values=None):
		"""Copy THIS master into `target_comp` as a configured host.

		The single supported way to stamp a registry host into a tool --
		configurator drops, fleet rollouts and scripts route here so the
		paid-for copy hazards stay fixed in ONE place:

		  * the source extension is kept quiet during copy() (an extension
		    initializing mid-copy runs as a half-configured host);
		  * the copy's inherited external identity is severed -- externaltox
		    binding OFF and cleared (boot would reload the MASTER's tox into
		    the copy), pi_suspect tag stripped (the tracker must not adopt
		    stray copies);
		  * inherited storage containers are scrubbed (a master's stored
		    state must not ride into hosts);
		  * Registration-par BINDs copied from a master that doubles as a
		    bound host are felled to CONSTANT BEFORE values are written
		    (assigning through a dangling bind raises);
		  * in-project cloning is wired as the guarded CLONE_EXPR expression;
		  * the extension is re-armed last, so registration runs against a
		    fully configured host.

		`par_values` is an optional {parName: value} dict applied to the
		Registration page (e.g. {'Excludepars': 'Spoutactive'}). Returns the
		new host COMP (or the existing one -- adopted, never overwritten);
		None when stamping is impossible.
		"""
		master = self.ownerComp
		if self._is_sys_global():
			debug(f'{self.REGISTRY_NAME}: StampHost belongs on the package '
				  f'master, not the /sys global')
			return None
		if target_comp is None or not getattr(target_comp, 'valid', False) \
				or target_comp.family != 'COMP':
			debug(f'{self.REGISTRY_NAME}: StampHost: no valid target COMP')
			return None
		existing = target_comp.op(self.REGISTRY_NAME)
		if existing is not None:
			debug(f'{self.REGISTRY_NAME}: StampHost: {existing.path} already '
				  f'exists -- adopted, not overwritten')
			return existing
		if not target_comp.allowCooking:
			debug(f'{self.REGISTRY_NAME}: StampHost: {target_comp.path} is '
				  f'cook-disabled -- a host extension cannot compile there')
			return None
		kids = [c for c in target_comp.children if hasattr(c, 'nodeX')]
		min_x = min((c.nodeX for c in kids), default=0)
		min_y = min((c.nodeY for c in kids), default=0)
		prev_initext = master.par.initextonstart.eval()
		try:
			master.par.initextonstart = False
			host = target_comp.copy(master, name=self.REGISTRY_NAME)
		finally:
			master.par.initextonstart = prev_initext
		host.nodeX = int(min_x // 200 * 200)
		host.nodeY = int((min_y - host.nodeHeight - 400) // 200 * 200)
		host.par.enableexternaltox = False
		host.par.externaltox = ''
		if 'pi_suspect' in host.tags:
			host.tags.remove('pi_suspect')
		for key in list(host.storage.keys()):
			if key.endswith('Stored') or key in ('PaneRegistry', 'HostCanonical', 'post_update'):
				host.unstore(key)
		for page in host.customPages:
			if page.name != self.HOST_PAGE_NAME:
				continue
			for p in page.pars:
				try:
					p.mode = ParMode.CONSTANT
				except Exception:
					pass
		comp_par = getattr(host.par, 'Comp', None)
		if comp_par is None:
			comp_par = getattr(host.par, 'Panel', None)
		if comp_par is not None:
			comp_par.val = '..'
		host.par.Canonicalname = canonical_name or target_comp.name
		if not promote_pars and hasattr(host.par, 'Promotepars'):
			host.par.Promotepars = False
		for pname, value in (par_values or {}).items():
			p = getattr(host.par, pname, None)
			if p is not None:
				p.val = value
			else:
				debug(f'{self.REGISTRY_NAME}: StampHost: no par {pname!r} on the host')
		host.par.Autoregister = bool(autoregister)
		if self.CLONE_EXPR:
			host.par.clone.expr = self.CLONE_EXPR
			host.par.enablecloning = True
		host.par.initextonstart = True
		host.par.reinitextensions.pulse()
		debug(f'{self.REGISTRY_NAME}: stamped host {host.path} '
			  f'(canonical {host.par.Canonicalname.eval()!r})')
		return host

	def _normalizeMenuOrder(self, menu_order):
		"""Return int sort wish, or None for default append behavior."""
		if menu_order is None:
			return None
		try:
			order = int(menu_order)
		except (TypeError, ValueError):
			return None
		if order < 0:
			return None
		return order

	# --- par-write helpers (compare-before-set: the healing tick re-runs
	# every few seconds, so repeated identical writes must be free) ---
	# Long in every subclass; now provided by the base -- the group-toggle
	# builder below always depended on them existing.

	def _setConst(self, par, value):
		if par.mode != ParMode.CONSTANT or par.eval() != value:
			par.val = value
			par.mode = ParMode.CONSTANT

	def _setExpr(self, par, expr):
		if par.mode != ParMode.EXPRESSION or par.expr != expr:
			par.expr = expr

	# --- hideable entry groups (bracket pairs, nestable) ---
	#
	# A group is a PAIR of virtual entries in the sequence -- a start switch
	# and an end cap -- the same kind of positional marker as the dividers this
	# surface already has, except the pair delimits a RANGE. Everything between
	# the markers belongs to the group, so membership is never stored anywhere:
	# drag an entry between them and it joins, drag it out and it leaves. That
	# also means a group can never have holes, and nothing needs re-applying on
	# boot beyond the markers themselves.
	#
	# Groups nest by nesting their brackets. An entry shows only when its own
	# display is on AND every group enclosing it is expanded, so collapsing an
	# outer group takes its inner switches with it while each inner group
	# remembers its own state for when the outer one opens again.
	#
	# The start switch is deliberately NOT inside its own group (collapsing must
	# never hide the only affordance that can expand it again); the end cap IS,
	# so a collapsed group renders as just the chevron.

	GROUP_START_PREFIX = 'GroupStart_'
	GROUP_END_PREFIX = 'GroupEnd_'

	def _isGroupStart(self, info):
		return bool(info) and info.get('group_start') == '1'

	def _isGroupEnd(self, info):
		return bool(info) and info.get('group_end') == '1'

	def _isGroupMarker(self, info):
		return self._isGroupStart(info) or self._isGroupEnd(info)

	def _groupStartName(self, gid):
		return self.GROUP_START_PREFIX + tdu.legalName(str(gid))

	def _groupEndName(self, gid):
		return self.GROUP_END_PREFIX + tdu.legalName(str(gid))

	def _newGroupId(self):
		entries = self.stored['PaneRegistry']
		i = 1
		while self._groupStartName('G%d' % i) in entries:
			i += 1
		return 'G%d' % i

	def _scanGroups(self, names):
		"""Resolve bracket nesting over a sequence.

		Returns (ancestors, orphans): ancestors[name] lists the enclosing group
		ids outermost-first, and orphans names markers whose partner is missing
		or whose brackets cross another group's. Healing drops those, so a
		malformed pair can never leave the surface unreadable."""
		entries = self.stored['PaneRegistry']
		ancestors = {}
		orphans = []
		stack = []
		for n in names:
			info = entries.get(n) or {}
			if self._isGroupStart(info):
				ancestors[n] = [g for g, _ in stack]
				stack.append((info.get('group_id'), n))
				continue
			if self._isGroupEnd(info):
				gid = info.get('group_id')
				if stack and stack[-1][0] == gid:
					ancestors[n] = [g for g, _ in stack]
					stack.pop()
				else:
					orphans.append(n)
				continue
			ancestors[n] = [g for g, _ in stack]
		for _gid, sname in stack:
			orphans.append(sname)
		return ancestors, orphans

	def _groupRanges(self, names):
		"""{group_id: (start_index, end_index)} over the given sequence."""
		entries = self.stored['PaneRegistry']
		starts, out = {}, {}
		for i, n in enumerate(names):
			info = entries.get(n) or {}
			if self._isGroupStart(info):
				starts[info.get('group_id')] = i
			elif self._isGroupEnd(info):
				gid = info.get('group_id')
				if gid in starts:
					out[gid] = (starts[gid], i)
		return out

	def _ensureGroupMarkers(self):
		"""Drop half-pairs and crossing brackets, and forget visibility state
		for groups that no longer exist. Runs at the top of every sync."""
		if not self._is_sys_global():
			return
		entries = self.stored['PaneRegistry']
		_, orphans = self._scanGroups(self._registeredNamesInOrder())
		for n in orphans:
			info = entries.get(n) or {}
			gid = info.get('group_id')
			# take the partner with it -- half a pair is not a group
			for partner in (self._groupStartName(gid), self._groupEndName(gid)):
				entries.pop(partner, None)
			entries.pop(n, None)
			debug('%s: dropped unmatched group marker %r' % (self.REGISTRY_NAME, n))
		live = set()
		for n in list(entries):
			info = entries.get(n) or {}
			if self._isGroupStart(info):
				live.add(info.get('group_id'))
		for gid in list(self.stored['GroupVisibility'].keys()):
			if gid not in live:
				self.stored['GroupVisibility'].pop(gid, None)

	# --- visibility ---

	def GroupVisible(self, group_id):
		"""Manager API: is this group expanded (default yes)."""
		api = self._registryApi()
		if api is not self:
			return api.GroupVisible(group_id)
		if not group_id:
			return True
		return self.stored['GroupVisibility'].get(group_id, '1') != '0'

	def SetGroupVisible(self, group_id, visible):
		"""Manager API: expand/collapse a group WITHOUT touching any member's
		own display flag, so expanding restores exactly what was showing."""
		api = self._registryApi()
		if api is not self:
			return api.SetGroupVisible(group_id, visible)
		if not group_id:
			return
		self.stored['GroupVisibility'][group_id] = '1' if visible else '0'
		self._syncSurface()

	def ToggleGroup(self, group_id):
		"""Manager API: flip a group; returns the new state."""
		api = self._registryApi()
		if api is not self:
			return api.ToggleGroup(group_id)
		visible = not self.GroupVisible(group_id)
		self.SetGroupVisible(group_id, visible)
		return visible

	def _effectiveDisplay(self, info, ancestors=()):
		"""An entry shows only if its own display is on and every group
		enclosing it is expanded."""
		if info.get('display', '1') == '0':
			return False
		return all(self.GroupVisible(gid) for gid in ancestors)

	# --- structure ---

	@property
	def Groups(self):
		"""Manager API: {group_id: {'label', 'members', 'parent', 'visible'}}.
		Members are the entries between the brackets, a nested group's start
		switch included (its own members are listed under that group)."""
		api = self._registryApi()
		if api is not self:
			return api.Groups
		entries = self.stored['PaneRegistry']
		names = self._registeredNamesInOrder()
		ancestors, _ = self._scanGroups(names)
		out = {}
		for n in names:
			info = entries.get(n) or {}
			if not self._isGroupStart(info):
				continue
			gid = info.get('group_id')
			chain = ancestors.get(n) or []
			out[gid] = {'label': info.get('label') or gid,
						'parent': chain[-1] if chain else None,
						'members': [], 'visible': self.GroupVisible(gid)}
		for n in names:
			info = entries.get(n) or {}
			if self._isGroupEnd(info):
				continue
			for gid in (ancestors.get(n) or []):
				if gid in out:
					out[gid]['members'].append(n)
		return out

	def GroupPath(self, canonical_name):
		"""Manager API: 'outer / inner' label path for an entry, '' if loose."""
		api = self._registryApi()
		if api is not self:
			return api.GroupPath(canonical_name)
		ancestors, _ = self._scanGroups(self._registeredNamesInOrder())
		chain = ancestors.get(canonical_name) or []
		if not chain:
			return ''
		groups = self.Groups
		return ' / '.join(groups.get(g, {}).get('label', g) for g in chain)

	# --- create / dissolve / rename ---

	def CreateGroup(self, first, last=None, label=None):
		"""Manager API: wrap the run from `first` to `last` (inclusive, in
		current bar order) in a new group.

		Refuses a span that would cross an existing group's brackets -- groups
		may nest or sit side by side, but never half-overlap."""
		api = self._registryApi()
		if api is not self:
			return api.CreateGroup(first, last=last, label=label)
		names = self._registeredNamesInOrder()
		last = last if last is not None else first
		if first not in names or last not in names:
			debug('%s: CreateGroup got names that are not on the bar' % self.REGISTRY_NAME)
			return None
		a, b = sorted((names.index(first), names.index(last)))
		for gid, (s, e) in self._groupRanges(names).items():
			disjoint = b < s or a > e
			inside = s < a and b < e
			contains = a < s and e < b
			if not (disjoint or inside or contains):
				debug('%s: CreateGroup refused -- the span would cross group %r; '
					  'brackets must nest, not overlap' % (self.REGISTRY_NAME, gid))
				return None
		gid = self._newGroupId()
		sname, ename = self._groupStartName(gid), self._groupEndName(gid)
		entries = self.stored['PaneRegistry']
		entries[sname] = {'virtual': '1', 'group_start': '1', 'group_id': gid,
						  'label': str(label).strip() if label else gid, 'display': '1'}
		entries[ename] = {'virtual': '1', 'group_end': '1', 'group_id': gid,
						  'display': '1'}
		self._decorateGroupMarkers(entries[sname], entries[ename], names[a])
		self.SetWidgetSequence(names[:a] + [sname] + names[a:b + 1] + [ename] + names[b + 1:])
		return gid

	def _decorateGroupMarkers(self, start_entry, end_entry, anchor_name):
		"""Surface hook: stamp surface-specific keys (the navbar's side/kind)
		onto a new pair, copied from the entry it is wrapping."""
		pass

	def RemoveGroup(self, group_id):
		"""Manager API: dissolve a group -- both markers go, members stay
		exactly where they are and keep their own display flags, so anything
		the group was hiding comes back."""
		api = self._registryApi()
		if api is not self:
			return api.RemoveGroup(group_id)
		entries = self.stored['PaneRegistry']
		found = False
		for n in (self._groupStartName(group_id), self._groupEndName(group_id)):
			if entries.pop(n, None) is not None:
				found = True
		self.stored['GroupVisibility'].pop(group_id, None)
		self._syncSurface()
		return found

	def RenameGroup(self, group_id, label):
		"""Manager API: relabel a group (id and markers untouched)."""
		api = self._registryApi()
		if api is not self:
			return api.RenameGroup(group_id, label)
		info = self.stored['PaneRegistry'].get(self._groupStartName(group_id))
		if not info:
			return False
		info['label'] = str(label).strip() or group_id
		self._syncSurface()
		return True

	GROUP_TOGGLE_CALLBACK_TEMPLATE = (
		"def onOffToOn(panelValue):\n"
		"\tif hasattr(op, {shortcut!r}):\n"
		"\t\tgetattr(op, {shortcut!r}).ToggleGroup({group!r})\n"
		"\treturn\n"
	)

	def _groupToggleCallbackText(self, group_id):
		return self.GROUP_TOGGLE_CALLBACK_TEMPLATE.format(
			shortcut=self.SHORTCUT, group=group_id)

	# mdi-chevron-left / mdi-chevron-right (Material Design Icons private-use
	# codepoints, verified against pictogrammers.com/library/mdi): the classic
	# collapse/expand affordance -- pointing left while the group is open
	# ("fold it away"), right while it is collapsed ("unfold it").
	GROUP_TOGGLE_ICON_VISIBLE = 0xF0141
	GROUP_TOGGLE_ICON_HIDDEN = 0xF0142
	def _groupToggleIcon(self, visible):
		"""Written as a VALUE on each sync, not as an expression. An
		expression would have to call GroupVisible(), and TD does not dirty
		an expression when extension storage mutates -- the glyph silently
		kept its first value while the group toggled underneath it. Every
		visibility change syncs the surface anyway, so a plain write is both
		correct and cheaper."""
		return chr(self.GROUP_TOGGLE_ICON_VISIBLE if visible
				   else self.GROUP_TOGGLE_ICON_HIDDEN)

	# Chevrons carry no text, so the switch can sit much narrower than a
	# labelled button -- it reads as a divider you can press.
	GROUP_TOGGLE_WIDTH = 8

	# A default buttonCOMP drives its label's colours from button STATE, so the
	# switch flickered between looks as it was pressed and toggled. The chevron
	# already carries the state, so the look is pinned to one flat set of
	# constants instead.
	GROUP_TOGGLE_LOOK = (
		('bgcolor', (0.2, 0.2, 0.2)),
		('bordera', (0.43, 0.43, 0.43)),
		('fontcolor', (0.6, 0.6, 0.6)),
	)

	def _applyGroupToggleLook(self, icon):
		for pg_name, values in self.GROUP_TOGGLE_LOOK:
			pg = getattr(icon.parGroup, pg_name, None)
			if pg is None:
				continue
			for par, value in zip(pg, values):
				self._setConst(par, value)

	def _groupToggleWidth(self, info):
		width = info.get('width')
		try:
			if width and int(width) > 0:
				return max(8, min(int(width), 400))
		except (TypeError, ValueError):
			pass
		return self.GROUP_TOGGLE_WIDTH

	def _buildGroupToggleWidget(self, container, name, info):
		"""Build (or refresh) a real clickable button as a child of
		`container` for a group_toggle entry: a narrow Material Design Icons
		eye/eye-off glyph (reflects current visibility) with a hover tooltip
		naming the group, wired via a panelexec to call ToggleGroup on click.
		Identical for every surface -- only sizing/alignorder/anchoring
		differ, so subclasses call this from their own _injectGroupStart."""
		gid = info.get('group_id', '')
		visible = self.GroupVisible(gid)
		inst = container.op(name)
		if inst is not None and inst.OPType != 'buttonCOMP':
			inst.destroy()
			inst = None
		if inst is None:
			inst = container.create(buttonCOMP, name)
			# create() in this project intermittently phantom-suffixes the
			# name ('..._test1'). Left alone the next sync cannot find the op
			# it just made, so it prunes and rebuilds it every pass -- a churn
			# loop that costs real frame time. Force the name we asked for.
			if inst.name != name:
				inst.name = name
			inst.par.buttontype = 'toggledown'
			tip = inst.create(textDAT, 'tip')
			tip.nodeX, tip.nodeY = 0, -150
			inst.par.helpdat = './tip'
			panelexec = inst.create(panelexecuteDAT, 'panelexec')
			panelexec.nodeX, panelexec.nodeY = 0, -300
			panelexec.par.panels.expr = 'parent()'
			panelexec.par.panelvalue = 'select'
			panelexec.par.offtoon = True
		# The glyph goes on the button's OWN 'text' child (a buttonCOMP is
		# cloned from TD's default, which already carries one showing
		# "button"). An extra child of our own would just sit alongside that
		# default label instead of replacing it.
		legacy = inst.op('icon')
		if legacy is not None:
			legacy.destroy()
		icon = inst.op('text')
		if icon is not None:
			icon.par.font = 'Material Design Icons'
			icon.par.alignx = 'center'
			icon.par.aligny = 'center'
			self._setConst(icon.par.text, self._groupToggleIcon(visible))
			self._applyGroupToggleLook(icon)
		tip = inst.op('tip')
		if tip is not None:
			label = info.get('label') or gid
			tip.text = f'Group: {label}' + ('' if visible else ' (hidden)')
		panelexec = inst.op('panelexec')
		if panelexec is not None:
			panelexec.text = self._groupToggleCallbackText(gid)
		self._setConst(inst.par.value0, 1 if visible else 0)
		return inst
