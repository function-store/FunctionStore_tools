CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class HubRegistryExt(RegistryBase):
	"""The FNS hub registry: which native panels appear as tabs in FNS_Hub.

	FNS_Hub -- a core package at the toolkit root, reached through op.FNS --
	is the one-stop window behind the FNS main-menu button: every surface's
	configurator, the console viewer, and whatever else a tool wants to show
	are TABS in it. Tabs are contributions, like every other surface in the
	toolkit: a tool carries a stamped FNS_HubRegistry host whose Registration
	pars name what the tab shows --

	  * a panel COMP (the tool itself, or any panel inside it) -- mirrored
	    into the hub through a Select COMP, so it can live anywhere;
	  * a DAT/CHOP/TOP/SOP/POP -- shown through an OP Viewer COMP;
	  * a parameter page scope of the tool -- a Parameter COMP.

	Nothing is discovered by scanning. A host registers itself at its own
	init, the base healing tick re-asks unpublished hosts during the boot
	window, and a host that appears after the hub is open registers itself
	exactly the same way. The hub holds no tab knowledge of its own; it only
	renders what this registry says.

	The global lives on /sys like every registry and is rebuilt on every
	open; hosts re-register on init. The SURFACE is in-project (the hub's
	`tabs` container): a root without the hub package still accumulates
	entries, and the sync simply waits for the surface to exist.
	"""

	# Offered when a panel COMP is dropped on the FNS button (RegistryBase).
	DROP_LABEL = 'Hub tab'
	SHORTCUT = 'FNS_HUBREGISTRY'
	EXT_NAME = 'HubRegistryExt'
	REGISTRY_NAME = 'FNS_HubRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Hb'
	TOOL_PAGE_LABEL = 'Hub'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus', 'Displayed',
					  'Tablabel', 'Taborder')

	# Location-independent: resolves through the toolkit root's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	CLONE_EXPR = "op.FNS.op('FNS_HubRegistry') if hasattr(op, 'FNS') else None"

	HUB_NAME = 'FNS_Hub'          # the surface package, a child of op.FNS
	TABS_CONTAINER = 'panel/tabs' # the hub container the mirrors live in
	TAB_PREFIX = 'hubtab_'
	TAB_TAG = 'HubRegistryTab'
	# tab kind -> the operator type that renders it inside the hub
	KINDS = {'panel': 'selectCOMP', 'opviewer': 'opviewerCOMP', 'params': 'parameterCOMP'}
	VIEWABLE_FAMILIES = ('DAT', 'CHOP', 'TOP', 'SOP', 'POP', 'MAT')
	SYNC_RETRY_FRAMES = 60
	TILE_STEP = 400               # mirror tiles are 160 wide; size + gap on the grid

	# --- surface hooks (RegistryBase contract; the surface is the hub) ---

	def _preInit(self):
		self._surface_signature = None

	def _syncSurface(self, attempts=40):
		"""Idempotent: one mirror/viewer per registered entry inside the
		hub's `tabs` container, stale ones pruned, then the hub re-reads
		the tab list. Defers until the hub exists (a root without the hub
		package never gets a surface; the entries stay registered)."""
		self._pane_sync_queued = False
		if not self._is_sys_global():
			return
		tabs = self._tabsContainer()
		if tabs is None:
			# no hub yet: retry for a while, then stand down -- the healing
			# tick and the next registration re-sync once a hub appears
			# (the queued flag must not stay set, or nothing ever re-arms)
			if attempts > 0:
				self._pane_sync_queued = True
				run(f"args[0].valid and args[0].extensionsReady and "
					f"args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
					self.ownerComp, attempts - 1,
					delayFrames=self.SYNC_RETRY_FRAMES, delayRef=op.TDResources)
			return
		live = set()
		for canonical, info in list(self.stored['PaneRegistry'].items()):
			info = dict(info)
			tool = self._resolvePanelOp(info)
			content = self._resolveContent(info)
			if tool is None or content is None:
				continue
			child = self._ensureTabChild(tabs, canonical, info, tool, content)
			if child is not None:
				live.add(child.name)
		for c in list(tabs.children):
			if c.name.startswith(self.TAB_PREFIX) and c.name not in live:
				c.destroy()
		self._layoutTabChildren(tabs)
		self._surface_signature = self._signature()
		hub = self._hubExt()
		if hub is not None:
			hub.RefreshTabs()

	def _scheduleSync(self):
		"""Coalesce: many registrations in one frame -> one sync next frame."""
		if not self._is_sys_global() or self._pane_sync_queued:
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].extensionsReady and "
			f"args[0].ext.{self.EXT_NAME}._syncSurface()",
			self.ownerComp, delayFrames=1, delayRef=op.TDResources)

	def _healRegistryEntries(self):
		super()._healRegistryEntries()
		if not self._is_sys_global():
			return
		tabs = self._tabsContainer()
		if tabs is None:
			return
		sig = self._signature()
		have = {c.name for c in tabs.children if c.name.startswith(self.TAB_PREFIX)}
		want = {self._tabChildName(s[0]) for s in sig}
		if sig != self._surface_signature or have != want:
			self._syncSurface()

	def _signature(self):
		rows = []
		for canonical, info in self.stored['PaneRegistry'].items():
			info = dict(info)
			rows.append((canonical, info.get('kind', ''), info.get('content_path', ''),
						 info.get('params', ''), str(info.get('displayed', '1')),
						 str(info.get('order', '')), info.get('label', '')))
		return tuple(sorted(rows))

	# --- the hub (surface) ---

	def _hubComp(self):
		root = getattr(op, 'FNS', None)
		hub = root.op(self.HUB_NAME) if root is not None else None
		return hub if (hub is not None and hub.valid) else None

	def _hubExt(self):
		hub = self._hubComp()
		if hub is None or not hub.extensionsReady:
			return None
		return getattr(hub.ext, 'HubExt', None)

	def _tabsContainer(self):
		hub = self._hubComp()
		tabs = hub.op(self.TABS_CONTAINER) if hub is not None else None
		return tabs if (tabs is not None and tabs.valid) else None

	def _tabChildName(self, canonical):
		return self.TAB_PREFIX + tdu.legalName(canonical)

	def _resolveContent(self, info):
		return self._resolveByIdOrPath(info.get('content_id'), info.get('content_path'))

	@staticmethod
	def _sameOp(a, b):
		return a is not None and b is not None and getattr(a, 'valid', False) and a.id == b.id

	def _ensureTabChild(self, tabs, canonical, info, tool, content):
		"""One rendering op per entry, typed by kind, pars compare-before-set
		(the healing tick calls this every few seconds)."""
		kind = info.get('kind') or 'panel'
		want = self.KINDS.get(kind)
		if want is None:
			return None
		name = self._tabChildName(canonical)
		child = tabs.op(name)
		if child is not None and child.OPType != want:
			child.destroy()
			child = None
		if child is None:
			ctor = {'selectCOMP': selectCOMP, 'opviewerCOMP': opviewerCOMP,
					'parameterCOMP': parameterCOMP}[want]
			child = tabs.create(ctor, name)
			child.tags.add(self.TAB_TAG)
			child.par.display = False      # the hub shows exactly one tab
			self.fnsLog(f'{self.REGISTRY_NAME}: tab "{canonical}" injected as {want}')
		if kind == 'panel':
			if not self._sameOp(child.par.selectpanel.eval(), content):
				child.par.selectpanel = content.path
		elif kind == 'opviewer':
			if not self._sameOp(child.par.opviewer.eval(), content):
				child.par.opviewer = content.path
			ip = getattr(child.par, 'interactive', None)
			if ip is not None and not ip.eval():
				ip.val = True
		else:
			if not self._sameOp(child.par.op.eval(), tool):
				child.par.op = tool.path
			scope = info.get('params') or '*'
			if child.par.pagescope.eval() != scope:
				child.par.pagescope = scope
			bp = getattr(child.par, 'builtin', None)
			if bp is not None and bp.eval():
				bp.val = False
		for pn, pv in (('hmode', 'fill'), ('vmode', 'fill')):
			p = getattr(child.par, pn, None)
			if p is not None and p.eval() != pv:
				p.val = pv
		return child

	def _layoutTabChildren(self, tabs):
		"""Generated tiles: one row on the grid, left to right by name."""
		kids = sorted((c for c in tabs.children if c.name.startswith(self.TAB_PREFIX)),
					  key=lambda c: c.name)
		for i, c in enumerate(kids):
			x = i * self.TILE_STEP
			if c.nodeX != x or c.nodeY != 0:
				c.nodeX, c.nodeY = x, 0

	# --- host registration (a host = one contributed tab) ---

	def _parStr(self, name):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return ''
		try:
			return str(p.eval()).strip()
		except Exception:
			return ''

	def _parInt(self, name, default=0):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return default
		try:
			return int(p.eval())
		except Exception:
			return default

	def _parOp(self, name):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return None
		try:
			o = p.eval()
		except Exception:
			return None
		return o if (o is not None and getattr(o, 'valid', False)) else None

	def _hostTabSpec(self, comp):
		"""(kind, content, params_scope, error) from the Registration pars."""
		params = self._parStr('Tabparams')
		if params:
			return 'params', comp, params, ''
		content = self._parOp('Tabcontent')
		if comp is None:
			return '', None, '', 'no tool COMP'
		if content is None or self._sameOp(content, comp):
			if getattr(comp, 'isPanel', False):
				return 'panel', comp, '', ''
			return '', None, '', ('tool COMP is not a panel -- set Tab Content '
								  '(a panel or a viewable operator) or Tab Parameters')
		return self._kindOf(content, comp)

	def _kindOf(self, content, comp):
		if getattr(content, 'isPanel', False):
			return 'panel', content, '', ''
		if getattr(content, 'family', '') in self.VIEWABLE_FAMILIES:
			return 'opviewer', content, '', ''
		return '', None, '', f'{content.path} is neither a panel nor a viewable operator'

	def _validateTab(self, comp, canonical, kind, content):
		if comp is None:
			return 'no tool COMP'
		if not canonical:
			return 'empty canonical name'
		if not canonical.replace('_', '').replace('-', '').isalnum():
			return 'canonical name must be letters, digits, _ -'
		if kind not in self.KINDS:
			return f'unknown tab kind {kind!r}'
		if content is None or not getattr(content, 'valid', False):
			return 'nothing to show'
		return ''

	def _applyHostRegistration(self, force=False):
		if self._is_sys_global():
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
		comp = self._hostComp()
		canonical = self._hostCanonicalName()
		kind, content, params, err = self._hostTabSpec(comp)
		err = err or self._validateTab(comp, canonical, kind, content)
		if err:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus(f'Error: {err}')
			return
		prev = self.stored['HostCanonical']
		api = self._registryApi()
		if prev and prev != canonical:
			self._unregisterOwnedMenuName(prev, api=api)
		api.RegisterTab(
			comp, canonical, content=content, params=params,
			label=self._parStr('Tablabel') or canonical,
			order=self._parInt('Taborder', 50),
			displayed=self._parBool('Displayed', True),
			# The host par is the ONE local override; otherwise derived
			# from the REGISTRANT's package first (the host's -- a tab
			# whose content lives in a rail, like the console driving the
			# webBrowser panel, still documents as its registrant's tool),
			# then the content's. Same rule the manifest publishes.
			help_url=(self._parStr('Helpurl')
					  or self._packageHelpUrl(self.ownerComp)
					  or self._packageHelpUrl(content)),
			source_registry=self.ownerComp,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {content.path} ({kind})')
		self._ensureToolRegistryPage()

	# --- public API (global only; hosts forward) ---

	def RegisterTab(self, comp, canonical, content=None, params='', label='',
					order=50, displayed=True, help_url='', source_registry=None):
		"""Publish a tab. `content`: a panel COMP (mirrored) or a viewable
		operator (OP Viewer); None = the tool COMP itself. `params`: a page
		scope -> a Parameter COMP view of the tool instead. `displayed`
		False registers the tab hidden -- it stays listed in the hub's tab
		manager, off the bar -- until someone shows it."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterTab(comp, canonical, content=content, params=params,
									   label=label, order=order, displayed=displayed,
									   help_url=help_url, source_registry=source_registry)
			debug(f'{self.REGISTRY_NAME}: RegisterTab ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		params = str(params or '').strip()
		if params:
			kind, content = 'params', comp
		else:
			if content is None:
				content = comp
			kind, content, _, err = self._kindOf(content, comp) if content is not None else ('', None, '', 'nothing to show')
			if err:
				debug(f'{self.REGISTRY_NAME}: RegisterTab({canonical!r}) rejected: {err}')
				return
		err = self._validateTab(comp, canonical, kind, content)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterTab({canonical!r}) rejected: {err}')
			return
		entry = {
			'panel_path': comp.path,
			'panel_id': int(comp.id),
			'content_path': content.path,
			'content_id': int(content.id),
			'kind': kind,
			'params': params,
			'label': str(label or canonical),
			'order': str(int(order)),
			'displayed': '1' if displayed else '0',
			'help_url': str(help_url or ''),
		}
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		self.stored['PaneRegistry'][canonical] = entry
		self.fnsLog(f'{self.REGISTRY_NAME}: registered tab "{canonical}" ({kind}: {content.path})')
		self._scheduleSync()

	def UnregisterTab(self, canonical):
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterTab(canonical)
			return
		if canonical in self.stored['PaneRegistry']:
			del self.stored['PaneRegistry'][canonical]
			self.fnsLog(f'{self.REGISTRY_NAME}: unregistered tab "{canonical}"')
			self._scheduleSync()

	# RegistryBase's host teardown calls this name on the API owner.
	UnregisterPanel = UnregisterTab

	def Tabs(self, include_hidden=False):
		"""Every live tab in order (an entry whose content is gone is
		skipped, never shown broken). Hidden tabs are left out unless
		include_hidden -- the tab manager asks for everything, the bar for
		what to show. `child` is the rendering op's name inside the hub."""
		api = self._registryApi()
		if api is not self:
			return api.Tabs(include_hidden=include_hidden)
		out = []
		for canonical, info in self.stored['PaneRegistry'].items():
			info = dict(info)
			content = self._resolveContent(info)
			tool = self._resolvePanelOp(info)
			if content is None or tool is None:
				continue
			displayed = str(info.get('displayed', '1')) != '0'
			if not displayed and not include_hidden:
				continue
			out.append({
				'name': canonical,
				'label': info.get('label') or canonical,
				'order': int(info.get('order', 50)),
				'displayed': displayed,
				'kind': info.get('kind', 'panel'),
				'content': content.path,
				'tool': tool.path,
				'help_url': info.get('help_url', ''),
				'child': self._tabChildName(canonical),
			})
		out.sort(key=lambda t: (t['order'], str(t['label']).lower()))
		return out

	def SetTabDisplayed(self, canonical, displayed):
		"""Show or hide a tab. The entry flips now, and the decision is
		written back to the contributing host's Displayed par
		(compare-before-set) -- that par is what persists with the tool and
		roams with its Registry page."""
		api = self._registryApi()
		if api is not self:
			return api.SetTabDisplayed(canonical, displayed)
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return {'ok': False, 'why': f'no tab: {canonical}'}
		displayed = bool(displayed)
		entry = dict(info)
		entry['displayed'] = '1' if displayed else '0'
		self.stored['PaneRegistry'][canonical] = entry
		wrote_host = False
		src = self._resolveSourceRegistry(entry)
		if src is not None:
			p = getattr(src.par, 'Displayed', None)
			if p is not None:
				try:
					if bool(p.eval()) != displayed:
						p.val = displayed
					wrote_host = True
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: Displayed write-back {src.path}: {e}')
		self.fnsLog(f'{self.REGISTRY_NAME}: tab "{canonical}" '
					f'{"shown" if displayed else "hidden"}')
		self._scheduleSync()
		return {'ok': True, 'name': canonical, 'displayed': displayed,
				'persisted': wrote_host}

	def Open(self, tab=None):
		"""Open FNS_Hub, on `tab` (a canonical name) when given."""
		api = self._registryApi()
		if api is not self:
			return api.Open(tab=tab)
		hub = self._hubExt()
		if hub is None:
			return {'ok': False, 'why': 'no FNS_Hub in this root (install the FNS_Hub package)'}
		return hub.Open(tab=tab)

	def OpenDocs(self, canonical):
		"""Open a tab's registered help page, if it has one."""
		api = self._registryApi()
		if api is not self:
			return api.OpenDocs(canonical)
		info = self.stored['PaneRegistry'].get(canonical) or {}
		url = str(dict(info).get('help_url', '') or '').strip()
		if not url:
			return False
		ui.viewFile(url)
		return True

	# --- host par callbacks (CustomParHelper: pulses get (_par), values
	# get (_par, _val, _prev); the owner is resolved THROUGH the par because
	# a shipped host plus the /sys global share one class-level EXT_SELF) ---

	def _reapply(self, _par):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParRegister(self, _par):
		self._hostExtFromPar(_par)._applyHostRegistration(force=True)

	def onParAutoregister(self, _par, _val, _prev):
		self._hostExtFromPar(_par)._applyHostRegistration()

	def onParCanonicalname(self, _par, _val, _prev):
		self._reapply(_par)

	def onParComp(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTabcontent(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTabparams(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTablabel(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTaborder(self, _par, _val, _prev):
		self._reapply(_par)

	def onParDisplayed(self, _par, _val, _prev):
		self._reapply(_par)

	def onParHelpurl(self, _par, _val, _prev):
		self._reapply(_par)

	def onParOpen(self, _par):
		ext = self._hostExtFromPar(_par)
		ext.Open(tab=ext.stored['HostCanonical'] or None)
