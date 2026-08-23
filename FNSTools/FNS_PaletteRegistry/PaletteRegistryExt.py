CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase

import json


class PaletteRegistryExt(RegistryBase):
	"""FNS_PaletteRegistry: tools contribute TABS to TouchDesigner's Palette
	Browser (/ui/dialogs/palette/palette), FNS registry-family shape.

	The surface is TD's own palette dialog. Its panel tree is 'emptypanel',
	a vertical top-to-bottom stack (spacing 2) whose children are placed by
	alignorder and whose stock 'list' is 'panelh - 32' tall -- the 32 px TD
	leaves free are exactly a folder-tab row. The /sys global owns that
	surface: it loads TD's shipped folderTabs widget into the free row
	('Palette' first, every contribution after it, ordered by Tab Order),
	and shows each contributed panel in the list's slot through a Select
	COMP mirror (fnspal_<canonical>, tag PaletteRegistryMirror) wired
	under emptypanel like the stock children. Nothing stock is copied,
	moved or re-expressed; the stock panels only get their display flag
	toggled while a contributed tab is selected.

	A contribution is a NATIVE PANEL COMP -- the registry knows nothing
	about web pages. A tool carries a stamped FNS_PaletteRegistry host
	whose Registration pars name the panel (Tab Panel, default the tool
	itself), and the registry sizes that panel to the tab slot while it is
	registered (w/h become SlotWidth()/SlotHeight() expressions, the
	originals are restored on unregister -- the same move TD's own dialog
	makes when it docks the palette through pane/palette). A Select COMP
	cannot push its size into its source, and a panel whose network parent
	is a plain baseCOMP has nothing to fill.

	Tab changes reach the contributing tool through its optional Callbacks
	DAT: onPaletteTab(canonical, previous) fires once per change, for every
	registered entry, so a tool sharing one panel across two tabs can route
	it. Mirrors are views: the tool's panel keeps its state (a Web Render's
	browser process included) across tab switches and across registry
	reinits -- the global rebuilds only the strip and the mirrors.

	Nothing about the surface is ever saved: /ui is rebuilt every open, the
	global re-injects on promotion, registration and heal.
	"""

	SHORTCUT = 'FNS_PALETTEREGISTRY'
	EXT_NAME = 'PaletteRegistryExt'
	REGISTRY_NAME = 'FNS_PaletteRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Pl'
	TOOL_PAGE_LABEL = 'Palette'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus', 'Displayed',
					  'Tablabel', 'Taborder')

	# Location-independent: resolves through the toolkit root's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	CLONE_EXPR = "op.FNS.op('FNS_PaletteRegistry') if hasattr(op, 'FNS') else None"
	PACKAGE_SHORTCUT = 'FNS'

	# --- the surface ---
	DIALOG_PATH = '/ui/dialogs/palette'
	PALETTE_PATH = '/ui/dialogs/palette/palette'
	STOCK_TAB = 'palette'
	STOCK_LABEL = 'Palette'
	# Stock panels hidden while a contributed tab shows (restored on the
	# stock tab and on removal). 'list' is the component browser; the
	# other three are TD's legacy bottom bar.
	STOCK_OPS = ('list', 'pathfield', 'explore', 'folder1')

	STRIP_NAME = 'fnspal_tabs'
	STRIP_EXEC_NAME = 'fnspal_tabs_exec'
	MIRROR_PREFIX = 'fnspal_'
	MIRROR_TAG = 'PaletteRegistryMirror'
	# TD's shipped Basic Widgets folderTabs: a wrapper container holding the
	# widgetCOMP. Loaded from the install at sync time so the registry ships
	# no widget of its own (hosts are copies of the master -- a shipped widget
	# would replicate into every tool).
	FOLDERTABS_TOX = 'Palette/UI/Basic Widgets/folderTabs.tox'
	TAB_H = 26
	# emptypanel stacks by alignorder: the hidden emptypanel2 is 0, the
	# hidden emptypanel1 is 1, 'list' is 3. The strip goes first, mirrors
	# stand where the list stacks (a mirror and the list never show together).
	STRIP_ALIGNORDER = 0.5
	MIRROR_ALIGNORDER = 2.5
	# The dialog is all layer 0 and its full-size emptypanel background paints
	# over later siblings; anything injected must draw above it.
	INJECT_LAYER = 1
	# Canonical name rules: menu names on the strip, so no spaces.
	_NAME_OK = staticmethod(lambda s: bool(s) and s.replace('_', '').replace('-', '').isalnum())

	SELECTPANEL_EXPR = ("op.FNS_PALETTEREGISTRY.PanelTarget({canonical!r}) "
						"if hasattr(op, 'FNS_PALETTEREGISTRY') else None")
	SLOT_W_EXPR = "op.FNS_PALETTEREGISTRY.SlotWidth() if hasattr(op, 'FNS_PALETTEREGISTRY') else {fallback}"
	SLOT_H_EXPR = "op.FNS_PALETTEREGISTRY.SlotHeight() if hasattr(op, 'FNS_PALETTEREGISTRY') else {fallback}"

	STRIP_EXEC_TEXT = (
		"# FNS_PaletteRegistry: the selected folder tab -> the registry.\n"
		"def onValueChange(par, prev):\n"
		"\treg = getattr(op, 'FNS_PALETTEREGISTRY', None)\n"
		"\tif reg is not None and hasattr(reg, 'ShowTab'):\n"
		"\t\treg.ShowTab(par.eval())\n"
		"\treturn\n"
	)

	# --- surface hooks (RegistryBase contract) ---

	def _preInit(self):
		self._current = self.STOCK_TAB
		# True while WE hold the stock panels hidden. Ownership must be
		# tracked, not inferred from _current: UnregisterTab resets the
		# current tab BEFORE it syncs, so the flag is the only honest record.
		self._stock_hidden = False

	def _syncSurface(self, attempts=40):
		"""Idempotent: strip present, one mirror per entry, orphans pruned,
		the strip's menu rebuilt, the current tab re-asserted. Defers until
		TD's palette dialog exists."""
		self._pane_sync_queued = False
		if not self._is_sys_global():
			return
		pal = self._palette()
		if pal is None or pal.op('list') is None or pal.op('emptypanel') is None:
			if attempts <= 0:
				debug(f'{self.REGISTRY_NAME}: palette dialog never became available, skipping sync')
				return
			self._pane_sync_queued = True
			run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
				self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)
			return
		# Nothing contributed: the registry owns NO surface. A strip carrying
		# only TD's own tab is noise, and it collides with whatever else lives
		# in the dialog's one free row -- TDXLU's legacy injector claims the
		# very same alignorder slot. Inert until the first RegisterTab.
		if not self._orderedNames(include_hidden=True):
			self._teardownSurface(pal)
			return
		self._ensureStrip(pal)
		self._pruneMirrors(pal)
		for canonical in self._orderedNames(include_hidden=True):
			self._injectMirror(canonical, pal)
		self._refreshStripMenu(pal)
		self._showTab(self._current, pal, announce=False)

	def _healRegistryEntries(self):
		super()._healRegistryEntries()
		if self._is_sys_global():
			self._syncSurface()

	def onDestroyTD(self):
		# The global going away (a newer version replacing it, or a plain
		# reinit): take the strip and the mirrors with it. They are views --
		# the tools' panels keep their state -- and postInit rebuilds them.
		if self._is_sys_global():
			try:
				self.RemoveSurface()
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: remove surface on destroy: {e}')
		super().onDestroyTD()

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

	def _validateTab(self, comp, canonical, panel):
		if comp is None:
			return 'no tool COMP'
		if not canonical:
			return 'empty canonical name'
		if not self._NAME_OK(canonical):
			return 'canonical name must be letters, digits, _ -'
		if canonical == self.STOCK_TAB:
			return f'{canonical!r} is TD\'s own tab'
		if panel is None:
			return 'no tab panel (set Tab Panel)'
		if not getattr(panel, 'isPanel', False):
			return 'tab panel is not a panel COMP'
		if panel.path.startswith('/sys') or panel.path.startswith('/ui'):
			return 'tab panel must live in the project, not under /sys or /ui'
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
		panel = self._parOp('Panel') or comp
		callback = self._hostCallbackDat()
		err = self._validateTab(comp, canonical, panel)
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
			comp, canonical, panel=panel,
			label=self._parStr('Tablabel') or canonical,
			order=self._parInt('Taborder', 50),
			displayed=self._parBool('Displayed', True),
			callback=callback,
			source_registry=self.ownerComp,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {panel.path}')
		self._ensureToolRegistryPage()

	# --- public API (global only; hosts forward) ---

	def RegisterTab(self, comp, canonical, panel=None, label='', order=50,
					displayed=True, callback=None, source_registry=None):
		"""Publish a tab: `panel` (a panel COMP in the project) is shown in
		the Palette Browser under a tab named `label`. `displayed` False
		registers the tab hidden (kept, off the strip) until someone shows
		it. `callback` is an optional DAT whose onPaletteTab(canonical,
		previous) fires on every tab change."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterTab(comp, canonical, panel=panel, label=label,
									   order=order, displayed=displayed,
									   callback=callback, source_registry=source_registry)
			debug(f'{self.REGISTRY_NAME}: RegisterTab ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return None
		if panel is None:
			panel = comp
		err = self._validateTab(comp, canonical, panel)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterTab({canonical!r}) rejected: {err}')
			return {'ok': False, 'why': err}
		entry = {
			'panel_path': panel.path,
			'panel_id': int(panel.id),
			'tool_path': comp.path,
			'tool_id': int(comp.id),
			'label': str(label or canonical),
			'order': str(int(order)),
			'displayed': '1' if displayed else '0',
		}
		if callback is not None:
			entry['callback_path'] = callback.path
			entry['callback_id'] = int(callback.id)
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		old = self.stored['PaneRegistry'].get(canonical)
		if old and old.get('orig_size') and self._resolvePanelOp(old) is panel:
			entry['orig_size'] = old['orig_size']       # re-register: keep the true original
		self.stored['PaneRegistry'][canonical] = entry
		self._sizePanel(canonical)
		self.fnsLog(f'{self.REGISTRY_NAME}: registered tab "{canonical}" ({panel.path})')
		self._syncSurface()
		return {'ok': True, 'name': canonical}

	def UnregisterTab(self, canonical):
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterTab(canonical)
			return
		if canonical in self.stored['PaneRegistry']:
			self._restorePanelSize(canonical)
			del self.stored['PaneRegistry'][canonical]
			self.fnsLog(f'{self.REGISTRY_NAME}: unregistered tab "{canonical}"')
			if self._current == canonical:
				self._current = self.STOCK_TAB
			self._syncSurface()

	# RegistryBase's host teardown and healing call this name on the API owner.
	UnregisterPanel = UnregisterTab

	def Tabs(self, include_hidden=False):
		"""Every tab, in strip order: TD's own Palette first, then the live
		contributions (an entry whose panel is gone is skipped, never shown
		broken). Hidden contributions are left out unless include_hidden."""
		api = self._registryApi()
		if api is not self:
			return api.Tabs(include_hidden=include_hidden)
		out = [{'name': self.STOCK_TAB, 'label': self.STOCK_LABEL, 'order': -1,
				'builtin': True, 'displayed': True}]
		for canonical in self._orderedNames(include_hidden=include_hidden):
			info = dict(self.stored['PaneRegistry'][canonical])
			out.append({
				'name': canonical,
				'label': info.get('label') or canonical,
				'order': int(info.get('order', 50)),
				'builtin': False,
				'displayed': str(info.get('displayed', '1')) != '0',
				'panel': info.get('panel_path'),
				'tool': info.get('tool_path'),
				'current': canonical == self._current,
			})
		return out

	def SetTabDisplayed(self, canonical, displayed):
		"""Show or hide a contributed tab; written back to the contributing
		host's Displayed par (compare-before-set) so it persists with the
		tool. TD's own tab cannot be hidden."""
		api = self._registryApi()
		if api is not self:
			return api.SetTabDisplayed(canonical, displayed)
		if canonical == self.STOCK_TAB:
			return {'ok': False, 'why': "TD's own tab cannot be hidden"}
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
		self._syncSurface()
		return {'ok': True, 'name': canonical, 'displayed': displayed, 'persisted': wrote_host}

	def ShowTab(self, canonical):
		"""Select a tab: TD's own ('palette') or a registered canonical."""
		api = self._registryApi()
		if api is not self:
			return api.ShowTab(canonical)
		pal = self._palette()
		if pal is None:
			return False
		return self._showTab(str(canonical or self.STOCK_TAB), pal)

	def CurrentTab(self):
		api = self._registryApi()
		if api is not self:
			return api.CurrentTab()
		return self._current

	def PanelTarget(self, canonical):
		"""Live panel for a tab (the mirrors' selectpanel expression)."""
		api = self._registryApi()
		if api is not self:
			return api.PanelTarget(canonical)
		info = self.stored['PaneRegistry'].get(canonical)
		return self._resolvePanelOp(info) if info else None

	def SlotWidth(self):
		"""Width of a tab's slot -- the palette column."""
		pal = op(self.PALETTE_PATH)
		return int(pal.width) if pal is not None and pal.width else 300

	def SlotHeight(self):
		"""Height of a tab's slot -- exactly where TD's own list stands."""
		pal = op(self.PALETTE_PATH)
		lst = pal.op('list') if pal is not None else None
		return int(lst.height) if lst is not None and lst.height else 1024

	def Resync(self):
		api = self._registryApi()
		if api is not self:
			return api.Resync()
		self._syncSurface()

	def RemoveSurface(self):
		"""Take the strip and every mirror out of the dialog and show the
		stock palette. Entries are kept; the next sync rebuilds."""
		api = self._registryApi()
		if api is not self:
			return api.RemoveSurface()
		pal = self._palette()
		if pal is None:
			return
		self._teardownSurface(pal, restore_stock=True)

	def _teardownSurface(self, pal, restore_stock=False):
		"""Destroy only OUR ops (fnspal_* carrying the mirror tag, plus the
		strip and its exec). The stock panels are put back only when WE hid
		them -- another injector sharing this dialog may legitimately own the
		stock display flags right now, and stamping them on would erase its
		view."""
		for o in list(pal.ops(self.MIRROR_PREFIX + '*')):
			if o.valid and (self.MIRROR_TAG in o.tags or o.name in (self.STRIP_NAME, self.STRIP_EXEC_NAME)):
				try:
					o.destroy()
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: remove {o.name}: {e}')
		if restore_stock or self._stock_hidden:
			self._showStock(pal, True)
		self._current = self.STOCK_TAB

	# --- the dialog ---

	def _palette(self):
		pal = op(self.PALETTE_PATH)
		return pal if (pal is not None and pal.valid) else None

	def _orderedNames(self, include_hidden=False):
		rows = []
		for canonical, info in self.stored['PaneRegistry'].items():
			info = dict(info)
			if self._resolvePanelOp(info) is None:
				continue
			if not include_hidden and str(info.get('displayed', '1')) == '0':
				continue
			rows.append((int(info.get('order', 50)), str(info.get('label') or canonical).lower(), canonical))
		rows.sort()
		return [r[2] for r in rows]

	def _mirrorName(self, canonical):
		return self.MIRROR_PREFIX + canonical

	def _anchor(self, panel_comp, pal):
		"""Wire the panel's COMP input to emptypanel -- how every stock child
		of the dialog joins its panel tree (an unwired panel never renders)."""
		bg = pal.op('emptypanel')
		if bg is None:
			return
		try:
			conn = panel_comp.inputCOMPConnectors[0]
			if not conn.connections:
				conn.connect(bg.outputCOMPConnectors[0])
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: anchoring {panel_comp.path}: {e}')

	def _ensureStrip(self, pal):
		strip = pal.op(self.STRIP_NAME)
		if strip is not None and strip.OPType != 'widgetCOMP':
			strip.destroy()
			strip = None
		if strip is None:
			path = app.samplesFolder + '/' + self.FOLDERTABS_TOX
			try:
				wrapper = pal.loadTox(path)
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: cannot load {path}: {e}')
				return None
			inner = next((o for o in wrapper.children if o.OPType == 'widgetCOMP'), None)
			if inner is None:
				debug(f'{self.REGISTRY_NAME}: {path} holds no widgetCOMP')
				wrapper.destroy()
				return None
			strip = pal.copy(inner, name=self.STRIP_NAME)
			wrapper.destroy()
			if strip.name != self.STRIP_NAME:
				strip.name = self.STRIP_NAME
			strip.tags.add(self.MIRROR_TAG)
			right = max((o.nodeX + o.nodeWidth for o in pal.children if o is not strip), default=0)
			strip.nodeX, strip.nodeY = right + 200, 0
			p = strip.par
			p.Folderdragtoreorder = False
			p.Folderusereorderscript = False
			p.Folderdeletebuttons = False
			p.Folderaddbutton = False
			p.Menulabels = self.STOCK_LABEL
			p.Menunames = self.STOCK_TAB
			p.Value0 = self.STOCK_TAB
			p.Default1 = self.STOCK_TAB
		self._setExpr(strip.par.w, 'parent().width')
		self._setConst(strip.par.h, self.TAB_H)
		self._setConst(strip.par.alignorder, self.STRIP_ALIGNORDER)
		self._setConst(strip.par.layer, self.INJECT_LAYER)
		self._anchor(strip, pal)
		ex = pal.op(self.STRIP_EXEC_NAME)
		if ex is None:
			ex = pal.create(parameterexecuteDAT, self.STRIP_EXEC_NAME)
			if ex.name != self.STRIP_EXEC_NAME:
				ex.name = self.STRIP_EXEC_NAME
			ex.tags.add(self.MIRROR_TAG)
			ex.nodeX, ex.nodeY = strip.nodeX, strip.nodeY - 200
		ex.par.op = self.STRIP_NAME
		ex.par.pars = 'Value0'
		ex.par.valuechange = True
		if ex.text != self.STRIP_EXEC_TEXT:
			ex.text = self.STRIP_EXEC_TEXT
		return strip

	def _refreshStripMenu(self, pal):
		strip = pal.op(self.STRIP_NAME)
		if strip is None:
			return
		names = [self.STOCK_TAB]
		labels = [self.STOCK_LABEL]
		for canonical in self._orderedNames():
			info = self.stored['PaneRegistry'][canonical]
			names.append(canonical)
			labels.append(str(info.get('label') or canonical).replace(' ', 'Â '))
		menu = ' '.join(names)
		lab = ' '.join(labels)
		if strip.par.Menunames.eval() != menu:
			strip.par.Menunames = menu
		if strip.par.Menulabels.eval() != lab:
			strip.par.Menulabels = lab
		if self._current not in names:
			self._current = self.STOCK_TAB

	def _injectMirror(self, canonical, pal):
		info = self.stored['PaneRegistry'].get(canonical)
		if not info or self._resolvePanelOp(info) is None:
			return
		name = self._mirrorName(canonical)
		mirror = pal.op(name)
		if mirror is not None and mirror.OPType != 'selectCOMP':
			mirror.destroy()
			mirror = None
		if mirror is None:
			mirror = pal.create(selectCOMP, name)
			if mirror.name != name:
				mirror.name = name
			mirror.tags.add(self.MIRROR_TAG)
			siblings = pal.ops(self.MIRROR_PREFIX + '*')
			strip = pal.op(self.STRIP_NAME)
			base_x = strip.nodeX if strip is not None else 0
			mirror.nodeX = base_x + 200 * max(0, len(siblings) - 2)
			mirror.nodeY = -400
		self._setExpr(mirror.par.selectpanel, self.SELECTPANEL_EXPR.format(canonical=canonical))
		self._setConst(mirror.par.matchsize, 0)
		self._setExpr(mirror.par.w, 'parent().width')
		self._setExpr(mirror.par.h, 'op("list").height')
		self._setConst(mirror.par.alignorder, self.MIRROR_ALIGNORDER)
		self._setConst(mirror.par.layer, self.INJECT_LAYER)
		self._anchor(mirror, pal)
		self._setConst(mirror.par.display, 1 if canonical == self._current else 0)

	def _pruneMirrors(self, pal):
		live = {self._mirrorName(c) for c in self.stored['PaneRegistry']}
		for o in list(pal.ops(self.MIRROR_PREFIX + '*')):
			if o.name in (self.STRIP_NAME, self.STRIP_EXEC_NAME):
				continue
			if self.MIRROR_TAG in o.tags and o.name not in live:
				o.destroy()

	def _showStock(self, pal, show):
		for n in self.STOCK_OPS:
			o = pal.op(n)
			if o is not None:
				self._setConst(o.par.display, 1 if show else 0)
		self._stock_hidden = not show

	def _showTab(self, name, pal, announce=True):
		"""Make `name` the visible tab: stock panels for TD's own tab, the
		matching mirror otherwise. Fires onPaletteTab on every entry's
		callbacks DAT when the tab actually changed."""
		names = [self.STOCK_TAB] + self._orderedNames()
		if name not in names:
			name = self.STOCK_TAB
		previous = self._current
		self._current = name
		native = name == self.STOCK_TAB
		self._showStock(pal, native)
		for canonical in self.stored['PaneRegistry']:
			m = pal.op(self._mirrorName(canonical))
			if m is not None:
				self._setConst(m.par.display, 1 if canonical == name else 0)
		strip = pal.op(self.STRIP_NAME)
		if strip is not None:
			try:
				if strip.par.Value0.eval() != name:
					strip.par.Value0 = name
			except Exception:
				pass
		if announce and previous != name:
			self._announceTab(name, previous)
		return True

	def _announceTab(self, name, previous):
		seen = set()
		for canonical, info in list(self.stored['PaneRegistry'].items()):
			dat = self._resolveCallbackDat(info)
			if dat is None or dat.id in seen:
				continue
			seen.add(dat.id)
			try:
				fn = getattr(dat.module, 'onPaletteTab', None)
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: callbacks DAT {dat.path} failed to compile: {e}')
				continue
			if callable(fn):
				try:
					fn(name, previous)
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: onPaletteTab on {dat.path}: {e}')

	# --- sizing the contributed panel to the slot ---

	def _sizePanel(self, canonical):
		info = self.stored['PaneRegistry'].get(canonical)
		panel = self._resolvePanelOp(info) if info else None
		if panel is None:
			return
		entry = dict(info)
		if not entry.get('orig_size'):
			orig = {}
			for axis in ('w', 'h'):
				p = getattr(panel.par, axis)
				orig[axis] = {'mode': str(p.mode), 'expr': p.expr or '', 'val': int(p.val or 0)}
			entry['orig_size'] = json.dumps(orig)
			self.stored['PaneRegistry'][canonical] = entry
		orig = json.loads(entry['orig_size'])
		for axis, template in (('w', self.SLOT_W_EXPR), ('h', self.SLOT_H_EXPR)):
			fallback = orig[axis]['val'] or (300 if axis == 'w' else 1024)
			self._setExpr(getattr(panel.par, axis), template.format(fallback=fallback))
		# the slot sizes it; a fill/anchor mode would fight the expression
		for axis in ('hmode', 'vmode'):
			self._setConst(getattr(panel.par, axis), 'fixed')

	def _restorePanelSize(self, canonical):
		info = self.stored['PaneRegistry'].get(canonical)
		panel = self._resolvePanelOp(info) if info else None
		if panel is None or not info.get('orig_size'):
			return
		try:
			orig = json.loads(info['orig_size'])
		except Exception:
			return
		for axis in ('w', 'h'):
			p = getattr(panel.par, axis)
			o = orig.get(axis) or {}
			try:
				if o.get('mode') == 'ParMode.EXPRESSION' and o.get('expr'):
					p.expr = o['expr']
				else:
					p.expr = None
					p.mode = ParMode.CONSTANT
					p.val = o.get('val', p.val)
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: restore {axis} on {panel.path}: {e}')

	# --- parameter callbacks (CustomParHelper) ---

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

	def onParPanel(self, _par, _val, _prev):
		self._reapply(_par)

	def onParCallback(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTablabel(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTaborder(self, _par, _val, _prev):
		self._reapply(_par)

	def onParDisplayed(self, _par, _val, _prev):
		self._reapply(_par)
