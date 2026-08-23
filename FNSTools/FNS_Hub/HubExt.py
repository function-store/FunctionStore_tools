"""FNS_Hub -- the toolkit's one-stop manager window.

The FNS main-menu button (this package's `select1`, published through the
MainMenu registry as canonical `FNS`) opens it. The hub renders whatever
FNS_HubRegistry says is a tab and holds NO tab knowledge of its own: the
registry injects one mirror/viewer per registered tab into `panel/tabs`
and calls RefreshTabs(); this extension only decides which one is shown,
keeps the folder-tab bar in step, and persists the user's tab order and
active tab (Hub page pars, roamed by the config registry).

Interaction model of the FNS button:
  left-click   Open()      the hub, on the last active tab
  right-click  OpenMenu()  a popMenu: every tab, then Settings / Install &
                           remove (the console's pages)
  drop         RouteDrop() a panel COMP dropped on the button (its main-menu
                           mirror forwards the drop) or on the hub window is
                           offered to every tab whose component implements
                           AcceptsDrop/PackageDrop -- the surface
                           configurators -- and the chosen one stamps its
                           registry host into the dropped COMP.

Exposure: only the shown tab's component is "live". A component that must
know (a Web Render burning a CEF process for nobody) implements
OnHubExposure(exposed) on its extension; a palette Web Browser (Active +
Address pars) has its Active switched directly.
"""

FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand')  # import

TAB_PREFIX = 'hubtab_'
CONSOLE_ITEMS = (('Settings', 'settings'), ('Install & remove', 'tools'))


