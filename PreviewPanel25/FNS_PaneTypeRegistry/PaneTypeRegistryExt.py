

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

import enum
import TDFunctions

RegistryBase = mod('RegistryBase').RegistryBase

class PaneActions(enum.Enum):
	NONE = 'NONE'
	OWNER = 'OWNER'

class PaneTypeRegistryExt(RegistryBase):
	EXT_NAME = 'PaneTypeRegistryExt'
	SHORTCUT = 'FNS_PANETYPEREGISTRY'
	REGISTRY_NAME = 'FNS_PaneTypeRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Pt'
	TOOL_PAGE_LABEL = 'Pane Menu'
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus', 'Menuorder')

	PANE_TYPE_NAMES = [
		'PANEL', 'NETWORKEDITOR', 'GEOMETRYVIEWER', 'TOPVIEWER', 'CHOPVIEWER',
		'ANIMATIONEDITOR', 'PARAMETERS', 'TEXTPORT', 'OPBROWSER',
	]
	PANE_TYPE_LABELS = [
		'Panel', 'Network Editor', 'Geometry Viewer', 'TOP Viewer', 'CHOP Viewer',
		'Animation Editor', 'Parameters', 'Textport', 'OP Browser',
	]
	# Legacy Action menu values (pre-0.0.6). Mapped in _entryFlags().
	BUILTIN_LABEL_TO_TYPE = {
		'Network Editor': 'NETWORKEDITOR',
		'Panel': 'PANEL',
		'Geometry Viewer': 'GEOMETRYVIEWER',
		'TOP Viewer': 'TOPVIEWER',
		'CHOP Viewer': 'CHOPVIEWER',
		'Animation Editor': 'ANIMATIONEDITOR',
		'Parameters': 'PARAMETERS',
		'Textport and DATs': 'TEXTPORT',
		'Textport': 'TEXTPORT',
		'OP Browser': 'OPBROWSER',
	}


	# Builtin panebar rows we inject (missing from TD's default menu).
	# (menu label, insert after this label)
	INJECTED_BUILTIN_MENU = [
		('OP Browser', 'Textport and DATs'),
	]

	ACTION_NAMES = ['OWNER', 'NONE']
	ACTION_LABELS = ['Change Owner + Type', 'None (no type change)']

	CALLBACK_DAT_NAME = 'panetype_callbacks'
	CALLBACK_TEMPLATE = 'callbacks_template'
	CALLBACK_SKELETON = '''"""PaneTypeRegistry recall callbacks.

Called when a registered panebar entry is selected.
"""


def onPaneRecall(ctx):
	"""Run custom logic after built-in recall actions.

	ctx keys:
		pane       - ui.Pane (reassigned after changeType if that ran)
		pane_comp  - panebar UI COMP that triggered the selection
		owner      - registered COMP, or None
		canonical  - panebar menu name
		info       - registry entry dict
		registry   - PaneTypeRegistryExt instance

	Built-in flags (Set Owner / Change Type / Maximize / Tear Away / Float) run first;
	use this for panel-specific behavior (Open, focus, etc.).
	"""
	# owner = ctx.get('owner')
	# pane = ctx.get('pane')
	# if owner is not None and hasattr(owner, 'Open'):
	#     owner.Open()
	pass
'''

	PANETYPE_MENUSOURCE_EXPR = (
		"me.ext.PaneTypeRegistryExt.PanetypeMenuSource "
		"if me.extensionsReady and hasattr(me.ext, 'PaneTypeRegistryExt') "
		"else tdu.ParMenu([])"
	)

	def _preInit(self):
		# DEFERRED, never inline. _preInit runs DURING extension construction;
		# touching the Panetype parameter here is what re-entered init and
		# killed the process (see _ensurePanetypeMenu). One frame later the
		# extension exists and the same work is ordinary.
		run("args[0].valid and args[0].extensionsReady and "
			"args[0].ext.PaneTypeRegistryExt._ensurePanetypeMenu()",
			self.ownerComp, delayFrames=1, delayRef=op.TDResources)

	@property
	def PanetypeMenuSource(self):
		"""MenuSource for the Panetype parameter.

		KEPT for back-compat only: older copies/toxes may still carry the
		menuSource expression that reads this. Nothing assigns that
		expression any more -- see _ensurePanetypeMenu.
		"""
		return tdu.ParMenu(self.PANE_TYPE_NAMES, self.PANE_TYPE_LABELS)

	@property
	def ActionMenuSource(self):
		"""Legacy MenuSource (Action parameter removed in 0.0.6)."""
		return tdu.ParMenu(self.ACTION_NAMES, self.ACTION_LABELS)

	def _ensurePanetypeMenu(self):
		"""Populate the Panetype menu WITHOUT a menuSource expression.

		This used to assign PANETYPE_MENUSOURCE_EXPR -- a menuSource that read
		`me.ext.PaneTypeRegistryExt.PanetypeMenuSource`, i.e. a parameter whose
		menu was computed by this very extension -- and it was assigned from
		_preInit, DURING that extension's construction. Evaluating it mid-init
		re-entered extension initialization (-> _preInit -> reassign ->
		evaluate -> ...) until the stack blew and took the whole TD process
		down with no traceback. `me.extensionsReady` did not reliably stop it.
		It looked intermittent only because the old setter compared before
		writing, so it fired just when something else had changed the
		menuSource first (clone sync, ext .py reload).

		The pane-type list is static, so the menu is set directly and nothing
		calls back into the extension. Runs deferred (see _preInit), and also
		CLEARS any inherited menuSource, so a copy or tox still carrying the
		old expression heals itself instead of crashing on its next reinit.
		"""
		par = getattr(self.ownerComp.par, 'Panetype', None)
		if par is None:
			return
		try:
			if str(getattr(par, 'menuSource', '') or ''):
				par.menuSource = None
			if list(par.menuNames) != list(self.PANE_TYPE_NAMES):
				par.menuNames = list(self.PANE_TYPE_NAMES)
			if list(par.menuLabels) != list(self.PANE_TYPE_LABELS):
				par.menuLabels = list(self.PANE_TYPE_LABELS)
		except Exception as e:
			debug('PaneTypeRegistry: Panetype menu: ' + str(e))

	# --- host auto-registration (Registration page) ---


	def _ensureSelectionExecuteRole(self):
		"""Only the /sys global registry may watch panebar selection DATs.

		Host / shipped copies keep datexec1 as a template (bypassed). They publish
		into the global registry and must not call onPaneTypeSelected themselves.
		"""
		dx = self.ownerComp.op('datexec1')
		if self._is_sys_global():
			if dx is not None:
				dx.bypass = False
				if hasattr(dx.par, 'active'):
					dx.par.active = True
			return

		if dx is not None:
			dx.bypass = True
		# Hosts must not keep a parallel menu table that selection could recall.
		try:
			self.stored['PaneRegistry'].clear()
		except Exception:
			pass

	def _validateHostForPaneType(self, host, panetype):
		"""Validate host against selected pane type. Returns error string or None.

		pane.owner always requires a COMP. PANEL additionally requires isPanel
		(containerCOMP / widget / other Panel Components).
		"""
		if host is None:
			return 'No COMP selected'
		if not getattr(host, 'isCOMP', False):
			return f'{host.path} is not a COMP (pane.owner requires a COMP)'

		pt = (panetype or '').upper()
		if pt == 'PANEL':
			if not getattr(host, 'isPanel', False):
				return (
					f'{host.path} is not a Panel COMP (isPanel=False). '
					'PANEL requires a container/widget Panel COMP.'
				)
		# NETWORKEDITOR, TOPVIEWER, CHOPVIEWER, GEOMETRYVIEWER,
		# ANIMATIONEDITOR, PARAMETERS, TEXTPORT, OPBROWSER: any COMP.
		return None

	def CreateCallbacks(self):
		"""Deploy a callbacks DAT skeleton into the TOOL and assign Callback.

		The DAT lives beside the host, in the registered COMP -- NOT inside
		the host. Two reasons: hosts are clones of the master, so anything
		inside one is replaced on the next clone sync (custom recall logic
		would silently vanish); and the behaviour belongs to the tool that
		owns it, travelling in that tool's tox.
		"""
		tool = self._hostComp() or self.ownerComp
		existing = tool.op(self.CALLBACK_DAT_NAME)
		if existing is None:
			template = self.ownerComp.op(self.CALLBACK_TEMPLATE)
			if template is not None:
				cb = tool.copy(template, name=self.CALLBACK_DAT_NAME)
				# The template is bound to this package's source file. A copy
				# inherits that binding, so without this every tool's
				# callbacks would read from -- and save over -- the one
				# shared template.
				for par_name in ('file', 'syncfile', 'loadonstart', 'write'):
					p = getattr(cb.par, par_name, None)
					if p is not None:
						try:
							p.mode = ParMode.CONSTANT
							p.val = '' if par_name == 'file' else False
						except Exception:
							pass
			else:
				# shipped copies may have had the template scrubbed
				cb = tool.create(textDAT, self.CALLBACK_DAT_NAME)
				cb.text = self.CALLBACK_SKELETON
			cb.nodeX = self.ownerComp.nodeX + self.ownerComp.nodeWidth + 200
			cb.nodeY = self.ownerComp.nodeY
		else:
			cb = existing
			if not str(cb.text or '').strip():
				cb.text = self.CALLBACK_SKELETON
		# a copy that came from a clone must not keep the master's identity
		for tag in ('FNS_externalized', 'py', 'tdn', 'pi_suspect'):
			if tag in cb.tags:
				cb.tags.remove(tag)
		if hasattr(self.ownerComp.par, 'Callback'):
			self.ownerComp.par.Callback = cb
		self._setRegStatus('Callback ready: ' + cb.path)
		if self._isAutoRegister():
			self._applyHostRegistration()
		return cb


	def onParViewreadme(self, _par=None):
		"""Pulse: build README annotate and open the md/scroll panel viewer."""
		# CustomParHelper uses a class-level EXT_SELF — always resolve from the pulsed par.
		owner = _par.owner if _par is not None else self.ownerComp
		if owner is None or not owner.valid:
			owner = self.ownerComp
		md = owner.op('md')
		if md is None:
			debug('PaneTypeRegistry: md viewer COMP missing on ' + owner.path)
			return
		ann = owner.op('annotate1')
		if ann is not None and hasattr(md.par, 'Annotateop'):
			md.par.Annotateop = ann
		if md.extensionsReady and hasattr(md.ext, 'MdAnnotateOp'):
			md.ext.MdAnnotateOp.Build()
		elif hasattr(md.par, 'Build'):
			md.par.Build.pulse()
		else:
			debug('PaneTypeRegistry: md viewer has no Build API')
			return
		scroll = md.op('scroll')
		if scroll is None:
			debug('PaneTypeRegistry: md/scroll panel missing on ' + md.path)
			return
		try:
			scroll.openViewer()
		except Exception as e:
			debug('PaneTypeRegistry: openViewer failed: ' + str(e))


	def onParAutoregister(self, _par, _val, _prev):
		self._hostExtFromPar(_par)._applyHostRegistration()

	def onParRegister(self, _par):
		self._hostExtFromPar(_par)._applyHostRegistration(force=True)

	def onParMenuorder(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParCanonicalname(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParPanetype(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParComp(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParPanel(self, _par, _val, _prev):
		# Back-compat if an older Panel parameter still exists.
		self.onParComp(_par, _val, _prev)

	def _onParRecallSetting(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParSetowner(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParChangetype(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParMaximize(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParTearaway(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParFloat(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParOpenparameters(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParCallback(self, _par, _val, _prev):
		self._onParRecallSetting(_par, _val, _prev)

	def onParCreatecallbacks(self, _par):
		self._hostExtFromPar(_par).CreateCallbacks()

	@property
	def _panebar(self):
		# resolved lazily -- does not exist yet while the project is loading
		return op('/ui/panes/panebar')

	@property
	def _default_pane(self):
		# resolved lazily -- does not exist yet while the project is loading
		return op('/ui/dialogs/panebar/panebar_default')

	@property
	def panes(self):
		panebar = self._panebar
		default = self._default_pane
		# note: list.extend() returns None, use + instead
		found = panebar.ops('pane*') if panebar else []
		return found + ([default] if default else [])

	def _uiReady(self):
		return self._panebar is not None and self._default_pane is not None

	def _syncSurface(self, attempts=40):
		# Idempotent: clears our injected rows and re-injects everything
		# registered. Defers itself until TD's pane UI exists -- it does
		# not exist yet while initextonstart runs us during project load.
		self._pane_sync_queued = False
		if self._uiReady():
			self._ensureDropdownLeftClickOnly()
			self._clearPanes()
			self._injectPanes()
			self._ensureInjectedBuiltinMenuRows()
			return
		if attempts <= 0:
			debug(f'PaneTypeRegistry: pane UI never became available, skipping pane sync ({self.ownerComp.path})')
			return
		self._pane_sync_queued = True
		run("args[0].valid and args[0].ext.PaneTypeRegistryExt._syncSurface(args[1])",
			self.ownerComp, attempts - 1, delayFrames=30, delayRef=op.TDResources)

	def _normalize_action(self, value):
		# storage must hold plain strings: TD pickles storage into the .toe
		# on save, and enum members defined in a DAT module fail pickle's
		# identity check once the extension reinits (new class object)
		name = getattr(value, 'name', value)
		try:
			return PaneActions[str(name).upper()].name
		except KeyError:
			return PaneActions.OWNER.name

	def _sanitizeStoredRegistry(self):
		# self-heal entries that stored PaneActions members (pre-0.0.4)
		for info in self.stored['PaneRegistry'].values():
			try:
				action = info.get('action')
			except AttributeError:
				continue
			normalized = self._normalize_action(action)
			if action != normalized:
				info['action'] = normalized

	def RegisterPanel(self, panel_op, canonical_name, pane_type=None, action=None,
					 set_owner=None, change_type=None, maximize=False,
					 tear_away=False, float_pane=False, open_parameters=False,
					 callback=None, source_registry=None, menu_order=None):
		"""Register a COMP for the panebar menu.

		Non-global (host / shipped) copies always forward to the /sys global
		registry so publishers use the installed menu and recall logic.
		Recall behavior uses orthogonal flags plus an optional callback DAT
		with onPaneRecall(ctx). Legacy action=OWNER|NONE still maps when flags omitted.

		menu_order: optional int sort wish among registered entries.
		  None or < 0 → append (default, same as before).
		  0, 1, 2, … → lower values appear earlier among custom rows.
		"""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterPanel(
					panel_op, canonical_name,
					pane_type=pane_type, action=action,
					set_owner=set_owner, change_type=change_type,
					maximize=maximize, tear_away=tear_away,
					float_pane=float_pane, open_parameters=open_parameters,
					callback=callback, source_registry=source_registry,
					menu_order=menu_order,
				)
			debug(
				'PaneTypeRegistry: RegisterPanel ignored on '
				+ self.ownerComp.path
				+ ' — no global /sys registry ready'
			)
			return

		flags = self._flagsFromArgs(
			action=action,
			set_owner=set_owner,
			change_type=change_type,
			maximize=maximize,
			tear_away=tear_away,
			float_pane=float_pane,
			open_parameters=open_parameters,
		)
		entry = {
			'panel_path': panel_op.path,
			'panel_id': int(panel_op.id),
			'pane_type': pane_type or 'PANEL',
			'set_owner': flags['set_owner'],
			'change_type': flags['change_type'],
			'maximize': flags['maximize'],
			'tear_away': flags['tear_away'],
			'float': flags['float'],
			'open_parameters': flags['open_parameters'],
			'action': 'OWNER' if (flags['set_owner'] and flags['change_type']) else (
				'NONE' if flags['set_owner'] else 'OWNER'
			),
		}
		order = self._normalizeMenuOrder(menu_order)
		if order is not None:
			entry['menu_order'] = order
		if callback is not None:
			entry['callback_path'] = callback.path
			entry['callback_id'] = int(callback.id)
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		self.stored['PaneRegistry'][canonical_name] = entry
		if self._uiReady():
			self._resyncRegisteredMenuRows()
		elif not self._pane_sync_queued:
			self._syncSurface()


	def _flagsFromArgs(self, action=None, set_owner=None, change_type=None,
					  maximize=False, tear_away=False, float_pane=False, open_parameters=False):
		if set_owner is None and change_type is None and action is not None:
			normalized = self._normalize_action(action)
			set_owner = True
			change_type = normalized != PaneActions.NONE.name
		if set_owner is None:
			set_owner = True
		if change_type is None:
			change_type = True
		return {
			'set_owner': bool(set_owner),
			'change_type': bool(change_type),
			'maximize': bool(maximize),
			'tear_away': bool(tear_away),
			'float': bool(float_pane),
			'open_parameters': bool(open_parameters),
		}

	def _entryFlags(self, info):
		"""Read recall flags from a stored entry, including legacy action."""
		if info is None:
			return self._flagsFromArgs()
		has_new = any(k in info for k in (
			'set_owner', 'change_type', 'maximize', 'float', 'tear_away', 'open_parameters', 'floating_copy'
		))
		if has_new:
			if 'tear_away' in info:
				tear_away = bool(info.get('tear_away', False))
				float_pane = bool(info.get('float', False))
			elif 'floating_copy' in info:
				tear_away = bool(info.get('floating_copy', False))
				float_pane = bool(info.get('float', False))
			elif 'float' in info:
				# Very old float flag meant tearAway.
				tear_away = bool(info.get('float', False))
				float_pane = False
			else:
				tear_away = False
				float_pane = bool(info.get('float', False))
			return {
				'set_owner': bool(info.get('set_owner', True)),
				'change_type': bool(info.get('change_type', True)),
				'maximize': bool(info.get('maximize', False)),
				'tear_away': tear_away,
				'float': float_pane,
				'open_parameters': bool(info.get('open_parameters', False)),
			}
		return self._flagsFromArgs(action=info.get('action'))

	def UnregisterPanel(self, canonical_name):
		"""Remove a panebar menu entry.

		Non-global copies forward to /sys so hosts never own the menu table.
		"""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterPanel(canonical_name)
			debug(
				'PaneTypeRegistry: UnregisterPanel ignored on '
				+ self.ownerComp.path
				+ ' — no global /sys registry ready'
			)
			return

		if canonical_name in self.stored['PaneRegistry']:
			del self.stored['PaneRegistry'][canonical_name]
		self._removeFromAllPaneTables(canonical_name)


	def _ensureDropdownLeftClickOnly(self, pane=None):
		"""Force panetype dropdown scripts to left-click cell select only.

		Default TD uses cellselectid, which also fires on right-click.
		celllselectid (triple-l) is left-only, freeing right-click for a menu.
		Applies to /ui/panes/panebar/pane* and panebar_default.
		"""
		targets = [pane] if pane is not None else self.panes
		for p in targets:
			if p is None:
				continue
			script = p.op('panetype/dropdown/script')
			if script is not None and hasattr(script.par, 'panelvalue'):
				if script.par.panelvalue.eval() != 'celllselectid':
					script.par.panelvalue = 'celllselectid'
			self._ensureDropdownRightClickHook(p)

	def _ensureDropdownRightClickHook(self, pane):
		"""Copy template rclick_panereg into the panetype dropdown and activate it."""
		if pane is None:
			return
		dropdown = pane.op('panetype/dropdown')
		if dropdown is None:
			return

		template = self.ownerComp.op('rclick_panereg')
		if template is None:
			return

		pe = dropdown.op('rclick_panereg')
		node_x = node_y = None
		node_w = template.nodeWidth or 160
		node_h = template.nodeHeight or 80
		if pe is not None:
			node_x, node_y = pe.nodeX, pe.nodeY
			node_w, node_h = pe.nodeWidth, pe.nodeHeight
			pe.destroy()

		pe = dropdown.copy(template)
		if pe.name != 'rclick_panereg':
			pe.name = 'rclick_panereg'

		if node_x is None:
			script = dropdown.op('script')
			if script is not None:
				node_x = script.nodeX + script.nodeWidth + 200
				node_y = script.nodeY
			else:
				node_x, node_y = 200, 0

		pe.nodeX = node_x
		pe.nodeY = node_y
		pe.nodeWidth = node_w
		pe.nodeHeight = node_h

		# Template lives outside the dropdown, so panels/'list/list' often won't
		# resolve there and can arrive blank after copy from /sys. Re-assert the
		# relative wiring that only makes sense once parent() is the dropdown.
		pe.par.fromop.expr = 'parent()'
		if hasattr(pe.par, 'panels'):
			pe.par.panels = 'list/list'
		if hasattr(pe.par, 'panel'):
			pe.par.panel = 'list/list'

		# Template stays bypassed in the registry; panebar deploys must run.
		pe.bypass = False
		pe.cloneImmune = True
		pe.par.active = True


	def _ensureInjectedBuiltinMenuRows(self):
		"""Insert hidden-but-supported PaneTypes into panebar menus.

		TD omits some valid PaneType values from the default panebar table
		(e.g. OPBROWSER). We add those labels after a known builtin row.
		Left-click is handled in onPaneTypeSelected via changeType().
		"""
		if not self._is_sys_global():
			return
		for pane in self.panes:
			for label, after_label in self.INJECTED_BUILTIN_MENU:
				self._ensureInjectedBuiltinMenuRow(pane, label, after_label)

	def _ensureInjectedBuiltinMenuRow(self, pane, label, after_label):
		table = pane.op('table1') if pane is not None else None
		if table is None:
			return
		names = list(table.col(0, val=True))
		after_idx = names.index(after_label) if after_label in names else None
		if label in names:
			cur = names.index(label)
			if after_idx is not None and cur == after_idx + 1:
				return
			table.deleteRow(label)
			names = list(table.col(0, val=True))
			after_idx = names.index(after_label) if after_label in names else None
		row = [label, '', '']
		if after_idx is not None:
			table.insertRow(row, after_idx + 1)
		else:
			table.appendRow(row)

	def _injectPane(self, canonical_name):
		panes = self.panes
		for _pane in panes:
			self._ensureDropdownLeftClickOnly(_pane)
			self._addToPaneTable(_pane, canonical_name)

	def _registeredNamesInMenuOrder(self):
		"""Registered menu names: ordered wishes first, then unordered (stable)."""
		ordered = []
		unordered = []
		for name, info in self.stored['PaneRegistry'].items():
			try:
				raw = info.get('menu_order', None)
			except AttributeError:
				raw = None
			order = self._normalizeMenuOrder(raw)
			if order is None:
				unordered.append(name)
			else:
				ordered.append((order, name))
		ordered.sort(key=lambda item: (item[0], item[1].lower()))
		return [name for _order, name in ordered] + unordered

	def _resyncRegisteredMenuRows(self):
		"""Remove and re-add all registered rows in menu_order wish order."""
		if not self._uiReady():
			return
		self._clearPanes()
		self._injectPanes()
		if hasattr(self, '_ensureInjectedBuiltinMenuRows'):
			self._ensureInjectedBuiltinMenuRows()

	def _injectPanes(self):
		for canonical_name in self._registeredNamesInMenuOrder():
			self._injectPane(canonical_name)


	def _addToPaneTable(self, pane, canonical_name):
		table = pane.op('table1')
		if not table:
			debug(f'No table found for pane: {pane.path}')
			return
		for _name in table.col(0, val=True):
			if _name == canonical_name:
				return
		table.appendRow([canonical_name])

	def _removeFromAllPaneTables(self, canonical_name):
		panes = self.panes
		for _pane in panes:
			self._removeFromPaneTable(_pane, canonical_name)

	def _removeFromPaneTable(self, pane, canonical_name):
		table = pane.op('table1')
		if not table:
			debug(f'No table found for pane: {pane.path}')
			return
		if table.row(canonical_name) is not None:
			table.deleteRow(canonical_name)

	def _clearPanes(self):
		# Only remove rows we manage (registered pane types) -- TD's
		# built-in entries stay untouched, whatever their count in this
		# build. _injectPanes() re-adds ours afterwards.
		names = list(self.stored['PaneRegistry'])
		if not names:
			return
		for _pane in self.panes:
			for name in names:
				self._removeFromPaneTable(_pane, name)

	def RecallPanel(self, pane, canonical_name, flags=None, run_callback=None):
		"""Apply a registered entry to a UI pane.

		flags: optional full flag dict override for one-shot recall.
		run_callback: True/False to force callback; None uses registered path default
		              (callback runs after built-ins when present).
		"""
		_paneObj = ui.panes[pane.name]
		if not _paneObj:
			debug('Pane object not found for pane: ' + str(pane))
			return

		info = self.stored['PaneRegistry'][canonical_name]
		if flags is None:
			flags = self._entryFlags(info)
		# Tear Away always applies owner+type first so the torn pane shows the right COMP.
		if flags.get('tear_away'):
			flags = dict(flags)
			flags['set_owner'] = True
			flags['change_type'] = True
		_owner = self._resolvePanelOp(info)

		if flags.get('set_owner'):
			if _owner is None:
				debug('Registered COMP not found for canonical name: ' + canonical_name)
				return
			if info.get('panel_path') != _owner.path or info.get('panel_id') != _owner.id:
				info['panel_path'] = _owner.path
				info['panel_id'] = int(_owner.id)
			_paneObj.owner = _owner

		if flags.get('change_type'):
			_panelType = info.get('pane_type')
			if (_panelType and _panelType.upper() in [pt.name for pt in PaneType]
					and (paneType := PaneType[_panelType.upper()])):
				_paneObj = _paneObj.changeType(paneType)
			else:
				debug('Invalid pane type: ' + str(_panelType) + ' for ' + canonical_name)
				return

		if flags.get('maximize'):
			_paneObj.maximize = True

		if flags.get('tear_away'):
			try:
				_paneObj.tearAway()
			except Exception as e:
				debug('PaneTypeRegistry tearAway failed: ' + str(e))

		if flags.get('float') and _owner is not None:
			self._floatOwner(_owner, info.get('pane_type'))

		if flags.get('open_parameters') and _owner is not None:
			try:
				_owner.openParameters()
			except Exception as e:
				debug('PaneTypeRegistry openParameters failed: ' + str(e))

		do_cb = run_callback
		if do_cb is None:
			do_cb = True
		if do_cb:
			self._invokeRecallCallback(info, {
				'pane': _paneObj,
				'pane_comp': pane,
				'owner': _owner,
				'canonical': canonical_name,
				'info': info,
				'registry': self,
			})

	def _invokeRecallCallback(self, info, ctx):
		cb = self._resolveCallbackDat(info)
		if cb is None:
			return
		try:
			fn = getattr(cb.module, 'onPaneRecall', None)
		except Exception as e:
			debug('PaneTypeRegistry callback module error: ' + str(e))
			return
		if fn is None:
			debug('PaneTypeRegistry callback missing onPaneRecall(): ' + cb.path)
			return
		try:
			fn(ctx)
		except Exception as e:
			debug('PaneTypeRegistry onPaneRecall error: ' + str(e))

	def _floatOwner(self, owner, pane_type=None):
		"""Context-dependent float for a registered COMP.

		Viewer-style pane types -> openViewer (floating OP viewer).
		Network/tool pane types -> showInPane Floating (network editor).
		"""
		if owner is None:
			return
		pt = (pane_type or '').upper()
		viewer_types = {
			'PANEL', 'GEOMETRYVIEWER', 'TOPVIEWER', 'CHOPVIEWER',
		}
		try:
			if pt == 'PARAMETERS':
				owner.openParameters()
			elif pt in viewer_types:
				owner.openViewer()
			else:
				TDFunctions.showInPane(owner, pane='Floating')
		except Exception as e:
			debug('PaneTypeRegistry float failed (' + pt + '): ' + str(e))

	def _popMenu(self):
		"""popMenu COMP on this registry (or None)."""
		pm = self.ownerComp.op('popMenu')
		if pm is not None and pm.valid:
			return pm
		return None

	def OpenFloatingNetworkEditor(self, owner_op, name=None):
		"""Open a floating Network Editor pointed at owner_op."""
		if owner_op is None:
			return None
		win_name = name or (owner_op.name + '_net')
		pane = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name=win_name)
		pane.owner = owner_op
		return pane

	def OpenPaneTypeContextMenu(self, panetype_comp, canonical_name):
		"""Right-click menu for a panebar panetype dropdown row."""
		if not canonical_name:
			return
		if canonical_name in self.stored['PaneRegistry']:
			self._openRegisteredContextMenu(panetype_comp, canonical_name)
			return
		pane_type = self.BUILTIN_LABEL_TO_TYPE.get(canonical_name)
		if pane_type:
			self._openBuiltinRegisterContextMenu(panetype_comp, canonical_name, pane_type)

	def _openRegisteredContextMenu(self, panetype_comp, canonical_name):
		pm = self._popMenu()
		if pm is None:
			debug('PaneTypeRegistry: popMenu not found on ' + self.ownerComp.path)
			return

		info = self.stored['PaneRegistry'][canonical_name]
		flags = self._entryFlags(info)
		has_callback = self._resolveCallbackDat(info) is not None

		items = [
			'Recall (as registered)',
			'Owner + Type',
			'Set Owner',
			'Change Type',
			'Maximize',
			'Tear Away',
			'Float',
			'Open Parameters',
			'Run Callback',
			'Open Floating Network Editor',
			'Unregister',
		]
		dividers = [
			'Recall (as registered)',
			'Owner + Type',
			'Run Callback',
		]
		checked = ['Recall (as registered)']
		for label, key in (
			('Set Owner', 'set_owner'),
			('Change Type', 'change_type'),
			('Maximize', 'maximize'),
			('Tear Away', 'tear_away'),
			('Float', 'float'),
			('Open Parameters', 'open_parameters'),
		):
			if flags.get(key):
				checked.append(label)
		if has_callback:
			checked.append('Run Callback')
		disabled = []
		if not has_callback:
			disabled.append('Run Callback')

		details = {
			'panetype': panetype_comp,
			'pane': panetype_comp.parent() if panetype_comp else None,
			'canonical': canonical_name,
			'info': info,
			'kind': 'registered',
		}
		self._openPopMenu(items, self.OnPaneTypeContextSelect, details, checked, disabled, dividers)

	def _openBuiltinRegisterContextMenu(self, panetype_comp, builtin_label, pane_type):
		pm = self._popMenu()
		if pm is None:
			return
		pane_comp = panetype_comp.parent() if panetype_comp else None
		owner = None
		if pane_comp is not None:
			try:
				owner = ui.panes[pane_comp.name].owner
			except Exception:
				owner = None
		owner_name = owner.name if owner else '(no owner)'
		items = [
			'Register "' + owner_name + '" as ' + builtin_label + '...',
		]
		details = {
			'panetype': panetype_comp,
			'pane': pane_comp,
			'builtin_label': builtin_label,
			'pane_type': pane_type,
			'owner': owner,
			'kind': 'builtin_register',
		}
		disabled = []
		if owner is None:
			disabled = list(items)
		self._openPopMenu(items, self.OnPaneTypeContextSelect, details, [], disabled, [])

	def _openPopMenu(self, items, callback, details, checked, disabled, dividers):
		pm = self._popMenu()
		if pm is None:
			return
		kw = dict(
			items=items,
			callback=callback,
			callbackDetails=details,
			checkedItems=checked,
			disabledItems=disabled,
			dividersAfterItems=dividers,
			autoClose=True,
		)
		if hasattr(pm, 'Open'):
			pm.Open(**kw)
		else:
			pm.ext.PopMenuExt.Open(**kw)

	def _hostRegistryTemplate(self):
		"""A project PaneTypeRegistry that has Registration pars (persist template)."""
		candidates = []
		for comp in root.findChildren(name='PaneTypeRegistry', maxDepth=12):
			if not comp or not comp.valid:
				continue
			if self._is_in_sys(comp):
				continue
			if hasattr(comp.par, 'Autoregister'):
				candidates.append(comp)
		if not candidates:
			return None
		def _template_score(c):
			# Prefer unused templates (no live HostCanonical) so copies do not
			# inherit another host's menu-name tracking.
			has_host = False
			if c.extensionsReady and hasattr(c.ext, 'PaneTypeRegistryExt'):
				has_host = bool(c.ext.PaneTypeRegistryExt.stored.get('HostCanonical'))
			return (1 if has_host else 0, c.path.count('/'), c.path)
		candidates.sort(key=_template_score)
		return candidates[0]

	def _findHostRegistry(self, owner, canonical):
		"""Find a host registry already bound to this menu name."""
		if owner is None or not canonical:
			return None
		for child in owner.findChildren(name='PaneTypeRegistry*', depth=1):
			if hasattr(child.par, 'Canonicalname'):
				name = str(child.par.Canonicalname.eval() or '').strip()
				if name == canonical:
					return child
			if child.extensionsReady and hasattr(child.ext, 'PaneTypeRegistryExt'):
				if child.ext.PaneTypeRegistryExt.stored.get('HostCanonical') == canonical:
					return child
		return None

	def _uniqueHostRegistryName(self, owner, canonical):
		"""Legal unique child name for a host registry instance."""
		if hasattr(tdu, 'legalName'):
			legal = tdu.legalName(canonical)
		else:
			legal = ''.join(c if (c.isalnum() or c == '_') else '_' for c in canonical)
		legal = legal.strip('_') or 'entry'
		base = 'PaneTypeRegistry_' + legal
		if owner.op(base) is None:
			return base
		n = 1
		while owner.op(base + str(n)) is not None:
			n += 1
		return base + str(n)

	def _scrubCopiedHostTracking(self, host_reg):
		"""Clear inherited HostCanonical from a template copy when we do not own it."""
		if host_reg is None or not host_reg.valid:
			return
		if not host_reg.extensionsReady or not hasattr(host_reg.ext, 'PaneTypeRegistryExt'):
			return
		ext = host_reg.ext.PaneTypeRegistryExt
		prev = ext.stored.get('HostCanonical') or ''
		if not prev:
			return
		if not ext._ownsGlobalMenuName(prev):
			# Stale name from template — do not unregister the template's live entry.
			ext.stored['HostCanonical'] = ''
			try:
				ext.stored['PaneRegistry'].clear()
			except Exception:
				pass

	def EnsureHostRegistry(self, owner, canonical, pane_type='PANEL'):
		"""Ensure owner has a PaneTypeRegistry child for this menu entry.

		Multiple registries per owner are allowed (e.g. Parameters + Network Editor).
		/sys storage does not persist; each host registry Autoregisters on open.
		"""
		if owner is None or not getattr(owner, 'isCOMP', False):
			return None
		host_reg = self._findHostRegistry(owner, canonical)
		if host_reg is None:
			template = self._hostRegistryTemplate()
			if template is None:
				debug('PaneTypeRegistry: no host template with Registration page; cannot persist')
				return None
			reg_name = self._uniqueHostRegistryName(owner, canonical)
			host_reg = owner.copy(template, name=reg_name)
			self._placeHostRegistry(owner, host_reg)
			# Copy may have already inited with the template's HostCanonical.
			# Drop stale tracking that does not belong to this new instance.
			self._scrubCopiedHostTracking(host_reg)
		self._configureHostRegistry(host_reg, canonical, pane_type)
		return host_reg

	def _placeHostRegistry(self, owner, host_reg):
		"""Place a newly copied host registry on a clear 200-grid slot."""
		import math
		siblings = [c for c in owner.children if c != host_reg]
		if not siblings:
			host_reg.nodeX = 0
			host_reg.nodeY = 0
			return
		right = max(c.nodeX + c.nodeWidth for c in siblings)
		host_reg.nodeX = int(math.ceil((right + 200) / 200.0) * 200)
		host_reg.nodeY = max(c.nodeY for c in siblings)

	def _configureHostRegistry(self, host_reg, canonical, pane_type):
		"""Set Registration pars so Autoregister re-publishes after restart."""
		if host_reg is None:
			return
		def _apply():
			if not host_reg.valid:
				return
			if not host_reg.extensionsReady or not hasattr(host_reg.ext, 'PaneTypeRegistryExt'):
				run(
					'args[0]()',
					_apply,
					delayFrames=3,
					delayRef=op.TDResources,
				)
				return
			ext = host_reg.ext.PaneTypeRegistryExt
			try:
				ext.stored['PaneRegistry'].clear()
			except Exception:
				pass
			# Keep HostCanonical so _applyHostRegistration can transition
			# a temporary copy/init name (host.name) to the final label.
			if hasattr(host_reg.par, 'Autoregister'):
				host_reg.par.Autoregister.val = True
			if hasattr(host_reg.par, 'Canonicalname'):
				host_reg.par.Canonicalname.val = canonical

			if hasattr(host_reg.par, 'Menuorder'):
				host_reg.par.Menuorder.val = -1
			if hasattr(host_reg.par, 'Panetype'):
				pt = host_reg.par.Panetype
				pt.menuNames = ext.PANE_TYPE_NAMES
				pt.menuLabels = ext.PANE_TYPE_LABELS
				pt.val = pane_type
			if hasattr(host_reg.par, 'Comp'):
				host_reg.par.Comp.val = '..'
			if hasattr(host_reg.par, 'Setowner'):
				host_reg.par.Setowner.val = True
			if hasattr(host_reg.par, 'Changetype'):
				host_reg.par.Changetype.val = True
			for name, val in (
				('Maximize', False),
				('Tearaway', False),
				('Float', False),
				('Openparameters', False),
			):
				if hasattr(host_reg.par, name):
					getattr(host_reg.par, name).val = val
			ext._applyHostRegistration(force=True)
			ext._ensureSelectionExecuteRole()
		_apply()

	def RegisterCurrentOwnerAsBuiltin(self, pane_comp, pane_type, builtin_label=None, owner=None):
		"""Register the pane's current owner as a custom panebar entry for pane_type."""
		if owner is None and pane_comp is not None:
			try:
				owner = ui.panes[pane_comp.name].owner
			except Exception:
				owner = None
		if owner is None:
			op.TDResources.PopDialog.OpenDefault(
				text='No owner on this pane to register.',
				title='PaneTypeRegistry',
				buttons=['OK'],
				textEntry=False,
			)
			return False

		label = builtin_label or pane_type
		# Distinct default per pane type so one COMP can register as several entries.
		default_name = owner.name + ' ' + label
		exists = default_name in self.stored['PaneRegistry']
		msg = (
			'Register this COMP as a panebar entry.\n'
			+ 'This adds a PaneTypeRegistry component inside the COMP\n'
			+ 'so the entry re-registers automatically on project open.\n\n'
			+ 'COMP: ' + owner.path + '\n'
			+ 'Pane type: ' + label + ' (' + pane_type + ')\n'
			+ 'Defaults: Owner + Type\n\n'
			+ 'Edit the menu name below:'
		)
		if exists:
			msg += '\n\nNote: "' + default_name + '" is already registered and will be replaced if you keep that name.'
		details = {
			'owner': owner,
			'pane_type': pane_type,
			'builtin_label': label,
			'pane': pane_comp,
		}
		op.TDResources.PopDialog.OpenDefault(
			text=msg,
			title='Register Pane Type',
			buttons=['Register', 'Cancel'],
			callback=self._onRegisterBuiltinDialog,
			details=details,
			textEntry=default_name,
			escButton=2,
			enterButton=1,
		)
		return True

	def _menuNameConflict(self, canonical, owner):
		"""Return conflict info if canonical is already registered, else None."""
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return None
		other = self._resolvePanelOp(info)
		other_path = None
		if other is not None:
			other_path = other.path
		else:
			other_path = info.get('panel_path') or '(missing COMP)'
		same_owner = False
		if owner is not None and other is not None:
			same_owner = (other == owner) or (other.path == owner.path)
		elif owner is not None and info.get('panel_path') == owner.path:
			same_owner = True
		return {
			'same_owner': same_owner,
			'other_path': other_path,
			'info': info,
		}

	def _suggestUniqueMenuName(self, canonical):
		"""Suggest an unused menu name based on canonical."""
		base = canonical
		if hasattr(tdu, 'incrementStringDigits'):
			candidate = canonical
			for _ in range(64):
				if candidate not in self.stored['PaneRegistry']:
					return candidate
				candidate = tdu.incrementStringDigits(candidate)
			return canonical + ' 2'
		n = 2
		while (base + ' ' + str(n)) in self.stored['PaneRegistry']:
			n += 1
		return base + ' ' + str(n)

	def _finishBuiltinRegister(self, owner, canonical, pane_type, pane_comp=None):
		"""Deploy host registry (persist) and optionally recall immediately."""
		host_reg = self.EnsureHostRegistry(owner, canonical, pane_type)
		if host_reg is None:
			self.RegisterPanel(
				owner,
				canonical,
				pane_type=pane_type,
				set_owner=True,
				change_type=True,
				maximize=False,
				tear_away=False,
				float_pane=False,
				open_parameters=False,
			)
		if pane_comp is not None:
			self.RecallPanel(pane_comp, canonical)

	def _onMenuNameConflictDialog(self, info):
		"""Handle Replace / Use Suggested / Cancel for menu name clashes."""
		if not info:
			return
		button = info.get('button')
		details = info.get('details') or {}
		owner = details.get('owner')
		pane_type = details.get('pane_type')
		pane = details.get('pane')
		if owner is None or not pane_type:
			return
		if button == 'Cancel' or button is None:
			return
		if button == 'Replace':
			canonical = details.get('canonical')
			# Drop the previous host registry binding if we can find it on the other COMP.
			self._unregisterConflictingHost(canonical, keep_owner=owner)
		elif button == 'Use Suggested':
			canonical = details.get('suggested') or self._suggestUniqueMenuName(
				details.get('canonical') or owner.name
			)
		else:
			return
		if not canonical:
			return
		self._finishBuiltinRegister(owner, canonical, pane_type, pane)

	def _unregisterConflictingHost(self, canonical, keep_owner=None):
		"""Clear Autoregister on other host registries that publish this menu name."""
		info = self.stored['PaneRegistry'].get(canonical) or {}
		other = self._resolvePanelOp(info)
		if other is None:
			self.UnregisterPanel(canonical)
			return
		if keep_owner is not None and (other == keep_owner or other.path == keep_owner.path):
			return
		for child in other.findChildren(name='PaneTypeRegistry*', depth=1):
			matches = False
			if hasattr(child.par, 'Canonicalname'):
				if str(child.par.Canonicalname.eval() or '').strip() == canonical:
					matches = True
			if child.extensionsReady and hasattr(child.ext, 'PaneTypeRegistryExt'):
				if child.ext.PaneTypeRegistryExt.stored.get('HostCanonical') == canonical:
					matches = True
			if not matches:
				continue
			if hasattr(child.par, 'Autoregister'):
				child.par.Autoregister.val = False
			if child.extensionsReady and hasattr(child.ext, 'PaneTypeRegistryExt'):
				child.ext.PaneTypeRegistryExt._clearHostRegistration()
				child.ext.PaneTypeRegistryExt._setRegStatus('Unregistered (name taken)')
		self.UnregisterPanel(canonical)

	def _onRegisterBuiltinDialog(self, info):
		"""PopDialog callback for RegisterCurrentOwnerAsBuiltin."""
		if not info or info.get('button') != 'Register':
			return
		details = info.get('details') or {}
		owner = details.get('owner')
		pane_type = details.get('pane_type')
		if owner is None or not pane_type:
			return
		canonical = str(info.get('enteredText') or '').strip()
		if not canonical:
			op.TDResources.PopDialog.OpenDefault(
				text='Menu name cannot be empty.',
				title='Register Pane Type',
				buttons=['OK'],
				textEntry=False,
			)
			return

		conflict = self._menuNameConflict(canonical, owner)
		if conflict is not None:
			# Same owner updating their own entry is fine; other owner needs a choice.
			if not conflict.get('same_owner'):
				other = conflict.get('other_path') or '(unknown)'
				suggested = self._suggestUniqueMenuName(canonical)
				op.TDResources.PopDialog.OpenDefault(
					text=(
						'Menu name "' + canonical + '" is already used by:\n'
						+ other + '\n\n'
						+ 'Replace that entry, use "' + suggested + '", or cancel?'
					),
					title='Menu Name Conflict',
					buttons=['Replace', 'Use Suggested', 'Cancel'],
					callback=self._onMenuNameConflictDialog,
					details={
						'owner': owner,
						'pane_type': pane_type,
						'pane': details.get('pane'),
						'canonical': canonical,
						'suggested': suggested,
					},
					textEntry=False,
					escButton=3,
					enterButton=2,
				)
				return

		self._finishBuiltinRegister(owner, canonical, pane_type, details.get('pane'))

	def OnPaneTypeContextSelect(self, infoDict):
		"""popMenu onSelect handler for panetype right-click menu."""
		item = infoDict.get('item') if infoDict else None
		details = (infoDict or {}).get('details') or {}
		if not item:
			return

		if details.get('kind') == 'builtin_register':
			if item.startswith('Register '):
				self.RegisterCurrentOwnerAsBuiltin(
					details.get('pane'),
					details.get('pane_type'),
					builtin_label=details.get('builtin_label'),
					owner=details.get('owner'),
				)
			return

		canonical = details.get('canonical')
		pane = details.get('pane')
		if not canonical or canonical not in self.stored['PaneRegistry']:
			return
		info = self.stored['PaneRegistry'][canonical]
		owner = self._resolvePanelOp(info)

		if item == 'Recall (as registered)':
			if pane is not None:
				self.RecallPanel(pane, canonical)
			return

		if item == 'Open Floating Network Editor':
			self.OpenFloatingNetworkEditor(owner)
			return

		if item == 'Unregister':
			self.UnregisterPanel(canonical)
			# clear host tracking on the source registry if it owns this name
			src = self._resolveSourceRegistry(info)
			if src is not None and src.extensionsReady:
				src_ext = getattr(src.ext, 'PaneTypeRegistryExt', None)
				if src_ext is not None and src_ext.stored.get('HostCanonical') == canonical:
					src_ext.stored['HostCanonical'] = ''
					src_ext._setRegStatus('Unregistered via context menu')
			return

		if pane is None:
			return

		one_shot = {
			'Set Owner': dict(set_owner=True, change_type=False, maximize=False, tear_away=False, float=False, open_parameters=False),
			'Change Type': dict(set_owner=False, change_type=True, maximize=False, tear_away=False, float=False, open_parameters=False),
			'Maximize': dict(set_owner=False, change_type=False, maximize=True, tear_away=False, float=False, open_parameters=False),
			'Tear Away': dict(set_owner=True, change_type=True, maximize=False, tear_away=True, float=False, open_parameters=False),
			'Float': dict(set_owner=False, change_type=False, maximize=False, tear_away=False, float=True, open_parameters=False),
			'Open Parameters': dict(set_owner=False, change_type=False, maximize=False, tear_away=False, float=False, open_parameters=True),
			'Owner + Type': dict(set_owner=True, change_type=True, maximize=False, tear_away=False, float=False, open_parameters=False),
		}
		if item == 'Run Callback':
			self.RecallPanel(pane, canonical, flags=dict(
				set_owner=False, change_type=False, maximize=False, tear_away=False, float=False, open_parameters=False
			), run_callback=True)
			return
		if item in one_shot:
			self.RecallPanel(pane, canonical, flags=one_shot[item], run_callback=False)

	def onPaneTypeSelected(self, change_dat):
		"""Panebar selection callback — global /sys registry only."""
		if not self._is_sys_global():
			return
		pane = change_dat.parent(2)
		selected = change_dat[0, 0].val
		if selected in self.stored['PaneRegistry']:
			self.RecallPanel(pane, selected)
			return

		# Injected builtins (e.g. OP Browser) — not in TD's desk table.
		injected = {label for label, _after in self.INJECTED_BUILTIN_MENU}
		if selected in injected:
			pane_type_name = self.BUILTIN_LABEL_TO_TYPE.get(selected)
			if not pane_type_name or pane is None:
				return
			try:
				pane_obj = ui.panes[pane.name]
			except Exception:
				pane_obj = None
			if pane_obj is None:
				debug('PaneTypeRegistry: pane not found for ' + selected)
				return
			try:
				pane_obj.changeType(getattr(PaneType, pane_type_name))
			except Exception as e:
				debug('PaneTypeRegistry: changeType(' + pane_type_name + ') failed: ' + str(e))
			return
		# Native TD builtins are applied via the table's desk command column.
