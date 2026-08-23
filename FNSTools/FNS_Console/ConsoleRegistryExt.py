CustomParHelper: CustomParHelper = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or me.parent().op('ExtUtils')).mod('CustomParHelper').CustomParHelper # import
###

RegistryBase = mod('RegistryBase').RegistryBase

import json


class ConsoleRegistryExt(RegistryBase):
	"""The FNS console: the toolkit's web front, as its own /sys service.

	One ephemeral Web Server DAT on the /sys global serves one page --
	Settings (every installed tool's persisted parameters, config
	export/import, global/project scope) and Install & remove (the
	FNS_Installer picker) -- and routes each request to the subsystem
	that owns it: the config registry's Ui* API, the installer's
	ServeRequest, or a tool's own tab. The console holds no tool
	knowledge of its own; it is the hub, not an owner.

	Tabs are CONTRIBUTIONS, like every other surface in the toolkit. A
	tool carries a stamped FNS_Console host whose Registration pars name
	a page DAT (served verbatim in an iframe under /t/<canonical>/) and an
	optional api DAT whose onConsoleRequest(action, method, body) answers
	/t/<canonical>/api/<action> with JSON-able data. Settings and Install
	& remove are built in, not registrations. What a tool contributes is
	a web re-expression of what it owns (tables, parameters, state) --
	never a TD panel; a browser cannot host one.

	Nothing about the server is ever saved: /sys is rebuilt every open,
	the DAT is created on demand, activated by Open, and deactivated
	after UI_IDLE_SECONDS of silence. Several open projects each run
	their own console on the first free port of UI_PORTS.
	"""

	SHORTCUT = 'FNS_CONSOLE'
	EXT_NAME = 'ConsoleRegistryExt'
	REGISTRY_NAME = 'FNS_Console'

	# Standardized 'Registry' page on the parent tool (see RegistryBase).
	TOOL_PAGE_PREFIX = 'Cs'
	TOOL_PAGE_LABEL = 'Console'
	# Autoregister is this registry's "expose to the console" switch (off =
	# the tool runs only its own local interface); Displayed is the console-
	# side show/hide the tab manager writes back to, so it persists with the
	# tool and roams with its Registry page.
	TOOL_PAGE_PARS = ('Autoregister', 'Register', 'Regstatus', 'Displayed',
					  'Tablabel', 'Taborder')

	# Location-independent: resolves through the toolkit root's global
	# shortcut, evaluates to None (no clone, no warning) where it is absent.
	CLONE_EXPR = "op.FNS.op('FNS_Console') if hasattr(op, 'FNS') else None"

	# A deliberately uncommon block: the 8xxx/9xxx dev-server range is
	# crowded, and a bind failure there is hard to tell from a toolkit bug.
	# Fifty wide because Windows reserves ~16-port ranges for Hyper-V/WSL at
	# semi-random places; the installer's picker sits just above (36760+).
	UI_PORTS = tuple(range(36710, 36760))
	UI_IDLE_SECONDS = 600
	UI_TICK_FRAMES = 1800

	SERVER_NAME = 'console_server'
	PAGE_NAME = 'console_page'
	CALLBACKS_NAME = 'console_server_callbacks'
	# assets the global must carry to serve anything; pulled from the master
	# when a promoted copy predates them
	CONSOLE_ASSETS = (PAGE_NAME, CALLBACKS_NAME)

	BUILTIN_TABS = (
		{'name': 'settings', 'label': 'Settings', 'order': 0, 'builtin': True},
		{'name': 'tools', 'label': 'Install & remove', 'order': 10, 'builtin': True},
	)

	# --- surface hooks (RegistryBase contract; the surface is the server) ---

	def _preInit(self):
		self._ui_timer_armed = False
		# A reinit counts as activity: a zero stamp here made the first idle
		# tick after a hot-reload read "idle for ages" and stop a live server.
		self._ui_last_request = absTime.seconds

	def _syncSurface(self, attempts=40):
		"""Keep one dormant server on the global, and retire the one the
		config registry served the page from before this service existed."""
		self._pane_sync_queued = False
		if not self._is_sys_global():
			return
		ws = self._ensureServer()
		self._retireLegacyServer()
		# a reinit dropped the armed tick; a server left serving must get
		# its idle watchdog back or it never stops
		if ws is not None and ws.par.active.eval():
			self._armTick()

	def _retireLegacyServer(self):
		"""FNS_ConfigRegistry used to serve the settings page from its own
		/sys copy. A global promoted from an older master may still hold
		that server; two listeners for one page is one too many."""
		reg = getattr(op, 'FNS_CONFIGREGISTRY', None)
		if reg is None or not reg.valid:
			return
		old = reg.op('settings_server')
		if old is None:
			return
		try:
			old.par.active = False
			old.destroy()
			self.fnsLog(f'{self.REGISTRY_NAME}: retired the config registry\'s own settings server')
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: retiring legacy settings_server: {e}')

	# --- host registration (a host = one contributed tab) ---

	def _parStr(self, name):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return ''
		try:
			return str(p.eval()).strip()
		except Exception:
			return ''

	def _parInt(self, name, default=0):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return default
		try:
			return int(p.eval())
		except Exception:
			return default

	def _parDat(self, name):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return None
		try:
			dat = p.eval()
		except Exception:
			return None
		return dat if (dat is not None and dat.valid and dat.family == 'DAT') else None

	def _validateTab(self, comp, canonical, page):
		if comp is None:
			return 'no tool COMP'
		if not canonical:
			return 'empty canonical name'
		if not canonical.replace('_', '').replace('-', '').isalnum():
			return 'canonical name must be URL-safe (letters, digits, _ -)'
		if canonical in {t['name'] for t in self.BUILTIN_TABS}:
			return f'{canonical!r} is a built-in tab'
		if page is None:
			return 'no tab page DAT (set Tab Page)'
		if not hasattr(page, 'text'):
			return 'tab page is not a text DAT'
		return ''

	# --- the tool's own browser: off while the console serves the page ---
	# A tool whose panel is a Web Render of the same page (ColorUI) names it
	# on the host's Local Browser par. Exposed = the console is the UI, so
	# that renderer would burn a CEF process and a texture for nobody; the
	# host switches its Active off when it publishes and back on when the
	# exposure ends -- Expose off, a failed registration, or the host going
	# away. Compare-before-set, so nothing flickers on a plain re-apply.

	def _localBrowserActivePar(self):
		p = getattr(self.ownerComp.par, 'Localbrowser', None)
		if p is None:
			return None
		try:
			comp = p.eval()
		except Exception:
			return None
		if comp is None or not getattr(comp, 'valid', False):
			return None
		return getattr(comp.par, 'Active', None)

	def _toolExposureHook(self, tool=None):
		"""A tool that manages its own renderer implements
		OnConsoleExposure(exposed) on its extension; the host then hands the
		decision over instead of flipping Active itself."""
		tool = tool or self._hostComp()
		if tool is None or not getattr(tool, 'valid', False):
			return None
		try:
			exts = tool.extensions
		except Exception:
			exts = []
		for ext in exts or []:
			fn = getattr(ext, 'OnConsoleExposure', None)
			if callable(fn):
				return fn
		return None

	def _setLocalBrowser(self, on):
		p = self._localBrowserActivePar()
		if p is None:
			return
		hook = self._toolExposureHook()
		if hook is not None:
			try:
				self._local_browser_owner = p.owner.path
				hook(not on)
			except Exception as e:
				debug(f'{self.REGISTRY_NAME}: OnConsoleExposure hook: {e}')
			return
		try:
			if bool(p.eval()) != bool(on):
				p.val = bool(on)
				self.fnsLog(f'{self.REGISTRY_NAME}: {self._hostCanonicalName()!r} local '
							f'browser {"on (local mode)" if on else "off (served by the console)"}')
			# remembered by path so a destroyed host can still hand the
			# browser back to the tool
			self._local_browser_owner = p.owner.path
		except Exception as e:
			debug(f'{self.REGISTRY_NAME}: local browser switch: {e}')

	def onDestroyTD(self):
		super().onDestroyTD()
		# onDestroyTD also fires on a plain reinit, where the owner is still
		# valid and postInit will re-apply -- only a real destruction hands
		# the browser back here
		if not self.ownerComp.valid:
			path = getattr(self, '_local_browser_owner', None)
			comp = op(path) if path else None
			if comp is None:
				return
			hook = self._toolExposureHook(comp.parent())
			if hook is not None:
				try:
					hook(False)
				except Exception:
					pass
				return
			p = getattr(comp.par, 'Active', None)
			if p is not None:
				try:
					p.val = True
				except Exception:
					pass

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
			self._setLocalBrowser(True)
			self._setRegStatus('Idle')
			return
		comp = self._hostComp()
		canonical = self._hostCanonicalName()
		page = self._parDat('Tabpage')
		api_dat = self._parDat('Tabapi')
		err = self._validateTab(comp, canonical, page)
		if err:
			if not force:
				self._clearHostRegistration()
			self._setLocalBrowser(True)   # not served: the tool keeps its own UI
			self._setRegStatus(f'Error: {err}')
			return
		prev = self.stored['HostCanonical']
		api = self._registryApi()
		if prev and prev != canonical:
			self._unregisterOwnedMenuName(prev, api=api)
		api.RegisterTab(
			comp, canonical, page=page, api_dat=api_dat,
			label=self._parStr('Tablabel') or canonical,
			order=self._parInt('Taborder', 50),
			displayed=self._parBool('Displayed', True),
			source_registry=self.ownerComp,
		)
		self.stored['HostCanonical'] = canonical
		self._setLocalBrowser(False)      # the console serves it from here on
		self._setRegStatus(f'Registered: {canonical} -> {page.path}')
		self._ensureToolRegistryPage()

	# --- public API (global only; hosts forward) ---

	def RegisterTab(self, comp, canonical, page=None, api_dat=None, label='',
					order=50, displayed=True, source_registry=None):
		"""Publish a tab: `page` (text DAT) is served as-is under
		/t/<canonical>/; `api_dat` (optional) answers /t/<canonical>/api/*
		through its onConsoleRequest(action, method, body). `displayed`
		False registers the tab hidden -- it stays in the tab manager,
		off the bar -- until someone shows it."""
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.RegisterTab(comp, canonical, page=page, api_dat=api_dat,
									   label=label, order=order, displayed=displayed,
									   source_registry=source_registry)
			debug(f'{self.REGISTRY_NAME}: RegisterTab ignored on {self.ownerComp.path}'
				  f' -- no global /sys registry ready')
			return
		err = self._validateTab(comp, canonical, page)
		if err:
			debug(f'{self.REGISTRY_NAME}: RegisterTab({canonical!r}) rejected: {err}')
			return
		entry = {
			'panel_path': comp.path,
			'panel_id': int(comp.id),
			'page_path': page.path,
			'page_id': int(page.id),
			'label': str(label or canonical),
			'order': str(int(order)),
			'displayed': '1' if displayed else '0',
		}
		if api_dat is not None:
			entry['api_path'] = api_dat.path
			entry['api_id'] = int(api_dat.id)
		if source_registry is not None:
			entry['source_registry'] = source_registry.path
			entry['source_registry_id'] = int(source_registry.id)
		self.stored['PaneRegistry'][canonical] = entry
		self.fnsLog(f'{self.REGISTRY_NAME}: registered tab "{canonical}" ({page.path})')

	def UnregisterTab(self, canonical):
		if not self._is_sys_global():
			api = self._registryApi()
			if api is not self:
				return api.UnregisterTab(canonical)
			return
		if canonical in self.stored['PaneRegistry']:
			del self.stored['PaneRegistry'][canonical]
			self.fnsLog(f'{self.REGISTRY_NAME}: unregistered tab "{canonical}"')

	# RegistryBase's host teardown calls this name on the API owner.
	UnregisterPanel = UnregisterTab

	def Tabs(self, include_hidden=False):
		"""Every tab, in order: the built-ins (always displayed), then the
		live contributions (a registration whose page DAT is gone is
		skipped, never shown broken). Hidden contributions are left out
		unless include_hidden -- the tab manager asks for everything, the
		bar for what to show."""
		api = self._registryApi()
		if api is not self:
			return api.Tabs(include_hidden=include_hidden)
		out = [dict(t, displayed=True) for t in self.BUILTIN_TABS]
		for canonical, info in self.stored['PaneRegistry'].items():
			info = dict(info)
			page = self._resolveByIdOrPath(info.get('page_id'), info.get('page_path'))
			if page is None:
				continue
			displayed = str(info.get('displayed', '1')) != '0'
			if not displayed and not include_hidden:
				continue
			out.append({
				'name': canonical,
				'label': info.get('label') or canonical,
				'order': int(info.get('order', 50)),
				'builtin': False,
				'displayed': displayed,
				'url': f'/t/{canonical}/',
				'api': bool(info.get('api_path')),
				'source': info.get('panel_path'),
			})
		out.sort(key=lambda t: (t['order'], str(t['label']).lower()))
		return out

	def SetTabDisplayed(self, canonical, displayed):
		"""Show or hide a contributed tab. The entry flips now, and the
		decision is written back to the contributing host's Displayed par
		(compare-before-set, so no callback storm) -- that par is what
		persists with the tool and roams with its Registry page, exactly
		like a toolbar widget's Displayed. Built-ins cannot be hidden."""
		api = self._registryApi()
		if api is not self:
			return api.SetTabDisplayed(canonical, displayed)
		if canonical in {t['name'] for t in self.BUILTIN_TABS}:
			return {'ok': False, 'why': f'{canonical!r} is a built-in tab'}
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return {'ok': False, 'why': f'no tab: {canonical}'}
		displayed = bool(displayed)
		entry = dict(info)
		entry['displayed'] = '1' if displayed else '0'
		self.stored['PaneRegistry'][canonical] = entry
		wrote_host = False
		src = self._resolveSourceRegistry(entry)
		if src is not None:
			p = getattr(src.par, 'Displayed', None)
			if p is not None:
				try:
					if bool(p.eval()) != displayed:
						p.val = displayed
					wrote_host = True
				except Exception as e:
					debug(f'{self.REGISTRY_NAME}: Displayed write-back {src.path}: {e}')
		self.fnsLog(f'{self.REGISTRY_NAME}: tab "{canonical}" '
					f'{"shown" if displayed else "hidden"}')
		return {'ok': True, 'name': canonical, 'displayed': displayed,
				'persisted': wrote_host}

	def ServeTab(self, canonical, subpath='', method='GET', body=None):
		"""Answer one request under /t/<canonical>/: '' -> the page,
		'api/<action>' -> the api DAT. Returns {'status', 'html'|'json'}."""
		api = self._registryApi()
		if api is not self:
			return api.ServeTab(canonical, subpath=subpath, method=method, body=body)
		info = self.stored['PaneRegistry'].get(canonical)
		if not info:
			return {'status': 404, 'json': {'ok': False, 'why': f'no tab: {canonical}'}}
		info = dict(info)
		if not subpath:
			page = self._resolveByIdOrPath(info.get('page_id'), info.get('page_path'))
			if page is None:
				return {'status': 404, 'json': {'ok': False, 'why': 'tab page DAT is gone'}}
			return {'status': 200, 'html': page.text}
		if subpath.startswith('api/'):
			dat = None
			if info.get('api_path'):
				dat = self._resolveByIdOrPath(info.get('api_id'), info.get('api_path'))
			if dat is None:
				return {'status': 404, 'json': {'ok': False, 'why': 'tab has no api DAT'}}
			try:
				fn = getattr(dat.module, 'onConsoleRequest', None)
			except Exception as e:
				return {'status': 500, 'json': {'ok': False, 'why': f'api DAT failed to compile: {e}'}}
			if not callable(fn):
				return {'status': 404, 'json': {'ok': False, 'why': 'api DAT defines no onConsoleRequest'}}
			try:
				result = fn(subpath[4:], method, body)
			except Exception as e:
				return {'status': 500, 'json': {'ok': False, 'why': str(e)}}
			return {'status': 200, 'json': result if result is not None else {'ok': True}}
		return {'status': 404, 'json': {'ok': False, 'why': f'not found: {subpath}'}}

	# --- the subsystems the console fronts ---

	def _configRegistry(self):
		"""FNS_ConfigRegistry's API owner, or None where the config package
		is not installed (the Settings tab then says so)."""
		reg = getattr(op, 'FNS_CONFIGREGISTRY', None)
		if reg is None or not reg.valid or not reg.extensionsReady:
			return None
		return getattr(reg.ext, 'ConfigRegistryExt', None)

	def _installerComp(self):
		root = getattr(op, 'FNS', None)
		return root.op('FNS_Installer') if root is not None else None

	def _installerExt(self):
		comp = self._installerComp()
		if comp is None or not comp.extensionsReady:
			return None
		return getattr(comp.ext, 'InstallerExt', None)

	# --- the ephemeral server ---

	def _ensureServer(self):
		"""The Web Server DAT, created on the API owner (the /sys global)
		if absent. Never on the in-project master: hosts clone the master,
		and a server there would replicate into every tool. A global
		promoted before an asset existed pulls it from the master."""
		comp = self.ownerComp
		master = self._masterComp()
		ws = comp.op(self.SERVER_NAME)
		if ws is None:
			ws = comp.create(webserverDAT, self.SERVER_NAME)
			ws.par.active = False        # Open turns it on
			# create() spawns its OWN empty callbacks DAT, named for the
			# server; left alone it squats on the real callbacks' name.
			auto = ws.par.callbacks.eval()
			if auto is not None:
				try:
					if auto.name.startswith(self.CALLBACKS_NAME):
						auto.destroy()
				except Exception:
					pass
		for name in self.CONSOLE_ASSETS:
			src = master.op(name) if (master is not None and master.valid) else None
			if src is None:
				continue
			local = comp.op(name)
			if local is not None and local.text.strip():
				continue
			if local is not None:
				local.destroy()
			comp.copy(src, name=name)
		page = comp.op(self.PAGE_NAME)
		if page is None:
			return None
		if not ws.nodeX and not ws.nodeY:
			ws.nodeX, ws.nodeY = page.nodeX, page.nodeY - 150
		cb = comp.op(self.CALLBACKS_NAME)
		if cb is not None and ws.par.callbacks.eval() is not cb:
			ws.par.callbacks = cb.name
		return ws

	def _freeUiPort(self):
		import socket
		for port in self.UI_PORTS:
			s = socket.socket()
			try:
				s.bind(('127.0.0.1', port))
				return port
			except OSError:
				continue
			finally:
				s.close()
		return None

	def Open(self, tab=None, panel=True):
		"""Serve the console and show it.

		tab: 'settings' (default), 'tools', or a contributed tab's
		canonical name -- the page opens there via the URL fragment.
		panel (default True) shows it in the toolkit root's webBrowser
		panel when the root has one -- the same in-TD surface the
		installer's picker uses, and it handles the console fully, file
		dialog included; a root without the panel, or panel=False, opens
		the system browser."""
		api = self._registryApi()
		if api is not self:
			return api.Open(tab=tab, panel=panel)
		ws = self._ensureServer()
		if ws is None:
			return {'ok': False, 'why': f'no {self.PAGE_NAME} in {self.ownerComp.path}'}
		if not ws.par.active.eval():
			port = self._freeUiPort()
			if port is None:
				return {'ok': False,
						'why': f'no free port in {self.UI_PORTS[0]}-{self.UI_PORTS[-1]}'}
			ws.par.port = port
			ws.par.active = True
		self._touchServer()
		url = f'http://127.0.0.1:{int(ws.par.port.eval())}/'
		if tab:
			tab = str(tab)
			if tab in ('tools',):
				url += '#tools'
			elif tab != 'settings':
				url += '#t-' + tab
		shown = self._showUrl(url, panel)
		return {'ok': True, 'url': url, 'shown': shown}

	def Serve(self, tab=None):
		"""Make sure the console is being served and return its URL (with
		the tab fragment when given) -- WITHOUT showing it anywhere. The hub
		calls this as its Console tab is exposed, so picking the tab never
		lands on a dead 127.0.0.1. None when no server can be started."""
		api = self._registryApi()
		if api is not self:
			return api.Serve(tab=tab)
		ws = self._ensureServer()
		if ws is None:
			return None
		if not ws.par.active.eval():
			port = self._freeUiPort()
			if port is None:
				return None
			ws.par.port = port
			ws.par.active = True
		self._touchServer()
		url = f'http://127.0.0.1:{int(ws.par.port.eval())}/'
		if tab:
			tab = str(tab)
			if tab in ('tools',):
				url += '#tools'
			elif tab != 'settings':
				url += '#t-' + tab
		return url

	def Close(self):
		api = self._registryApi()
		if api is not self:
			return api.Close()
		ws = self.ownerComp.op(self.SERVER_NAME)
		if ws is not None:
			ws.par.active = False
		return {'ok': True}

	def Url(self):
		"""The console's URL if it is serving right now, else None."""
		api = self._registryApi()
		if api is not self:
			return api.Url()
		ws = self.ownerComp.op(self.SERVER_NAME)
		if ws is None or not ws.par.active.eval():
			return None
		return f'http://127.0.0.1:{int(ws.par.port.eval())}/'

	def _showUrl(self, url, panel):
		"""Where a console URL gets displayed: the hub's Console tab when
		FNS_Hub is installed (the root's webBrowser registered as a hub tab),
		else the root's webBrowser viewer when asked for AND present, else
		the system browser."""
		if panel:
			root = getattr(op, 'FNS', None)
			browser = root.op('webBrowser') if root is not None else None
			if browser is not None:
				hubreg = getattr(op, 'FNS_HUBREGISTRY', None)
				try:
					in_hub = hubreg is not None and any(
						t.get('name') == 'console' for t in hubreg.Tabs(include_hidden=True))
				except Exception:
					in_hub = False
				if in_hub:
					# the hub switches the renderer on as the tab is shown
					browser.par.Address = url
					res = hubreg.Open(tab='console')
					if isinstance(res, dict) and res.get('ok'):
						return 'hub'
				# the rail's browser is dormant until opened (its winopen
				# watcher keeps it that way); switch it on first so the page
				# starts loading as the viewer appears
				act = getattr(browser.par, 'Active', None)
				if act is not None and not act.eval():
					act.val = True
				browser.par.Address = url
				browser.openViewer()
				return 'panel'
		import webbrowser
		webbrowser.open(url)
		return 'browser'

	def _touchServer(self):
		self._ui_last_request = absTime.seconds
		self._armTick()

	def _armTick(self):
		# re-arming must NOT refresh _ui_last_request, or idle never elapses
		if getattr(self, '_ui_timer_armed', False):
			return
		self._ui_timer_armed = True
		run(
			"args[0].valid and args[0].extensionsReady and "
			f"args[0].ext.{self.EXT_NAME}._idleTick()",
			self.ownerComp,
			delayFrames=self.UI_TICK_FRAMES,
			delayRef=op.TDResources,
		)

	def _idleTick(self):
		self._ui_timer_armed = False
		ws = self.ownerComp.op(self.SERVER_NAME)
		if ws is None or not ws.par.active.eval():
			return
		if absTime.seconds - getattr(self, '_ui_last_request', 0) >= self.UI_IDLE_SECONDS:
			ws.par.active = False
			debug(f'{self.REGISTRY_NAME}: console idle, server stopped')
			return
		self._armTick()

	# --- host par callbacks (CustomParHelper: pulses get (_par), values
	# get (_par, _val, _prev); the owner is resolved THROUGH the par because
	# a shipped host plus the /sys global share one class-level EXT_SELF) ---

	def _reapply(self, _par):
		ext = self._hostExtFromPar(_par)
		if ext._isAutoRegister():
			ext._applyHostRegistration()

	def onParRegister(self, _par):
		self._hostExtFromPar(_par)._applyHostRegistration(force=True)

	def onParAutoregister(self, _par, _val, _prev):
		self._hostExtFromPar(_par)._applyHostRegistration()

	def onParCanonicalname(self, _par, _val, _prev):
		self._reapply(_par)

	def onParComp(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTabpage(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTabapi(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTablabel(self, _par, _val, _prev):
		self._reapply(_par)

	def onParTaborder(self, _par, _val, _prev):
		self._reapply(_par)

	def onParDisplayed(self, _par, _val, _prev):
		self._reapply(_par)

	def onParOpen(self, _par):
		self._hostExtFromPar(_par).Open()
