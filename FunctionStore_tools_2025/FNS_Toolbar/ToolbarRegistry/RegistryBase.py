

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

from TDStoreTools import StorageManager

class RegistryBase:
	EXT_NAME = 'RegistryBase'
	SHORTCUT = None
	REGISTRY_NAME = 'Registry'
	HOST_PAGE_NAME = 'Registration'

	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self._preInit()
		storedItems = [
			{'name': 'PaneRegistry', 'default': {}, 'property': True, 'readOnly': True},
			{'name': 'HostCanonical', 'default': '', 'property': True, 'readOnly': True},
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
			self._clearHostRegistration()
		except Exception as e:
			debug(f'{self.REGISTRY_NAME} onDestroyTD: {e}')

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
			self._stripHostParameters()
			self._syncSurface()
			self._armRegistryWatch()
			self._ensureSelectionExecuteRole()
			return

		self._sanitizeStoredRegistry()
		self._installGlobalRegistry()
		self._release_shipped_shortcut()
		self._applyHostRegistration()
		self._ensureSelectionExecuteRole()

	def _stripHostParameters(self):
		"""The global /sys instance is pure infrastructure -- host-publisher
		parameters (Registration page) are meaningless on it and are removed.
		Hosts keep the page; every host-par read in this class is hasattr-
		guarded, so a stripped instance degrades cleanly."""
		for page in list(self.ownerComp.customPages):
			if page.name != self.HOST_PAGE_NAME:
				continue
			try:
				page.destroy()
			except Exception:
				for p in list(page.pars):
					p.destroy()

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
			ext._stripHostParameters()
			ext._syncSurface()

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
