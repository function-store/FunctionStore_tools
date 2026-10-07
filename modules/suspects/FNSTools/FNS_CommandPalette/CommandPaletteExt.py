'''Info Header Start
Name : CommandPaletteExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
"""CommandPaletteExt -- the catalogue, ranking and activation behind FNS_CommandPalette.

This half is deliberately UI-free: it answers "what rows exist", "how do they
rank for this query" and "what happens on Enter", and knows nothing about the
window that will draw them. That is what makes it testable without pixels, and
it is the half worth getting right first.

Design notes and the measured numbers behind them: docs/CommandPaletteDesign.md.

THE ONE RULE THAT SHAPES EVERYTHING
-----------------------------------
Context is snapshotted at SUMMON, never read at Enter. 25 of the registry's
commands declare a `context` (network / selected / current / rollover-par) and
every one of those resolves against what the user is looking at -- but opening
the palette's Window COMP moves focus and takes the mouse out of the network
editor, so `ui.rolloverPar` is already None by the time a row is chosen. The
snapshot is the palette's answer to the same problem the launcher solves by
capturing the foreground pid before its overlay steals focus.
"""

import inspect
import json

# the docked ExtUtils, found by TAG -- the toolkit's import contract
CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper

CommandPaletteExt_ROWCAP = 12          # the launcher caps at 12; so do we


class CommandPaletteExt:

	# Row kinds. Weights are the "type nudge" from the launcher's formula,
	# re-tuned for a palette whose subject is commands rather than sessions:
	# a command outranks a palette component for the same word, because
	# running something you own beats placing someone else's .tox.
	KIND_COMMAND = 'command'
	KIND_COMPONENT = 'component'
	KIND_NETWORK = 'network'
	KIND_METHOD = 'method'
	KIND_EXT = 'ext'
	KIND_TOOL = 'tool'
	KIND_PICK = 'pick'
	KIND_PRESET = 'preset'
	TYPE_WEIGHT = {KIND_COMMAND: 10, KIND_COMPONENT: 6, KIND_NETWORK: 8, KIND_METHOD: 8,
				   KIND_EXT: 8, KIND_TOOL: 8, KIND_PICK: 8,
				   KIND_PRESET: 11}       # user-authored: just above the command it wraps

	# Nudges. Small on purpose: enough to win a tie, never enough to bury a
	# clearly better fuzzy match.
	FAVOURITE_BONUS = 12
	AVAILABLE_BONUS = 3

	# Where TD keeps its palette. This is the Palette Browser's own model, so
	# it already includes user palette folders; we do no scanning of our own.
	PALETTE_DATA = '/ui/dialogs/palette/palette/data'

	# --- persisted preferences -----------------------------------------------
	# Declared here; CustomParHelper.Init creates them (the parfield layer).
	# Queryhistory roams through the FNS_ConfigRegistry host stamped into this
	# tool. Favouritekeys, Visibilityoverrides and Presets are the store from
	# BEFORE the command curation file shared with the launcher
	# (docs/CommandCuration.md): adopted into it once, then emptied, and
	# excluded from the config host so nothing roams twice.
	Favouritekeys = CustomParHelper.ParStr(
		default='[]', page='Palette', label='Favourite keys',
		help='Legacy store of starred command identities (tool#id) from before the shared '
			 'curation file; adopted into that file on first read, then emptied.')
	Queryhistory = CustomParHelper.ParStr(
		default='[]', page='Palette', label='Query history',
		help='JSON list of executed palette queries, oldest first, recalled with '
			 'Alt+Up / Alt+Down. Persisted by the config host.')
	Visibilityoverrides = CustomParHelper.ParStr(
		default='{}', page='Palette', label='Visibility overrides',
		help='Legacy store of visibility overrides (tool#id -> hidden or shown) from before '
			 'the shared curation file; adopted into that file on first read, then emptied.')
	Presets = CustomParHelper.ParStr(
		default='[]', page='Palette', label='Presets',
		help='Legacy store of presets from before the shared curation file; adopted into '
			 'that file on first read, then emptied.')
	Rankbyusage = CustomParHelper.ParToggle(
		default=True, page='Palette', label='Rank By Usage',
		help='Commands you run often rank higher: a small bonus that fades with a 14-day half-life '
			 'and breaks ties between similar matches, never above a better match or a favourite. '
			 'Usage is shared with the TDXLU launcher (command-usage.json) and recorded even when '
			 'this is off.')
	HISTORY_CAP = 50
	PLACEHOLDER = 'Type a command or component'

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp)     # creates the declared pars, routes par callbacks
		self._snapshot = None            # context captured at summon
		self._catalogue = None           # lazily built, invalidated on summon
		self._curationFile = None        # the shared curation file, opened on first use
		self._usageFile = None           # the shared usage file, opened on first use
		self._query = ''
		self._selected = 0
		self._rows = []
		self._lastKeys = []
		self._pending = None
		self._histPos = None
		self._recalling = False
		# a hot-sync reinit mid-use would leave the window open with no state
		# behind it; start closed instead
		win = ownerComp.op('window')
		if win is not None and win.isOpen:
			self.Dismiss()

	# --- context -----------------------------------------------------------

	def CaptureContext(self) -> dict:
		"""Snapshot what the user is looking at, BEFORE the window opens.

		Everything a command's `context` can name is resolved here and nowhere
		else. Mirrors the shape Envoy's get_focus reports, for the same reason:
		it is the only moment the answer is true.
		"""
		snap = {'pane': None, 'network': None, 'current': None, 'selected': [],
				'rollover-par': None}
		try:
			pane = ui.panes.current
			snap['pane'] = pane
			owner = pane.owner if pane is not None else None
			if owner is not None:
				snap['network'] = owner
				child = getattr(owner, 'currentChild', None)
				snap['current'] = child
				snap['selected'] = [c for c in owner.children if c.selected]
		except Exception:
			pass
		try:
			pg = getattr(ui, 'rolloverParGroup', None)
			snap['rollover-par'] = pg if (pg is not None and len(pg) > 1) \
				else ui.rolloverPar
		except Exception:
			pass
		self._snapshot = snap
		return snap

	def Context(self) -> dict:
		"""The active snapshot, capturing one now if the palette never opened."""
		if self._snapshot is None:
			self.CaptureContext()
		return self._snapshot

	def _isAvailable(self, contexts) -> bool:
		"""Whether every context a command declares is present in the snapshot.

		A command that declares none is always available. This is what greys a
		row out, and because it reads the snapshot rather than live ui state it
		stays stable while the palette is open instead of flickering.
		"""
		if not contexts:
			return True
		snap = self.Context()
		for name in contexts:
			value = snap.get(name)
			if value is None or (isinstance(value, list) and not value):
				return False
		return True

	# --- catalogue ---------------------------------------------------------

	def _commandRows(self) -> list:
		"""Every command the registry announces, as palette rows.

		Guarded: no registry in the project is a normal state, not an error.
		Serves ALL commands -- `surface` narrows only when a tool declares it,
		and today none declares one for us.
		"""
		reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
		if reg is None or not hasattr(reg, 'Commands'):
			return []
		over = self._overrides()
		rows = []
		for cmd in reg.Commands():
			ident = self._identity(cmd)
			if over.get(ident, bool(cmd.get('hidden'))):
				continue
			contexts = cmd.get('context') or []
			instance = cmd.get('instance') or ''
			rows.append({
				'kind': self.KIND_COMMAND,
				'key': cmd.get('key'),
				'ident': ident,
				'instance': instance,
				'title': self._instanceTitle(cmd.get('label') or cmd.get('id') or '', instance),
				'category': cmd.get('tool') or '',
				'detail': cmd.get('help') or '',
				'path': cmd.get('path') or '',
				'params': cmd.get('params') or [],
				'state': cmd.get('state'),
				'capability': cmd.get('capability') or '',
				'builtin': bool(cmd.get('builtin')),      # TD/system functionality, not a tool's
				'contexts': contexts,
				'available': self._isAvailable(contexts),
			})
		return rows

	def _paletteRows(self) -> list:
		"""Every .tox in TD's palette, as palette rows.

		The category is a walk up `folderid`, so `checker` reads as
		"Derivative / Generators" -- which is what makes a category search
		useful rather than a flat list of 1377 names.
		"""
		data = op(self.PALETTE_DATA)
		if data is None or data.numRows < 2:
			return []
		names, parents = {}, {}
		for r in range(1, data.numRows):
			rid = data[r, 'id'].val
			names[rid] = data[r, 'name'].val
			parents[rid] = data[r, 'folderid'].val

		def category(rid):
			parts, seen = [], set()
			cur = parents.get(rid)
			while cur and cur in names and cur not in seen:
				seen.add(cur)                 # a malformed table must not loop
				parts.append(names[cur])
				cur = parents.get(cur)
			return ' / '.join(reversed(parts))

		rows = []
		for r in range(1, data.numRows):
			if data[r, 'type'].val != 'tox' or data[r, 'deleted'].val == '1':
				continue
			rid = data[r, 'id'].val
			rows.append({
				'kind': self.KIND_COMPONENT,
				'key': 'palette:' + rid,
				'title': data[r, 'name'].val,
				'category': category(rid),
				'detail': category(rid),
				'path': data[r, 'path'].val,
				# Derivative's own tree (folder ids under '1') ships each
				# component as a BUNDLE: a base of the same name holding the
				# real component plus its icon and help. TD's palette unwraps
				# it on drop (palette/list/components/tree/table/drag); so do we.
				'bundled': rid.startswith('1'),
				'params': [],
				'state': None,
				'contexts': ['network'],      # it has to be placed somewhere
				'available': self._isAvailable(['network']),
			})
		return rows

	def Catalogue(self, rebuild: bool = False) -> list:
		"""Every row the palette can offer, commands first."""
		if rebuild or self._catalogue is None:
			self._catalogue = self._presetRows() + self._commandRows() + self._paletteRows()
		return self._catalogue

	# --- ranking -----------------------------------------------------------

	@staticmethod
	def _subsequenceScore(query: str, text: str):
		"""Fuzzy score in 0..1, or None when `query` is not a subsequence.

		Rewards matches that start at the beginning and that run contiguously,
		so "che" prefers "checker" over a word with c, h and e scattered
		through it.
		"""
		if not query:
			return 0.0
		if not text:
			return None
		q, t = query.lower(), text.lower()
		qi, runs, run, first = 0, 0, 0, None
		for i, ch in enumerate(t):
			if qi < len(q) and ch == q[qi]:
				if first is None:
					first = i
				qi += 1
				run += 1
			elif run:
				runs = max(runs, run)
				run = 0
		if qi < len(q):
			return None
		runs = max(runs, run)
		contiguity = runs / float(len(q))
		position = 1.0 - (first / float(len(t))) if first is not None else 0.0
		density = len(q) / float(len(t))
		return 0.5 * contiguity + 0.3 * position + 0.2 * density

	# Field penalties for the tiered matcher (scripts/shared/FuzzyMatch.py,
	# bound here as the FuzzyMatch DAT): a title hit outranks the same hit in
	# the category, and the file path stays SUBSTRING ONLY -- subsequence
	# matching over a long path matches almost anything and buries real
	# hits. That lesson is inherited rather than rediscovered.
	CATEGORY_PENALTY = 0.4
	PATH_PENALTY = 0.7

	def _rowScore(self, query: str, row: dict):
		"""Match score for a row as one float, or None if the query misses.

		The tiered matcher answers (tier, quality); the tier owns the
		thousands so a word-start hit always lists above a typo hit, and the
		quality the hundreds, which is the reach the type, favourite and
		context nudges had before: enough to win a tie, never a tier.
		"""
		fuzzy = self.ownerComp.op('FuzzyMatch').module
		hit = fuzzy.score_fields(query, (
			(row.get('title') or '', 0.0, False),
			(row.get('category') or '', self.CATEGORY_PENALTY, False),
			(row.get('path') or '', self.PATH_PENALTY, True)))
		if hit is None:
			return None
		tier, quality = hit
		return (10.0 - tier) * 1000 + quality * 100

	# --- prefixes and relevance ---------------------------------------------
	#
	# A leading character scopes the whole query, as in the launcher overlay:
	#     >  commands only      =  components only      /  navigate the network
	# `?` is accepted as a synonym for `>`. Bare `>` and `=` are browse modes;
	# bare `/` lists the child COMPs of the network you came from.
	PREFIXES = {'>': 'commands', '?': 'toolcommands', '=': 'components', '/': 'network',
				'~': 'methods', '#': 'tools', '.': 'network'}

	# How relevant a command is to what the user was looking at: the most
	# specific context it declares AND the snapshot satisfies. The owner's
	# ordering -- a parameter under the mouse beats an operator beats the
	# network beats "general" -- and a declared context the snapshot cannot
	# satisfy sinks below everything. Components sit under general commands so
	# 1377 of them never flood the untyped list.
	CONTEXT_TIER = {'rollover-par': 24, 'current': 18, 'selected': 18, 'network': 12}
	TIER_GENERAL = 6
	# TD's own (builtin) commands list AFTER tool commands and `?` leaves them
	# out entirely -- the consumer side of the registry's wire contract.
	TIER_BUILTIN = 4
	TIER_COMPONENT = 3
	TIER_UNAVAILABLE = -20

	@classmethod
	def _parsePrefix(cls, query):
		raw = (query or '').lstrip()
		q = raw.strip()
		if q and q[0] in cls.PREFIXES:
			mode = cls.PREFIXES[q[0]]
			if mode == 'tools':
				return mode, raw          # a trailing space means "this tool is chosen"
			return mode, (q if mode in ('network', 'methods') else q[1:].strip())
		return 'all', q

	def _relevance(self, row):
		if row['kind'] in (self.KIND_NETWORK, self.KIND_METHOD, self.KIND_EXT,
						   self.KIND_TOOL, self.KIND_PICK):
			return self.TIER_GENERAL
		if row['kind'] == self.KIND_COMPONENT:
			return self.TIER_COMPONENT
		contexts = row.get('contexts') or []
		if not contexts:
			return self.TIER_BUILTIN if row.get('builtin') else self.TIER_GENERAL
		if not row.get('available', True):
			return self.TIER_UNAVAILABLE
		return max(self.CONTEXT_TIER.get(c, self.CONTEXT_TIER['network']) for c in contexts)

	def Rank(self, query: str = '', limit: int = None) -> list:
		"""The rows to show, best first.

		Untyped: ordered by relevance to the snapshot -- commands whose context
		is satisfied first, most specific first, then general commands, then
		components, favourites ahead within a tier. Typed: fuzzy-scored, with
		the relevance tier as a nudge that wins ties and near-ties but does not
		bury a clearly better match.
		"""
		limit = CommandPaletteExt_ROWCAP if limit is None else limit
		mode, q = self._parsePrefix(query)
		if mode == 'network':
			return self._networkRows(q)[:limit]
		if mode == 'methods':
			return self._methodRows(q)[:limit]
		if mode == 'tools':
			return self._toolRows(q)[:limit]
		rows = self.Catalogue()
		if mode == 'commands':          # presets are commands with the arguments filled in
			rows = [r for r in rows if r['kind'] in (self.KIND_COMMAND, self.KIND_PRESET)]
		elif mode == 'toolcommands':
			rows = [r for r in rows if r['kind'] in (self.KIND_COMMAND, self.KIND_PRESET)
					and not (r.get('builtin') or (r.get('command') or {}).get('builtin'))]
		elif mode == 'components':
			rows = [r for r in rows if r['kind'] == self.KIND_COMPONENT]
		favourites = self.Favourites()
		usage = self._usageBonuses()

		if not q:
			ordered = sorted(
				rows,
				key=lambda r: (-self._relevance(r),
							   -self.TYPE_WEIGHT.get(r['kind'], 0),
							   0 if self._curationId(r) in favourites else 1,
							   -usage.get(self._usageId(r), 0.0),
							   r['title'].lower()))
			return ordered[:limit]

		scored = []
		for row in rows:
			base = self._rowScore(q, row)
			if base is None:
				continue
			total = (base
					 + self.TYPE_WEIGHT.get(row['kind'], 0)
					 + (self.FAVOURITE_BONUS if self._curationId(row) in favourites else 0)
					 + usage.get(self._usageId(row), 0.0)
					 + self._relevance(row))
			scored.append((total, row))
		scored.sort(key=lambda pair: (-pair[0], pair[1]['title'].lower()))
		return [row for _, row in scored[:limit]]

	# --- network navigation: `/` root, `./` here, `../` up -------------------

	def _navigationBase(self, query):
		"""Where a navigation query points, by the usual path conventions.

		`/...` is absolute from the root; `.` or `./...` is the network you
		came from; each `..` goes up one level, to any depth. Returns
		(base, partial), or (None, partial) when a segment does not resolve.
		"""
		q = query or ''
		if q.startswith('/'):
			base, rest = op('/'), q[1:]
		else:
			base = self.Context().get('network')
			if base is None or not base.valid:
				base = op('/')
			rest = q
		parts = rest.split('/')
		if parts and parts[-1] in ('.', '..'):
			dirs, partial = parts, ''
		else:
			dirs, partial = parts[:-1], parts[-1]
		for d in dirs:
			if d in ('', '.'):
				continue
			if d == '..':
				base = base.parent() or base
				continue
			nxt = base.op(d)
			if nxt is None or not nxt.isCOMP:
				return None, partial
			base = nxt
		return base, partial

	def _networkRows(self, query):
		"""Child COMPs of the path typed so far, one level deep, as rows."""
		base, partial = self._navigationBase(query)
		if base is None:
			return []

		def row(c, note=''):
			return {'kind': self.KIND_NETWORK, 'key': 'nav:' + c.path,
					'title': c.name or '/', 'category': c.path,
					'detail': note or c.type, 'path': c.path, 'optype': c.type,
					'params': [], 'state': None, 'contexts': [], 'available': True}

		def navigable(c):
			return c.isCOMP and c.type != 'annotate' and not getattr(c, 'utility', False)

		kids = [c for c in base.findChildren(depth=1) if navigable(c)]
		if not partial:
			here = [row(base, 'this network')]
			return here + [row(c) for c in sorted(kids, key=lambda c: c.name.lower())]
		scored = []
		for c in kids:
			score = self._subsequenceScore(partial, c.name)
			if score is not None:
				scored.append((score, c))
		scored.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
		return [row(c) for _, c in scored]

	def _navigateTo(self, path):
		"""Point the pane the user summoned from at `path`."""
		target = op(path)
		if target is None or not target.isCOMP:
			return {'ok': False, 'error': 'no such network %s' % path}
		pane = self.Context().get('pane')
		try:
			if pane is None:
				pane = ui.panes.current
			pane.owner = target
		except Exception as exc:
			return {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)}
		return {'ok': True, 'network': target.path}

	# --- extension methods: the `~` prefix -----------------------------------

	@staticmethod
	def _extensionsOf(comp):
		"""COMP.extensions lists None for every EMPTY slot; only real ones count."""
		return [e for e in (getattr(comp, 'extensions', None) or []) if e is not None]

	def _methodSubject(self):
		"""The COMP whose promoted methods `~` lists.

		A selected COMP first, then the current child if it is a COMP, then
		the network the user came from -- preferring, within that order, one
		that actually carries extensions.
		"""
		snap = self.Context()
		cands = [c for c in (snap.get('selected') or []) if c is not None and c.valid and c.isCOMP]
		cur = snap.get('current')
		if cur is not None and cur.valid and cur.isCOMP:
			cands.append(cur)
		net = snap.get('network')
		if net is not None and net.valid:
			cands.append(net)
		for c in cands:
			if self._extensionsOf(c):
				return c
		return cands[0] if cands else None

	@staticmethod
	def _coerce(token):
		"""An inline argument typed after the method name."""
		low = token.lower()
		if low in ('true', 'false'):
			return low == 'true'
		for cast in (int, float):
			try:
				return cast(token)
			except ValueError:
				pass
		return token

	_SCOPE_EXTLIST = object()      # `~ext.` typed, no extension named yet

	def _namedExtensions(self, comp):
		"""[(label, object)] -- the label is what `.ext.<label>` resolves by.

		Enumerated over the RAW list because `COMP.extensions` holds a None per
		EMPTY slot, and dropping those first would shift every extname index.
		"""
		out = []
		for i, e in enumerate(getattr(comp, 'extensions', None) or []):
			if e is None:
				continue
			p = comp.par['extname%d' % (i + 1)]
			name = str(p.eval()).strip() if p is not None else ''
			out.append((name or type(e).__name__, e))
		return out

	@classmethod
	def _parseMethodHead(cls, head):
		"""(scope, partial) for the first token after `~`.

		`ext.` or `ext.Par` lists the EXTENSIONS; `Name.x` and `ext.Name.x`
		scope to that extension; anything else keeps the flat listing of the
		subject's promoted methods.
		"""
		h = head or ''
		if h.lower().startswith('ext.'):
			body = h[4:]
			if '.' in body:
				name, _, partial = body.partition('.')
				return name, partial
			return cls._SCOPE_EXTLIST, body
		if '.' in h:
			name, _, partial = h.partition('.')
			return name, partial
		return None, h

	@staticmethod
	def _signatureOf(fn):
		"""('(a, b=1)', required_count) for a callable, defensively."""
		try:
			sig = inspect.signature(fn)
		except (TypeError, ValueError):
			return '(...)', 0
		shown, required = [], 0
		for prm in sig.parameters.values():
			if prm.name == 'self':
				continue
			if prm.kind == prm.VAR_POSITIONAL:
				shown.append('*' + prm.name)
			elif prm.kind == prm.VAR_KEYWORD:
				shown.append('**' + prm.name)
			elif prm.default is prm.empty:
				shown.append(prm.name)
				if prm.kind in (prm.POSITIONAL_ONLY, prm.POSITIONAL_OR_KEYWORD):
					required += 1
			else:
				shown.append('%s=%r' % (prm.name, prm.default))
		return '(%s)' % ', '.join(shown), required

	def _extensionRows(self, subject, partial):
		"""One row per extension on the subject -- what `~ext.` lists."""
		rows = []
		for label, obj in self._namedExtensions(subject):
			score = 0
			if partial:
				score = self._subsequenceScore(partial, label)
				if score is None:
					continue
			n = len([m for m in dir(obj) if not m.startswith('_')])
			rows.append({'kind': self.KIND_EXT, 'title': label,
						 'key': 'ext:%s#%s' % (subject.path, label),
						 'category': '%s   -   %d members' % (type(obj).__name__, n),
						 'detail': type(obj).__name__, 'path': subject.path,
						 'extname': label, 'params': [], 'state': None,
						 'contexts': [], 'available': True, '_score': score})
		rows.sort(key=lambda r: (-r['_score'], r['title'].lower()))
		return rows

	@staticmethod
	def _generatedNames(comp):
		"""Accessor names CustomParHelper puts on the class, one set per par.

		`parX` / `evalX` (and the `parGroupX` / `evalGroupX` pair on a tuplet),
		in both the private and expose_public spellings. They are machinery,
		not API: on a tool with forty parameters they are eighty rows burying
		the methods, which is what makes the list useless to read.

		Built from the COMP's ACTUAL parameters rather than by matching a
		prefix, so a hand-written `parse()` or `evaluate()` is never mistaken
		for one of them.
		"""
		out = set()
		try:
			pars = comp.customPars
		except Exception:
			return out
		for p in pars:
			for pre in ('par', 'Par', 'eval', 'Eval'):
				out.add(pre + p.name)
			try:
				group = p.parGroup.name
			except Exception:
				continue
			for pre in ('parGroup', 'ParGroup', 'evalGroup', 'EvalGroup'):
				out.add(pre + group)
		return out

	def _memberRows(self, subject, extname, partial, args):
		"""Members of ONE extension, addressed as `ext.<Name>.<member>`.

		Everything not underscored, not only the capitalized half: reaching a
		member through `.ext.<Name>` does not require promotion, so the
		lowerCamelCase wiring tier is callable here even though the COMP does
		not expose it. Read off the class and the instance dict rather than
		with getattr, so listing cannot evaluate a property as a side effect.
		"""
		obj, label = None, extname
		for lbl, e in self._namedExtensions(subject):
			if lbl.lower() == (extname or '').lower():
				obj, label = e, lbl
				break
		if obj is None:
			return []
		entries, seen = [], set()
		skip = self._generatedNames(subject)
		for name, val in vars(type(obj)).items():
			if name.startswith('_') or name in seen or name in skip:
				continue
			seen.add(name)
			if isinstance(val, property):
				entries.append((name, '', 0, 'property'))
			elif callable(val):
				sig, required = self._signatureOf(val)
				entries.append((name, sig, required, 'method'))
		for name, val in vars(obj).items():
			if name.startswith('_') or name in seen or name in skip:
				continue
			seen.add(name)
			entries.append((name, '', 0, type(val).__name__))
		rows = []
		for name, sig, required, note in entries:
			score = 0
			if partial:
				score = self._subsequenceScore(partial, name)
				if score is None:
					continue
			rows.append({'kind': self.KIND_METHOD, 'title': name + sig,
						 'key': 'method:%s#%s.%s' % (subject.path, label, name),
						 'category': '%s: %s' % (label, note), 'detail': note,
						 'path': subject.path, 'method': name, 'extname': label,
						 'args': args, 'required': required, 'params': [],
						 'state': None, 'contexts': [], 'available': True,
						 '_score': score})
		rows.sort(key=lambda r: (-r['_score'], r['title'].lower()))
		return rows

	def _methodRows(self, query):
		"""Public methods of the subject's PROMOTED extensions, as rows.

		Promoted means reachable on the COMP itself (`comp.Method`), which is
		also how Enter calls it, so the palette can never run something the
		COMP does not expose.
		"""
		rest = (query or '~')[1:].strip()
		parts = rest.split()
		partial, args = (parts[0] if parts else ''), parts[1:]
		subject = self._methodSubject()
		if subject is None:
			return []
		scope, scoped = self._parseMethodHead(partial)
		if scope is self._SCOPE_EXTLIST:
			return self._extensionRows(subject, scoped)
		if scope is not None:
			return self._memberRows(subject, scope, scoped, args)
		rows = []
		exts = self._extensionsOf(subject)
		multi = len(exts) > 1
		for ext in exts:
			cls = type(ext).__name__
			for name in dir(ext):
				if not name[:1].isupper() or not hasattr(subject, name):
					continue
				try:
					fn = getattr(ext, name)
				except Exception:
					continue
				if not callable(fn):
					continue
				required = 0
				try:
					sig = inspect.signature(fn)
					shown = []
					for prm in sig.parameters.values():
						if prm.kind == prm.VAR_POSITIONAL:
							shown.append('*' + prm.name)
						elif prm.kind == prm.VAR_KEYWORD:
							shown.append('**' + prm.name)
						elif prm.default is prm.empty:
							shown.append(prm.name)
							if prm.kind in (prm.POSITIONAL_ONLY, prm.POSITIONAL_OR_KEYWORD):
								required += 1
						else:
							shown.append('%s=%r' % (prm.name, prm.default))
					sig = '(%s)' % ', '.join(shown)
				except (TypeError, ValueError):
					sig = '(...)'
				doc = (inspect.getdoc(fn) or '').strip().split(chr(10))[0]
				cap = max(20, 62 - len(name + sig))   # one 640px line: title + doc + badge
				if len(doc) > cap:
					doc = doc[:cap - 1].rstrip() + '~'
				rows.append({'kind': self.KIND_METHOD,
							 'key': 'method:%s#%s' % (subject.path, name),
							 'title': name + sig,
							 'category': ((cls + ': ' if multi else '') + doc) if doc else cls,
							 'detail': doc, 'path': subject.path, 'method': name,
							 'args': args, 'required': required,
							 'params': [], 'state': None, 'contexts': [], 'available': True})
		if not partial:
			rows.sort(key=lambda r: r['method'].lower())
			return rows
		scored = []
		for r in rows:
			score = self._subsequenceScore(partial, r['method'])
			if score is not None:
				scored.append((score, r))
		scored.sort(key=lambda pair: (-pair[0], pair[1]['method'].lower()))
		return [r for _, r in scored]

	@staticmethod
	def _rowHead(row):
		"""The text after `~` that names this row exactly, canonical form."""
		if row.get('kind') == CommandPaletteExt.KIND_EXT:
			return 'ext.%s.' % row['extname']
		if row.get('extname'):
			return 'ext.%s.%s' % (row['extname'], row['method'])
		return row['method']

	@classmethod
	def _namesMethod(cls, query, row):
		"""Has the user already typed this row's name after `~`?

		`ext.` is optional in what they type -- `~ExtTest.Hello` names the same
		member as `~ext.ExtTest.Hello` -- so it is stripped before comparing.
		"""
		parts = (query or '')[1:].strip().split()
		if not parts:
			return False
		head = parts[0]
		if head.lower().startswith('ext.'):
			head = head[4:]
		want = cls._rowHead(row)
		if want.lower().startswith('ext.'):
			want = want[4:]
		return head == want

	def _completeExt(self, row):
		"""`~ext.<Name>.` -- scope the list to one extension's members."""
		inp = self._ui('panel/input')
		if inp is None:
			return {'ok': False, 'error': 'no input field'}
		inp.par.text = '~ext.%s.' % row['extname']
		run("me.ext.CommandPaletteExt._focusInput()", fromOP=self.ownerComp, delayFrames=1)
		return {'ok': True, 'scoped': row['extname']}

	def _completeMethod(self, row):
		"""Put the method into the input so arguments can be typed after it.

		Selecting a method used to CALL it on the spot, which left nowhere to
		put arguments: anything with a required parameter simply refused until
		you had guessed the whole name yourself and typed the values behind it.
		So the first Enter completes -- the row becomes `~Method ` in the field
		and the list re-ranks to it -- and the second Enter runs it. Writing
		the input's text is the same mechanism `_drill` uses for tool rows.
		"""
		inp = self._ui('panel/input')
		if inp is None:
			return {'ok': False, 'error': 'no input field'}
		inp.par.text = '~%s ' % self._rowHead(row)
		run("me.ext.CommandPaletteExt._focusInput()", fromOP=self.ownerComp, delayFrames=1)
		return {'ok': True, 'completed': row['method']}

	def _runMethod(self, row):
		"""Call a promoted method THROUGH the COMP, with the inline arguments."""
		comp = op(row['path'])
		if comp is None or not comp.valid:
			return {'ok': False, 'error': 'subject %s is gone' % row['path']}
		if row.get('extname'):
			# addressed as ext.<Name>.<member>, which does NOT require the
			# member to be promoted -- that is the whole point of the form
			holder = getattr(comp.ext, row['extname'], None)
			if holder is None:
				return {'ok': False, 'error': 'no extension %s on %s' % (row['extname'], comp.path)}
			fn = getattr(holder, row['method'], None)
			called = '%s.ext.%s.%s' % (comp.path, row['extname'], row['method'])
		else:
			fn = getattr(comp, row['method'], None)
			called = '%s.%s' % (comp.path, row['method'])
		if fn is None:
			return {'ok': False, 'error': '%s is no longer promoted on %s' % (row['method'], comp.path)}
		if not callable(fn):
			return {'ok': True, 'called': called, 'result': repr(fn)[:200]}
		args = [self._coerce(a) for a in (row.get('args') or [])]
		try:
			out = fn(*args)
		except Exception as exc:
			return {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)}
		return {'ok': True, 'called': called, 'result': repr(out)[:200]}

	# --- the `#` prefix: one tool's commands ------------------------------------

	def _toolRows(self, query):
		"""`#` lists the tools (one row each); `#tool ` lists that tool's commands.

		A tool is matched by name or by the `capability` its commands declare,
		so `#quick` finds QuickMarks, QuickPane and friends.
		"""
		rest = (query or '#')[1:]
		tok, sep, sub = rest.partition(' ')
		tok, sub = tok.strip(), sub.strip()
		cmds = [r for r in self.Catalogue() if r['kind'] == self.KIND_COMMAND]
		if not sep and tok and any(r['category'].lower() == tok.lower() for r in cmds):
			sep = ' '                   # the full name typed: list its commands
		if not sep:
			counts = {}
			for r in cmds:
				counts[r['category']] = counts.get(r['category'], 0) + 1
			rows = []
			for tool, n in counts.items():
				score = self._subsequenceScore(tok, tool) if tok else 0.0
				if score is None:
					caps = {r.get('capability') for r in cmds if r['category'] == tool}
					if not any(c and self._subsequenceScore(tok, c) is not None for c in caps):
						continue
					score = 0.3
				rows.append((score, {
					'kind': self.KIND_TOOL, 'key': 'tool:' + tool, 'title': tool,
					'category': '%d command%s' % (n, '' if n == 1 else 's'),
					'detail': '', 'path': '', 'params': [], 'state': None,
					'contexts': [], 'available': True, 'tool': tool}))
			rows.sort(key=lambda pair: (-pair[0], pair[1]['title'].lower()))
			return [r for _, r in rows]
		low = tok.lower()
		chosen = ([r for r in cmds if r['category'].lower() == low]
				  or [r for r in cmds if low in r['category'].lower()
					  or low in (r.get('capability') or '').lower()])
		if not sub:
			return sorted(chosen, key=lambda r: r['title'].lower())
		scored = []
		for r in chosen:
			score = self._rowScore(sub, r)
			if score is not None:
				scored.append((score, r))
		scored.sort(key=lambda pair: (-pair[0], pair[1]['title'].lower()))
		return [r for _, r in scored]

	# --- favourites and history ---------------------------------------------
	# Favourites, hidden/shown overrides and presets live in the command
	# curation file SHARED with the launcher (docs/CommandCuration.md), via
	# CommandCuration.CurationFile. The three Str pars declared above are the
	# store from before that file existed: adopted once on first read, then
	# emptied. Query history stays on its par and roams with the config.

	def _jsonPar(self, name):
		par = getattr(self.ownerComp.par, name, None)
		if par is None:
			return []
		try:
			value = json.loads(str(par.eval()) or '[]')
		except ValueError:
			value = []
		return value if isinstance(value, list) else []

	def _setJsonPar(self, name, values):
		par = getattr(self.ownerComp.par, name, None)
		if par is not None:
			par.val = json.dumps(list(values))

	# --- curation identity ----------------------------------------------------
	# Favourites, hidden overrides and presets are keyed by `tool#id`, the
	# identity the launcher's config uses, NOT by the wire key `path#id`: the
	# wire key encodes where the owner sits, so moving a tool would silently
	# detach every favourite, override and preset. `tool` on the wire is the
	# owner's name, so the two derivations agree for every command (measured
	# 141/141, 2026-09-02). The wire key is still what Run() takes; rows carry
	# both. Entries stored before the switch migrate on first read.

	@staticmethod
	def _identity(cmd) -> str:
		return '%s#%s' % (cmd.get('tool') or '', cmd.get('id') or '')

	@staticmethod
	def _migrateIdent(value) -> str:
		"""`/path/Tool#id` from before the switch becomes `Tool#id`; anything
		else (an identity, a `palette:` or `preset:` key) is returned as is."""
		v = str(value or '')
		if v.startswith('/') and '#' in v:
			return v.rsplit('/', 1)[-1]
		return v

	@staticmethod
	def _curationId(row) -> str:
		return row.get('ident') or row.get('key') or ''

	# --- multiple instances (registry >= 1.11.0) -------------------------------
	# A tool that exists as several copies registers each copy on its own path
	# and labels it with `instance`. Favourites and hidden overrides stay on the
	# shared `tool#id` (they are about the capability, not the copy). A preset
	# may pin one copy: its target is then `tool#id@instance`. An unpinned
	# preset over a multi-instance command lists once per live copy, since
	# "run on whichever registered first" is not a meaning anyone chose.

	@staticmethod
	def _instanceTitle(title: str, instance: str) -> str:
		return '%s · %s' % (title, instance) if instance else title

	@staticmethod
	def _splitTarget(target: str):
		"""`tool#id@instance` -> ('tool#id', 'instance'); no `@` -> (target, None).
		Tool names and ids cannot contain `@`, so the first `@` is the split."""
		ident, sep, instance = str(target or '').partition('@')
		return ident, (instance if sep and instance else None)

	@classmethod
	def _presetTarget(cls, row) -> str:
		"""What a preset authored from ROW targets: pinned to the row's copy
		when the command carries an instance label, else the shared identity."""
		ident = cls._curationId(row)
		return '%s@%s' % (ident, row['instance']) if row.get('instance') else ident

	def _curation(self):
		"""The shared curation file, opened on first use; the legacy pars are
		adopted into it once (a union) and emptied."""
		if self._curationFile is None:
			module = self.ownerComp.op('CommandCuration').module
			self._curationFile = module.CurationFile(seed=self._legacyCuration, log=debug)
		return self._curationFile

	def _legacyCuration(self) -> dict:
		"""Everything the three pars held before the shared file (2026-09-02),
		shaped like the file. The pars are emptied so this runs once per
		project; identities stored before the tool#id switch migrate here."""
		import time
		now = time.time()
		data = {'commands': {}, 'presets': {}}
		for k in self._jsonPar('Favouritekeys'):
			ident = self._migrateIdent(k)
			if ident:
				data['commands'].setdefault(ident, {})['favorite'] = True
		par = getattr(self.ownerComp.par, 'Visibilityoverrides', None)
		try:
			over = json.loads(str(par.eval()) or '{}') if par is not None else {}
		except ValueError:
			over = {}
		for k, v in (over.items() if isinstance(over, dict) else []):
			ident = self._migrateIdent(k)
			if ident:
				data['commands'].setdefault(ident, {})['hidden'] = bool(v)
		for p in self._jsonPar('Presets'):
			if not (isinstance(p, dict) and (p.get('ident') or p.get('key'))):
				continue
			pid = str(p.get('id') or '') or __import__('uuid').uuid4().hex[:8]
			target = p.get('ident') or self._migrateIdent(p.get('key'))
			data['presets'][pid] = {'label': str(p.get('label') or target), 'target': target,
									'kwargs': dict(p.get('args') or {})}
		for section in data.values():
			for entry in section.values():
				entry['updated'] = now
		for name, blank in (('Favouritekeys', '[]'), ('Visibilityoverrides', '{}'), ('Presets', '[]')):
			par = getattr(self.ownerComp.par, name, None)
			if par is not None:
				par.val = blank
		return data

	def Favourites(self) -> set:
		"""Identities (tool#id) starred with Ctrl+D here or in the launcher."""
		return self._curation().favourites()

	def ToggleFavourite(self, key: str) -> bool:
		on = key not in self.Favourites()
		self._curation().set_favourite(key, on)
		return on

	def History(self) -> list:
		"""Executed queries, oldest first."""
		return self._jsonPar('Queryhistory')

	def _pushHistory(self, query):
		q = (query or '').strip()
		if not q:
			return
		items = [x for x in self.History() if x != q] + [q]
		self._setJsonPar('Queryhistory', items[-self.HISTORY_CAP:])

	# --- usage: frequently run commands rank higher (docs/CommandUsage.md) ------
	# A second file shared with the launcher, beside the curation file. Every
	# successful command or preset run records against the command's tool#id;
	# the bonus is 0..8, below FAVOURITE_BONUS, so it only breaks ties.

	def _usage(self):
		if self._usageFile is None:
			module = self.ownerComp.op('CommandCuration').module
			self._usageFile = module.UsageFile(log=debug)
		return self._usageFile

	def _usageId(self, row) -> str:
		"""The tool#id a row's usage counts against: a command's own, a
		preset's target command's; nothing for components and the rest."""
		if row.get('kind') == self.KIND_COMMAND:
			return row.get('ident') or ''
		if row.get('kind') == self.KIND_PRESET and row.get('command'):
			return self._identity(row['command'])
		return ''

	def _usageBonuses(self) -> dict:
		par = getattr(self.ownerComp.par, 'Rankbyusage', None)
		if par is not None and not par.eval():
			return {}
		try:
			return self._usage().bonuses()
		except Exception as exc:
			debug('FNS_CommandPalette: usage file not read (%s)' % exc)
			return {}

	def _recordUsage(self, ident: str) -> None:
		try:
			self._usage().record(ident)
		except Exception as exc:
			debug('FNS_CommandPalette: usage not recorded (%s)' % exc)

	def UsageBonus(self, key: str) -> float:
		"""The current ranking bonus (0..8) for a command identity, tool#id."""
		return self._usage().bonuses().get(key, 0.0)

	def ClearUsage(self) -> bool:
		"""Forget this palette's usage history. The launcher's history is in
		its own block of the shared file and still counts."""
		return self._usage().clear()

	# --- presets: a command with its arguments baked in, under a name ----------
	# Authored with Alt+S (during a parameter walk, or on any command row) and
	# resolved against the UNFILTERED command set, so a preset over a hidden
	# command still runs: authoring the preset is the opt-in.

	def ListPresets(self) -> list:
		# not Presets(): that name is the DECLARED PAR above, and a method of
		# the same name would shadow the declaration before Init ever saw it
		return self._curation().presets()

	def SavePreset(self, ident: str, args: dict, label: str) -> dict:
		"""Add a preset over the command with identity `ident` (tool#id), `args` baked in."""
		preset = self._curation().add_preset(label=label, target=ident, kwargs=args)
		self._catalogue = None
		return preset

	def DeletePreset(self, preset_id: str) -> bool:
		if not self._curation().delete_preset(preset_id):
			return False
		self._catalogue = None
		return True

	def _presetRows(self) -> list:
		"""Every preset as a row, carrying the live command it runs."""
		presets = self.ListPresets()
		if not presets:
			return []
		reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
		commands = {}                             # identity -> every live copy of it
		if reg is not None and hasattr(reg, 'Commands'):
			for cmd in reg.Commands():            # unfiltered: hidden ones included
				commands.setdefault(self._identity(cmd), []).append(cmd)
		rows = []
		for p in presets:
			ident, pinned = self._splitTarget(p['ident'])
			copies = commands.get(ident, [])
			if pinned is not None:
				copies = [c for c in copies if c.get('instance') == pinned]
			args = p.get('args') or {}
			summary = ', '.join('%s=%s' % (k, v) for k, v in args.items())
			if not copies:
				rows.append({'kind': self.KIND_PRESET, 'key': 'preset:' + p['id'], 'preset': p,
							 'ident': 'preset:' + p['id'],
							 'title': p['label'], 'detail': '', 'params': [], 'state': None,
							 'command': None, 'args': args,
							 'category': 'command missing: ' + p['ident'],
							 'path': '', 'contexts': [], 'available': False})
				continue
			for cmd in copies:
				instance = cmd.get('instance') or ''
				# One row per copy only when the preset is unpinned AND several
				# copies are live; the key must stay unique per row.
				spread = pinned is None and len(copies) > 1
				contexts = cmd.get('context') or []
				rows.append({
					'kind': self.KIND_PRESET,
					'key': 'preset:' + p['id'] + (('@' + (cmd.get('key') or '')) if spread else ''),
					# Curation (favourite star) stays on the preset, not the copy.
					'ident': 'preset:' + p['id'],
					'preset': p,
					'title': self._instanceTitle(p['label'], instance if spread else ''),
					'detail': cmd.get('help') or '', 'params': [], 'state': None,
					'command': cmd, 'args': args,
					'category': self._instanceTitle(cmd.get('label') or cmd.get('id') or '', instance)
								+ ((' - ' + summary) if summary else ''),
					'path': cmd.get('path') or '',
					'contexts': contexts, 'available': self._isAvailable(contexts)})
		return rows

	# --- hidden, and the manager tab ------------------------------------------
	# The Commands tab in FNS_Hub edits the same pars the palette reads, so the
	# two can never disagree. The effective state of a command is the user's
	# override when there is one, else the tool's declared `hidden`.

	def _overrides(self):
		"""identity -> True (hidden) / False (shown); absent = the tool's default."""
		return self._curation().overrides()

	def _registryCommands(self):
		reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
		if reg is None or not hasattr(reg, 'Commands'):
			return []
		return reg.Commands()

	def IsHidden(self, key: str) -> bool:
		default = next((bool(c.get('hidden')) for c in self._registryCommands()
						if self._identity(c) == key), False)
		return bool(self._overrides().get(key, default))

	def ToggleHidden(self, key: str) -> bool:
		"""Flip a command's visibility. An override equal to the tool's own
		default is dropped, so the dict only ever holds real choices."""
		default = next((bool(c.get('hidden')) for c in self._registryCommands()
						if self._identity(c) == key), False)
		new = not bool(self._overrides().get(key, default))
		self._curation().set_hidden(key, None if new == default else new)
		self._catalogue = None
		return new

	def RefreshManager(self) -> int:
		"""Rebuild the Commands tab's table: every registry command, hidden
		ones included, with the star and hidden state from the prefs."""
		table = self._ui('manager/table_commands')
		if table is None:
			return 0
		favs, over = self.Favourites(), self._overrides()
		table.clear()
		table.appendRow(['Tool', 'Command', 'Context', 'Star', 'Hidden', 'Key'])
		cmds = sorted(self._registryCommands(),
					  key=lambda c: ((c.get('tool') or '').lower(), (c.get('label') or '').lower()))
		for c in cmds:
			key = self._identity(c)
			hidden = over.get(key, bool(c.get('hidden')))
			table.appendRow([c.get('tool') or '', c.get('label') or c.get('id') or '',
							 ', '.join((['built-in'] if c.get('builtin') else []) + list(c.get('context') or [])),
							 '*' if key in favs else '', 'hidden' if hidden else '', key])
		lister = self._ui('manager/lister')
		if lister is not None and hasattr(lister.par, 'Refresh'):
			lister.par.Refresh.pulse()
		self._catalogue = None
		return table.numRows - 1

	def OnManagerButton(self, name: str):
		"""The toolbar buttons on the Commands tab."""
		if name == 'btn_refresh':
			return self.RefreshManager()
		if name == 'btn_palette':
			return self.Summon()
		if name == 'btn_clearhistory':
			self._setJsonPar('Queryhistory', [])
			return self.RefreshManager()
		if name == 'btn_clearusage':
			self.ClearUsage()
			return self.RefreshManager()
		return None

	def OnHubExposure(self, exposed: bool):
		"""FNS_Hub tells a tab's component when it is shown; rebuild then."""
		if exposed:
			self.RefreshManager()

	# --- activation --------------------------------------------------------

	def Activate(self, row: dict, args: dict = None) -> dict:
		"""Enter on a row. Returns a result dict; never raises at the caller."""
		if not row:
			return {'ok': False, 'error': 'no row'}
		if row['kind'] == self.KIND_COMMAND:
			return self._runCommand(row, args or {})
		if row['kind'] == self.KIND_PRESET:
			if not row.get('command'):
				return {'ok': False, 'error': 'the preset\'s command is gone'}
			return self._runCommand(row['command'], row.get('args') or {})
		if row['kind'] == self.KIND_COMPONENT:
			return self._placeComponent(row)
		if row['kind'] == self.KIND_NETWORK:
			return self._navigateTo(row['path'])
		if row['kind'] == self.KIND_METHOD:
			return self._runMethod(row)
		if row['kind'] == self.KIND_TOOL:
			self._drill()
			return {'ok': True, 'listed': row.get('tool')}
		return {'ok': False, 'error': 'unknown row kind %r' % row.get('kind')}

	def _runCommand(self, row, args) -> dict:
		reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
		if reg is None or not hasattr(reg, 'Run'):
			return {'ok': False, 'error': 'no command registry'}
		try:
			result = reg.Run(row['key'], kwargs=(args or None)) or {'ok': True}
		except Exception as exc:
			return {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)}
		if not (isinstance(result, dict) and result.get('ok') is False):
			# a command row carries its ident; a preset hands over the raw command
			self._recordUsage(row.get('ident') or self._identity(row))
		return result

	def _placeComponent(self, row) -> dict:
		"""Load a palette .tox into the network the palette was summoned over.

		The target is the SNAPSHOT's network, not the current pane -- by the
		time a row is chosen the palette's own window is what is current.
		"""
		target = self.Context().get('network')
		if target is None or not target.valid:
			return {'ok': False, 'error': 'no network to place into'}
		try:
			placed = target.loadTox(row['path'])
		except Exception as exc:
			return {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)}
		if placed is None:
			return {'ok': False, 'error': 'loadTox returned nothing'}
		placed = self._unwrapBundle(placed, target, bundled=bool(row.get('bundled')))
		self._placeAt(placed, target)
		placed.current = True
		placed.selected = True
		# Hand the component to the mouse, the way the OP Create dialog hands
		# over a new operator: the user clicks where it goes. Deferred past
		# the palette's own close so the pane has focus again; the fallback
		# position above stands if the pane is gone by then.
		pane = self.Context().get('pane')
		run("args[0].valid and args[1].valid and args[0].ext.CommandPaletteExt._placeWithMouse(args[1], args[2])",
			self.ownerComp, placed, pane, delayFrames=2, delayRef=op.TDResources)
		return {'ok': True, 'placed': placed.path}

	@staticmethod
	def _placeWithMouse(placed, pane):
		"""NetworkEditor.placeOPs: the component follows the cursor in the
		snapshot's pane until the user clicks. Only when that pane still shows
		the network the component was loaded into."""
		try:
			if pane is None or pane.type != PaneType.NETWORKEDITOR or pane.owner is not placed.parent():
				return False
			pane.placeOPs([placed], undoName='Place ' + placed.name)
			return True
		except Exception as exc:
			debug('CommandPalette: placeOPs failed:', exc)
			return False

	@staticmethod
	def _unwrapBundle(placed, target, bundled=False):
		"""A built-in palette .tox is a bundle: a base named X holding the
		component X beside an `icon` TOP and a `help` DAT. Lift X out and drop
		the wrapper, keeping X's name. The shape is checked as well as the
		flag, so a user tox that happens to nest a same-named COMP is left
		alone unless it also carries the bundle's icon."""
		inner = placed.op(placed.name) if placed.isCOMP else None
		if inner is None or not inner.isCOMP:
			return placed
		looks_bundled = bundled or placed.op('icon') is not None
		if not looks_bundled:
			return placed
		name = placed.name
		lifted = target.copy(inner)       # uniquified beside the wrapper
		placed.destroy()
		try:
			lifted.name = name
		except Exception:
			pass
		return lifted

	# --- dragging a component row out, TD's palette browser way ---------------
	#
	# The rows use the LEGACY drag with a Drop Destination Script
	# (panel/dropdest), which is exactly how /ui/dialogs/palette drags: TD
	# drags the row panel itself, and at the drop it copies the row into a
	# temporary network and runs the script, which loads the row's .tox
	# there, unwraps a built-in bundle and prints the component's path; TD
	# then copies that into the drop network. Nothing printed = nothing
	# dropped, which is what a command row does.

	def dragPathFor(self, comp):
		"""panel/dropdest: the (.tox path, bundled) behind a row panel, or
		None when that row is not a component."""
		name = getattr(comp, 'name', '') or ''
		if not name.startswith('row'):
			return None
		try:
			i = int(name[3:])
		except ValueError:
			return None
		if i >= len(self._rows):
			return None
		r = self._rows[i]
		if r.get('kind') != self.KIND_COMPONENT or not r.get('path'):
			return None
		return (r['path'], bool(r.get('bundled')))

	def rowReleased(self, index: int, inside: bool = True):
		"""panel/panelexec_rows: the mouse button came up on a row. Released
		INSIDE the row it is a click and does what Enter does; released
		elsewhere it was a drag (the legacy drag has no callback of its own
		to say so) and activates nothing."""
		if not inside:
			return
		self.OnRowClick(index)

	@staticmethod
	def _placeAt(placed, target):
		"""Put a newly placed component somewhere sane.

		loadTox drops it at the origin, and a component left at (0, 0) on top
		of whatever is already there is the exact failure the layout rules
		exist to prevent. Right of everything, snapped to the 200 grid.
		"""
		try:
			siblings = [c for c in target.children if c is not placed]
			if siblings:
				right = max(c.nodeX + c.nodeWidth for c in siblings)
				top = max(c.nodeY for c in siblings)
				placed.nodeX = int((int(right + 200) // 200 + 1) * 200)
				placed.nodeY = int(top // 200 * 200)
			else:
				placed.nodeX, placed.nodeY = 0, 0
		except Exception:
			pass

	# --- UI ------------------------------------------------------------------
	#
	# The window and its rows. This half is thin on purpose: it reads the
	# ranked list and paints it. Twelve fixed Text COMPs are refreshed in
	# place -- no replicator, because rebuilding operators on every keystroke
	# is the one cost a palette must never pay.

	ROW_COUNT = 12
	COL_TEXT = (0.80, 0.80, 0.82)
	COL_DIM = (0.46, 0.46, 0.52)
	COL_OFF = (0.36, 0.36, 0.40)
	COL_SEL_TEXT = (0.98, 0.98, 1.00)
	COL_SEL_DIM = (0.78, 0.84, 0.96)     # category text stays legible on the accent bar
	COL_BUILTIN = (0.60, 0.80, 0.55)     # TD's own commands: a hue no row kind uses
	COL_INSTALL = (0.95, 0.58, 0.48)     # "Install <tool>" rows served by FNS_Installer
	INSTALL_IDENT_PREFIX = 'Installer#install-'   # docs/CommandAvailability.md
	# one hue per row kind, kept under the saturation ceiling; lifted toward
	# white on the accent bar so the badge stays legible when selected
	KIND_COLOUR = {KIND_COMMAND: (0.93, 0.68, 0.30),
				   KIND_COMPONENT: (0.36, 0.78, 0.72),
				   KIND_NETWORK: (0.64, 0.68, 0.94),
				   KIND_METHOD: (0.90, 0.58, 0.66),
				   KIND_EXT: (0.78, 0.62, 0.90),
				   KIND_TOOL: (0.93, 0.68, 0.30),
				   KIND_PICK: (0.93, 0.68, 0.30),
				   KIND_PRESET: (0.90, 0.86, 0.48)}
	CONTEXT_TAG = {'rollover-par': 'par', 'current': 'op', 'selected': 'op', 'network': 'net'}

	def _ui(self, name):
		return self.ownerComp.op(name)

	def Summon(self):
		"""Open the palette over whatever the user is looking at right now.

		The context snapshot is taken FIRST, before the window can take
		focus -- see CaptureContext for why that order is the whole design.
		"""
		self.CaptureContext()
		self._query = ''
		self._selected = 0
		self._pending = None
		self._histPos = None
		self._restorePlaceholder()
		self.Catalogue(rebuild=True)
		inp = self._ui('panel/input')
		if inp is not None:
			inp.par.text = ''
		self._refresh()
		kb = self._ui('keyboardin')
		if kb is not None:
			kb.par.active = True
		win = self._ui('window')
		if win is not None:
			win.par.winopen.pulse()
		# the window needs a couple of frames to exist before anything
		# inside it can take keyboard focus
		run("me.ext.CommandPaletteExt._focusInput()", fromOP=self.ownerComp,
			delayFrames=3)
		return True

	def _focusInput(self):
		inp = self._ui('panel/input')
		if inp is None:
			return
		for name in ('setKeyboardFocus', 'setFocus'):
			fn = getattr(inp, name, None)
			if fn is None:
				continue
			try:
				fn()
				return
			except Exception:
				continue

	def Dismiss(self):
		"""Close the palette and stop listening for keys."""
		kb = self._ui('keyboardin')
		if kb is not None:
			kb.par.active = False
		win = self._ui('window')
		if win is not None and win.isOpen:
			win.par.winclose.pulse()
		return True

	def IsOpen(self):
		win = self._ui('window')
		return bool(win is not None and win.isOpen)

	def OnQuery(self, text):
		"""Every keystroke in the input lands here (editablecontinuous).

		While a parameter walk is pending the text is a VALUE, not a query.
		"""
		if self._pending is not None:
			self._pending['text'] = text or ''
			self._selected = 0
			self._paintPending()
			return
		if self._recalling:
			self._recalling = False          # a history recall, not the user typing
		else:
			self._histPos = None
		self._query = text or ''
		self._selected = 0
		self._refresh()

	def OnKey(self, key, ctrl=False, alt=False, shift=False):
		"""Raw key names from the Keyboard In DAT while the palette is open."""
		k = (key or '').lower()
		self._lastKeys = (self._lastKeys + [k])[-8:]
		if alt and k == 'up':
			self._historyStep(-1)
		elif alt and k == 'down':
			self._historyStep(+1)
		elif ctrl and k == 'd':
			self._toggleSelectedFavourite()
		elif ctrl and k == 'h':
			self._toggleSelectedHidden()
		elif alt and k == 's':
			self._beginNaming()
		elif k == 'up':
			self._select(self._selected - 1)
		elif k == 'down':
			self._select(self._selected + 1)
		elif k in ('enter', 'return', 'kpenter'):
			self.ActivateSelected()
		elif k in ('esc', 'escape'):
			if self._pending is not None:
				self._endPending()           # back out of the walk, not the palette
			else:
				self.Dismiss()
		elif k == 'tab':
			self._completeSelected()
		elif k == 'right':
			self._drill()
		elif k == 'left':
			if self._pending is not None:
				self._pendingBack()
			else:
				self._drillBack()

	def _completeSelected(self):
		"""Tab: take the selected row's name into the input, and never run it.

		Enter is deliberately two-faced -- it completes, then runs -- so Tab is
		the half that only ever completes. It is also what accepts the greyed
		guess, because the guess IS the selected row.
		"""
		if not self._rows:
			return {'ok': False, 'error': 'nothing to complete'}
		r = self._rows[self._selected]
		if r['kind'] == self.KIND_EXT:
			return self._completeExt(r)
		if r['kind'] == self.KIND_METHOD:
			return self._completeMethod(r)
		if r['kind'] in (self.KIND_NETWORK, self.KIND_TOOL):
			self._drill()
			return {'ok': True, 'completed': r.get('title')}
		return {'ok': False, 'error': 'nothing to complete for a %s row' % r['kind']}

	def _drill(self):
		"""Right on a network row descends into it; on a tool row lists its
		commands. Writing the input's text fires its callback, so the list
		re-ranks by itself."""
		if not self._rows:
			return
		r = self._rows[self._selected]
		inp = self._ui('panel/input')
		if inp is None:
			return
		if r['kind'] == self.KIND_NETWORK:
			inp.par.text = self._drillText(r)
		elif r['kind'] == self.KIND_TOOL:
			inp.par.text = '#' + r['tool'] + ' '
		elif r['kind'] == self.KIND_METHOD:
			inp.par.text = '~%s ' % self._rowHead(r)   # Right completes, as Enter does
		elif r['kind'] == self.KIND_EXT:
			inp.par.text = '~ext.%s.' % r['extname']

	def _drillText(self, r):
		"""The query that lists INSIDE a network row, in the convention the
		user is typing in: absolute stays absolute, relative stays relative."""
		q = self._query
		head = q.rsplit('/', 1)[0] if '/' in q else q
		base, _ = self._navigationBase(q)
		if base is not None and r['path'] == base.path:      # the "this network" row
			return (head + '/') if head else '/'
		if head in ('', '/'):
			return '/' + r['title'] + '/'
		return head.rstrip('/') + '/' + r['title'] + '/'

	def _drillBack(self):
		"""Left: list the parent of the current listing, in the same
		convention; while filtering by tool, back to the tool list."""
		inp = self._ui('panel/input')
		if inp is None:
			return
		q = self._query
		if q.startswith('#'):
			inp.par.text = '#'
			return
		if q.startswith('/'):
			base, _ = self._navigationBase(q)
			parent = base.parent() if base is not None else None
			inp.par.text = (parent.path.rstrip('/') + '/') if parent is not None else '/'
			return
		if not q.startswith('.'):
			return
		parts = q.split('/')
		if parts and parts[-1] not in ('', '.', '..'):
			parts = parts[:-1]                     # a partial name is not a directory
		dirs = [d for d in parts if d != '']
		if dirs and dirs[-1] not in ('.', '..'):
			dirs = dirs[:-1]
		else:
			dirs.append('..')
		text = '/'.join(dirs) + '/'
		while text.startswith('./../'):
			text = text[2:]
		inp.par.text = text

	def _historyStep(self, delta):
		"""Alt+Up / Alt+Down: cycle executed queries, shell style."""
		items = self.History()
		if not items:
			return
		pos = len(items) if self._histPos is None else self._histPos
		pos = max(0, min(len(items), pos + delta))
		self._histPos = pos
		text = items[pos] if pos < len(items) else ''
		inp = self._ui('panel/input')
		if inp is None or str(inp.par.text.eval()) == text:
			return
		self._recalling = True               # OnQuery must not reset the cursor
		inp.par.text = text

	def _toggleSelectedFavourite(self):
		"""Ctrl+D on a command or component row."""
		if not self._rows:
			return
		r = self._rows[self._selected]
		if r['kind'] not in (self.KIND_COMMAND, self.KIND_COMPONENT, self.KIND_PRESET):
			return
		self.ToggleFavourite(self._curationId(r))
		self._paint()

	def _toggleSelectedHidden(self):
		"""Ctrl+H: hide the selected command from the palette (the Commands
		tab in FNS_Hub shows it again); on a preset row, delete the preset."""
		if not self._rows or self._pending is not None:
			return
		r = self._rows[self._selected]
		if r['kind'] == self.KIND_PRESET:
			self.DeletePreset(r['preset']['id'])
		elif r['kind'] == self.KIND_COMMAND:
			self.ToggleHidden(self._curationId(r))
		else:
			return
		self._catalogue = None
		self._refresh()

	# --- preset authoring: Alt+S ---------------------------------------------

	def _beginNaming(self):
		"""Alt+S. During a parameter walk: bake what has been entered so far,
		the current field included if it parses, plus defaults, then ask for
		a name. On a command row outside a walk: an alias under a name of its
		own. The name prompt reuses the walk's own field and footer."""
		pend = self._pending
		if pend is not None:
			if pend.get('naming'):
				return
			row = pend['row']
			values = dict(pend['values'])
			prm = self._pendingParam()
			if prm is not None:
				value, error = self._parsePendingValue()
				if error:
					self._paintPending(error)
					return
				if value is not None:
					values[prm.get('name')] = value
			for prm in row.get('params') or []:
				if prm.get('name') not in values and prm.get('default') is not None:
					values[prm.get('name')] = prm.get('default')
			prev_query = pend.get('prev_query') or ''
		else:
			if not self._rows:
				return
			row = self._rows[self._selected]
			if row['kind'] != self.KIND_COMMAND:
				return
			values, prev_query = {}, self._query
		summary = ' '.join('%s=%s' % (k, v) for k, v in values.items())
		suggested = (row['title'] + (' ' + summary if summary else ''))[:48]
		self._pending = {'row': row, 'index': 0, 'values': values, 'text': '',
						 'prev_query': prev_query, 'naming': True,
						 'params': [{'name': '_label', 'label': 'Preset name', 'style': 'str',
									 'required': True, 'default': suggested,
									 'help': 'Enter saves the preset'}]}
		self._promptParam()

	def _savePreset(self, label):
		pend = self._pending
		preset = self.SavePreset(self._presetTarget(pend['row']), pend['values'], label)
		self._endPending()
		self._catalogue = None
		self._refresh()
		foot = self._ui('panel/footer')
		if foot is not None:
			foot.par.text = 'Saved preset %s   -   Ctrl+H on it deletes it' % preset['label']
		return {'ok': True, 'preset': preset['id']}

	# --- dismiss on blur --------------------------------------------------------

	def OnInputBlur(self):
		"""The input lost keyboard focus (panel/input_callbacks onFocusEnd).
		Decided a few frames later, because a click on one of our own rows
		blurs the input for a moment before it takes focus back."""
		if self.IsOpen():
			run("me.ext.CommandPaletteExt._checkBlur()", fromOP=self.ownerComp, delayFrames=3)

	def _checkBlur(self):
		if not self.IsOpen():
			return
		inp, panel = self._ui('panel/input'), self._ui('panel')
		if inp is None or panel is None:
			return
		if inp.panel.focus or panel.panel.inside:
			return                    # focus came back, or the mouse is on us
		self.Dismiss()

	def _select(self, index):
		if not self._rows:
			return
		self._selected = max(0, min(index, len(self._rows) - 1))
		self._paint()

	def ActivateSelected(self):
		"""Enter. Dismiss first, so the user is back in their network when a
		placed component appears or a command changes something there."""
		if self._pending is not None:
			return self._acceptPending()
		if not self._rows:
			return {'ok': False, 'error': 'nothing selected'}
		row = self._rows[self._selected]
		if not row.get('available', True):
			self._hint()
			return {'ok': False, 'error': 'unavailable in this context'}
		if row['kind'] == self.KIND_EXT:
			return self._completeExt(row)     # scope to that extension
		if row['kind'] == self.KIND_METHOD and not self._namesMethod(self._query, row):
			return self._completeMethod(row)  # first Enter completes, second runs
		if row['kind'] == self.KIND_METHOD and len(row.get('args') or []) < row.get('required', 0):
			self._hint()                     # the footer already says what it needs
			return {'ok': False, 'error': 'missing arguments'}
		if row['kind'] == self.KIND_TOOL:
			self._drill()
			return {'ok': True, 'listed': row.get('tool')}
		if row['kind'] == self.KIND_COMMAND and row.get('params'):
			return self._beginPending(row)   # walk the parameters first
		self._pushHistory(self._query)
		self.Dismiss()
		return self.Activate(row)

	def OnRowClick(self, index: int):
		"""A mouse click on a row (panel/panelexec_rows): select it, then do
		exactly what Enter does, so clicks and keys can never diverge. If the
		palette stays open -- a refusal, a drill, a parameter prompt -- the
		input takes keyboard focus back so typing keeps working."""
		if not self._rows or index < 0 or index >= len(self._rows):
			return {'ok': False, 'error': 'no such row'}
		self._selected = index
		self._paint()
		out = self.ActivateSelected()
		if self.IsOpen():
			run("me.ext.CommandPaletteExt._focusInput()", fromOP=self.ownerComp, delayFrames=1)
		return out

	# --- the parameter walk ----------------------------------------------------
	# One mechanism for every command that declares `params`: Enter walks them
	# one at a time, a menu param becomes pick rows, the rest a text field;
	# Left steps back a param, Esc backs out to the list. Both reuse the
	# ordinary rows and footer, so nothing new has to be drawn.

	def _beginPending(self, row):
		self._pending = {'row': row, 'index': 0, 'values': {}, 'text': '',
						 'prev_query': self._query}
		self._promptParam()
		return {'ok': True, 'pending': row['key']}

	def _pendingParams(self):
		pend = self._pending
		return (pend.get('params') or pend['row']['params']) if pend else []

	def _pendingParam(self):
		pend = self._pending
		return self._pendingParams()[pend['index']] if pend else None

	def _promptParam(self):
		prm = self._pendingParam()
		inp = self._ui('panel/input')
		if prm is None or inp is None:
			return
		self._pending['text'] = ''
		label = prm.get('label') or prm.get('name') or 'value'
		hint = '%s (%s)' % (label, prm.get('style') or 'str')
		if prm.get('default') is not None:
			hint += '   default %r' % (prm.get('default'),)
		inp.par.placeholdertext = hint
		inp.par.text = ''                    # fires OnQuery -> _paintPending
		self._paintPending()

	def _restorePlaceholder(self):
		inp = self._ui('panel/input')
		if inp is not None:
			inp.par.placeholdertext = self.PLACEHOLDER

	def _menuItems(self, prm):
		items = prm.get('menu') or []
		out = []
		for m in items:
			if isinstance(m, dict):
				name = str(m.get('name', m.get('value', '')))
				out.append((name, str(m.get('label', name))))
			else:
				out.append((str(m), str(m)))
		return out

	def _paintPending(self, error=None):
		prm = self._pendingParam()
		if prm is None:
			return
		pend = self._pending
		typed = pend.get('text') or ''
		label = prm.get('label') or prm.get('name') or 'value'
		if (prm.get('style') or '') == 'menu':
			rows = []
			for name, text in self._menuItems(prm):
				score = self._subsequenceScore(typed, text) if typed else 0.0
				if score is None:
					continue
				rows.append((score, {'kind': self.KIND_PICK, 'key': 'pick:' + name,
									 'title': text, 'category': name if name != text else '',
									 'detail': '', 'path': '', 'params': [], 'state': None,
									 'contexts': [], 'available': True, 'value': name}))
			rows.sort(key=lambda pair: (-pair[0], pair[1]['title'].lower()))
			self._rows = [r for _, r in rows]
		else:
			shown = typed if typed else (repr(prm.get('default')) if prm.get('default') is not None else '')
			self._rows = [{'kind': self.KIND_PICK, 'key': 'pick:' + str(prm.get('name')),
						   'title': '%s = %s' % (label, shown) if shown else label,
						   'category': prm.get('help') or '', 'detail': '', 'path': '',
						   'params': [], 'state': None, 'contexts': [], 'available': True,
						   'value': None}]
		self._selected = max(0, min(self._selected, max(0, len(self._rows) - 1)))
		self._paintRows()
		foot = self._ui('panel/footer')
		if foot is not None:
			n, total = pend['index'] + 1, len(self._pendingParams())
			if error:
				foot.par.text = '%s   -   Left back, Esc cancels' % error
			else:
				foot.par.text = '%s   %d of %d for %s   -   Enter accepts, Left back, Esc cancels' % (
					prm.get('help') or label, n, total, pend['row']['title'])

	def _parsePendingValue(self):
		"""The current field as a value: (value, None), or (None, error)."""
		prm = self._pendingParam()
		pend = self._pending
		typed = (pend.get('text') or '').strip()
		style = prm.get('style') or 'str'
		label = prm.get('label') or prm.get('name')
		if style == 'menu':
			if not self._rows:
				return None, 'no option matches %r' % typed
			return self._rows[self._selected].get('value'), None
		if typed == '':
			if prm.get('default') is not None:
				return prm.get('default'), None
			if prm.get('required'):
				return None, '%s is required' % label
			return None, None
		if style == 'int':
			try:
				return int(typed), None
			except ValueError:
				return None, '%s needs a whole number' % label
		if style == 'float':
			try:
				return float(typed), None
			except ValueError:
				return None, '%s needs a number' % label
		return typed, None

	def _acceptPending(self):
		prm = self._pendingParam()
		pend = self._pending
		if prm is None:
			return self._endPending()
		value, error = self._parsePendingValue()
		if error:
			self._paintPending(error)
			return {'ok': False, 'error': error}
		if pend.get('naming'):
			return self._savePreset(value)
		if value is not None:
			pend['values'][prm.get('name')] = value
		pend['index'] += 1
		if pend['index'] < len(self._pendingParams()):
			self._selected = 0
			self._promptParam()
			return {'ok': True, 'pending': pend['index']}
		row, values, prev = pend['row'], dict(pend['values']), pend['prev_query']
		self._endPending(restore=False)
		self._pushHistory(prev)
		self.Dismiss()
		return self.Activate(row, values)

	def _pendingBack(self):
		pend = self._pending
		if pend is None:
			return
		if pend['index'] == 0:
			self._endPending()
			return
		pend['index'] -= 1
		pend['values'].pop(self._pendingParam().get('name'), None)
		self._selected = 0
		self._promptParam()

	def _endPending(self, restore=True):
		pend, self._pending = self._pending, None
		self._restorePlaceholder()
		if restore and pend is not None:
			inp = self._ui('panel/input')
			if inp is not None:
				inp.par.text = pend.get('prev_query') or ''   # fires OnQuery -> re-rank
				if str(inp.par.text.eval()) == (pend.get('prev_query') or ''):
					self._query = pend.get('prev_query') or ''
					self._refresh()
		return {'ok': True, 'cancelled': True}

	def _refresh(self):
		self._rows = self.Rank(self._query)
		if self._rows:
			self._selected = max(0, min(self._selected, len(self._rows) - 1))
		self._paint()
		self._writeResults()

	@staticmethod
	def _code(rgb):
		return '{#color(%d,%d,%d);}' % tuple(int(c * 255) for c in rgb)

	def _paintRows(self):
		favs = self.Favourites()
		n = len(self._rows)
		for i in range(self.ROW_COUNT):
			row = self._ui('panel/rows/row%d' % i)
			if row is None:
				continue
			if i >= n:
				row.par.display = False
				continue
			r = self._rows[i]
			sel = (i == self._selected)
			avail = r.get('available', True)
			colour = self.COL_SEL_TEXT if sel else (self.COL_TEXT if avail else self.COL_OFF)
			dim = self.COL_SEL_DIM if sel else self.COL_DIM
			installRow = (r['kind'] == self.KIND_COMMAND
						  and str(r.get('ident') or '').startswith(self.INSTALL_IDENT_PREFIX))
			kc = (self.COL_BUILTIN if r.get('builtin')
				  else self.COL_INSTALL if installRow
				  else self.KIND_COLOUR.get(r['kind'], self.COL_DIM))
			if sel:
				kc = tuple(c + (1.0 - c) * 0.45 for c in kc)
			if not avail:
				kc = self.COL_OFF
			if r['kind'] == self.KIND_NETWORK:
				badge = (r.get('optype') or 'comp').upper()
			elif r['kind'] == self.KIND_COMMAND:
				badge = 'TD' if r.get('builtin') else 'INSTALL' if installRow else 'COMMAND'
			elif r['kind'] == self.KIND_METHOD:
				badge = 'METHOD'
			elif r['kind'] == self.KIND_TOOL:
				badge = 'TOOL'
			elif r['kind'] == self.KIND_PRESET:
				badge = 'PRESET'
			elif r['kind'] == self.KIND_PICK:
				badge = 'OPTION' if r.get('value') is not None else ''
			else:
				badge = 'TOX'
			tag = ''
			if r['kind'] in (self.KIND_COMMAND, self.KIND_PRESET) and r.get('contexts'):
				ctx = max(r['contexts'], key=lambda c: self.CONTEXT_TIER.get(c, 0))
				tag = ' ' + self.CONTEXT_TAG.get(ctx, ctx)
			star = '* ' if self._curationId(r) in favs else ''
			row.par.text = '%s%s%s    %s  %s%s%s' % (
				star, r['title'], self._code(dim), r.get('category') or '',
				self._code(kc), badge, tag)
			row.par.fontcolorr, row.par.fontcolorg, row.par.fontcolorb = colour
			row.par.bgalpha = 1.0 if sel else 0.0
			row.par.display = True

	def _paint(self):
		self._paintRows()
		self._hint()

	def _guess(self):
		"""What Tab would complete the query to, or '' when there is nothing.

		Kept as the typed text plus the remainder rather than the row's own
		casing, so `~exttest.hel` under `Hello` still reads back as something
		the user recognises as their own typing extended.

		(An inline GREY version of this behind the field was tried and backed
		out: the palette's input lives in a `verttb` container, where a child's
		x/y is ignored even with `alignallow = ignore`, so the overlay rendered
		as a second line instead of behind the text. Doing it properly means
		reparenting the input inside the ghost, which is a bigger change than
		this footer.)
		"""
		q = self._query or ''
		guess = ''
		if self._rows and self._pending is None:
			r = self._rows[self._selected]
			if r['kind'] in (self.KIND_METHOD, self.KIND_EXT):
				head = self._rowHead(r)
				typed = (q[1:].split() or [''])[0]
				if head.lower().startswith('ext.') and not typed.lower().startswith('ext.'):
					head = head[4:]     # they are typing the short form; stay in it
				guess = '~' + head
			elif r['kind'] == self.KIND_TOOL and r.get('tool'):
				guess = '#' + r['tool']
		if guess and len(guess) > len(q) and guess.lower().startswith(q.lower()):
			return q + guess[len(q):]
		return ''

	def _hint(self):
		"""The footer always says what Enter will do to THIS row; with nothing
		typed it shows the prefixes, as the launcher overlay does."""
		foot = self._ui('panel/footer')
		if foot is None:
			return
		if not self._query:
			foot.par.text = ('>  commands   ?  tools only   =  components   /  ./  ../  navigate   '
							 '~  methods   #  tools   Ctrl+D star   Ctrl+H hide   Alt+S preset')
			return
		if not self._rows:
			if self._query.startswith('/'):
				foot.par.text = 'No such network   -   /  root,  ./  here,  ../  up'
			elif self._query.startswith('~'):
				subj = self._methodSubject()
				foot.par.text = 'No promoted methods on %s' % (subj.path if subj is not None else 'anything here')
			else:
				foot.par.text = 'No matches'
			return
		r = self._rows[self._selected]
		n = len(self._rows)
		if r['kind'] == self.KIND_NETWORK:
			foot.par.text = 'Enter opens %s   -   Right drills in, Left backs out' % r['path']
		elif r['kind'] == self.KIND_TOOL:
			foot.par.text = 'Enter or Right lists %s commands   -   %d tools' % (r.get('tool'), n)
		elif r['kind'] == self.KIND_EXT:
			foot.par.text = 'Tab  %s   -   Enter lists %s members   -   %d extensions' % (
				self._guess() or ('~ext.%s.' % r['extname']), r['title'], n)
		elif r['kind'] == self.KIND_METHOD:
			given = r.get('args') or []
			if not self._namesMethod(self._query, r):
				foot.par.text = 'Tab  %s   -   Enter completes, then arguments, then Enter runs   -   %d' % (
					self._guess() or r['title'], n)
			elif len(given) < r.get('required', 0):
				foot.par.text = '%s needs %d argument(s)   -   type them after the name' % (
					r['method'], r.get('required', 0))
			else:
				foot.par.text = 'Enter runs %s.%s(%s)   -   %d methods' % (
					r['path'], r['method'], ', '.join(given), n)
		elif r['kind'] == self.KIND_PRESET and not r.get('command'):
			foot.par.text = "Preset's command is gone   -   Ctrl+H removes it"
		elif r['kind'] == self.KIND_PRESET and r.get('available', True):
			foot.par.text = 'Enter runs preset %s   -   Ctrl+H deletes it   -   %d results' % (r['title'], n)
		elif not r.get('available', True):
			foot.par.text = 'Needs %s in the network you came from   -   %d results' % (
				', '.join(r.get('contexts') or []), n)
		elif r['kind'] == self.KIND_COMPONENT:
			net = self.Context().get('network')
			foot.par.text = 'Enter places %s into %s   -   %d results' % (
				r['title'], net.path if net is not None else '?', n)
		else:
			foot.par.text = 'Enter runs %s   -   %d results   -   Up/Down select' % (
				r['title'], n)

	def _writeResults(self):
		"""A plain table of what is on screen: inspectable without a screenshot."""
		t = self._ui('results')
		if t is None:
			return
		t.clear()
		t.appendRow(['i', 'kind', 'title', 'category', 'available', 'key'])
		for i, r in enumerate(self._rows):
			t.appendRow([str(i), r['kind'], r['title'], r.get('category') or '',
						 '1' if r.get('available', True) else '0', r['key']])
