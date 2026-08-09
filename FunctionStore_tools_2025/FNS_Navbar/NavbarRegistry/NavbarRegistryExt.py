

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class NavbarRegistryExt(RegistryBase):
	SHORTCUT = 'NAVBARREGISTRY'
	EXT_NAME = 'NavbarRegistryExt'
	REGISTRY_NAME = 'NavbarRegistry'

	ITEM_PREFIX = 'nbitem_'
	ITEM_TAG = 'NavbarRegistryItem'
	# TD's pane bar: the default template plus one live bar per open pane.
	BAR_PATH = '/ui/dialogs/panebar/panebar_default'
	PANE_BARS_PATH = '/ui/panes/panebar'

	SIDES = ('left', 'right')
	KINDS = ('widget', 'overlay', 'logic')

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Nb'
	TOOL_PAGE_LABEL = 'Navbar'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus',
					  'Menuorder', 'Align', 'Displayed')

	# Widgets fill the bar's inner height (the same expression the legacy
	# installer's templates carried) -- context-correct in every pane bar.
	ITEM_HEIGHT_EXPR = ("me.panelParent().height - me.panelParent().par.marginb"
						" - me.panelParent().par.margint")

	# --- surface hooks (RegistryBase contract) ---

	def _preInit(self):
		self._ensurePackageShortcut()

	def _ensurePackageShortcut(self):
		"""Re-assert the navbar package's FNS_NAVBAR shortcut if it was lost.

		Suspects-tox save/reload flows can strip a package root's opshortcut;
		the clone expressions and OpenConfigurator resolve through it, so any
		registry instance that initializes inside the package restores it."""
		if hasattr(op, 'FNS_NAVBAR'):
			return
		parent = self.ownerComp.parent()
		while parent is not None and parent.path not in ('/',):
			c = parent.op('containers')
			if c is not None and c.op('parent_hierarchy') is not None:
				try:
					parent.par.opshortcut = 'FNS_NAVBAR'
				except Exception:
					pass
				return
			parent = parent.parent()

	def _ensureSelectionExecuteRole(self):
		# Navbar has no selection DAT; hosts just must not keep a parallel table.
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _sanitizeStoredRegistry(self):
		"""Coerce legacy/foreign entry shapes: side and kind always valid."""
		for name, info in list(self.stored['PaneRegistry'].items()):
			try:
				info = dict(info)
			except (TypeError, AttributeError):
				continue
			changed = False
			if info.get('side') not in self.SIDES:
				info['side'] = 'right'
				changed = True
			if info.get('kind') not in self.KINDS:
				info['kind'] = 'widget'
				changed = True
			if changed:
				self.stored['PaneRegistry'][name] = info

	def _syncSurface(self, attempts=40):
		"""Idempotent: for every pane bar, prune orphan items, then ensure one
		managed instance per registered entry, sided/ordered/shown per the
		central store. Defers until TD's default pane bar exists."""
		self._pane_sync_queued = False
		if self._barReady():
			for bar in self._bars():
				self._pruneItems(bar)
				layout = self._computeAlignLayout(bar)
				for canonical in self._registeredNamesInOrder():
					self._injectItem(canonical, bar, layout)
			return
		if attempts <= 0:
			debug(f'{self.REGISTRY_NAME}: pane bar never became available, skipping sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	# --- bar helpers ---

	def _defaultBar(self):
		return op(self.BAR_PATH)

	def _bars(self):
		"""Every live pane bar: the default template + one per open pane."""
		bars = []
		default = self._defaultBar()
		if default and default.valid:
			bars.append(default)
		holder = op(self.PANE_BARS_PATH)
		if holder:
			bars.extend(b for b in holder.ops('*') if b.valid and b.isCOMP)
		return bars

	def _navbarComp(self):
		return getattr(op, 'FNS_NAVBAR', None)

	def _barReady(self):
		bar = self._defaultBar()
		return bool(bar and bar.valid)

	def _itemName(self, canonical):
		return self.ITEM_PREFIX + tdu.legalName(canonical)

	def _registeredNamesInOrder(self, side=None):
		"""Widget entries for a side ordered by menu_order (unordered last);
		side=None returns left widgets, right widgets, then overlay/logic."""
		entries = self.stored['PaneRegistry']
		if side is not None:
			ordered = []
			unordered = []
			for name, info in entries.items():
				if info.get('kind', 'widget') != 'widget' or info.get('side', 'right') != side:
					continue
				order = self._normalizeMenuOrder(info.get('menu_order'))
				(ordered if order is not None else unordered).append((order, name))
			ordered.sort(key=lambda t: (t[0], t[1].lower()))
			return [n for _, n in ordered] + [n for _, n in unordered]
		others = sorted(n for n, i in entries.items() if i.get('kind', 'widget') != 'widget')
		return (self._registeredNamesInOrder('left')
				+ self._registeredNamesInOrder('right')
				+ others)

	# --- alignorder allocation (the left/right mechanism) ---

	def _computeAlignLayout(self, bar):
		"""alignorder per widget canonical, computed from the bar's LIVE stock
		numbering. TD's own items are never renumbered: left entries subdivide
		the open interval between the last stock-left item and the fill pivot
		(panenav, the stretchy path area); right entries subdivide between the
		pivot and the first stock-right item. Recomputed every sync, so stock
		renumbering in future TD builds heals on the next pass."""
		stock = []
		for c in bar.children:
			if not c.isPanel or c.name.startswith(self.ITEM_PREFIX):
				continue
			if self.ITEM_TAG in c.tags:
				continue
			try:
				if c.par.alignallow.eval() == 'ignore':
					continue
				ao = float(c.par.alignorder.eval())
				hm = c.par.hmode.eval()
				layer = c.par.layer.eval()
			except Exception:
				continue
			if ao <= 0:
				continue  # the alignorder-0 cluster: mode panels, overlays
			stock.append((ao, hm, layer))
		# the pivot is the in-flow stretchy element (panenav, the path area);
		# overlay fills ride layer > 0 and are excluded above via alignorder 0
		fills = [ao for ao, hm, layer in stock if hm == 'fill' and layer == 0]
		pivot = min(fills) if fills else 6.0
		lefts = [ao for ao, hm, layer in stock if ao < pivot]
		rights = [ao for ao, hm, layer in stock if ao > pivot]
		left_lo = max(lefts) if lefts else pivot - 1.0
		right_hi = min(rights) if rights else pivot + 1.0
		layout = {}
		left_names = self._registeredNamesInOrder('left')
		for i, name in enumerate(left_names):
			layout[name] = left_lo + (pivot - left_lo) * (i + 1) / (len(left_names) + 1)
		right_names = self._registeredNamesInOrder('right')
		for i, name in enumerate(right_names):
			layout[name] = pivot + (right_hi - pivot) * (i + 1) / (len(right_names) + 1)
		return layout

	# --- managed item lifecycle ---

	def WidgetTarget(self, canonical):
		"""Resolve the live source COMP for a registered canonical name."""
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return None
		return self._resolvePanelOp(info)

	def _injectItem(self, canonical, bar, layout):
		"""Ensure one managed copy of the entry's source inside this bar.

		Copies, not selectCOMP mirrors: every pane bar needs its OWN instance
		(a breadcrumb must show ITS pane's path), and two entry kinds are not
		mirrorable at all (click-through overlays, non-panel logic COMPs)."""
		info = self.stored['PaneRegistry'].get(canonical)
		source = self.WidgetTarget(canonical)
		if source is None:
			debug(f'{self.REGISTRY_NAME}: no live source for {canonical!r}, skipping inject')
			return
		kind = info.get('kind', 'widget')
		name = self._itemName(canonical)
		inst = bar.op(name)
		if inst is not None and (inst.OPType != source.OPType
								 or inst.fetch('nbsrc', None, search=False) != int(source.id)):
			inst.destroy()
			inst = None
		if inst is None:
			inst = bar.copy(source, name=name)
			inst.tags.add(self.ITEM_TAG)
			inst.store('nbsrc', int(source.id))
			inst.allowCooking = True
			inst.nodeX = 500 + (len(bar.ops(self.ITEM_PREFIX + '*')) - 1) * 200
			inst.nodeY = -700
			# sources carry their own registry host INSIDE them (each
			# component ships standalone); the bar copy must not -- the
			# /sys-or-/ui guard would neutralize it anyway, but keep
			# instances lean
			embedded = inst.op('NavbarRegistry')
			if embedded is not None:
				embedded.par.Autoregister = False
				embedded.destroy()
		if kind == 'logic':
			return  # presence is the whole contract
		self._anchorItem(inst, bar)
		# Display: an explicit manager hide wins; otherwise a template display
		# EXPRESSION (e.g. gating on the owning tool's shortcut) is preserved.
		p = inst.par.display
		if info.get('display', '1') == '0':
			self._setConst(p, 0)
		elif p.mode != ParMode.EXPRESSION:
			self._setConst(p, 1)
		if kind == 'widget':
			ao = layout.get(canonical)
			if ao is not None:
				self._setConst(inst.par.alignorder, round(ao, 3))
			self._setExpr(inst.par.h, self.ITEM_HEIGHT_EXPR)
			width = info.get('width', '')
			if width:
				try:
					self._setConst(inst.par.w, int(width))
				except (TypeError, ValueError):
					pass

	def _anchorItem(self, inst, bar):
		"""Wire the instance's panel input to the bar's emptypanel when it is
		unconnected -- unwired panels drop out of the pane bar's layout flow
		(same contract as the bookmark bar). Sources that carry their own
		wiring (e.g. the overlay's panenav input) are left untouched."""
		anchor = bar.op('emptypanel')
		if anchor is None:
			return
		try:
			in_conn = inst.inputCOMPConnectors[0]
			if not in_conn.connections:
				in_conn.connect(anchor.outputCOMPConnectors[0])
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: anchoring {inst.path} failed: {e}')

	def _pruneItems(self, bar):
		"""Drop managed items whose canonical is no longer registered."""
		live = {self._itemName(c) for c in self.stored['PaneRegistry']}
		for inst in bar.ops(self.ITEM_PREFIX + '*'):
			if self.ITEM_TAG in inst.tags and inst.name not in live:
				inst.destroy()

	def _destroyInstances(self, canonical):
		name = self._itemName(canonical)
		for bar in self._bars():
			inst = bar.op(name)
			if inst and self.ITEM_TAG in inst.tags:
				inst.destroy()

	def RefreshWidget(self, canonical):
		"""Manager API: re-stamp an entry's instances from its live source
		(after the source widget itself was edited)."""
		api = self._registryApi()
		if api is not self:
			return api.RefreshWidget(canonical)
		if canonical not in self.stored['PaneRegistry']:
			return False
		self._destroyInstances(canonical)
		self._syncSurface()
		return True

	def OpenConfigurator(self):
		"""Open the Navbar Configurator (lives in the FNS_Navbar package)."""
		api = self._registryApi()
		if api is not self:
			return api.OpenConfigurator()
		cfg = getattr(op, 'NAVBARCONFIG', None)
		if cfg is None:
			nb = self._navbarComp()
			cfg = nb.op('NavbarConfigurator') if nb else None
		if cfg is None or not hasattr(cfg.ext, 'ConfiguratorExt'):
			debug(f'{self.REGISTRY_NAME}: no NavbarConfigurator installed (needs the FNS_Navbar package)')
			return
		cfg.ext.ConfiguratorExt.Refresh()
		cfg.ext.ConfiguratorExt.Open()

	def _setExpr(self, par, expr):
		# Compare-before-set: the healing tick re-runs injection every few
		# seconds, so repeated identical writes must be free.
		if par.mode != ParMode.EXPRESSION or par.expr != expr:
			par.expr = expr

	def _setConst(self, par, value):
		if par.mode != ParMode.CONSTANT or par.eval() != value:
			par.val = value
			par.mode = ParMode.CONSTANT

	def _healRegistryEntries(self):
		"""Base healing plus surface repair: re-inject into every bar. This is
		what covers pane bars born AFTER the last sync -- splitting a pane
		creates a fresh panebar that the next watch tick populates."""
		super()._healRegistryEntries()
		if not self._is_sys_global() or not self._barReady():
			return
		for bar in self._bars():
			self._pruneItems(bar)
			layout = self._computeAlignLayout(bar)
			for canonical in self._registeredNamesInOrder():
				self._injectItem(canonical, bar, layout)
		self._healHostClones()

	# Location-independent: resolves through the navbar package's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	CLONE_EXPR = "op.FNS_NAVBAR.op('NavbarRegistry') if hasattr(op, 'FNS_NAVBAR') else None"

	def _healHostClones(self):
		"""Re-assert in-project cloning on tool hosts. Release flows scrub
		the clone par on shipped copies (pre_release); if a release tool
		scrubbed the LIVE host instead of a staged copy, this restores it."""
		nb = self._navbarComp()
		master = nb.op('NavbarRegistry') if nb else None
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

	def RegisterWidget(self, widget_op, canonical_name, order=None, side=None,
					   kind=None, display=True, callback=None,
					   source_registry=None, width=None, help_url=None):
		"""Publish a COMP as a navbar item under canonical_name.

		side: 'left' docks before the path area, 'right' (default) after it.
		kind: 'widget' (aligned panel), 'overlay' (out-of-flow panel, e.g. a
		click-through layer), 'logic' (non-panel COMP that just needs to run
		inside every pane bar)."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterWidget(
					widget_op, canonical_name, order=order, side=side, kind=kind,
					display=display, callback=callback,
					source_registry=source_registry, width=width, help_url=help_url)
			debug(f'{self.REGISTRY_NAME}: RegisterWidget ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		kind = kind if kind in self.KINDS else 'widget'
		side = side if side in self.SIDES else 'right'
		err = self._validateWidget(widget_op, kind)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterWidget({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
			'side': side,
			'kind': kind,
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
		prev = self.stored['PaneRegistry'].get(canonical_name)
		self.stored['PaneRegistry'][canonical_name] = entry
		if prev and prev.get('panel_id') != entry['panel_id']:
			self._destroyInstances(canonical_name)
		if self._barReady():
			self._syncSurface()
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
		if canonical_name in self.stored['PaneRegistry']:
			self._destroyInstances(canonical_name)
			self.stored['PaneRegistry'].pop(canonical_name, None)
			self._syncSurface()

	# RegistryBase healing calls self.UnregisterPanel(name); alias it.
	def UnregisterPanel(self, canonical_name):
		return self.UnregisterWidget(canonical_name)

	def SetWidgetOrder(self, canonical_name, order):
		"""Manager API: reposition a registered widget within its side."""
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
		self._writeBackHostPar(info, 'Menuorder', norm if norm is not None else -1)
		self._syncSurface()

	def SetWidgetDisplay(self, canonical_name, visible):
		"""Manager API: show or hide a registered item."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetDisplay(canonical_name, visible)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return
		info['display'] = '1' if visible else '0'
		self._writeBackHostPar(info, 'Displayed', 1 if visible else 0)
		self._syncSurface()

	def SetWidgetSide(self, canonical_name, side):
		"""Manager API: dock a widget left or right of the path area."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetSide(canonical_name, side)
		if side not in self.SIDES:
			return False
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info or info.get('kind', 'widget') != 'widget':
			return False
		info['side'] = side
		self._writeBackHostPar(info, 'Align', side)
		self._syncSurface()
		return True

	def SetWidgetWidth(self, canonical_name, width):
		"""Manager API: override a widget's bar width (applied to the managed
		copies; the source widget is never touched). None/0/'' clears the
		override back to the widget's own sizing."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetWidth(canonical_name, width)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		if width in (None, '', 0, '0'):
			had = info.pop('width', None)
			self._writeBackHostPar(info, 'Barwidth', 0)
			if had:
				# instances keep their copied width expr only via a re-stamp
				self._destroyInstances(canonical_name)
		else:
			try:
				info['width'] = str(max(1, min(int(width), 800)))
			except (TypeError, ValueError):
				return False
			self._writeBackHostPar(info, 'Barwidth', info['width'])
		self._syncSurface()
		return True

	@property
	def Widgets(self):
		"""Manager API: snapshot of all registered entries."""
		return {k: dict(v) for k, v in self.stored['PaneRegistry'].items()}

	@property
	def WidgetSequence(self):
		"""Manager API: canonical names -- left widgets, right widgets, then
		overlay/logic entries."""
		api = self._registryApi()
		if api is not self:
			return api.WidgetSequence
		return self._registeredNamesInOrder()

	@property
	def SideSequences(self):
		"""Manager API: {'left': [...], 'right': [...]} widget names in order."""
		api = self._registryApi()
		if api is not self:
			return api.SideSequences
		return {side: self._registeredNamesInOrder(side) for side in self.SIDES}

	def SetWidgetSequence(self, canonical_names):
		"""Manager API: reassign order 1..N per side from the given sequence.
		Each widget keeps its side; its position among its OWN side's widgets
		follows the order it appears in the list. Unknown names are ignored;
		widgets missing from the list drop to the end of their side. One
		surface sync at the end -- the batch primitive a drag-reorder UI calls."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetSequence(canonical_names)
		entries = self.stored['PaneRegistry']
		counters = {side: 1 for side in self.SIDES}
		seen = set()
		for name in canonical_names:
			info = entries.get(name)
			if info is None or info.get('kind', 'widget') != 'widget' or name in seen:
				continue
			side = info.get('side', 'right')
			info['menu_order'] = counters[side]
			counters[side] += 1
			seen.add(name)
		for side in self.SIDES:
			for name in self._registeredNamesInOrder(side):
				if name not in seen:
					entries[name]['menu_order'] = counters[side]
					counters[side] += 1
		for name, info in entries.items():
			if 'menu_order' in info:
				self._writeBackHostPar(info, 'Menuorder', info['menu_order'])
		self._syncSurface()

	def _writeBackHostPar(self, info, par_name, value):
		"""Persist a manager edit onto the entry's host publisher par
		(compare-before-set so host callbacks do not storm)."""
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

	def _validateWidget(self, widget_op, kind='widget'):
		if widget_op is None:
			return 'No source COMP selected'
		if widget_op.family != 'COMP':
			return f'{widget_op.path} is not a COMP'
		if kind != 'logic' and not widget_op.isPanel:
			return f'{widget_op.path} is not a Panel COMP (isPanel=False)'
		return None

	# --- host registration (Registration page), navbar flavor ---

	def _hostSide(self):
		if hasattr(self.ownerComp.par, 'Align'):
			side = str(self.ownerComp.par.Align.eval())
			if side in self.SIDES:
				return side
		return 'right'

	def _hostKind(self):
		if hasattr(self.ownerComp.par, 'Kind'):
			kind = str(self.ownerComp.par.Kind.eval())
			if kind in self.KINDS:
				return kind
		return 'widget'

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
			self._setRegStatus('Error: no source COMP')
			return
		canonical = self._hostCanonicalName()
		if not canonical:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus('Error: empty canonical name')
			return
		kind = self._hostKind()
		err = self._validateWidget(widget, kind)
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
			side=self._hostSide(),
			kind=kind,
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
		set, else auto-discovered from the registered COMP or its parent --
		either a docsHelper COMP (its Url par) or a Url/Wikipage custom par
		on the COMP itself (both pre-registry self-reporting conventions)."""
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

	def onParAlign(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParKind(self, _par, _val, _prev):
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
