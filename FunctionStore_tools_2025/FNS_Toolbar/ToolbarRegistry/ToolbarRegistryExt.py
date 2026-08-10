

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class ToolbarRegistryExt(RegistryBase):
	SHORTCUT = 'TOOLBARREGISTRY'
	EXT_NAME = 'ToolbarRegistryExt'
	REGISTRY_NAME = 'ToolbarRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Tb'
	TOOL_PAGE_LABEL = 'Toolbar'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus',
					  'Menuorder', 'Displayed', 'Barwidth')

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
	# Soft-enforced bar icon height: mirrors always render 19 px tall; the
	# source widget's own size is never touched.
	BAR_ICON_HEIGHT = 19
	MIRROR_WIDTH_EXPR = (
		"(op.TOOLBARREGISTRY.WidgetTarget({canonical!r}).width "
		"if hasattr(op, 'TOOLBARREGISTRY') "
		"and op.TOOLBARREGISTRY.WidgetTarget({canonical!r}) is not None else 30)"
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
			self._ensureGroupMarkers()
			self._pruneMirrors()
			names = self._registeredNamesInOrder()
			ancestors, _ = self._scanGroups(names)
			for i, canonical in enumerate(names):
				self._injectWidget(canonical, i, ancestors.get(canonical, ()))
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

	def _isDividerEntry(self, info):
		return bool(info) and info.get('divider') == '1'

	def _barOrder(self, info, seq_index):
		"""Bar position comes from the entry's place in the RESOLVED sequence,
		not its stored menu_order: group switches deliberately store no order
		of their own (theirs is derived), and two entries sharing a stored
		order would otherwise land on the same alignorder and fight."""
		if seq_index is not None:
			return seq_index
		order = self._normalizeMenuOrder(info.get('menu_order'))
		if order is None:
			order = len(self._bar().ops(self.MIRROR_PREFIX + '*'))
		return order

	def _injectWidget(self, canonical, seq_index=None, ancestors=()):
		bar = self._bar()
		if not bar:
			return
		info = self.stored['PaneRegistry'].get(canonical)
		if self._isDividerEntry(info):
			self._injectDivider(canonical, info, bar, seq_index, ancestors)
			return
		if self._isGroupStart(info):
			self._injectGroupStart(canonical, info, bar, seq_index, ancestors)
			return
		if self._isGroupEnd(info):
			self._injectGroupEnd(canonical, info, bar, seq_index, ancestors)
			return
		if info.get('adopted') == '1':
			self._applyAdopted(canonical, info, bar, seq_index, ancestors)
			return
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
		# Mirrors own their geometry: height is soft-enforced to the bar
		# standard, width follows the source live unless overridden.
		mirror.par.matchsize = False
		width = info.get('width', '')
		if width:
			try:
				self._setConst(mirror.par.w, int(width))
			except (TypeError, ValueError):
				pass
		else:
			self._setExpr(mirror.par.w, self.MIRROR_WIDTH_EXPR.format(canonical=canonical))
		self._setConst(mirror.par.h, self.BAR_ICON_HEIGHT)
		self._anchorMirror(mirror, bar)
		# The registry is the manager: order and visibility come from the
		# central entry, not from any table.
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(mirror.par.alignorder,
					   self.MIRROR_ORDER_BASE + self._barOrder(info, seq_index))

	def _applyAdopted(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""An ADOPTED entry is a panel that already lives in the bar -- TD's
		own icons. It is managed IN PLACE: order and visibility are written
		straight onto the panel, and no mirror is made, because making one
		would show the thing twice."""
		o = self._resolvePanelOp(info)
		if o is None:
			return
		self._setConst(o.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(o.par.alignorder,
					   self.MIRROR_ORDER_BASE + self._barOrder(info, seq_index))

	def AdoptBarWidget(self, widget_op, canonical_name, order=None, display=True,
					   source_registry=None):
		"""Take a panel that is ALREADY in the bar under registry management
		(TD's built-in icons), so it can be ordered, grouped and hidden like
		any published widget. Unlike RegisterWidget this never creates a
		mirror -- see _applyAdopted."""
		api = self._registryApi()
		if api is not self:
			return api.AdoptBarWidget(widget_op, canonical_name, order=order,
									  display=display, source_registry=source_registry)
		err = self._validateWidget(widget_op)
		if err:
			debug(f'{self.REGISTRY_NAME}: AdoptBarWidget({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
			'adopted': '1',
		}
		norm = self._normalizeMenuOrder(order)
		if norm is not None:
			entry['menu_order'] = norm
		# deliberately NO source_registry: an adopted icon is not published by
		# a host, and recording one couples it to whatever host did the
		# adopting -- which publishes its own widget (see _writeBackHostPar).
		self.stored['PaneRegistry'][canonical_name] = entry
		self._syncSurface()
		return canonical_name

	def _injectGroupStart(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""The group's switch: a narrow chevron button that collapses or
		expands everything up to the matching end cap."""
		name = self._mirrorName(canonical)
		fresh = bar.op(name) is None
		mirror = self._buildGroupToggleWidget(bar, name, info)
		mirror.tags.add(self.MIRROR_TAG)
		if fresh:
			siblings = bar.ops(self.MIRROR_PREFIX + '*')
			mirror.nodeX = 500 + (len(siblings) - 1) * 200
			mirror.nodeY = -700
		self._setConst(mirror.par.w, self._groupToggleWidth(info))
		self._setConst(mirror.par.h, self.BAR_ICON_HEIGHT)
		self._anchorMirror(mirror, bar)
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(mirror.par.alignorder,
					   self.MIRROR_ORDER_BASE + self._barOrder(info, seq_index))

	def _injectGroupEnd(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""The closing bracket is STRUCTURE ONLY -- it marks where the group
		ends in the sequence and is never drawn. The group's extent already
		reads from its collapse behaviour and from the tree, so a tick in the
		bar is only clutter. Anything an earlier build left behind is cleaned
		up here."""
		stale = bar.op(self._mirrorName(canonical))
		if stale is not None and self.MIRROR_TAG in stale.tags:
			stale.destroy()

	def _injectDivider(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""Virtual divider: a registry-owned blank panel -- no source widget."""
		name = self._mirrorName(canonical)
		mirror = bar.op(name)
		if mirror is not None and mirror.OPType != 'containerCOMP':
			mirror.destroy()
			mirror = None
		if mirror is None:
			mirror = bar.create(containerCOMP, name)
			mirror.tags.add(self.MIRROR_TAG)
			siblings = bar.ops(self.MIRROR_PREFIX + '*')
			mirror.nodeX = 500 + (len(siblings) - 1) * 200
			mirror.nodeY = -700
		try:
			self._setConst(mirror.par.w, max(1, int(info.get('width', '3') or 3)))
		except (TypeError, ValueError):
			self._setConst(mirror.par.w, 3)
		self._setConst(mirror.par.h, self.BAR_ICON_HEIGHT)
		self._setConst(mirror.par.bgalpha, 0)
		self._anchorMirror(mirror, bar)
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(mirror.par.alignorder,
					   self.MIRROR_ORDER_BASE + self._barOrder(info, seq_index))

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
		self._ensureGroupMarkers()
		self._pruneMirrors()
		names = self._registeredNamesInOrder()
		ancestors, _ = self._scanGroups(names)
		for i, canonical in enumerate(names):
			self._injectWidget(canonical, i, ancestors.get(canonical, ()))
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
					   callback=None, source_registry=None, width=None, help_url=None):
		"""Publish a panel COMP as a toolbar widget under canonical_name."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterWidget(
					widget_op, canonical_name, order=order, display=display,
					callback=callback, source_registry=source_registry, width=width,
					help_url=help_url)
			debug(f'{self.REGISTRY_NAME}: RegisterWidget ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		err = self._validateWidget(widget_op)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterWidget({canonical_name!r}) rejected: {err}')
			return
		try:
			if int(widget_op.height) != self.BAR_ICON_HEIGHT:
				debug(f'{self.REGISTRY_NAME}: {canonical_name!r} widget is {int(widget_op.height)}px tall; '
					  f'the bar renders it at {self.BAR_ICON_HEIGHT}px')
		except Exception:
			pass
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
		}
		norm_order = self._normalizeMenuOrder(order)
		if norm_order is not None:
			entry['menu_order'] = norm_order
		try:
			if width and int(width) > 0:
				entry['width'] = str(max(1, min(int(width), 800)))
		except (TypeError, ValueError):
			pass
		if help_url:
			entry['help_url'] = str(help_url)
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
		self._writeBackHostPar(info, 'Displayed', 1 if visible else 0)
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

	def _writeBackHostPar(self, info, par_name, value):
		"""Persist a manager edit onto the entry's host publisher par
		(compare-before-set so host callbacks do not storm).

		ADOPTED entries are excluded: TD's built-ins have no host publisher of
		their own -- the Configurator persists them in its state table. Their
		source_registry merely records which host adopted them, and that host
		publishes its OWN widget, so writing back stomps that widget's
		Registration pars. Hiding a TD icon switched the gear's Displayed off
		exactly this way, and SetWidgetSequence would have done the same to
		its Menuorder."""
		if info.get('adopted') == '1':
			return
		src_reg = self._resolveSourceRegistry(info)
		if src_reg is None:
			return
		p = getattr(src_reg.par, par_name, None)
		if p is None:
			return
		try:
			if str(p.eval()) != str(value):
				p.val = value
		except Exception:
			pass

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
		for name, info in entries.items():
			if 'menu_order' in info:
				self._writeBackHostPar(info, 'Menuorder', info['menu_order'])
		self._syncSurface()

	DIVIDER_TAG = 'ToolbarRegistryDivider'

	def SetWidgetWidth(self, canonical_name, width):
		"""Manager API: override any entry's bar width (applied to the MIRROR,
		matchsize off -- the source widget's own size is never touched).
		width None/0/'' clears the override back to auto-match."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetWidth(canonical_name, width)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		if width in (None, '', 0, '0'):
			info.pop('width', None)
			self._writeBackHostPar(info, 'Barwidth', 0)
		else:
			try:
				info['width'] = str(max(1, min(int(width), 800)))
			except (TypeError, ValueError):
				return False
			self._writeBackHostPar(info, 'Barwidth', info['width'])
		self._syncSurface()
		return True

	# Back-compat alias (0.3.x): dividers now use the same entry override.
	def SetDividerWidth(self, canonical_name, width):
		return self.SetWidgetWidth(canonical_name, width)

	def RegisterDivider(self, canonical_name, order=None, width=None, display=True):
		"""Publish a VIRTUAL divider -- a registry-owned blank separator with
		no backing widget. Works anywhere the registry works. Persistence is
		the publisher's job (the Toolbar Configurator owns its dividers)."""
		api = self._registryApi()
		if api is not self:
			return api.RegisterDivider(canonical_name, order=order, width=width, display=display)
		entry = {'virtual': '1', 'divider': '1',
				 'display': '1' if display else '0'}
		try:
			entry['width'] = str(max(1, min(int(width), 400))) if width else '3'
		except (TypeError, ValueError):
			entry['width'] = '3'
		norm = self._normalizeMenuOrder(order)
		if norm is not None:
			entry['menu_order'] = norm
		self.stored['PaneRegistry'][canonical_name] = entry
		if self._barReady():
			self._injectWidget(canonical_name)
		elif not self._pane_sync_queued:
			self._syncSurface()
		return canonical_name

	def AddDivider(self, after=None, width=None):
		"""Manager API: insert a new virtual divider after the given
		canonical name (or at the end)."""
		api = self._registryApi()
		if api is not self:
			return api.AddDivider(after=after, width=width)
		i = 1
		while f'DividerX{i}' in self.stored['PaneRegistry']:
			i += 1
		canonical = f'DividerX{i}'
		seq = self._registeredNamesInOrder()
		if after in seq:
			seq.insert(seq.index(after) + 1, canonical)
		else:
			seq.append(canonical)
		self.RegisterDivider(canonical, width=width)
		self.SetWidgetSequence(seq)
		return canonical

	def RemoveDivider(self, canonical_name):
		"""Manager API: remove a divider (virtual, or a legacy widget-based
		one, which also destroys its DIVIDER_TAG-owned widget)."""
		api = self._registryApi()
		if api is not self:
			return api.RemoveDivider(canonical_name)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		if self._isDividerEntry(info):
			self.UnregisterWidget(canonical_name)
			return True
		w = self._resolvePanelOp(info)
		if w is not None and self.DIVIDER_TAG in w.tags:
			self.UnregisterWidget(canonical_name)
			w.destroy()
			return True
		debug(f'{self.REGISTRY_NAME}: RemoveDivider refused -- {canonical_name!r} is not a divider')
		return False

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
		bar_width = None
		if hasattr(self.ownerComp.par, 'Barwidth'):
			try:
				bw = int(self.ownerComp.par.Barwidth.eval())
				bar_width = bw if bw > 0 else None
			except (TypeError, ValueError):
				pass
		api.RegisterWidget(
			widget, canonical,
			order=self._hostMenuOrder(),
			display=display,
			callback=self._hostCallbackDat(),
			source_registry=self.ownerComp,
			width=bar_width,
			help_url=self._hostHelpUrl(widget),
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {widget.path}')
		self._ensureToolRegistryPage()

	def _hostHelpUrl(self, widget):
		"""The tool's self-reported wiki page: the host's Helpurl par when
		set, else auto-discovered from the registered panel or its parent --
		either a docsHelper COMP (its Url par) or a Url/Wikipage custom par
		on the panel itself (both pre-registry self-reporting conventions)."""
		if hasattr(self.ownerComp.par, 'Helpurl'):
			u = str(self.ownerComp.par.Helpurl.eval()).strip()
			if u:
				return u
		for holder in (widget, widget.parent()):
			if holder is None:
				continue
			dh = holder.op('docsHelper')
			if dh is not None and hasattr(dh.par, 'Url'):
				u = str(dh.par.Url.eval()).strip()
				if u:
					return u
			for par_name in ('Url', 'Helpurl', 'Wikipage'):
				p = getattr(holder.par, par_name, None)
				if p is not None and p.isCustom:
					u = str(p.eval()).strip()
					if u:
						return u
		return None

	def OpenDocs(self, canonical_name):
		"""Open the tool's self-reported wiki/help page, if it has one."""
		api = self._registryApi()
		if api is not self:
			return api.OpenDocs(canonical_name)
		info = self.stored['PaneRegistry'].get(canonical_name) or {}
		url = info.get('help_url')
		if not url:
			debug(f'{self.REGISTRY_NAME}: no help URL registered for {canonical_name!r}')
			return False
		ui.viewFile(url)
		return True

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
