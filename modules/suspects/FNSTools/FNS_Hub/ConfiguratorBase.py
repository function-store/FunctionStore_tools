"""ConfiguratorBase -- the one implementation behind every surface configurator
tab in FNS_Hub (Toolbar, Navbar, MainMenu, OpMenu).

A configurator is a native lister UI over a registry's manager API: it shows
the surface's entries in bar order, lets the user reorder (drag), show/hide,
group (bracket pairs) and -- where the surface has them -- flip sides, set
widths and add dividers. It owns exactly one piece of persistent state: the
`state` table (dividers, group brackets, adopted built-ins' order/display/
width and their original `td_order`), republished on every boot and roamed
through the hub's config_callbacks (SnapshotState / RestoreState). Everything
else on a bar is persisted by the publishing tool's own host parameters.

Extracted 2026-08-23 from three near-identical ConfiguratorExt copies
(Toolbar / Navbar / MainMenu). What differs between surfaces is expressed as
class attributes and a handful of hooks on a thin subclass:

  REGISTRY_SHORTCUT / REGISTRY_EXT / REGISTRY_NAME  which registry this drives
  BAR_PATH, ITEM_PREFIX, PANE_BARS_PATH           where the surface lives
  HAS_SIDES     entries carry a left/right side (navbar, main menu)
  HAS_KINDS     entries carry a kind: widget / overlay / logic (navbar)
  HAS_DIVIDERS  the configurator owns divider entries (toolbar)
  HAS_WIDTH     entries have a settable bar width (toolbar)
  HAS_GROUPS    bracket-pair groups are supported (all bars; not the OP menu)
  SUPPORTS_DROP drop-to-register stamps this surface's host (all bars)
  ADOPTS_BUILTINS  TD's own items are adopted into the managed sequence
  _adoptCandidates / _adoptCall / _seedFirstAdoption  how adoption happens

Every subclass lives next to this DAT inside FNS_Hub and imports it with
`ConfiguratorBase = mod('../ConfiguratorBase').ConfiguratorBase`.
"""


