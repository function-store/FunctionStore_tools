"""FNS_CMS -- the authoring cockpit. Dev tooling, never shipped.

One local page over the release motions: PI publishing (dirty lister,
per-package Save, Preflight, Stage), entitlement authoring
(gate_package: tiers/Gumroad, both files in one motion), and the package
roster (live versions, help URLs, the rare FNS_About.Helpurl override,
doc stubs). ZERO OWNED STATE: every action reads or writes the repo's
files or calls Private Investigator's live API -- the files stay the
source of truth, this component is only the pen
(docs/CmsResearch.md, briefs/2026-08-28-fns-cms.md).

Placement contract: lives at the project ROOT beside
/private_investigator1 -- outside /FNSTools so Packages() can never see
it, per docs/ExternalizationOwnership.md. Being its own PI-tracked
component (instead of UI stamped INTO PI, which reverts on project open
because PI cannot track itself) is the point.

The server is the console pattern: loopback-pinned ALWAYS, ephemeral
(idle shutdown), port pool 36770-36779. Handlers run on TD's main
thread: everything here is a par read, a PI call, or a short file op --
Stage() hashes for a few seconds and is a deliberate button press, the
same cost the PI lister's cloud button already pays. Nothing here does
network I/O in-process (upload and check_pins stay shell commands the
Publish tab prints).
"""

import json
import os
import time
from urllib.parse import urlparse, parse_qs

IDLE_SECONDS = 600
PORT_POOL = tuple(range(36770, 36780))
# Blank Local Address = every interface (Derivative docs). This page can
# save suspects and stage releases with no auth, so it must never leave
# this machine. Re-asserted on every Open, not only at create.
BIND_ADDRESS = '127.0.0.1'
RAILS = ('FNS_Installer', 'webBrowser')
# NOT a constant here: build_manifest.DOCS_SITE is the source, and the
# copy that used to sit at this line went stale at the domain migration
# while still being reported as the effective URL.


def fnsLog(*args, level='INFO'):
	try:
		lg = op.FNS.op('logger')
		if lg and lg.par.Active.eval():
			lg.Log(*args, level=level)
	except Exception:
		pass


