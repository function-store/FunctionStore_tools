

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase

import json
import os
import time



### FNS_CommandRegistry helpers - from the FNSCommand module in ExtUtils
### (single source of truth: QuickExt/ExtUtils/FNSCommand.py). Missing
### module degrades to no-commands; the registry ext itself must never
### fail to compile over it.
try:
	_fnsmod = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('FNSCommand')
	fns_command = _fnsmod.fns_command
	fns_announce = _fnsmod.announce
except Exception:
	def fns_command(fn=None, **kw):
		return fn if callable(fn) else (lambda f: f)
	def fns_announce(comp):
		return None


class ConfigRegistryExt(RegistryBase):
	"""Registry for persisted tool settings (the FNS config file).

	Every tool ships ONE ConfigRegistry host (Comp='..'); the host publishes
	the tool into the /sys global, and the global -- the ONLY file writer --
	aggregates every tool's section into one JSON in the user palette:

		<userPaletteFolder>/FNStools_ext/config/FNStools_config.json

	What persists per tool:

	  * custom PARAMETER state (mode/val/expr/bindExpr) of the tool COMP.
	    Meta pages (SKIP_PAGES) and per-host exclude patterns are skipped,
	    read-only pars and pulses are skipped, and a par missing from the
	    live tool is NEVER created on load -- a stale file cannot resurrect
	    retired parameters.
	  * optional tool STATE via a config_callbacks DAT the tool owns
	    (spawned by the Create Callbacks pulse):

		def onConfigSave():
			'''JSON-serializable dict stored under the tool's "state".'''
			return {}

		def onConfigLoad(data):
			'''Re-apply previously saved state (called after par apply).'''
			pass

	Save triggers: TD's project pre-save (presave_exec, global only), the
	Saveall pulse (any host forwards to the global), and the UPDATER right
	before it replaces the toolkit. Load: per tool at registration time
	(Autoload, default on), deferred a few frames, once per session.

	Scope (Configscope par): authored on the TOOLKIT ROOT (op.FNS,
	'FNSTools' page) -- the master's and global's own Configscope pars
	BIND to it, so the root par is the single record and either surface
	edits it. 'global' (default) roams through the JSON
	above; 'project' never reads or writes the file -- the .toe is the
	whole store (host pars, state tables and tool pars all boot from the
	project itself), so the config travels with the project file. Save
	triggers still run every tool's onConfigSave for its side effects
	(the configurators freshen their state tables there) -- only the file
	I/O is gated. NOTE for the updater rework: under project scope both
	roaming directions are blocked, so the tool-replacement handoff must
	carry sections itself (own snapshot/apply, or a temp Configfile with
	scope forced global for the swap).

	The file is read-merge-write: sections of tools that are not currently
	installed are PRESERVED on save, so partial installs never lose data.
	A file with a different schema version is never merged into and never
	applied -- it is moved aside and started fresh on the next save.
	"""

	SHORTCUT = 'FNS_CONFIGREGISTRY'
	EXT_NAME = 'ConfigRegistryExt'
	REGISTRY_NAME = 'FNS_ConfigRegistry'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Cf'
	TOOL_PAGE_LABEL = 'Config'
	TOOL_PAGE_PARS = ('Createcallbacks', 'Autoregister', 'Register', 'Regstatus',
					  'Autoload', 'Persistpars', 'Excludepars', 'Excludepages')

	# The DAT a host spawns into its tool, and the template it comes from.
	CALLBACKS_NAME = 'config_callbacks'
	CALLBACKS_TEMPLATE = 'callbacks_template'

	# On-disk contract. Bump only on breaking shape changes.
	SCHEMA = 1
	FILE_NAME = 'FNStools_config.json'
	SUBFOLDER = 'FNStools_ext/config'

	# Pages never persisted (plus per-host Excludepages patterns). The
	# tool's 'Registry' page IS persisted on purpose: its pars are the bind
	# MASTERS holding registry order/display as constants on the tool, and
	# restoring them is how surface layout survives a tool replacement.
	SKIP_PAGES = ('About', 'Version Ctrl', 'Info', 'Callbacks', 'Common')
	# Styles with no persistable value.
	SKIP_STYLES = ('Pulse', 'Momentary', 'Header')

	# --- surface hooks (RegistryBase contract; the 'surface' is the file) ---

	def _preInit(self):
		# Which canonicals were applied this session: healing-tick republishes
		# must not re-apply config every few seconds. Plain attribute -- /sys
		# is rebuilt every boot, so 'once per session' resets naturally.
		self._applied_this_session = set()
		self._cfg_cache = None
		self._cfg_cache_mtime = -1

	def _ensureSelectionExecuteRole(self):
		ex = self.ownerComp.op('presave_exec')
		if self._is_sys_global():
			if ex is not None and not ex.par.active.eval():
				ex.par.active = True
			return
		# Hosts must not keep a parallel table and must not write the file.
		self.stored['PaneRegistry'].clear()
		if ex is not None and ex.par.active.eval():
			ex.par.active = False

	def _syncSurface(self, attempts=40):
		"""The file needs no injection -- 'sync' just keeps the pre-save hook
		armed on the global. Idempotent and cheap; promotion and healing call
		it repeatedly."""
		self._pane_sync_queued = False
		if not self._is_sys_global():
			return
		ex = self.ownerComp.op('presave_exec')
		if ex is not None and not ex.par.active.eval():
			ex.par.active = True

	def _healRegistryEntries(self):
		"""Base healing covers the boot re-publish sweep and clone healing;
		the file surface only needs its pre-save hook kept armed -- plus the
		FNS_persist tag sweep, but ONLY inside the boot window."""
		super()._healRegistryEntries()
		if not self._is_sys_global():
			return
		# Boot-window budget for the tag sweep -- same bound and same lazy
		# init as the base's host sweep, because a global promoted from a
		# copy runs _preInit on the host branch, before it is the global.
		if getattr(self, '_persist_sweeps_left', None) is None:
			self._persist_sweeps_left = self.BOOT_SWEEPS
		if self._persist_sweeps_left > 0:
			self._persist_sweeps_left -= 1
			self._sweepPersistTags()
		self._syncSurface()

	# --- FNS_persist: registration by tag, for tools with no host ---

	PERSIST_TAG = 'FNS_persist'

	def _sweepPersistTags(self):
		"""Register COMPs tagged FNS_persist that ship no host of their own.

		The tag IS the registration: a micro-tool too small to carry a
		ConfigRegistry host gets its custom parameters roamed by tagging it
		-- no host, no callback, no configuration, defaults throughout. A
		HOSTED tool always wins its canonical name; the tag never overrides
		a real registration.

		WHEN IT RUNS -- never on a timer. Scanning the project for a tag is
		a whole-tree walk, and this toolkit runs inside live shows: nothing
		here may add recurring per-frame work. It runs at exactly the two
		moments the answer can change anything:

		  * the BOOT window (bounded by BOOT_SWEEPS, like the base's host
		    re-publish sweep) -- /sys is ephemeral, so this is what
		    re-registers tagged COMPs on open, in time for their settings to
		    be applied;
		  * every SaveAll -- pre-save, the Saveall pulse, the UPDATER -- so
		    a COMP tagged mid-session is picked up by the save that would
		    persist it, and an untagged one stops being written.

		Between those, tagging is inert: a tag added after the boot window
		takes effect at the next save, and its settings apply on the next
		open. Untagging unregisters but does NOT delete the tool's section
		-- the file preserves sections of tools that are not installed.
		"""
		if not self._is_sys_global():
			return
		try:
			# NO depth argument: TD's findChildren depth is an EXACT depth,
			# not a maximum -- passing one silently matches nothing.
			tagged = op('/').findChildren(tags=[self.PERSIST_TAG])
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: persist-tag sweep: {e}')
			return
		live = {}
		for comp in tagged:
			if comp.family != 'COMP':
				continue
			path = comp.path
			if path.startswith('/sys') or path.startswith('/ui'):
				continue
			claimed = live.setdefault(comp.name, comp)
			if claimed is not comp:
				debug(f'{self.REGISTRY_NAME}: {self.PERSIST_TAG} name clash on '
					  f'{comp.name!r} -- keeping {claimed.path}, ignoring {path}')
		entries = self.stored['PaneRegistry']
		# a COMP that lost the tag gives its registration up (its saved
		# section stays in the file, like any uninstalled tool)
		for name, info in list(entries.items()):
			if info.get('tag_source') == '1' and name not in live:
				self.UnregisterTool(name)
		for name, comp in live.items():
			info = entries.get(name)
			if info is not None:
				if info.get('tag_source') != '1':
					continue  # a real host owns this canonical name
				if self._resolvePanelOp(info) is comp:
					continue  # already registered off the tag
			self.RegisterTool(comp, name, autoload=True, persist_pars=True)
			entry = entries.get(name)
			if entry is not None:
				entry = dict(entry)
				entry['tag_source'] = '1'
				entries[name] = entry

	# Location-independent: resolves through the config package's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	# _healHostClones and StampHost come from RegistryBase off these two.
	CLONE_EXPR = "op.FNS.op('FNS_ConfigRegistry') if hasattr(op, 'FNS') else None"

	# --- config file ---

	@property
	def ConfigPath(self):
		"""Absolute path of the aggregated config file. An explicit Configfile
		par (Config page, set on the MASTER -- promotion carries it to the
		global) overrides the user-palette default."""
		override = ''
		p = getattr(self.ownerComp.par, 'Configfile', None)
		if p is not None:
			try:
				override = str(p.eval()).strip()
			except Exception:
				override = ''
		if override:
			return override.replace('\\', '/')
		return (app.userPaletteFolder + '/' + self.SUBFOLDER + '/' + self.FILE_NAME).replace('\\', '/')

	def _scopeIsProject(self):
		"""True when Configscope says the config lives in the .toe only.

		The own par normally BINDS to the toolkit root's Configscope
		(op.FNS, the authored record); a rootless/standalone deploy falls
		through to its own constant value, and anything missing or broken
		reads as global -- a copy predating the par behaves as before."""
		p = getattr(self.ownerComp.par, 'Configscope', None)
		if p is not None:
			try:
				return str(p.eval()) == 'project'
			except Exception:
				pass  # dangling bind (no toolkit root) -- try the root directly
		root = getattr(op, 'FNS', None)
		p = getattr(root.par, 'Configscope', None) if root is not None else None
		if p is not None:
			try:
				return str(p.eval()) == 'project'
			except Exception:
				pass
		return False

	def _freshData(self):
		return {'schema': self.SCHEMA, 'tools': {}}

	def _retireFile(self, suffix):
		"""Move the current file aside (never silently destroy user data)."""
		path = self.ConfigPath
		try:
			bak = path + suffix
			if os.path.exists(bak):
				os.remove(bak)
			os.replace(path, bak)
			debug(f'{self.REGISTRY_NAME}: moved unreadable config aside -> {bak}')
		except OSError as e:
			debug(f'{self.REGISTRY_NAME}: could not move config aside: {e}')

	def _readFile(self):
		"""Raw read. Missing file -> fresh dict. Corrupt JSON -> moved aside,
		fresh dict. Never raises."""
		path = self.ConfigPath
		if not os.path.exists(path):
			return self._freshData()
		try:
			with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			if not isinstance(data, dict):
				raise ValueError('config root is not an object')
			return data
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: unreadable config file ({e})')
			self._retireFile('.corrupt.bak')
			return self._freshData()

	@property
	def ConfigData(self):
		"""Parsed, schema-gated, mtime-cached view of the file. A mismatched
		schema is REFUSED for reading -- callers see an empty document."""
		api = self._registryApi()
		if api is not self:
			return api.ConfigData
		path = self.ConfigPath
		try:
			mt = os.path.getmtime(path)
		except OSError:
			mt = None
		if self._cfg_cache is not None and self._cfg_cache_mtime == mt:
			return self._cfg_cache
		data = self._readFile()
		if data.get('schema') != self.SCHEMA:
			debug(f'{self.REGISTRY_NAME}: config schema {data.get("schema")!r} != '
				  f'{self.SCHEMA} -- refusing to load {path}')
			data = self._freshData()
		self._cfg_cache = data
		self._cfg_cache_mtime = mt
		return data

	def _writeFile(self, data):
		"""Atomic write: same-dir temp + fsync + os.replace."""
		path = self.ConfigPath
		folder = os.path.dirname(path)
		tmp = path + '.tmp.%d' % os.getpid()
		try:
			os.makedirs(folder, exist_ok=True)
			with open(tmp, 'w', encoding='utf-8') as f:
				json.dump(data, f, indent=1)
				f.flush()
				os.fsync(f.fileno())
			os.replace(tmp, path)
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: config write FAILED: {e}')
			try:
				if os.path.exists(tmp):
					os.remove(tmp)
			except OSError:
				pass
			return False
		try:
			self._cfg_cache = data
			self._cfg_cache_mtime = os.path.getmtime(path)
		except OSError:
			self._cfg_cache = None
			self._cfg_cache_mtime = -1
		return True

	# --- par snapshot / apply (hand-rolled; TDJSON rejected because its
	# loader CREATES missing pars -- the legacy resurrection bug) ---

	def _matchAny(self, patterns, name):
		patterns = (patterns or '').strip()
		if not patterns:
			return False
		try:
			return bool(tdu.match(patterns, [name]))
		except Exception:
			return False

	def _jsonSafe(self, value):
		if isinstance(value, (int, float, str, bool)) or value is None:
			return value
		return str(value)

	def _snapshotPars(self, tool, info):
		"""{parName: {mode, val, eval, expr, bindExpr}} for the tool's custom
		pars, exclusions applied."""
		out = {}
		exclude_pars = info.get('exclude_pars', '')
		exclude_pages = info.get('exclude_pages', '')
		for p in tool.customPars:
			try:
				page_name = p.page.name
				if page_name in self.SKIP_PAGES or self._matchAny(exclude_pages, page_name):
					continue
				if p.style in self.SKIP_STYLES or p.readOnly:
					continue
				if self._matchAny(exclude_pars, p.name):
					continue
				rec = {'mode': p.mode.name, 'val': self._jsonSafe(p.val)}
				try:
					rec['eval'] = self._jsonSafe(p.eval())
				except Exception:
					rec['eval'] = rec['val']
				if p.expr:
					rec['expr'] = p.expr
				if p.bindExpr:
					rec['bindExpr'] = p.bindExpr
				out[p.name] = rec
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: snapshot {tool.path}.{p.name}: {e}')
		return out

	def _applyPars(self, tool, pars_section, canonical):
		"""Apply a saved par section onto the live tool. Per-par containment;
		a par missing from the tool is skipped, NEVER created."""
		applied = 0
		missing = []
		errors = []
		for name, rec in (pars_section or {}).items():
			p = getattr(tool.par, name, None)
			if p is None or not p.isCustom:
				missing.append(name)
				continue
			if p.style in self.SKIP_STYLES or p.readOnly:
				continue
			try:
				mode = rec.get('mode', 'CONSTANT')
				if mode == 'EXPRESSION':
					p.expr = rec.get('expr') or ''
					p.mode = ParMode.EXPRESSION
				elif mode == 'BIND':
					p.bindExpr = rec.get('bindExpr') or ''
					p.mode = ParMode.BIND
					master = None
					try:
						master = p.bindMaster
					except Exception:
						master = None
					if master is None:
						# dangling bind would raise on every eval and kill
						# extension inits -- fall back to a plain value
						p.mode = ParMode.CONSTANT
						p.val = rec.get('eval', rec.get('val'))
					else:
						try:
							p.val = rec.get('eval', rec.get('val'))
						except Exception:
							pass
				else:
					if p.mode != ParMode.CONSTANT:
						p.mode = ParMode.CONSTANT
					p.val = rec.get('val')
				applied += 1
			except Exception as e:
				errors.append(f'{name}: {e}')
		if missing:
			debug(f'{self.REGISTRY_NAME}: {canonical!r}: {len(missing)} saved par(s) '
				  f'not on the live tool, skipped: {", ".join(sorted(missing)[:8])}'
				  + (' ...' if len(missing) > 8 else ''))
		if errors:
			debug(f'{self.REGISTRY_NAME}: {canonical!r}: par apply errors: '
				  + '; '.join(errors[:8]))
		return applied

	# --- save / load engine (global only; hosts forward) ---

	def _callbackModule(self, info):
		dat = self._resolveCallbackDat(info)
		if dat is None:
			return None
		try:
			return dat.module
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: callbacks DAT {dat.path} failed to compile: {e}')
			return None

	def _toolVersion(self, tool):
		p = getattr(tool.par, 'Version', None)
		if p is not None:
			try:
				return str(p.eval())
			except Exception:
				pass
		return ''

	def _snapshotTool(self, canonical, info):
		"""One tool's file section, or None when the tool is unreachable."""
		tool = self._resolvePanelOp(info)
		if tool is None:
			return None
		section = {}
		if info.get('persist_pars', '1') == '1':
			section['pars'] = self._snapshotPars(tool, info)
		module = self._callbackModule(info)
		fn = getattr(module, 'onConfigSave', None) if module is not None else None
		if callable(fn):
			try:
				state = fn()
				if state:
					json.dumps(state)  # probe: a bad state drops THIS tool's
					section['state'] = state  # state only, never the file
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: onConfigSave from {canonical!r}: {e}')
		section['meta'] = {
			'saved': time.strftime('%Y-%m-%dT%H:%M:%S'),
			'tool_version': self._toolVersion(tool),
		}
		return section

	def SaveAll(self):
		"""Snapshot every registered tool into the aggregated file (the ONLY
		code path that writes it). Sections of unregistered tools survive."""
		api = self._registryApi()
		if api is not self:
			return api.SaveAll()
		if not self._is_sys_global():
			debug(f'{self.REGISTRY_NAME}: SaveAll ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return False
		# A save is one of the two moments a tag can change the answer, and
		# the only one that runs mid-session (see _sweepPersistTags). It has
		# to happen BEFORE the snapshot below: registering also queues a
		# deferred apply, so a COMP tagged mid-session whose canonical name
		# already had a section written by another project must have its LIVE
		# values written out first -- otherwise that apply lands the foreign
		# section on it a few frames later.
		self._sweepPersistTags()
		if self._scopeIsProject():
			# Project scope: the .toe is the store. Still run every tool's
			# snapshot -- onConfigSave callbacks freshen in-project state
			# (the configurators' group rows live there) -- but leave the
			# roaming file untouched.
			snapped = 0
			for canonical, info in self.stored['PaneRegistry'].items():
				try:
					if self._snapshotTool(canonical, dict(info)) is not None:
						snapped += 1
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: snapshot {canonical!r}: {e}')
			debug(f'{self.REGISTRY_NAME}: SaveAll (project scope): refreshed '
				  f'{snapped} tool(s), file untouched')
			return True
		data = self._readFile()
		if data.get('schema') != self.SCHEMA:
			# never merge into an unknown shape; keep the old file as a .bak
			self._retireFile('.schema%s.bak' % data.get('schema'))
			data = self._freshData()
		tools = data.setdefault('tools', {})
		saved = 0
		for canonical, info in self.stored['PaneRegistry'].items():
			try:
				section = self._snapshotTool(canonical, dict(info))
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: snapshot {canonical!r}: {e}')
				continue
			if section is None:
				continue
			tools[canonical] = section
			saved += 1
		data['schema'] = self.SCHEMA
		data['saved'] = time.strftime('%Y-%m-%dT%H:%M:%S')
		data['saved_by'] = {'project': project.name}
		ok = self._writeFile(data)
		if ok:
			debug(f'{self.REGISTRY_NAME}: saved {saved} tool section(s) -> {self.ConfigPath}')
			self.fnsLog(f'{self.REGISTRY_NAME}: SaveAll wrote {saved} tool section(s) -> {self.ConfigPath}')
		return ok

	def SaveTool(self, canonical_name):
		"""Read-merge-write a single tool's section."""
		api = self._registryApi()
		if api is not self:
			return api.SaveTool(canonical_name)
		if not self._is_sys_global():
			return False
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			debug(f'{self.REGISTRY_NAME}: SaveTool: {canonical_name!r} not registered')
			return False
		section = self._snapshotTool(canonical_name, dict(info))
		if section is None:
			return False
		if self._scopeIsProject():
			return True  # snapshot ran for its side effects; file untouched
		data = self._readFile()
		if data.get('schema') != self.SCHEMA:
			self._retireFile('.schema%s.bak' % data.get('schema'))
			data = self._freshData()
		data.setdefault('tools', {})[canonical_name] = section
		data['schema'] = self.SCHEMA
		data['saved'] = time.strftime('%Y-%m-%dT%H:%M:%S')
		data['saved_by'] = {'project': project.name}
		return self._writeFile(data)

	def LoadTool(self, canonical_name, force=False):
		"""Apply a tool's saved section onto the live tool now. force=True
		re-applies even if it already ran this session."""
		api = self._registryApi()
		if api is not self:
			return api.LoadTool(canonical_name, force=force)
		if not self._is_sys_global():
			return False
		if not force and canonical_name in self._applied_this_session:
			return False
		return self._applyToolConfig(canonical_name)

	def LoadAll(self):
		"""Explicitly re-apply every registered tool's saved section."""
		api = self._registryApi()
		if api is not self:
			return api.LoadAll()
		if not self._is_sys_global():
			return False
		count = 0
		for canonical in list(self.stored['PaneRegistry'].keys()):
			if self._applyToolConfig(canonical):
				count += 1
		debug(f'{self.REGISTRY_NAME}: LoadAll applied {count} tool section(s)')
		self.fnsLog(f'{self.REGISTRY_NAME}: LoadAll applied {count} tool section(s)')
		return count

	# --- scope-flip confirmation (configscope_parexec watches the toolkit
	# root's Configscope; clone hosts and the /sys copy carry the DAT too,
	# so only the master's copy is armed AND handled) ---

	def _isRootMaster(self):
		"""True only on the in-project master directly beside the root."""
		root = getattr(op, 'FNS', None)
		return root is not None and self.ownerComp is root.op(self.REGISTRY_NAME)

	def ConfigScopeChanged(self, par, prev):
		"""Confirm the risky flip. Back to 'global' means the next save
		OVERWRITES the machine-global config, so it gets a three-way
		dialog (push / adopt / stay project); flipping to 'project' moves
		no data and just logs. Programmatic flips go through
		SetConfigScope, which keeps the dialog quiet by default."""
		if not self._isRootMaster():
			return  # inert on clone hosts and the /sys copy
		new = str(par.eval())
		self.fnsLog(f'{self.REGISTRY_NAME}: config scope -> {new}')
		if new != 'global' or getattr(self, '_scope_set_quietly', False):
			return
		op.TDResources.PopDialog.OpenDefault(
			text=('Config scope is back to GLOBAL: from the next save on, '
				  'this project OVERWRITES the machine-global config '
				  '(bar layouts + tool settings).\n\n'
				  'Push: write this project\'s state to the global file '
				  'now.\nAdopt: apply the current global config onto this '
				  'project instead.\nStay Project: cancel the flip.'),
			title='Config Scope -> Global',
			buttons=['Push to Global', 'Adopt Global', 'Stay Project'],
			callback=self._onScopeDialog,
			escButton=3, enterButton=1)

	def _onScopeDialog(self, info):
		n = info.get('buttonNum')
		if n == 1:
			self.SaveAll()          # routes to the /sys global
		elif n == 2:
			self.LoadAll()
		elif n == 3:
			self.SetConfigScope('project')

	def SetConfigScope(self, value, prompt=False):
		"""Flip the config scope programmatically ('global' / 'project').
		Default is quiet -- scripts, tests and the future updater handoff
		must not pop the confirm dialog; that is for interactive flips.
		Routes to the master so the quiet flag lands where the dialog
		handler runs."""
		if str(value) not in ('global', 'project'):
			return False
		root = getattr(op, 'FNS', None)
		master = root.op(self.REGISTRY_NAME) if root is not None else None
		if (master is not None and master is not self.ownerComp
				and hasattr(master.ext, self.EXT_NAME)):
			return getattr(master.ext, self.EXT_NAME).SetConfigScope(
				value, prompt=prompt)
		p = getattr(root.par, 'Configscope', None) if root is not None else None
		if p is None:
			p = getattr(self.ownerComp.par, 'Configscope', None)
		if p is None:
			return False
		if not prompt:
			# parexec fires on the set below; lift the flag a few frames
			# later so only THIS change is exempt from the dialog
			self._scope_set_quietly = True
			run('setattr(args[0], "_scope_set_quietly", False)',
				self, delayFrames=3, delayRef=op.TDResources)
		p.val = str(value)
		return True

	# --- Settings UI: a JSON API over the registrations -------------------
	# The HTML page (settings_page, served by settings_server) is a DUMB
	# CLIENT of UiState/UiSet: everything it lists, renders, or writes flows
	# through the same filters and persistence the registry already
	# enforces. There is deliberately no list of tools or pars in the page,
	# so the UI is correct for whatever subset is installed and can never
	# drift -- this is the replacement for hand-authored root control pars.

	UI_PORTS = tuple(range(9871, 9881))
	UI_IDLE_SECONDS = 600
	UI_TICK_FRAMES = 1800

	def UiState(self):
		"""Everything the settings page needs, in one call."""
		api = self._registryApi()
		if api is not self:
			return api.UiState()
		tools = []
		for canonical, info in sorted(self.stored['PaneRegistry'].items(),
									  key=lambda kv: kv[0].lower()):
			tool = self._resolvePanelOp(dict(info))
			if tool is None:
				continue
			pars = self._describePars(tool, dict(info))
			if not pars:
				continue
			tools.append({'name': canonical, 'path': tool.path,
						  'version': self._toolVersion(tool), 'pars': pars})
		inst = self._installerComp()
		return {'tools': tools, 'config_path': self.ConfigPath,
				'project': project.name,
				'scope': 'project' if self._scopeIsProject() else 'global',
				'installer': inst.path if inst is not None else None}

	# pages that persist fine but are registration plumbing, not settings
	UI_SKIP_PAGES = ('Registry',)

	def _describePars(self, tool, info):
		"""Render metadata for the pars _snapshotPars persists -- one filter,
		two views: what is not persisted is not shown (minus UI_SKIP_PAGES,
		which are plumbing). One entry per parGroup, so a float3 or RGB is
		ONE labelled row whose `pars` lists its components; the page writes
		components individually and UiSet validates against them. Pars that
		are not constant-mode ship readonly so the page can show but never
		fight a bind or expression."""
		out = []
		exclude_pars = info.get('exclude_pars', '')
		exclude_pages = info.get('exclude_pages', '')
		for g in tool.customParGroups:
			try:
				p0 = g[0]
				page_name = p0.page.name
				if page_name in self.SKIP_PAGES or page_name in self.UI_SKIP_PAGES \
						or self._matchAny(exclude_pages, page_name):
					continue
				if p0.style in self.SKIP_STYLES or p0.readOnly:
					continue
				comps = []
				for p in g:
					if self._matchAny(exclude_pars, p.name):
						continue
					comps.append({'name': p.name,
								  'val': self._jsonSafe(p.eval()),
								  'readonly': p.mode != ParMode.CONSTANT,
								  'mode': p.mode.name})
				if not comps:
					continue
				d = {'name': p0.name, 'label': g.label or p0.label,
					 'page': page_name, 'style': p0.style,
					 'order': p0.order, 'pars': comps,
					 'help': str(getattr(p0, 'help', '') or '')}
				if p0.style in ('Menu', 'StrMenu'):
					d['menuNames'] = list(p0.menuNames)
					d['menuLabels'] = list(p0.menuLabels)
				if p0.style in ('Int', 'Float'):
					if p0.clampMin:
						d['min'] = p0.min
					if p0.clampMax:
						d['max'] = p0.max
				out.append(d)
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: describe {tool.path}.{g}: {e}')
		return out

	def UiSet(self, canonical_name, par_name, value):
		"""Set ONE par from the page and persist it through SaveTool.
		Refuses anything _describePars would not have shown."""
		api = self._registryApi()
		if api is not self:
			return api.UiSet(canonical_name, par_name, value)
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return {'ok': False, 'why': f'not registered: {canonical_name}'}
		tool = self._resolvePanelOp(dict(info))
		if tool is None:
			return {'ok': False, 'why': f'tool unreachable: {canonical_name}'}
		allowed = {c['name']: (d, c)
				   for d in self._describePars(tool, dict(info))
				   for c in d['pars']}
		hit = allowed.get(par_name)
		if hit is None:
			return {'ok': False, 'why': f'par not exposed: {par_name}'}
		d, c = hit
		if c['readonly']:
			return {'ok': False, 'why': f'par not constant-mode: {par_name}'}
		p = getattr(tool.par, par_name)
		try:
			if p.style == 'Toggle':
				p.val = value if not isinstance(value, str) \
					else value.lower() in ('1', 'true', 'on', 'yes')
			elif p.style == 'Menu':
				if value not in p.menuNames:
					return {'ok': False, 'why': f'not a menu entry: {value!r}'}
				p.val = value
			elif p.style == 'Int':
				p.val = int(value)
			elif p.isNumber:
				# any numeric component style (Float, RGB, XYZ, UV, WH...)
				p.val = float(value)
			else:
				p.val = str(value)
		except Exception as e:
			return {'ok': False, 'why': str(e)}
		self.SaveTool(canonical_name)
		return {'ok': True, 'val': self._jsonSafe(p.eval())}

	# --- Settings UI: console extensions (export / import / scope / picker) --
	# The page is a landing for the whole toolkit: besides settings it fronts
	# the FNS_Installer picker (proxied by settings_server_callbacks through
	# _installerComp) and moves whole config documents in and out. Install
	# changes WHAT is in the project; the config is a separate layer that
	# re-applies over any install, which is why removal keeps sections and
	# import works even for tools that are not installed yet.

	def _installerComp(self):
		"""The FNS_Installer COMP inside the toolkit root, if this project
		ships one. The console's Tools view degrades gracefully without it."""
		root = getattr(op, 'FNS', None)
		return root.op('FNS_Installer') if root is not None else None

	def UiExport(self, save=True):
		"""A portable config document snapshotted from the LIVE tools.

		Same shape as the roaming file, built fresh instead of read from
		disk so it is correct under project scope too (where the file is
		deliberately never written). With save=True (the page's default)
		the document is ALSO written beside the roaming file, under
		`exports/`, so an export never depends on whatever browser shows
		the console honouring a download -- the page still offers one."""
		api = self._registryApi()
		if api is not self:
			return api.UiExport(save=save)
		tools = {}
		for canonical, info in self.stored['PaneRegistry'].items():
			try:
				section = self._snapshotTool(canonical, dict(info))
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: export {canonical!r}: {e}')
				continue
			if section is not None:
				tools[canonical] = section
		doc = {'schema': self.SCHEMA,
			   'saved': time.strftime('%Y-%m-%dT%H:%M:%S'),
			   'saved_by': {'project': project.name, 'export': True},
			   'tools': tools}
		out = {'ok': True, 'document': doc, 'tools': len(tools)}
		if save:
			folder = os.path.join(os.path.dirname(self.ConfigPath), 'exports')
			path = os.path.join(
				folder, 'FNStools_config_%s.json' % time.strftime('%Y%m%d-%H%M%S')
			).replace('\\', '/')
			try:
				os.makedirs(folder, exist_ok=True)
				with open(path, 'w', encoding='utf-8') as f:
					json.dump(doc, f, indent=1)
				out['saved_to'] = path
			except Exception as e:
				out['save_error'] = str(e)
		return out

	def UiImport(self, data):
		"""Apply an exported/roamed config document from the page.

		Tools that are installed AND registered get the document's pars and
		state applied now; sections for anything else are merged into the
		roaming file so they land when that tool is next installed (the
		file's normal preserve-unknown-sections behavior). Under project
		scope the live apply still happens but the file stays untouched --
		the .toe is the store there."""
		api = self._registryApi()
		if api is not self:
			return api.UiImport(data)
		if not isinstance(data, dict) or data.get('schema') != self.SCHEMA:
			return {'ok': False,
					'why': 'not a schema-%s FNStools config document' % self.SCHEMA}
		sections = data.get('tools')
		if not isinstance(sections, dict) or not sections:
			return {'ok': False, 'why': 'document has no tool sections'}
		applied, deferred = [], []
		for canonical, section in sections.items():
			if not isinstance(section, dict):
				continue
			info = self.stored['PaneRegistry'].get(canonical)
			tool = self._resolvePanelOp(dict(info)) if info else None
			if tool is None:
				deferred.append(canonical)
				continue
			if info.get('persist_pars', '1') == '1':
				self._applyPars(tool, section.get('pars'), canonical)
			state = section.get('state')
			if state is not None:
				module = self._callbackModule(info)
				fn = getattr(module, 'onConfigLoad', None) if module is not None else None
				if callable(fn):
					try:
						fn(state)
					except Exception as e:
						debug(f'{self.REGISTRY_NAME}: import onConfigLoad '
							  f'{canonical!r}: {e}')
			applied.append(canonical)
		if not self._scopeIsProject():
			# merge not-installed sections first, then SaveAll snapshots the
			# live (just-applied) tools on top -- its read-merge-write keeps
			# the foreign sections we just planted
			if deferred:
				file_data = self._readFile()
				if file_data.get('schema') != self.SCHEMA:
					self._retireFile('.schema%s.bak' % file_data.get('schema'))
					file_data = self._freshData()
				file_tools = file_data.setdefault('tools', {})
				for canonical in deferred:
					file_tools[canonical] = sections[canonical]
				file_data['schema'] = self.SCHEMA
				file_data['saved'] = time.strftime('%Y-%m-%dT%H:%M:%S')
				file_data['saved_by'] = {'project': project.name, 'import': True}
				self._writeFile(file_data)
			self.SaveAll()
		self.fnsLog(f'{self.REGISTRY_NAME}: UiImport applied {len(applied)} '
					f'tool(s), deferred {len(deferred)} to next install')
		return {'ok': True, 'applied': sorted(applied),
				'deferred': sorted(deferred),
				'scope': 'project' if self._scopeIsProject() else 'global'}

	def UiScope(self, value=None, mode=None):
		"""Read or flip the config scope from the console.

		value None -> report only. 'project' flips quietly (no data moves;
		the .toe becomes the store). 'global' must say what happens to the
		machine-global file: mode 'push' overwrites it with this project's
		state, 'adopt' applies the global config onto this project -- the
		same three-way choice the in-TD dialog offers, decided explicitly
		by the page instead of a popup."""
		api = self._registryApi()
		if api is not self:
			return api.UiScope(value=value, mode=mode)
		if value is None:
			return {'ok': True,
					'scope': 'project' if self._scopeIsProject() else 'global'}
		value = str(value)
		if value == 'project':
			ok = self.SetConfigScope('project')
		elif value == 'global':
			if mode not in ('push', 'adopt'):
				return {'ok': False,
						'why': "flipping to global needs mode 'push' or 'adopt'"}
			ok = self.SetConfigScope('global')
			if ok:
				if mode == 'push':
					self.SaveAll()
				else:
					self.LoadAll()
		else:
			return {'ok': False, 'why': f'unknown scope: {value}'}
		return {'ok': bool(ok),
				'scope': 'project' if self._scopeIsProject() else 'global'}

	# --- Settings UI: ephemeral server lifecycle --------------------------
	# The server exists only while the page is in use: OpenSettingsUI
	# activates it on the first free UI_PORT, every request re-arms an idle
	# timer, and the timer deactivates it after UI_IDLE_SECONDS of silence.
	# Nothing listens when nobody is looking.

	SETTINGS_ASSETS = ('settings_page', 'settings_server_callbacks')

	def _ensureSettingsServer(self):
		"""The Web Server DAT that serves the settings page, created if absent.

		It lives HERE, on whichever copy owns the API -- in practice the
		/sys global, which `_registryApi()` has already routed us to. Not
		on the in-project master: hosts clone the master
		(`enablecloning`, see StampHost), so a server op there would
		replicate into every tool's host copy, and one settings page would
		become seven listening sockets. The global sheds its clone binding
		on promotion and owns itself, which is exactly the singleton this
		wants.

		Built in code, like _ensurePresaveHealPar, because it was not: an
		install carried the page and the callbacks with nothing to serve
		them, so OpenSettingsUI answered "no settings_server" and the
		settings UI was unreachable. A hand-made op can go missing again;
		one the registry re-creates on demand cannot -- and because it is
		re-created per session it never has to be saved into a package.

		A global promoted BEFORE the page existed carries no assets to
		serve (promotion is a comp copy, so a fresh one would have them);
		they are pulled from the master here rather than leaving the UI
		dead until the next promotion. Returns None when neither copy has
		a page."""
		comp = self.ownerComp
		master = self._masterComp()
		ws = comp.op('settings_server')
		if ws is None:
			ws = comp.create(webserverDAT, 'settings_server')
			ws.par.active = False        # OpenSettingsUI turns it on
			# create() spawns its OWN empty callbacks DAT, named for the
			# server. Destroy it before the assets land: left alone it
			# squats on settings_server_callbacks, and the copy below --
			# which only fills in what is missing -- would then leave the
			# server wired to an empty stub that answers nothing.
			auto = ws.par.callbacks.eval()
			if auto is not None and auto is not master:
				try:
					if auto.name.startswith('settings_server_callbacks'):
						auto.destroy()
				except Exception:
					pass
		# Pull the assets, replacing anything empty: a stub left by an
		# earlier run must not win over the real page or callbacks.
		for name in self.SETTINGS_ASSETS:
			src = master.op(name) if (master is not None and master.valid) else None
			if src is None:
				continue
			local = comp.op(name)
			if local is not None and local.text.strip():
				continue
			if local is not None:
				local.destroy()
			comp.copy(src, name=name)
		page = comp.op('settings_page')
		if page is None:
			return None
		if not ws.nodeX and not ws.nodeY:
			ws.nodeX, ws.nodeY = page.nodeX, page.nodeY - 150
		cb = comp.op('settings_server_callbacks')
		if cb is not None:
			ws.par.callbacks = cb
		return ws

	def OpenSettingsUI(self, tab=None, panel=True):
		"""Serve the FNS console and show it.

		tab: 'settings' (default) or 'tools' -- the console opens on that
		tab via the URL fragment. panel (default True) shows it in the
		toolkit root's webBrowser panel when the root has one -- the same
		in-TD surface the installer's picker uses, and it handles the
		console fully, file dialog included; a root without the panel, or
		panel=False, opens the system browser."""
		api = self._registryApi()
		if api is not self:
			return api.OpenSettingsUI(tab=tab, panel=panel)
		ws = self._ensureSettingsServer()
		if ws is None:
			return {'ok': False,
					'why': f'no settings_page in {self.ownerComp.path}'}
		if not ws.par.active.eval():
			port = self._freeUiPort()
			if port is None:
				return {'ok': False, 'why': f'no free port in {self.UI_PORTS}'}
			ws.par.port = port
			ws.par.active = True
		self._touchSettingsServer()
		url = f'http://127.0.0.1:{int(ws.par.port.eval())}/'
		if tab and str(tab) != 'settings':
			url += '#' + str(tab)
		self._showUrl(url, panel)
		return {'ok': True, 'url': url, 'panel': panel}

	def _showUrl(self, url, panel):
		"""Where a console URL gets displayed: the toolkit root's webBrowser
		panel when asked for AND present, else the system browser."""
		if panel:
			root = getattr(op, 'FNS', None)
			browser = root.op('webBrowser') if root is not None else None
			if browser is not None:
				browser.par.Address = url
				browser.openViewer()
				return 'panel'
		import webbrowser
		webbrowser.open(url)
		return 'browser'

	def CloseSettingsUI(self):
		api = self._registryApi()
		if api is not self:
			return api.CloseSettingsUI()
		ws = self.ownerComp.op('settings_server')
		if ws is not None:
			ws.par.active = False
		return {'ok': True}

	def _freeUiPort(self):
		import socket
		for port in self.UI_PORTS:
			s = socket.socket()
			try:
				s.bind(('127.0.0.1', port))
				s.close()
				return port
			except OSError:
				s.close()
		return None

	def _touchSettingsServer(self):
		self._ui_last_request = absTime.seconds
		self._armSettingsTick()

	def _armSettingsTick(self):
		# re-arming must NOT refresh _ui_last_request, or idle never elapses
		if getattr(self, '_ui_timer_armed', False):
			return
		self._ui_timer_armed = True
		run(
			"args[0].valid and args[0].extensionsReady and "
			f"args[0].ext.{self.EXT_NAME}._settingsIdleTick()",
			self.ownerComp,
			delayFrames=self.UI_TICK_FRAMES,
			delayRef=op.TDResources,
		)

	def _settingsIdleTick(self):
		self._ui_timer_armed = False
		ws = self.ownerComp.op('settings_server')
		if ws is None or not ws.par.active.eval():
			return
		if absTime.seconds - getattr(self, '_ui_last_request', 0) >= self.UI_IDLE_SECONDS:
			ws.par.active = False
			debug(f'{self.REGISTRY_NAME}: settings server idle, stopped')
			return
		self._armSettingsTick()

	def _queueApply(self, canonical_name):
		"""Deferred once-per-session apply, scheduled at registration. The
		delay puts it after clone sync, the tool's own extension init, and
		the Registry-page bind wiring."""
		if canonical_name in self._applied_this_session:
			return
		self._applied_this_session.add(canonical_name)
		run(f"args[0].valid and args[0].extensionsReady and "
			f"args[0].ext.{self.EXT_NAME}._applyToolConfig(args[1])",
			self.ownerComp, canonical_name,
			delayFrames=30, delayRef=op.TDResources)

	def _applyToolConfig(self, canonical_name):
		"""Apply pars, then hand state to the tool's onConfigLoad."""
		self._applied_this_session.add(canonical_name)
		if self._scopeIsProject():
			# .toe state stands; log the skip once per session, not per tool
			if not getattr(self, '_scope_skip_logged', False):
				self._scope_skip_logged = True
				self.fnsLog(f'{self.REGISTRY_NAME}: project scope -- roamed '
							f'config not applied (.toe state stands)')
			return False
		info = self.stored['PaneRegistry'].get(canonical_name)
		if not info:
			return False
		tool = self._resolvePanelOp(info)
		if tool is None:
			debug(f'{self.REGISTRY_NAME}: load {canonical_name!r}: tool COMP gone')
			return False
		section = (self.ConfigData.get('tools') or {}).get(canonical_name)
		if not section:
			return False
		if info.get('persist_pars', '1') == '1':
			self._applyPars(tool, section.get('pars'), canonical_name)
		state = section.get('state')
		if state is not None:
			module = self._callbackModule(info)
			fn = getattr(module, 'onConfigLoad', None) if module is not None else None
			if callable(fn):
				try:
					fn(state)
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: onConfigLoad from {canonical_name!r}: {e}')
		return True

	# --- public API ---

	def RegisterTool(self, comp, canonical_name, callback=None, autoload=True,
					 persist_pars=True, exclude_pars='', exclude_pages='',
					 source_registry=None):
		"""Publish a tool COMP for settings persistence under canonical_name."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterTool(
					comp, canonical_name, callback=callback, autoload=autoload,
					persist_pars=persist_pars, exclude_pars=exclude_pars,
					exclude_pages=exclude_pages, source_registry=source_registry)
			debug(f'{self.REGISTRY_NAME}: RegisterTool ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		err = self._validateTool(comp, callback)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterTool({canonical_name!r}) rejected: {err}')
			return
		entry = {
			'panel_path': comp.path,
			'panel_id': int(comp.id),
			'autoload': '1' if autoload else '0',
			'persist_pars': '1' if persist_pars else '0',
			'exclude_pars': str(exclude_pars or ''),
			'exclude_pages': str(exclude_pages or ''),
		}
		if callback is not None:
			entry['callback_path'] = callback.path
			entry['callback_id'] = int(callback.id)
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		self.stored['PaneRegistry'][canonical_name] = entry
		self.fnsLog(f'{self.REGISTRY_NAME}: registered tool "{canonical_name}" ({comp.path})')
		if autoload:
			self._queueApply(canonical_name)

	def UnregisterTool(self, canonical_name):
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterTool(canonical_name)
			debug(f'{self.REGISTRY_NAME}: UnregisterTool ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		self.stored['PaneRegistry'].pop(canonical_name, None)

	# RegistryBase healing calls self.UnregisterPanel(name); alias it.
	def UnregisterPanel(self, canonical_name):
		return self.UnregisterTool(canonical_name)

	@property
	def Tools(self):
		"""Manager API: snapshot of all registered tool entries."""
		api = self._registryApi()
		if api is not self:
			return api.Tools
		return {k: dict(v) for k, v in self.stored['PaneRegistry'].items()}

	def _validateTool(self, comp, callback):
		if comp is None:
			return 'No COMP selected'
		if comp.family != 'COMP':
			return f'{comp.path} is not a COMP'
		if callback is not None and not callback.isDAT:
			return f'{callback.path} is not a DAT'
		return None

	# --- host registration (Registration page), config flavor ---

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
		err = self._validateTool(comp, callback) or (
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
		api.RegisterTool(
			comp, canonical,
			callback=callback,
			autoload=self._parBool('Autoload', True),
			persist_pars=self._parBool('Persistpars', True),
			exclude_pars=self._parStr('Excludepars'),
			exclude_pages=self._parStr('Excludepages'),
			source_registry=self.ownerComp,
		)
		self.stored['HostCanonical'] = canonical
		self._setRegStatus(f'Registered: {canonical} -> {comp.path}')
		self._ensureToolRegistryPage()

	def _parStr(self, name):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return ''
		try:
			return str(p.eval()).strip()
		except Exception:
			return ''

	# --- callbacks DAT bootstrap ---

	def CreateCallbacks(self):
		"""Spawn a `config_callbacks` DAT into this host's tool and point the
		host's Callback parameter at it. Idempotent -- an existing DAT is
		adopted, never overwritten."""
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
			# The template may be bound to the registry's own source file. A
			# copy inherits that binding, so without this every tool's
			# callbacks would read from -- and save over -- the shared template.
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

	# --- CustomParHelper callbacks ---

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

	def onParCallback(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParAutoload(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParPersistpars(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParExcludepars(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParExcludepages(self, _par, _val, _prev):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParSaveall(self, _par):
		self._hostExtFromPar(_par).SaveAll()

	def onParLoadall(self, _par):
		self._hostExtFromPar(_par).LoadAll()

	### FNS_CommandRegistry (quick-launch commands) ###
	# Registered only by the ACTIVE /sys global - this class runs in every
	# host/shipper instance, and one palette row set is enough.

	@fns_command(label='Save all tool configs')
	def SaveAllConfigs(self):
		"""Save every registered tool's config."""
		self.SaveAll()
		return {'ok': True}

	@fns_command(label='Load all tool configs', hidden=True)
	def LoadAllConfigs(self):
		"""Load every registered tool's config."""
		self.LoadAll()
		return {'ok': True}

	@fns_command(label='Open FNS settings')
	def OpenConfigSettings(self):
		"""Open the FNS_Config settings UI."""
		self.OpenSettingsUI()
		return {'ok': True}

	def _isCommandOwner(self):
		return self.ownerComp is getattr(op, 'FNS_CONFIGREGISTRY', None)

	def onInitTD(self):
		run('args[0]._announceCommands()', self, delayFrames=60)

	def _announceCommands(self):
		if self._isCommandOwner():
			fns_announce(self.ownerComp)

	def onDestroyTD(self):
		super().onDestroyTD()
		try:
			if self._isCommandOwner():
				reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
				if reg is not None and hasattr(reg, 'Unregister'):
					reg.Unregister(self.ownerComp.path)
		except Exception:
			pass