class ConfiguratorBase:

	# --- surface description (override per subclass) ---------------------
	CFG_NAME = 'Configurator'            # debug/log label
	REGISTRY_SHORTCUT = ''               # e.g. 'FNS_TOOLBARREGISTRY'
	REGISTRY_EXT = ''                    # e.g. 'ToolbarRegistryExt'
	REGISTRY_NAME = ''                   # e.g. 'FNS_ToolbarRegistry' (master + host name)
	BAR_PATH = ''                        # the TD surface this manages
	PANE_BARS_PATH = None                # extra bars to apply overrides to (navbar)
	ITEM_PREFIX = ''                     # the registry's mirror/copy prefix on the bar
	HUB_TAB = ''                         # canonical name of this configurator's hub tab
	ORIGIN_PANE = 'cfg_origin'           # floating network editor name for OpenOrigin
	PKG_LABEL = 'package'                # 'toolbar package' etc. (docs only)
	BUILTIN_NOUN = 'built-in items'      # restore dialog wording
	OWN_NOUN = 'items and groups'

	HAS_SIDES = False
	HAS_KINDS = False
	HAS_DIVIDERS = False
	HAS_WIDTH = False
	HAS_GROUPS = True
	SUPPORTS_DROP = True
	ADOPTS_BUILTINS = True
	# adoption filter flags (see _adoptableBuiltins)
	ADOPT_UNIQUE_ALIGNORDER = True
	ADOPT_LAYER0_ONLY = True
	ADOPT_SORT_BY_X = False

	DEFAULT_STATE = ()                   # rows seeded into an empty state table
	STATE_COLUMNS = ('target_group', 'group_id', 'label', 'anchor', 'side', 'td_order')
	STAMP_EXTRA_PARS = {}                # surface pars a stamped host gets (Align, Kind, ...)

	TREE_SEP = '/'
	TREE_ORDER_SEP = '~'

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self._ensureState()
		run('args[0]()', self._boot, delayFrames=90, delayRef=op.TDResources)

	def _log(self, msg):
		debug(f'{self.CFG_NAME}: {msg}')

	# --- state table ------------------------------------------------------

	def _stateDat(self):
		return self.ownerComp.op('state')

	def _ensureState(self):
		t = self._stateDat()
		if t is None:
			return
		if t.numRows < 2 and self.DEFAULT_STATE and not self.ownerComp.fetch('state_seeded', False):
			t.clear()
			t.appendRow(['kind', 'name', 'order', 'width', 'display'])
			for row in self.DEFAULT_STATE:
				t.appendRow(list(row))
			self.ownerComp.store('state_seeded', True)
		if t.numRows < 1:
			t.appendRow(['kind', 'name', 'order', 'width', 'display'])
		# migrations: columns later schemas added (tableDAT silently drops
		# cells for missing columns -- td_order was lost that way once)
		header = [c.val for c in t.row(0)]
		for col_name in self.STATE_COLUMNS:
			if col_name not in header:
				t.appendCol([col_name] + [''] * (t.numRows - 1))
		# groups used to be a per-entry tag with an auto switch; they are
		# bracket pairs now, so membership/switch rows are stale
		for stale in ('group_toggle', 'groupmember', 'self'):
			cell = t.findCell(stale, cols=['kind'])
			while cell is not None:
				t.deleteRow(cell.row)
				cell = t.findCell(stale, cols=['kind'])
		# collapse duplicate name rows (an older _writeState appended instead
		# of updating; latest non-empty cell wins)
		seen = {}
		r = 1
		while r < t.numRows:
			nm = t[r, 'name'].val
			if nm in seen:
				for col in ('order', 'width', 'display'):
					v = t[r, col].val
					if v:
						t[seen[nm], col] = v
				t.deleteRow(r)
				continue
			seen[nm] = r
			r += 1

	def _stateRowIndex(self, name):
		"""Row index for a name -- rows are keyed by the 'name' column,
		never by tableDAT's first-column row lookup."""
		t = self._stateDat()
		if t is None:
			return None
		cell = t.findCell(name, cols=['name'], caseSensitive=True)
		return cell.row if cell is not None else None

	def _stateRow(self, name):
		t = self._stateDat()
		r = self._stateRowIndex(name)
		if t is None or r is None:
			return None
		return {c.val: t[r, c.col].val for c in t.row(0)}

	def _writeState(self, kind, name, **cols):
		"""Append or update a state row against the table's ACTUAL current
		header -- not a hardcoded column list, so schema migrations are
		honored on the very first write for a name."""
		t = self._stateDat()
		if t is None:
			return
		r = self._stateRowIndex(name)
		if r is None:
			header = [c.val for c in t.row(0)]
			defaults = {'display': '1'}
			row = [kind if col == 'kind' else name if col == 'name'
				   else str(cols.get(col, defaults.get(col, ''))) for col in header]
			t.appendRow(row)
		else:
			for k, v in cols.items():
				t[r, k] = str(v)

	def _dropState(self, name):
		t = self._stateDat()
		r = self._stateRowIndex(name)
		if t is not None and r is not None:
			t.deleteRow(r)

	def _ownedKinds(self):
		kinds = ['groupstart', 'groupend']
		if self.HAS_DIVIDERS:
			kinds += ['divider', 'builtin']
		return tuple(kinds)

	def _ownedNames(self):
		t = self._stateDat()
		if t is None:
			return set()
		kinds = self._ownedKinds()
		return {t[r, 'name'].val for r in range(1, t.numRows) if t[r, 'kind'].val in kinds}

	def _ownedKind(self, info):
		if info.get('group_start') == '1':
			return 'groupstart'
		if info.get('group_end') == '1':
			return 'groupend'
		if info.get('adopted') == '1':
			return 'builtin'
		return 'divider'

	# --- boot: re-apply overrides, publish what this component owns -------

	def _boot(self, attempts=20):
		self._applyBuiltinOverrides()
		api = self._api()
		if api is None:
			if attempts > 0:
				run('args[0](args[1])', self._boot, attempts - 1,
					delayFrames=60, delayRef=op.TDResources)
			else:
				self._log('no registry found -- standalone (built-ins only) mode')
				self.Refresh()
			return
		self._publishOwned(api)
		self.Refresh()

	def _publishOwned(self, api):
		if self.HAS_DIVIDERS:
			t = self._stateDat()
			if t is not None:
				for r in range(1, t.numRows):
					if t[r, 'kind'].val != 'divider':
						continue
					name = t[r, 'name'].val
					order = t[r, 'order'].val
					width = t[r, 'width'].val
					display = t[r, 'display'].val != '0'
					api.RegisterDivider(name, order=int(order) if order else None,
										width=int(width) if width else None, display=display)
		if self.ADOPTS_BUILTINS:
			self._adoptBuiltins(api)
		self._reapplyStoredOrders(api)
		if self.HAS_GROUPS:
			self._republishGroupMarkers(api)

	def _bars(self):
		bars = []
		default = op(self.BAR_PATH) if self.BAR_PATH else None
		if default is not None:
			bars.append(default)
		if self.PANE_BARS_PATH:
			holder = op(self.PANE_BARS_PATH)
			if holder:
				bars.extend(b for b in holder.ops('*') if b.valid and b.isCOMP)
		return bars

	def _applyBuiltinOverrides(self):
		"""Overrides land on every bar this surface has (the navbar: the
		default template AND every live pane bar, so panes TD opens later
		inherit them)."""
		t = self._stateDat()
		if t is None:
			return
		for r in range(1, t.numRows):
			if t[r, 'kind'].val != 'builtin':
				continue
			for bar in self._bars():
				o = bar.op(t[r, 'name'].val)
				if o is None:
					continue
				try:
					if t[r, 'display'].val in ('0', '1'):
						o.par.display = int(t[r, 'display'].val)
					if self.HAS_WIDTH and t[r, 'width'].val:
						o.par.w = max(1, min(int(t[r, 'width'].val), 800))
				except Exception:
					pass

	# --- built-in adoption ---------------------------------------------------

	def _builtinWidgets(self):
		"""Stock items of the bar in the align flow that are not our
		mirrors/copies, in bar order."""
		bar = op(self.BAR_PATH) if self.BAR_PATH else None
		if bar is None:
			return []
		out = []
		for c in bar.children:
			if not c.isPanel or (self.ITEM_PREFIX and c.name.startswith(self.ITEM_PREFIX)):
				continue
			try:
				if c.par.alignallow.eval() == 'ignore':
					continue
				ao = float(c.par.alignorder.eval())
			except Exception:
				continue
			if ao <= 0:
				continue
			out.append((ao, c))
		out.sort(key=lambda t: t[0])
		return [c for _, c in out]

	def _adoptableBuiltins(self):
		"""Stock items safe to take over: fixed width, in the align flow,
		LEFT of the bar's fill pivot. ADOPT_LAYER0_ONLY / ADOPT_UNIQUE_ALIGNORDER
		tighten that (the pane bar's mode panels share alignorder 1.0 and
		its overlays ride layer 1); ADOPT_SORT_BY_X orders by live position
		instead of alignorder (the main menu's duplicate-alignorder pair)."""
		bar = op(self.BAR_PATH) if self.BAR_PATH else None
		if bar is None:
			return []
		rows, counts = [], {}
		pivot = None
		for c in bar.children:
			if not c.isPanel or (self.ITEM_PREFIX and c.name.startswith(self.ITEM_PREFIX)):
				continue
			try:
				if c.par.alignallow.eval() == 'ignore':
					continue
				ao = float(c.par.alignorder.eval())
				hm = c.par.hmode.eval()
				layer = int(c.par.layer.eval())
			except Exception:
				continue
			if ao <= 0:
				continue
			counts[ao] = counts.get(ao, 0) + 1
			rows.append((ao, hm, layer, c))
			if hm == 'fill' and layer == 0 and (pivot is None or ao < pivot):
				pivot = ao
		if pivot is None:
			return []
		out = [(ao, c) for ao, hm, layer, c in rows
			   if hm != 'fill' and ao < pivot
			   and (not self.ADOPT_LAYER0_ONLY or layer == 0)
			   and (not self.ADOPT_UNIQUE_ALIGNORDER or counts[ao] == 1)]
		if self.ADOPT_SORT_BY_X:
			out.sort(key=lambda t: t[1].x)
		else:
			out.sort(key=lambda t: t[0])
		return [c for _, c in out]

	def _adoptCandidates(self):
		"""Which stock items adoption considers (subclass hook)."""
		return self._adoptableBuiltins()

	def _adoptCall(self, api, o, stored, disp):
		"""The registry's adopt call for one item (signatures differ per
		registry -- subclass hook)."""
		raise NotImplementedError

	def _seedFirstAdoption(self, api, unordered, prev):
		"""First adoption: keep TD's items in the order TD had them, ahead
		of anything already there."""
		rest = [n for n in prev if n not in set(unordered)]
		api.SetWidgetSequence(unordered + rest)

	def _adoptBuiltins(self, api):
		"""Bring TD's stock items under management so they can be reordered,
		grouped and hidden like published entries. They are ADOPTED (managed
		in place by name), never stamped. Each item's original alignorder is
		recorded once as `td_order` so this is reversible."""
		if api is None:
			return
		existing = api.Widgets
		fresh = [o for o in self._adoptCandidates() if o.name not in existing]
		if not fresh:
			return
		prev = api.WidgetSequence
		unordered = []
		for o in fresh:
			row = self._stateRow(o.name) or {}
			disp = bool(o.par.display.eval()) if hasattr(o.par, 'display') else True
			td_order = row.get('td_order') or ''
			if not td_order:
				try:
					td_order = str(float(o.par.alignorder.eval()))
				except Exception:
					td_order = ''
			cols = {'display': 1 if disp else 0, 'td_order': td_order}
			if self.HAS_SIDES:
				cols['side'] = 'left'
			self._writeState('builtin', o.name, **cols)
			stored = (self._stateRow(o.name) or {}).get('order')
			self._adoptCall(api, o, int(stored) if stored else None, disp)
			if not stored:
				unordered.append(o.name)
		if unordered:
			self._seedFirstAdoption(api, unordered, prev)

	def PromptRestoreBuiltins(self):
		"""Right-click the TD button: offer to put TD's own items back."""
		api = self._api()
		if api is None:
			return
		n = sum(1 for i in api.Widgets.values() if i.get('adopted') == '1')
		if not n:
			return
		op.TDResources.PopDialog.OpenDefault(
			text=f"Put TouchDesigner's {n} {self.BUILTIN_NOUN} back to their "
				 f"original order, all visible and outside any group?\n\n"
				 f"Your own {self.OWN_NOUN} are left alone.",
			title='Restore TD Built-ins',
			buttons=['Restore', 'Cancel'],
			callback=self._onRestoreBuiltinsDialog,
			escButton=2, enterButton=1)

	def _onRestoreBuiltinsDialog(self, info):
		if info.get('buttonNum') == 1:
			self.RestoreBuiltinOrder()

	def RestoreBuiltinOrder(self):
		"""Put TD's items back: original order, visible, outside any group,
		while staying adopted so they can be rearranged again. Moving them to
		the front of the sequence is what un-groups them: membership is
		positional."""
		api = self._api()
		if api is None:
			return
		widgets = api.Widgets
		adopted = [n for n, i in widgets.items() if i.get('adopted') == '1']
		if not adopted:
			return

		def td_order(name):
			row = self._stateRow(name) or {}
			try:
				return float(row.get('td_order'))
			except (TypeError, ValueError):
				return float('inf')

		adopted.sort(key=td_order)
		for name in adopted:
			if widgets[name].get('display', '1') == '0':
				api.SetWidgetDisplay(name, True)
			self._writeState('builtin', name, display=1)
		rest = [n for n in api.WidgetSequence if n not in set(adopted)]
		self.PushSequence(adopted + rest)
		self._log(f'restored {len(adopted)} TD built-ins')

	# --- groups: bracket pairs this component owns --------------------------

	def _republishGroupMarkers(self, api, attempts=6):
		"""Re-create the group brackets around the entries they wrap, and
		re-apply each group's collapsed state.

		Only the MARKERS are restored -- membership is whatever ends up
		between them. Each bracket is re-inserted next to its anchor entry
		rather than at a stored index, because tool entries get their order
		back from their own host pars independently: an absolute slot would
		land the bracket wherever that slot happens to be this boot. A group
		whose anchors have not registered yet is retried."""
		t = self._stateDat()
		if t is None or api is None:
			return
		entries = api.stored['PaneRegistry']
		specs = {}
		for r in range(1, t.numRows):
			kind = t[r, 'kind'].val
			if kind not in ('groupstart', 'groupend'):
				continue
			gid = t[r, 'group_id'].val
			name = t[r, 'name'].val
			if not gid or not name:
				continue
			specs.setdefault(gid, {})[kind] = {
				'name': name, 'anchor': t[r, 'anchor'].val,
				'label': t[r, 'label'].val or gid, 'row': r}
		if not specs:
			return  # nothing owned -> never touch live markers
		pending = False
		for n, info in list(entries.items()):
			if api._isGroupMarker(info):
				entries.pop(n, None)
		base = api._registeredNamesInOrder()
		starts, ends = {}, {}
		for gid, spec in specs.items():
			s, e = spec.get('groupstart'), spec.get('groupend')
			if not s or not e:
				continue
			if s['anchor'] not in base or e['anchor'] not in base:
				pending = True  # the wrapped tools have not registered yet
				continue
			entries[s['name']] = {'virtual': '1', 'group_start': '1',
								  'group_id': gid, 'label': s['label'], 'display': '1'}
			entries[e['name']] = {'virtual': '1', 'group_end': '1',
								  'group_id': gid, 'display': '1'}
			self._decorateRestoredMarker(entries[s['name']], t, s['row'])
			self._decorateRestoredMarker(entries[e['name']], t, e['row'])
			starts.setdefault(s['anchor'], []).append((gid, s['name'], e['anchor']))
			ends.setdefault(e['anchor'], []).append((gid, e['name'], s['anchor']))
		# where several brackets share an anchor, the OUTER one opens first
		# and closes last -- order them by how far their partner reaches
		for lst in starts.values():
			lst.sort(key=lambda x: base.index(x[2]), reverse=True)
		for lst in ends.values():
			lst.sort(key=lambda x: base.index(x[2]), reverse=True)
		seq = []
		for n in base:
			for _gid, sname, _a in starts.get(n, []):
				seq.append(sname)
			seq.append(n)
			for _gid, ename, _a in ends.get(n, []):
				seq.append(ename)
		api.SetWidgetSequence(seq)
		for r in range(1, t.numRows):
			if t[r, 'kind'].val != 'group':
				continue
			gid = t[r, 'name'].val
			if not gid:
				continue
			visible = t[r, 'display'].val != '0'
			if api.GroupVisible(gid) != visible:
				api.SetGroupVisible(gid, visible)
		api._syncSurface()
		if pending and attempts > 0:
			run('args[0](args[1], args[2])', self._republishGroupMarkers, api,
				attempts - 1, delayFrames=60, delayRef=op.TDResources)

	def _decorateRestoredMarker(self, entry, table, row):
		"""A restored marker comes back on the side it was created on (a
		group cannot span a bar's fill pivot) and, on kinded surfaces, as an
		ordinary aligned widget."""
		if self.HAS_KINDS:
			entry['kind'] = 'widget'
		if self.HAS_SIDES:
			entry['side'] = table[row, 'side'].val or 'right'

	def _writeMarkerState(self, api, gid):
		"""Persist a group's brackets by the entries they WRAP, not by index
		(see _republishGroupMarkers)."""
		widgets = api.Widgets
		members = [m for m in (api.Groups.get(gid) or {}).get('members', [])
				   if not api._isGroupMarker(widgets.get(m))]
		if not members:
			# an emptied group has nothing to anchor to -- keep the stored
			# spec (the dormant-group contract) instead of blank anchors
			return
		anchors = {'groupstart': members[0], 'groupend': members[-1]}
		for kind, name in (('groupstart', api._groupStartName(gid)),
						   ('groupend', api._groupEndName(gid))):
			info = widgets.get(name, {})
			cols = dict(order=info.get('menu_order', ''), display='1', group_id=gid,
						label=info.get('label', ''), anchor=anchors[kind])
			if self.HAS_SIDES:
				cols['side'] = info.get('side', 'right')
			self._writeState(kind, name, **cols)

	# --- config roaming -----------------------------------------------------

	def RestoreState(self, rows=None):
		"""Replace the state table from a roamed config payload, then
		re-apply it to the live registry.

		The /sys global is ephemeral and a config payload lands well after
		`_boot` has already republished, so a restore has to redo everything
		boot does -- built-in overrides, dividers, stored order, group
		brackets -- not merely rewrite the table. Without that the bar keeps
		the old layout until the next start.

		rows -- full table INCLUDING the header row; omit to re-apply the
		table already in place.
		"""
		t = self._stateDat()
		if t is None:
			return False
		if rows:
			t.clear()
			for row in rows:
				t.appendRow([str(c) for c in row])
			self.ownerComp.store('state_seeded', True)
			self._ensureState()
		self._applyBuiltinOverrides()
		api = self._api()
		if api is None:
			return False
		if rows:
			self._retireDroppedDividers(api)
		self._publishOwned(api)
		self.Refresh()
		return True

	def SnapshotState(self):
		"""State-table rows for a roamed config payload (header included),
		with every LIVE group's collapsed state refreshed from the registry
		first -- the bar-side eye button writes only registry storage, so
		the registry is the single source of truth at snapshot time. A
		dormant group has no live record and keeps its stored row as-is."""
		t = self._stateDat()
		if t is None or t.numRows < 1:
			return []
		api = self._api()
		if api is not None and self.HAS_GROUPS:
			for gid in api.Groups:
				self._writeState('group', gid,
								 display=1 if api.GroupVisible(gid) else 0)
		return [[c.val for c in row] for row in t.rows()]

	def _retireDroppedDividers(self, api):
		"""A restore REPLACES the layout, so dividers the incoming table no
		longer lists are entries nothing owns any more.

		Deliberately asymmetric: builtins absent from the incoming table
		keep their current overrides -- a reset-to-TD-defaults pass would
		fight _applyBuiltinOverrides ordering for little gain."""
		remove = getattr(api, 'RemoveDivider', None)
		if remove is None:
			return
		keep = self._ownedNames()
		for name, info in api.Widgets.items():
			if info.get('divider') == '1' and name not in keep:
				remove(name)

	def _reapplyStoredOrders(self, api):
		"""Re-assert the state table's stored order for the entries THIS
		component owns.

		`_adoptBuiltins` applies a stored order only at adoption time and
		early-outs once every built-in is adopted, so a table arriving AFTER
		boot would otherwise leave TD's own icons wherever they were first
		adopted. Idempotent: on a normal boot the orders already match."""
		t = self._stateDat()
		if t is None or api is None:
			return
		stored = {}
		for r in range(1, t.numRows):
			if t[r, 'kind'].val not in ('divider', 'builtin'):
				continue
			try:
				stored[t[r, 'name'].val] = int(t[r, 'order'].val)
			except (TypeError, ValueError):
				continue
		if not stored:
			return
		widgets = api.Widgets
		live = [n for n in api._registeredNamesInOrder()
				if not api._isGroupMarker(widgets.get(n, {}))]
		if not any(n in stored for n in live):
			return
		keyed = []
		for i, name in enumerate(live):
			try:
				cur = int(widgets.get(name, {}).get('menu_order'))
			except (TypeError, ValueError):
				cur = i + 1
			keyed.append((stored.get(name, cur), i, name))
		keyed.sort()
		api.SetWidgetSequence([n for _, _, n in keyed])

	# --- registry access ------------------------------------------------------

	def _api(self):
		reg = getattr(op, self.REGISTRY_SHORTCUT, None) if self.REGISTRY_SHORTCUT else None
		if reg is not None and hasattr(reg.ext, self.REGISTRY_EXT):
			return getattr(reg.ext, self.REGISTRY_EXT)
		return None

	# --- list building ----------------------------------------------------------

	def _showBuiltins(self):
		if self._api() is None:
			return True  # standalone mode: built-ins are all there is
		b = self.ownerComp.op('topbar/btn_builtin')
		try:
			return bool(b.panel.state) if b is not None else False
		except Exception:
			return False

	def _originOf(self, info):
		src = info.get('source_registry', '')
		parts = [p for p in src.split('/') if p]
		return parts[-2] if len(parts) >= 2 else 'chrome'

	def _widthOf(self, api, name, info):
		override = info.get('width', '')
		if override:
			return override + ('' if info.get('divider') == '1' else '*')
		w = api.WidgetTarget(name)
		try:
			return str(int(w.width)) if w is not None else ''
		except Exception:
			return ''

	def _entryColumns(self):
		cols = ['Name']
		if self.HAS_SIDES:
			cols.append('Side')
		cols.append('Show')
		if self.HAS_WIDTH:
			cols.append('Width')
		cols += ['Group', 'Origin']
		return cols

	def _entryRow(self, api, name, info, groups, label=None, side=None):
		"""One row for the entries table, in _entryColumns() order."""
		is_start = info.get('group_start') == '1'
		is_end = info.get('group_end') == '1'
		kind = info.get('kind', 'widget')
		if is_start:
			# Show on a switch row means "is the GROUP expanded" -- the
			# switch's own display would be a dead end.
			show = '1' if api.GroupVisible(info.get('group_id')) else '0'
		else:
			show = '0' if info.get('display', '1') == '0' else '1'
		if self.HAS_KINDS and kind == 'logic':
			show = '-'
		if info.get('divider') == '1':
			origin = 'divider'
		elif info.get('adopted') == '1':
			origin = 'built-in'
		elif is_start:
			origin = 'group'
		elif is_end:
			origin = 'group end'
		else:
			origin = self._originOf(info)
		# Group is DERIVED from where the entry sits between brackets -- a
		# switch row shows its own group at the end of the path
		group = api.GroupPath(name) if self.HAS_GROUPS else ''
		if is_start:
			own = groups.get(info.get('group_id'), {}).get('label', '')
			group = f'{group} / {own}' if group else own
		row = [label if label is not None else name]
		if self.HAS_SIDES:
			if side is None:
				side = info.get('side', 'right') if (not self.HAS_KINDS or kind == 'widget') else '-'
			row.append(side)
		row.append(show)
		if self.HAS_WIDTH:
			row.append(self._widthOf(api, name, info))
		row += [group, origin]
		return row

	def Refresh(self):
		"""Rebuild the flat entries table from live state (the tree view
		is the one on screen; this table is its hidden fallback)."""
		t = self.ownerComp.op('entries')
		if t is None:
			return
		t.clear()
		cols = self._entryColumns()
		t.appendRow(cols)
		api = self._api()
		show_builtins = self._showBuiltins()
		if api is None:
			if show_builtins:
				for o in self._builtinWidgets():
					show = '1'
					if hasattr(o.par, 'display'):
						show = '1' if o.par.display.eval() else '0'
					row = [o.name] + (['-'] if self.HAS_SIDES else []) + [show]
					if self.HAS_WIDTH:
						row.append('')
					row += ['-', 'built-in']
					t.appendRow(row)
			return
		widgets = api.Widgets
		groups = api.Groups if self.HAS_GROUPS else {}
		for name in api.WidgetSequence:
			info = widgets.get(name, {})
			if info.get('adopted') == '1' and not show_builtins:
				continue
			t.appendRow(self._entryRow(api, name, info, groups))
		self.RefreshTree()

	# --- tree view ------------------------------------------------------------
	#
	# The treeLister renders the hierarchy natively from a `path` column, so
	# the bracket structure IS the tree: a group is a branch, its members are
	# its children, and the end cap never appears -- the branch itself
	# conveys where the group stops. Sided surfaces add one wrinkle: a group
	# cannot span the bar's fill pivot (see TreeMoveRows).

	def _treeSeg(self, key, index):
		"""One path segment, prefixed with a zero-padded position: treeLister
		sorts siblings by path key, so encoding the position makes that sort
		produce BAR order by construction. Never seen -- Name comes from the
		table, not the path."""
		return f'{index:04d}{self.TREE_ORDER_SEP}{key}'

	def _treeKey(self, segment):
		seg = str(segment)
		return seg.split(self.TREE_ORDER_SEP, 1)[1] if self.TREE_ORDER_SEP in seg else seg

	def _treeColumns(self):
		cols = ['path', 'Name']
		if self.HAS_SIDES:
			cols.append('Side')
		cols.append('Show')
		if self.HAS_WIDTH:
			cols.append('Width')
		cols.append('Origin')
		return cols

	def RefreshTree(self):
		"""Rebuild the tree table. Group starts become branch rows keyed by
		their group id; end caps are omitted entirely. Un-adopted stock items
		(mode panels, the pivot, overlays) are listed after the managed run,
		flat and read-only, so they are still visible and hideable."""
		t = self.ownerComp.op('tree_entries')
		api = self._api()
		if t is None:
			return
		t.clear()
		t.appendRow(self._treeColumns())
		if api is None:
			return
		show_builtins = self._showBuiltins()
		widgets = api.Widgets
		names = api.WidgetSequence
		ancestors, _ = api._scanGroups(names) if self.HAS_GROUPS else ({}, [])
		groups = api.Groups if self.HAS_GROUPS else {}
		seg_of = {}
		for i, name in enumerate(names):
			info = widgets.get(name, {})
			if info.get('group_end') == '1':
				continue  # the branch already shows the extent
			chain = [seg_of[g] for g in (ancestors.get(name) or []) if g in seg_of]
			kind = info.get('kind', 'widget')
			if info.get('group_start') == '1':
				gid = info.get('group_id')
				seg = self._treeSeg(gid, i)
				seg_of[gid] = seg
				label = (groups.get(gid) or {}).get('label', gid)
				show = '1' if api.GroupVisible(gid) else '0'
				row = [self.TREE_SEP.join(chain + [seg]), label]
				if self.HAS_SIDES:
					row.append(info.get('side', 'right') if (not self.HAS_KINDS or kind == 'widget') else '-')
				row.append(show)
				if self.HAS_WIDTH:
					row.append('')
				row.append('group')
				t.appendRow(row)
				continue
			if info.get('adopted') == '1' and not show_builtins:
				continue
			show = '0' if info.get('display', '1') == '0' else '1'
			if self.HAS_KINDS and kind == 'logic':
				show = '-'
			if info.get('divider') == '1':
				origin = 'divider'
			elif info.get('adopted') == '1':
				origin = 'built-in'
			else:
				origin = self._originOf(info)
			row = [self.TREE_SEP.join(chain + [self._treeSeg(name, i)]), name]
			if self.HAS_SIDES:
				row.append(info.get('side', 'right') if (not self.HAS_KINDS or kind == 'widget') else '-')
			row.append(show)
			if self.HAS_WIDTH:
				row.append(self._widthOf(api, name, info))
			row.append(origin)
			t.appendRow(row)
		if show_builtins and self.ADOPTS_BUILTINS:
			managed = set(names)
			base = len(names)
			for j, o in enumerate(self._builtinWidgets()):
				if o.name in managed:
					continue
				show = '1' if (hasattr(o.par, 'display') and o.par.display.eval()) else '0'
				row = [self._treeSeg(o.name, base + j), o.name]
				if self.HAS_SIDES:
					row.append('-')
				row.append(show)
				if self.HAS_WIDTH:
					row.append('')
				row.append('TD fixed')
				t.appendRow(row)

	def TreeRowName(self, path):
		"""Resolve a tree path back to the entry it stands for -- a group
		branch resolves to its start marker, so clicks act on the switch.
		A name that is not a registry entry is a built-in bar item: it is
		handed back bare (ToggleShow/OpenOrigin treat an unknown name as a
		built-in, and the drag path drops it -- not in WidgetSequence)."""
		api = self._api()
		if api is None or not path:
			return None
		leaf = self._treeKey(str(path).split(self.TREE_SEP)[-1])
		if leaf in api.Widgets:
			return leaf
		if self.HAS_GROUPS:
			start = api._groupStartName(leaf)
			if start in api.Widgets:
				return start
		return leaf

	def NameRightClick(self, name):
		"""Right-click a Name cell: a group branch renames, anything else
		opens its wiki page."""
		api = self._api()
		info = api.Widgets.get(name) if api is not None else None
		if info is not None and info.get('group_start') == '1':
			self.PromptGroup(name)
		else:
			self.OpenDocs(name)

	def _pathOfRow(self, row):
		"""Tree path off a lister row -- the source row carrying `path` hangs
		under 'rowObject', not at the top level of the displayed dict."""
		if isinstance(row, dict):
			if row.get('path'):
				return row['path']
			inner = row.get('rowObject')
			if isinstance(inner, dict):
				return inner.get('path')
			return getattr(inner, 'path', None)
		return getattr(row, 'path', None)

	def _activeLister(self):
		"""(listCOMP, is_tree) for whichever view is on screen. The flat
		lister is kept as a hidden fallback, so selection must be read from
		the one actually displayed."""
		tree = self.ownerComp.op('treeLister')
		if tree is not None and tree.par.display.eval():
			return tree.op('lister'), True
		return self.ownerComp.op('lister'), False

	def _blockOf(self, api, seq, name):
		"""The contiguous run a row stands for: a group branch carries its
		whole bracket range (nested groups included), anything else is just
		itself."""
		info = api.Widgets.get(name, {})
		if info.get('group_start') != '1':
			return [name]
		end = api._groupEndName(info.get('group_id'))
		try:
			i, j = seq.index(name), seq.index(end)
		except ValueError:
			return [name]
		return seq[i:j + 1]

	def TreeMoveRows(self, paths, moved_indices):
		"""A drop in the tree is a reorder AND a regroup at once -- and on a
		sided surface a side change too.

		Membership is positional, so landing between a group's brackets IS
		joining it: the moved block lands immediately after the row above
		it, which means dropping onto a group's header makes it that group's
		first child. A group cannot straddle a bar's fill pivot, so the
		moved block also adopts the side of the row it lands under -- which
		is what makes dragging across the left/right boundary work."""
		api = self._api()
		if api is None or not paths or not moved_indices:
			return
		seq = api.WidgetSequence
		moved_indices = sorted(i for i in moved_indices if 0 <= i < len(paths))
		if not moved_indices:
			return
		names = [self.TreeRowName(paths[i]) for i in moved_indices]
		block = []
		for n in [x for x in names if x]:
			for member in self._blockOf(api, seq, n):
				if member not in block:
					block.append(member)
		if not block:
			return
		block = [n for n in seq if n in set(block)]     # keep bar order
		anchor_i = moved_indices[0] - 1
		anchor = self.TreeRowName(paths[anchor_i]) if anchor_i >= 0 else None
		if anchor is not None and anchor in block:
			self._log('a group cannot be dropped inside itself')
			self.Refresh()
			return
		rest = [n for n in seq if n not in set(block)]
		if anchor is None:
			idx = 0
		else:
			try:
				idx = rest.index(anchor) + 1
			except ValueError:
				self.Refresh()
				return
		# adopt the anchor's side, but only from a real aligned widget --
		# overlay/logic entries sit outside the layout flow and have no side.
		# NOTE: go through SetWidgetSide, never `api.Widgets[n]['side'] = ...`
		# -- the Widgets property hands back COPIES, so mutating one changes
		# nothing and (because sided bars renumber per side) the whole move
		# silently collapses into a no-op.
		if self.HAS_SIDES and anchor is not None:
			ainfo = api.Widgets.get(anchor, {})
			if not self.HAS_KINDS or ainfo.get('kind', 'widget') == 'widget':
				side = ainfo.get('side', 'right')
				for n in block:
					info = api.Widgets.get(n, {})
					if (not self.HAS_KINDS or info.get('kind', 'widget') == 'widget') and info.get('side') != side:
						api.SetWidgetSide(n, side)
		self.PushSequence(rest[:idx] + block + rest[idx:])

	# --- edits (each persists to its owner) -----------------------------------

	def PushSequence(self, names):
		api = self._api()
		if api is not None:
			api.SetWidgetSequence([n for n in names if n])
			widgets = api.Widgets
			# persist new positions for everything THIS component owns --
			# dividers and both ends of every group bracket
			for name in self._ownedNames():
				info = widgets.get(name)
				if info and 'menu_order' in info:
					cols = {'order': info['menu_order']}
					if self.HAS_SIDES:
						cols['side'] = info.get('side', 'right')
					self._writeState(self._ownedKind(info), name, **cols)
			# adopted built-ins have no host publisher -- their order persists
			# HERE (entries live in /sys, which is not saved), or a reorder
			# would not survive a restart
			for name, info in widgets.items():
				if info.get('adopted') == '1' and 'menu_order' in info:
					self._writeState('builtin', name, order=info['menu_order'],
									 display=info.get('display', '1'))
			# a reorder can change which entries a bracket wraps -- re-derive
			# every LIVE group's anchors from the sequence that now stands
			# (dormant groups are absent from Groups and keep their spec)
			if self.HAS_GROUPS:
				for gid in api.Groups:
					self._writeMarkerState(api, gid)
		self.Refresh()

	def ToggleShow(self, name):
		api = self._api()
		info = api.Widgets.get(name) if api is not None else None
		if info is None:
			# built-in: flip the display par directly on every bar, persist
			# the override
			bar = op(self.BAR_PATH) if self.BAR_PATH else None
			o = bar.op(name) if bar else None
			if o is not None and hasattr(o.par, 'display'):
				new = 0 if o.par.display.eval() else 1
				for b in self._bars():
					bo = b.op(name)
					if bo is not None and hasattr(bo.par, 'display'):
						bo.par.display = new
				self._writeState('builtin', name, display=new)
			self.Refresh()
			return
		if self.HAS_KINDS and info.get('kind', 'widget') == 'logic':
			return  # nothing to show or hide
		if info.get('group_start') == '1':
			# Show on a switch row acts on the GROUP, not the button's own
			# display -- clicking it is just another way to press the switch.
			gid = info.get('group_id')
			api.ToggleGroup(gid)
			self._writeState('group', gid, display=1 if api.GroupVisible(gid) else 0)
			self.Refresh()
			return
		visible = info.get('display', '1') == '0'
		api.SetWidgetDisplay(name, visible)
		if name in self._ownedNames() or info.get('adopted') == '1':
			# no host publisher to persist to -- the state table owns it
			self._writeState(self._ownedKind(info), name, display=1 if visible else 0)
		self.Refresh()

	def ToggleSide(self, name):
		"""Flip a widget between the left and right of the bar's pivot."""
		if not self.HAS_SIDES:
			return
		api = self._api()
		info = api.Widgets.get(name) if api is not None else None
		if info is None or (self.HAS_KINDS and info.get('kind', 'widget') != 'widget'):
			return
		if api._isGroupMarker(info):
			self._log('a group bracket follows the side of the run it wraps -- move its members instead')
			return
		new_side = 'left' if info.get('side', 'right') == 'right' else 'right'
		api.SetWidgetSide(name, new_side)
		self.Refresh()

	def PromptWidth(self, name):
		if not self.HAS_WIDTH:
			return
		api = self._api()
		is_builtin = api is None or api.Widgets.get(name) is None
		cur = ''
		if is_builtin:
			bar = op(self.BAR_PATH) if self.BAR_PATH else None
			o = bar.op(name) if bar else None
			if o is None:
				return
			cur = str(int(o.par.w.eval()))
		else:
			cur = api.Widgets[name].get('width', '')
		op.TDResources.PopDialog.OpenDefault(
			text=f'Width for {name} (empty = auto)',
			title='Bar Width',
			buttons=['Set', 'Cancel'],
			callback=self._onWidthDialog,
			details={'canonical': name, 'builtin': is_builtin},
			textEntry=cur,
			escButton=2, enterButton=1)

	def _onWidthDialog(self, info):
		if info.get('buttonNum') != 1:
			return
		det = info.get('details') or {}
		name = det.get('canonical')
		txt = str(info.get('enteredText', '') or '').strip()
		if not name:
			return
		api = self._api()
		if det.get('builtin'):
			bar = op(self.BAR_PATH) if self.BAR_PATH else None
			o = bar.op(name) if bar else None
			if o is not None and txt:
				try:
					val = max(1, min(int(float(txt)), 800))
					o.par.w = val
					self._writeState('builtin', name, width=val)
				except (TypeError, ValueError):
					self._log(f'invalid width {txt!r}')
		elif api is not None:
			api.SetWidgetWidth(name, txt if txt else None)
			if name in self._ownedNames():
				self._writeState('divider', name, width=txt)
		self.Refresh()

	def PromptGroup(self, name):
		"""Group cell on a switch row renames that group. On any other row the
		cell is derived from position and cannot be typed into -- to change
		what a group holds, drag rows in or out of its brackets."""
		api = self._api()
		info = api.Widgets.get(name) if api is not None else None
		if info is None or info.get('group_start') != '1':
			return
		gid = info.get('group_id', '')
		label = (api.Groups.get(gid) or {}).get('label', gid)
		op.TDResources.PopDialog.OpenDefault(
			text=f'Rename group "{label}" (empty = dissolve it)',
			title='Group',
			buttons=['Set', 'Cancel'],
			callback=self._onGroupDialog,
			details={'group_id': gid},
			textEntry=label,
			escButton=2, enterButton=1)

	def _onGroupDialog(self, info):
		if info.get('buttonNum') != 1:
			return
		det = info.get('details') or {}
		txt = str(info.get('enteredText', '') or '').strip()
		api = self._api()
		gid = det.get('group_id')
		if api is None or not gid:
			return
		if not txt:
			self.DissolveGroup(gid)
			return
		if api.RenameGroup(gid, txt):
			self._writeState('groupstart', api._groupStartName(gid), label=txt)
		self.Refresh()

	def PromptNewGroup(self):
		"""Ask for a name, then wrap the selected run in a new group."""
		if not self.HAS_GROUPS or self._api() is None:
			return
		names = self.SelectedNames()
		if not names:
			self._log('select the rows to group first')
			return
		count = len(names)
		op.TDResources.PopDialog.OpenDefault(
			text=f'Name for the new group around {count} selected '
				 f'row{"" if count == 1 else "s"}',
			title='New Group',
			buttons=['Create', 'Cancel'],
			callback=self._onNewGroupDialog,
			details={'names': names},
			textEntry='',
			escButton=2, enterButton=1)

	def _onNewGroupDialog(self, info):
		if info.get('buttonNum') != 1:
			return
		label = str(info.get('enteredText', '') or '').strip()
		self.GroupSelected(label=label or None)

	def GroupSelected(self, label=None):
		"""Wrap the selected run in a new group. The selection's first and
		last rows become the brackets, so everything between them -- nested
		groups included -- comes along. On a sided surface every selected
		row must be on one side (a group cannot span the fill pivot), and on
		a kinded one only aligned widgets can be grouped."""
		if not self.HAS_GROUPS:
			self._log('this surface has no groups')
			return None
		api = self._api()
		if api is None:
			self._log('no registry -- cannot group in standalone mode')
			return None
		names = self.SelectedNames()
		if not names:
			return None
		widgets = api.Widgets
		if self.HAS_SIDES:
			sides = {(widgets.get(n) or {}).get('side', 'right') for n in names}
			if len(sides) > 1:
				self._log('a group cannot span both sides of the bar')
				return None
		if self.HAS_KINDS:
			kinds = {(widgets.get(n) or {}).get('kind', 'widget') for n in names}
			if kinds - {'widget'}:
				self._log('only aligned widgets can be grouped (overlay/logic entries are not in the layout flow)')
				return None
		gid = api.CreateGroup(names[0], names[-1], label=label)
		if not gid:
			return None  # CreateGroup already said why (crossing brackets)
		self._writeMarkerState(api, gid)
		# inserting brackets renumbers everything after them, so re-persist
		# the CURRENT order of every owned entry
		self.PushSequence(api.WidgetSequence)
		return gid

	def DissolveGroup(self, gid):
		"""Remove a group's brackets. Members stay exactly where they are and
		keep their own Show state, so anything it was hiding comes back."""
		api = self._api()
		if api is None or not gid:
			return
		marker_names = (api._groupStartName(gid), api._groupEndName(gid))
		api.RemoveGroup(gid)
		for n in marker_names:
			self._dropState(n)
		r = self._stateRowIndex(gid)
		t = self._stateDat()
		if t is not None and r is not None and t[r, 'kind'].val == 'group':
			t.deleteRow(r)
		# removing brackets renumbers what followed them
		self.PushSequence(api.WidgetSequence)

	def DissolveGroupFor(self, name):
		"""Dissolve the innermost group enclosing a row (or the one a switch
		row controls) -- right-click the Group cell."""
		api = self._api()
		info = api.Widgets.get(name) if (api is not None and name) else None
		if not info:
			return
		gid = info.get('group_id')
		if not gid:
			ancestors, _ = api._scanGroups(api.WidgetSequence)
			chain = ancestors.get(name) or []
			gid = chain[-1] if chain else None
		if gid:
			self.DissolveGroup(gid)

	def UngroupSelected(self):
		"""Dissolve the innermost group around the selection."""
		self.DissolveGroupFor(self.SelectedName())

	def AddDivider(self):
		if not self.HAS_DIVIDERS:
			return
		api = self._api()
		if api is None:
			self._log('no registry -- cannot add dividers in standalone mode')
			return
		canonical = api.AddDivider(after=self.SelectedName())
		if canonical:
			info = api.Widgets.get(canonical, {})
			self._writeState('divider', canonical,
							 order=info.get('menu_order', ''),
							 width=info.get('width', '3'),
							 display='1')
		self.PushSequence(api.WidgetSequence)

	def RemoveSelected(self):
		api = self._api()
		sel = self.SelectedName()
		if api is not None and sel:
			info = api.Widgets.get(sel, {})
			if info.get('group_start') == '1' or info.get('group_end') == '1':
				# a bracket is not deletable on its own -- half a pair is not
				# a group, so removing one means dissolving the group
				self.DissolveGroupFor(sel)
				return
			if self.HAS_DIVIDERS and api.RemoveDivider(sel):
				self._dropState(sel)
		self.Refresh()

	def SelectedNames(self):
		"""Selected rows' canonical names, in bar order.

		Reads whichever view is on screen (the flat lister is kept as a hidden
		fallback), and in the tree resolves through the row's PATH -- the Name
		cell there is a label, so a group row shows its label, not its marker."""
		lst, is_tree = self._activeLister()
		if lst is None:
			return []
		try:
			rows = sorted(lst.SelectedRows or [])
			out = []
			for r in rows:
				row = lst.Data[r]
				name = (self.TreeRowName(self._pathOfRow(row)) if is_tree
						else row.get('Name'))
				if name and name not in out:
					out.append(name)
		except Exception as e:
			self._log(f'SelectedNames failed: {e}')
			return []
		api = self._api()
		if api is not None:
			seq = api.WidgetSequence
			out.sort(key=lambda n: seq.index(n) if n in seq else 1 << 30)
		return out

	def SelectedName(self):
		names = self.SelectedNames()
		return names[0] if names else None

	# --- drop-to-register (the hub routes a dropped panel COMP here) ----------

	def AcceptsDrop(self, items):
		"""True if the drag payload contains at least one packageable panel COMP."""
		if not self.SUPPORTS_DROP:
			return False
		try:
			return any(self._isPackageable(i) for i in items)
		except Exception:
			return False

	def _isPackageable(self, item):
		if not isinstance(item, COMP) or not item.isPanel:
			return False
		me_ = self.ownerComp
		if item is me_ or me_.path.startswith(item.path + '/'):
			return False  # never package ourselves or our ancestors
		if item.path.startswith(me_.path + '/'):
			return False  # nor our own internals
		for bar in self._bars():
			if item is bar or item.path.startswith(bar.path + '/'):
				return False  # things already living in the bar (mirrors, built-ins)
		return True

	def PackageDrop(self, comp):
		"""Turn a dropped panel COMP into a self-registering package of this
		surface. Returns the accepted COMP; the actual stamping runs a few
		frames later -- copying a clone-bound COMP inside the drop-event
		stack has crashed TD, so it is never done inline."""
		if not self.SUPPORTS_DROP or not self._isPackageable(comp):
			return None
		run('args[0](args[1])', self._stampPackage, comp.path,
			delayFrames=3, delayRef=op.TDResources)
		return comp

	def _stampOrderCounts(self, info):
		"""Does this entry count when choosing the order a fresh package
		gets (after the LAST entry of the side/kind it will join)?"""
		if self.HAS_SIDES and info.get('side', 'right') != 'right':
			return False
		if self.HAS_KINDS and info.get('kind', 'widget') != 'widget':
			return False
		return True

	def _stampPackage(self, comp_path):
		"""Deferred worker for PackageDrop: stamp the registry MASTER's host
		into the COMP through RegistryBase.StampHost (the one blessed copy
		path -- ext-init-during-copy, inherited externaltox/pi_suspect,
		storage and bind scrubs all live there), placed after the bar's
		last entry, then registered. Idempotent -- a COMP that already
		carries a host is just re-kicked."""
		comp = op(comp_path)
		if comp is None or not comp.valid or not self._isPackageable(comp):
			return
		host = comp.op(self.REGISTRY_NAME)
		fresh = host is None
		if fresh:
			root = getattr(op, 'FNS', None)
			master = root.op(self.REGISTRY_NAME) if root is not None else None
			if master is None or not hasattr(master, 'StampHost'):
				self._log(f'no {self.REGISTRY_NAME} master to stamp from')
				return
			api = self._api()
			orders = []
			if api is not None:
				for i in api.Widgets.values():
					if not self._stampOrderCounts(i):
						continue
					try:
						orders.append(int(i.get('menu_order')))
					except (TypeError, ValueError):
						pass
			order = (max(orders) + 1) if orders else 0
			par_values = {'Menuorder': order, 'Displayed': True, 'Barwidth': 0}
			par_values.update(self.STAMP_EXTRA_PARS)
			host = master.StampHost(comp, canonical_name=comp.name, autoregister=True,
									par_values=par_values)
			if host is None:
				return
		else:
			host.par.Autoregister = True
		run('args[0](args[1])', self._kickHost, host.path,
			delayFrames=15, delayRef=op.TDResources)
		run('args[0]()', self.Refresh, delayFrames=25, delayRef=op.TDResources)
		self._focusHost(host)
		self._log(f'{"packaged" if fresh else "re-registered"} {comp.path}')

	def _focusHost(self, host):
		"""Navigate the user's CURRENT network editor into the dropped COMP
		and land on the freshly stamped registry host."""
		try:
			pane = ui.panes.current
			if pane is None or pane.type != PaneType.NETWORKEDITOR:
				pane = next((p for p in ui.panes if p.type == PaneType.NETWORKEDITOR), None)
			if pane is None:
				return
			pane.owner = host.parent()
			host.current = True
			host.selected = True
			pane.home(op=host)
		except Exception as e:
			self._log(f'focus after stamp failed: {e}')

	def _kickHost(self, host_path):
		h = op(host_path)
		if h is not None and h.valid and hasattr(h.ext, self.REGISTRY_EXT):
			getattr(h.ext, self.REGISTRY_EXT)._applyHostRegistration(force=True)

	# --- navigation -----------------------------------------------------------

	def OpenDocs(self, name):
		"""Open the tool's self-reported wiki page (registered help_url)."""
		api = self._api()
		if api is not None:
			api.OpenDocs(name)

	def OpenOrigin(self, name):
		"""Floating network editor on the component owning an entry."""
		api = self._api()
		bar = op(self.BAR_PATH) if self.BAR_PATH else None
		if api is None:
			target = bar
		else:
			target = None
			info = api.Widgets.get(name)
			if info:
				src = info.get('source_registry')
				if src and op(src) is not None:
					target = op(src).parent()
				if target is None:
					w = api.WidgetTarget(name)
					if w is not None:
						target = w.parent()
			if target is None and name in self._ownedNames():
				target = self.ownerComp
			if target is None and bar and bar.op(name) is not None:
				target = bar
		if target is None:
			return
		pane_name = self.ORIGIN_PANE
		pane = next((p for p in ui.panes if p.name == pane_name), None)
		if pane is None:
			pane = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name=pane_name)
		pane.owner = target

	def Open(self):
		"""Open FNS_Hub on this configurator's tab."""
		reg = getattr(op, 'FNS_HUBREGISTRY', None)
		if reg is not None and hasattr(reg, 'Open'):
			reg.Open(tab=self.HUB_TAB)
