
'''Info Header Start
Name : ExtUpdater
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
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

WHAT DECIDES "NEWER" is the `Pkgversion` par the component declares about
ITSELF, compared against the version the store publishes for it (Compare).
Hashes verify downloads; versions decide updates. An artifact hash cannot
answer "is this newer?" because a .tox does not export to reproducible
bytes -- the same component exported twice differs, so hash-based staleness
was tried and reversed. The release label is for humans and changelogs.

Reading the LIVE par, not a record of what was installed, is what makes
this work for a package embedded in the .toe: there is no file to consult,
but the component still says what it is, and no side table can drift out of
truth.

The `installed` table in the toolkit root remains the audit trail --
package -> the sha256 it was installed FROM -- and answers exactly one
question Compare cannot: which packages were installed but are no longer
present. It is PROJECT state, so it travels with the project, which is also
what makes an interrupted update pass safe to simply run again.

Never hash the live COMP for anything: a .tox re-saved inside a project no
longer hashes to what was published.
"""

import hashlib
import json
import os
import shutil
import time
from urllib.parse import unquote, urlparse

MANIFEST_NAME = 'manifest.json'

# ---------------------------------------------------------------------------
# Discovery -- the one thing this component hardcodes.
#
# PINNED FOREVER. Every copy of this updater ever shipped reads exactly
# these URLs, in this order, and no update can change them for a copy
# already in the field: editing this list mints a NEW GENERATION of the
# component, it does not fix the installs that are already out there.
# Everything else -- where the manifest lives, which builds may still run,
# what message reaches every install -- is data in the document these URLs
# serve. Change the data, never the file.
#
# Two independent origins, three names:
#   1. the bucket itself (Cloudflare R2)
#   2. the docs site, a 200-PROXY to 1 (Vercel rewrite) -- a proxy and
#      not a copy on purpose: a hand-maintained copy someone forgot to
#      redeploy serves a wrong endpoint forever and looks perfectly healthy
#   3. GitHub raw -- the only genuinely independent origin, and therefore
#      the one that must be published by the release step and never by hand
#
# Pin 2 must name a host THIS Vercel project actually serves. Measured
# 2026-08-28, before any of this shipped: the old pin 2 named the apex
# functionstore.xyz, which belongs to a DIFFERENT Vercel project and 308s
# to www -- so vercel.json's rewrite could never fire and the pin was dead
# on arrival. It probed as a plain 404, indistinguishable from "the file
# is not published yet", which is exactly the healthy-looking failure this
# list exists to survive. Hence the standing rule: no pin ships until
# packaging/check_pins.py has seen it serve the real document. That is
# also why all three now sit under two registrable domains rather than
# three -- a pin that is provably live beats one that is merely more
# independent on paper.
DISCOVERY_PINS = (
	'https://storage.functionstore.tools/fnstools/.well-known/fnstools.json',
	'https://functionstore.tools/.well-known/fnstools.json',
	'https://raw.githubusercontent.com/function-store/fnstools-links/main/fnstools.json',
)
DISCOVERY_NAME = 'fnstools.json'
# Last copy that PARSED. The fetch target is overwritten in place, so a
# truncated or error-page response would otherwise destroy the only
# fallback at exactly the moment it is needed.
DISCOVERY_CACHE = 'fnstools.last.json'

# ---------------------------------------------------------------------------
# Release signing -- authenticity for the two documents everything trusts.
#
# Artifact hashes verify DOWNLOADS against the manifest; nothing verified
# the manifest itself, so whoever could serve one of these URLs supplied
# both the malicious tox and the hash that blessed it. Now the manifest and
# the discovery document each ship a sidecar `<name>.sig` (Ed25519 over the
# exact file bytes, base64), signed at Stage time (packaging/sign_release.py;
# the private key lives OUTSIDE the repo).
#
# PINNED like DISCOVERY_PINS, same contract: replacing this key mints a new
# generation of the component, it never fixes installs already out there.
SIGNING_PUBKEY_HEX = '71daacb7672f0da1b2a113b727d3dd8e1c97f8b4355d70a46df2eb850fc1a118'
# The asymmetry, mirroring the TD-build floor and the kill switch:
#   * a WELL-FORMED signature that fails to verify REFUSES the document --
#     that is tamper evidence, the exact thing this exists to catch;
#   * a missing or unparseable sig is treated as UNSIGNED: allowed and
#     logged loudly while REQUIRE_SIGNED is False (documents published
#     before signing existed, and CDN error pages fetched as .sig bodies,
#     must not strand the fleet). Flip to True once every fleet install
#     has seen a signed release; unsigned then refuses too.
REQUIRE_SIGNED = False
SIG_SUFFIX = '.sig'
DISCOVERY_SIG = DISCOVERY_NAME + SIG_SUFFIX
MANIFEST_SIG = MANIFEST_NAME + SIG_SUFFIX

# The curated list of OTHER PEOPLE'S tools. Fetched and cached under a
# SUBFOLDER of the store, never beside the packages: every update mechanism
# reads the store by manifest name, so nothing in there is ever compared,
# re-hashed or updated. Linking is the default; a row carrying a pinned
# sha256 may also be placed.
COMMUNITY_NAME = 'recommendations.json'
# package -> the bytes it was installed from. Written by the installer and
# by every update; read to decide what is stale. packaging/InstallerExt.py
# writes the same four columns -- keep the two in step.
INSTALLED_DAT = 'installed'
INSTALLED_COLS = ['package', 'sha256', 'release', 'when']
UPDATES_DAT = 'updates'
UPDATES_COLS = ['package', 'state', 'installed', 'available', 'note']

# Seconds of zero progress before a fetch is called dead.
STALL_SECONDS = 45
# Discovery is a ~200 byte JSON off a CDN. A pin that has not answered in
# this long is not slow, it is dead -- and three dead pins must still fall
# back to the cached document inside a wait a human will sit through.
DISCOVERY_STALL_SECONDS = 12


# Runs AFTER the DAT holding this file is destroyed, so it may reference
# nothing inside the package -- only literals and ops that outlive it.
_SELF_UPDATE = """
_dest = op(%(dest)r)
if _dest is None:
	debug('UPDATER: self-update aborted, target vanished')
else:
	_root = _dest.parent()
	_nx, _ny = _dest.nodeX, _dest.nodeY
	_dest.destroy()
	_before = {c.id for c in _root.children}
	_root.loadTox(%(tox)r)
	_fresh = [c for c in _root.children if c.id not in _before]
	if _fresh:
		_fresh[0].name = %(name)r
		_fresh[0].nodeX, _fresh[0].nodeY = _nx, _ny
		debug('UPDATER: replaced itself from %(tox)s')
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


def _tdBuildTooOld(min_build, this_build):
	"""Is `this_build` older than the artifact's floor? ('2025.33070')

	Answers False for anything it cannot read -- a manifest predating the
	field, a malformed value, an unparseable running build. A floor is a
	guard against a KNOWN incompatibility, so an unknown must never turn
	into a refusal to update; that would strand every install the moment a
	build string changed shape.
	"""
	def parts(v):
		chunks = str(v or '').strip().split('.')
		if len(chunks) != 2 or not all(c.isdigit() for c in chunks):
			return None
		return tuple(int(c) for c in chunks)

	want, have = parts(min_build), parts(this_build)
	if want is None or have is None:
		return False
	return have < want


def _sha256(path):
	h = hashlib.sha256()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(1 << 20), b''):
			h.update(chunk)
	return h.hexdigest()


# --- Ed25519 verify (RFC 8032), embedded -----------------------------------
# TouchDesigner ships no crypto package and a shipped DAT must be
# self-contained, so verification lives here in full. VERIFY ONLY -- this
# component never holds anything that can sign. Cross-checked against
# packaging/ed25519_ref.py, the RFC's own vectors, and node:crypto by
# tests/test_release_signing.py. ~10 ms per call, run twice per pass.

_ED_P = 2 ** 255 - 19
_ED_L = 2 ** 252 + 27742317777372353535851937790883648493
_ED_D = (-121665 * pow(121666, _ED_P - 2, _ED_P)) % _ED_P
_ED_I = pow(2, (_ED_P - 1) // 4, _ED_P)


def _ed_recover_x(y, sign):
	xx = (y * y - 1) * pow(_ED_D * y * y + 1, _ED_P - 2, _ED_P) % _ED_P
	x = pow(xx, (_ED_P + 3) // 8, _ED_P)
	if (x * x - xx) % _ED_P != 0:
		x = x * _ED_I % _ED_P
	if (x * x - xx) % _ED_P != 0:
		return None
	if x & 1 != sign:
		x = _ED_P - x
	return x


_ED_BY = 4 * pow(5, _ED_P - 2, _ED_P) % _ED_P
_ED_BX = _ed_recover_x(_ED_BY, 0)
_ED_B = (_ED_BX, _ED_BY, 1, _ED_BX * _ED_BY % _ED_P)


def _ed_add(p, q):
	a = (p[1] - p[0]) * (q[1] - q[0]) % _ED_P
	b = (p[1] + p[0]) * (q[1] + q[0]) % _ED_P
	c = 2 * p[3] * q[3] * _ED_D % _ED_P
	d = 2 * p[2] * q[2] % _ED_P
	e, f, g, h = b - a, d - c, d + c, b + a
	return (e * f % _ED_P, g * h % _ED_P, f * g % _ED_P, e * h % _ED_P)


def _ed_mul(s, p):
	q = (0, 1, 1, 0)
	while s > 0:
		if s & 1:
			q = _ed_add(q, p)
		p = _ed_add(p, p)
		s >>= 1
	return q


def _ed_decompress(b):
	n = int.from_bytes(b, 'little')
	y = n & ((1 << 255) - 1)
	if y >= _ED_P:
		return None
	x = _ed_recover_x(y, n >> 255)
	if x is None:
		return None
	return (x, y, 1, x * y % _ED_P)


def _ed25519_verify(pub, sig, msg):
	"""32-byte public key, 64-byte signature, message bytes -> bool."""
	if len(pub) != 32 or len(sig) != 64:
		return False
	a = _ed_decompress(pub)
	r = _ed_decompress(sig[:32])
	if a is None or r is None:
		return False
	s = int.from_bytes(sig[32:], 'little')
	if s >= _ED_L:
		return False
	k = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(),
					   'little') % _ED_L
	lhs, rhs = _ed_mul(s, _ED_B), _ed_add(r, _ed_mul(k, a))
	return ((lhs[0] * rhs[2] - rhs[0] * lhs[2]) % _ED_P == 0
			and (lhs[1] * rhs[2] - rhs[1] * lhs[2]) % _ED_P == 0)


def _signatureState(doc_path, sig_path):
	"""'verified' | 'unsigned' | 'bad' for a document + sidecar sig.

	'bad' means a WELL-FORMED 64-byte signature that fails against the
	pinned key -- tamper evidence, always refused. Anything that cannot
	even be read as a signature (absent file, CDN error page fetched as
	the .sig body, truncated base64) is 'unsigned' -- see REQUIRE_SIGNED
	for what that refuses."""
	import base64 as _b64
	try:
		with open(doc_path, 'rb') as f:
			body = f.read()
	except Exception:
		return 'unsigned'
	sig = None
	try:
		with open(sig_path, 'r', encoding='utf-8', errors='ignore') as f:
			raw = f.read().strip()
		if raw and len(raw) < 200:
			sig = _b64.b64decode(raw, validate=True)
	except Exception:
		sig = None
	if sig is None or len(sig) != 64:
		return 'unsigned'
	pub = bytes.fromhex(SIGNING_PUBKEY_HEX)
	return 'verified' if _ed25519_verify(pub, sig, body) else 'bad'


def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass


FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class ExtUpdater:
	"""Update motions for the toolkit, decided by declared versions."""

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		# The wiki button colours itself from this; it now means "this
		# project has packages the store has newer bytes for".
		self.IsUpdatable = tdu.Dependency(False)
		self._job = None
		self._place = None          # community placement, separate from a pass
		fnsLog('UPDATER: init')

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

	def _parBool(self, name, default=True):
		p = getattr(self.ownerComp.par, name, None)
		return default if p is None else bool(p.eval())

	def _discoveryPath(self):
		return '%s/%s' % (self.StoreFolder(), DISCOVERY_NAME)

	def _discoveryCachePath(self):
		return '%s/%s' % (self.StoreFolder(), DISCOVERY_CACHE)

	def _readDiscovery(self, path=None):
		"""A parsed discovery document, or None.

		Reads the last copy that PARSED, not the last copy that arrived --
		see DISCOVERY_CACHE. A document with no usable manifest endpoint is
		treated as absent: half a document is worse than none, because it
		would override a working `Baseurl` with nothing.
		"""
		path = path or self._discoveryCachePath()
		try:
			with open(path, 'r', encoding='utf-8') as f:
				doc = json.load(f)
		except Exception:
			return None
		if not isinstance(doc, dict):
			return None
		base = str((doc.get('endpoints') or {}).get('manifest', '')).strip()
		return doc if base else None

	def DiscoveredBase(self):
		"""Where discovery says the manifest lives, or '' if it has never
		successfully been read on this machine."""
		doc = self._readDiscovery()
		if not doc:
			return ''
		return str(doc['endpoints']['manifest']).rstrip('/')

	def BaseUrl(self):
		"""The manifest base this pass should use.

		Precedence, and each rung exists for a reason:

		1. A LOCAL `Baseurl` (a bare path or file://) always wins. That is
		   the mirror / offline test rail the whole flow is exercised
		   against, and it must never be second-guessed by a network
		   lookup.
		2. Discovery, when `Usediscovery` is on. This is what lets the
		   bucket move without a component update.
		3. The `Baseurl` par. Also the fallback when discovery has never
		   been read on this machine -- a fresh install with no network
		   history still knows where to look, because the par ships with
		   the current endpoint.

		`Usediscovery` is a NEW par rather than "empty Baseurl means
		discovery": custom par values are PRESERVED across an in-place
		update (reloadcustom = off), so every existing install already
		holds a non-empty Baseurl and would never opt in. A new par lands
		with its build value on every install -- measured, UpdaterHardening
		section 1.
		"""
		par = self._par('Baseurl').rstrip('/')
		if self._localBase(par) is not None:
			return par
		if self._parBool('Usediscovery', True):
			found = self.DiscoveredBase()
			if found:
				return found
		return par

	def _belowFloor(self):
		"""(refused, floor) -- is THIS updater below the discovery
		document's `minimum_updater`?

		The kill switch. Refuses only on a floor it could actually parse
		and that is genuinely newer, so a malformed or missing value can
		never strand the fleet -- the same asymmetry the TD-build floor
		uses (a known incompatibility refuses; an unknown one does not).

		Enforced here, on the client. That is necessarily advisory: an
		install that never reaches a pin keeps running on its cached
		document. Server-side enforcement needs the updater to send its
		version on every request, which is a protocol change -- see
		RailHardening 2.2.
		"""
		doc = self._readDiscovery()
		floor = str((doc or {}).get('minimum_updater', '') or '').strip()
		if not floor:
			return False, ''
		return _isNewer(floor, _version(self.ownerComp)), floor

	def Notices(self):
		"""Messages the discovery document wants every install to see."""
		doc = self._readDiscovery()
		return [str(n) for n in ((doc or {}).get('notices') or []) if str(n).strip()]

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
		fnsLog(f'UPDATER: {text}')
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
		  incompatible newer, but the artifact was built on a TD newer than
		               this one -- reported, never updated. An older TD
		               loading a newer-build tox returns nothing SILENTLY,
		               so this has to be caught before the download rather
		               than discovered after the old copy is destroyed.
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
				floor = pkg.get('min_td_build', '')
				if _tdBuildTooOld(floor, app.build):
					# Refused BEFORE the download, and before the embedded
					# rail would destroy the installed copy: an older TD
					# loading a newer-build tox returns nothing silently.
					rows.append({'package': child.name, 'state': 'incompatible',
								 'installed': have, 'available': avail,
								 'note': 'needs TouchDesigner %s or newer '
										 '(this is %s)' % (floor, app.build)})
					continue
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
		# Discovery runs FIRST, and only for network passes: the local /
		# file:// rail exists precisely to bypass the network, and a pass
		# pointed at a mirror must not be re-routed by a lookup.
		if self._job['local'] is None and self._parBool('Usediscovery', True):
			self._job['stage'] = 'discovery'
			self._job['pins'] = list(DISCOVERY_PINS)
			self._status('%s: locating the manifest...' % kind)
			return self._fetchDiscovery()
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

	def _fetchDiscovery(self):
		"""Try the pins in order. One request in flight at a time.

		Failure here is NOT fatal: a machine that cannot reach any pin
		falls back to its last good document, and failing that to the
		`Baseurl` par, which ships with the current endpoint. Discovery
		makes a moved bucket survivable; it must never make an unreachable
		one worse than it already is.
		"""
		job = self._job
		if job is None:
			return {'ok': False, 'why': 'no job'}
		os.makedirs(self.StoreFolder(), exist_ok=True)
		if not job.get('pins'):
			return self._onDiscoveryExhausted()
		url = job['pins'].pop(0)
		job['pin_tried'] = url
		# Monotonic per attempt. A pin that dies slowly can produce its
		# abort callback AFTER the stall check already moved on; without
		# this both would advance and a pin would be skipped unread.
		job['pin_seq'] = job.get('pin_seq', 0) + 1
		seq = job['pin_seq']
		job['pin_at'] = absTime.seconds
		dl = self.ownerComp.op('fileDownloader')
		if dl is not None:
			try:
				dl.AbortAll()      # one pin in flight at a time
			except Exception:
				pass
		self._download(url, DISCOVERY_NAME)
		run('args[0]._discoveryStalled(%d)' % seq, self,
			delayFrames=60, delayRef=op.TDResources)
		return {'ok': True, 'why': 'locating (async)'}

	def _discoveryStalled(self, seq):
		"""A pin that never opens produces NO callback at all -- the same
		silent hang _watchdog covers for artifacts. That watchdog only
		watches the 'artifacts' stage, so discovery needs its own or a
		dead first pin would wedge every pass before it started."""
		job = self._job
		if job is None or job.get('stage') != 'discovery':
			return
		if job.get('pin_seq') != seq:
			return                                  # this attempt resolved
		if absTime.seconds - job.get('pin_at', 0) < DISCOVERY_STALL_SECONDS:
			run('args[0]._discoveryStalled(%d)' % seq, self,
				delayFrames=60, delayRef=op.TDResources)
			return
		if job.get('sig_wait') == 'discovery':
			# The DOCUMENT arrived; only its signature is hanging. That is
			# an availability problem, not tamper evidence -- classify with
			# the sig absent (the unsigned path decides) rather than
			# discarding a good document over a slow sidecar.
			return self._onDiscoverySig()
		fnsLog('UPDATER: discovery pin did not answer in %ds (%s)'
			   % (DISCOVERY_STALL_SECONDS, job.get('pin_tried', '')),
			   level='WARNING')
		self._fetchDiscovery()

	def _advanceDiscovery(self, seq):
		"""Try the next pin, unless a newer attempt already started."""
		job = self._job
		if job is None or job.get('stage') != 'discovery':
			return
		if job.get('pin_seq') != seq:
			return
		self._fetchDiscovery()

	def _onDiscovery(self):
		"""A pin answered. Accept it only if it PARSES and names an
		endpoint -- an error page or a truncated body is a failed pin, not
		a new configuration."""
		job = self._job
		if job is None:
			return {'ok': False, 'why': 'no job'}
		doc = self._readDiscovery(self._discoveryPath())
		if not doc:
			fnsLog('UPDATER: discovery pin returned nothing usable (%s)'
				   % job.get('pin_tried', ''), level='WARNING')
			return self._fetchDiscovery()        # next pin
		# The document parsed; its signature now decides whether this
		# pin's answer is trusted. A stale sig left by a previous pin must
		# not judge these bytes, so clear it before fetching.
		try:
			os.remove('%s/%s' % (self.StoreFolder(), DISCOVERY_SIG))
		except Exception:
			pass
		job['sig_wait'] = 'discovery'
		job['pin_at'] = absTime.seconds          # restart the stall clock
		self._download(job.get('pin_tried', '') + SIG_SUFFIX, DISCOVERY_SIG)
		return {'ok': True, 'why': 'verifying discovery (async)'}

	def _onDiscoverySig(self):
		"""The discovery signature arrived (or provably will not). Decide.

		Promotion to the last-good cache happens HERE, not at parse time:
		only a document that passed the signature policy may become the
		fallback every offline pass trusts."""
		job = self._job
		if job is None or job.get('stage') != 'discovery':
			return
		job['sig_wait'] = None
		pin = job.get('pin_tried', '')
		state = _signatureState(self._discoveryPath(),
								'%s/%s' % (self.StoreFolder(), DISCOVERY_SIG))
		if state == 'bad':
			fnsLog('UPDATER: discovery signature INVALID (%s) -- refusing '
				   'this pin' % pin, level='ERROR')
			return self._fetchDiscovery()        # next pin
		if state == 'unsigned':
			if REQUIRE_SIGNED:
				fnsLog('UPDATER: discovery document unsigned (%s) -- refused, '
					   'signing is required' % pin, level='ERROR')
				return self._fetchDiscovery()
			fnsLog('UPDATER: discovery document is UNSIGNED (%s) -- accepted '
				   'during the signing transition' % pin, level='WARNING')
		else:
			fnsLog('UPDATER: discovery signature verified (%s)' % pin)
		try:
			shutil.copyfile(self._discoveryPath(), self._discoveryCachePath())
		except Exception as e:
			debug('UPDATER: could not cache discovery (%s)' % e)
		return self._afterDiscovery()

	def _onDiscoveryExhausted(self):
		"""Every pin failed. Carry on with whatever we already knew."""
		cached = self.DiscoveredBase()
		fnsLog('UPDATER: no discovery pin reachable; using %s'
			   % ('the last good document' if cached else 'the Baseurl parameter'),
			   level='WARNING')
		return self._afterDiscovery()

	def _afterDiscovery(self):
		"""Re-resolve the base now that discovery may have changed it, run
		the kill switch, then proceed to the manifest."""
		job = self._job
		refused, floor = self._belowFloor()
		if refused:
			mine = _version(self.ownerComp)
			why = ('this updater (%s) is below the minimum supported version '
				   '(%s) -- update FNS_Updater by re-dropping the current '
				   'FNSTools.tox, then try again' % (mine or 'unversioned', floor))
			fnsLog('UPDATER: refused by minimum_updater (%s < %s)' % (mine, floor),
				   level='ERROR')
			return self._fail(why)
		for note in self.Notices():
			fnsLog('UPDATER notice: %s' % note, level='INFO')
		base = self.BaseUrl()
		if not base:
			return self._fail('no manifest endpoint: discovery gave none and '
							  'no Baseurl is set')
		if base != job['base']:
			fnsLog('UPDATER: endpoint moved to %s' % base, level='INFO')
		job['base'] = base
		job['local'] = self._localBase(base)
		job['stage'] = 'manifest'
		self._status('%s: fetching manifest...' % job['kind'])
		return self._fetchManifest()

	def _fetchManifest(self):
		job = self._job
		dest_dir = self.StoreFolder()
		os.makedirs(dest_dir, exist_ok=True)
		if job['local'] is not None:
			src = '%s/%s' % (job['local'], MANIFEST_NAME)
			if not os.path.exists(src):
				return self._fail('no manifest at %s' % src)
			shutil.copyfile(src, '%s/%s' % (dest_dir, MANIFEST_NAME))
			# The local rail exercises the SAME trust path as the network:
			# copy the sidecar sig when the mirror has one, then classify.
			sig_dst = '%s/%s' % (dest_dir, MANIFEST_SIG)
			try:
				os.remove(sig_dst)
			except Exception:
				pass
			if os.path.exists(src + SIG_SUFFIX):
				shutil.copyfile(src + SIG_SUFFIX, sig_dst)
			return self._onManifestSig()
		self._download('%s/%s' % (job['base'], MANIFEST_NAME), MANIFEST_NAME)
		return {'ok': True, 'why': 'fetching manifest (async)'}

	def _fetchManifestSig(self):
		"""The manifest arrived; fetch its signature before trusting it."""
		job = self._job
		sig_path = '%s/%s' % (self.StoreFolder(), MANIFEST_SIG)
		try:
			os.remove(sig_path)      # a stale sig must not judge fresh bytes
		except Exception:
			pass
		job['msig_seq'] = job.get('msig_seq', 0) + 1
		job['msig_at'] = absTime.seconds
		self._download('%s/%s' % (job['base'], MANIFEST_SIG), MANIFEST_SIG)
		run('args[0]._manifestSigStalled(%d)' % job['msig_seq'], self,
			delayFrames=60, delayRef=op.TDResources)
		return {'ok': True, 'why': 'verifying manifest (async)'}

	def _manifestSigStalled(self, seq):
		"""Same silent-hang cover the discovery sig gets: the manifest is
		here, only its sidecar is hanging -- classify with the sig absent
		rather than wedging the pass."""
		job = self._job
		if (job is None or job.get('msig_seq') != seq
				or job.get('manifest_sig') is not None):
			return
		if absTime.seconds - job.get('msig_at', 0) < DISCOVERY_STALL_SECONDS:
			run('args[0]._manifestSigStalled(%d)' % seq, self,
				delayFrames=60, delayRef=op.TDResources)
			return
		self._onManifestSig()

	def _onManifestSig(self):
		"""Signature verdict for the manifest, then on to the real work.

		'bad' FAILS THE PASS: a well-formed signature that does not verify
		against the pinned key means these are not the bytes that were
		signed, and installing from them is the exact outcome this exists
		to prevent."""
		job = self._job
		if job is None:
			return {'ok': False, 'why': 'no job'}
		if job.get('manifest_sig') is not None:
			return {'ok': True, 'why': 'already classified'}
		state = _signatureState('%s/%s' % (self.StoreFolder(), MANIFEST_NAME),
								'%s/%s' % (self.StoreFolder(), MANIFEST_SIG))
		if state == 'bad':
			fnsLog('UPDATER: manifest signature INVALID -- refusing this '
				   'manifest', level='ERROR')
			return self._fail('the manifest failed signature verification -- '
							  'refusing to trust it (possible tampering, or a '
							  'mis-published release)')
		if state == 'unsigned':
			if REQUIRE_SIGNED:
				return self._fail('the manifest is unsigned and this updater '
								  'requires signed releases')
			fnsLog('UPDATER: manifest is UNSIGNED -- accepted during the '
				   'signing transition', level='WARNING')
		else:
			fnsLog('UPDATER: manifest signature verified')
		job['manifest_sig'] = state
		return self._onManifest()

	def _download(self, url, filename, gated=False):
		"""One file into the store. dwnldCopy=False overwrites: a refresh
		that silently kept the old bytes would be worse than no refresh.

		A gated artifact carries a bearer token; nothing else does. The
		vendored downloader already takes authType/oauth2Token PER CALL, so
		the manifest and every free artifact keep going out unauthenticated
		-- which matters, because they are served by a CDN that would
		otherwise see a credential it has no business holding."""
		auth = {}
		if gated:
			token = self._gatedToken()
			if token:
				auth = {'authType': 'oauth2', 'oauth2Token': token}
		self.ownerComp.op('fileDownloader').Download(
			url=url,
			location=self.StoreFolder(),
			loadIntoProj=False,
			discCopy=True,
			dwnldCopy=False,
			renameTo=filename,
			showProgress=bool(self.ownerComp.par.Showprogress.eval())
			if hasattr(self.ownerComp.par, 'Showprogress') else False,
			**auth,
		)

	def OnFileDownloaded(self, callbackInfo):
		"""Dispatch by filename -- the downloader is shared, so the arriving
		file says what it was for. Bookkeeping only; the next stage runs a
		frame later (see _later)."""
		path = str(callbackInfo.get('path') or '')
		name = os.path.basename(path)
		# Community placement runs OUTSIDE the update job -- it is one
		# user-initiated file, not a pass -- so it is dispatched first.
		if getattr(self, '_place', None) and 'community' in path.replace(chr(92), '/'):
			self._later('_onCommunityFile')
			return
		job = self._job
		if job is None:
			return
		if name == DISCOVERY_NAME:
			self._later('_onDiscovery')
			return
		if name == DISCOVERY_SIG:
			self._later('_onDiscoverySig')
			return
		if name == MANIFEST_NAME:
			self._later('_onManifest')
			return
		if name == MANIFEST_SIG:
			self._later('_onManifestSig')
			return
		if name in job.get('inflight', {}):
			self._verifyFetched(name, job['inflight'].pop(name), path)
			self._later('_pump')

	def OnDownloadAborted(self, callbackInfo):
		name = os.path.basename(str(callbackInfo.get('path') or '')) or 'download'
		if getattr(self, '_place', None):
			pending, self._place = self._place, None
			self._placeFailed(pending.get('name') or 'the community list',
							  'the download failed')
			return
		job = self._job
		if job is None:
			return
		if name == DISCOVERY_NAME:
			# A dead pin is expected, not an error: that is what having
			# more than one is for. Try the next; exhaustion falls back.
			run('args[0]._advanceDiscovery(%d)' % job.get('pin_seq', 0), self,
				delayFrames=1, delayRef=op.TDResources)
			return
		if name in (DISCOVERY_SIG, MANIFEST_SIG):
			# An aborted SIG fetch is an availability fact about a sidecar,
			# not about the document -- classify with the sig absent and
			# let the unsigned policy decide.
			self._later('_onDiscoverySig' if name == DISCOVERY_SIG
						else '_onManifestSig')
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
			# A gated item with no valid token must not go out bare: the
			# 401 error body fails the sha check downstream and reads as a
			# checksum failure -- website defect #4's class, reachable
			# when the 15-minute token expires mid-pass on a slow
			# connection. Dropped HERE, before inflight, with an auth
			# sentence that travels to the report (see _gatedWhy).
			if item.get('gated') and not self._gatedToken():
				name = item['file'][:-4]
				job.setdefault('gated', []).append(name)
				job.setdefault('gated_reasons', {})[name] = (
					'%s: download token missing or expired -- run the '
					'update again to request a fresh one' % name)
				fnsLog('UPDATER: %s dropped -- gated item with no valid '
					   'token' % name, level='WARNING')
				continue
			job['inflight'][item['file']] = item['sha']
			self._download(item['url'], item['file'], gated=item.get('gated'))
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
		if not want:
			# A manifest row with no hash is not permission to skip the
			# check: nothing vouches for these bytes, so they never enter
			# the store.
			try:
				os.remove(path)
			except Exception:
				pass
			job['failed'].append('%s: manifest carries no sha256 (refused)' % name)
			return
		digest = _sha256(path)
		if digest != want:
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
		# Nothing downstream of this line runs on an unclassified manifest:
		# the network path detours through the signature fetch exactly once
		# (the local rail classifies synchronously in _fetchManifest).
		if job.get('manifest_sig') is None:
			return self._fetchManifestSig()
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
						 'sha': (pkg['artifact'] or {}).get('sha256', ''),
						 'gated': self._isGated(pkg)}
						for pkg in wanted]
		# Gated artifacts sit behind a Worker on the SAME host (the `plus/`
		# prefix), so the URL above is already right and only the header is
		# missing. Fetch one short-lived token for the whole pass rather
		# than one per artifact.
		if any(i['gated'] for i in job['queue']) and not self._gatedToken():
			a = self._auth()
			if a is None:
				return self._onGateDenied('no auth extension')
			self._status('%s: authorising...' % job['kind'])
			a.RequestToken(callback=self._onGateToken)
			return {'ok': True, 'why': 'authorising (async)'}
		self._pump()
		return {'ok': True, 'why': 'fetching %d artifact(s) (async)' % len(wanted)}

	def _onGateToken(self, ok, why):
		"""The gate answered. Either way the pass continues -- the free
		artifacts in this queue have nothing to do with entitlement."""
		if not ok:
			self._onGateDenied(why)
			return
		self._later('_pump')

	def _onGateDenied(self, why):
		"""Drop the gated items and fetch the rest.

		Failing the whole pass because one paid package could not be
		authorised would punish the free packages queued beside it. The
		skipped ones are REPORTED, not silently dropped: a user who cannot
		see why a package did not arrive assumes the updater is broken."""
		job = self._job
		if job is None:
			return {'ok': False, 'why': 'no job'}
		dropped = [i['file'][:-4] for i in job['queue'] if i['gated']]
		job['queue'] = [i for i in job['queue'] if not i['gated']]
		# The REASON travels with the drop, and the drop is NOT a failure.
		# Recomputing the reason at report time from local auth state turns
		# "could not reach the gate" and the gate's own "Sign in again"
		# into "your tier does not include X" -- the exact inversion
		# auth_client_callbacks warns must never happen. And routing these
		# through job['failed'] flipped ok False for what is a refusal,
		# not a malfunction.
		reasons = job.setdefault('gated_reasons', {})
		for name in dropped:
			reasons[name] = '%s: %s' % (name, why)
		job.setdefault('gated', []).extend(dropped)
		if dropped:
			fnsLog('UPDATER: %d gated package(s) skipped -- %s'
				   % (len(dropped), why), level='WARNING')
		self._later('_pump')
		return {'ok': True, 'why': why}

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
			# a scoped refresh fetches just these; [] is manifest-only
			names = job.get('names')
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
			# A gated package this install is not entitled to is SKIPPED,
			# not attempted. Asking would 403, and _verifyFetched would
			# reject the error body on its hash -- correct, but it would
			# report as a download failure rather than as "you do not have
			# this", which is the thing the user needs told.
			if self._isGated(pkg) and not self._entitled(pkg['name']):
				job.setdefault('gated', []).append(pkg['name'])
				continue
			out.append(pkg)
		return out

	# ------------------------------------------------------------------
	# community tools -- other people's, placed but never MANAGED
	# ------------------------------------------------------------------

	def _communityPath(self, *parts):
		"""A SUBFOLDER of the store, and that is load-bearing.

		Every update mechanism reads the store by asking the manifest for a
		name and looking at `<store>/<name>.tox` -- `_needed`, `StoreStatus`
		and `RefreshStore` all iterate manifest rows and none of them walks
		the directory. So nothing placed here is ever seen, compared,
		re-hashed or updated. That is the whole promise of this list.
		"""
		return '/'.join([self.StoreFolder(), 'community'] + [p for p in parts])

	def CommunityList(self):
		"""The curated list, from its cached copy. [] when never fetched."""
		try:
			with open(self._communityPath(COMMUNITY_NAME), 'r', encoding='utf-8') as f:
				doc = json.load(f)
			return [t for t in doc.get('tools', []) if isinstance(t, dict)]
		except Exception:
			return []

	def _communityRow(self, name):
		for t in self.CommunityList():
			if str(t.get('name', '')) == name:
				return t
		return None

	def _isPlaceable(self, row):
		"""Placement needs a PINNED hash. The pin is the whole safety
		argument -- it promises these are the exact bytes a curator looked
		at. Without one this stays a link, because installing whatever
		happens to be at someone else's URL today is not something we can
		stand behind."""
		sha = str((row or {}).get('sha256', '')).strip().lower()
		return bool(str((row or {}).get('tox_url', '')).strip()
					and len(sha) == 64 and all(c in '0123456789abcdef' for c in sha))

	def RefreshCommunity(self):
		"""Fetch the curated list. Cheap, and independent of any release."""
		if self._job is not None and self._job.get('stage') not in ('done', 'failed'):
			return {'ok': False, 'why': 'an update job is running'}
		base = self.BaseUrl()
		if not base:
			return {'ok': False, 'why': 'no base url'}
		os.makedirs(self._communityPath(), exist_ok=True)
		local = self._localBase(base)
		if local is not None:
			src = '%s/%s' % (local, COMMUNITY_NAME)
			if not os.path.exists(src):
				return {'ok': False, 'why': 'no %s at %s' % (COMMUNITY_NAME, local)}
			shutil.copyfile(src, self._communityPath(COMMUNITY_NAME))
			return {'ok': True, 'tools': len(self.CommunityList())}
		self._place = {'stage': 'list', 'name': None}
		self.ownerComp.op('fileDownloader').Download(
			url='%s/%s' % (base, COMMUNITY_NAME),
			location=self._communityPath(), loadIntoProj=False,
			discCopy=True, dwnldCopy=False, renameTo=COMMUNITY_NAME,
			showProgress=False)
		return {'ok': True, 'why': 'fetching the list (async)'}

	def PlaceCommunityTool(self, name, target=None):
		"""Download one community tool and place it in the project.

		NOT an install. Nothing is recorded, nothing is versioned, and no
		update pass will ever touch it again -- if the author ships a new
		one, the curated list changes and the user places it again. That is
		the deal this list makes, and keeping it is why the bytes never
		enter the store proper or the manifest.
		"""
		if self._job is not None and self._job.get('stage') not in ('done', 'failed'):
			return {'ok': False, 'why': 'an update job is running -- try again after it finishes'}
		row = self._communityRow(name)
		if row is None:
			return {'ok': False, 'why': 'unknown community tool %r -- refresh the list first' % name}
		if not self._isPlaceable(row):
			return {'ok': False, 'why': '%s is a link only; open %s to get it'
					% (name, row.get('url', 'the author\'s page'))}
		dest = self._root(target)
		if dest is None or not dest.valid:
			return {'ok': False, 'why': 'no target COMP'}
		os.makedirs(self._communityPath(), exist_ok=True)
		self._place = {'stage': 'tox', 'name': name, 'row': row,
					   'target': dest.path, 'file': name + '.tox'}
		self._status('fetching %s from %s...' % (name, row.get('author', 'its author')))
		self.ownerComp.op('fileDownloader').Download(
			url=row['tox_url'], location=self._communityPath(),
			loadIntoProj=False, discCopy=True, dwnldCopy=False,
			renameTo=name + '.tox',
			showProgress=bool(self.ownerComp.par.Showprogress.eval())
			if hasattr(self.ownerComp.par, 'Showprogress') else False)
		return {'ok': True, 'why': 'fetching %s (async)' % name}

	def _onCommunityFile(self):
		"""A community download landed. Verify SIZE then HASH before the
		bytes are allowed anywhere near the project."""
		job = getattr(self, '_place', None)
		if not job:
			return
		if job['stage'] == 'list':
			self._place = None
			n = len(self.CommunityList())
			fnsLog('UPDATER: community list refreshed (%d tool(s))' % n)
			self._status('community list: %d tool(s)' % n)
			return
		self._place = None
		name, row = job['name'], job['row']
		path = self._communityPath(job['file'])
		try:
			size = os.path.getsize(path)
		except OSError:
			return self._placeFailed(name, 'the download did not arrive')
		# Size first: it is free, and it turns a truncated file or an error
		# page into a specific answer instead of an opaque hash mismatch.
		want_size = row.get('bytes')
		if isinstance(want_size, int) and size != want_size:
			return self._placeFailed(name, 'wrong size (%d bytes, expected %d) -- '
									 'the author may have republished it' % (size, want_size))
		if _sha256(path) != str(row['sha256']).strip().lower():
			return self._placeFailed(
				name, 'this is not the build we checked -- %s has republished it. '
				'Get it from %s instead.' % (row.get('author', 'the author'),
											 row.get('url', 'their page')))
		dest = op(job['target'])
		if dest is None or not dest.valid:
			return self._placeFailed(name, 'the target went away')
		before = {c.id for c in dest.children}
		try:
			dest.loadTox(path)
		except Exception as e:
			return self._placeFailed(name, 'TouchDesigner refused the file (%s)' % e)
		fresh = [c for c in dest.children if c.id not in before]
		if not fresh:
			# An OLDER TD loading a newer-build tox returns nothing SILENTLY.
			return self._placeFailed(name, 'the file loaded nothing -- it may need '
									 'a newer TouchDesigner build')
		fnsLog('UPDATER: placed community tool %s by %s at %s'
			   % (name, row.get('author', '?'), fresh[0].path))
		self._status('placed %s by %s' % (name, row.get('author', '?')))
		return {'ok': True, 'placed': fresh[0].path}

	def _placeFailed(self, name, why):
		fnsLog('UPDATER: could not place %s -- %s' % (name, why), level='WARNING')
		self._status('%s: %s' % (name, why))
		return {'ok': False, 'why': why}

	# ------------------------------------------------------------------
	# gated packages
	# ------------------------------------------------------------------

	def _isGated(self, pkg):
		"""Does this package need an entitlement?

		`access` NAMES A TIER, so anything that is not the literal 'free'
		is gated. Reading it this way means a tier added later needs no
		change here -- and a manifest predating the field reads as free,
		which is right: everything predating it was."""
		return str(pkg.get('access', 'free') or 'free') != 'free'

	def _auth(self):
		try:
			return self.ownerComp.ext.ExtAuth
		except Exception:
			return None          # auth DAT absent: behave as signed out

	def _entitled(self, name):
		a = self._auth()
		return bool(a and a.IsEntitled(name))

	def _gatedToken(self):
		"""The download token for gated artifacts, or ''."""
		a = self._auth()
		return a.CachedToken() if a else ''

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

	def RefreshStore(self, names=None):
		"""Fetch the manifest, then artifacts whose bytes differ.
		Machine-wide; no project is read or touched.

		`names` scopes the artifact fetch: None mirrors the whole release
		(the Refresh Store pulse -- offline installs, shared bindings),
		a list fetches just those packages (the picker downloads exactly
		the selection at install time), and [] is manifest-only (what
		makes the picker appear in seconds instead of after the mirror).
		"""
		return self._startJob('refresh', names=names)

	def StoreStatus(self):
		"""What the store actually holds, verified against its manifest."""
		man = self.StoreManifest()
		if not man:
			return {'ok': False, 'why': 'store has no manifest -- refresh first'}
		present, missing, mismatched, gated = [], [], [], []
		total = 0
		for pkg in man.get('packages', []):
			art = pkg.get('artifact')
			if not art:
				continue
			path = self._storePath(pkg['name'])
			if not os.path.exists(path):
				# A gated package this install is not entitled to was never
				# fetched -- by design, not breakage. Counting it as missing
				# made every refresh read as a broken store (ok False, the
				# package listed missing) for a signed-out user, with no
				# sentence saying why. Its own bucket keeps the verdict
				# honest: the store holds everything it is ALLOWED to hold.
				if self._isGated(pkg) and not self._entitled(pkg['name']):
					gated.append(pkg['name'])
				else:
					missing.append(pkg['name'])
			elif _sha256(path) != art.get('sha256'):
				mismatched.append(pkg['name'])
			else:
				present.append(pkg['name'])
				total += os.path.getsize(path)
		return {'ok': not missing and not mismatched, 'release': man.get('release', ''),
				'folder': self.StoreFolder(), 'verified': len(present),
				'missing': missing, 'mismatched': mismatched, 'gated': gated,
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
		# Gated skips never entered the store; applying them would fail
		# with "no artifact in the store" beside the entitlement sentence
		# and flip ok False -- the double report the gated list exists to
		# prevent. Filtered HERE, at consumption, because the list can
		# still grow after _needed (a gate denial mid-pass drops more).
		gated_skips = set(job.get('gated') or [])
		if gated_skips:
			names = [n for n in names if n not in gated_skips]
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
		# NEVER drain inline. The manifest/artifact callbacks can arrive on
		# a worker thread (threaded downloader, headless drivers), and
		# replaceOp re-inits extensions whose registry hosts copy widgets
		# into UI surfaces -- op mutation off the main thread wedges TD
		# inside the copy with unbounded memory growth (seen live: navbar
		# RegisterWidget spinning in bar.copy). run() marshals to the main
		# thread; later steps already chain the same way.
		run('args[0]._drain()', self, delayFrames=1, delayRef=op.TDResources)
		return {'ok': True, 'why': 'applying %d package(s)' % planned}

	def _saveConfig(self):
		cfg = getattr(op, 'FNS_CONFIGREGISTRY', None)
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
		if not queue and any(r.get('verify') for r in job.get('results', [])):
			# The last package's reload is still being judged (it gets one
			# extra tick). Finishing here would leave it recorded as a
			# success nobody ever checked, which is the whole failure this
			# verification exists to catch.
			run('args[0]._drain()', self, delayFrames=3, delayRef=op.TDResources)
			return
		if not queue:
			self._settleStaleErrors(job)
			if job.get('results') and not job.get('failed'):
				# next project open offers this release's notes, once
				root = self._root(job.get('target'))
				if root is not None:
					root.store('updater_show_changelog', True)
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

	# ------------------------------------------------------------------
	# post-update changelog prompt (execute1 calls this on project start)
	# ------------------------------------------------------------------

	def ShowChangelogAfterUpdate(self):
		"""Offer this release's notes once, on the first open after an
		update. The flag is stored on the toolkit root by a successful
		update pass and cleared here; the notes come from the store
		manifest -- they ride the release, no web anything."""
		root = self.ownerComp.parent()
		if root is None or not root.fetch('updater_show_changelog', False, search=False):
			return
		root.unstore('updater_show_changelog')
		man = self.StoreManifest() or {}
		label = man.get('release', '')
		notes = str(man.get('notes', '')).strip()
		text = 'FunctionStore tools updated%s.' % (' to %s' % label if label else '')
		if notes:
			text += '\n\n' + notes[:900]
		try:
			ui.messageBox('FNS tools updated', text, buttons=['OK'])
		except Exception as e:
			debug('UPDATER: changelog prompt failed: %s' % e)

	def _settleStaleErrors(self, job):
		"""After the whole pass: recook packages that still flag errors.

		A package replaced EARLY in the pass errors when a registry master
		it clones from is replaced LATER -- its clone par momentarily
		pointed at a deleted comp, and nothing recooks an idle package, so
		the flag just sits there looking like breakage. One recook against
		the settled network clears exactly those. Deliberately a CLEANER,
		not a judge: each replacement was already verified when it landed,
		and a pre-existing quirk inside a package must not turn a clean
		pass into a reported failure.
		"""
		root = self._root(job.get('target'))
		if root is None:
			return
		for res in job.get('results', []):
			comp = root.op(res.get('package', ''))
			if comp is None or not comp.errors(recurse=True):
				continue
			try:
				comp.cook(force=True, recurse=True)
			except Exception:
				pass

	def _settleVerifications(self, job):
		"""Finish judging reloads from the previous tick.

		A COMP reloaded by pulsing its external-tox reload does not report
		its new state within the call that fired the pulse, so a rewrite
		records what it wants checked and the next frame checks it.

		Two things are judged: that the reload HAPPENED (the child ids the
		rewrite recorded are gone, because a reload recreates them) and that
		what came back is clean. The first gets one extra tick before it is
		called a failure -- a reload that has not landed yet and a reload
		that never will look identical on the first look, and only one of
		them deserves to fail the package.
		"""
		for res in job.get('results', []):
			path = res.get('verify')
			if not path:
				continue
			comp = op(path)
			if comp is None:
				res.pop('verify', None)
				res.pop('reload_token', None)
				res['ok'], res['why'] = False, 'gone after reload'
				continue
			token = res.get('reload_token')
			# An empty token means the COMP had no children to renew, so the
			# id check cannot say anything -- skip it rather than fail blind.
			if token:
				if sorted(c.id for c in comp.children) == token:
					if not res.get('reload_retried'):
						res['reload_retried'] = True
						continue          # look again next tick
					res.pop('verify', None)
					res.pop('reload_token', None)
					res.pop('reload_retried', None)
					res['ok'] = False
					res['why'] = ('reload pulse did nothing -- still the previous '
								  'contents (unreadable artifact, or a tox this '
								  'TD build refuses)')
					continue
			res.pop('verify', None)
			res.pop('reload_token', None)
			res.pop('reload_retried', None)
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
		if not step.get('sha256'):
			return {'package': step['name'], 'ok': False,
					'why': 'manifest carries no sha256 (refused)'}
		if digest != step['sha256']:
			return {'package': step['name'], 'ok': False, 'why': 'store copy fails its hash'}
		# record BEFORE the swap: afterwards there is no `self` left to do it
		self.RecordInstalled(step['name'], digest, step.get('release', ''), target)
		script = _SELF_UPDATE % {'tox': path, 'dest': dest.path,
								 'name': step['name']}
		run(script, delayFrames=5, delayRef=op.TDResources)
		return {'package': step['name'], 'ok': True, 'why': 'self-replacement scheduled'}

	def _rewriteBound(self, comp, bound, step, digest, target=None):
		"""Update a package that lives in a file: write the file, reload it.

		The clean path. No copy/destroy of an extension-bearing COMP (the
		crash-prone case), no docked-op juggling, and the change is a file
		the user can see and version-control. When the binding already
		points AT the store artifact -- palette-shared installs -- the
		refresh has written those bytes already and this is only a reload.

		Settings: what actually carries them depends on `reloadcustom`.

		  reloadcustom OFF (9 of 50 packages) -- the reload PRESERVES live
		  custom par values. Settings survive in place and need no handoff.

		  reloadcustom ON (41 of 50) -- the reload resets every custom par,
		  and the tool depends entirely on ConfigRegistry re-applying its
		  section when its host re-registers. That handoff is saved before
		  the pass by SaveAll().

		DO NOT rely on that handoff unconditionally: under `Configscope =
		project` the config file is never read OR written (docs/ConfigScope.md),
		so for the 41 there is nothing to restore from and the user's settings
		are simply lost. This is the reason the fleet is moving to
		reloadcustom off everywhere -- see docs/UpdaterHardening.md.
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
		# A reload RECREATES the children, so their ids all change. Capturing
		# them here is what lets the next tick tell a real reload from a
		# no-op: a pulse that quietly did nothing (unreadable file, a build
		# floor TD refused, a binding that no longer resolves) otherwise
		# reports success and the user is told they are on a version they
		# are not running.
		token = sorted(c.id for c in comp.children)
		comp.par.enableexternaltoxpulse.pulse()
		self.RecordInstalled(name, digest, step.get('release', ''), target)
		# The pulse's effect is not visible in this same call, so the count
		# and error check happen on the next drain tick rather than here.
		return {'package': name, 'ok': True, 'how': 'rewrote %s' % bound,
				'verify': comp.path, 'reload_token': token}

	def _backupFolder(self):
		"""Where the pre-replace exports live. One deep, per package: the
		previous version of anything the updater destroyed, so a failed
		replace is recoverable by hand even after TD is closed."""
		d = os.path.join(self.StoreFolder(), '_backup')
		os.makedirs(d, exist_ok=True)
		return d

	def _backupPackage(self, comp, name):
		"""Export the installed COMP before it is destroyed. Path, or ''.

		Deliberately NOT the store artifact: what has to come back is the
		version the user is running, with whatever this project did to it,
		not a fresh copy of what the bucket published. `.save()` writes the
		live component; a failure here is a refusal upstream, never a
		warning we proceed past.
		"""
		try:
			path = os.path.join(self._backupFolder(), '%s.tox' % name).replace('\\', '/')
			comp.save(path)
			if os.path.exists(path) and os.path.getsize(path) > 0:
				return path
			debug('UPDATER: backup of %s produced no file' % name)
		except Exception as e:
			debug('UPDATER: could not back up %s: %s' % (name, e))
		return ''

	def _restorePackage(self, root, backup, name, nx, ny, color):
		"""Put the backed-up version back after a failed replace.

		Same load rail as the replace itself, so a restore cannot fail for
		a reason the replace would not have. Returns whether the component
		is actually back -- the caller reports the difference, because
		"update failed" and "update failed and your package is gone" are
		not the same sentence.
		"""
		if not backup or not os.path.exists(backup):
			return False
		try:
			before = {c.id for c in root.children}
			root.loadTox(backup)
			fresh = [c for c in root.children if c.id not in before]
			comp = fresh[0] if fresh else root.op(name)
			if comp is None:
				return False
			if comp.name != name:
				comp.name = name
			comp.nodeX, comp.nodeY, comp.color = nx, ny, color
			debug('UPDATER: restored %s from %s' % (name, backup))
			return True
		except Exception as e:
			debug('UPDATER: could not restore %s from %s: %s' % (name, backup, e))
			return False

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
		if not step.get('sha256'):
			return {'package': name, 'ok': False,
					'why': 'manifest carries no sha256 (refused)'}
		if digest != step['sha256']:
			return {'package': name, 'ok': False, 'why': 'store copy fails its hash'}

		bound = self._boundPath(dest)
		if bound:
			return self._rewriteBound(dest, bound, step, digest, target)

		# Embedded: the SAME rail the installer uses -- destroy the old COMP,
		# loadTox the artifact live into the root. The previous mechanism
		# (stage cooking-disabled, TDF.replaceOp graft) copy/destroys an
		# extension-bearing COMP, which is TD's most fragile operation and
		# took the process down twice (off-main wedge, on-main hard crash).
		# destroy+loadTox has installed every package cleanly since the
		# bootstrap existed, and packages are self-contained root children
		# with no wires.
		#
		# It is also the one rail with a POINT OF NO RETURN: between the
		# destroy and a successful load the package does not exist. An older
		# TD loading a newer-build tox returns nothing SILENTLY, so "artifact
		# loaded nothing" is a reachable state, not a theoretical one -- and
		# it used to leave the user with the package simply gone and a row in
		# a table saying so. Export first, restore on either failure.
		nx, ny, color = dest.nodeX, dest.nodeY, dest.color
		backup = self._backupPackage(dest, name)
		if not backup:
			# Refusing is the point: without a backup the destroy below is
			# unrecoverable. A store we cannot write to is a real signal
			# (full disk, permissions), not a reason to gamble the package.
			return {'package': name, 'ok': False,
					'why': 'could not back up the installed version -- '
						   'refusing to replace it (check the store folder is writable)'}
		dest.destroy()
		before = {c.id for c in root.children}
		try:
			root.loadTox(path)
		except Exception as e:
			restored = self._restorePackage(root, backup, name, nx, ny, color)
			return {'package': name, 'ok': False,
					'why': 'loadTox failed: %s%s' % (
						str(e)[:110],
						' (previous version restored)' if restored
						else ' AND THE BACKUP COULD NOT BE RESTORED: ' + backup)}
		fresh = [c for c in root.children if c.id not in before]
		new = fresh[0] if fresh else root.op(name)
		if new is None:
			restored = self._restorePackage(root, backup, name, nx, ny, color)
			return {'package': name, 'ok': False,
					'why': 'artifact loaded nothing%s' % (
						' -- previous version restored' if restored
						else ' AND THE BACKUP COULD NOT BE RESTORED: ' + backup)}
		if new.name != name:
			new.name = name  # TD numbers on collision; the manifest name wins
		new.nodeX, new.nodeY, new.color = nx, ny, color
		self.RecordInstalled(name, digest, step.get('release', ''), target)
		errs = new.errors(recurse=True)
		if errs:
			# one recook with extensions up separates init-order noise
			# (ext.X read before the ext existed) from real breakage
			try:
				new.cook(force=True, recurse=True)
			except Exception:
				pass
			errs = new.errors(recurse=True)
		return {'package': name, 'ok': not errs, 'ops': len(new.findChildren()),
				'why': errs.splitlines()[0][:140] if errs else ''}

	# ------------------------------------------------------------------
	# reporting
	# ------------------------------------------------------------------

	def _gatedWhy(self, job):
		"""The skipped-gated names and their sentences, for any report
		kind. A drop that carries its own stamped reason (gate
		unreachable, session expired -- see _onGateDenied) speaks it
		verbatim; only the local entitlement skip falls back to
		MissingFor, because there the local auth state IS the reason."""
		gated = sorted(set(job.get('gated') or []))
		_a = self._auth()
		reasons = job.get('gated_reasons') or {}
		why = [reasons.get(n)
			   or (_a.MissingFor(n) if _a
				   else '%s needs a supporter account.' % n)
			   for n in gated]
		return gated, why

	def _report(self):
		job = self._job or {}
		kind = job.get('kind', 'check')
		job['stage'] = 'done' if not job.get('failed') else 'failed'

		if kind == 'refresh':
			st = self.StoreStatus()
			gated, why_gated = self._gatedWhy(job)
			self._status('store %s: %d verified, %d MB%s%s'
						 % (st.get('release', '?'), st.get('verified', 0),
							st.get('total_mb', 0),
							'; FAILED: ' + ', '.join(job.get('failed', []))
							if job.get('failed') else '',
							'; ' + ' '.join(why_gated) if why_gated else ''))
			return {'ok': st.get('ok') and not job.get('failed'), 'store': st,
					'failed': job.get('failed', []),
					'gated': gated, 'gated_why': why_gated}

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
		# Gated packages that were skipped are NOT failures, and must not
		# read as silence either: say which, and why (see _gatedWhy).
		gated, why_gated = self._gatedWhy(job)
		self._status('updated %d package(s)%s%s'
					 % (len(done),
						'; FAILED: ' + ', '.join('%s (%s)' % (r['package'], r.get('why', ''))
												 for r in bad) if bad else '',
						'; ' + ' '.join(why_gated) if why_gated else ''))
		return {'ok': not bad and not job.get('failed'), 'updated': done,
				'failed': bad + [{'why': f} for f in job.get('failed', [])],
				'gated': gated, 'gated_why': why_gated,
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

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Check for updates')
	def CheckForUpdates(self):
		"""Check the store for FunctionStore tool updates."""
		run('args[0].par.Check.pulse()', self.ownerComp, delayFrames=1)
		return {'ok': True, 'started': True}

	@FNSCommand.fns_command(label='Update tools', hidden=True)
	def UpdateTools(self):
		"""Download and install available tool updates."""
		run('args[0].par.Update.pulse()', self.ownerComp, delayFrames=1)
		return {'ok': True, 'started': True}
