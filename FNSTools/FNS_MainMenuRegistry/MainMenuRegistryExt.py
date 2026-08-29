

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class MainMenuRegistryExt(RegistryBase):
	SHORTCUT = 'FNS_MAINMENUREGISTRY'
	EXT_NAME = 'MainMenuRegistryExt'
	REGISTRY_NAME = 'FNS_MainMenuRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	# Createcallbacks first: make the callbacks DAT, turn registration on,
	# see the result, then tune (the OpMenu ordering).
	TOOL_PAGE_PREFIX = 'Mm'
	TOOL_PAGE_LABEL = 'Main Menu'
	TOOL_PAGE_PARS = ('Createcallbacks', 'Autoregister', 'Register', 'Regstatus',
					  'Menuorder', 'Align', 'Anchor', 'Displayed', 'Barwidth')

	MIRROR_PREFIX = 'mmitem_'
	MIRROR_TAG = 'MainMenuRegistryItem'
	CALLBACKS_NAME = 'mainmenu_callbacks'
	CALLBACKS_TEMPLATE = 'callbacks_template'
	# TD's main menu bar (File/Edit ... fps/gpu cluster). ONE bar, unlike
	# the pane bar -- so entries render as selectCOMP mirrors (the proven
	# toolbar pattern), never stamped copies.
	BAR_PATH = '/ui/dialogs/mainmenu'

	SIDES = ('left', 'right')

	SELECTPANEL_EXPR = (
		"op.FNS_MAINMENUREGISTRY.WidgetTarget({canonical!r}) "
		"if hasattr(op, 'FNS_MAINMENUREGISTRY') else None"
	)
	MIRROR_WIDTH_EXPR = (
		"(op.FNS_MAINMENUREGISTRY.WidgetTarget({canonical!r}).width "
		"if hasattr(op, 'FNS_MAINMENUREGISTRY') "
		"and op.FNS_MAINMENUREGISTRY.WidgetTarget({canonical!r}) is not None else 30)"
	)
	# Soft-enforced bar icon height: every stock main-menu item renders 19 px
	# tall (same convention as the bookmark bar); the source widget's own
	# size is never touched.
	BAR_ICON_HEIGHT = 19

	# --- surface hooks (RegistryBase contract) ---

	def _preInit(self):
		self._ensurePackageShortcut()

	def _ensurePackageShortcut(self):
		"""Re-assert the package's FNS_MAINMENU shortcut if it was lost.

		Suspects-tox save/reload flows can strip a package root's opshortcut;
		the clone expressions and OpenConfigurator resolve through it, so any
		registry instance that initializes inside the package restores it."""
		if hasattr(op, 'FNS_MAINMENU'):
			return
		parent = self.ownerComp.parent()
		while parent is not None and parent.path not in ('/',):
			if (parent.op('MainMenuConfigurator') is not None
					and parent.op('MainMenuRegistry') is not None):
				try:
					parent.par.opshortcut = 'FNS_MAINMENU'
				except Exception:
					pass
				return
			parent = parent.parent()

	def _ensureSelectionExecuteRole(self):
		# Main menu has no selection DAT; hosts just must not keep a parallel table.
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _decorateGroupMarkers(self, start_entry, end_entry, anchor_name):
		"""Both markers sit on the same side as the run they wrap -- a group
		cannot span the bar's fill pivot, so the pair inherits the side of
		the entry it is wrapping."""
		anchor = self.stored['PaneRegistry'].get(anchor_name) or {}
		side = anchor.get('side', 'right')
		for entry in (start_entry, end_entry):
			entry['side'] = side

	def _sanitizeStoredRegistry(self):
		"""Coerce legacy/foreign entry shapes: side always valid."""
		for name, info in list(self.stored['PaneRegistry'].items()):
			try:
				info = dict(info)
			except (TypeError, AttributeError):
				continue
			if info.get('side') not in self.SIDES:
				info['side'] = 'right'
				self.stored['PaneRegistry'][name] = info

	def _syncSurface(self, attempts=40):
		"""Idempotent: prune orphan mirrors, then ensure one managed mirror
		per registered entry, sided/ordered/shown per the central store.
		Defers until TD's main menu bar exists."""
		self._pane_sync_queued = False
		if self._barReady():
			self._ensureGroupMarkers()
			bar = self._bar()
			self._pruneMirrors()
			ancestors, _ = self._scanGroups(self._registeredNamesInOrder())
			layout = self._computeAlignLayout(bar)
			for canonical in self._registeredNamesInOrder():
				self._injectWidget(canonical, bar, layout,
								   ancestors.get(canonical, ()))
			return
		if attempts <= 0:
			debug(f'{self.REGISTRY_NAME}: menu bar never became available, skipping sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	# --- bar helpers ---

	def _bar(self):
		return op(self.BAR_PATH)

	def _packageComp(self):
		return getattr(op, 'FNS_MAINMENU', None)

	def _barReady(self):
		bar = self._bar()
		return bool(bar and bar.valid)

	def _mirrorName(self, canonical):
		return self.MIRROR_PREFIX + tdu.legalName(canonical)

	def _registeredNamesInOrder(self, side=None):
		"""Entries for a side ordered by menu_order (unordered last);
		side=None returns left entries then right entries."""
		entries = self.stored['PaneRegistry']
		if side is not None:
			ordered = []
			unordered = []
			for name, info in entries.items():
				if info.get('side', 'right') != side:
					continue
				order = self._normalizeMenuOrder(info.get('menu_order'))
				(ordered if order is not None else unordered).append((order, name))
			ordered.sort(key=lambda t: (t[0], t[1].lower()))
			return [n for _, n in ordered] + [n for _, n in unordered]
		return (self._registeredNamesInOrder('left')
				+ self._registeredNamesInOrder('right'))

	# --- alignorder allocation (the left/right mechanism) ---

	def _computeAlignLayout(self, bar):
		"""alignorder per canonical, computed from the bar's LIVE stock
		numbering. TD's own items are never renumbered: left entries subdivide
		the open interval between the last stock-left item and the fill pivot
		(stringfield, the stretchy spacer); right entries subdivide between
		the pivot and the first stock-right item (OpFamUI/update today).
		An entry carrying an `anchor` (a stock item's name) is pinned into
		the gap directly AFTER that item instead -- how projname keeps its
		historical slot between tutorials and startstop. Recomputed every
		sync, so stock renumbering in future TD builds heals on the next
		pass, and a vanished anchor falls back to the side band."""
		stock = []
		adopted = self._adoptedNames()
		for c in bar.children:
			if not c.isPanel or c.name.startswith(self.MIRROR_PREFIX):
				continue
			if self.MIRROR_TAG in c.tags:
				continue
			# an adopted stock item is OURS to place now -- leaving it in the
			# stock scan would make it both a fixed landmark and a positioned
			# entry, and the two would fight
			if c.name in adopted:
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
				continue  # the alignorder-0 cluster: the File/Edit menu strip, emptypanel
			stock.append((ao, hm, layer, c.name))
		# the pivot is the in-flow stretchy element (stringfield)
		fills = [ao for ao, hm, layer, n in stock if hm == 'fill' and layer == 0]
		pivot = min(fills) if fills else 4.0
		lefts = [ao for ao, hm, layer, n in stock if ao < pivot]
		rights = [ao for ao, hm, layer, n in stock if ao > pivot]
		left_lo = max(lefts) if lefts else pivot - 1.0
		right_hi = min(rights) if rights else pivot + 1.0
		stock_aos = sorted(ao for ao, hm, layer, n in stock)
		stock_by_name = {}
		for ao, hm, layer, n in stock:
			stock_by_name.setdefault(n, ao)
		entries = self.stored['PaneRegistry']

		def entry_anchor(name):
			an = (entries.get(name) or {}).get('anchor')
			return an if an and an in stock_by_name else None

		layout = {}
		left_names = [n for n in self._registeredNamesInOrder('left')
					  if entry_anchor(n) is None]
		for i, name in enumerate(left_names):
			layout[name] = left_lo + (pivot - left_lo) * (i + 1) / (len(left_names) + 1)
		right_names = [n for n in self._registeredNamesInOrder('right')
					   if entry_anchor(n) is None]
		for i, name in enumerate(right_names):
			layout[name] = pivot + (right_hi - pivot) * (i + 1) / (len(right_names) + 1)
		# anchored entries: subdivide the gap between the anchor and the next
		# stock item, in overall sequence order
		anchored = {}
		for name in self._registeredNamesInOrder():
			an = entry_anchor(name)
			if an is not None:
				anchored.setdefault(an, []).append(name)
		for an, names in anchored.items():
			lo = stock_by_name[an]
			higher = [x for x in stock_aos if x > lo]
			hi = min(higher) if higher else lo + 1.0
			for i, name in enumerate(names):
				layout[name] = lo + (hi - lo) * (i + 1) / (len(names) + 1)
		return layout

	# --- managed mirror lifecycle ---

	def WidgetTarget(self, canonical):
		"""Resolve the live source COMP for a registered canonical name.

		Mirrors' Select Panel parameters call this, so a moved or renamed
		widget heals on the next cook instead of leaving a dead path."""
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return None
		return self._resolvePanelOp(info)

	def _injectWidget(self, canonical, bar, layout, ancestors=()):
		info = self.stored['PaneRegistry'].get(canonical)
		if self._isGroupStart(info):
			self._injectGroupStart(canonical, info, bar, layout, ancestors)
			return
		if self._isGroupEnd(info):
			self._injectGroupEnd(canonical, info, bar, layout, ancestors)
			return
		if info.get('adopted') == '1':
			self._applyAdopted(canonical, info, bar, layout, ancestors)
			return
		widget = self.WidgetTarget(canonical)
		if widget is None:
			debug(f'{self.REGISTRY_NAME}: no live widget for {canonical!r}, skipping inject')
			return
		name = self._mirrorName(canonical)
		mirror = bar.op(name)
		if mirror is not None and mirror.OPType != 'selectCOMP':
			mirror.destroy()
			mirror = None
		if mirror is None:
			mirror = bar.create(selectCOMP, name)
			# create() in this project intermittently phantom-suffixes the
			# name; force the name we asked for so the next sync finds it.
			if mirror.name != name:
				mirror.name = name
			mirror.tags.add(self.MIRROR_TAG)
			siblings = bar.ops(self.MIRROR_PREFIX + '*')
			mirror.nodeX = 500 + (len(siblings) - 1) * 200
			mirror.nodeY = -700
		self._setExpr(mirror.par.selectpanel, self.SELECTPANEL_EXPR.format(canonical=canonical))
		# Mirrors own their geometry: height fills the bar, width follows
		# the source live unless the entry carries an override.
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
		self._mirrorDragDrop(mirror, widget)
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		ao = layout.get(canonical)
		if ao is not None:
			self._setConst(mirror.par.alignorder, round(ao, 3))

	def _injectGroupStart(self, canonical, info, bar, layout, ancestors=()):
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
		ao = layout.get(canonical)
		if ao is not None:
			self._setConst(mirror.par.alignorder, round(ao, 3))

	def _injectGroupEnd(self, canonical, info, bar, layout, ancestors=()):
		"""The closing bracket is STRUCTURE ONLY -- it marks where the group
		ends in the sequence and is never drawn. Anything an earlier build
		left behind is cleaned up here."""
		stale = bar.op(self._mirrorName(canonical))
		if stale is not None and self.MIRROR_TAG in stale.tags:
			stale.destroy()

	def _applyAdopted(self, canonical, info, bar, layout, ancestors=()):
		"""An ADOPTED entry is a panel that already lives in the bar -- TD's
		own items. It is managed IN PLACE: side/order/visibility are written
		straight onto the panel, and no mirror is made, because making one
		would show the thing twice."""
		o = self._resolvePanelOp(info)
		if o is None:
			return
		self._setConst(o.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		ao = layout.get(canonical)
		if ao is not None:
			self._setConst(o.par.alignorder, round(ao, 3))

	def AdoptBarWidget(self, widget_op, canonical_name, side='left', order=None,
					   display=True):
		"""Take a panel that is ALREADY in the bar under registry management
		(TD's built-in items), so it can be ordered, grouped and hidden like
		any published widget. Unlike RegisterWidget this never creates a
		mirror -- see _applyAdopted. NOT applied automatically: repositioning
		a stock main-menu item is an explicit user decision."""
		api = self._registryApi()
		if api is not self:
			return api.AdoptBarWidget(widget_op, canonical_name, side=side,
									  order=order, display=display)
		err = self._validateWidget(widget_op)
		if err:
			debug(f'{self.REGISTRY_NAME}: AdoptBarWidget({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
			'adopted': '1',
			'side': side if side in self.SIDES else 'left',
		}
		norm = self._normalizeMenuOrder(order)
		if norm is not None:
			entry['menu_order'] = norm
		# deliberately NO source_registry: an adopted item is not published by
		# a host, and recording one couples it to whatever host did the
		# adopting -- which publishes its own widget (see _writeBackHostPar).
		self.stored['PaneRegistry'][canonical_name] = entry
		self._syncSurface()
		return canonical_name

	def _adoptedNames(self):
		return {n for n, i in self.stored['PaneRegistry'].items()
				if i.get('adopted') == '1'}

	def _anchorMirror(self, mirror, bar):
		"""Wire the mirror's panel input to the bar's emptypanel -- every
		stock main-menu item carries exactly this wire, and unwired panels
		drop out of the bar's layout flow."""
		anchor = bar.op('emptypanel')
		if not anchor:
			return
		try:
			in_conn = mirror.inputCOMPConnectors[0]
			if not in_conn.connections:
				in_conn.connect(anchor.outputCOMPConnectors[0])
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: anchoring {mirror.path} failed: {e}')

	def _pruneMirrors(self):
		"""Drop mirrors whose canonical is no longer registered."""
		bar = self._bar()
		if not bar:
			return
		# Keep only entries that STILL RESOLVE (virtual entries -- dividers and
		# group markers -- have no backing op and are always kept). Keying off
		# raw stored keys let a DEAD entry shield its own mirror: TD does not
		# call onDestroyTD when a host dies inside its parent's subtree, so the
		# entry outlives the COMP and _syncSurface could never clear it.
		live = {self._mirrorName(c) for c, info in self.stored['PaneRegistry'].items()
				if str(info.get('virtual', '')) == '1' or self._resolvePanelOp(info) is not None}
		for mirror in bar.ops(self.MIRROR_PREFIX + '*'):
			if self.MIRROR_TAG in mirror.tags and mirror.name not in live:
				mirror.destroy()

	def OpenConfigurator(self):
		"""Open the MainMenu Configurator (lives in the FNS_MainMenu package)."""
		api = self._registryApi()
		if api is not self:
			return api.OpenConfigurator()
		cfg = getattr(op, 'MAINMENUCONFIG', None)
		if cfg is None:
			pkg = self._packageComp()
			cfg = pkg.op('MainMenuConfigurator') if pkg else None
		if cfg is None or not hasattr(cfg.ext, 'ConfiguratorExt'):
			debug(f'{self.REGISTRY_NAME}: no MainMenuConfigurator installed (needs the FNS_MainMenu package)')
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
		"""Base healing plus surface repair: re-inject any registered entry
		whose mirror is missing or stale. This is what makes a LATE-arriving
		bar work -- _syncSurface gives up after its retry budget, but the
		watch tick keeps checking and re-applies managed state."""
		super()._healRegistryEntries()
		if not self._is_sys_global() or not self._barReady():
			return
		self._ensureGroupMarkers()
		bar = self._bar()
		self._pruneMirrors()
		ancestors, _ = self._scanGroups(self._registeredNamesInOrder())
		layout = self._computeAlignLayout(bar)
		for canonical in self._registeredNamesInOrder():
			self._injectWidget(canonical, bar, layout, ancestors.get(canonical, ()))

	# Location-independent: resolves through the package's global shortcut,
	# evaluates to None (no clone, no warning) where it is absent.
	# _healHostClones and StampHost come from RegistryBase off these two.
	CLONE_EXPR = "op.FNS.op('FNS_MainMenuRegistry') if hasattr(op, 'FNS') else None"

	# --- entry lifecycle hooks (the tool's callbacks DAT) ---

	def _invokeHook(self, info, hook, *args):
		"""Call an optional hook on the entry's callbacks DAT (the tool-owned
		DAT the host's Callback par references). Every hook is optional and
		best-effort: a missing DAT or function is silent, a raising hook is
		reported and contained -- a broken callbacks DAT must never take the
		menu bar down."""
		dat = self._resolveCallbackDat(info)
		if dat is None:
			return
		try:
			fn = getattr(dat.module, hook, None)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: callbacks DAT {dat.path} failed to compile: {e}')
			return
		if not callable(fn):
			return
		try:
			fn(*args)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: {hook} on {dat.path} raised: {e}')

	# --- public API ---

	def RegisterWidget(self, widget_op, canonical_name, order=None, side=None,
					   display=True, callback=None, source_registry=None,
					   width=None, help_url=None, anchor=None):
		"""Publish a panel COMP as a main-menu item under canonical_name.

		side: 'left' packs after TD's left cluster (before the stretchy
		spacer), 'right' (default) before the OpFam/update corner.
		anchor: a stock bar item's name (e.g. 'tutorials') pins the entry
		into the gap directly after it, overriding the side band."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterWidget(
					widget_op, canonical_name, order=order, side=side,
					display=display, callback=callback,
					source_registry=source_registry, width=width,
					help_url=help_url, anchor=anchor)
			debug(f'{self.REGISTRY_NAME}: RegisterWidget ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		side = side if side in self.SIDES else 'right'
		err = self._validateWidget(widget_op)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterWidget({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
			'side': side,
		}
		if anchor:
			entry['anchor'] = str(anchor).strip()
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
		self.fnsLog(f'{self.REGISTRY_NAME}: registered widget "{canonical_name}" ({widget_op.path}, side={side})')
		# Fires on EVERY publish, including boot and healing re-applies --
		# hooks must be idempotent ("my entry is live", not "first time").
		self._invokeHook(entry, 'onRegistered', canonical_name, dict(entry))
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
			info = self.stored['PaneRegistry'].pop(canonical_name, None)
			self.fnsLog(f'{self.REGISTRY_NAME}: unregistered "{canonical_name}"')
			bar = self._bar()
			if bar:
				mirror = bar.op(self._mirrorName(canonical_name))
				if mirror and self.MIRROR_TAG in mirror.tags:
					mirror.destroy()
			self._invokeHook(info, 'onUnregistered', canonical_name)
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
		self._invokeHook(info, 'onDisplayChanged', canonical_name, bool(visible))
		self._syncSurface()

	def SetWidgetSide(self, canonical_name, side):
		"""Manager API: dock a widget left or right of the stretchy spacer."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetSide(canonical_name, side)
		if side not in self.SIDES:
			return False
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		info['side'] = side
		self._writeBackHostPar(info, 'Align', side)
		self._invokeHook(info, 'onSideChanged', canonical_name, side)
		self._syncSurface()
		return True

	def SetWidgetAnchor(self, canonical_name, stock_name):
		"""Manager API: pin an entry directly after a named stock bar item
		(e.g. 'tutorials'), overriding its side band. None/'' clears the pin
		back to the normal left/right allocation. The name is resolved live
		each sync -- a vanished anchor falls back to the band, and heals if
		the item comes back."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetAnchor(canonical_name, stock_name)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		if not stock_name:
			info.pop('anchor', None)
			self._writeBackHostPar(info, 'Anchor', '')
		else:
			info['anchor'] = str(stock_name).strip()
			self._writeBackHostPar(info, 'Anchor', info['anchor'])
		self._syncSurface()
		return True

	def SetWidgetWidth(self, canonical_name, width):
		"""Manager API: override an entry's bar width (applied to the MIRROR,
		matchsize off -- the source widget's own size is never touched).
		width None/0/'' clears the override back to live-follow."""
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

	@property
	def Widgets(self):
		"""Manager API: snapshot of all registered entries."""
		return {k: dict(v) for k, v in self.stored['PaneRegistry'].items()}

	@property
	def WidgetSequence(self):
		"""Manager API: canonical names -- left entries, then right entries."""
		api = self._registryApi()
		if api is not self:
			return api.WidgetSequence
		return self._registeredNamesInOrder()

	@property
	def SideSequences(self):
		"""Manager API: {'left': [...], 'right': [...]} names in order."""
		api = self._registryApi()
		if api is not self:
			return api.SideSequences
		return {side: self._registeredNamesInOrder(side) for side in self.SIDES}

	def SetWidgetSequence(self, canonical_names):
		"""Manager API: reassign order 1..N per side from the given sequence.
		Each entry keeps its side; its position among its OWN side's entries
		follows the order it appears in the list. Unknown names are ignored;
		entries missing from the list drop to the end of their side. One
		surface sync at the end -- the batch primitive a drag-reorder UI calls."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetSequence(canonical_names)
		entries = self.stored['PaneRegistry']
		counters = {side: 1 for side in self.SIDES}
		seen = set()
		for name in canonical_names:
			info = entries.get(name)
			if info is None or name in seen:
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
		(compare-before-set so host callbacks do not storm).

		ADOPTED entries are excluded: TD's built-ins have no host publisher of
		their own -- the Configurator persists them in its state table. Their
		source_registry merely records which host adopted them, and that host
		publishes its OWN widget, so writing back stomps that widget's
		Registration pars."""
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

	def _validateWidget(self, widget_op):
		if widget_op is None:
			return 'No widget COMP selected'
		if widget_op.family != 'COMP':
			return f'{widget_op.path} is not a COMP'
		if not widget_op.isPanel:
			return f'{widget_op.path} is not a Panel COMP (isPanel=False)'
		return None

	# --- host registration (Registration page), main-menu flavor ---

	def _hostSide(self):
		if hasattr(self.ownerComp.par, 'Align'):
			side = str(self.ownerComp.par.Align.eval())
			if side in self.SIDES:
				return side
		return 'right'

	def _hostAnchor(self):
		if hasattr(self.ownerComp.par, 'Anchor'):
			a = str(self.ownerComp.par.Anchor.eval() or '').strip()
			if a:
				return a
		return None

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
			side=self._hostSide(),
			display=display,
			callback=self._hostCallbackDat(),
			source_registry=self.ownerComp,
			width=bar_width,
			help_url=self._hostHelpUrl(widget),
			anchor=self._hostAnchor(),
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {widget.path}')
		self._ensureToolRegistryPage()

	def _hostHelpUrl(self, widget):
		"""The tool's docs page: the host's Helpurl par is the ONE local
		override, else derived from the enclosing package -- the same
		landed rule the manifest publishes (build_manifest._helpUrl). The
		pre-registry self-reporting ladder that used to live here
		(docsHelper Url / Url / Helpurl / Wikipage pars on the widget) was
		measured empty fleet-wide on 2026-08-26 and is retired: it never
		fired once, and it made every gear menu register no help link at
		all while the manifest carried a perfect one."""
		if hasattr(self.ownerComp.par, 'Helpurl'):
			u = str(self.ownerComp.par.Helpurl.eval()).strip()
			if u:
				return u
		return (self._packageHelpUrl(self.ownerComp)
				or self._packageHelpUrl(widget) or None)

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

	# --- callbacks DAT bootstrap ---

	def CreateCallbacks(self):
		"""Spawn a `mainmenu_callbacks` DAT into this host's tool and point
		the host's Callback parameter at it.

		The whole setup for a new publisher: pulse this, fill in the hooks
		you want, done. Idempotent -- if the tool already has one it is
		adopted (never overwritten), so pulsing again just repairs a
		Callback reference that came unset.
		"""
		# The TOOL is the host's parent component -- NOT _hostComp(), which on
		# this surface is the registered widget PANEL (e.g. a bare textCOMP);
		# the callbacks DAT belongs beside the host, inside the tool.
		tool = self.ownerComp.parent()
		if tool is None or not tool.valid or tool.path == '/':
			debug(f'{self.REGISTRY_NAME}: CreateCallbacks -- host has no tool parent')
			return None
		existing = tool.op(self.CALLBACKS_NAME)
		if existing is not None:
			dat = existing
			created = False
		else:
			template = self.ownerComp.op(self.CALLBACKS_TEMPLATE)
			if template is None:
				debug(f'{self.REGISTRY_NAME}: CreateCallbacks -- no {self.CALLBACKS_TEMPLATE!r} '
					  f'inside {self.ownerComp.path}')
				return None
			dat = tool.copy(template, name=self.CALLBACKS_NAME)
			# A copy could inherit a file binding or the template's tracker
			# identity -- without this every tool's callbacks would read
			# from, and save over, the one shared template.
			for par_name in ('file', 'syncfile', 'loadonstart', 'write'):
				p = getattr(dat.par, par_name, None)
				if p is not None:
					try:
						p.mode = ParMode.CONSTANT
						p.val = '' if par_name == 'file' else False
					except Exception:
						pass
			for tag in ('FNS_externalized', 'py', 'tdn', 'pi_suspect'):
				if tag in dat.tags:
					dat.tags.remove(tag)
			dat.nodeX = self.ownerComp.nodeX + self.ownerComp.nodeWidth + 200
			dat.nodeY = self.ownerComp.nodeY
			created = True
		# point the host at it (bare sibling name -- OP-ref pars on the host
		# resolve against the tool network, not the host's own children)
		cb_par = getattr(self.ownerComp.par, 'Callback', None)
		if cb_par is not None and cb_par.eval() is not dat:
			cb_par.val = dat.name
		if self._isAutoRegister():
			self._applyHostRegistration()
		debug(f'{self.REGISTRY_NAME}: {"created" if created else "adopted"} '
			  f'{dat.path} and wired it to {self.ownerComp.path}')
		return dat

	def onParCreatecallbacks(self, _par):
		self._hostExtFromPar(_par).CreateCallbacks()

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

	def onParAnchor(self, _par, _val, _prev):
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
