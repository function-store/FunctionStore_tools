CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase


class TimelineRegistryExt(RegistryBase):
	"""Publishes tool-owned panels into TD's timeline dialog.

	The surface is `/ui/dialogs/timeline` -- a singleton, unlike the navbar
	(one bar per pane), so entries are MIRRORS (selectCOMPs pointing at the
	tool's own widget) exactly as the toolbar does, not copies. TD's per-pane
	timelines under `/ui/panes/pane_timeline` are 20px frame strips with no
	transport row; they are deliberately not a target here.

	Three zones -- the containers a tool can sensibly reach, which lay out
	differently:

	  transport     `/ui/dialogs/timeline/transport`  horizlr, 44px tall
	  background    the timeline dialog itself        a strip the bar grows for
	  graphheading  the keyframer's graph heading     horizlr, 18px tall

	There is deliberately no zone for the timeline's left-hand properties
	block. The dialog stacks THREE 279x130 panels at (0, 0) -- timeproperties,
	timeattributes and emptypanel1 -- and only `timeattributes` draws: tinting
	each and counting pixels in a capture gives 0 / 34344 / 0. Anything sent to
	the other two is laid out correctly and then covered, which is
	indistinguishable from never having registered. `timeattributes` itself is
	no better a host: its own children consume its horizlr flow, so an appended
	section lands at x=276 in a 279-wide block, and a section placed over the
	block from the dialog is drawn under it. A zone that cannot be seen is
	worse than no zone, so it is not offered.

	Native transport controls occupy alignorder 0..12, so contributions start
	at MIRROR_ORDER_BASE and never fight them. Nothing is injected until the
	first registration -- an empty registry claims no surface.
	"""

	SHORTCUT = 'FNS_TIMELINEREGISTRY'
	EXT_NAME = 'TimelineRegistryExt'
	REGISTRY_NAME = 'FNS_TimelineRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Tl'
	TOOL_PAGE_LABEL = 'Timeline'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus',
					  'Menuorder', 'Displayed', 'Barwidth', 'Barheight', 'Zone')

	MIRROR_PREFIX = 'tlmirror_'
	MIRROR_TAG = 'TimelineRegistryMirror'
	DIVIDER_TAG = 'TimelineRegistryDivider'

	BAR_PATH = '/ui/dialogs/timeline'

	# zone -> how a mirror is placed there.
	#   child   : container inside the dialog, or '' for the dialog itself
	#   h / w   : pinned size, None = follow the source live
	#   base    : alignorder base; contributions are base + sequence index
	#   place   : optional absolute {x, y, align} for 'none'-aligned strips
	#
	# 'background' is the odd one and the reason this is a dict: TD's timeline
	# has no free band, so a background is not appended -- it is placed IN the
	# frame-ruler band and drawn UNDERNEATH it. framebarslider sits at
	# alignorder 2.0 with bgalpha 0, so a strip just below that order shows
	# through it. Panel y is measured from the BOTTOM of the dialog, so y=56 on
	# a 70-tall bar is the ruler band, not the floor.
	ZONES = {
		# justifyh: the transport row flows left-to-right, so a contribution lands
		# immediately after TD's own controls and crowds them. The bar is ~2470
		# wide and TD uses barely a third of it, so the section fills the leftover
		# and packs its contributions against the far right, where there is
		# nothing to collide with.
		'transport':  {'child': 'transport',      'h': 39,   'w': None, 'base': 100,
					   'section': 'fnsbar_transport', 'section_h': 39,
					   'justifyh': 'right'},
		'background': {'child': '',               'h': 14,   'w': None, 'base': 1.9,
					   'place': {'x': 0, 'y': None, 'align': 'none'},
					   'anchor': 'transportpanel', 'grow': True,
					   # framebar is the PLAYHEAD -- a 2px column whose height is a
					   # constant, so on a grown bar it stops partway up and the
					   # playhead no longer spans the row it is pointing at.
					   'follow_height': ('emptypanel1', 'timeattributes'),
					   # The play marker is its OWN rule, not a height follower. It is
					   # 2px wide, its x tracks the playhead, and it is a fixed 13 tall
					   # natively -- one ruler row. Left at 13 on a grown bar it becomes
					   # a stub floating under the strip, detached from the ruler it
					   # belongs to. Spanning the bar is what a playhead over a filmstrip
					   # should do, so it is stated deliberately instead of riding along
					   # with the left-hand blocks.
					   'play_marker': ('framebar',),
					   # framebarslider (the ruler) is positioned from the BOTTOM by a
					   # stock constant, while rangebar anchors to the top (always
					   # bar - 14). Growing the bar therefore pulls them apart, and the
					   # ruler has to drop to stay readable against the added row.
					   # -12 is EMPIRICAL -- it is what looks right on screen, matching
					   # rangebar's own height, and it does not vary with the strip
					   # height because the bar grows by exactly that amount.
					   'shift_y': (('framebarslider', -12),)},
		'graphheading': {'dialog': '/ui/dialogs/keyframer',
					 # the LABEL inside the strip: graphheading is verttb and 18
					 # tall with textbg already filling it, so a sibling is
					 # pushed straight out. textbg is `align = none`, so the
					 # section takes its width by expression rather than by fill.
					 'child': 'graphheading/textbg',
					 'section': 'fnsbar_graphheading',
					 'section_h': 18,
					 'justifyh': 'right',
					 'h': 18, 'w': None, 'base': 100},
	}
	DEFAULT_ZONE = 'transport'

	# TD's own transport controls sit at alignorder 0..12; the default base
	# clears them. Per-zone bases override it (see ZONES).
	MIRROR_ORDER_BASE = 100

	# TD's stock timeline height. A `grow` zone ADDS its row on top of this
	# rather than taking the space out of the transport row, and the height is
	# recomputed as base + growth every sync -- never incremented -- so it
	# cannot creep upward across sessions or double-apply on a re-register.
	BAR_BASE_HEIGHT = 70

	# TD's own idiom for "be as tall as the bar" -- timeproperties and
	# transportpanel already use it. The left-hand blocks do not: they are fixed
	# constants, so they keep their old height when the bar grows and leave a
	# ragged edge down the left. A `grow` zone points them at the same
	# expression (see `follow_height`).
	FOLLOW_HEIGHT_EXPR = 'par("../panelh")'
	FOLLOW_HEIGHT_STORE = 'follow_height_before'
	PLAY_MARKER_STORE = 'play_marker_before'
	# The parent spans from its own y to the top of the bar, so it tracks the
	# shift_y nudge automatically instead of baking the offset in.
	#
	# TSCRIPT, not Python. TD's stock timeline parameters are tscript expressions
	# -- which is why FOLLOW_HEIGHT_EXPR is `par("../panelh")` and not a Python
	# reference. Writing Python here fails at COOK time, not at write time:
	# `me.par.y` gave "Bad data type for function or operation" and evaluated the
	# height to 0, silently collapsing the slider.
	PLAY_MARKER_PARENT_EXPR = 'par("../panelh") - par("y")'
	SHIFT_Y_STORE = 'shift_y_before'

	SELECTPANEL_EXPR = (
		"op.FNS_TIMELINEREGISTRY.WidgetTarget({canonical!r}) "
		"if hasattr(op, 'FNS_TIMELINEREGISTRY') else None"
	)
	MIRROR_WIDTH_EXPR = (
		"(op.FNS_TIMELINEREGISTRY.WidgetTarget({canonical!r}).width "
		"if hasattr(op, 'FNS_TIMELINEREGISTRY') "
		"and op.FNS_TIMELINEREGISTRY.WidgetTarget({canonical!r}) is not None else 39)"
	)
	MIRROR_HEIGHT_EXPR = (
		"(op.FNS_TIMELINEREGISTRY.WidgetTarget({canonical!r}).height "
		"if hasattr(op, 'FNS_TIMELINEREGISTRY') "
		"and op.FNS_TIMELINEREGISTRY.WidgetTarget({canonical!r}) is not None else 20)"
	)

	# Location-independent: resolves through the toolkit root's shortcut and
	# evaluates to None (no clone, no warning) where FNS is absent.
	CLONE_EXPR = "op.FNS.op('FNS_TimelineRegistry') if hasattr(op, 'FNS') else None"

	# --- zones -------------------------------------------------------------

	def _normalizeZone(self, zone):
		z = str(zone or '').strip().lower()
		return z if z in self.ZONES else self.DEFAULT_ZONE

	def _entryZone(self, info):
		return self._normalizeZone((info or {}).get('zone'))

	def _dialog(self, zone=None):
		"""The DIALOG a zone publishes into.

		Defaults to TD's timeline. A zone may name another one -- the keyframer's
		graph heading is a time surface too, and giving it a zone here is far
		cheaper than a second registry with its own /sys global, promotion path,
		host parameters and release scrub, to publish into a dialog that is
		conceptually the same thing.
		"""
		if zone is None:
			return op(self.BAR_PATH)
		return op(self._zoneSpec(zone).get('dialog', self.BAR_PATH))

	def _zoneSpec(self, zone=None):
		return self.ZONES[self._normalizeZone(zone)]

	def _zoneBase(self, zone=None):
		return self._zoneSpec(zone).get('base', self.MIRROR_ORDER_BASE)

	def _bar(self, zone=None, create=False):
		"""The container an entry's mirror lives in ('' = the dialog itself).

		`child` may be a PATH, not just a name -- the graph heading's host is
		`graphheading/textbg`, the label inside the strip, because the strip
		itself is verttb and already full.

		A zone with a `section` puts its contributions inside a managed container
		instead of straight into the host, so the awkward geometry is solved once
		rather than by every contributor. It is only CREATED when something is
		actually being injected: reads must not conjure an empty section into a
		dialog nobody has contributed to.
		"""
		spec = self._zoneSpec(zone)
		dlg = self._dialog(zone)
		if not dlg:
			return None
		child = spec.get('child', '')
		host = dlg if not child else dlg.op(child)
		if host is None:
			return None
		name = spec.get('section')
		if not name:
			return host
		sec = host.op(name)
		if sec is None and create:
			sec = self.EnsureSection(host, name,
									 height=spec.get('section_h', spec.get('h') or 18),
									 spec=spec)
		return sec if sec is not None else (host if not create else None)

	def _allBars(self):
		"""Every container we may have put something in, across every dialog.

		Prune walks this, so a zone missing from here strands its mirrors when a
		tool unregisters.
		"""
		bars = []
		for zname, spec in self.ZONES.items():
			b = self._bar(zname)
			if b is not None and b not in bars:
				bars.append(b)
			# A sectioned zone must list its HOST as well. The section is where
			# things go now, but a mirror that landed in the host before the
			# section existed is invisible to a prune that only walks the
			# section -- and then there are two of it. Same shape as the spacer
			# that outlived its entry.
			if spec.get('section'):
				dlg = self._dialog(zname)
				child = spec.get('child', '')
				host = (dlg if not child else dlg.op(child)) if dlg else None
				if host is not None and host not in bars:
					bars.append(host)
		return bars

	def _barReady(self):
		dlg = self._dialog()
		if not (dlg and dlg.valid):
			return False
		return self._bar(self.DEFAULT_ZONE) is not None

	# --- surface hooks (RegistryBase contract) ------------------------------

	def _ensureSelectionExecuteRole(self):
		# No selection DAT on this surface; hosts must not keep a parallel table.
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _syncSurface(self, attempts=40):
		"""Idempotent: prune orphan mirrors, then ensure one managed mirror per
		registered entry, zoned/ordered/shown per the central store. Defers
		until TD's timeline dialog exists."""
		self._pane_sync_queued = False
		if self._barReady():
			names = self._registeredNamesInOrder()
			if not names:
				self._pruneMirrors()
				self._applyGrowthSettled()
				return
			self._ensureGroupMarkers()
			self._pruneMirrors()
			names = self._registeredNamesInOrder()
			ancestors, _ = self._scanGroups(names)
			for i, canonical in enumerate(names):
				self._injectWidget(canonical, i, ancestors.get(canonical, ()))
			self._sizeSections()        # after ALL of them: it is a sum
			self._applyGrowthSettled()
			return
		if attempts <= 0:
			debug(f'{self.REGISTRY_NAME}: timeline never became available, skipping sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	def _mirrorName(self, canonical):
		return self.MIRROR_PREFIX + tdu.legalName(canonical)

	def _registeredNamesInOrder(self):
		entries = self.stored['PaneRegistry']
		ordered, unordered = [], []
		for name, info in entries.items():
			order = self._normalizeMenuOrder(info.get('menu_order'))
			(ordered if order is not None else unordered).append((order, name))
		ordered.sort(key=lambda t: (t[0], t[1].lower()))
		return [n for _, n in ordered] + [n for _, n in unordered]

	# --- managed mirror lifecycle ------------------------------------------

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
		"""Position comes from the entry's place in the RESOLVED sequence, not
		its stored menu_order: group switches deliberately store no order of
		their own, and two entries sharing a stored order would otherwise land
		on the same alignorder and fight."""
		if seq_index is not None:
			return seq_index
		order = self._normalizeMenuOrder(info.get('menu_order'))
		if order is None:
			bar = self._bar(self._entryZone(info))
			order = len(bar.ops(self.MIRROR_PREFIX + '*')) if bar else 0
		return order

	def _applyGrowthSettled(self):
		"""Apply the growth now, and once more after the store settles.

		Registration lands in two steps -- the entry is stored, and its ZONE
		arrives with the host's parameter a frame later. Growth computed in the
		first step sees no `background` entry and leaves the bar at its base
		height, while the mirror is injected anyway: a strip with no row to live
		in. Nothing re-ran it, so the bar stayed 70 with the strip squeezed into
		the transport row until something else happened to trigger a sync.

		Re-applying one frame later costs nothing -- the computation is
		idempotent by construction (always BASE + growth, never incremented) --
		and it is what makes register/unregister symmetric.
		"""
		self._applySurfaceGrowth()
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._applySurfaceGrowth()",
			self.ownerComp, delayFrames=1, delayRef=op.TDResources)

	def _applySurfaceGrowth(self):
		"""Give a `grow` zone its own row instead of stealing one.

		Anchoring a strip puts it in the bar's layout flow, so without this it
		takes its height out of the transport row and clips the controls. The
		dialog height is always recomputed as BAR_BASE_HEIGHT + growth, never
		incremented: /sys is rebuilt on every project open but the DIALOG height
		is saved in the .toe, so an increment-and-restore scheme would creep
		taller every session. Recomputing is idempotent and self-healing.
		"""
		dlg = self._dialog()
		if dlg is None:
			return
		grown = 0
		for zname, spec in self.ZONES.items():
			if not spec.get('grow'):
				continue
			# SUM, not max. Two strips in a grow zone need two bands: taking the
			# tallest gave them one to share, so the second drew on top of the
			# first and the bar was too short for both.
			for i in self.stored['PaneRegistry'].values():
				if self._entryZone(i) == zname and self._effectiveDisplay(i, ()):
					grown += int(self._entryHeight(i, spec) or 0)
		want = self.BAR_BASE_HEIGHT + grown
		try:
			if int(dlg.par.h.eval()) != want:
				dlg.par.h = want
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: timeline height {want}: {e}')
		self._applyHeightFollowers(dlg, grown > 0)
		self._applyPlayMarker(dlg, grown > 0)
		self._applyShiftY(dlg, grown > 0)

	def _applyShiftY(self, dlg, grown):
		"""Nudge panels whose stock Y no longer suits a taller bar.

		Same store-and-restore contract as the height followers: remember what
		the parameter said, apply the offset while a `grow` zone is registered,
		put the original back on teardown. Kept separate from follow_height
		because it is an OFFSET from whatever TD had, not a shared expression --
		the stock value is an expression (`76-20`) and must survive.
		"""
		shifts = []
		for spec in self.ZONES.values():
			shifts.extend(spec.get('shift_y', ()))
		if not shifts:
			return
		saved = dict(self.ownerComp.fetch(self.SHIFT_Y_STORE, {}) or {})
		for name, delta in shifts:
			panel = dlg.op(name)
			if panel is None or not hasattr(panel.par, 'y'):
				continue
			par = panel.par.y
			if grown:
				if name in saved:
					continue                      # already shifted; never twice
				saved[name] = par.expr if par.mode == ParMode.EXPRESSION else str(par.eval())
				if par.mode == ParMode.EXPRESSION:
					par.expr = f'({par.expr}) + ({delta})'
				else:
					par.val = par.eval() + delta
			elif name in saved:
				was = saved.pop(name)
				try:
					if any(c in was for c in '+-*/()'):
						par.expr = was
					else:
						par.mode = ParMode.CONSTANT
						par.val = float(was)
				except Exception:
					pass
		self.ownerComp.store(self.SHIFT_Y_STORE, saved)

	def _applyHeightFollowers(self, dlg, grown):
		"""Make the bar's fixed-height blocks track the bar.

		Growing the dialog is only half the job: timeproperties and
		transportpanel already say par("../panelh") and follow along, but the
		left-hand blocks are fixed constants, so they keep their old height and
		leave a ragged edge down the left of a taller bar.

		Their originals are remembered so a teardown puts them back. Losing that
		memory is survivable by design -- the expression evaluates correctly at
		ANY bar height, so the worst case of a forgotten restore is a panel that
		tracks the bar instead of a constant that happens to match it.
		"""
		names = set()
		for spec in self.ZONES.values():
			for n in spec.get('follow_height', ()):
				names.add(n)
		if not names:
			return
		saved = dict(self.ownerComp.fetch(self.FOLLOW_HEIGHT_STORE, {}) or {})
		for n in sorted(names):
			panel = dlg.op(n)
			if panel is None or not hasattr(panel.par, 'h'):
				continue
			par = panel.par.h
			if grown:
				if par.mode != ParMode.EXPRESSION or par.expr != self.FOLLOW_HEIGHT_EXPR:
					saved.setdefault(n, str(int(par.eval())))
					par.expr = self.FOLLOW_HEIGHT_EXPR
			elif n in saved:
				try:
					par.mode = ParMode.CONSTANT
					par.val = int(saved.pop(n))
				except Exception:
					saved.pop(n, None)
		self.ownerComp.store(self.FOLLOW_HEIGHT_STORE, saved)

	SOURCE_WIDTH_STORE = 'source_width_before'

	def _sizeSourceToBar(self, canonical, anchor):
		"""Make a full-width strip's SOURCE panel track the bar it is mirrored into.

		The expression is absolute because it is evaluated on the source, which
		lives inside the contributing tool and cannot reach the dialog relatively.
		That is the same BAR_PATH this registry already hardcodes everywhere --
		TD's timeline is a singleton.

		The original is remembered so unregistering hands the tool its own panel
		back at the size it had.
		"""
		src = self._resolvePanelOp(self.stored['PaneRegistry'].get(canonical) or {})
		if src is None or not hasattr(src.par, 'w'):
			return
		target = f'{self.BAR_PATH}/{anchor}' if anchor else self.BAR_PATH
		expr = f"op({target!r}).width"
		if src.par.w.mode == ParMode.EXPRESSION and src.par.w.expr == expr:
			return
		saved = dict(self.ownerComp.fetch(self.SOURCE_WIDTH_STORE, {}) or {})
		# The PATH goes in too. Restore cannot look the source up through the
		# registry entry, because UnregisterWidget pops the entry BEFORE calling
		# it -- so it resolved nothing, restored nothing, and left the tool's own
		# panel stretched to the bar's width for good. Found when a test tenant
		# left ui_bar at 2473 instead of 190.
		saved.setdefault(canonical, self._sourceRecord(src))
		self.ownerComp.store(self.SOURCE_WIDTH_STORE, saved)
		self._setExpr(src.par.w, expr)

	def _sourceRecord(self, src):
		"""`path|w|h` snapshot of a source panel's own size."""
		def cur(name):
			par = getattr(src.par, name, None)
			try:
				return str(int(par.eval())) if par is not None else ''
			except (TypeError, ValueError):
				return ''
		return f'{src.path}|{cur("w")}|{cur("h")}'

	def _sizeSourceToEntry(self, canonical, info):
		"""Size the SOURCE panel to what the registration asked for.

		A Select mirror draws its source at the SOURCE's size, so setting only
		the mirror crops instead of scaling: a 300x300 button registered at
		200x18 showed a 200x18 corner of itself -- measured, 306 lit pixels out
		of the 3400 the slot can hold, which reads on screen as "my button did
		not show up" and as "it is always a limited height".

		Only declared axes are touched, and the original is remembered so
		unregistering hands the tool its panel back. Registering must not be a
		way to silently resize somebody's widget on an axis they said nothing
		about.
		"""
		src = self._resolvePanelOp(info)
		if src is None:
			return
		wanted = {}
		for key, par_name in (('width', 'w'), ('height', 'h')):
			try:
				v = int(info.get(key) or 0)
			except (TypeError, ValueError):
				v = 0
			par = getattr(src.par, par_name, None)
			if v > 0 and par is not None and par.eval() != v:
				wanted[par_name] = v
		if not wanted:
			return
		saved = dict(self.ownerComp.fetch(self.SOURCE_WIDTH_STORE, {}) or {})
		saved.setdefault(canonical, self._sourceRecord(src))
		self.ownerComp.store(self.SOURCE_WIDTH_STORE, saved)
		for par_name, v in wanted.items():
			self._setConst(getattr(src.par, par_name), v)

	def _restoreSourceWidth(self, canonical):
		"""Give a tool's panel its own width back when it unregisters."""
		saved = dict(self.ownerComp.fetch(self.SOURCE_WIDTH_STORE, {}) or {})
		if canonical not in saved:
			return
		record = str(saved.pop(canonical))
		self.ownerComp.store(self.SOURCE_WIDTH_STORE, saved)
		# path|w|h -- resolved from the RECORD, not from the registry entry,
		# which is already gone by the time this runs. Two fields is the older
		# width-only form and still restores.
		parts = record.split('|')
		path, dims = parts[0], parts[1:]
		src = op(path) if path else None
		if src is None:
			return
		for name, saved_val in zip(('w', 'h'), dims):
			par = getattr(src.par, name, None)
			if par is None or saved_val == '':
				continue
			try:
				par.mode = ParMode.CONSTANT
				par.val = int(saved_val)
			except Exception:
				pass

	def _applyPlayMarker(self, dlg, grown):
		"""Let the play marker span a grown bar instead of stubbing out.

		Separate from `_applyHeightFollowers` on purpose. That mechanism is about
		blocks whose fixed height leaves a ragged EDGE; this is about the
		playhead remaining legible, and conflating them is how the marker got
		reshaped by accident in the first place.

		Natively the marker is 13 tall -- one ruler row -- which reads correctly
		on a 70px bar where the ruler is most of it. Add a 60px strip and the
		same 13 becomes a stub floating below the strip, visually detached from
		the ruler it marks. Spanning the bar is what a playhead drawn over a
		filmstrip should do.

		The original is remembered so a teardown restores TD's own value.
		"""
		names = set()
		for spec in self.ZONES.values():
			for n in spec.get('play_marker', ()):
				names.add(n)
		if not names:
			return
		saved = dict(self.ownerComp.fetch(self.PLAY_MARKER_STORE, {}) or {})
		targets = []
		for n in sorted(names):
			panel = dlg.op(n)
			if panel is None or not hasattr(panel.par, 'h'):
				continue
			targets.append((n, panel, self.FOLLOW_HEIGHT_EXPR))
			# THE MARKER IS CLIPPED BY ITS PANEL PARENT. framebar's panel parent
			# is framebarslider -- 14px tall -- so its native h of 13 is "fill my
			# parent", and setting the marker to the bar height on its own does
			# NOTHING on screen. Measured the hard way: the marker read 130 tall
			# while still drawing as a stub. The parent has to span as well.
			host = panel.panelParent()
			if (host is not None and host is not dlg
					and hasattr(host.par, 'h') and host.par['y'] is not None):
				targets.append((host.name, host, self.PLAY_MARKER_PARENT_EXPR))
		for n, panel, want_expr in targets:
			par = panel.par.h
			if grown:
				if par.mode != ParMode.EXPRESSION or par.expr != want_expr:
					saved.setdefault(n, str(int(par.eval())))
					par.expr = want_expr
			elif n in saved:
				try:
					par.mode = ParMode.CONSTANT
					par.val = int(saved.pop(n))
				except Exception:
					saved.pop(n, None)
		self.ownerComp.store(self.PLAY_MARKER_STORE, saved)

	def _anchorMirror(self, mirror, spec):
		"""Wire an absolutely-placed strip into the bar's content flow.

		Every one of TD's own full-width strips -- newhashrow, rangebar,
		framebarslider -- feeds its COMP input from `transportpanel`, and that
		connection is what puts them in the bar's content area rather than at
		the dialog's raw origin. An unwired strip renders, sits at the right
		alignorder, reports the right size, and still draws as a ~100px sliver
		in the corner. Costly to rediscover; cheap to copy.
		"""
		name = spec.get('anchor')
		if not name:
			return
		dlg = self._dialog()
		target = dlg.op(name) if dlg else None
		if target is None:
			return
		try:
			conn = mirror.inputCOMPConnectors[0]
			if not conn.connections:
				conn.connect(target.outputCOMPConnectors[0])
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: anchoring {mirror.path} failed: {e}')

	def _mirrorOrder(self, info, seq_index):
		"""Where this entry sits in its zone's alignorder space.

		A flowed zone (transport, graphheading) counts up from its base. An
		absolutely-placed strip must NOT: its base IS the slot, chosen to fall
		underneath a specific piece of TD chrome, and adding a whole sequence
		index to it walks straight past that chrome -- a background at menu
		order 1 landed on 2.9 and drew OVER the ruler it was meant to sit under.
		Strips therefore stack in hundredths and stay inside their slot.
		"""
		spec = self._zoneSpec(self._entryZone(info))
		base = spec.get('base', self.MIRROR_ORDER_BASE)
		step = 0.01 if spec.get('place') else 1
		return base + self._barOrder(info, seq_index) * step

	def _entryHeight(self, info, spec=None):
		"""This entry's height: its own if it asked for one, else the zone's.

		A `grow` zone's height is what the bar grows BY, so an entry that wants
		a taller strip has to be able to say so -- otherwise every contributor
		is stuck with whatever the zone was written with.
		"""
		if spec is None:
			spec = self._zoneSpec(self._entryZone(info))
		try:
			h = int(info.get('height') or 0)
		except (TypeError, ValueError):
			h = 0
		return h if h > 0 else spec.get('h')

	SPACER_PREFIX = 'tlspacer_'          # legacy; swept, never created

	# --- managed sections -------------------------------------------------------
	#
	# Some surfaces have nowhere to put a contribution. The keyframer's
	# graphheading is `verttb` and 18 tall with its label already filling it, so a
	# sibling gets pushed out of the strip; the label itself is `align = none`, so
	# a child there keeps its x but every contributor would have to work out its
	# own placement.
	#
	# So the registry plops down ONE container per section and contributions live
	# inside it. The section spans its HOST and TD justifies what is inside it --
	# `justifyh` on a container packs its children against an edge, which is the
	# whole of what the old spacer was faking. Gone with it: the per-zone slack
	# container, the summed section width (a section sized to its contents cannot
	# justify -- there is no slack to justify INTO, which is why a second
	# contribution landed at x=-200 and was clipped away), and the hand-written
	# `section_x` expression that had to re-derive a right edge the layout engine
	# already knows.

	SECTION_PREFIX = 'fnsbar_'

	def _sizeSections(self):
		"""Re-apply managed section geometry every pass.

		Not a size computation any more -- the section takes its width from the
		host and TD packs the children. This only re-states what a zone declares,
		because `EnsureSection` runs for a MISSING section only, so an existing
		one would never pick up a changed zone spec.
		"""
		for zname, spec in self.ZONES.items():
			name = spec.get('section')
			if not name:
				continue
			dlg = self._dialog(zname)
			child = spec.get('child', '')
			host = (dlg if not child else dlg.op(child)) if dlg else None
			sec = host.op(name) if host is not None else None
			if sec is None:
				continue
			self._applySectionGeometry(sec, spec)

	def _applySectionGeometry(self, sec, spec):
		"""Span the host, then let TD justify the contributions inside.

		How the section claims the host's width depends on the host: inside an
		ALIGNED parent it is `hmode = fill`, which hands it whatever the row has
		left over after TD's own controls; inside an `align = none` parent (the
		keyframer's textbg) nothing flows, so it takes the width by expression
		instead. Either way the section ends up as wide as the space available
		and `justifyh` decides which end the contributions sit at.
		"""
		host = sec.parent()
		self._setConst(sec.par.align, 'horizlr')
		self._setConst(sec.par.justifyh, spec.get('justifyh', 'left'))
		self._setConst(sec.par.justifyv, spec.get('justifyv', 'center'))
		self._setConst(sec.par.h, spec.get('section_h', spec.get('h') or 18))
		self._setConst(sec.par.alignorder,
					   spec.get('base', self.MIRROR_ORDER_BASE))
		if host is not None and host.par.align.eval() == 'none':
			self._setConst(sec.par.hmode, 'fixed')
			self._setExpr(sec.par.w, 'parent().width')
			self._setConst(sec.par.x, 0)
		else:
			self._setConst(sec.par.hmode, 'fill')
			self._setConst(sec.par.w, 0)

	def EnsureSection(self, host, name, height=18, spec=None):
		"""Create or update a managed section container inside `host`."""
		if host is None:
			return None
		sec = host.op(name)
		if sec is None:
			sec = host.create(containerCOMP, name)
			sec.nodeX, sec.nodeY = 400, -400
		sec.tags = set(sec.tags) | {self.MIRROR_TAG}
		# `opacity` on a container applies to its CHILDREN as well, so a zero
		# there hides the whole section. Transparency comes from bgalpha, which
		# is a container's default anyway -- the section is a frame, and only
		# what is IN it draws.
		self._setConst(sec.par.opacity, 1)
		self._setConst(sec.par.bgalpha, 0)
		self._applySectionGeometry(sec, spec or {'section_h': height})
		return sec

	def _applyMirrorGeometry(self, mirror, canonical, info):
		"""Zone decides which axis is pinned and which follows the source."""
		spec = self._zoneSpec(self._entryZone(info))
		fixed_h, fixed_w = self._entryHeight(info, spec), spec.get('w')
		place = spec.get('place')
		mirror.par.matchsize = False
		width = info.get('width', '')
		if width:
			try:
				self._setConst(mirror.par.w, int(width))
			except (TypeError, ValueError):
				pass
		elif fixed_w:
			self._setConst(mirror.par.w, fixed_w)
		elif place:
			# a full-width strip spans the bar's CONTENT area, which is the
			# anchor's width -- not the dialog's. TD's own strips are 2473 wide
			# inside a 2752 dialog; the difference is the properties block.
			anchor = spec.get('anchor')
			self._setExpr(mirror.par.w,
						  f"parent().op({anchor!r}).width" if anchor else 'parent().width')
			# ...and so must the SOURCE. A Select mirror draws its source at the
			# SOURCE's size, so a source pinned to a constant does not care that
			# the window shrank: measured, dialog 1257 with the source still 2473.
			# The keyframer surface adapts because its Transform TOP carries
			# expressions that re-evaluate; this one had nothing re-evaluating at
			# all. Pointing the source at the same anchor makes a window resize
			# just work, with no rebake -- the strip texture stretches.
			self._sizeSourceToBar(canonical, anchor)
		else:
			self._setExpr(mirror.par.w, self.MIRROR_WIDTH_EXPR.format(canonical=canonical))
		if fixed_h:
			self._setConst(mirror.par.h, fixed_h)
		else:
			self._setExpr(mirror.par.h, self.MIRROR_HEIGHT_EXPR.format(canonical=canonical))
		if not place:
			# the mirror is a WINDOW onto the source, not a scaler -- give the
			# source the size the slot expects or the contribution is cropped
			self._sizeSourceToEntry(canonical, dict(info, height=info.get('height') or fixed_h or ''))
		if place:
			# an absolutely-placed strip: it is positioned, not flowed
			self._setConst(mirror.par.align, place.get('align', 'none'))
			self._setConst(mirror.par.x, place.get('x', 0))
			y = place.get('y')
			if y is None:
				# a grow zone owns the band it added. Panel y is measured from
				# the BOTTOM, so the added band is at the TOP -- follow the
				# dialog's height rather than pinning a number that goes stale
				# the moment the row is added or removed.
				#
				# And follow the mirror's OWN height rather than baking the
				# height in as a literal: that literal was written once at inject
				# time, so raising the strip height left the band anchored to the
				# old one -- bottom in the right place, top running off the end of
				# the bar. `h` is a constant here, so there is no cycle.
				# ...minus the bands already taken by strips ordered before this
				# one, so a second contribution stacks under the first instead of
				# landing on top of it. Recomputed every inject, like the spacer.
				above = self._bandAbove(canonical, info)
				self._setExpr(mirror.par.y,
							  'parent().height - me.par.h'
							  + (f' - {above}' if above else ''))
			else:
				self._setConst(mirror.par.y, y)

	def _bandAbove(self, canonical, info):
		"""Total height of the grow-zone strips that sit above this one."""
		zone = self._entryZone(info)
		spec = self._zoneSpec(zone)
		if not spec.get('grow'):
			return 0
		# Rank by the entry's OWN menu order, with the canonical as a tiebreak.
		# _mirrorOrder needs a sequence index, and feeding it 0 for every entry
		# made them all rank equal -- so nothing was ever "above" anything and
		# both strips landed on the same band.
		def rank(name, entry):
			try:
				o = self._normalizeMenuOrder(entry.get('menu_order'))
			except Exception:
				o = None
			return (0 if o is None else 1, o if o is not None else 0, str(name))

		mine = rank(canonical, info)
		total = 0
		for name, other in self.stored['PaneRegistry'].items():
			if name == canonical or self._entryZone(other) != zone:
				continue
			if not self._effectiveDisplay(other, ()):
				continue
			if rank(name, other) < mine:
				total += int(self._entryHeight(other, spec) or 0)
		return total

	def _placeMirror(self, mirror, bar):
		"""Park a freshly made mirror out of the way of the host's own nodes."""
		siblings = bar.ops(self.MIRROR_PREFIX + '*')
		mirror.nodeX = 500 + (len(siblings) - 1) * 200
		mirror.nodeY = -700

	def _relocateMirror(self, mirror, bar):
		"""A zone change moves the mirror between containers; TD cannot reparent,
		so the old one is destroyed and the caller remakes it."""
		if mirror is not None and mirror.parent() is not bar:
			mirror.destroy()
			return None
		return mirror

	def _injectWidget(self, canonical, seq_index=None, ancestors=()):
		info = self.stored['PaneRegistry'].get(canonical)
		if info is None:
			return
		bar = self._bar(self._entryZone(info), create=True)
		if not bar:
			return
		# One mirror per entry, in ONE place. Prune keys on NAME, so a mirror of a
		# LIVE canonical sitting in the wrong container is KEPT by it -- and then
		# there are two. That happens whenever an entry's target moves: a zone
		# gains a section, or an entry is re-zoned. The wrong-place copy goes here.
		mname = self._mirrorName(canonical)
		for other in self._allBars():
			if other is bar:
				continue
			dup = other.op(mname)
			if dup is not None and self.MIRROR_TAG in dup.tags:
				dup.destroy()
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
		mirror = self._relocateMirror(bar.op(name) or self._findMirrorAnywhere(name), bar)
		if not mirror:
			mirror = bar.create(selectCOMP, name)
			mirror.tags.add(self.MIRROR_TAG)
			self._placeMirror(mirror, bar)
		self._setExpr(mirror.par.selectpanel, self.SELECTPANEL_EXPR.format(canonical=canonical))
		self._applyMirrorGeometry(mirror, canonical, info)
		self._mirrorDragDrop(mirror, widget)
		self._anchorMirror(mirror, self._zoneSpec(self._entryZone(info)))
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(mirror.par.alignorder, self._mirrorOrder(info, seq_index))

	def _findMirrorAnywhere(self, name):
		"""A mirror whose entry changed zone still lives in the old container."""
		for bar in self._allBars():
			m = bar.op(name)
			if m is not None and self.MIRROR_TAG in m.tags:
				return m
		return None

	def _applyAdopted(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""An ADOPTED entry is a panel already living in the timeline -- TD's own
		transport controls. Managed IN PLACE: order and visibility are written
		straight onto the panel and no mirror is made, because making one would
		show the control twice."""
		o = self._resolvePanelOp(info)
		if o is None:
			return
		self._setConst(o.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		order = self._normalizeMenuOrder(info.get('menu_order'))
		if order is not None:
			self._setConst(o.par.alignorder, order)

	def AdoptTimelineWidget(self, widget_op, canonical_name, order=None, display=True):
		"""Take a panel that is ALREADY in the timeline under registry
		management (TD's built-in transport controls), so it can be reordered,
		grouped and hidden like any published widget.

		Unlike RegisterWidget this never creates a mirror (see _applyAdopted),
		and unlike the toolbar's adopt it keeps the panel's NATIVE alignorder
		space (0..12) rather than pushing it past MIRROR_ORDER_BASE -- an
		adopted native control belongs among its native siblings."""
		api = self._registryApi()
		if api is not self:
			return api.AdoptTimelineWidget(widget_op, canonical_name,
										   order=order, display=display)
		err = self._validateWidget(widget_op)
		if err:
			debug(f'{self.REGISTRY_NAME}: AdoptTimelineWidget({canonical_name!r}) rejected: {err}')
			return
		zone = self.DEFAULT_ZONE
		for zname, spec in self.ZONES.items():
			dlg = self._dialog()
			child = spec.get('child', '')
			holder = (dlg if not child else dlg.op(child)) if dlg else None
			if holder is not None and widget_op.parent() is holder:
				zone = zname
				break
		entry = {
			'panel_path': widget_op.path,
			'panel_id': int(widget_op.id),
			'display': '1' if display else '0',
			'adopted': '1',
			'zone': zone,
		}
		norm = self._normalizeMenuOrder(order)
		if norm is not None:
			entry['menu_order'] = norm
		# deliberately NO source_registry -- an adopted control is not published
		# by a host, and recording one couples it to whatever host adopted it.
		self.stored['PaneRegistry'][canonical_name] = entry
		self._syncSurface()
		return canonical_name

	def _injectGroupStart(self, canonical, info, bar, seq_index=None, ancestors=()):
		name = self._mirrorName(canonical)
		existing = self._relocateMirror(self._findMirrorAnywhere(name), bar)
		fresh = existing is None
		mirror = self._buildGroupToggleWidget(bar, name, info)
		mirror.tags.add(self.MIRROR_TAG)
		if fresh:
			self._placeMirror(mirror, bar)
		self._setConst(mirror.par.w, self._groupToggleWidth(info))
		fixed_h = self._zoneSpec(self._entryZone(info)).get('h')
		self._setConst(mirror.par.h, fixed_h or 20)
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(mirror.par.alignorder,
					   self._mirrorOrder(info, seq_index))

	def _injectGroupEnd(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""The closing bracket is STRUCTURE ONLY -- it marks where the group ends
		in the sequence and is never drawn. Clean up anything an earlier build
		left behind."""
		stale = self._findMirrorAnywhere(self._mirrorName(canonical))
		if stale is not None and self.MIRROR_TAG in stale.tags:
			stale.destroy()

	def _injectDivider(self, canonical, info, bar, seq_index=None, ancestors=()):
		"""Virtual divider: a registry-owned blank panel -- no source widget."""
		name = self._mirrorName(canonical)
		mirror = self._relocateMirror(self._findMirrorAnywhere(name), bar)
		if mirror is not None and mirror.OPType != 'containerCOMP':
			mirror.destroy()
			mirror = None
		if mirror is None:
			mirror = bar.create(containerCOMP, name)
			mirror.tags.add(self.MIRROR_TAG)
			self._placeMirror(mirror, bar)
		try:
			self._setConst(mirror.par.w, max(1, int(info.get('width', '3') or 3)))
		except (TypeError, ValueError):
			self._setConst(mirror.par.w, 3)
		fixed_h = self._zoneSpec(self._entryZone(info)).get('h')
		self._setConst(mirror.par.h, fixed_h or 20)
		self._setConst(mirror.par.bgalpha, 0)
		self._setConst(mirror.par.display, 1 if self._effectiveDisplay(info, ancestors) else 0)
		self._setConst(mirror.par.alignorder,
					   self._mirrorOrder(info, seq_index))

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
		"""Drop mirrors whose canonical is no longer registered.

		Keyed off entries that STILL RESOLVE (virtual entries -- dividers and
		group markers -- have no backing op and are always kept). Keying off raw
		stored keys would let a DEAD entry shield its own mirror: TD does not
		call onDestroyTD when a host dies inside its parent's subtree, so the
		entry outlives the COMP."""
		canonicals = [c for c, info in self.stored['PaneRegistry'].items()
					  if str(info.get('virtual', '')) == '1'
					  or self._resolvePanelOp(info) is not None]
		# A mirror is not the only thing an entry puts in the bar: a right-aligned
		# one also owns a SPACER. Pruning only `tlmirror_*` left the spacer of a
		# dead entry behind forever -- found as a `tlspacer_asdf` still holding
		# slack in the transport row for a canonical nothing had registered in
		# who knows how long. Everything an entry owns is pruned by the same pass.
		live = {self._mirrorName(c) for c in canonicals}
		# spacers are per-ZONE now; a stale per-canonical one must be swept
		live |= {self.SPACER_PREFIX + z for z in self.ZONES}
		for bar in self._allBars():
			for owned in (list(bar.ops(self.MIRROR_PREFIX + '*'))
						  + list(bar.ops(self.SPACER_PREFIX + '*'))):
				if self.MIRROR_TAG in owned.tags and owned.name not in live:
					owned.destroy()
		self._sweepOrphanSections()
		self._pruneEmptySections()

	def _pruneEmptySections(self):
		"""A section with nothing in it must not stay in someone else's dialog.

		Same rule as the registry itself: claim no surface when there is nothing
		to show. The container is ours, it sits inside TD's own chrome, and after
		the last contribution leaves there is no reason for it to be there.
		"""
		for zname, spec in self.ZONES.items():
			name = spec.get('section')
			if not name:
				continue
			dlg = self._dialog(zname)
			child = spec.get('child', '')
			host = (dlg if not child else dlg.op(child)) if dlg else None
			sec = host.op(name) if host is not None else None
			if sec is not None and self.MIRROR_TAG in sec.tags and not sec.children:
				sec.destroy()

	def _sweepOrphanSections(self):
		"""Destroy a managed section (and its contents) sitting anywhere but the
		host its zone currently names.

		Retargeting or retiring a zone strands the old one: nothing else
		collects it -- the prune pass only walks the CURRENT hosts, so an
		abandoned host is invisible to it forever while the stale copy keeps
		answering to the same name, with a live mirror still inside it.
		"""
		# A RETIRED zone has no spec left to look its section up by, so sweep
		# every section we own that no live zone claims. `properties` was
		# retired this way; without this its container would have sat in TD's
		# timeline forever, owned by nobody and named after a zone that no
		# longer exists.
		live_sections = {sp['section'] for sp in self.ZONES.values() if sp.get('section')}
		for dlg in {self._dialog(z) for z in self.ZONES}:
			if dlg is None:
				continue
			for found in dlg.findChildren(name=self.SECTION_PREFIX + '*'):
				if self.MIRROR_TAG in found.tags and found.name not in live_sections:
					found.destroy()
		for zname, spec in self.ZONES.items():
			name = spec.get('section')
			dlg = self._dialog(zname)
			if not name or dlg is None:
				continue
			child = spec.get('child', '')
			host = (dlg if not child else dlg.op(child))
			keep = host.op(name) if host is not None else None
			for found in dlg.findChildren(name=name):
				if found is not keep and self.MIRROR_TAG in found.tags:
					found.destroy()
			# ...and the mirrors the abandoned host still holds. A mirror that
			# moved with its zone leaves a working copy behind: the timeline drew
			# BOTH until one of them was covered, and only the live one answers to
			# the registry, so the leftover can never be told apart by name.
			if keep is None:
				continue
			for found in dlg.findChildren(name=self.MIRROR_PREFIX + '*'):
				if (self.MIRROR_TAG in found.tags
						and found.parent() is not keep
						and self._entryZone(self._infoForMirror(found.name)) == zname):
					found.destroy()

	def _infoForMirror(self, mirror_name):
		"""The registry entry a mirror belongs to, or {} if nothing claims it."""
		for canonical, info in self.stored['PaneRegistry'].items():
			if self._mirrorName(canonical) == mirror_name:
				return info
		return {}

	def _healRegistryEntries(self):
		"""Base healing plus surface repair: re-inject any registered entry whose
		mirror is missing or stale. This is what makes a LATE-arriving timeline
		work -- _syncSurface gives up after its retry budget, but the watch tick
		keeps checking and re-applies managed state."""
		super()._healRegistryEntries()
		if not self._is_sys_global() or not self._barReady():
			return
		names = self._registeredNamesInOrder()
		if not names:
			self._pruneMirrors()
			self._applyGrowthSettled()
			return
		self._ensureGroupMarkers()
		self._pruneMirrors()
		names = self._registeredNamesInOrder()
		ancestors, _ = self._scanGroups(names)
		for i, canonical in enumerate(names):
			self._injectWidget(canonical, i, ancestors.get(canonical, ()))
		self._applyGrowthSettled()

	# --- public API ---------------------------------------------------------

	def RegisterWidget(self, widget_op, canonical_name, order=None, display=True,
					   callback=None, source_registry=None, width=None, height=None,
					   help_url=None, zone=None):
		"""Publish a panel COMP into the timeline under canonical_name."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterWidget(
					widget_op, canonical_name, order=order, display=display,
					callback=callback, source_registry=source_registry,
					width=width, height=height, help_url=help_url, zone=zone)
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
			'zone': self._normalizeZone(zone),
		}
		norm_order = self._normalizeMenuOrder(order)
		if norm_order is not None:
			entry['menu_order'] = norm_order
		try:
			if width and int(width) > 0:
				entry['width'] = str(max(1, min(int(width), 800)))
		except (TypeError, ValueError):
			pass
		try:
			if height and int(height) > 0:
				entry['height'] = str(max(2, min(int(height), 400)))
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
		self.fnsLog(f'{self.REGISTRY_NAME}: registered widget "{canonical_name}" '
					f'({widget_op.path}) in zone "{entry["zone"]}"')
		if self._barReady():
			self._injectWidget(canonical_name)
			# the fast path injects straight into a ready bar and skips the sync
			# pass -- so it has to ask for the row itself, or a `grow` zone gets
			# its mirror with no row to put it in (UnregisterWidget always did
			# the reverse, which is what made the pair asymmetric)
			self._applyGrowthSettled()
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
		info = self.stored['PaneRegistry'].pop(canonical_name, None)
		self.fnsLog(f'{self.REGISTRY_NAME}: unregistered widget "{canonical_name}"')
		# An adopted native control keeps living in the bar -- give it back its
		# visibility rather than leaving it hidden by a registry that is gone.
		if info is not None and info.get('adopted') == '1':
			o = self._resolvePanelOp(info)
			if o is not None:
				self._setConst(o.par.display, 1)
			return
		self._restoreSourceWidth(canonical_name)
		mirror = self._findMirrorAnywhere(self._mirrorName(canonical_name))
		if mirror is not None and self.MIRROR_TAG in mirror.tags:
			mirror.destroy()
		self._applySurfaceGrowth()

	# RegistryBase healing calls self.UnregisterPanel(name); alias it.
	def UnregisterPanel(self, canonical_name):
		return self.UnregisterWidget(canonical_name)

	def SetWidgetZone(self, canonical_name, zone):
		"""Manager API: move a registered entry to another timeline zone."""
		api = self._registryApi()
		if api is not self:
			return api.SetWidgetZone(canonical_name, zone)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		info['zone'] = self._normalizeZone(zone)
		self._writeBackHostPar(info, 'Zone', info['zone'])
		self._syncSurface()
		return True

	def SetWidgetOrder(self, canonical_name, order):
		"""Manager API: reposition a registered widget."""
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

	def SetWidgetWidth(self, canonical_name, width):
		"""Manager API: override an entry's width (applied to the MIRROR,
		matchsize off -- the source widget's own size is never touched).
		width None/0/'' clears the override back to auto."""
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

	def SetWidgetSequence(self, canonical_names):
		"""Manager API: reassign order 1..N from the given full sequence.

		Names not in the sequence keep registration but drop to the end;
		unknown names are ignored. One surface sync at the end -- this is the
		batch primitive a drag-reorder UI calls."""
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

	def RegisterDivider(self, canonical_name, order=None, width=None,
						display=True, zone=None):
		"""Publish a VIRTUAL divider -- a registry-owned blank separator with no
		backing widget. Persistence is the publisher's job."""
		api = self._registryApi()
		if api is not self:
			return api.RegisterDivider(canonical_name, order=order, width=width,
									   display=display, zone=zone)
		entry = {'virtual': '1', 'divider': '1',
				 'display': '1' if display else '0',
				 'zone': self._normalizeZone(zone)}
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
			# the fast path injects straight into a ready bar and skips the sync
			# pass -- so it has to ask for the row itself, or a `grow` zone gets
			# its mirror with no row to put it in (UnregisterWidget always did
			# the reverse, which is what made the pair asymmetric)
			self._applyGrowthSettled()
		elif not self._pane_sync_queued:
			self._syncSurface()
		return canonical_name

	def RemoveDivider(self, canonical_name):
		api = self._registryApi()
		if api is not self:
			return api.RemoveDivider(canonical_name)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		if self._isDividerEntry(info):
			self.UnregisterWidget(canonical_name)
			return True
		debug(f'{self.REGISTRY_NAME}: RemoveDivider refused -- {canonical_name!r} is not a divider')
		return False

	@property
	def Widgets(self):
		"""Manager API: snapshot of all registered entries."""
		return {k: dict(v) for k, v in self.stored['PaneRegistry'].items()}

	@property
	def WidgetSequence(self):
		"""Manager API: canonical names in current order."""
		api = self._registryApi()
		if api is not self:
			return api.WidgetSequence
		return self._registeredNamesInOrder()

	def _writeBackHostPar(self, info, par_name, value):
		"""Persist a manager edit onto the entry's host publisher par
		(compare-before-set so host callbacks do not storm).

		ADOPTED entries are excluded: TD's built-ins have no host publisher of
		their own, and their source_registry would point at whatever host did
		the adopting -- which publishes its OWN widget."""
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

	def OpenConfigurator(self):
		"""No dedicated configurator yet -- the timeline surface is managed
		through the registry API (and, once it ships a hub tab, through
		FNS_Hub). Kept so the RegistryBase manager contract is complete."""
		debug(f'{self.REGISTRY_NAME}: no Timeline configurator installed yet')

	# --- host registration (Registration page), timeline flavor -------------

	def _syncZoneMenu(self):
		"""Keep a host's Zone menu in step with the zones that actually exist.

		The menu was authored by hand on the host COMP, so adding a zone in code
		left it unselectable -- `graphheading` existed, worked when registered
		from Python, and simply was not in the dropdown. A hand-written list of
		something the code already enumerates will drift every time, so it is
		derived instead.
		"""
		par = self.ownerComp.par['Zone']
		if par is None:
			return
		names = list(self.ZONES.keys())
		if list(par.menuNames or ()) == names:
			return
		# A TD menu par stores an INDEX, so rewriting menuNames silently
		# reinterprets whatever it held: retiring `properties` turned every
		# host sitting on index 1 into `background` without a callback firing.
		# The par is therefore not trustworthy across a rebuild -- prefer what
		# this host actually REGISTERED, which is recorded on the entry, and
		# fall back to the par only when nothing is registered yet.
		current = self._registeredZone() or str(par.eval())
		par.menuNames = names
		par.menuLabels = [n.replace('_', ' ').title() for n in names]
		if current in names:                 # setting menuNames resets the value
			par.val = current

	def _registeredZone(self):
		"""The zone this host's own registration is actually using, if any."""
		canonical = self.stored['HostCanonical']
		if not canonical:
			return None
		try:
			info = dict(self._registryApi().Widgets).get(canonical) or {}
		except Exception:
			return None
		zone = str(info.get('zone') or '')
		return zone if zone in self.ZONES else None

	def _applyHostRegistration(self, force=False):
		self._syncZoneMenu()
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
		bar_height = None
		if hasattr(self.ownerComp.par, 'Barheight'):
			try:
				bh = int(self.ownerComp.par.Barheight.eval())
				bar_height = bh if bh > 0 else None
			except (TypeError, ValueError):
				pass
		zone = None
		if hasattr(self.ownerComp.par, 'Zone'):
			zone = self.ownerComp.par.Zone.eval()
		api.RegisterWidget(
			widget, canonical,
			order=self._hostMenuOrder(),
			display=display,
			callback=self._hostCallbackDat(),
			source_registry=self.ownerComp,
			width=bar_width,
			height=bar_height,
			help_url=self._hostHelpUrl(widget),
			zone=zone,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {widget.path}')
		self._ensureToolRegistryPage()

	def _hostHelpUrl(self, widget):
		p = getattr(self.ownerComp.par, 'Helpurl', None)
		if p is None:
			return None
		try:
			val = str(p.eval()).strip()
		except Exception:
			return None
		return val or None

	# --- Registration page callbacks ---------------------------------------

	def onParAutoregister(self, _par, _val=None, _prev=None):
		# Autoregister is a TOGGLE, so CustomParHelper dispatches it through
		# OnValueChange with (_par, _val, _prev) -- a one-argument handler is
		# never called and the toggle silently does nothing. (The toolbar's host
		# has the same one-arg signature and gets away with it because its
		# Registration pars are BOUND to the tool's page and fire from there;
		# these hosts are CONSTANT, so they need the real signature.)
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

	def onParZone(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParBarheight(self, _par, _val, _prev):
		# the height rides in the stored ENTRY, so changing it has to
		# re-register -- writing the host par alone leaves the bar at the
		# height the last registration asked for
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()
