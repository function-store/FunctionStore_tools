

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

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
	"""

	SHORTCUT = 'OPMENUREGISTRY'
	EXT_NAME = 'OpMenuRegistryExt'
	REGISTRY_NAME = 'OpMenuRegistry'

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
		# Hosts must not keep a parallel table; the global owns all entries.
		if not self._is_sys_global():
			self.stored['PaneRegistry'].clear()

	def _syncSurface(self, attempts=40):
		"""Idempotent: splice contributed stages and panels into the dialog and
		rebuild the right-click menu from registered entries. Defers until
		TD's Insert-Operator dialog exists."""
		self._pane_sync_queued = False
		if self._menuReady():
			self._syncChain()
			self._syncPanels()
			self._syncPopMenu()
			return
		if attempts <= 0:
			debug(f'{self.REGISTRY_NAME}: {self.MENU_PATH} never became available, '
				  f'skipping sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run(f"args[0].valid and args[0].ext.{self.EXT_NAME}._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	def _healRegistryEntries(self):
		"""Base healing plus surface repair -- this is what makes a LATE
		dialog work and what restores the chain node if TD rebuilt it."""
		super()._healRegistryEntries()
		if not self._is_sys_global() or not self._menuReady():
			return
		self._reapplyAutoregisterHosts()
		self._syncChain()
		self._syncPanels()
		self._syncPopMenu()
		self._healHostClones()

	# Boot window: how many heal ticks re-sweep for unpublished hosts.
	# /sys does NOT save with the project, so on every open (and after any
	# extension reinit wave) the global comes up empty while hosts believe
	# they are registered -- their Autoregister ran at ext init, which can
	# predate the global being ready. The sweep is bounded because it is a
	# project-wide search: it fixes the boot window, then stops.
	BOOT_SWEEPS = 6

	def _reapplyAutoregisterHosts(self):
		"""Ask live Autoregister hosts that the global has no entry for to
		republish. Without this a cold boot leaves the dialog unaugmented
		until someone touches a Register pulse."""
		if not self._is_sys_global():
			return
		if getattr(self, '_boot_sweeps_left', None) is None:
			self._boot_sweeps_left = self.BOOT_SWEEPS
		if self._boot_sweeps_left <= 0:
			return
		self._boot_sweeps_left -= 1
		published = set()
		for info in self.stored['PaneRegistry'].values():
			src = self._resolveSourceRegistry(info)
			if src is not None:
				published.add(src.path)
		try:
			# NO depth argument: TD's findChildren depth is an EXACT depth,
			# not a maximum -- passing one silently matches nothing.
			candidates = op('/').findChildren(name=self.REGISTRY_NAME)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: host sweep: {e}')
			return
		for host in candidates:
			if host is self.ownerComp or host.path in published:
				continue
			path = host.path
			if path.startswith('/sys') or path.startswith('/ui'):
				continue
			if not host.valid or not host.extensionsReady:
				continue
			ext = getattr(host.ext, self.EXT_NAME, None)
			if ext is None or not ext._isAutoRegister():
				continue
			try:
				ext._applyHostRegistration()
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: re-apply {path}: {e}')

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
	CLONE_EXPR = "op.FNS_OPMOD.op('OpMenuRegistry') if hasattr(op, 'FNS_OPMOD') else None"

	def _healHostClones(self):
		"""Re-assert in-project cloning on tool hosts. Release flows scrub the
		clone par on shipped copies (pre_release); if a release tool scrubbed
		the LIVE host instead of a staged copy, this restores it."""
		package = getattr(op, 'FNS_OPMOD', None)
		master = package.op('OpMenuRegistry') if package is not None else None
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
		for o in list(menu.children):
			if self.PANEL_TAG in o.tags and o.name not in wanted:
				o.destroy()
		for name, (canonical, src, anchor_name) in wanted.items():
			panel = menu.op(name)
			if self._isStale(panel, src, self.PANEL_TAG):
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
		return label

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
		if self._menuReady():
			self._syncPopMenu()
		elif not self._pane_sync_queued:
			self._syncSurface()

	def UnregisterContributor(self, canonical_name):
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterContributor(canonical_name)
			debug(f'{self.REGISTRY_NAME}: UnregisterContributor ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		self.stored['PaneRegistry'].pop(canonical_name, None)
		if self._menuReady():
			self._syncPopMenu()

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
