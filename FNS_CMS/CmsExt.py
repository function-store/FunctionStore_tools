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
								  '/api/preflight', '/api/rebuildrails',
								  '/api/retire',
								  '/api/refreshstore',
								  '/api/stage',
								  '/api/release', '/api/upload',
								  '/api/prunebucket',
								  '/api/uploadlog', '/api/hotkeys',
								  '/api/helpurl', '/api/parameters',
								  '/api/parhelp', '/api/parexport'],
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
				('POST', '/api/rebuildrails'): self._apiRebuildRails,
				('POST', '/api/retire'): lambda b=body: self._apiRetire(b),
				('POST', '/api/refreshstore'): self._apiRefreshStore,
				('POST', '/api/stage'): self._apiStage,
				('POST', '/api/release'): lambda b=body: self._apiRelease(b),
				('POST', '/api/upload'): self._apiUpload,
				('POST', '/api/prunebucket'): lambda b=body: self._apiPruneBucket(b),
				('GET', '/api/uploadlog'): self._apiUploadLog,
				('GET', '/api/hotkeys'): self._apiHotkeys,
				('POST', '/api/helpurl'): lambda b=body: self._apiHelpurl(b),
				('GET', '/api/parameters'): self._apiParameters,
				('POST', '/api/parhelp'): lambda b=body: self._apiParHelp(b),
				('POST', '/api/parexport'): self._apiParExport,
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
		# What each package's PI build read when its artifact last shipped
		# (release_one._recordShippedBuilds). Live Build differing means the
		# tox changed since it shipped -- selectable and bumpable even while
		# the version still equals the published one.
		shipped = {}
		try:
			path = os.path.join(project.folder,
								'packaging', 'shipped_builds.json')
			with open(path, encoding='utf-8') as f:
				doc = json.load(f)
			if isinstance(doc, dict):
				shipped = doc
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
			# Child-first, like every reader in the release rail: the
			# FNS_About copy is the authoritative one (bumps write it),
			# so a severed comp-level mirror can never invert who wins.
			# The comp's own bare Pkgversion answers for packages that
			# never grew the child (packaging/CREATING.md).
			ver = ''
			fa = c.op('FNS_About')
			if fa is not None and hasattr(fa.par, 'Pkgversion'):
				ver = str(fa.par.Pkgversion.eval()).strip()
			if not ver:
				vp = getattr(c.par, 'Pkgversion', None)
				if vp is not None:
					ver = str(vp.eval()).strip()
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
			# live PI build vs the counter recorded at last ship: differing
			# means the tox changed without a bump yet. None (no record, or
			# no PI info) reads as unknown, never as changed.
			sb = (shipped.get(name) or {}).get('build')
			live_b = info.get('Build')
			changed = None
			if sb is not None and live_b is not None:
				changed = str(live_b) != str(sb)
			rows.append({'name': name,
						 'dirty': dirty,
						 'help_override': over,
						 'help_derived': derived,
						 'version': ver,
						 'published': pub,
						 # unshipped: the world has nothing by this name, or
						 # has an older one. The reason this table exists.
						 'unshipped': bool(ver) and ver != pub,
						 'build': live_b,
						 'shipped_build': sb,
						 'build_changed': changed,
						 'saved': info.get('Savetimestamp', '')})
		# The install rails' own row: not a package (their dirt lives in
		# repo files PI cannot see), but a first-class release citizen --
		# stale means rebuild first, changed means worth a release.
		rails = {}
		unlanded, rippled = set(), set()
		try:
			mod = self._pkgMod('release_one.py')
			rails = mod['RailsState']()
			# the THIRD change signal: sources newer than the suspect tox.
			# A file-synced DAT edit reloads the live comp without touching
			# PI's dirty flag OR its build counter, so without this a
			# changed package can read clean + current all the way to ship.
			u, rp = mod['_unlandedPackages']([r['name'] for r in rows])
			unlanded, rippled = set(u), set(rp)
		except Exception as e:
			rails = {'state': 'unknown', 'error': str(e)}
		for r in rows:
			r['unlanded'] = r['name'] in unlanded
			r['rippled'] = r['name'] in rippled
		# The prune rail. Three lists, three verbs:
		#   vanished        published but no longer a live package -- Stage
		#                   refuses the next release until each is DECLARED
		#                   retired (or the package is loaded again)
		#   stale_retired   declared retired but still live -- a standing
		#                   authorisation for a future accidental drop
		#   prunable_retired  declared, gone, and no published manifest
		#                   still lists it -- the entry has done its job
		retired_list = []
		try:
			with open(os.path.join(project.folder, 'packaging',
								   'release.json'), encoding='utf-8') as f:
				retired_list = [str(n) for n in
								(json.load(f).get('retired') or [])]
		except Exception:
			pass
		# The Published column reads the STORE CACHE (the last manifest
		# actually fetched from the bucket) -- so right after an upload it
		# lags until the store refreshes. Ship both release labels so the
		# page can SAY that instead of looking broken (field-confirmed:
		# "I released and uploaded, still the old versions after refresh").
		published_release = ''
		try:
			folder2 = ''
			upd2 = op.FNS.op('FNS_Updater')
			if upd2 is not None:
				folder2 = str(upd2.par.Storefolder.eval() or '')
			if not folder2:
				folder2 = '%s/FNStools_ext/store' % app.userPaletteFolder
			with open(os.path.join(folder2, 'manifest.json'),
					  encoding='utf-8') as f:
				published_release = str(json.load(f).get('release', ''))
		except Exception:
			pass
		staged_release = ''
		try:
			with open(self._repo('packaging', 'publish', 'manifest.json'),
					  encoding='utf-8') as f:
				staged_release = str(json.load(f).get('release', ''))
		except Exception:
			pass
		live_names = {r['name'] for r in rows} - {'FNSTools'}
		pruning = {
			'vanished': sorted(set(published) - live_names
							   - set(retired_list)),
			'stale_retired': sorted(set(retired_list) & live_names),
			'prunable_retired': sorted(set(retired_list) - set(published)
									   - live_names),
			'retired': sorted(retired_list),
		}
		return {'rows': rows, 'rails': rails, 'pruning': pruning,
				'published_release': published_release,
				'staged_release': staged_release}

	def _apiRefreshStore(self):
		"""Fetch the bucket's rolling manifest into the store cache --
		names=[] is the manifest-only refresh, no artifact downloads.
		Async in the updater; the page re-polls /api/dirty after a beat."""
		upd = op.FNS.op('FNS_Updater')
		if upd is None:
			return {'error': 'no FNS_Updater in the toolkit root'}
		try:
			r = upd.ext.ExtUpdater.RefreshStore(names=[])
		except Exception as e:
			return {'error': 'store refresh failed to start: %s' % e}
		# `why` on a started job is STATUS ("locating (async)"), not a
		# refusal -- only ok:False means it did not start
		if isinstance(r, dict) and r.get('ok') is False:
			return {'error': r.get('why') or 'store refresh refused'}
		fnsLog('CMS: store manifest refresh started')
		return {'ok': True}

	def _apiRetire(self, body):
		"""The prune rail's writer: declare a vanished package retired
		(archiving its leftovers), or -- undo=True -- remove a name from
		the retired list (clearing a stale entry, or pruning one no
		published manifest still lists).

		Retiring also prunes what would otherwise keep the package alive
		on the site and in the books: the catalog entry goes, the doc is
		ARCHIVED to packaging/docs/retired/ (moved, never deleted -- the
		site build only scans the top level), and the shipped-builds
		record is dropped. release.json keeps every other key untouched.
		"""
		name = str(body.get('name', '')).strip()
		undo = bool(body.get('undo'))
		if not name:
			return {'error': 'no package name'}
		rel_path = os.path.join(project.folder, 'packaging', 'release.json')
		try:
			with open(rel_path, encoding='utf-8') as f:
				doc = json.load(f)
		except Exception as e:
			return {'error': 'release.json unreadable: %s' % e}
		retired = [str(n) for n in (doc.get('retired') or [])]
		live = {c.name for c in self._packages()}
		notes = []
		if undo:
			if name not in retired:
				return {'error': '%s is not in the retired list' % name}
			retired = [n for n in retired if n != name]
			arch = os.path.join(project.folder, 'packaging', 'docs',
								'retired', name + '.md')
			if os.path.exists(arch):
				notes.append('its doc is still archived at packaging/docs/'
							 'retired/%s.md -- restore it (and a catalog '
							 'entry) by hand if the package returns' % name)
		else:
			if name in live:
				return {'error': '%s is still a live package in this '
								 'project -- retiring it now would only '
								 'create a stale entry. Unload it (or drop '
								 'its pi_suspect tag) first.' % name}
			if name in retired:
				return {'error': '%s is already declared retired' % name}
			retired.append(name)
			cat_path = os.path.join(project.folder, 'packaging',
									'catalog.json')
			try:
				with open(cat_path, encoding='utf-8') as f:
					cat = json.load(f)
				entry = (cat.get('packages') or {}).pop(name, None)
				if entry is not None:
					with open(cat_path, 'w', encoding='utf-8') as f:
						json.dump(cat, f, indent=1)
						f.write('\n')
					notes.append('catalog entry removed')
					if entry.get('access') and entry['access'] != 'free':
						notes.append('it was GATED (%s): remove it from the '
									 "worker's tier map (wrangler.toml) and "
									 'deploy' % entry['access'])
			except Exception as e:
				notes.append('catalog not touched (%s)' % e)
			doc_path = os.path.join(project.folder, 'packaging', 'docs',
									name + '.md')
			if os.path.exists(doc_path):
				arch_dir = os.path.join(project.folder, 'packaging', 'docs',
										'retired')
				os.makedirs(arch_dir, exist_ok=True)
				os.replace(doc_path,
						   os.path.join(arch_dir, name + '.md'))
				notes.append('doc archived to packaging/docs/retired/%s.md'
							 % name)
			sb_path = os.path.join(project.folder, 'packaging',
								   'shipped_builds.json')
			try:
				with open(sb_path, encoding='utf-8') as f:
					sb = json.load(f)
				if isinstance(sb, dict) and name in sb:
					sb.pop(name)
					with open(sb_path, 'w', encoding='utf-8') as f:
						json.dump(sb, f, indent=1, sort_keys=True)
						f.write('\n')
					notes.append('shipped-builds record dropped')
			except Exception:
				pass
		doc['retired'] = sorted(set(retired))
		with open(rel_path, 'w', encoding='utf-8') as f:
			json.dump(doc, f, indent=1)
			f.write('\n')
		return {'ok': True, 'name': name, 'undone': undo,
				'retired': doc['retired'], 'notes': notes}

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

	def _apiRebuildRails(self):
		"""Rebuild the install rails (packaging/dist) from their current
		sources -- the remedy for preflight's "rails stale" blocker.
		Stage() hashes the dist bytes, and staging bytes nobody built
		would ship an installer that does not match its sources. Runs
		inside TD because the rails are built FROM live operators; the
		UI pauses for the few seconds the export takes."""
		m = self._pkgMod('build_installer.py')
		inst = m['BuildInstaller']()
		boot = m['BuildBootstrap']()
		fnsLog('CMS: rails rebuilt (%s, %s)'
			   % (inst.get('out', '?'), boot.get('out', '?')))
		return {'ok': True,
				'installer': {k: inst.get(k) for k in ('out', 'bytes', 'errors')},
				'bootstrap': {k: boot.get(k) for k in ('out', 'bytes', 'errors')}}

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
		rails = bool(body.get('rails'))
		if not names and not rails:
			return {'error': 'no packages selected'}
		bump = str(body.get('bump', 'auto')).strip() or 'auto'
		if bump not in ('auto', 'patch', 'minor', 'major', 'none'):
			return {'error': 'bump must be auto, patch, minor, major or none'}
		ro = self._pkgMod('release_one.py')
		try:
			res = ro['Release'](names,
								bump=(None if bump == 'none' else bump),
								upload=False,
								rails=rails,
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

	def _apiPruneBucket(self, body):
		"""Prune old release directories from the bucket -- the detached
		upload.py --prune-only rail, watched through the same
		/api/uploadlog. `dry` previews the deletions and touches nothing.
		The current release is always kept (upload.py pins it first)."""
		# NOT `or 3`: keep=0 is falsy, and the fallback silently turned an
		# invalid request into a REAL prune (field lesson, 2026-08-31 --
		# this exact line deleted two old release directories).
		try:
			keep = int(body.get('keep', 3))
		except (TypeError, ValueError):
			return {'error': 'keep must be a number'}
		if keep < 1:
			return {'error': 'keep must be at least 1 (the current release)'}
		dry = bool(body.get('dry'))
		pub = self._repo('packaging', 'publish')
		if not os.path.exists(os.path.join(pub, 'manifest.json')):
			return {'error': 'nothing staged -- packaging/publish/ has no '
							 'manifest (prune reads base_url off it)'}
		log = os.path.join(pub, '.upload.log')
		if os.path.exists(log) and time.time() - os.path.getmtime(log) < 15:
			return {'error': 'an upload or prune appears to be running (its '
							 'log moved seconds ago) -- watch it, do not '
							 'start a second'}
		ro = self._pkgMod('release_one.py')
		ro['StartPrune'](keep, dry=dry)
		fnsLog('CMS: bucket prune %sstarted (keep %d)'
			   % ('preview ' if dry else '', keep))
		return {'ok': True, 'dry': dry, 'keep': keep,
				'log': 'packaging/publish/.upload.log'}

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
	# Parameters tab
	#
	# A custom parameter's `help` is the tooltip in TouchDesigner AND the
	# description on the docs page -- build_manifest.Parameters() reads the
	# pars live and website/tools/build-site.mjs renders exactly that
	# string. So this tab is not "a place to write documentation about
	# parameters": it writes the parameter's own help text, and the docs
	# follow. There is no second copy to keep in step, which is the whole
	# reason the field is worth authoring here rather than in a markdown
	# table someone has to remember to update.
	# ------------------------------------------------------------------

	def _apiParameters(self):
		"""Every package's customization surface plus its help coverage.

		Derived through build_manifest.Parameters -- the same call the
		release build makes -- so this page can never show one thing while
		the site publishes another.
		"""
		bm = self._pkgMod('build_manifest.py')
		out, done, total = [], 0, 0
		for c in self._packages():
			try:
				rows = bm['Parameters'](c)
			except Exception as e:
				out.append({'name': c.name, 'error': str(e), 'rows': []})
				continue
			# A Header is a section label, not a control: it has no tooltip
			# to write and counting it would flatter the coverage number.
			real = [r for r in rows if r.get('style') != 'Header']
			have = len([r for r in real if r.get('help')])
			done += have
			total += len(real)
			out.append({'name': c.name, 'rows': rows,
						'documented': have, 'controls': len(real)})
		return {'packages': out, 'documented': done, 'controls': total,
				# pages this tab refuses to write: the toolkit authors them
				'locked': [bm['REGISTRY_PAGE']] + list(bm['DEV_PAGES'])}

	def _apiParHelp(self, body):
		"""Write help text onto live parameters, then PI-save ONCE.

		Batched per package on purpose. Each save re-exports the suspect
		tox, so saving per keystroke would mean a tox write per sentence;
		and an unsaved live par change dies on the next reload (the
		pi-save discipline _apiHelpurl already follows).
		"""
		name = str(body.get('name', '')).strip()
		edits = body.get('edits') or []
		comp = self._pkgByName(name)
		if comp is None or comp is op.FNS:
			return {'error': 'unknown package %r' % name}
		bm = self._pkgMod('build_manifest.py')
		locked = set([bm['REGISTRY_PAGE']]) | set(bm['DEV_PAGES'])
		pages = {pg.name: pg for pg in comp.customPages}
		written, skipped = [], []
		for edit in edits:
			page_name = str(edit.get('page', ''))
			par_name = str(edit.get('name', ''))
			text = str(edit.get('help', '')).strip()
			# The stamped pages are authored ONCE, in RegistryBase and the
			# About stamper. Writing them here would document one package's
			# copy and leave the other 48 saying something else -- exactly
			# the drift the shared reference exists to prevent.
			if page_name in locked:
				skipped.append('%s/%s (stamped by the toolkit)'
							   % (page_name, par_name))
				continue
			page = pages.get(page_name)
			if page is None:
				skipped.append('%s/%s (no such page)' % (page_name, par_name))
				continue
			members = [pr for pr in page.pars
					   if str(pr.tupletName) == par_name]
			if not members:
				skipped.append('%s/%s (no such parameter)'
							   % (page_name, par_name))
				continue
			# One tooltip per control: TD shows the group's help, so every
			# member of a tuplet carries the same sentence.
			for pr in members:
				pr.help = text
			written.append('%s/%s' % (page_name, par_name))
		if written:
			pi = self._pi()
			if pi is not None:
				pi.Save(comp)
			fnsLog('CMS: help text on %s -- %d written (suspect saved)'
				   % (name, len(written)))
		rows = bm['Parameters'](comp)
		real = [r for r in rows if r.get('style') != 'Header']
		return {'ok': True, 'name': name, 'written': written,
				'skipped': skipped, 'rows': rows,
				'documented': len([r for r in real if r.get('help')]),
				'controls': len(real)}

	def _apiParExport(self):
		"""Regenerate packaging/parameters.json from the live pars.

		The docs build reads that file, so this is what carries a tooltip
		written a minute ago onto the site without waiting for a release.
		"""
		bm = self._pkgMod('build_manifest.py')
		return dict(bm['BuildParameters'](), ok=True)

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


