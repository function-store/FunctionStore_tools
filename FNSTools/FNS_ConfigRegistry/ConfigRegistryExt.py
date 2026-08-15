

CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase

import json
import os
import time


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
		return {'tools': tools, 'config_path': self.ConfigPath,
				'project': project.name}

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

	# --- Settings UI: ephemeral server lifecycle --------------------------
	# The server exists only while the page is in use: OpenSettingsUI
	# activates it on the first free UI_PORT, every request re-arms an idle
	# timer, and the timer deactivates it after UI_IDLE_SECONDS of silence.
	# Nothing listens when nobody is looking.

	def OpenSettingsUI(self):
		api = self._registryApi()
		if api is not self:
			return api.OpenSettingsUI()
		ws = self.ownerComp.op('settings_server')
		if ws is None:
			return {'ok': False,
					'why': f'no settings_server on {self.ownerComp.path}'}
		if not ws.par.active.eval():
			port = self._freeUiPort()
			if port is None:
				return {'ok': False, 'why': f'no free port in {self.UI_PORTS}'}
			ws.par.port = port
			ws.par.active = True
		self._touchSettingsServer()
		url = f'http://127.0.0.1:{int(ws.par.port.eval())}/'
		import webbrowser
		webbrowser.open(url)
		return {'ok': True, 'url': url}

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
