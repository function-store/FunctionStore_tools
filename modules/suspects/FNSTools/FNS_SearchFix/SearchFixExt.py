"""FNS_SearchFix: a find bar that finds things (docs/SearchFix.md).

Every network editor pane has a find bar, /ui/panes/pane_find/<pane name>,
made the first time it opens. TouchDesigner's own search there is a tscript
`lc <path>/<text>*`: a case-sensitive prefix match over the current network.
This patches each bar with a Python search on the shared tiered matcher
(scripts/shared/FuzzyMatch.py) and keeps the bar's arrows, Home toggle and
label. TD's tscript handlers are switched off while patched and back on
when not, and nothing of TD's is deleted, so Active off is the bar as TD
made it.

The controls (Legacy, Fuzzy, Deep and the depth field, with the search DATs
inside them) are `bar_template`, published into every find bar through
FNS_PaneSearchRegistry like any contribution (docs/PaneSearchRegistry.md).
This tool only patches the search itself: the results feed and TD's
handlers.
"""
from __future__ import annotations

import fnmatch
from typing import Optional

# TouchDesigner's own UI locations: fixed by TD, not by a project.
PANE_FIND = '/ui/panes/pane_find'
# the registry's copy of bar_template in each find bar: FNS_PaneSearchRegistry
# names an instance ITEM_PREFIX + its canonical name
CANONICAL = 'SearchFix'
WIDGET = 'psr_' + CANONICAL
LEGACY_WIDGET = 'fns_searchfix'          # injected by SearchFix itself before 0.2.0
BRIDGE = 'fns_searchfix_results'         # Select DAT feeding the bar's `results`
# TD's tscript handlers this patch stands in for, switched off while active
TSCRIPT_HANDLERS = ('datexec1', 'back/script', 'forward/script', 'pathchange')
# not searched when the search starts at the project root
SKIP_AT_ROOT = ('ui', 'sys', 'local')
# a word with any of these is a TouchDesigner pattern, matched by tdu.match
WILDCARDS = set('*?[^')