class HubExt:

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self._exposed = set()
		self._opening = False
		# the window is closed at boot: every tab's content starts un-exposed
		# (a browser left Active in the tox would otherwise render for nobody)
		run('args[0].valid and args[0].extensionsReady and args[0].ext.HubExt._boot()',
			ownerComp, delayFrames=30, delayRef=op.TDResources)

	def _boot(self):
		self.RefreshTabs()
		if not self._windowOpen():
			self._unexposeAll(force=True)
		self._announceCommands(attempts=6)

	ANNOUNCE_RETRY_FRAMES = 120

	def _announceCommands(self, attempts=0):
		"""The command registry's init rescan can run before this extension
		has compiled, and this extension can boot before the registry is
		promoted -- so announce here, and re-try a bounded number of times
		until the registry actually lists the hub. Idempotent and cheap."""
		reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
		listed = False
		if reg is not None:
			ann = self.ownerComp.op('ExtUtils/FNSCommandAnnouncer')
			if ann is not None and hasattr(ann, 'Announce'):
				try:
					ann.Announce()
				except Exception as e:
					debug(f'FNS_Hub: command announce: {e}')
			try:
				me_ = self.ownerComp.path + '#'
				listed = any(str(c.get('key', '')).startswith(me_) for c in reg.Commands())
			except Exception:
				listed = False
		if not listed and attempts > 0:
			run('args[0].valid and args[0].extensionsReady and args[0].ext.HubExt._announceCommands(args[1])',
				self.ownerComp, attempts - 1, delayFrames=self.ANNOUNCE_RETRY_FRAMES, delayRef=op.TDResources)

	# --- quick-launch commands (FNS_CommandRegistry) ------------------------

	@FNSCommand.fns_command(label='Open FNS Hub')
	def OpenHub(self):
		"""Open the FNS Hub window: every registry's configurator, the console, and any tab a tool contributes."""
		return self.Open()

	@FNSCommand.fns_command(label='Open main-menu configurator')
	def OpenMainMenuConfigurator(self):
		"""Open FNS Hub on the Main Menu tab (the configurator lives in the hub)."""
		return self.Open(tab='mainmenu')

	# --- plumbing -----------------------------------------------------

	def _registry(self):
		reg = getattr(op, 'FNS_HUBREGISTRY', None)
		if reg is None or not reg.valid or not reg.extensionsReady:
			return None
		return reg

	def _tabsContainer(self):
		return self.ownerComp.op('panel/tabs')

	def _tabBar(self):
		return self.ownerComp.op('panel/tabbar')

	def _folderTabs(self):
		return self.ownerComp.op('panel/masterFolderTabs')

	def _barStyle(self):
		"""'rows' (the hub's wrapping bar) or 'strip' (TD's folder-tabs
		widget: one row, scroll arrows, drag-to-reorder) -- the Tab Bar par."""
		p = getattr(self.ownerComp.par, 'Tabbar', None)
		return str(p.eval()) if p is not None else 'rows'

	def _window(self):
		return self.ownerComp.op('window')

	# --- the tab bar: hub-owned, wraps into rows ---------------------------
	# One textCOMP per shown tab, copied from tab_template, laid out by the
	# bar's Grid Rows alignment (alignmax follows the bar width, the bar's
	# height follows the row count), so a long tab set wraps instead of
	# shrinking. Active = brighter label + accent underline. No close button:
	# hiding is the tool's `Shown in Hub` par or SetTabDisplayed, and every
	# hidden tab is offered back in the right-click menu.

	TAB_ACTIVE = {'bg': (0.25, 0.25, 0.25), 'font': (0.96, 0.96, 0.96), 'border': 'borderb'}
	TAB_IDLE = {'bg': (0.17, 0.17, 0.17), 'font': (0.62, 0.62, 0.62), 'border': 'off'}
	# per-tab tints (canonical -> (active, idle)); the console is the toolkit's
	# own page and reads differently from the tool tabs (Rows style only --
	# TD's strip widget has one look for every tab)
	TAB_TINTS = {
		'console': ({'bg': (0.36, 0.26, 0.12), 'font': (1.0, 0.92, 0.72), 'border': 'borderb'},
					{'bg': (0.23, 0.18, 0.11), 'font': (0.93, 0.72, 0.40), 'border': 'off'}),
	}
	TAB_TILE_STEP = 400

	def _rebuildTabBar(self, tabs):
		bar = self._tabBar()
		if bar is None:
			return
		tpl = bar.op('tab_template')
		tbl = bar.op('tabs_table')
		if tbl is not None:
			tbl.clear()
			tbl.appendRow(['name', 'label', 'tool'])
			for t in tabs:
				tbl.appendRow([t['name'], t['label'], t['tool']])
		# the bar's height expression follows this par (a DAT's row count
		# would not re-trigger a parameter expression; a par does)
		tc = getattr(bar.par, 'Tabcount', None)
		if tc is not None and int(tc.eval()) != len(tabs):
			tc.val = len(tabs)
		want = {}
		for i, t in enumerate(tabs):
			nm = 'tab_' + tdu.legalName(t['name'])
			want[nm] = (i, t)
		for c in list(bar.children):
			if c.OPType == 'textCOMP' and c.name.startswith('tab_') and c.name != 'tab_template' and c.name not in want:
				c.destroy()
		for nm, (i, t) in want.items():
			c = bar.op(nm)
			if c is None:
				if tpl is None:
					return
				c = bar.copy(tpl, name=nm)
				c.nodeY = -800
			c.nodeX = i * self.TAB_TILE_STEP
			if c.par.text.eval() != t['label']:
				c.par.text = t['label']
			if c.par.alignorder.eval() != i:
				c.par.alignorder = i
			if c.fetch('canonical', '') != t['name']:
				c.store('canonical', t['name'])
			if not c.par.display.eval():
				c.par.display = True

	def _styleTabs(self, active_name):
		bar = self._tabBar()
		if bar is None:
			return
		for c in bar.children:
			if not c.name.startswith('tab_') or c.name == 'tab_template':
				continue
			canonical = c.fetch('canonical', '')
			active, idle = self.TAB_TINTS.get(canonical, (self.TAB_ACTIVE, self.TAB_IDLE))
			st = active if canonical == active_name else idle
			r, g, b = st['bg']
			if (c.par.bgcolorr.eval(), c.par.bgcolorg.eval(), c.par.bgcolorb.eval()) != (r, g, b):
				c.par.bgcolorr, c.par.bgcolorg, c.par.bgcolorb = r, g, b
			r, g, b = st['font']
			if (c.par.fontcolorr.eval(), c.par.fontcolorg.eval(), c.par.fontcolorb.eval()) != (r, g, b):
				c.par.fontcolorr, c.par.fontcolorg, c.par.fontcolorb = r, g, b
			if c.par.bottomborder.eval() != st['border']:
				c.par.bottomborder = st['border']

	@staticmethod
	def _setConst(par, value):
		if par.mode != ParMode.CONSTANT or par.eval() != value:
			par.mode = ParMode.CONSTANT
			par.val = value

	def _orderedTabs(self, include_hidden=False):
		"""Registry order, overridden by the user's dragged order."""
		reg = self._registry()
		if reg is None:
			return []
		tabs = reg.Tabs(include_hidden=include_hidden)
		stored = self.ownerComp.par.Tabuserorder.eval().split()
		def key(t):
			if t['name'] in stored:
				return (stored.index(t['name']), 0, '')
			return (len(stored), t['order'], str(t['label']).lower())
		return sorted(tabs, key=key)

	def Tabs(self):
		"""The shown tabs, in bar order (dicts from FNS_HubRegistry.Tabs)."""
		return self._orderedTabs()

	# --- the tab bar ----------------------------------------------------

	def RefreshTabs(self):
		"""Rebuild the folder-tab bar from the registry and show the active
		tab. Called by the registry after every surface sync; idempotent."""
		tabs = self._orderedTabs()
		names = [t['name'] for t in tabs]
		style = self._barStyle()
		bar, mft = self._tabBar(), self._folderTabs()
		if bar is not None and bool(bar.par.display.eval()) != (style == 'rows'):
			bar.par.display = (style == 'rows')
		if mft is not None and bool(mft.par.display.eval()) != (style == 'strip'):
			mft.par.display = (style == 'strip')
		if style == 'strip' and mft is not None:
			self._setConst(mft.par.Menunames, '\n'.join(names))
			self._setConst(mft.par.Menulabels, '\n'.join(t['label'] for t in tabs))
		else:
			self._rebuildTabBar(tabs)
		hint = self.ownerComp.op('panel/tabs/hint')
		if hint is not None:
			hint.par.display = not names
		want = self.ownerComp.par.Activetab.eval()
		if want not in names:
			want = names[0] if names else ''
		self._showTab(want, tabs)
		return names

	def _showTab(self, name, tabs=None):
		tabs = tabs if tabs is not None else self._orderedTabs()
		active = next((t for t in tabs if t['name'] == name), None)
		child_name = active['child'] if active else ''
		cont = self._tabsContainer()
		if cont is not None:
			for c in cont.children:
				if c.name.startswith(TAB_PREFIX):
					show = (c.name == child_name)
					if bool(c.par.display.eval()) != show:
						c.par.display = show
		# exposure follows the WINDOW: a tab shown while the window is closed
		# (boot, a roamed Activetab landing) keeps its content dormant
		live = self._windowOpen()
		for t in tabs:
			self._expose(t, live and t is active)
		self._setConst(self.ownerComp.par.Activetab, name)
		if self._barStyle() == 'strip':
			mft = self._folderTabs()
			if mft is not None and name and mft.par.Value0.eval() != name:
				mft.par.Value0 = name
		else:
			self._styleTabs(name)

	def _windowOpen(self):
		if self._opening:
			return True
		w = self._window()
		return bool(w is not None and w.isOpen)

	def _expose(self, tab, on, force=False):
		comp = op(tab.get('tool'))
		if comp is None or not comp.valid:
			return
		key = comp.path
		if not force and on == (key in self._exposed):
			return
		hook = None
		try:
			for ext in comp.extensions or []:
				fn = getattr(ext, 'OnHubExposure', None)
				if callable(fn):
					hook = fn
					break
		except Exception:
			hook = None
		try:
			if on and tab.get('name') == 'console':
				self._serveConsole(comp)
			if hook is not None:
				hook(on)
			elif getattr(comp.par, 'Address', None) is not None:
				p = getattr(comp.par, 'Active', None)
				if p is not None and bool(p.eval()) != on:
					p.val = on
			# refresh-on-show, by capability (the tools_ui convention): a tool
			# carrying a Refresh pulse is pulsed as its tab becomes visible
			if on:
				r = getattr(comp.par, 'Refresh', None)
				if r is not None and r.style == 'Pulse':
					r.pulse()
		except Exception as e:
			debug(f'FNS_Hub: exposure hook on {comp.path}: {e}')
		if on:
			self._exposed.add(key)
		else:
			self._exposed.discard(key)

	def _serveConsole(self, browser):
		"""The Console tab is a viewer on FNS_Console's server, which only
		runs on demand and stops when idle: picking the tab must (re)start
		it, or the browser lands on a dead 127.0.0.1. Keeps the page's
		fragment (the console's own tab) when the address already points
		at the live server."""
		con = getattr(op, 'FNS_CONSOLE', None)
		if con is None or not hasattr(con, 'Serve'):
			return
		url = con.Serve()
		if not url:
			return
		addr = getattr(browser.par, 'Address', None)
		if addr is None:
			return
		cur = str(addr.eval())
		if not cur.startswith(url):
			addr.val = url
		else:
			rp = getattr(browser.par, 'Reload', None)   # same server: just make sure it is loaded
			if rp is not None and rp.style == 'Pulse':
				rp.pulse()

	def OnTabSelected(self, name):
		"""A tab on the bar was clicked (tabbar/tabs_exec)."""
		if name:
			self._showTab(name)

	def OpenTabParameters(self, index):
		"""Right-click on a tab: the owning tool's parameter window (the
		mappers are configured there). `index` = position on the bar."""
		tabs = self._orderedTabs()
		try:
			tool = op(tabs[int(index)]['tool'])
		except (IndexError, ValueError, TypeError):
			tool = None
		if tool is not None and tool.valid:
			tool.openParameters()
			return True
		return False

	def OnActivetabChanged(self, name):
		"""The Active Tab par changed from outside (a roamed value landing
		after boot, or a script) -- follow it. _showTab writes the par
		compare-before-set, so this never loops."""
		if name and name != self._shownName():
			self._showTab(name)

	def _shownName(self):
		cont = self._tabsContainer()
		if cont is None:
			return ''
		for t in self._orderedTabs():
			c = cont.op(t['child'])
			if c is not None and bool(c.par.display.eval()):
				return t['name']
		return ''

	def OnTabReorder(self, fromIndex, toIndex):
		"""Move a tab on the bar: the order persists on Tab User Order."""
		names = [t['name'] for t in self._orderedTabs()]
		if not (0 <= fromIndex < len(names)):
			return
		n = names.pop(fromIndex)
		names.insert(min(max(toIndex, 0), len(names)), n)
		self.ownerComp.par.Tabuserorder = ' '.join(names)
		self.RefreshTabs()

	def HiddenTabs(self):
		"""Registered tabs currently hidden (the right-click menu offers them back)."""
		return [t for t in self._orderedTabs(include_hidden=True) if not t['displayed']]

	def ShowTab(self, name, displayed=True):
		reg = self._registry()
		if reg is None:
			return {'ok': False, 'why': 'no hub registry'}
		return reg.SetTabDisplayed(name, displayed)

	# --- opening ----------------------------------------------------------

	def Open(self, tab=None):
		"""Open the window; `tab` = a canonical name to switch to (a hidden
		tab is shown again first)."""
		if tab:
			if tab not in [t['name'] for t in self._orderedTabs()]:
				self.ShowTab(tab, True)      # the registry re-syncs next frame
			self.ownerComp.par.Activetab = tab
		w = self._window()
		if w is not None:
			w.par.winopen.pulse()
		self._opening = True        # isOpen may lag the pulse by a frame
		try:
			self.RefreshTabs()
		finally:
			self._opening = False
		self._armCloseWatch()
		return {'ok': True, 'tab': self.ownerComp.par.Activetab.eval()}

	def Close(self):
		w = self._window()
		if w is not None:
			w.par.winclose.pulse()
		self._unexposeAll()
		return {'ok': True}

	def _unexposeAll(self, force=False):
		for t in self._orderedTabs(include_hidden=True):
			self._expose(t, False, force=force)

	# A windowCOMP has no close callback and the panel's `winopen` value
	# stays 0 under a windowCOMP, so while the window is open a once-a-second
	# tick watches isOpen; the moment it closes every tab is un-exposed (the
	# console's browser stops rendering) and the tick stops. Bounded: nothing
	# runs while the hub is closed.
	CLOSE_WATCH_FRAMES = 60

	def _armCloseWatch(self):
		if getattr(self, '_close_watch_armed', False):
			return
		self._close_watch_armed = True
		run('args[0].valid and args[0].extensionsReady and args[0].ext.HubExt._closeTick()',
			self.ownerComp, delayFrames=self.CLOSE_WATCH_FRAMES, delayRef=op.TDResources)

	def _closeTick(self):
		self._close_watch_armed = False
		w = self._window()
		if w is not None and w.isOpen:
			self._armCloseWatch()
			return
		self._unexposeAll()

	def OpenMenu(self):
		"""Right-click on the FNS button: jump straight to a tab, or to one
		of the console's pages."""
		tabs = self._orderedTabs()
		labels = [t['label'] for t in tabs]
		console = [lbl for lbl, _ in CONSOLE_ITEMS]
		hidden = self.HiddenTabs()
		show_items = ['Show ' + t['label'] for t in hidden]
		items = labels + console + show_items
		if not items:
			return
		dividers = []
		if labels and (console or show_items):
			dividers.append(labels[-1])
		if console and show_items:
			dividers.append(console[-1])
		details = {'tabs': {t['label']: t['name'] for t in tabs},
				   'show': {'Show ' + t['label']: t['name'] for t in hidden}}
		op.TDResources.op('popMenu').Open(
			items=items, callback=self._onMenu, callbackDetails=details,
			dividersAfterItems=dividers, autoClose=True)

	def _onMenu(self, info):
		item = info.get('item')
		details = info.get('details') or {}
		name = details.get('tabs', {}).get(item)
		if name:
			self.Open(tab=name)
			return
		name = details.get('show', {}).get(item)
		if name:
			self.Open(tab=name)       # a hidden tab is shown again, then opened
			return
		page = dict(CONSOLE_ITEMS).get(item)
		con = getattr(op, 'FNS_CONSOLE', None)
		if page and con is not None:
			con.Open(tab=page, panel=True)

	# --- drop-to-register -------------------------------------------------

	def AcceptsDrop(self, items):
		try:
			return any(self._isDroppable(i) for i in items)
		except Exception:
			return False

	def _isDroppable(self, item):
		if not isinstance(item, COMP) or not item.isPanel:
			return False
		me_ = self.ownerComp
		if item is me_ or item.path.startswith(me_.path + '/') or me_.path.startswith(item.path + '/'):
			return False
		return True

	def _dropTargets(self):
		"""Every tab whose component can package a drop (the configurators)."""
		out = []
		for t in self._orderedTabs(include_hidden=True):
			comp = op(t['tool'])
			if comp is None or not comp.valid or not comp.extensionsReady:
				continue
			try:
				exts = comp.extensions or []
			except Exception:
				exts = []
			for ext in exts:
				if callable(getattr(ext, 'PackageDrop', None)) and callable(getattr(ext, 'AcceptsDrop', None)):
					out.append((t['label'], comp))
					break
		return out

	def RouteDrop(self, items):
		"""Drop entry point (drop_callbacks). Nothing happens inside the
		drop-event stack: the choice and the stamping run a frame later."""
		paths = [i.path for i in items if self._isDroppable(i)]
		if not paths:
			return
		run('args[0].valid and args[0].extensionsReady and args[0].ext.HubExt._routeDrop(args[1])',
			self.ownerComp, paths, delayFrames=1, delayRef=op.TDResources)

	def _routeDrop(self, paths):
		comps = [c for c in (op(p) for p in paths) if c is not None and c.valid]
		if not comps:
			return
		targets = [(label, comp) for label, comp in self._dropTargets()
				   if any(comp.AcceptsDrop([c]) for c in comps)]
		if not targets:
			debug(f'FNS_Hub: no registry tab accepts {", ".join(c.path for c in comps)}')
			return
		if len(targets) == 1:
			self._stampInto(targets[0][1], comps)
			return
		details = {'targets': {label: comp.path for label, comp in targets},
				   'paths': [c.path for c in comps]}
		op.TDResources.op('popMenu').Open(
			items=[label for label, _ in targets], callback=self._onDropMenu,
			callbackDetails=details, autoClose=True, title='Register into')

	def _onDropMenu(self, info):
		details = info.get('details') or {}
		tpath = details.get('targets', {}).get(info.get('item'))
		target = op(tpath) if tpath else None
		comps = [c for c in (op(p) for p in details.get('paths', [])) if c is not None]
		if target is not None and comps:
			self._stampInto(target, comps)

	def _stampInto(self, target, comps):
		for c in comps:
			accepted = target.PackageDrop(c)
			debug(f'FNS_Hub: {c.path} -> {target.name}: {"accepted" if accepted else "rejected"}')

	# --- par callbacks (parexec on the Hub page) --------------------------

	def OnPulse(self, name):
		if name == 'Open':
			self.Open()
		elif name == 'Refreshtabs':
			self.RefreshTabs()

	def OnParChange(self, name, value):
		if name == 'Activetab':
			self.OnActivetabChanged(str(value))
		elif name == 'Tabbar':
			self.RefreshTabs()