class CmsExt:
	"""The CMS server + API. Promoted surface: Open, Close, ServeRequest."""

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self._last_hit = 0.0
		self._watch_armed = False
		self._mods = {}          # exec'd packaging modules, cached by mtime
		self._setStatus('idle')

	def onDestroyTD(self):
		self._watch_armed = False

	# ------------------------------------------------------------------
	# repo + packaging-module plumbing
	# ------------------------------------------------------------------

	def _repo(self, *parts):
		return os.path.join(project.folder, *parts).replace('\\', '/')

	def _pkgMod(self, filename):
		"""Exec packaging/<filename> into a namespace, cached by mtime so
		an edited file is picked up without a stale copy lingering. The
		repo file stays the single source; this is just how TD runs it
		(op/project/debug are TD builtins, visible to exec'd code)."""
		path = self._repo('packaging', filename)
		mtime = os.path.getmtime(path)
		cached = self._mods.get(filename)
		if cached and cached[0] == mtime:
			return cached[1]
		# __name__ MUST be set to a non-'__main__' value: without it, the
		# name resolves through TD's builtins in a way that lets a file's
		# `if __name__ == '__main__':` CLI block RUN -- measured live:
		# exec'ing gate_package.py without this rewrote catalog.json and
		# wrangler.toml on a read-only page load. Exec-as-module always
		# pins __name__.
		g = {'__file__': path, '__name__': 'fns_cms_' + filename[:-3]}
		with open(path, encoding='utf-8') as f:
			exec(compile(f.read(), path, 'exec'), g)
		self._mods[filename] = (mtime, g)
		return g

	def _pi(self):
		comp = op('/private_investigator1')
		return comp.extensions[0] if comp and comp.extensions else None

	def _packages(self):
		"""The manifest roster, read live -- same filter as
		build_manifest.Packages(): depth-1 tracked suspects, rails out."""
		root = op.FNS
		out = []
		for c in root.children:
			if c.family != 'COMP' or c.name in RAILS:
				continue
			p = getattr(c.par, 'externaltox', None)
			if not (p and p.eval() and 'pi_suspect' in c.tags):
				continue
			out.append(c)
		return sorted(out, key=lambda c: c.name.lower())

	def _pkgByName(self, name):
		if name == 'FNSTools':
			return op.FNS
		for c in self._packages():
			if c.name == name:
				return c
		return None

	# ------------------------------------------------------------------
	# server lifecycle (console pattern)
	# ------------------------------------------------------------------

	def _server(self):
		return self.ownerComp.op('webserver')

	def _freePort(self):
		import socket
		start = int(self.ownerComp.par.Port.eval())
		pool = [p for p in PORT_POOL if p >= start] or list(PORT_POOL)
		for port in pool:
			s = socket.socket()
			try:
				s.bind(('127.0.0.1', port))
				s.close()
				return port
			except OSError:
				s.close()
		return None

	def Open(self):
		"""Serve the page on loopback and open it in the browser."""
		ws = self._server()
		if ws is None:
			self._setStatus('no webserver DAT')
			return {'ok': False, 'why': 'no webserver DAT'}
		try:
			if str(ws.par.localaddress.eval()) != BIND_ADDRESS:
				ws.par.localaddress = BIND_ADDRESS
		except Exception as e:
			fnsLog('CMS: could not pin %s to loopback (%s)' % (ws.path, e),
				   level='ERROR')
		port = self._freePort()
		if port is None:
			self._setStatus('no free port in %s' % (PORT_POOL,))
			return {'ok': False, 'why': 'no free port'}
		ws.par.port = port
		ws.par.active = True
		self._last_hit = time.time()
		url = 'http://127.0.0.1:%d/' % port
		import webbrowser
		webbrowser.open(url)
		self._setStatus('serving %s' % url)
		fnsLog('CMS: serving %s' % url)
		if not self._watch_armed:
			self._watch_armed = True
			run('args[0]._idleTick()', self, delayFrames=300,
				delayRef=op.TDResources)
		return {'ok': True, 'url': url}

	def Close(self):
		ws = self._server()
		if ws is not None:
			ws.par.active = False
		self._watch_armed = False
		self._setStatus('idle')
		return {'ok': True}

	def _idleTick(self):
		"""A page nobody is using must not hold a listening socket."""
		if not self._watch_armed:
			return
		ws = self._server()
		if ws is None or not ws.par.active.eval():
			self._watch_armed = False
			return
		if (self.ownerComp.par.Autoclose.eval()
				and time.time() - self._last_hit > IDLE_SECONDS):
			fnsLog('CMS: idle %ds -- closing' % IDLE_SECONDS)
			self.Close()
			return
		run('args[0]._idleTick()', self, delayFrames=300,
			delayRef=op.TDResources)

	def _setStatus(self, text):
		p = getattr(self.ownerComp.par, 'Status', None)
		if p is not None:
			p.val = text

	# ------------------------------------------------------------------
	# HTTP dispatch (called by cms_server_callbacks, main thread)
	# ------------------------------------------------------------------

	def ServeRequest(self, request, response):
		self._last_hit = time.time()
		path = urlparse(request.get('uri', '/')).path.rstrip('/') or '/'
		method = str(request.get('method', 'GET')).upper()
		try:
			if path == '/':
				# No UI here by design. This component exists because PI is
				# a TouchDesigner extension: calling Get_Dirt/Save means
				# running Python on TD's main thread, so SOMETHING has to
				# live inside TD to receive the request. That is all this
				# is -- an adapter. The interface is the content CMS, which
				# proxies /api/td/* here, and a second page competing with
				# it is what made these two surfaces copies of each other.
				response['statusCode'], response['statusReason'] = 200, 'OK'
				response['content-type'] = 'application/json; charset=utf-8'
				response['data'] = json.dumps({
					'service': 'fns-release',
					'ui': 'website/tools/cms.mjs -- npm run cms, then Release',
					'endpoints': ['/api/ping', '/api/dirty', '/api/save',
								  '/api/preflight', '/api/stage',
								  '/api/release', '/api/upload',
								  '/api/uploadlog', '/api/hotkeys',
								  '/api/helpurl'],
				})
				return response
			body = {}
			raw = request.get('data')
			if raw:
				try:
					body = json.loads(raw.decode('utf-8')
									  if isinstance(raw, bytes) else str(raw))
				except Exception:
					body = {}
			handler = {
				# Identity, so a client hunting the port range can tell THIS
				# console from whatever else happens to be listening. A port
				# being open proved to mean nothing once: a foreign Python
				# server was found squatting the content CMS's 8787.
				('GET', '/api/ping'): lambda: {
					'ok': True, 'service': 'fns-release',
					# the port it is SERVING on, which is not always the
					# configured one -- the opener walks the range when a
					# port is taken
					'port': int(self.ownerComp.op('webserver').par.port.eval()),
				},
				('GET', '/api/dirty'): self._apiDirty,
				('POST', '/api/save'): lambda b=body: self._apiSave(b),
				('GET', '/api/preflight'): self._apiPreflight,
				('POST', '/api/stage'): self._apiStage,
				('POST', '/api/release'): lambda b=body: self._apiRelease(b),
				('POST', '/api/upload'): self._apiUpload,
				('GET', '/api/uploadlog'): self._apiUploadLog,
				('GET', '/api/hotkeys'): self._apiHotkeys,
				('POST', '/api/helpurl'): lambda b=body: self._apiHelpurl(b),
			}.get((method, path))
			if handler is None:
				payload, code = {'error': 'no such endpoint'}, 404
			else:
				payload = handler()
				code = 400 if isinstance(payload, dict) and payload.get('error') else 200
		except SystemExit as e:
			# gate_package refuses via sys.exit(message) -- that message
			# is the user-facing answer, not a crash.
			payload, code = {'error': str(e)}, 400
		except Exception as e:
			fnsLog('CMS: %s %s failed (%s)' % (method, path, e), level='ERROR')
			payload, code = {'error': str(e)}, 500
		response['statusCode'] = code
		response['statusReason'] = 'OK' if code == 200 else 'Error'
		response['content-type'] = 'application/json; charset=utf-8'
		response['data'] = json.dumps(payload)
		return response

	# ------------------------------------------------------------------
	# Publish tab
	# ------------------------------------------------------------------

	def _apiDirty(self):
		pi = self._pi()
		if pi is None:
			return {'error': 'Private Investigator not found'}
		# What a publish view is FOR: live Pkgversion against the version
		# the world already has. PI's Build column counts tox saves -- dev
		# bookkeeping that never decides whether anyone gets an update
		# (`Pkgversion` governs updates; hashes only verify), so it rides
		# along as a detail rather than as the number on screen.
		# NOT release_one._publishedVersions(): despite its docstring it
		# reads packaging/manifest.json -- the REPO manifest, which Build()
		# regenerates from the live project. That is what we are about to
		# publish, so comparing against it always says "shipped" and this
		# column would be a mirror. The updater's store cache is the last
		# manifest actually FETCHED from the bucket, which is the closest
		# offline answer to "what does the world have".
		published = {}
		try:
			upd = op.FNS.op('FNS_Updater')
			folder = ''
			if upd is not None:
				folder = str(upd.par.Storefolder.eval() or '')
			if not folder:
				folder = '%s/FNStools_ext/store' % app.userPaletteFolder
			path = os.path.join(folder, 'manifest.json')
			with open(path, encoding='utf-8') as f:
				published = {p['name']: p.get('version', '')
							 for p in json.load(f).get('packages', [])}
		except Exception:
			pass
		rows = []
		for c in self._packages() + [op.FNS]:
			info = {}
			try:
				info = pi.Get_Info(c) or {}
			except Exception:
				pass
			try:
				dirty = bool(pi.Get_Dirt(c))
			except Exception:
				dirty = None
			name = 'FNSTools' if c is op.FNS else c.name
			ver = ''
			fa = c.op('FNS_About')
			if fa is not None and hasattr(fa.par, 'Pkgversion'):
				ver = str(fa.par.Pkgversion.eval()).strip()
			pub = str(published.get(name, '') or '')
			# the ONE help override, and what the name derives to when it is
			# blank -- shown on the row because the packages view that used
			# to hold them belongs to the content CMS now
			over, derived = '', ''
			if c is not op.FNS:
				fa = c.op('FNS_About')
				if fa is not None:
					pp = getattr(fa.par, 'Helpurl', None)
					if pp is not None:
						over = str(pp.eval()).strip()
				site = self._docsSite()
				if site:
					derived = '%s/%s/' % (site,
										  name.lower().replace('_', '-'))
			rows.append({'name': name,
						 'dirty': dirty,
						 'help_override': over,
						 'help_derived': derived,
						 'version': ver,
						 'published': pub,
						 # unshipped: the world has nothing by this name, or
						 # has an older one. The reason this table exists.
						 'unshipped': bool(ver) and ver != pub,
						 'build': info.get('Build'),
						 'saved': info.get('Savetimestamp', '')})
		return {'rows': rows}

	def _apiSave(self, body):
		name = str(body.get('name', '')).strip()
		comp = self._pkgByName(name)
		if comp is None:
			return {'error': 'unknown package %r' % name}
		pi = self._pi()
		if pi is None:
			return {'error': 'Private Investigator not found'}
		pi.Save(comp)
		fnsLog('CMS: PI-saved %s' % comp.path)
		tox = self._repo(str(comp.par.externaltox.eval()))
		return {'ok': True, 'name': name,
				'tox_mtime': os.path.getmtime(tox) if os.path.exists(tox) else None}

	def _apiPreflight(self):
		return self._pkgMod('release_one.py')['Preflight'](quiet=True)

	def _apiStage(self):
		r = self._pkgMod('publish.py')['Stage']()
		r['upload_command'] = 'python packaging/upload.py'
		r['pins_command'] = 'python packaging/check_pins.py'
		return r

	# ------------------------------------------------------------------
	# Entitlement tab (gate_package is the implementation; this is JSON)
	# ------------------------------------------------------------------


	# ------------------------------------------------------------------
	# Packages tab
	# ------------------------------------------------------------------

	def _catalog(self):
		with open(self._repo('packaging', 'catalog.json'), encoding='utf-8') as f:
			return json.load(f)


	def _docsSite(self):
		"""The docs host, from build_manifest -- the one place that owns it.

		RegistryBase mirrors the same value under an explicit change-both-
		or-neither rule; a third copy here drifted at the domain migration
		and reported a dead host as the effective help URL.
		"""
		try:
			return self._pkgMod('build_manifest.py')['DOCS_SITE']
		except Exception:
			return ''

	def _apiHotkeys(self):
		"""Every package's real bindings, live from the hotkey manager.

		The same derivation the manifest uses -- build_manifest.Hotkeys --
		rather than a second reading of the manager, so the CMS cannot show
		one thing while the release ships another. Live rather than read
		from the manifest, because a key rebound five minutes ago should
		appear before the next build, not after it.
		"""
		bm = self._pkgMod('build_manifest.py')
		out = {}
		for c in self._packages():
			try:
				hk = bm['Hotkeys'](c)
			except Exception:
				hk = []
			if hk:
				out[c.name] = hk
		return {'packages': out}

	def _apiRelease(self, body):
		"""Publish the named packages: bump, export, manifest, Stage.

		This is release_one.ReleaseMany, not a reimplementation of it --
		the sequence has ordering rules that took real failures to learn
		(the bump must aim at the FNS_About child, not the tool's mirror,
		or it ships the OLD version while every install reads current),
		and a second copy here would drift from them.

		upload stays FALSE here and this action never ships: release &
		stage and upload are TWO buttons by decision (the two-step is the
		honesty -- docs/EntitlementFunnelPlan.md, CMS section). Shipping
		is /api/upload: the same detached subprocess PI uses, watched
		through /api/uploadlog rather than a shell.

		Blocking, and honestly so: exporting a package runs on TD's main
		thread, so the editor is frozen for its duration. Seconds for one
		package, minutes for forty-nine -- which is why the caller picks.
		"""
		names = [str(n).strip() for n in (body.get('names') or []) if str(n).strip()]
		if not names:
			return {'error': 'no packages selected'}
		bump = str(body.get('bump', 'auto')).strip() or 'auto'
		if bump not in ('auto', 'patch', 'minor', 'major', 'none'):
			return {'error': 'bump must be auto, patch, minor, major or none'}
		ro = self._pkgMod('release_one.py')
		try:
			res = ro['Release'](names,
								bump=(None if bump == 'none' else bump),
								upload=False,
								force=bool(body.get('force')))
		except Exception as e:
			fnsLog('CMS: release failed -- %s' % e, level='ERROR')
			return {'error': str(e)}
		# the Popen handle Release can carry is not JSON, and we never ask
		# for an upload anyway
		res.pop('_proc', None)
		fnsLog('CMS: released %s' % ', '.join(names))
		return res

	def _apiUpload(self):
		"""Kick the bucket sync -- the same detached StartUpload PI uses,
		so the CMS can SHIP, not only stage. Zero owned state holds: no
		Popen handle is kept; the log file IS the run's state, so the
		view survives reinit and 'already running' is read off the log's
		mtime. The uploader itself verifies what the bucket serves and
		fails the run if the plus/ prefix is publicly readable."""
		pub = self._repo('packaging', 'publish')
		if not os.path.exists(os.path.join(pub, 'manifest.json')):
			return {'error': 'nothing staged -- packaging/publish/ has no '
							 'manifest; Release & stage first'}
		log = os.path.join(pub, '.upload.log')
		if os.path.exists(log) and time.time() - os.path.getmtime(log) < 15:
			return {'error': 'an upload appears to be running (its log moved '
							 'seconds ago) -- watch it, do not start a second'}
		ro = self._pkgMod('release_one.py')
		ro['StartUpload']()
		fnsLog('CMS: bucket upload started, log at packaging/publish/.upload.log')
		return {'ok': True, 'log': 'packaging/publish/.upload.log'}

	def _apiUploadLog(self):
		"""Tail of the detached upload's log -- the read-only ship-state
		view. This endpoint only reports the uploader's own words; it
		never re-derives ship state."""
		log = self._repo('packaging', 'publish', '.upload.log')
		if not os.path.exists(log):
			return {'ok': True, 'exists': False, 'age_s': None, 'tail': ''}
		with open(log, 'r', encoding='utf-8', errors='replace') as f:
			text = f.read()
		return {'ok': True, 'exists': True, 'size': len(text),
				'age_s': round(time.time() - os.path.getmtime(log), 1),
				'tail': text[-8000:]}

	def _apiHelpurl(self, body):
		"""Set (or clear) the ONE help override -- FNS_About.Helpurl --
		and PI-save the package in the same action, per the pi-save
		discipline: a live par change that is not in the suspect tox dies
		on the next reload."""
		name = str(body.get('name', '')).strip()
		url = str(body.get('url', '')).strip()
		comp = self._pkgByName(name)
		if comp is None or comp is op.FNS:
			return {'error': 'unknown package %r' % name}
		fa = comp.op('FNS_About')
		if fa is None:
			return {'error': '%s has no FNS_About' % name}
		p = getattr(fa.par, 'Helpurl', None)
		if p is None:
			pages = fa.customPages
			page = pages[0] if pages else fa.appendCustomPage('About')
			p = page.appendStr('Helpurl', label='Help URL')[0]
			p.help = ('The ONE override for this package\'s docs page. '
					  'Blank = derived from the package name '
					  '(build_manifest._helpUrl / RegistryBase rule).')
		p.val = url
		pi = self._pi()
		if pi is not None:
			pi.Save(comp)
		effective = url or '%s/%s/' % (self._docsSite(),
									   comp.name.lower().replace('_', '-'))
		fnsLog('CMS: Helpurl override for %s = %r (suspect saved)' % (name, url))
		return {'ok': True, 'name': name, 'override': url,
				'effective': effective}

	# ------------------------------------------------------------------
	# Content tab -- ONE front door over TWO backends
	#
	# website/tools/cms.mjs (127.0.0.1:8787) is the CONTENT cms: docs
	# prose, catalog descriptions/categories, recommendations, icons. It
	# existed before this component and does that job better (markdown
	# editing, stub/TODO tracking, frontmatter ordering) -- so NO doc
	# authoring lives here. Instead the page's Content tab EMBEDS it
	# (iframe, its own origin, fully interactive) and can start it when
	# the port is closed. The split stays: cms.mjs owns content; FNS_CMS
	# owns what needs the LIVE project (PI publishing, Preflight, Stage,
	# the Helpurl par override) plus entitlement, which cms.mjs
	# deliberately declined ("does not offer to invent a tier id").
	# ------------------------------------------------------------------

	# A port being OPEN does not mean OUR cms is on it -- measured live:
	# 8787 was squatted by a foreign Python BaseHTTP process 501'ing every
	# GET, which a bare connect-probe reported as "up". So the probe reads
	# the response and looks for the page title, and the spawner walks to
	# a genuinely free port via CMS_PORT (which cms.mjs honours).
	CONTENT_CMS_PORTS = tuple(range(8787, 8792))
	CONTENT_CMS_MARK = b'FNSTools CMS'

	def _probeContentPort(self, port):
		"""'ours' | 'foreign' | 'closed'. Loopback, 0.4 s cap -- a
		button-driven check, never per-frame."""
		import socket
		s = socket.socket()
		s.settimeout(0.4)
		try:
			if s.connect_ex(('127.0.0.1', port)) != 0:
				return 'closed'
			s.sendall(b'GET / HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n')
			data = b''
			while len(data) < 4096:
				chunk = s.recv(1024)
				if not chunk:
					break
				data += chunk
			return 'ours' if self.CONTENT_CMS_MARK in data else 'foreign'
		except OSError:
			return 'foreign'
		finally:
			s.close()