class SearchFixExt:
	"""Python search for the network editor's find bar, patched per pane."""

	def __init__(self, ownerComp: COMP) -> None:
		self.ownerComp = ownerComp
		# per find bar (by path): where the search runs, the network a pick
		# navigated into, and the last results seen, so a pick that moves
		# the pane does not restart the search from the new network
		self._roots = {}
		self._navTo = {}
		self._lastSig = {}
		# /ui is rebuilt on every project open, after extensions come up
		run('args[0].valid and args[0].extensionsReady'
			' and args[0].ext.SearchFixExt.PatchAll()',
			ownerComp, delayFrames=60, delayRef=op.TDResources)

	# ------------------------------------------------------------ patching

	def PatchAll(self) -> int:
		"""Patch every find bar there is, or unpatch them all when Active is off.

		The controls follow Active through the registry host: on, they are
		published into every find bar; off, the registry takes them out.
		"""
		active = bool(self.ownerComp.par.Active.eval())
		host = self.ownerComp.op('FNS_PaneSearchRegistry')
		if host is not None and host.par['Autoregister'] is not None \
				and bool(host.par.Autoregister.eval()) != active:
			host.par.Autoregister = active
		home = op(PANE_FIND)
		if home is None:
			return 0
		n = 0
		for fb in home.children:
			if not fb.isCOMP or fb.op('search/text1') is None:
				continue
			if active:
				self._patch(fb)
			else:
				self._unpatch(fb)
			n += 1
		return n

	def _patch(self, fb: COMP) -> None:
		old = fb.op(LEGACY_WIDGET)
		if old is not None:
			old.destroy()                # SearchFix injected its own controls before
		bridge = fb.op(BRIDGE)
		if bridge is None:
			bridge = fb.create(selectDAT, BRIDGE)
		# the registry's copy may arrive a frame after this: a Select DAT
		# resolves its `dat` by name on every cook, so it finds it then
		bridge.par.dat = WIDGET + '/script_results'
		home = fb.op('home')
		if home is not None:
			bridge.nodeX = home.nodeX + 300
			bridge.nodeY = home.nodeY - 400
		results = fb.op('results')
		if results is not None and (not results.inputs or results.inputs[0] != bridge):
			results.inputConnectors[0].connect(bridge)
		for name in TSCRIPT_HANDLERS:
			d = fb.op(name)
			if d is not None and d.par['active'] is not None:
				d.par.active = False

	def _unpatch(self, fb: COMP) -> None:
		results = fb.op('results')
		select1 = fb.op('select1')
		if results is not None and select1 is not None:
			results.inputConnectors[0].connect(select1)
		for name in (BRIDGE, LEGACY_WIDGET):
			o = fb.op(name)
			if o is not None:
				o.destroy()
		for name in TSCRIPT_HANDLERS:
			d = fb.op(name)
			if d is not None and d.par['active'] is not None:
				d.par.active = True
		for store in (self._roots, self._navTo, self._lastSig):
			store.pop(fb.path, None)

	# ------------------------------------------------------------ the shortcut

	def onFindShortcut(self) -> None:
		"""Wiring for kbd_findbar: the find bar's shortcut also closes it.

		TouchDesigner toggles a pane's find bar on Ctrl+F (Cmd+F on macOS)
		while the network has the keyboard, but the bar takes the keyboard
		as it opens, and from its search field the shortcut does nothing.
		Nothing in TD says whether a bar is open (its container, the pane bar
		and the pane's geometry read the same either way), but the field's
		`focus` panel value, read here before TD handles the key, says which
		case this is (measured 2026-10-01): on, the user is typing in that
		bar, and this closes it with the bar's own close button. Off, the
		press is TD's own, opening or closing.
		"""
		if not self.ownerComp.par.Togglefindbar.eval():
			return
		home = op(PANE_FIND)
		if home is None:
			return
		for fb in home.children:
			field = fb.op('search/text1') if fb.isCOMP else None
			if field is None or not field.panel.focus.val:
				continue
			button = fb.op('close/button')
			if button is not None:
				# press and release on separate frames, like a mouse click: a
				# Panel Execute compares frames, and a one-call click() changes
				# the state and back inside one frame, which it never sees
				button.click(1)
				run('args[0].valid and args[0].click(0)', button,
					delayFrames=2, delayRef=op.TDResources)
			return

	# ------------------------------------------------------------ searching

	def FillResults(self, scriptOp: scriptDAT) -> None:
		"""The script_results cook: one row per hit, its path relative to the search root."""
		scriptOp.clear()
		w = scriptOp.parent()
		fb = w.parent()
		if fb is None or fb.parent() is None or fb.parent().path != PANE_FIND:
			return                       # the template inside this tool
		text = str(fb.op('search/text1').par.text.eval())
		path = fb.op('path')
		here = path[0, 0].val if path is not None and path.numRows else ''
		par = self.ownerComp.par
		legacy = bool(par.Legacy.eval())
		fuzzy = bool(par.Fuzzy.eval())
		# this bar's own: Deep off searches this network only, Deep on goes as
		# deep as the bar's Depth field, counted like findChildren's maxDepth
		# (1 is this network, as with Deep off); the tool's Depth is where the
		# field starts
		deep = w.par['Deep'] is not None and bool(w.par.Deep.eval())
		depth = max(1, int(w.par.Depth.eval())) if deep and w.par['Depth'] is not None else 1
		cap = max(1, int(par.Maxresults.eval()))
		root = self._searchRoot(fb, here)
		if root is None or not text.strip():
			return
		for rel in self.Search(root, text, legacy=legacy, fuzzy=fuzzy, depth=depth, limit=cap):
			scriptOp.appendRow([rel])

	def _searchRoot(self, fb: COMP, here: str) -> Optional[COMP]:
		"""The network the search runs in: where the pane is, unless a pick moved it.

		A pick that enters a deeper network moves the pane, which changes the
		bar's `path`. Searching from there would replace the results under the
		arrows, so the root stays put until the user navigates somewhere a pick
		did not take them.
		"""
		key = fb.path
		root = self._roots.get(key)
		if root is None or op(root) is None or (here != root and here != self._navTo.get(key)):
			root = here
			self._navTo.pop(key, None)
		self._roots[key] = root
		return op(root) if root else None

	def Search(self, root: COMP, text: str, legacy: bool = False, fuzzy: bool = False,
			   depth: int = 1, limit: int = 500) -> list:
		"""Paths of the operators matching `text`, relative to `root`, best first.

		Legacy is TouchDesigner's own find bar: the name starts with the text,
		case-sensitive, in `root` only. Otherwise every word of the text must
		hit the name: a word with *, ?, [ or ^ is a TouchDesigner pattern,
		matched by tdu.match like a Select OP's field (case-insensitive here),
		any other through the matcher's strict tiers (exact, prefix, word
		start, substring), or all its tiers with `fuzzy` (initials, typos,
		letters in order).
		"""
		if legacy:
			names = [c.name for c in root.children if fnmatch.fnmatchcase(c.name, text + '*')]
			return sorted(names)[:limit]
		words = text.split()
		fm = self.ownerComp.op('FuzzyMatch').module
		cands = root.children if depth <= 1 else root.findChildren(maxDepth=depth)
		at_root = root.path == '/'
		base = len(root.path.rstrip('/')) + 1
		keep = []
		for c in cands:
			rel = c.path[base:]
			if at_root and rel.split('/', 1)[0] in SKIP_AT_ROOT:
				continue
			keep.append((c, rel))
		# one tdu.match per pattern word over every name, not one per name
		names = list({c.name for c, _ in keep})
		patterns = {}
		for word in words:
			if WILDCARDS & set(word):
				patterns[word] = set(tdu.match(word, names, caseSensitive=False))
		hits = []
		for c, rel in keep:
			m = self._score(fm, words, c.name, fuzzy, patterns)
			if m is None:
				continue
			hits.append((m[0], rel.count('/'), -m[1], c.name.lower(), rel))
		hits.sort()
		return [h[-1] for h in hits[:limit]]

	@staticmethod
	def _score(fm, words: list, name: str, fuzzy: bool, patterns: dict) -> Optional[tuple]:
		"""(tier, quality) like FuzzyMatch.match, or None. `patterns` holds the
		names each pattern word matched (tdu.match), computed once per search."""
		worst, total = 0, 0.0
		for word in words:
			if word in patterns:
				if name not in patterns[word]:
					return None
				tier, quality = 0, 1.0
			else:
				m = fm.match_token(word, name, strict=not fuzzy)
				if m is None and '_' in word:
					# the field turns spaces into underscores, so a word that
					# misses as typed is tried as its parts, every one a hit:
					# simple_chang still finds FNS_SimpleSceneChanger
					m = SearchFixExt._scoreParts(fm, word, name, fuzzy)
				if m is None:
					return None
				tier, quality = m
			worst = max(worst, tier)
			total += quality - tier
		return worst, total / len(words)

	@staticmethod
	def _scoreParts(fm, word: str, name: str, fuzzy: bool) -> Optional[tuple]:
		"""(worst tier, mean quality) over the underscore-separated parts of `word`, or None."""
		parts = [p for p in word.split('_') if p]
		if len(parts) < 2:
			return None
		worst, total = 0, 0.0
		for part in parts:
			m = fm.match_token(part, name, strict=not fuzzy)
			if m is None:
				return None
			worst = max(worst, m[0])
			total += m[1]
		return worst, total / len(parts)

	# ------------------------------------------------------------ picking

	def onResultsChange(self, fb: COMP) -> None:
		"""New results: point at the first one, like TD's bar always did."""
		res = fb.op(WIDGET + '/script_results')
		if res is None:
			return
		rows = [r[0].val for r in res.rows()]
		sig = (self._roots.get(fb.path), tuple(rows))
		if self._lastSig.get(fb.path) == sig:
			return                       # the same search, re-cooked by a pick
		self._lastSig[fb.path] = sig
		if rows:
			self.Pick(fb, 0)
		else:
			self._label(fb, 'nothing found')

	def Step(self, fb: COMP, delta: int) -> None:
		"""Back (-1) or forward (+1) through the results."""
		cur = fb.op('current')
		i = int(cur[0, 0].val) if cur is not None and cur.numRows else 0
		self.Pick(fb, i + delta)

	def Pick(self, fb: COMP, index: int) -> Optional[OP]:
		"""Make result `index` current and selected, entering its network if
		needed, and home on it when the bar's Home toggle is on."""
		res = fb.op(WIDGET + '/script_results')
		n = res.numRows if res is not None else 0
		if n == 0:
			self._label(fb, 'nothing found')
			return None
		i = index % n
		cur = fb.op('current')
		if cur is not None:
			cur[0, 0] = i
		root = op(self._roots.get(fb.path) or '')
		target = root.op(res[i, 0].val) if root is not None else None
		if target is None:
			return None
		network = target.parent()
		pane = self._pane(fb.name)
		if pane is not None and pane.owner != network:
			self._navTo[fb.path] = network.path
			pane.owner = network
		for o in network.selectedChildren:
			o.selected = False
		target.current = True
		target.selected = True
		home = fb.op('home/out1')
		if pane is not None and home is not None and home['v1'] is not None and home['v1'].eval():
			pane.homeSelected(zoom=True)
		self._label(fb, '%d of %d' % (i + 1, n))
		return target

	@staticmethod
	def _pane(name: str):
		for p in ui.panes:
			if p.name == name:
				return p
		return None

	@staticmethod
	def _label(fb: COMP, text: str) -> None:
		d = fb.op('label/define')
		if d is not None and d.row('label') is not None:
			d['label', 1] = text

	# ------------------------------------------------------------ parameters

	def _onActiveValueChange(self, par: Par, prev) -> None:
		self.PatchAll()

	def _onDepthValueChange(self, par: Par, prev) -> None:
		# a find bar's depth field starts where the registry's copy of the
		# template starts, so the tool's Deep Depth is the template's
		template = self.ownerComp.op('bar_template')
		if template is not None and template.par['Depth'] is not None:
			template.par.Depth = max(1, int(par.eval()))

	def _onRepatchPulse(self, par: Par) -> None:
		self.PatchAll()
