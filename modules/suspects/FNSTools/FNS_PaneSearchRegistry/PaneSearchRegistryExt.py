
CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or next((c for c in me.parent().children if 'ExtUtils' in c.tags), None)).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class PaneSearchRegistryExt(RegistryBase):
	"""FNS_PaneSearchRegistry: contributed panels in every network editor
	pane's find bar (docs/PaneSearchRegistry.md).

	The find bar is /ui/panes/pane_find/<pane name>, one per pane, made by
	TouchDesigner the first time that pane opens its find bar. Each registered
	panel is COPIED into every bar (not mirrored: a contribution may keep
	per-pane state), hung off the bar's `emptypanel` like TD's own controls,
	and ordered between Home and the filler. The registry adds containers to
	the bar and nothing else: the search itself is not its business.
	"""
	SHORTCUT = 'FNS_PANESEARCHREGISTRY'
	EXT_NAME = 'PaneSearchRegistryExt'
	REGISTRY_NAME = 'FNS_PaneSearchRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Ps'
	TOOL_PAGE_LABEL = 'Find Bar'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus', 'Menuorder', 'Displayed')

	# TouchDesigner's own UI location: fixed by TD, not by a project.
	PANE_FIND = '/ui/panes/pane_find'
	ITEM_PREFIX = 'psr_'
	ITEM_TAG = 'PaneSearchRegistryItem'
	OWNERSHIP_TAGS = ('FNS_externalized', 'pi_suspect')
	# TD's own controls: search 0, back 1, forward 2, label 3, Home 3.5,
	# filler 4, close 5. Contributions share the gap after Home.
	ORDER_FIRST = 3.6
	ORDER_SPAN = 0.3

	CLONE_EXPR = "op.FNS.op('FNS_PaneSearchRegistry') if hasattr(op, 'FNS') else None"

	# --- stamping: a host is not the package ---

	def StampHost(self, target_comp, canonical_name=None, autoregister=True,
				  promote_pars=True, par_values=None):
		"""RegistryBase.StampHost, then shaped like every other registry host."""
		host = super().StampHost(target_comp, canonical_name=canonical_name,
								 autoregister=autoregister, promote_pars=promote_pars,
								 par_values=par_values)
		if host is not None:
			self._shapeHost(host)
		return host

	def _shapeHost(self, host):
		"""Drop what came along from the master that a host must not carry.

		The copy brings the master's FNS_About and annotation. No other
		registry host carries an FNS_About, and in a shipped tool the clone
		re-syncs it on load, when its extension starts before its docked
		ExtUtils resolves: "has no attribute ExtFnsAbout" in SearchFix's host
		(field report 2026-10-06). The About values the master reads through
		it become constants, as on every other host.
		"""
		for p in host.customPars:
			if p.page.name == 'About' and p.mode != ParMode.CONSTANT:
				value = p.eval()
				p.val = value
		if host.par['Touchbuild'] is not None and not str(host.par.Touchbuild.eval()):
			host.par.Touchbuild = str(app.build)
		fa = host.op('FNS_About')
		if fa is not None:
			fa.destroy()
		for ann in host.findChildren(type=annotateCOMP, includeUtility=True, maxDepth=1):
			ann.destroy()

	# --- surface hooks (RegistryBase contract) ---

	def _ensureSelectionExecuteRole(self):
		# no selection DAT; hosts must not keep a parallel table
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _syncSurface(self, attempts=40):
		"""Idempotent: every find bar gets one copy per registered panel, in
		order, and loses the copies of panels no longer registered."""
		self._pane_sync_queued = False
		if not self._is_sys_global():
			return
		if not self._barReady():
			if attempts > 0:
				self._pane_sync_queued = True
				run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
					self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)
			return
		for bar in self._bars():
			self._syncBar(bar)

	def _healRegistryEntries(self):
		"""Base healing, then the surface: this is also what reaches a find bar
		opened since the last sync, should the pane_find watcher miss it."""
		super()._healRegistryEntries()
		if self._is_sys_global() and self._barReady():
			for bar in self._bars():
				self._syncBar(bar)

	def onPaneFindChange(self):
		"""Wiring for the pane_find watcher: a pane opened its find bar."""
		if self._is_sys_global():
			run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface()",
				self.ownerComp, delayFrames=1, delayRef=op.TDResources)

	# --- the find bars ---

	def _barReady(self):
		return op(self.PANE_FIND) is not None

	def _bars(self):
		"""Every pane's find bar there is."""
		home = op(self.PANE_FIND)
		if home is None:
			return []
		return [b for b in home.children
				if b.valid and b.isCOMP and b.op('emptypanel') is not None]

	def _itemName(self, canonical):
		return self.ITEM_PREFIX + tdu.legalName(canonical)

	def _registeredNamesInOrder(self):
		entries = self.stored['PaneRegistry']
		ordered, unordered = [], []
		for name, info in entries.items():
			order = self._normalizeMenuOrder(info.get('menu_order'))
			(ordered if order is not None else unordered).append((order, name))
		ordered.sort(key=lambda t: (t[0], t[1].lower()))
		return [n for _, n in ordered] + [n for _, n in unordered]

	def _syncBar(self, bar):
		self._pruneItems(bar)
		names = [n for n in self._registeredNamesInOrder()
				 if self._resolvePanelOp(self.stored['PaneRegistry'][n]) is not None]
		for i, canonical in enumerate(names):
			self._injectItem(canonical, bar, i, len(names))

	def _injectItem(self, canonical, bar, index, count):
		info = self.stored['PaneRegistry'].get(canonical)
		source = self._resolvePanelOp(info) if info else None
		if source is None:
			return
		name = self._itemName(canonical)
		inst = bar.op(name)
		# a copy is kept as long as its source is the same operator: the
		# copy's own state is per pane. RefreshWidget forces a new copy.
		if inst is not None and inst.fetch('psr_source_id', None, search=False) != int(source.id):
			inst.destroy()
			inst = None
		if inst is None:
			inst = self._copyQuiet(bar, source, name)
			self._detachInstanceFiles(inst)
			inst.tags.add(self.ITEM_TAG)
			inst.store('psr_source_id', int(source.id))
			home = bar.op('home')
			if home is not None:
				inst.nodeX = home.nodeX + 200 * index
				inst.nodeY = home.nodeY - 400
		inst.par.display = str(info.get('display', '1')) == '1'
		inst.par.alignorder = self.ORDER_FIRST + self.ORDER_SPAN * index / float(max(count, 1))
		self._anchorItem(inst, bar)

	def _copyQuiet(self, bar, source, name):
		"""Copy a source into a bar without letting a registry host inside it
		wake up during copy() (FNS_NavbarRegistry paid for this: a copy's
		host registers before anything can destroy it)."""
		hosts = [h for h in source.findChildren(type=COMP, maxDepth=2)
				 if h.name.endswith('Registry') and hasattr(h.par, 'initextonstart')]
		saved = [(h, h.par.initextonstart.eval()) for h in hosts]
		try:
			for h, _ in saved:
				h.par.initextonstart = False
			return bar.copy(source, name=name)
		finally:
			for h, v in saved:
				try:
					h.par.initextonstart = v
				except Exception:
					pass

	def _detachInstanceFiles(self, inst):
		"""A copy holds the text it was copied with and answers to nothing on
		disk: one owner per file (FNS_NavbarRegistry, same rule)."""
		for d in inst.findChildren(type=DAT):
			try:
				if d.par.syncfile.eval() or d.par.file.eval():
					d.par.syncfile = False
					d.par.file = ''
			except Exception:
				pass
			if d.tags:
				d.tags -= set(self.OWNERSHIP_TAGS)
		inst.tags -= set(self.OWNERSHIP_TAGS)

	def _anchorItem(self, inst, bar):
		"""Hang the copy off `emptypanel`: the find bar lays out what is
		connected there, as TD wires its own controls."""
		anchor = bar.op('emptypanel')
		if anchor is None:
			return
		try:
			if anchor not in inst.inputCOMPs:
				inst.inputCOMPConnectors[0].connect(anchor)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: anchoring {inst.path} failed: {e}')

	def _pruneItems(self, bar):
		"""Drop copies whose entry is gone or no longer resolves."""
		live = {self._itemName(c) for c, info in self.stored['PaneRegistry'].items()
				if self._resolvePanelOp(info) is not None}
		for inst in bar.ops(self.ITEM_PREFIX + '*'):
			if self.ITEM_TAG in inst.tags and inst.name not in live:
				inst.destroy()

	def _destroyInstances(self, canonical):
		name = self._itemName(canonical)
		for bar in self._bars():
			inst = bar.op(name)
			if inst is not None and self.ITEM_TAG in inst.tags:
				inst.destroy()

	# --- public API ---

	def WidgetTarget(self, canonical):
		"""The live source panel registered under `canonical`, or None."""
		info = self.stored['PaneRegistry'].get(canonical)
		return self._resolvePanelOp(info) if info else None

	def Instance(self, bar, canonical):
		"""The copy of `canonical` in one find bar, or None."""
		inst = bar.op(self._itemName(canonical)) if bar is not None else None
		return inst if inst is not None and self.ITEM_TAG in inst.tags else None

	def Widgets(self):
		"""The registered names, in bar order."""
		return self._registeredNamesInOrder()

	def RefreshWidget(self, canonical):
		"""Replace every find bar's copy of `canonical` with a fresh copy of
		its source, after the source changed."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self and api is not None:
				return api.RefreshWidget(canonical)
			return
		self._destroyInstances(canonical)
		self._syncSurface()

	def RegisterWidget(self, widget_op, canonical_name, order=None, display=True,
					   callback=None, source_registry=None):
		"""Publish a panel COMP into every pane's find bar under canonical_name."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterWidget(
					widget_op, canonical_name, order=order, display=display,
					callback=callback, source_registry=source_registry)
			debug(f'{self.REGISTRY_NAME}: RegisterWidget ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		err = self._validateWidget(widget_op)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterWidget({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
		}
		norm_order = self._normalizeMenuOrder(order)
		if norm_order is not None:
			entry['menu_order'] = norm_order
		if callback is not None:
			entry['callback_path'] = callback.path
			entry['callback_id'] = int(callback.id)
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		self.stored['PaneRegistry'][canonical_name] = entry
		self.fnsLog(f'{self.REGISTRY_NAME}: registered widget "{canonical_name}" ({widget_op.path})')
		self._syncSurface()

	def UnregisterWidget(self, canonical_name):
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterWidget(canonical_name)
			debug(f'{self.REGISTRY_NAME}: UnregisterWidget ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		self.stored['PaneRegistry'].pop(canonical_name, None)
		self.fnsLog(f'{self.REGISTRY_NAME}: unregistered widget "{canonical_name}"')
		self._destroyInstances(canonical_name)

	# RegistryBase healing calls self.UnregisterPanel(name); alias it.
	def UnregisterPanel(self, canonical_name):
		return self.UnregisterWidget(canonical_name)

	def _validateWidget(self, widget_op):
		if widget_op is None:
			return 'No widget COMP selected'
		if widget_op.family != 'COMP':
			return f'{widget_op.path} is not a COMP'
		if not widget_op.isPanel:
			return f'{widget_op.path} is not a Panel COMP (isPanel=False)'
		return None

	# --- host registration (Registration page) ---

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
		widget = self._hostComp()
		if not widget:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus('Error: no widget COMP')
			return
		canonical = self._hostCanonicalName()
		if not canonical:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus('Error: empty canonical name')
			return
		err = self._validateWidget(widget)
		if err:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus(f'Error: {err}')
			return
		prev = self.stored['HostCanonical']
		api = self._registryApi()
		if prev and prev != canonical:
			self._unregisterOwnedMenuName(prev, api=api)
		api.RegisterWidget(
			widget, canonical,
			order=self._hostMenuOrder(),
			display=self._parBool('Displayed', True),
			callback=self._hostCallbackDat(),
			source_registry=self.ownerComp,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {widget.path}')
		self._ensureToolRegistryPage()

	def onParAutoregister(self, _par, _val, _prev):
		self._hostExtFromPar(_par)._applyHostRegistration()

	def onParRegister(self, _par):
		self._hostExtFromPar(_par)._applyHostRegistration(force=True)

	def onParCanonicalname(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParComp(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParMenuorder(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParDisplayed(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParCallback(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()
