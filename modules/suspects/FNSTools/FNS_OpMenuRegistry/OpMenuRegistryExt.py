

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or next((c for c in me.parent().children if 'ExtUtils' in c.tags), None)).mod('CustomParHelper').CustomParHelper # import
###

import os
import time
from collections import defaultdict, deque

RegistryBase = mod('RegistryBase').RegistryBase


class OpMenuRegistryExt(RegistryBase):
	"""Registry for TD's Insert-Operator dialog (/ui/dialogs/menu_op).

	Tools publish CONTRIBUTIONS instead of the dialog hardcoding them:

	  * fuzzy search words   -- extra words that match an operator type
	  * node-table decorations -- relabel a row (e.g. mark 'has a template')
	  * right-click menu items -- appended after TD's own three

	Every contribution's CODE lives in the publishing tool, in a callbacks
	DAT the tool owns; the entry only carries a reference to it. This
	registry therefore never names a tool, and a tool's menu behaviour
	travels inside that tool's own tox.

	Callbacks DAT protocol (all functions optional):

		def onSearchWords():
			'''{opType: [word, ...]} merged into the dialog's fuzzy search.'''
			return {}

		def onDecorateLabel(opType, label):
			'''Return a replacement row label, or None to leave it alone.'''
			return None

		def onMenuItems():
			'''Labels this tool adds to the node table's right-click menu.'''
			return []

		def onMenuItem(label, opType):
			'''One of this tool's menu items was clicked.'''
			pass

		def onChainNodes():
			'''Script DATs to splice into the node table's filter chain,
			after TD's own 'families' node, in contributor order.'''
			return []

		def onPanels():
			'''Panel COMPs to inject into the dialog, as (comp, anchor)
			where anchor names a panel inside /ui/dialogs/menu_op whose
			output the injected panel's input is wired to.'''
			return []

		def onAlternatives():
			'''{opType: [alternative, ...]} this tool offers when that type is
			created with the registry's Shortcutalternatives keys held.

			An alternative is {'label': str, 'source': OP | str, 'help': str}.
			`source` is the op or COMP that replaces the fresh operator, or a
			.tox path the registry loads first. A COMP is placed WHOLE, as one
			node, wired through its connectors -- that is a tool offering
			itself. Add 'unpack': True to have a COMP's children copied out
			instead (a library base holding a chain; TEMPLATE_ROOT/IN/OUT
			tags or the in/out ops mark the ends). A bare OP is accepted,
			labelled with its name, and unpacks. OpTemplates publishes its
			library this way; any tool may publish itself.'''
			return {}
	"""

	SHORTCUT = 'FNS_OPMENUREGISTRY'
	EXT_NAME = 'OpMenuRegistryExt'
	REGISTRY_NAME = 'FNS_OpMenuRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Om'
	TOOL_PAGE_LABEL = 'Op Menu'
	# Ordered as a setup flow, matching the host's Registration page:
	# make the callbacks DAT, turn registration on, see the result, then tune
	# how the contribution appears.
	TOOL_PAGE_PARS = ('Createcallbacks', 'Autoregister', 'Register', 'Regstatus',
					  'Menuorder', 'Displayed')

	# The DAT a host spawns into its tool, and the template it comes from.
	CALLBACKS_NAME = 'opmenu_callbacks'
	CALLBACKS_TEMPLATE = 'callbacks_template'

	# TD's stock Insert-Operator dialog.
	MENU_PATH = '/ui/dialogs/menu_op'
	# TD puts keyboard focus in the search field when the dialog opens
	# (launch_menu_op / set_focus both end with `controlpanel -k` on it), and
	# typing straight away is the whole point of the dialog. Adding or
	# removing a child panel relays out the container and drops that focus.
	# Steady state is converged so this never fires, but during the boot
	# window hosts register ONE AT A TIME -- each registration is a real
	# change -- so a dialog opened early loses its focus mid-type.
	SEARCH_FIELD = 'search/textfield'
	NODETABLE_PATH = '/ui/dialogs/menu_op/nodetable'
	POPMENU_PATH = '/ui/dialogs/menu_op/nodetable/popMenu'
	POPMENU_CALLBACKS = 'popMenuCallbacks'

	# TD's own right-click items (Help / Python Help / Snippets) always lead;
	# registered items are appended after them. The dispatcher in
	# popmenu_dispatch uses the same offset.
	BUILTIN_MENU_ITEMS = 3

	# Contributed chain stages are spliced in after TD's own 'families' node.
	# The registry owns NO stage of its own: aggregating search words and
	# decorators is registry work, but APPLYING them to TD's operator table
	# is a contribution like any other (FNS_OpMenu publishes that stage), so
	# nothing here is coupled to TD's node-table schema.
	CHAIN_ANCHOR = 'families'
	POPMENU_HEIGHT_EXPR = '18 * op("./itemsLayout").numRows'
	# Where a parameter-declared panel is wired when no anchor is given.
	DEFAULT_PANEL_ANCHOR = 'searchpanel'
	# Injected panels sit in the dialog's vertical layout flow, so their
	# vertical sizing must yield to it. A source left on 'fixed' bloats the
	# row and shoves the dialog out of shape -- soft-enforced on the COPY
	# every sync, exactly like the toolbar enforces mirror height. The
	# publisher's own COMP is never touched.
	PANEL_VMODE = 'fill'

	# Registry-owned artifacts published BY tools: filter-chain script DATs
	# and dialog panels. Tagged and pruned so we only ever touch our own.
	CHAIN_TAG = 'OpMenuRegistryChain'
	PANEL_TAG = 'OpMenuRegistryPanel'

	# --- surface hooks (RegistryBase contract) ---

	def _ensureSelectionExecuteRole(self):
		self._ensureAlternatives()
		# Hosts must not keep a parallel table; the global owns all entries.
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _syncSurface(self, attempts=40):
		"""Idempotent: splice contributed stages and panels into the dialog and
		rebuild the right-click menu from registered entries. Defers until
		TD's Insert-Operator dialog exists."""
		self._pane_sync_queued = False
		if self._menuReady():
			had_focus = self._hasSearchFocus()
			self._syncChain()
			changed = self._syncPanels()
			self._syncPopMenu()
			if changed and had_focus:
				self._restoreSearchFocus()
			return
		if attempts <= 0:
			debug(f'{self.REGISTRY_NAME}: {self.MENU_PATH} never became available, '
				  f'skipping sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	def _healRegistryEntries(self):
		"""Base healing (incl. the boot re-publish sweep and clone healing)
		plus surface repair -- this is what makes a LATE dialog work and what
		restores the chain node if TD rebuilt it."""
		super()._healRegistryEntries()
		if not self._is_sys_global() or not self._menuReady():
			return
		had_focus = self._hasSearchFocus()
		self._syncChain()
		changed = self._syncPanels()
		self._syncPopMenu()
		if changed and had_focus:
			self._restoreSearchFocus()

	def Resync(self):
		"""Public: re-apply the whole surface now. Publishers whose
		contributions depend on a live toggle call this instead of waiting
		for the healing tick."""
		api = self._registryApi()
		if api is not self:
			return api.Resync()
		self._syncSurface()
		return True

	# Location-independent: resolves through the op-menu package's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	# _healHostClones and StampHost come from RegistryBase off these two.
	CLONE_EXPR = "op.FNS.op('FNS_OpMenuRegistry') if hasattr(op, 'FNS') else None"

	# --- surface helpers ---

	def _menuReady(self):
		nodetable = op(self.NODETABLE_PATH)
		return bool(nodetable and nodetable.valid)

	def _setExpr(self, par, expr):
		# Compare-before-set: the healing tick re-runs this every few seconds,
		# so repeated identical writes must be free.
		if par.mode != ParMode.EXPRESSION or par.expr != expr:
			par.expr = expr

	def _setConst(self, par, value):
		if par.mode != ParMode.CONSTANT or par.eval() != value:
			par.val = value
			par.mode = ParMode.CONSTANT

	def _injectAfter(self, target_comp, target_op, inject_op, panelparent=None):
		"""Splice a copy of inject_op into target_op's output chain.

		Generalized from the legacy FNS_OpMenu install() injector: an existing
		copy is replaced in place, keeping whatever was downstream of it (so a
		re-inject never orphans another tool's node further down the chain).
		"""
		existing = target_comp.op(inject_op.name)
		if existing is not None:
			out_owners = ([c.owner for c in existing.outputConnectors[0].connections]
						  if existing.outputConnectors else [])
			existing.destroy()
		elif target_op is not None and target_op.outputConnectors:
			out_owners = [c.owner for c in target_op.outputConnectors[0].connections]
		else:
			out_owners = []

		new_op = target_comp.copy(inject_op)
		if target_op is not None:
			new_op.nodeX = target_op.nodeX + 150
			new_op.nodeY = target_op.nodeY
		for i, dock in enumerate(new_op.docked):
			dock.nodeX = new_op.nodeX
			dock.nodeY = new_op.nodeY - 100 - i * 100
		if new_op.isPanel and panelparent is not None and new_op.inputCOMPConnectors:
			new_op.inputCOMPConnectors[0].connect(panelparent.outputCOMPConnectors[0])
		if new_op.outputConnectors:
			for owner in out_owners:
				if owner is not None and owner.valid:
					new_op.outputConnectors[0].connect(owner)
		if new_op.inputConnectors and target_op is not None:
			new_op.inputConnectors[0].connect(target_op)
		new_op.bypass = False
		return new_op

	def _adoptInjected(self, node, source, tag):
		"""Mark an injected copy as ours and point it at its OWN docked
		callbacks DAT (a copied callbacks par holds the SOURCE's absolute
		path, which would tether every copy back to the publishing tool)."""
		node.tags.add(tag)
		node.store('source_id', int(source.id))
		cb = next((d for d in node.docked if d.isDAT), None)
		cb_par = getattr(node.par, 'callbacks', None)
		if cb is not None and cb_par is not None:
			self._setConst(cb_par, cb.name)

	def _isStale(self, node, source, tag):
		return (node is None or tag not in node.tags
				or node.fetch('source_id', None) != int(source.id))

	def _syncChain(self):
		"""Splice every publisher's filter-chain script DATs into the node
		table, in contributor order, downstream of the registry's own node.

		This is what the legacy installer hardcoded for the I/O filter: any
		tool can now contribute a chain stage, and the chain heals and
		re-orders itself instead of depending on install order.
		"""
		nodetable = op(self.NODETABLE_PATH)
		if nodetable is None:
			return
		anchor = nodetable.op(self.CHAIN_ANCHOR)
		if anchor is None:
			debug(f'{self.REGISTRY_NAME}: no {self.CHAIN_ANCHOR!r} in {self.NODETABLE_PATH}')
			return
		wanted = {}
		for canonical, fn in self._contributions('onChainNodes'):
			try:
				nodes = fn() or []
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onChainNodes from {canonical!r}: {e}')
				continue
			if not isinstance(nodes, (list, tuple)):
				nodes = [nodes]
			for src in nodes:
				if src is None or not src.valid:
					continue
				wanted[src.name] = (canonical, src)
		# prune chain stages we own that nobody publishes any more
		for o in list(nodetable.children):
			if self.CHAIN_TAG in o.tags and o.name not in wanted:
				o.destroy()
		prev = anchor
		stages = []
		for name, (canonical, src) in wanted.items():
			node = nodetable.op(name)
			if self._isStale(node, src, self.CHAIN_TAG):
				node = self._injectAfter(nodetable, prev, src)
				if node is None:
					continue
				self._adoptInjected(node, src, self.CHAIN_TAG)
			stages.append(node)
			prev = node
		self._relinkChain(anchor, stages)

	def _relinkChain(self, anchor, stages):
		"""Enforce anchor -> stage1 -> ... -> stageN -> (chain consumers).

		Wiring must be re-asserted for EXISTING stages too, not just newly
		injected ones: a stage that is merely 'not stale' is still wired to
		whatever neighbour it had when it was injected, so adding, removing
		or re-ordering any other stage silently leaves it mis-linked (and can
		strand TD's own downstream ops on the wrong stage).
		"""
		chain = [anchor] + [s for s in stages if s is not None and s.valid]
		ours = {s.id for s in chain[1:]}

		# who consumed the chain before we touched it -- remember the exact
		# input index so a multi-input consumer is reconnected faithfully
		consumers = []
		for member in chain:
			if not member.outputConnectors:
				continue
			for conn in member.outputConnectors[0].connections:
				dest = conn.owner
				if dest is None or not dest.valid or dest.id in ours:
					continue
				for idx, in_conn in enumerate(dest.inputConnectors):
					if any(c.owner is member for c in in_conn.connections):
						if (dest, idx) not in consumers:
							consumers.append((dest, idx))

		# link the stages in contributor order
		for i in range(1, len(chain)):
			node, want = chain[i], chain[i - 1]
			if not node.inputConnectors:
				continue
			first = node.inputConnectors[0]
			if not (len(first.connections) == 1 and first.connections[0].owner is want):
				first.disconnect()
				first.connect(want)
			for extra in node.inputConnectors[1:]:
				if extra.connections:
					extra.disconnect()

		# the LAST stage feeds whatever consumed the chain
		tail = chain[-1]
		if tail.outputConnectors:
			for dest, idx in consumers:
				if idx >= len(dest.inputConnectors):
					continue
				in_conn = dest.inputConnectors[idx]
				if not any(c.owner is tail for c in in_conn.connections):
					in_conn.disconnect()
					in_conn.connect(tail)
		return tail

	def _syncPanels(self):
		"""Inject every publisher's dialog panels, anchored to the panel they
		name (the legacy installer hardcoded 'searchpanel').

		Two sources, merged: the host's `Panel` parameter (zero-code) and
		whatever onPanels() returns (computed). A tool may use either or both.
		"""
		menu = op(self.MENU_PATH)
		if menu is None:
			return
		wanted = {}
		# 1. parameter-declared panels, straight off the entries
		for canonical in self._activeNames():
			info = self.stored['PaneRegistry'].get(canonical) or {}
			comp = self._resolveByIdOrPath(info.get('decl_panel_id'),
										   info.get('decl_panel_path'))
			if comp is not None and comp.valid:
				wanted[comp.name] = (canonical, comp,
									 info.get('decl_panel_anchor') or self.DEFAULT_PANEL_ANCHOR)
		# 2. callback-declared panels
		for canonical, fn in self._contributions('onPanels'):
			try:
				items = fn() or []
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onPanels from {canonical!r}: {e}')
				continue
			for item in items:
				if isinstance(item, (list, tuple)):
					comp = item[0] if item else None
					anchor_name = item[1] if len(item) > 1 else None
				else:
					comp, anchor_name = item, None
				if comp is None or not comp.valid:
					continue
				wanted[comp.name] = (canonical, comp, anchor_name)
		# whether the dialog's CHILD SET changed -- the layout-affecting part,
		# and so the part that costs the search field its keyboard focus
		changed = False
		for o in list(menu.children):
			if self.PANEL_TAG in o.tags and o.name not in wanted:
				o.destroy()
				changed = True
		for name, (canonical, src, anchor_name) in wanted.items():
			panel = menu.op(name)
			if self._isStale(panel, src, self.PANEL_TAG):
				changed = True
				anchor = menu.op(anchor_name) if anchor_name else None
				if anchor_name and anchor is None:
					debug(f'{self.REGISTRY_NAME}: {canonical!r} panel anchor '
						  f'{anchor_name!r} not found in {self.MENU_PATH}')
				panel = self._injectAfter(menu, None, src, panelparent=anchor)
				if panel is None:
					continue
				self._adoptInjected(panel, src, self.PANEL_TAG)
			d = getattr(panel.par, 'display', None)
			if d is not None:
				self._setConst(d, 1)
			# the copy yields to the dialog's layout; the source keeps its own
			vm = getattr(panel.par, 'vmode', None)
			if vm is not None and str(vm.eval()) != self.PANEL_VMODE:
				try:
					vm.val = self.PANEL_VMODE
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: vmode on {panel.path}: {e}')
		return changed

	# --- keyboard focus (see SEARCH_FIELD) ---

	def _searchField(self):
		menu = op(self.MENU_PATH)
		return menu.op(self.SEARCH_FIELD) if menu is not None else None

	def _hasSearchFocus(self):
		"""True when the dialog's search field currently holds keyboard focus."""
		field = self._searchField()
		if field is None:
			return False
		try:
			return bool(field.panel.focus)
		except Exception:
			return False

	def _restoreSearchFocus(self):
		"""Hand keyboard focus back, once the relayout has settled.

		Only ever called when the field HAD focus a moment ago, so this
		restores what our own edit took -- it never steals focus from
		somewhere else, and never opens or raises the dialog.
		"""
		field = self._searchField()
		if field is None:
			return
		run('args[0].valid and args[0].setKeyboardFocus()', field,
			delayFrames=1, delayRef=op.TDResources)

	def _syncPopMenu(self):
		"""Rebuild the node table's right-click menu: TD's stock items first,
		then one entry per registered menu item, and install the dispatcher
		that routes clicks back here."""
		pop = op(self.POPMENU_PATH)
		if pop is None:
			return
		self._setExpr(pop.par.h, self.POPMENU_HEIGHT_EXPR)
		items_par = getattr(pop.par, 'Items', None)
		if items_par is None:
			return
		try:
			items = list(eval(items_par.eval()))
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: unreadable popMenu Items: {e}')
			return
		desired = items[:self.BUILTIN_MENU_ITEMS] + [label for _, label in self.MenuItems]
		if items != desired:
			items_par.val = str(desired)
		# The dialog's callbacks DAT is TD's, living outside our component --
		# keep its text in sync with our dispatcher template.
		src = self.ownerComp.op('popmenu_dispatch')
		dst = pop.parent().op(self.POPMENU_CALLBACKS)
		if src is not None and dst is not None and dst.text != src.text:
			dst.text = src.text

	# --- contribution model ---

	def _activeNames(self):
		"""Registered canonical names in menu order, hidden entries dropped."""
		entries = self.stored['PaneRegistry']
		ordered, unordered = [], []
		for name, info in entries.items():
			if info.get('display', '1') == '0':
				continue
			order = self._normalizeMenuOrder(info.get('menu_order'))
			(ordered if order is not None else unordered).append((order, name))
		ordered.sort(key=lambda t: (t[0], t[1].lower()))
		return [n for _, n in ordered] + [n for _, n in sorted(unordered, key=lambda t: t[1].lower())]

	def _callbackModule(self, info):
		"""Compile the publishing tool's callbacks DAT. A broken callbacks DAT
		must never take the whole dialog down -- it is reported and skipped."""
		dat = self._resolveCallbackDat(info)
		if dat is None:
			return None
		try:
			return dat.module
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: callbacks DAT {dat.path} failed to compile: {e}')
			return None

	def _contributions(self, hook):
		"""Yield (canonical, function) for every active entry defining hook."""
		entries = self.stored['PaneRegistry']
		for name in self._activeNames():
			module = self._callbackModule(entries.get(name))
			if module is None:
				continue
			fn = getattr(module, hook, None)
			if callable(fn):
				yield name, fn

	@property
	def SearchWords(self):
		"""Merged {opType: [word, ...]} from every contributor.

		Read by the injected node's onCook -- the replacement for the single
		hardcoded search-word table the dialog used to reach for by name.
		"""
		api = self._registryApi()
		if api is not self:
			return api.SearchWords
		merged = {}
		for name, fn in self._contributions('onSearchWords'):
			try:
				contributed = fn() or {}
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onSearchWords from {name!r}: {e}')
				continue
			try:
				pairs = contributed.items()
			except AttributeError:
				debug(f'{self.REGISTRY_NAME}: onSearchWords from {name!r} did not return a dict')
				continue
			for optype, words in pairs:
				if isinstance(words, str):
					words = [words]
				bucket = merged.setdefault(str(optype), [])
				for w in words or []:
					w = str(w).strip()
					if w and w not in bucket:
						bucket.append(w)
		return merged

	@property
	def Alternatives(self):
		"""Merged {opType: [alternative, ...]} from every contributor.

		A contributor's key may name several types at once, space-separated
		or as a list (see _alternativeKeyTypes); the merge is always keyed by
		one type. Each alternative is normalised to {'label', 'source',
		'help', 'contributor'} so the picker can group by tool and the engine
		can say where a placement came from. A contributor that raises, or
		returns something that is not a dict, is skipped and named in the
		log; it never costs the others their entries -- same isolation as
		SearchWords.
		"""
		api = self._registryApi()
		if api is not self:
			return api.Alternatives
		cached = getattr(self, '_altCache', None)
		if cached is not None and cached[0] == absTime.frame:
			return cached[1]
		merged = {}
		for name, fn in self._contributions('onAlternatives'):
			try:
				contributed = fn() or {}
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onAlternatives from {name!r}: {e}')
				continue
			try:
				pairs = contributed.items()
			except AttributeError:
				debug(f'{self.REGISTRY_NAME}: onAlternatives from {name!r} did not return a dict')
				continue
			for key, alts in pairs:
				if not isinstance(alts, (list, tuple)):
					alts = [alts]
				entries = [e for e in (self._normalizeAlternative(alt, name) for alt in alts)
						   if e is not None]
				for optype in self._alternativeKeyTypes(key):
					merged.setdefault(optype, []).extend(entries)
		for optype, alts in self._storeAlternatives().items():
			merged.setdefault(optype, []).extend(alts)
		self._altCache = (absTime.frame, merged)
		return merged

	@staticmethod
	def _alternativeKeyTypes(key):
		"""The operator types one onAlternatives() key names.

		A key is one type ('moviefileinTOP'), several separated by spaces
		('moviefileinTOP ndiinTOP'), or a list/tuple of them -- so a tool
		that stands in for several types declares its alternative once.
		"""
		if isinstance(key, (list, tuple, set)):
			names = [str(k) for k in key]
		else:
			names = str(key).split()
		return [n for n in (x.strip() for x in names) if n]

	@staticmethod
	def _normalizeAlternative(alt, contributor):
		"""One contributed alternative as a dict, or None when it is unusable.

		A bare OP is the common case for a template library; a dict lets a
		tool name itself and point at a .tox on disk.
		"""
		if isinstance(alt, OP):
			return {'label': alt.name, 'source': alt, 'help': '',
					'contributor': contributor, 'unpack': True}
		if not isinstance(alt, dict):
			return None
		source = alt.get('source')
		if source is None:
			return None
		# a .tox path (the store layer's source) labels itself by file name
		fallback = getattr(source, 'name', '') if isinstance(source, OP) else 			os.path.splitext(os.path.basename(str(source)))[0]
		label = str(alt.get('label') or fallback or '').strip()
		if not label:
			return None
		return {'label': label, 'source': source,
				'help': str(alt.get('help', '') or ''),
				'contributor': contributor,
				# a bare op from a library unpacks; a tool that names itself
				# is placed whole unless it asks to be unpacked
				'unpack': bool(alt.get('unpack', False))}

	# ------------------------------------------------------------------
	# Op alternatives: the engine (moved here from OpTemplates, 2026-09-10)
	#
	# The surface is "you just created an operator with the modifier held":
	# every contributor's onAlternatives() for that type is collected, one
	# alternative is placed straight away, several open a picker. The code
	# that swaps the fresh op for the chosen alternative and restores its
	# wiring is placeOPchain from OpTemplates, ported whole -- it handles
	# single ops, chains, COMPs, docked ops and family-convert operators,
	# and that behaviour is the contract every contributor now gets.
	#
	# Only the /sys global runs any of this: the watcher DAT's Active
	# parameter is an identity test, and every method below that acts
	# delegates to the global first. Design: docs/OpAlternatives.md.
	# ------------------------------------------------------------------

	ALTERNATIVES_PAGE = 'Alternatives'
	ALTERNATIVES_SHORTCUT_PAR = 'Shortcutalternatives'
	_TEMPLATE_TAGS = ('TEMPLATE_OUT', 'TEMPLATE_IN', 'TEMPLATE_COPY', 'TEMPLATE_ROOT')
	_FAMILY_CONVERT_TYPES = ('choptoTOP', 'dattoCHOP', 'toptoCHOP', 'soptoCHOP',
							 'choptoDAT', 'soptoDAT', 'chopexecDAT',
							 'choptoSOP', 'trailSOP', 'toptoPOP', 'poptoTOP', 'choptoPOP',
							 'soptoPOP', 'dattoPOP', 'poptoCHOP', 'poptoDAT', 'poptoSOP')

	def _ensureAlternatives(self):
		"""Get-or-create the Alternatives page on the master and the global.
		Never overwrites a value there. A HOST sheds the page instead: it
		arrives as a copy of the master carrying the par, nothing on a host
		reads it, and the hotkey manager listed every copy as one more
		'alt ctrl' binding (five rows for one setting, 2026-09-10)."""
		c = self.ownerComp
		if not (self._is_sys_global() or self._isMaster()):
			self._shedAlternativesPage()
		else:
			page = next((pg for pg in c.customPages if pg.name == self.ALTERNATIVES_PAGE), None)
			if page is None:
				page = c.appendCustomPage(self.ALTERNATIVES_PAGE)
			p = c.par[self.ALTERNATIVES_SHORTCUT_PAR]
			default = 'alt ctrl' if app.osName == 'Windows' else 'cmd ctrl'
			if p is None:
				p = page.appendStr(self.ALTERNATIVES_SHORTCUT_PAR, label='Alternatives Shortcut')[0]
				p.val = default
			p.default = default
			p.help = ('Modifier keys to hold while creating an operator to be offered '
					  'the alternatives registered for its type (space-separated: alt, '
					  'ctrl, shift, cmd). Without the keys the operator is created as '
					  'normal. Applies on the /sys global; the master holds the value '
					  'the global is promoted with.')
		if getattr(self, '_observed', None) is None:
			self.refreshObserved()
		self._shedEngineOps()

	def _shedAlternativesPage(self):
		"""Drop the copied Alternatives page from a host (par first, then the
		page once it is empty)."""
		c = self.ownerComp
		p = c.par[self.ALTERNATIVES_SHORTCUT_PAR]
		if p is not None and p.page.name == self.ALTERNATIVES_PAGE:
			try:
				p.destroy()
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: could not shed {self.ALTERNATIVES_SHORTCUT_PAR} from {c.path}: {e}')
		page = next((pg for pg in c.customPages if pg.name == self.ALTERNATIVES_PAGE), None)
		if page is not None and not list(page.pars):
			try:
				page.destroy()
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: could not shed the {self.ALTERNATIVES_PAGE} page from {c.path}: {e}')

	ENGINE_OPS = ('hotkey', 'watch_children')

	def _isMaster(self):
		"""The depth-1 package under the toolkit root, the one StampHost copies."""
		root = getattr(op, 'FNS', None)
		c = self.ownerComp
		return root is not None and c.parent() is root and c.name == self.REGISTRY_NAME

	def _shedEngineOps(self):
		"""A host is a COPY of the master (StampHost), so it arrives carrying
		the watcher and the hotkey chain. The watcher is gated inert, but the
		chain's keyboardin cooks on every key event wherever it lives, and a
		host needs neither: only the /sys global runs the engine. Hosts drop
		both at init; the master and the global keep them."""
		if self._is_sys_global() or self._isMaster():
			return
		for name in self.ENGINE_OPS:
			o = self.ownerComp.op(name)
			if o is not None:
				try:
					o.destroy()
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: could not shed {name} from {self.ownerComp.path}: {e}')

	# -- the watcher -----------------------------------------------------

	def _snapshotChildren(self):
		"""{id: op} for the current pane owner's immediate children.

		Immediate children only, keyed by OP.id: the cook-diet form of the
		OpTemplates observer (a deep walk cost a full findChildren of whatever
		network was open, and keying by the op itself read a rename as a
		create + delete and placed a template on rename)."""
		try:
			target = ui.panes.current.owner
		except Exception:
			target = None
		return {c.id: c for c in target.children} if target else {}

	def _observedOwnerId(self):
		try:
			target = ui.panes.current.owner
		except Exception:
			target = None
		return target.id if target else None

	def _rebaseline(self, current):
		self._observedOwner = self._observedOwnerId()
		self._observed = current
		# OP ids only grow within a session, so the highest id seen at a tick
		# separates "existed somewhere already" from "created since" -- the
		# only way to tell a fresh op apart on the first tick in a network
		# the watcher has no snapshot for.
		seen = getattr(self, '_idWatermark', 0) or 0
		self._idWatermark = max([seen] + list(current.keys()))

	def refreshObserved(self):
		"""Re-baseline the snapshot -- after a placement, so the pasted ops
		are not read as new and placed again."""
		self._rebaseline(self._snapshotChildren())

	def observeChildren(self):
		"""watch_children's hook: diff the snapshot, hand each new undocked op
		to the engine. The docked check is why a rampTOP's docked DAT never
		counts as a creation.

		A pane switch is not a creation either: the watched op follows
		ui.panes.current.owner, and there is no tick on the switch itself, so
		the first tick after entering a network has no snapshot of it. Diffing
		against the previous network's snapshot read every child as new and,
		with the modifier held, offered alternatives for all of them
		(measured: 100 offers from one navigation into /). On a changed owner
		the candidates are the children whose id is above the watermark of the
		last tick: the op just created, and nothing that already existed."""
		if not self._is_sys_global():
			return
		owner = self._observedOwnerId()
		current = self._snapshotChildren()
		if owner != getattr(self, '_observedOwner', None):
			mark = getattr(self, '_idWatermark', None)
			new_ids = {i for i in current if mark is not None and i > mark}
		else:
			before = getattr(self, '_observed', None) or {}
			new_ids = current.keys() - before.keys()
		self._rebaseline(current)
		for _id in new_ids:
			_op = current[_id]
			if _op is not None and _op.valid and not _op.dock:
				self._onNewOp(_op)

	# -- the gate and the pick -------------------------------------------

	@property
	def _shortcutHeld(self):
		hk = self.ownerComp.op('hotkey/out1')
		try:
			return bool(hk[0].eval()) if hk is not None else False
		except Exception:
			return False

	def _onNewOp(self, _op, force=False):
		"""A fresh operator: offer its alternatives if the modifier is held.

		`force` skips the modifier (programmatic use and tests); it never
		skips the type check."""
		if not (force or self._shortcutHeld):
			return
		alts = self.Alternatives.get(_op.OPType) or []
		if not alts:
			return
		if len(alts) == 1:
			self.PlaceAlternative(_op, alts[0])
			return
		live = [a for a in alts if a.get('contributor') != self.STORE_CONTRIBUTOR]
		store = [a for a in alts if a.get('contributor') == self.STORE_CONTRIBUTOR]
		ordered = live + store
		self._pendingOrig = _op
		self._pendingAlts = ordered
		labels = [self._pickLabel(a) for a in ordered]
		# the store's entries sit below a divider: same picker, its own section
		dividers = [self._pickLabel(live[-1])] if live and store else []
		try:
			op.TDResources.PopMenu.Open(items=labels, callback=self._onAlternativePicked,
										callbackDetails={'optype': _op.OPType},
										dividersAfterItems=dividers or None,
										title=_op.OPType)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: picker failed to open: {e}')
			self._pendingOrig, self._pendingAlts = None, []

	@staticmethod
	def _pickLabel(alt):
		"""'label  (contributor)' -- two contributors may both call something
		'noise', and the tool name is what tells them apart."""
		return '%s  (%s)' % (alt['label'], alt['contributor'])

	def _onAlternativePicked(self, info):
		"""TDResources.PopMenu callback: place the chosen alternative."""
		orig, alts = getattr(self, '_pendingOrig', None), getattr(self, '_pendingAlts', None) or []
		self._pendingOrig, self._pendingAlts = None, []
		if orig is None or not orig.valid:
			return
		item = (info or {}).get('item')
		chosen = next((a for a in alts if self._pickLabel(a) == item), None)
		if chosen is None:
			return
		self.PlaceAlternative(orig, chosen)

	def PlaceAlternative(self, orig_op, alternative):
		"""Replace `orig_op` in place with one alternative (a dict from
		Alternatives, or a bare OP), restoring its input and output wiring.
		Promoted: a tool or a test may place programmatically, and the store
		layer calls this with a .tox source."""
		api = self._registryApi()
		if api is not self:
			return api.PlaceAlternative(orig_op, alternative)
		if isinstance(alternative, OP):
			alternative = {'label': alternative.name, 'source': alternative,
						   'help': '', 'contributor': ''}
		source = alternative.get('source')
		if orig_op is None or not orig_op.valid:
			return False
		if isinstance(source, str):
			debug(f'{self.REGISTRY_NAME}: placing {alternative.get("label")!r} from the store '
				  f'for {orig_op.OPType} at {orig_op.path}')
			ok = self._placeTox(orig_op, source, name=alternative.get('package'))
			self.refreshObserved()
			return ok
		if not isinstance(source, OP):
			debug(f'{self.REGISTRY_NAME}: alternative {alternative.get("label")!r} has a '
				  f'{type(source).__name__} source; not placeable')
			return False
		if not source.valid:
			return False
		if orig_op.path == source.path or orig_op.path.startswith(source.path + '/'):
			# a tool cannot stand in for an operator inside itself: the copy
			# would land inside its own source (the case of testing a tool's
			# alternative from within that tool's network)
			debug(f'{self.REGISTRY_NAME}: {alternative.get("label")!r} is not offered '
				  f'inside its own source {source.path}; nothing placed')
			return False
		debug(f'{self.REGISTRY_NAME}: placing {alternative.get("label")!r} from '
			  f'{alternative.get("contributor")!r} for {orig_op.OPType} at {orig_op.path}')
		if source.isCOMP and not alternative.get('unpack'):
			ok = self._placeComp(orig_op, source)
		else:
			self._placeOpChain(orig_op, [source])
			ok = True
		self.refreshObserved()
		return ok

	# -- alternatives that are only in the store ----------------------------
	#
	# The owner's rule: a package downloaded into the updater's store folder
	# is offered and placed from disk, through the same mechanism. Which
	# operator types a tox answers cannot be read without loading it, so
	# that comes from the cached manifest's alternatives_for (derived at
	# build). Offered = in the manifest AND on disk AND not live in the
	# project. Nothing is fetched here; a place is a place, no install row.

	STORE_CONTRIBUTOR = 'store'
	_STORE_SCAN_TTL = 5.0

	def _storeManifest(self):
		"""The updater's cached manifest, or a test override."""
		override = getattr(self, '_storeManifestOverride', None)
		if override is not None:
			return override
		upd = getattr(op, 'FNS_UPDATER', None)
		if upd is None or not hasattr(upd, 'StoreManifest'):
			return None
		try:
			return upd.StoreManifest()
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: store manifest unreadable: {e}')
			return None

	def _storeFolder(self):
		upd = getattr(op, 'FNS_UPDATER', None)
		if upd is None or not hasattr(upd, 'StoreFolder'):
			return None
		try:
			return upd.StoreFolder()
		except Exception:
			return None

	def RefreshStoreAlternatives(self):
		"""Drop the cached store scan; the next read rescans the folder."""
		self._storeCache = None

	def _storeAlternatives(self):
		"""{optype: [alternative]} for every store tox whose manifest row
		declares alternatives_for and whose package is not live. Cached for
		a few seconds: the node table's decorator reads Alternatives per row
		per cook, and a folder listing per row is not on."""
		cache = getattr(self, '_storeCache', None)
		now = time.time()
		if cache is not None and now - cache[0] < self._STORE_SCAN_TTL:
			return cache[1]
		out = {}
		manifest = self._storeManifest()
		folder = self._storeFolder()
		root = getattr(op, 'FNS', None)
		if manifest and folder and os.path.isdir(folder):
			for row in (manifest.get('packages') or []):
				types = row.get('alternatives_for') or []
				name = str(row.get('name') or '')
				if not types or not name:
					continue
				if root is not None and root.op(name) is not None:
					continue           # live in the project: its own contribution covers it
				tox = '%s/%s.tox' % (folder, name)
				if not os.path.isfile(tox):
					continue           # in the manifest, not yet downloaded: not offered
				entry = {'label': str(row.get('title') or name), 'source': tox,
						 'help': str(row.get('description') or ''),
						 'contributor': self.STORE_CONTRIBUTOR, 'unpack': False,
						 'package': name}
				for optype in types:
					out.setdefault(str(optype), []).append(entry)
		self._storeCache = (now, out)
		return out

	def _placeTox(self, orig_op, path, name=None):
		"""Replace orig_op with a tox loaded from disk, as one node, wired
		through its connectors. loadTox never copies a live subtree, so the
		clone-host crash class does not apply here."""
		if not os.path.isfile(path):
			debug(f'{self.REGISTRY_NAME}: {path} is not on disk any more')
			return False
		_parent = orig_op.parent()
		pos = (orig_op.nodeX, orig_op.nodeY)
		in_conns = self._indexConnections(orig_op, 'inputs', 'outputConnectors')
		out_conns = self._indexConnections(orig_op, 'outputs', 'inputConnectors')
		orig_path = orig_op.path
		ui.undo.startBlock(f'Replacing {orig_path} with {os.path.basename(path)}')
		try:
			orig_op.destroy()
			new = _parent.loadTox(path)
		finally:
			ui.undo.endBlock()
		if new is None:
			return False
		if name:
			try:
				new.name = name
			except Exception:
				pass
		new.nodeX, new.nodeY = pos
		self._restoreToComp(in_conns, 'outputConnectors', new)
		self._restoreToComp(out_conns, 'inputConnectors', new)
		return True

	# -- a tool placed whole ----------------------------------------------

	@staticmethod
	def _indexConnections(orig_op, op_attr, conn_attr):
		"""{neighbour: [connector indices]} wired to orig_op, so the wiring
		can be put back onto whatever replaces it."""
		conns = defaultdict(list)
		for other in set(getattr(orig_op, op_attr)):
			for idx, connector in enumerate(getattr(other, conn_attr)):
				for connection in connector.connections:
					if connection and connection.owner is orig_op:
						conns[other].append(idx)
		return conns

	@staticmethod
	def _restoreToComp(conns, connector_attr, comp):
		"""Re-wire neighbours onto a COMP's connectors (input side uses its
		output connector and vice versa, because a COMP's connectors face
		outward)."""
		invert = 'outputConnectors' if connector_attr == 'inputConnectors' else 'inputConnectors'
		mine = getattr(comp, invert)
		if not mine:
			return
		for other, indices in conns.items():
			for idx in indices:
				try:
					getattr(other, connector_attr)[idx].connect(mine[0])
				except Exception as e:
					debug(f'{comp.name}: could not restore a connection to {other.name}: {e}')

	def _placeComp(self, orig_op, source):
		"""Replace orig_op with a copy of `source` as ONE node, wiring the
		neighbours to its connectors.

		A tool's COMP carries registry hosts, and copying a subtree with an
		enabled clone host crashes TouchDesigner: every host inside has
		cloning disabled and the source's initextonstart is off for the
		duration of the copy, all restored in a finally, on both the source
		and the copy.

		A placed copy is an INSTANCE in the user's network, not a second
		tool: every registry host inside it gets Autoregister off before its
		extensions init, or the copy publishes itself -- a second alternative
		for the same type, and under the same canonical name it steals the
		original's entry (measured: three placed copies of one tool, the
		entry pointing at the last copy)."""
		_parent = orig_op.parent()
		pos = (orig_op.nodeX, orig_op.nodeY)
		in_conns = self._indexConnections(orig_op, 'inputs', 'outputConnectors')
		out_conns = self._indexConnections(orig_op, 'outputs', 'inputConnectors')
		# The copy is the tool, so it carries the tool's name (TD uniquifies
		# on collision), not the name of the stock operator it replaces.
		name = source.name
		orig_path = orig_op.path
		hosts = [c for c in source.findChildren(type=COMP)
				 if c.par['enablecloning'] is not None and bool(c.par.enablecloning.eval())
				 and c.par['clone'] is not None and str(c.par.clone.val).strip()]
		# Registry hosts are children with their OWN initextonstart, so their
		# extensions init during the copy and would register the copy before
		# anything could stop them. Hold their init off across the copy, flag
		# the copies, then let them init idle.
		reg_hosts = [c for c in source.findChildren(type=COMP)
					 if c.par['Autoregister'] is not None and c.par['Regstatus'] is not None
					 and c.par['initextonstart'] is not None]
		host_init = {c.path: bool(c.par.initextonstart.eval()) for c in reg_hosts}
		init_par = source.par['initextonstart']
		prev_init = bool(init_par.eval()) if init_par is not None else None
		new = None
		ui.undo.startBlock(f'Replacing {orig_path} with {source.name}')
		try:
			orig_op.destroy()
			for h in hosts:
				h.par.enablecloning = False
			for c in reg_hosts:
				c.par.initextonstart = False
			if init_par is not None:
				init_par.val = False
			new = _parent.copy(source, name=name)
		finally:
			for h in hosts:
				h.par.enablecloning = True
			for c in reg_hosts:
				c.par.initextonstart = host_init.get(c.path, True)
			if init_par is not None and prev_init is not None:
				init_par.val = prev_init
			if new is not None:
				for h in new.findChildren(type=COMP):
					if h.par['enablecloning'] is not None and h.par['clone'] is not None 							and str(h.par.clone.val).strip():
						h.par.enablecloning = True
					if h.par['Autoregister'] is not None and h.par['Regstatus'] is not None:
						h.par.Autoregister = False      # an instance does not publish
						h.par.Regstatus = 'Idle (placed instance)'   # not the source's copied status
						rel = h.path[len(new.path):]
						if h.par['initextonstart'] is not None:
							h.par.initextonstart = host_init.get(source.path + rel, True)
				np = new.par['initextonstart']
				if np is not None and prev_init is not None:
					np.val = prev_init
			ui.undo.endBlock()
		if new is None:
			return False
		new.nodeX, new.nodeY = pos
		self._restoreToComp(in_conns, 'outputConnectors', new)
		self._restoreToComp(out_conns, 'inputConnectors', new)
		return True

	# -- placeOPchain, ported ---------------------------------------------

	@staticmethod
	def _opFamilies():
		return [fam.__name__ for fam in OP.__subclasses__()]

	def _cleanTemplateTags(self, _parent):
		for _op in _parent.findChildren(tags=list(self._TEMPLATE_TAGS), depth=1):
			for tag in self._TEMPLATE_TAGS:
				if tag in _op.tags:
					_op.tags.remove(tag)

	def _placeOpChain(self, orig_op, template_ops):
		"""Handles single operators, operator chains, docked operators,
		inserting between operators, and restoring relative positions -- all
		at the same time. OpTemplates' placeOPchain, unchanged in behaviour."""
		families = self._opFamilies()

		def index_connections(orig_op, op_attr, conn_attr):
			conns_indexed = defaultdict(list)
			for inOp in set(getattr(orig_op, op_attr)):
				for idx, _connector in enumerate(getattr(inOp, conn_attr)):
					for _connection in _connector.connections:
						if _connection and _connection.owner is orig_op:
							conns_indexed[inOp].append(idx)
			return conns_indexed

		def restore_connections(conns_indexed, connector_attr, new_op):
			to_connect = new_op
			if conns_indexed:
				for _o, indices in conns_indexed.items():
					for connector_idx in indices:
						if new_op.family == 'COMP':
							invert = 'outputConnectors' if connector_attr == 'inputConnectors' else 'inputConnectors'
							to_connect = getattr(new_op, invert)[0]
							if not to_connect:
								return
						getattr(_o, connector_attr)[connector_idx].connect(to_connect)

		def bfs(_o):
			visited, queue, out = {_o}, deque([_o]), []
			while queue:
				_o = queue.popleft()
				if _o:
					out.append(_o)
					for output in _o.outputs:
						if output not in visited:
							visited.add(output)
							queue.append(output)
			return out

		def get_new_root(_parent, orig_type):
			roots = _parent.findChildren(tags=['TEMPLATE_ROOT'], depth=1)
			roots = sorted(roots, key=lambda _o: _o.OPType == orig_type)
			return roots[0] if roots else None

		def new_ops_bfs_sorted(_parent, orig_type):
			root = get_new_root(_parent, orig_type)
			return bfs(root) if root else []

		def get_famconvert(orig_op):
			if orig_op.OPType not in self._FAMILY_CONVERT_TYPES:
				return None
			from_type = next((sub.lower() for sub in families if sub.lower() in orig_op.OPType), None)
			if from_type and hasattr(orig_op.par, from_type):
				return (from_type, getattr(orig_op.par, from_type).val)
			return None

		def set_famconvert(new_op, orig_famconvert):
			if hasattr(new_op.par, orig_famconvert[0]):
				setattr(new_op.par, orig_famconvert[0], orig_famconvert[1])

		template_op = template_ops[0]
		_parent = orig_op.parent()
		op_pos = (orig_op.nodeX, orig_op.nodeY)
		orig_type = orig_op.OPType
		orig_famconvert = get_famconvert(orig_op)
		in_conns_indexed = index_connections(orig_op, 'inputs', 'outputConnectors')
		out_conns_indexed = index_connections(orig_op, 'outputs', 'inputConnectors')
		orig_path = orig_op.path

		orig_op.destroy()
		ui.undo.startBlock(f'Replacing {orig_path} with an alternative')
		try:
			to_clean = []
			if template_op.OPType == 'baseCOMP':
				template_op.allowCooking = False
				ops_to_copy = template_op.findChildren(depth=1)
				if template_op.inputConnectors and (_roots := template_op.inputConnectors[0].inOP.outputs):
					ops_to_copy.remove(template_op.inputConnectors[0].inOP)
					for _o in _roots:
						_o.tags.add('TEMPLATE_IN')
						_o.tags.add('TEMPLATE_ROOT')
						to_clean.append(_o)
				else:
					_root = template_op.findChildren(key=lambda _o: _o.OPType == orig_type and not _o.inputs)
					if _root:
						to_clean.extend(_root)
						_root = _root[0]
					else:
						_root = ops_to_copy[0]
						to_clean.extend(ops_to_copy)
					_root.tags.add('TEMPLATE_ROOT')
				if template_op.outputConnectors and (_outs := template_op.outputConnectors[0].outOP.inputs):
					_outs[0].tags.add('TEMPLATE_OUT')
					to_clean.extend(_outs)
					ops_to_copy.remove(template_op.outputConnectors[0].outOP)
				else:
					to_clean.append(_root)
			else:
				template_op.tags.add('TEMPLATE_ROOT')
				to_clean.append(template_op)
				ops_to_copy = bfs(template_op)
				if orig_famconvert:
					set_famconvert(template_op, orig_famconvert)

			for i, _o in enumerate(ops_to_copy):
				_o.tags.add('TEMPLATE_COPY')
				_o.tags.add('TEMPLATE_IDX_%d' % i)
				to_clean.append(_o)
			# the library's own wiring, by index, so it can be restored after
			# the paste: pasteOPs drops a wire whose op it had to RENAME on a
			# name collision in the target network (measured on box1 -> box2
			# at /, the attributecreate behind it left with no input)
			wires = []
			for i, _o in enumerate(ops_to_copy):
				for k, conn in enumerate(_o.inputConnectors):
					for src_conn in conn.connections:
						if src_conn.owner in ops_to_copy:
							wires.append((ops_to_copy.index(src_conn.owner), src_conn.index, i, k))

			ui.copyOPs(ops_to_copy)
			ui.pasteOPs(_parent, x=op_pos[0], y=op_pos[1])

			pasted = _parent.findChildren(tags=['TEMPLATE_COPY'], depth=1)
			by_idx = {}
			for _o in pasted:
				for tag in list(_o.tags):
					if tag.startswith('TEMPLATE_IDX_'):
						by_idx[int(tag[len('TEMPLATE_IDX_'):])] = _o
						_o.tags.remove(tag)
			for src_i, src_k, dst_i, dst_k in wires:
				s_op, d_op = by_idx.get(src_i), by_idx.get(dst_i)
				if s_op is None or d_op is None:
					continue
				try:
					if not d_op.inputConnectors[dst_k].connections:
						d_op.inputConnectors[dst_k].connect(s_op.outputConnectors[src_k])
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: could not restore a library wire '
						  f'{s_op.name} -> {d_op.name}: {e}')
			# pasteOPs anchors the group's bounding box at (x, y), which puts
			# the leftmost op near the cursor but not on it. Owner's call
			# (2026-09-10): the LEFTMOST operator, the start of the chain,
			# sits exactly under the cursor; the rest lays out to the right.
			anchor = min(pasted, key=lambda o: (o.nodeX, -o.nodeY)) if pasted else None
			if anchor is not None:
				dx, dy = op_pos[0] - anchor.nodeX, op_pos[1] - anchor.nodeY
				if dx or dy:
					for o in pasted:
						o.nodeX += dx
						o.nodeY += dy
			for new_op in pasted:
				new_op.bypass = False
				new_op.allowCooking = True
				new_op.tags.remove('TEMPLATE_COPY')

			if new_in_ops := _parent.findChildren(tags=['TEMPLATE_IN'], depth=1):
				for _o in new_in_ops:
					restore_connections(in_conns_indexed, 'outputConnectors', _o)
					_o.tags.remove('TEMPLATE_IN')
			else:
				_inOP = get_new_root(_parent, orig_type)
				if _inOP is not None:
					restore_connections(in_conns_indexed, 'outputConnectors', _inOP)

			if new_out_ops := _parent.findChildren(tags=['TEMPLATE_OUT'], depth=1):
				_outOP = new_out_ops[0]
				for _o in new_out_ops:
					_o.tags.remove('TEMPLATE_OUT')
			else:
				new_ops = new_ops_bfs_sorted(_parent, orig_type)
				_outOP = new_ops[-1] if new_ops else None

			if _outOP:
				if 'TEMPLATE_ROOT' in _outOP.tags:
					_outOP.tags.remove('TEMPLATE_ROOT')
				restore_connections(out_conns_indexed, 'inputConnectors', _outOP)

			# Every op this pass tagged is in to_clean, on both sides of the
			# copy. OpTemplates only ever cleaned the destination network, so
			# a COMP template's children kept TEMPLATE_ROOT / TEMPLATE_OUT in
			# the LIBRARY -- and a stale TEMPLATE_OUT is what the next
			# placement wires the outputs to. Measured leaked on const_speed
			# the first time this ran (2026-09-10).
			for _o in to_clean:
				if _o is not None and _o.valid:
					for tag in list(_o.tags):
						if tag in self._TEMPLATE_TAGS or tag.startswith('TEMPLATE_IDX_'):
							_o.tags.remove(tag)
			self._cleanTemplateTags(_parent)
		finally:
			ui.undo.endBlock()

	@property
	def Decorators(self):
		"""[(canonical, fn)] label decorators, resolved ONCE.

		The injected node cooks over every operator type in the dialog, so it
		resolves this list per cook and calls the functions per row rather
		than re-resolving contributors hundreds of times.
		"""
		api = self._registryApi()
		if api is not self:
			return api.Decorators
		return list(self._contributions('onDecorateLabel'))

	def DecorateLabel(self, optype, label):
		"""Run every contributor's row decorator over a node-table label."""
		api = self._registryApi()
		if api is not self:
			return api.DecorateLabel(optype, label)
		for name, fn in self._contributions('onDecorateLabel'):
			try:
				replacement = fn(optype, label)
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onDecorateLabel from {name!r}: {e}')
				continue
			if replacement:
				label = str(replacement)
		return self._markAlternatives(optype, label)

	# One marker for every contributor, so a tool that offers itself reads
	# the same in the node table as a template does. ' >>>' = an alternative
	# is live in the project; ' >>' = the only alternatives are toxes in the
	# store, placed from disk. A contributor that still appends ' >>>' itself
	# is not marked twice.
	ALT_MARK_LIVE = ' >>>'
	ALT_MARK_STORE = ' >>'

	def MarkAlternatives(self, optype, label):
		"""Append the alternatives mark to one node-table label.

		The dialog's chain stage resolves contributor decorators once per
		cook and applies them itself, so it never goes through DecorateLabel;
		it calls this per row instead. Alternatives is cached per frame, so a
		cook over every type costs one merge."""
		api = self._registryApi()
		if api is not self:
			return api.MarkAlternatives(optype, label)
		return self._markAlternatives(optype, label)

	def _markAlternatives(self, optype, label):
		alts = self.Alternatives.get(str(optype)) or []
		if not alts:
			return label
		live = any(a.get('contributor') != self.STORE_CONTRIBUTOR for a in alts)
		mark = self.ALT_MARK_LIVE if live else self.ALT_MARK_STORE
		if label.endswith(self.ALT_MARK_LIVE) or label.endswith(self.ALT_MARK_STORE):
			return label
		return label + mark

	@property
	def MenuItems(self):
		"""[(canonical, label)] appended after TD's stock right-click items."""
		api = self._registryApi()
		if api is not self:
			return api.MenuItems
		items = []
		for name, fn in self._contributions('onMenuItems'):
			try:
				labels = fn() or []
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onMenuItems from {name!r}: {e}')
				continue
			if isinstance(labels, str):
				labels = [labels]
			for label in labels:
				items.append((name, str(label)))
		return items

	def InvokeMenuItem(self, index, optype):
		"""Dispatch a right-click menu click (index is already offset past
		TD's stock items) back to the tool that published it."""
		api = self._registryApi()
		if api is not self:
			return api.InvokeMenuItem(index, optype)
		items = self.MenuItems
		try:
			index = int(index)
		except (TypeError, ValueError):
			return False
		if not 0 <= index < len(items):
			return False
		canonical, label = items[index]
		module = self._callbackModule(self.stored['PaneRegistry'].get(canonical))
		fn = getattr(module, 'onMenuItem', None) if module is not None else None
		if not callable(fn):
			debug(f'{self.REGISTRY_NAME}: {canonical!r} published {label!r} but has no onMenuItem')
			return False
		try:
			fn(label, optype)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: onMenuItem {label!r} from {canonical!r}: {e}')
			return False
		return True

	# --- public API ---

	def RegisterContributor(self, comp, canonical_name, callback=None, order=None,
							display=True, source_registry=None, help_url=None,
							panel=None, panel_anchor=None):
		"""Publish a COMP's op-menu contributions under canonical_name.

		`panel` (+ `panel_anchor`) is the zero-code path: a tool that only
		wants a panel in the dialog declares it on the host's Registration
		page and needs no callbacks DAT at all. It is ADDITIVE with
		onPanels() -- declaring both injects both -- so a tool can pin one
		panel by parameter and compute others in code.
		"""
		self._altCache = None   # a contributor changed: the per-frame Alternatives merge is stale
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterContributor(
					comp, canonical_name, callback=callback, order=order,
					display=display, source_registry=source_registry, help_url=help_url,
					panel=panel, panel_anchor=panel_anchor)
			debug(f'{self.REGISTRY_NAME}: RegisterContributor ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		err = self._validateContributor(comp, callback, panel)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterContributor({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': comp.path,
			'panel_id': int(comp.id),
			'display': '1' if display else '0',
		}
		norm_order = self._normalizeMenuOrder(order)
		if norm_order is not None:
			entry['menu_order'] = norm_order
		if help_url:
			entry['help_url'] = str(help_url)
		if callback is not None:
			entry['callback_path'] = callback.path
			entry['callback_id'] = int(callback.id)
		# parameter-declared panel: stored on the entry so the global can apply
		# it without reaching back into the host's pars
		if panel is not None and getattr(panel, 'valid', False):
			entry['decl_panel_path'] = panel.path
			entry['decl_panel_id'] = int(panel.id)
			entry['decl_panel_anchor'] = str(panel_anchor or self.DEFAULT_PANEL_ANCHOR)
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		self.stored['PaneRegistry'][canonical_name] = entry
		self.fnsLog(f'{self.REGISTRY_NAME}: registered contributor "{canonical_name}" ({comp.path})')
		# The WHOLE surface, whether the dialog is up or not. This used to
		# rebuild only the right-click menu when the dialog already existed
		# and leave the full sync to the deferred path, which is the boot
		# case -- so a tool installed into a running session registered
		# fine and never got its chain stages or panels until a restart or
		# a hand Resync (FNS_OpMenuMods on a fresh install, 2026-09-14:
		# hosts "Registered", no script_inject, no IOFilter stage). The
		# sync is idempotent and cheap; a second pass a few frames later
		# catches a contributor whose own ops were still being built when
		# its host registered.
		if not self._pane_sync_queued:
			self._syncSurface()
		if self._menuReady():
			run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface()",
				self.ownerComp, delayFrames=10, delayRef=op.TDResources)

	def UnregisterContributor(self, canonical_name):
		self._altCache = None   # a contributor changed: the per-frame Alternatives merge is stale
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterContributor(canonical_name)
			debug(f'{self.REGISTRY_NAME}: UnregisterContributor ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		self.stored['PaneRegistry'].pop(canonical_name, None)
		self.fnsLog(f'{self.REGISTRY_NAME}: unregistered contributor "{canonical_name}"')
		# the whole surface, so the leaver's chain stages and panels go too
		if self._menuReady():
			self._syncSurface()

	# RegistryBase healing calls self.UnregisterPanel(name); alias it.
	def UnregisterPanel(self, canonical_name):
		return self.UnregisterContributor(canonical_name)

	def SetContributorOrder(self, canonical_name, order):
		"""Manager API: reorder a contributor's menu items."""
		api = self._registryApi()
		if api is not self:
			return api.SetContributorOrder(canonical_name, order)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		norm = self._normalizeMenuOrder(order)
		if norm is None:
			info.pop('menu_order', None)
		else:
			info['menu_order'] = norm
		self._writeBackHostPar(info, 'Menuorder', -1 if norm is None else norm)
		self._syncSurface()
		return True

	def SetContributorDisplay(self, canonical_name, visible):
		"""Manager API: enable or disable a tool's contributions."""
		api = self._registryApi()
		if api is not self:
			return api.SetContributorDisplay(canonical_name, visible)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		info['display'] = '1' if visible else '0'
		self._writeBackHostPar(info, 'Displayed', 1 if visible else 0)
		self._syncSurface()
		return True

	@property
	def Contributors(self):
		"""Manager API: snapshot of all registered contributor entries."""
		api = self._registryApi()
		if api is not self:
			return api.Contributors
		return {k: dict(v) for k, v in self.stored['PaneRegistry'].items()}

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

	def _hostPanelDeclaration(self):
		"""The host's parameter-declared panel: (comp, anchor) or (None, None).

		The zero-code contribution path -- a tool that only wants a panel in
		the dialog sets this and needs no callbacks DAT.
		"""
		par = getattr(self.ownerComp.par, 'Panel', None)
		comp = par.eval() if par is not None else None
		if comp is None or not getattr(comp, 'valid', False):
			return None, None
		anchor_par = getattr(self.ownerComp.par, 'Panelanchor', None)
		anchor = str(anchor_par.eval()).strip() if anchor_par is not None else ''
		return comp, (anchor or self.DEFAULT_PANEL_ANCHOR)

	def _validateContributor(self, comp, callback, panel=None):
		if comp is None:
			return 'No COMP selected'
		if comp.family != 'COMP':
			return f'{comp.path} is not a COMP'
		# a tool may contribute via a callbacks DAT, a declared Panel, or both
		if callback is None and panel is None:
			return 'Nothing to contribute (set a Callback DAT and/or a Panel)'
		if callback is not None and not callback.isDAT:
			return f'{callback.path} is not a DAT'
		if panel is not None and not getattr(panel, 'isPanel', False):
			return f'{panel.path} is not a Panel COMP (isPanel=False)'
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

	# --- host registration (Registration page), op-menu flavor ---

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
		callback = self._hostCallbackDat()
		panel, panel_anchor = self._hostPanelDeclaration()
		err = self._validateContributor(comp, callback, panel) or (
			None if canonical else 'empty canonical name')
		if err:
			if not force:
				self._clearHostRegistration()
			self._setRegStatus(f'Error: {err}')
			return
		prev = self.stored['HostCanonical']
		api = self._registryApi()
		if prev and prev != canonical:
			self._unregisterOwnedMenuName(prev, api=api)
		api.RegisterContributor(
			comp, canonical,
			callback=callback,
			order=self._hostMenuOrder(),
			display=self._parBool('Displayed', True),
			source_registry=self.ownerComp,
			help_url=self._hostHelpUrl(comp),
			panel=panel, panel_anchor=panel_anchor,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {comp.path}')
		self._ensureToolRegistryPage()

	def _hostHelpUrl(self, comp):
		"""The tool's self-reported wiki page: the host's Helpurl par when
		set, else auto-discovered from the registered COMP or its parent --
		either a docsHelper COMP (its Url par) or a Url/Wikipage custom par
		on the COMP itself (both pre-registry self-reporting conventions)."""
		if hasattr(self.ownerComp.par, 'Helpurl'):
			u = str(self.ownerComp.par.Helpurl.eval()).strip()
			if u:
				return u
		for holder in (comp, comp.parent() if comp else None):
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

	# --- callbacks DAT bootstrap ---

	def CreateCallbacks(self):
		"""Spawn an `opmenu_callbacks` DAT into this host's tool and point
		the host's Callback parameter at it.

		The whole setup for a new publisher: pulse this, fill in the hooks
		you want, done. Idempotent -- if the tool already has one it is
		adopted (never overwritten), so pulsing again just repairs a
		Callback reference that came unset.
		"""
		tool = self._hostComp()
		if tool is None:
			debug(f'{self.REGISTRY_NAME}: CreateCallbacks -- no tool COMP (check the Comp par)')
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
			# The template is bound to the registry's own source file. A copy
			# inherits that binding, so without this every tool's callbacks
			# would read from -- and save over -- the one shared template.
			for par_name in ('file', 'syncfile', 'loadonstart', 'write'):
				p = getattr(dat.par, par_name, None)
				if p is not None:
					try:
						p.mode = ParMode.CONSTANT
						p.val = '' if par_name == 'file' else False
					except Exception:
						pass
			# nor should it inherit the template's tracker identity
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

	def onParDisplayed(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParCallback(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()
