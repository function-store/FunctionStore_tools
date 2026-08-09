

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class ToolbarRegistryExt(RegistryBase):
	SHORTCUT = 'TOOLBARREGISTRY'
	EXT_NAME = 'ToolbarRegistryExt'
	REGISTRY_NAME = 'ToolbarRegistry'

	MIRROR_PREFIX = 'tbmirror_'
	MIRROR_TAG = 'ToolbarRegistryMirror'
	# The installed bar: FNS_Toolbar copies its widgets into TD's bookmark bar.
	BAR_PATH = '/ui/dialogs/bookmark_bar'

	# Mirrors sort after the legacy table-driven widgets until those are
	# migrated; the registry is the sole order/visibility manager.
	MIRROR_ORDER_BASE = 1000

	SELECTPANEL_EXPR = (
		"op.TOOLBARREGISTRY.WidgetTarget({canonical!r}) "
		"if hasattr(op, 'TOOLBARREGISTRY') else None"
	)

	# --- surface hooks (RegistryBase contract) ---

	def _ensureSelectionExecuteRole(self):
		# Toolbar has no selection DAT; hosts just must not keep a parallel table.
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _syncSurface(self, attempts=40):
		"""Idempotent: prune orphan mirrors, then ensure one managed mirror
		per registered entry, ordered and shown per the central store.
		Defers until TD's bookmark bar exists."""
		self._pane_sync_queued = False
		if self._barReady():
			self._ensureConfigEntry()
			self._pruneMirrors()
			for canonical in self._registeredNamesInOrder():
				self._injectWidget(canonical)
			return
		if attempts <= 0:
			debug(f'{self.REGISTRY_NAME}: bar never became available, skipping sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	# --- bar helpers ---

	def _bar(self):
		return op(self.BAR_PATH)

	def _toolbarComp(self):
		return getattr(op, 'FNS_TOOLBAR', None)

	def _barReady(self):
		bar = self._bar()
		return bool(bar and bar.valid)

	def _mirrorName(self, canonical):
		return self.MIRROR_PREFIX + tdu.legalName(canonical)

	def _registeredNamesInOrder(self):
		entries = self.stored['PaneRegistry']
		ordered = []
		unordered = []
		for name, info in entries.items():
			order = self._normalizeMenuOrder(info.get('menu_order'))
			(ordered if order is not None else unordered).append((order, name))
		ordered.sort(key=lambda t: (t[0], t[1].lower()))
		return [n for _, n in ordered] + [n for _, n in unordered]

	# --- managed mirror lifecycle ---

	def WidgetTarget(self, canonical):
		"""Resolve the live widget COMP for a registered canonical name.

		Mirrors' Select Panel parameters call this, so a moved or renamed
		widget heals on the next cook instead of leaving a dead path.
		"""
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return None
		return self._resolvePanelOp(info)

	def _injectWidget(self, canonical):
		bar = self._bar()
		if not bar:
			return
		info = self.stored['PaneRegistry'].get(canonical)
		widget = self.WidgetTarget(canonical)
		if widget is None:
			debug(f'{self.REGISTRY_NAME}: no live widget for {canonical!r}, skipping inject')
			return
		name = self._mirrorName(canonical)
		mirror = bar.op(name)
		if not mirror:
			mirror = bar.create(selectCOMP, name)
			mirror.tags.add(self.MIRROR_TAG)
			siblings = bar.ops(self.MIRROR_PREFIX + '*')
			mirror.nodeX = 500 + (len(siblings) - 1) * 200
			mirror.nodeY = -700
		self._setExpr(mirror.par.selectpanel, self.SELECTPANEL_EXPR.format(canonical=canonical))
		mirror.par.matchsize = True
		self._anchorMirror(mirror, bar)
		# The registry is the manager: order and visibility come from the
		# central entry, not from any table.
		order = self._normalizeMenuOrder(info.get('menu_order'))
		if order is None:
			order = len(bar.ops(self.MIRROR_PREFIX + '*'))
		self._setConst(mirror.par.display, 0 if info.get('display', '1') == '0' else 1)
		self._setConst(mirror.par.alignorder, self.MIRROR_ORDER_BASE + order)

	CONFIG_CANONICAL = 'Configure'
	# 0 sorts before every published widget (they start at 1), so the gear
	# sits left-most, right after TD's own built-in bar items.
	CONFIG_ORDER = 0

	def _ensureConfigEntry(self):
		"""Register the registry's own gear button (ships dormant in every
		copy; only the sys-global publishes it, pinned at the bar's end)."""
		if not self._is_sys_global():
			return
		btn = self.ownerComp.op('btn_config')
		if btn is None or self.CONFIG_CANONICAL in self.stored['PaneRegistry']:
			return
		self.RegisterWidget(btn, self.CONFIG_CANONICAL, order=self.CONFIG_ORDER)

	def OpenConfigurator(self):
		"""Open the Toolbar Configurator (lives in the FNS_Toolbar package)."""
		api = self._registryApi()
		if api is not self:
			return api.OpenConfigurator()
		cfg = getattr(op, 'TOOLBARCONFIG', None)
		if cfg is None:
			tb = self._toolbarComp()
			cfg = tb.op('ToolbarConfigurator') if tb else None
		if cfg is None or not hasattr(cfg.ext, 'ConfiguratorExt'):
			debug(f'{self.REGISTRY_NAME}: no ToolbarConfigurator installed (needs the FNS_Toolbar package)')
			return
		cfg.ext.ConfiguratorExt.Refresh()
		cfg.ext.ConfiguratorExt.Open()

	def _anchorMirror(self, mirror, bar):
		"""Wire the mirror's panel input to the bar's emptypanel -- the same
		anchoring the original FNS_Toolbar installer applied to every copied
		widget. Unwired panels drop out of the bookmark bar's layout flow."""
		anchor = bar.op('emptypanel')
		if not anchor:
			return
		try:
			in_conn = mirror.inputCOMPConnectors[0]
			if not in_conn.connections:
				in_conn.connect(anchor.outputCOMPConnectors[0])
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: anchoring {mirror.path} failed: {e}')

	def _setExpr(self, par, expr):
		# Compare-before-set: the healing tick re-runs injection every few
		# seconds, so repeated identical writes must be free.
		if par.mode != ParMode.EXPRESSION or par.expr != expr:
			par.expr = expr

	def _setConst(self, par, value):
		if par.mode != ParMode.CONSTANT or par.eval() != value:
			par.val = value
			par.mode = ParMode.CONSTANT


	def _pruneMirrors(self):
		"""Drop mirrors whose canonical is no longer registered."""
		bar = self._bar()
		if not bar:
			return
		live = {self._mirrorName(c) for c in self.stored['PaneRegistry']}
		for mirror in bar.ops(self.MIRROR_PREFIX + '*'):
			if self.MIRROR_TAG in mirror.tags and mirror.name not in live:
				mirror.destroy()

	def _healRegistryEntries(self):
		"""Base healing plus surface repair: re-inject any registered entry
		whose mirror is missing or stale. This is what makes a LATE-arriving
		bar work -- _syncSurface gives up after its retry budget, but the
		watch tick keeps checking and re-applies managed state."""
		super()._healRegistryEntries()
		if not self._is_sys_global() or not self._barReady():
			return
		for canonical in self._registeredNamesInOrder():
			self._injectWidget(canonical)
		self._healHostClones()

	# Location-independent: resolves through the toolbar package's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	CLONE_EXPR = "op.FNS_TOOLBAR.op('ToolbarRegistry') if hasattr(op, 'FNS_TOOLBAR') else None"

	def _healHostClones(self):
		"""Re-assert in-project cloning on tool hosts. Release flows scrub
		the clone par on shipped copies (pre_release); if a release tool
		scrubbed the LIVE host instead of a staged copy, this restores it."""
		tb = self._toolbarComp()
		master = tb.op('ToolbarRegistry') if tb else None
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

	# --- public API ---

	def RegisterWidget(self, widget_op, canonical_name, order=None, display=True,
					   callback=None, source_registry=None):
		"""Publish a panel COMP as a toolbar widget under canonical_name."""
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
		if self._barReady():
			self._injectWidget(canonical_name)
		elif not self._pane_sync_queued:
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
		bar = self._bar()
		if bar:
			name = self._mirrorName(canonical_name)
			mirror = bar.op(name)
			if mirror and self.MIRROR_TAG in mirror.tags:
				mirror.destroy()

	# RegistryBase healing calls self.UnregisterPanel(name); alias it.
	def UnregisterPanel(self, canonical_name):
		return self.UnregisterWidget(canonical_name)

	def SetWidgetOrder(self, canonical_name, order):
		"""Manager API: reposition a registered widget in the bar."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetOrder(canonical_name, order)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return
		norm = self._normalizeMenuOrder(order)
		if norm is None:
			info.pop('menu_order', None)
		else:
			info['menu_order'] = norm
		self._syncSurface()

	def SetWidgetDisplay(self, canonical_name, visible):
		"""Manager API: show or hide a registered widget."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetDisplay(canonical_name, visible)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return
		info['display'] = '1' if visible else '0'
		self._syncSurface()

	@property
	def Widgets(self):
		"""Manager API: snapshot of all registered widget entries."""
		return {k: dict(v) for k, v in self.stored['PaneRegistry'].items()}

	@property
	def WidgetSequence(self):
		"""Manager API: canonical names in current bar order."""
		api = self._registryApi()
		if api is not self:
			return api.WidgetSequence
		return self._registeredNamesInOrder()

	def SetWidgetSequence(self, canonical_names):
		"""Manager API: reassign order 1..N from the given full sequence.

		Names not in the sequence keep registration but drop to the end;
		unknown names are ignored. One surface sync at the end -- this is
		the batch primitive a drag-reorder UI calls."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetSequence(canonical_names)
		entries = self.stored['PaneRegistry']
		order = 1
		for name in canonical_names:
			info = entries.get(name)
			if info is not None:
				info['menu_order'] = order
				order += 1
		for name in self._registeredNamesInOrder():
			if name not in canonical_names:
				entries[name]['menu_order'] = order
				order += 1
		self._syncSurface()

	DIVIDER_TAG = 'ToolbarRegistryDivider'

	def AddDivider(self, after=None):
		"""Manager API: create a registry-owned divider widget and register
		it (after the given canonical name, or at the end). The widget is
		copied from the toolbar package's divider template and lives in its
		widgets shelf."""
		api = self._registryApi()
		if api is not self:
			return api.AddDivider(after=after)
		tb = self._toolbarComp()
		shelf = tb.op('widgets') if tb else None
		template = shelf.op('FNS_divider1') if shelf else None
		if template is None:
			debug(f'{self.REGISTRY_NAME}: AddDivider needs the FNS_Toolbar package (widgets/FNS_divider1)')
			return None
		i = 1
		while shelf.op(f'divider_x{i}') or f'DividerX{i}' in self.stored['PaneRegistry']:
			i += 1
		w = shelf.copy(template, name=f'divider_x{i}')
		w.tags.add(self.DIVIDER_TAG)
		w.nodeY = template.nodeY - 200 * i
		canonical = f'DividerX{i}'
		seq = self._registeredNamesInOrder()
		if after in seq:
			seq.insert(seq.index(after) + 1, canonical)
		else:
			seq.append(canonical)
		self.RegisterWidget(w, canonical)
		self.SetWidgetSequence(seq)
		return canonical

	def RemoveDivider(self, canonical_name):
		"""Manager API: unregister and destroy a registry-owned divider.
		Refuses widgets it does not own (no DIVIDER_TAG)."""
		api = self._registryApi()
		if api is not self:
			return api.RemoveDivider(canonical_name)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		w = self._resolvePanelOp(info)
		if w is None or self.DIVIDER_TAG not in w.tags:
			debug(f'{self.REGISTRY_NAME}: RemoveDivider refused -- {canonical_name!r} is not a registry-owned divider')
			return False
		self.UnregisterWidget(canonical_name)
		w.destroy()
		return True

	def _validateWidget(self, widget_op):
		if widget_op is None:
			return 'No widget COMP selected'
		if widget_op.family != 'COMP':
			return f'{widget_op.path} is not a COMP'
		if not widget_op.isPanel:
			return f'{widget_op.path} is not a Panel COMP (isPanel=False)'
		return None

	# --- host registration (Registration page), toolbar flavor ---

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
		display = self._parBool('Displayed', True)
		prev = self.stored['HostCanonical']
		api = self._registryApi()
		if prev and prev != canonical:
			self._unregisterOwnedMenuName(prev, api=api)
		api.RegisterWidget(
			widget, canonical,
			order=self._hostMenuOrder(),
			display=display,
			callback=self._hostCallbackDat(),
			source_registry=self.ownerComp,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {widget.path}')

	# --- CustomParHelper callbacks (Registration page) ---

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
