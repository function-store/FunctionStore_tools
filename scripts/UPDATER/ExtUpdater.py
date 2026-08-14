
'''Info Header Start
Name : ExtUpdater
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
"""Bucket + manifest updates for the toolkit.

TWO MOTIONS, deliberately separate (ConfiguratorDistribution 4.2):

  RefreshStore()   Machine-wide, project-independent. Fetches
                   <Baseurl>/manifest.json and every artifact whose bytes
                   differ, into the palette store. Mutates no project.

  UpdateProject()  Per project, explicit, never automatic. Compares what
                   THIS project recorded at install time against the store
                   and replaces only the packages that differ.

WHAT DECIDES "NEWER" is the artifact's sha256, never a version number: 38
of 39 packages carry no version at all and `build` is a save counter that
ticks on every .toe save, so neither can answer "is this newer than what I
installed?". The release label is for humans and changelogs.

The project's side of that comparison is the `installed` table in the
toolkit root -- package -> the sha256 it was installed FROM. It is PROJECT
state, so it lives in the project and travels with it, which is also what
makes an interrupted update pass safe to simply run again.

Never hash the live COMP to decide staleness: a .tox re-saved inside a
project no longer hashes to what was published, so the recorded
install-time hash is the only honest comparison.
"""

import hashlib
import json
import os
import shutil
import time
from urllib.parse import unquote, urlparse

import TDFunctions as TDF

MANIFEST_NAME = 'manifest.json'
# package -> the bytes it was installed from. Written by the installer and
# by every update; read to decide what is stale. packaging/InstallerExt.py
# writes the same four columns -- keep the two in step.
INSTALLED_DAT = 'installed'
INSTALLED_COLS = ['package', 'sha256', 'release', 'when']
UPDATES_DAT = 'updates'
UPDATES_COLS = ['package', 'state', 'installed', 'available', 'note']

STAGE_COMP = 'fns_update_stage'
# Seconds of zero progress before a fetch is called dead.
STALL_SECONDS = 45


# Runs AFTER the DAT holding this file is destroyed, so it may reference
# nothing inside the package -- only literals and ops that outlive it.
_SELF_UPDATE = """
import TDFunctions as TDF
_q = op('/sys/quiet')
_stage = _q.op(%(stage)r) or _q.create(baseCOMP, %(stage)r)
_stage.allowCooking = False
_before = {c.id for c in _stage.children}
_stage.loadTox(%(tox)r)
_fresh = [c for c in _stage.children if c.id not in _before]
_dest = op(%(dest)r)
if _fresh and _dest is not None:
	_new = TDF.replaceOp(_dest, _fresh[0])
	_fresh[0].destroy()
	_new.name = %(name)r
	debug('UPDATER: replaced itself from %(tox)s')
elif _fresh:
	_fresh[0].destroy()
	debug('UPDATER: self-update aborted, target vanished')
else:
	debug('UPDATER: self-update aborted, artifact loaded nothing')
"""


def _version(comp):
    """The version a component declares about itself."""
    p = getattr(comp.par, 'Pkgversion', None) if comp is not None else None
    return str(p.eval()).strip() if p is not None else ''


def _isNewer(available, installed):
    """Is `available` a later version than `installed`?

    Dotted-numeric compares in order (1.10.0 > 1.9.0, which string
    comparison gets wrong); anything that does not parse falls back to
    "differs", so an unparseable scheme still surfaces rather than being
    silently treated as current.
    """
    if not available or available == installed:
        return False
    if not installed:
        return True

    def parts(v):
        out = []
        for chunk in str(v).split('.'):
            digits = ''.join(c for c in chunk if c.isdigit())
            if digits == '' or digits != chunk.strip():
                return None
            out.append(int(digits))
        return out

    a, b = parts(available), parts(installed)
    if a is None or b is None:
        return True
    pad = max(len(a), len(b))
    return a + [0] * (pad - len(a)) > b + [0] * (pad - len(b))


def _sha256(path):
	h = hashlib.sha256()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(1 << 20), b''):
			h.update(chunk)
	return h.hexdigest()


class ExtUpdater:
	"""Update motions for the toolkit, driven by artifact hashes."""

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		# The wiki button colours itself from this; it now means "this
		# project has packages the store has newer bytes for".
		self.IsUpdatable = tdu.Dependency(False)
		self._job = None

	# ------------------------------------------------------------------
	# where things live
	# ------------------------------------------------------------------

	def _par(self, name, default=''):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return default
		return str(p.eval()).strip() or default

	def _root(self, target=None):
		"""The toolkit container this project installs packages into."""
		if target is not None:
			return target if isinstance(target, OP) else op(str(target))
		p = self.ownerComp.par.Target.eval()
		return p if isinstance(p, OP) else op(str(p))

	def StoreFolder(self):
		"""Machine-wide package store. Flat: one copy of each package, which
		is exactly what "what the store holds" means."""
		v = self._par('Storefolder')
		if not v:
			v = '%s/FNStools_ext/store' % app.userPaletteFolder
		return v.replace('\\', '/').rstrip('/')

	def BaseUrl(self):
		return self._par('Baseurl').rstrip('/')

	def _localBase(self, base):
		"""A local directory for `base`, or None when it is a real URL.

		file:// and bare paths keep the whole flow exercisable with no
		bucket in existence (handover 4b). publish.py already lays
		packaging/publish/ out exactly like the bucket, so pointing Baseurl
		at it exercises the real code path rather than a mock.
		"""
		b = base.strip().replace('\\', '/')
		if not b:
			return None
		if b.lower().startswith('file:'):
			parsed = urlparse(b)
			local = unquote(parsed.netloc + parsed.path)
			if len(local) > 2 and local[0] == '/' and local[2] == ':':
				local = local[1:]  # file:///C:/x -> C:/x
			return local.rstrip('/')
		if '://' in b:
			return None
		return b.rstrip('/')

	def _artifactRel(self, pkg, manifest):
		"""Where the artifact sits UNDER the base, mirroring the bucket.

		Releases are pinned, so the URL in the manifest already carries the
		release; derive from it and fall back to the layout publish.py
		writes only if a manifest ever arrives without one.

		Everything is then fetched relative to the CONFIGURED base, not the
		manifest's own base_url. Against the real bucket the two are the
		same string; pointed at a mirror, a local publish/ tree or a
		file:// path, only this makes the artifacts follow the manifest.
		"""
		url = (pkg.get('artifact') or {}).get('url', '')
		base = str(manifest.get('base_url', '')).rstrip('/')
		if url and base and url.startswith(base + '/'):
			return url[len(base) + 1:]
		return '%s/%s.tox' % (manifest.get('release', ''), pkg['name'])

	def _storePath(self, name):
		return '%s/%s.tox' % (self.StoreFolder(), name)

	# ------------------------------------------------------------------
	# the two records
	# ------------------------------------------------------------------

	def StoreManifest(self):
		"""What the store holds, as of its last refresh. None if never."""
		path = '%s/%s' % (self.StoreFolder(), MANIFEST_NAME)
		if not os.path.exists(path):
			return None
		try:
			with open(path, 'r', encoding='utf-8') as f:
				return json.load(f)
		except Exception as e:
			debug('UPDATER: store manifest unreadable (%s)' % e)
			return None

	def _installedTable(self, target=None, create=True):
		root = self._root(target)
		if root is None:
			return None
		t = root.op(INSTALLED_DAT)
		if t is None:
			if not create:
				return None
			t = root.create(tableDAT, INSTALLED_DAT)
			t.nodeX, t.nodeY = -800, -400
			t.color = (0.35, 0.45, 0.55)
		# a fresh tableDAT already holds one empty row, so "no rows" is the
		# wrong test for "needs a header"
		if t.numRows == 0 or t[0, 0].val != INSTALLED_COLS[0]:
			t.clear()
			t.appendRow(INSTALLED_COLS)
		return t

	def Installed(self, target=None):
		"""package -> {sha256, release, when} as recorded at install time."""
		t = self._installedTable(target, create=False)
		out = {}
		if t is None or t.numRows < 2:
			return out
		for r in t.rows()[1:]:
			cells = [c.val for c in r]
			if not cells or not cells[0]:
				continue
			out[cells[0]] = {
				'sha256': cells[1] if len(cells) > 1 else '',
				'release': cells[2] if len(cells) > 2 else '',
				'when': cells[3] if len(cells) > 3 else '',
			}
		return out

	def RecordInstalled(self, name, sha256, release='', target=None):
		"""Upsert one package's install-time hash. Called per package as it
		lands, so an interrupted pass leaves a truthful record and simply
		re-running picks up where it stopped."""
		t = self._installedTable(target)
		if t is None:
			return False
		when = time.strftime('%Y-%m-%d %H:%M:%S')
		row = [name, sha256, release, when]
		for i in range(1, t.numRows):
			if t[i, 0].val == name:
				for c, v in enumerate(row):
					t[i, c] = v
				return True
		t.appendRow(row)
		return True

	# ------------------------------------------------------------------
	# status surface
	# ------------------------------------------------------------------

	def _status(self, text):
		p = getattr(self.ownerComp.par, 'Status', None)
		if p is not None:
			p.val = str(text)[:400]
		return text

	def _writeUpdates(self, rows):
		t = self.ownerComp.op(UPDATES_DAT)
		if t is None:
			return
		t.clear()
		t.appendRow(UPDATES_COLS)
		for r in rows:
			t.appendRow([r.get(c, '') for c in UPDATES_COLS])

	# ------------------------------------------------------------------
	# comparison -- the whole decision, in one place
	# ------------------------------------------------------------------

	def Compare(self, target=None):
		"""What this project has vs what the store publishes. No network.

		The comparison is between the version a component DECLARES about
		itself -- `Pkgversion`, read live off the installed COMP -- and the
		version the store publishes for it. Nothing is hashed to decide it:
		a .tox re-exports to different bytes every time (verified), so an
		artifact hash cannot tell a changed package from an unchanged one.
		Hashes verify downloads; versions decide updates.

		Reading the live parameter, rather than a record of what was
		installed, is what makes this work for a package embedded in the
		.toe: there is no file to consult, but the component still says
		what it is. It also means no side table can drift out of truth.

		States:
		  update       the store publishes a newer version
		  current      same version, or the store's is older
		  unversioned  the component declares no version -- reported, never
		               updated, because we cannot know what it is
		  locked       newer, but this copy must not be touched (see
		               _refuseReason)
		  missing      recorded as installed, but the component is gone
		"""
		man = self.StoreManifest()
		if not man:
			return {'ok': False, 'why': 'store has no manifest -- refresh the store first',
					'rows': [], 'updates': []}
		root = self._root(target)
		if root is None:
			return {'ok': False, 'why': 'no toolkit root (Target)', 'rows': [], 'updates': []}

		index = {p['name']: p for p in man.get('packages', [])}
		rows, updates, seen = [], [], set()

		for child in sorted(root.children, key=lambda c: c.name.lower()):
			pkg = index.get(child.name) if child.family == 'COMP' else None
			if pkg is None:
				continue          # not something the store publishes: say nothing
			seen.add(child.name)
			have = _version(child)
			avail = str(pkg.get('version', '')).strip()
			if not have:
				rows.append({'package': child.name, 'state': 'unversioned', 'installed': '',
							 'available': avail,
							 'note': 'component declares no version -- reinstall to adopt'})
				continue
			if _isNewer(avail, have):
				refuse = self._refuseReason(child)
				rows.append({'package': child.name, 'state': 'locked' if refuse else 'update',
							 'installed': have, 'available': avail,
							 'note': refuse or man.get('release', '')})
				if not refuse:
					updates.append(child.name)
			else:
				rows.append({'package': child.name, 'state': 'current',
							 'installed': have, 'available': avail, 'note': ''})

		# Recorded as installed but no longer here -- the one thing the
		# audit trail still tells us that the live network cannot.
		for name, rec in sorted(self.Installed(target).items()):
			if name in seen or root.op(name) is not None:
				continue
			rows.append({'package': name, 'state': 'missing', 'installed': rec.get('release', ''),
						 'available': str((index.get(name) or {}).get('version', '')),
						 'note': 'recorded as installed but not in this project'})

		return {'ok': True, 'release': man.get('release', ''), 'rows': rows,
				'updates': updates, 'why': ''}

	# ------------------------------------------------------------------
	# job plumbing (a manifest fetch, then whatever asked for it)
	# ------------------------------------------------------------------

	def _startJob(self, kind, names=None, target=None):
		if self._job is not None and self._job.get('stage') not in ('done', 'failed'):
			return {'ok': False, 'why': 'an update job is already running (%s)'
					% self._job.get('kind')}
		base = self.BaseUrl()
		if not base:
			return {'ok': False, 'why': 'no Baseurl set'}
		self._job = {'kind': kind, 'stage': 'manifest', 'names': names,
					 'target': target, 'base': base, 'local': self._localBase(base),
					 'queue': [], 'inflight': {}, 'failed': [], 'fetched': [],
					 'results': []}
		# Start from a clean downloader. Its stateDict keys on url+location,
		# and an entry left in GET/WAIT by an earlier pass makes every later
		# request for that file return the stale state instead of fetching.
		dl = self.ownerComp.op('fileDownloader')
		if dl is not None:
			try:
				dl.AbortAll()
			except Exception as e:
				debug('UPDATER: could not reset the downloader (%s)' % e)
		self._status('%s: fetching manifest...' % kind)
		return self._fetchManifest()

	def _later(self, method):
		"""Run a stage on the NEXT frame.

		A new webclientDAT request issued from inside that same DAT's
		callback is silently dropped -- the file lands, the next GET never
		goes out. So every stage that follows a download is deferred by a
		frame, which is also where the heavy work (loadTox, replaceOp)
		belongs rather than inside a callback.
		"""
		run('args[0].%s()' % method, self, delayFrames=1, delayRef=op.TDResources)

	def _fetchManifest(self):
		job = self._job
		dest_dir = self.StoreFolder()
		os.makedirs(dest_dir, exist_ok=True)
		if job['local'] is not None:
			src = '%s/%s' % (job['local'], MANIFEST_NAME)
			if not os.path.exists(src):
				return self._fail('no manifest at %s' % src)
			shutil.copyfile(src, '%s/%s' % (dest_dir, MANIFEST_NAME))
			return self._onManifest()
		self._download('%s/%s' % (job['base'], MANIFEST_NAME), MANIFEST_NAME)
		return {'ok': True, 'why': 'fetching manifest (async)'}

	def _download(self, url, filename):
		"""One file into the store. dwnldCopy=False overwrites: a refresh
		that silently kept the old bytes would be worse than no refresh."""
		self.ownerComp.op('fileDownloader').Download(
			url=url,
			location=self.StoreFolder(),
			loadIntoProj=False,
			discCopy=True,
			dwnldCopy=False,
			renameTo=filename,
			showProgress=bool(self.ownerComp.par.Showprogress.eval())
			if hasattr(self.ownerComp.par, 'Showprogress') else False,
		)

	def OnFileDownloaded(self, callbackInfo):
		"""Dispatch by filename -- the downloader is shared, so the arriving
		file says what it was for. Bookkeeping only; the next stage runs a
		frame later (see _later)."""
		path = str(callbackInfo.get('path') or '')
		name = os.path.basename(path)
		job = self._job
		if job is None:
			return
		if name == MANIFEST_NAME:
			self._later('_onManifest')
			return
		if name in job.get('inflight', {}):
			self._verifyFetched(name, job['inflight'].pop(name), path)
			self._later('_pump')

	def OnDownloadAborted(self, callbackInfo):
		name = os.path.basename(str(callbackInfo.get('path') or '')) or 'download'
		job = self._job
		if job is None:
			return
		job.setdefault('failed', []).append('%s: download aborted' % name)
		if name == MANIFEST_NAME:
			self._fail('manifest download failed')
			return
		job.get('inflight', {}).pop(name, None)
		self._later('_pump')

	def _pump(self):
		"""Keep the downloader fed, at most Maxdownloads in flight.

		The queue is ours rather than the downloader's own: its queueNext()
		re-issues from inside the callback, which is exactly the case that
		gets dropped.
		"""
		job = self._job
		if job is None or job.get('stage') != 'artifacts':
			return
		dl = self.ownerComp.op('fileDownloader')
		cap = max(1, int(dl.par.Maxdownloads.eval()))
		issued = False
		while job['queue'] and len(job['inflight']) < cap:
			item = job['queue'].pop(0)
			job['inflight'][item['file']] = item['sha']
			self._download(item['url'], item['file'])
			issued = True
		if not job['queue'] and not job['inflight']:
			self._onArtifacts()
			return
		if issued:
			job['progress_at'] = absTime.seconds
		self._status('%s: %d fetched, %d to go'
					 % (job['kind'], len(job['fetched']),
						len(job['queue']) + len(job['inflight'])))
		if not job.get('watching'):
			job['watching'] = True
			run('args[0]._watchdog()', self, delayFrames=120, delayRef=op.TDResources)

	def _watchdog(self):
		"""A connection that never opens produces NO callback at all -- the
		downloader leaves the request sitting in GET forever. Without this
		a wrong base URL or a 404 would hang the pass in silence."""
		job = self._job
		if job is None or job.get('stage') != 'artifacts':
			if job is not None:
				job['watching'] = False
			return
		if absTime.seconds - job.get('progress_at', 0) > STALL_SECONDS:
			stuck = ', '.join(list(job.get('inflight', {}))[:4]) or 'download'
			job['failed'].append('stalled after %ds -- no response for %s (check Base URL)'
								 % (STALL_SECONDS, stuck))
			job['inflight'], job['queue'], job['watching'] = {}, [], False
			self._onArtifacts()
			return
		run('args[0]._watchdog()', self, delayFrames=120, delayRef=op.TDResources)

	def _verifyFetched(self, name, want, path):
		"""Bytes that do not match the manifest never enter the store."""
		job = self._job
		if not os.path.exists(path):
			job['failed'].append('%s: file missing after download' % name)
			return
		digest = _sha256(path)
		if want and digest != want:
			try:
				os.remove(path)
			except Exception:
				pass
			job['failed'].append('%s: hash mismatch (deleted)' % name)
			return
		job['fetched'].append(name)
		job['progress_at'] = absTime.seconds

	def _onManifest(self):
		job = self._job
		if job is None:
			return {'ok': False, 'why': 'no job'}
		man = self.StoreManifest()
		if not man:
			return self._fail('fetched manifest is unreadable')
		job['manifest'] = man
		if job['kind'] == 'check':
			return self._report()
		wanted = self._needed(man, job)
		if not wanted:
			return self._onArtifacts()
		job['stage'] = 'artifacts'
		self._status('%s: fetching %d artifact(s)...' % (job['kind'], len(wanted)))
		if job['local'] is not None:
			for pkg in wanted:
				self._copyLocal(pkg, man)
			return self._onArtifacts()
		job['queue'] = [{'file': pkg['name'] + '.tox',
						 'url': '%s/%s' % (job['base'], self._artifactRel(pkg, man)),
						 'sha': (pkg['artifact'] or {}).get('sha256', '')}
						for pkg in wanted]
		self._pump()
		return {'ok': True, 'why': 'fetching %d artifact(s) (async)' % len(wanted)}

	def _copyLocal(self, pkg, man):
		job = self._job
		name = pkg['name']
		src = '%s/%s' % (job['local'], self._artifactRel(pkg, man))
		dst = self._storePath(name)
		if not os.path.exists(src):
			job['failed'].append('%s: not at %s' % (name, src))
			return
		os.makedirs(os.path.dirname(dst), exist_ok=True)
		shutil.copyfile(src, dst)
		self._verifyFetched(name + '.tox', (pkg.get('artifact') or {}).get('sha256', ''), dst)

	def _needed(self, man, job):
		"""Artifacts whose store copy is absent or has the wrong bytes.

		Re-hashing the store rather than trusting the previous manifest is
		what makes a half-finished refresh self-heal on the next run.
		"""
		if job['kind'] == 'update':
			cmp_ = self.Compare(job.get('target'))
			names = cmp_['updates']
			if job.get('names'):
				names = [n for n in names if n in job['names']]
			job['plan_names'] = names
		else:
			names = None
		out = []
		for pkg in man.get('packages', []):
			if names is not None and pkg['name'] not in names:
				continue
			art = pkg.get('artifact')
			if not art or not art.get('url'):
				continue
			path = self._storePath(pkg['name'])
			if os.path.exists(path) and _sha256(path) == art.get('sha256'):
				continue
			out.append(pkg)
		return out

	def _onArtifacts(self):
		job = self._job
		if job is None:
			return {'ok': False, 'why': 'no job'}
		if job['kind'] == 'refresh':
			return self._report()
		return self._apply()

	def _fail(self, why):
		if self._job is not None:
			self._job['stage'] = 'failed'
		self._status('failed: %s' % why)
		return {'ok': False, 'why': why}

	# ------------------------------------------------------------------
	# motion 1 -- refresh the store
	# ------------------------------------------------------------------

	def RefreshStore(self):
		"""Fetch the manifest and every artifact whose bytes differ.
		Machine-wide; no project is read or touched."""
		return self._startJob('refresh')

	def StoreStatus(self):
		"""What the store actually holds, verified against its manifest."""
		man = self.StoreManifest()
		if not man:
			return {'ok': False, 'why': 'store has no manifest -- refresh first'}
		present, missing, mismatched = [], [], []
		total = 0
		for pkg in man.get('packages', []):
			art = pkg.get('artifact')
			if not art:
				continue
			path = self._storePath(pkg['name'])
			if not os.path.exists(path):
				missing.append(pkg['name'])
			elif _sha256(path) != art.get('sha256'):
				mismatched.append(pkg['name'])
			else:
				present.append(pkg['name'])
				total += os.path.getsize(path)
		return {'ok': not missing and not mismatched, 'release': man.get('release', ''),
				'folder': self.StoreFolder(), 'verified': len(present),
				'missing': missing, 'mismatched': mismatched,
				'total_mb': round(total / 1048576.0, 2)}

	# ------------------------------------------------------------------
	# motion 2 -- update this project from the store
	# ------------------------------------------------------------------

	def CheckUpdates(self, target=None):
		"""Fetch the manifest, then compare. Cheap: one small JSON, no
		artifacts -- answering "is there anything new?" should not cost a
		6 MB download."""
		return self._startJob('check', target=target)

	def UpdateProject(self, names=None, target=None):
		"""Fetch the manifest, pull only the artifacts THIS project needs,
		then replace those packages. A package the user never installed
		stays uninstalled: an update pass is not an install pass."""
		return self._startJob('update', names=names, target=target)

	def _apply(self):
		job = self._job
		names = job.get('plan_names')
		if names is None:
			cmp_ = self.Compare(job.get('target'))
			names = cmp_['updates']
			if job.get('names'):
				names = [n for n in names if n in job['names']]
		man = job['manifest']
		index = {p['name']: p for p in man.get('packages', [])}
		steps = []
		for name in names:
			pkg = index.get(name)
			art = (pkg or {}).get('artifact') or {}
			steps.append({'name': name, 'path': self._storePath(name),
						  'sha256': art.get('sha256', ''),
						  'release': man.get('release', '')})
		if not steps:
			return self._report()
		# Updating the package this extension lives in saws off the branch
		# it is standing on, so it goes LAST and runs detached (see
		# _selfUpdate): everything else has already landed by then, and the
		# worst case is one package the user re-drops by hand.
		mine = [s for s in steps if self._isSelf(s['name'], job.get('target'))]
		steps = [s for s in steps if s not in mine] + mine

		# Snapshot every registered tool's settings before anything is
		# replaced. Guarded: a config problem must never block an update.
		self._saveConfig()
		planned = len(steps)          # _drain pops from this very list
		job['apply'] = steps
		job['stage'] = 'apply'
		self._status('updating %d package(s)...' % planned)
		self._drain()
		return {'ok': True, 'why': 'applying %d package(s)' % planned}

	def _saveConfig(self):
		cfg = getattr(op, 'CONFIGREGISTRY', None)
		if cfg and cfg.valid and cfg.extensionsReady:
			try:
				cfg.SaveAll()
			except Exception as e:
				debug('UPDATER: config save before update failed: %s' % e)
		else:
			debug('UPDATER: no ConfigRegistry global -- updating without a config snapshot')

	def _drain(self):
		"""One package per frame. Each replacement reinitialises extensions,
		so batching them into a single frame is both a long main-thread
		block and the crash-prone case."""
		job = self._job
		if job is None or job.get('stage') != 'apply':
			return
		self._settleVerifications(job)
		queue = job.get('apply') or []
		if not queue:
			job['stage'] = 'done'
			self._report()
			return
		step = queue.pop(0)
		try:
			if self._isSelf(step['name'], job.get('target')):
				res = self._selfUpdate(step, job.get('target'))
			else:
				res = self._replacePackage(step, job.get('target'))
		except Exception as e:
			res = {'package': step['name'], 'ok': False, 'why': str(e)[:160]}
		job['results'].append(res)
		if not res.get('ok'):
			job['failed'].append('%s: %s' % (step['name'], res.get('why', '')))
		self._status('updated %d of %d...' % (len(job['results']),
											  len(job['results']) + len(queue)))
		run('args[0]._drain()', self, delayFrames=3, delayRef=op.TDResources)

	def Drain(self):
		"""Public entry so a stalled pass can be nudged from the textport."""
		self._drain()

	def _settleVerifications(self, job):
		"""Finish judging reloads from the previous tick.

		A COMP reloaded by pulsing its external-tox reload does not report
		its new state within the call that fired the pulse, so a rewrite
		records what it wants checked and the next frame checks it.
		"""
		for res in job.get('results', []):
			path = res.pop('verify', None)
			if not path:
				continue
			comp = op(path)
			if comp is None:
				res['ok'], res['why'] = False, 'gone after reload'
				continue
			res['ops'] = len(comp.findChildren())
			errs = comp.errors(recurse=True)
			if errs:
				res['ok'], res['why'] = False, errs.splitlines()[0][:140]

	def _refuseReason(self, comp):
		"""Why this COMP must not be touched, or '' if it may be.

		A plain `externaltox` binding is NOT a refusal -- it is the BETTER
		update path (see _rewriteBound): the file takes the new bytes and
		the COMP reloads, with no copy/destroy of an extension-bearing COMP.

		Embody's tracked rows ARE a refusal, because there the .tox is
		AUTHORED FROM the live COMP rather than installed into it -- writing
		over it destroys work, and orphaning the rows has made move
		detection delete the master .py ~20 clones sync from.

		The first line of defence is coarser and more reliable: in the
		toolkit's own SOURCE checkout nothing is updatable at all, because
		every component there is authored rather than installed -- the
		published artifacts are outputs of that project, so "updating" it
		would overwrite the work with a copy of itself. That is what should
		have stopped an artifact being written over the live AutoRes.
		"""
		if self._isAuthoredHere(comp):
			return 'authored in this project, not installed into it -- the published .tox is its output'
		rows = self._embodyRows(comp.path)
		if rows:
			return 'Embody authors its .tox (%d tracked row(s)) -- not an install' % len(rows)
		return ''

	def _isAuthoredHere(self, comp):
		"""Is `comp` one of the components THIS project authors?

		Two conditions, both required. The project must be the toolkit's own
		source tree -- detected by the packaging generator sitting beside it,
		which no install has -- AND the component must live in the container
		that source tree exports from, which is the one holding this UPDATER.

		Both halves matter: without the first, a normal user install would
		refuse to update itself; without the second, a scratch copy staged
		elsewhere in the source project could not be updated either, and
		that is exactly how this path gets tested.

		The export container is read from the generator's own TOOLKIT
		constant, NOT taken as this UPDATER's parent: the updater running
		the check may itself be a scratch install (that is the self-update
		rehearsal), and anchoring home to its parent made such a copy lock
		its own siblings as "authored".
		"""
		gen = os.path.join(project.folder, 'packaging', 'build_manifest.py')
		if not os.path.exists(gen):
			return False
		home = ''
		try:
			with open(gen) as f:
				for line in f:
					if line.startswith('TOOLKIT'):
						home = line.split('=', 1)[1].strip().strip('\'"')
						break
		except Exception:
			pass
		if not home:
			parent = self.ownerComp.parent()
			home = parent.path if parent is not None else ''
		return bool(home) and comp.parent() is not None \
			and comp.parent().path == home

	def _boundPath(self, comp):
		"""Absolute path of the .tox this COMP loads from, or '' if it is
		embedded in the .toe."""
		p = getattr(comp.par, 'externaltox', None)
		en = getattr(comp.par, 'enableexternaltox', None)
		if p is None or (en is not None and not en.eval()):
			return ''
		v = str(p.eval()).strip().replace('\\', '/')
		if not v:
			return ''
		if os.path.isabs(v):
			return v
		return os.path.join(project.folder, v).replace('\\', '/')

	def _embodyRows(self, comp_path):
		"""Externalization rows Embody tracks under this COMP."""
		tsv = os.path.join(project.folder, 'externalizations.tsv')
		if not os.path.exists(tsv):
			return []
		prefix = comp_path + '/'
		hits = []
		try:
			with open(tsv, 'r', encoding='utf-8') as f:
				for line in f:
					path = line.split('\t', 1)[0]
					if path == comp_path or path.startswith(prefix):
						hits.append(path)
		except Exception as e:
			debug('UPDATER: could not read externalizations.tsv (%s)' % e)
		return hits

	def _staging(self):
		"""Cooking-disabled staging home. A live copy of a registry master
		otherwise promotes itself to the /sys global and destroys the
		running one -- cooking must be off BEFORE the tox loads."""
		quiet = op('/sys/quiet')
		if quiet is None:
			raise RuntimeError('/sys/quiet is missing -- nowhere safe to stage')
		stage = quiet.op(STAGE_COMP)
		if stage is None:
			stage = quiet.create(baseCOMP, STAGE_COMP)
		stage.allowCooking = False
		return stage

	def _isSelf(self, name, target=None):
		"""Is `name` the package this extension is running inside?"""
		root = self._root(target)
		comp = root.op(name) if root is not None else None
		if comp is None:
			return False
		me_path = self.ownerComp.path
		return me_path == comp.path or me_path.startswith(comp.path + '/')

	def _selfUpdate(self, step, target=None):
		"""Replace the package this extension lives in, from a DETACHED
		script.

		The replacement destroys the DAT this code came from, so the work
		cannot reference `self` or any op inside the package -- the script
		text carries only literal paths and is owned by TDResources' run
		queue, not by anything being replaced.

		NOT live-verified: on a dev checkout this package is externaltox-
		bound and therefore refused, and a scratch target can never be the
		package that is actually running. Treat a failure here as "re-drop
		the UPDATER tox by hand", not as a corrupted install -- by the time
		this runs, every other package has already landed.
		"""
		root = self._root(target)
		dest = root.op(step['name'])
		if dest is None:
			return {'package': step['name'], 'ok': False, 'why': 'not present in this project'}
		refuse = self._refuseReason(dest)
		if refuse:
			return {'package': step['name'], 'ok': False, 'why': 'refused: ' + refuse}
		path = step['path']
		if not os.path.exists(path):
			return {'package': step['name'], 'ok': False, 'why': 'no artifact in the store'}
		digest = _sha256(path)
		if step.get('sha256') and digest != step['sha256']:
			return {'package': step['name'], 'ok': False, 'why': 'store copy fails its hash'}
		# record BEFORE the swap: afterwards there is no `self` left to do it
		self.RecordInstalled(step['name'], digest, step.get('release', ''), target)
		script = _SELF_UPDATE % {'tox': path, 'dest': dest.path, 'name': step['name'],
								 'stage': STAGE_COMP}
		run(script, delayFrames=5, delayRef=op.TDResources)
		return {'package': step['name'], 'ok': True, 'why': 'self-replacement scheduled'}

	def _rewriteBound(self, comp, bound, step, digest, target=None):
		"""Update a package that lives in a file: write the file, reload it.

		The clean path. No copy/destroy of an extension-bearing COMP (the
		crash-prone case), no docked-op juggling, and the change is a file
		the user can see and version-control. When the binding already
		points AT the store artifact -- palette-shared installs -- the
		refresh has written those bytes already and this is only a reload.

		Settings ride through exactly as they do for a replacement: saved
		before the pass by ConfigRegistry.SaveAll(), and reloaded by each
		tool's own host when it re-registers after the reload. User data
		lives in the palette JSON, not in the .tox, so it is never in the
		bytes being overwritten.
		"""
		name = step['name']
		try:
			if os.path.normcase(os.path.abspath(bound)) != \
					os.path.normcase(os.path.abspath(step['path'])):
				folder = os.path.dirname(bound)
				if folder:
					os.makedirs(folder, exist_ok=True)
				shutil.copyfile(step['path'], bound)
		except Exception as e:
			return {'package': name, 'ok': False,
					'why': 'could not write %s (%s)' % (bound, str(e)[:80])}
		comp.par.enableexternaltoxpulse.pulse()
		self.RecordInstalled(name, digest, step.get('release', ''), target)
		# The pulse's effect is not visible in this same call, so the count
		# and error check happen on the next drain tick rather than here.
		return {'package': name, 'ok': True, 'how': 'rewrote %s' % bound,
				'verify': comp.path}

	def _replacePackage(self, step, target=None):
		name = step['name']
		root = self._root(target)
		dest = root.op(name)
		if dest is None:
			return {'package': name, 'ok': False, 'why': 'not present in this project'}
		refuse = self._refuseReason(dest)
		if refuse:
			return {'package': name, 'ok': False, 'why': 'refused: ' + refuse}
		path = step['path']
		if not os.path.exists(path):
			return {'package': name, 'ok': False, 'why': 'no artifact in the store'}
		digest = _sha256(path)
		if step.get('sha256') and digest != step['sha256']:
			return {'package': name, 'ok': False, 'why': 'store copy fails its hash'}

		bound = self._boundPath(dest)
		if bound:
			return self._rewriteBound(dest, bound, step, digest, target)

		stage = self._staging()
		before = {c.id for c in stage.children}
		stage.loadTox(path)
		fresh = [c for c in stage.children if c.id not in before]
		if not fresh:
			return {'package': name, 'ok': False, 'why': 'artifact loaded nothing'}
		src = fresh[0]
		try:
			new = TDF.replaceOp(dest, src)
		finally:
			src.destroy()
		if new.name != name:
			new.name = name  # TD numbers on collision; the manifest name wins
		self.RecordInstalled(name, digest, step.get('release', ''), target)
		errs = new.errors(recurse=True)
		return {'package': name, 'ok': not errs, 'ops': len(new.findChildren()),
				'why': errs.splitlines()[0][:140] if errs else ''}

	# ------------------------------------------------------------------
	# reporting
	# ------------------------------------------------------------------

	def _report(self):
		job = self._job or {}
		kind = job.get('kind', 'check')
		job['stage'] = 'done' if not job.get('failed') else 'failed'

		if kind == 'refresh':
			st = self.StoreStatus()
			self._status('store %s: %d verified, %d MB%s'
						 % (st.get('release', '?'), st.get('verified', 0),
							st.get('total_mb', 0),
							'; FAILED: ' + ', '.join(job.get('failed', []))
							if job.get('failed') else ''))
			return {'ok': st.get('ok') and not job.get('failed'), 'store': st,
					'failed': job.get('failed', [])}

		cmp_ = self.Compare(job.get('target'))
		self._writeUpdates(cmp_['rows'])
		self.IsUpdatable.val = bool(cmp_['updates'])

		if kind == 'check':
			self._status('%d update(s) available%s'
						 % (len(cmp_['updates']),
							': ' + ', '.join(cmp_['updates']) if cmp_['updates'] else ''))
			return {'ok': cmp_['ok'], 'why': cmp_['why'], 'release': cmp_.get('release', ''),
					'updates': cmp_['updates'], 'rows': cmp_['rows']}

		done = [r['package'] for r in job.get('results', []) if r.get('ok')]
		bad = [r for r in job.get('results', []) if not r.get('ok')]
		self._status('updated %d package(s)%s'
					 % (len(done),
						'; FAILED: ' + ', '.join('%s (%s)' % (r['package'], r.get('why', ''))
												 for r in bad) if bad else ''))
		return {'ok': not bad and not job.get('failed'), 'updated': done,
				'failed': bad + [{'why': f} for f in job.get('failed', [])],
				'remaining': cmp_['updates']}

	# ------------------------------------------------------------------
	# parameter callbacks (extensionParExec dispatches par name -> method)
	# ------------------------------------------------------------------

	def Check(self, _=None):
		if self.ownerComp.par.Enabled.eval():
			self.CheckUpdates()

	def Update(self, _=None):
		if self.ownerComp.par.Enabled.eval():
			self.UpdateProject()

	def Refreshstore(self, _=None):
		self.RefreshStore()
