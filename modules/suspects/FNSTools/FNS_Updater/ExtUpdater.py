
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

import glob
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
# The endpoint that ships IN THE BINARY, derived from the first pin so the
# two can never drift. This is rung 3 of BaseUrl, and it has to be a
# constant rather than a parameter value: the shipped Baseurl par is empty,
# so a machine with no cached discovery had nowhere to look at all --
# _startJob refuses with 'no Baseurl set' BEFORE it creates a job, and the
# picker then waits on a refresh that never began. Measured 2026-09-18 on a
# clean macOS install: _job None, no store folder, the page sitting on
# 'First run: fetching the package catalog' for good. A dev machine cannot
# reproduce it -- its store already holds a discovery document.
PINNED_BASE = DISCOVERY_PINS[0].split('/.well-known/')[0]
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

# Artifacts download to a staging name and are promoted onto the store
# file only after the sha check passes. Without this, a failed fetch --
# a gate 401 body against a revoked token, a CDN error page -- lands
# DIRECTLY on the store path, and the hash-mismatch cleanup then deletes
# what used to be good bytes (seen live: a signed-out install pass
# destroyed a verified FNS_TimelineTools.tox).
PART_SUFFIX = '.part'

# The curated list of OTHER PEOPLE'S tools. Fetched and cached under a
# SUBFOLDER of the store, never beside the packages: every update mechanism
# reads the store by manifest name, so nothing in there is ever compared,
# re-hashed or updated. Linking is the default; a row carrying a pinned
# sha256 may also be placed.
COMMUNITY_NAME = 'recommendations.json'

# Packages TouchDesigner ships without a dist-info folder, or under another
# import name; a dist-info scan of its site-packages misses them. A second
# copy of any bundled package in a project's venv is a known crash class,
# so a tdp lock naming one is refused. Kept identical to
# packaging/tdp_pin.py (tests/test_community_tdp.py).
TD_BUNDLED_SEED = ('numpy', 'opencv-python', 'opencv-contrib-python',
                   'opencv-python-headless', 'opencv-contrib-python-headless',
                   'pyparsing', 'pyyaml', 'requests', 'attrs', 'pip')
TDP_INSTALL_TIMEOUT = 600      # seconds before a hung install is given up


# --- tdp helpers (pure; tests/test_community_tdp.py runs them outside TD)
def _canonPkg(name):
	import re
	return re.sub(r'[-_.]+', '-', str(name)).lower()


def _tdpRequirements(tdp):
	"""What to install: the package and whatever it imports without
	declaring (`also`), by name only. No versions: the latest resolves at
	install time (owner, 2026-09-27), and the dry run shows what that is."""
	reqs = [str(tdp.get('package', '')).strip()]
	for a in tdp.get('also') or ():
		a = str(a).strip()
		if a and a not in reqs:
			reqs.append(a)
	return [r for r in reqs if r]


def _dryRunNames(text):
	"""Package names a dry run would install: uv prints ` + name==version`,
	one per line."""
	import re
	out = []
	for line in str(text or '').splitlines():
		m = re.match(r'^\s*\+\s+([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)==', line)
		if m:
			out.append(_canonPkg(m.group(1)))
	return out


def _reportNames(report):
	"""The same from pip's `--dry-run --report` JSON."""
	out = []
	for item in (report or {}).get('install') or ():
		name = ((item or {}).get('metadata') or {}).get('name')
		if name:
			out.append(_canonPkg(name))
	return out


def _bundledNames(site_dir):
	"""Every distribution TouchDesigner ships, read from its site-packages."""
	import re
	names = {_canonPkg(n) for n in TD_BUNDLED_SEED}
	try:
		for entry in os.listdir(site_dir):
			m = re.match(r'^(.+?)-\d[^-]*\.dist-info$', entry)
			if m:
				names.add(_canonPkg(m.group(1)))
	except OSError:
		pass
	return names


def _tdpInstallCommand(reqs, venv_python, uv=None, dry_run=False, report=None):
	"""Install the requirements, wheels only, uv when there is one, else the
	venv's own pip. With `dry_run` nothing is installed: it says what would
	be (uv on its output, pip into the `report` JSON file)."""
	if uv:
		cmd = [uv, 'pip', 'install', '--python', venv_python, '--only-binary', ':all:']
		if dry_run:
			cmd.append('--dry-run')
		return cmd + list(reqs)
	cmd = [venv_python, '-m', 'pip', 'install', '--disable-pip-version-check',
		   '--no-input', '--only-binary=:all:']
	if dry_run:
		cmd += ['--dry-run', '--quiet', '--report', report]
	return cmd + list(reqs)


def _tdpChildEnv(environ):
	"""The installer's environment without what tdPyEnvManager and TD set
	for their own process: a child resolving against TD's Python by mistake
	is how an install lands in the wrong place."""
	env = {k: v for k, v in environ.items()
		   if k not in ('VIRTUAL_ENV', 'PYTHONPATH', 'PYTHONHOME', 'PYTHONUSERBASE')}
	env['PYTHONUTF8'] = '1'
	return env


def _tdpToxExpression(module, tox_key=None):
	"""What `externaltox` reads: the package's own path to its tox, so the
	binding follows the installed version on any machine (the launcher binds
	the same way)."""
	if tox_key:
		return "mod.%s._ToxFiles['%s']" % (module, tox_key)
	return 'mod.%s.ToxFile' % module
# --- end tdp helpers
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
    """The version a component declares about itself.

    FNS_About first: the child is the authoritative copy (release bumps
    write it), so reading it directly means a severed comp-level mirror
    can never invert who wins -- the comp par is display, not truth. A
    package without the child answers through its own bare Pkgversion."""
    if comp is None:
        return ''
    fa = comp.op('FNS_About')
    if fa is not None:
        p = getattr(fa.par, 'Pkgversion', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
    p = getattr(comp.par, 'Pkgversion', None)
    return str(p.eval()).strip() if p is not None else ''


def _variantOf(comp):
    """Which build of a package this component IS: FNS_About's `Pkgvariant`
    first (the master says what it is, docs/TierVariants.md), else the
    comp's own, else 'base' -- every package without variants is base."""
    if comp is None:
        return 'base'
    for host in (comp.op('FNS_About'), comp):
        if host is None:
            continue
        p = getattr(host.par, 'Pkgvariant', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip().lower()
    return 'base'


def _artifactFor(pkg, vid='base'):
    """The artifact of one build of a manifest row: the Base build is the
    row's own `artifact`, a variant's sits under `variants.<vid>`."""
    if vid and vid != 'base':
        return (((pkg or {}).get('variants') or {}).get(vid) or {}).get('artifact')
    return (pkg or {}).get('artifact')


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


# --- the toolkit's folder in the user palette ------------------------------
# <user palette>/FNSTools (docs/PaletteFolderContract.md). Until 2026-09-18
# this was FNStools_ext; a legacy folder is renamed into place the first
# time any reader looks, so store, config, tables and templates all move
# at once and nothing is re-downloaded or re-saved. Every FNS extension
# that reads the folder carries this same function: they ship as separate
# toxes and cannot share a module, and whichever reader gets there first
# must be able to migrate on its own. The launcher (TDXLU) derives the
# same folder independently and runs the same migration.
PALETTE_DIR = 'FNSTools'
LEGACY_PALETTE_DIR = 'FNStools_ext'


def _fnsPaletteRoot():
	"""'<user palette>/FNSTools', migrating a legacy FNStools_ext folder into
	place on first sight; '' when this install has no user palette folder."""
	try:
		base = str(app.userPaletteFolder).replace('\\', '/').rstrip('/')
	except Exception:
		return ''
	if not base:
		return ''
	new = '%s/%s' % (base, PALETTE_DIR)
	legacy = None
	try:
		for fn in os.listdir(base):
			if fn.lower() == LEGACY_PALETTE_DIR.lower() and os.path.isdir('%s/%s' % (base, fn)):
				legacy = '%s/%s' % (base, fn)
				break
	except Exception:
		pass
	if legacy is None:
		return new
	if not os.path.isdir(new):
		try:
			os.rename(legacy, new)
			return new
		except OSError as e:
			# a file held open, most likely; this session keeps using the
			# old folder and the next start tries again
			debug('FNS: could not rename %s to %s (%s)' % (legacy, new, e))
			return legacy
	# both exist (a race, or an older launcher recreated the legacy
	# folder): whatever the legacy folder holds that the new one lacks
	# moves over, and the legacy folder goes once it is empty
	# entry by entry, each on its own: a folder something still watches
	# (TDFam's Folder DAT on the old family tree) refuses to move, and that
	# must not keep the store or the config from moving. A folder both
	# sides hold is merged the same way one level down, because a reader
	# that seeds its file when it is missing (OpTemplates) can have made
	# the new folder before this ran. A FILE both sides hold stays as the
	# new side has it, and the legacy copy is kept aside under
	# FNSTools/legacy_<old name>/ at its old relative path, never deleted:
	# the new side's file is usually the later state, but it can be a seed
	# (OpTemplates writes its default library when its file is missing)
	# while the legacy one is the user's work. OpTemplates looks there
	# before seeding again. Deleting it lost a user's library (2026-09-18).
	left = []

	def merge(src_dir, dst_dir):
		for fn in os.listdir(src_dir):
			src, dst = '%s/%s' % (src_dir, fn), '%s/%s' % (dst_dir, fn)
			try:
				if not os.path.exists(dst):
					os.rename(src, dst)
				elif os.path.isdir(src) and os.path.isdir(dst):
					merge(src, dst)
					if not os.listdir(src):
						os.rmdir(src)
				elif os.path.isfile(src) and os.path.isfile(dst):
					rel = os.path.relpath(src, legacy).replace('\\', '/')
					keep = '%s/legacy_%s/%s' % (new, LEGACY_PALETTE_DIR, rel)
					if os.path.exists(keep):
						os.remove(src)
					else:
						os.makedirs(os.path.dirname(keep), exist_ok=True)
						os.rename(src, keep)
			except OSError as e:
				left.append('%s (%s)' % (fn, e))

	try:
		merge(legacy, new)
		if not os.listdir(legacy):
			os.rmdir(legacy)
	except Exception as e:
		left.append(str(e))
	if left:
		debug('FNS: legacy palette folder %s not fully merged: %s' % (legacy, '; '.join(left)))
	return new


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

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

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
			v = '%s/store' % _fnsPaletteRoot()
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
		3. The `Baseurl` par, then PINNED_BASE. A fresh install with no
		   network history still knows where to look -- through the
		   constant, NOT the par, which ships empty. The par stays ahead of
		   it so a mirror or a moved bucket set there still wins.

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
		return par or PINNED_BASE

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

	def _storePath(self, name, vid='base'):
		# a variant build has its own file beside the Base one: FNS_Foo.pro.tox
		stem = name if not vid or vid == 'base' else '%s.%s' % (name, vid)
		return '%s/%s.tox' % (self.StoreFolder(), stem)

	def _familyStoreStale(self, pkg):
		"""Is this family member's store copy missing, or not the manifest's
		bytes? Size first, so a current store costs one stat per member."""
		art = _artifactFor(pkg) or {}
		want = art.get('sha256', '')
		if not pkg or not want:
			return False
		path = self._storePath(str(pkg.get('name', '')))
		if not os.path.exists(path):
			return True
		try:
			if art.get('bytes') and os.path.getsize(path) != int(art['bytes']):
				return True
			return _sha256(path) != want
		except Exception:
			return True

	def _variantRank(self, man, access):
		"""Where a tier sits in the manifest's ladder (higher is more)."""
		ladder = [str(t.get('id')) for t in ((man.get('toolkit') or {}).get('tiers') or [])]
		acc = str(access or '')
		return ladder.index(acc) if acc in ladder else -1

	def BestVariant(self, name, manifest=None):
		"""The highest build of `name` this account holds: 'base', or a
		variant id whose product (FNS_Foo.pro) the account is entitled to,
		ranked by its tier's place in the ladder. Asked by the installer at
		plan time and by the fetch list, so both land the same build."""
		man = manifest or self.StoreManifest() or {}
		pkg = next((p for p in man.get('packages', []) if p.get('name') == name), None)
		vs = (pkg or {}).get('variants') or {}
		best, best_rank = 'base', -1
		for vid, v in vs.items():
			if not (v or {}).get('artifact'):
				continue
			rank = self._variantRank(man, (v or {}).get('access'))
			if rank > best_rank and self._entitled('%s.%s' % (name, vid)):
				best, best_rank = str(vid), rank
		return best

	def _allRows(self, man, scoped=False, plan_variants=None):
		"""Every fetchable build as its own row: each package's Base row,
		then one synthetic row per variant (name FNS_Foo.pro, its artifact,
		its access, `_base` the package). A SCOPED fetch (an install, an
		update) wants only the build that will land -- the planned variant,
		else the best entitled one; a full mirror takes every row and lets
		entitlement sort them downstream."""
		out = []
		for pkg in man.get('packages', []):
			vs = pkg.get('variants') or {}
			rows = [dict(pkg, _base=pkg['name'], _variant='base')]
			for vid, v in sorted(vs.items()):
				vart = (v or {}).get('artifact')
				if not vart:
					continue
				rows.append({'name': '%s.%s' % (pkg['name'], vid), 'artifact': vart,
					'access': str((v or {}).get('access', '') or '') or pkg.get('access', 'free'),
					'version': (v or {}).get('version') or pkg.get('version', ''),
					'_base': pkg['name'], '_variant': str(vid)})
			if scoped and vs:
				want = (plan_variants or {}).get(pkg['name']) or self.BestVariant(pkg['name'], man)
				rows = [r for r in rows if r['_variant'] == want]
			out.extend(rows)
		return out

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
		  component    pane-placed (placement: 'pane'): spawned into the
		               user's networks, frozen at spawn version; reported,
		               never updated in place. A spawn on the installer's
		               doorstep -- in the root, or beside it at the network
		               root -- is NOT this: it compares and updates like
		               any root child.
		  self-managed a foreign package that keeps ITSELF current
		               (manifest `updates: 'self'`, docs/ForeignPackages.md):
		               the store installed it once; its own updater owns it
		               from then on. Reported, never offered an update, never
		               touched by UpdateProject -- two updaters rewriting the
		               same externaltox would fight.
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

		# The installer's doorstep, for updates: a pane-placed package
		# spawned beside the toolkit container (network root -- the
		# no-editor fallback and a /-showing pane both land there) is in
		# reachable territory and compares/updates in place like a root
		# child. Copies anywhere else stay frozen ('component', below).
		candidates = list(root.children)
		home = root.parent()
		if home is not None:
			for c in home.children:
				if (c.family == 'COMP' and c.id != root.id
						and (index.get(c.name) or {}).get('placement')
						in ('pane', 'root')
						and root.op(c.name) is None):
					candidates.append(c)

		for child in sorted(candidates, key=lambda c: c.name.lower()):
			pkg = index.get(child.name) if child.family == 'COMP' else None
			if pkg is None:
				continue          # not something the store publishes: say nothing
			seen.add(child.name)
			have = _version(child)
			avail = str(pkg.get('version', '')).strip()
			if str(pkg.get('updates', '') or '') == 'self':
				# Its own updater owns it after install. No Pkgversion
				# is required inside the artifact, so `installed` may be
				# blank; the store's version is shown for orientation only.
				rows.append({'package': child.name, 'state': 'self-managed',
							 'installed': have, 'available': avail,
							 'note': 'keeps itself current -- check for '
									 'updates from inside the tool'})
				continue
			if not have:
				rows.append({'package': child.name, 'state': 'unversioned', 'installed': '',
							 'available': avail,
							 'note': 'component declares no version -- reinstall to adopt'})
				continue
			# Tier variants (docs/TierVariants.md): which build is installed,
			# and which one the account holds today.
			vs = pkg.get('variants') or {}
			have_vid = _variantOf(child)
			target_vid = have_vid if have_vid in vs else 'base'
			if vs:
				if target_vid != 'base' and not self._entitled('%s.%s' % (child.name, target_vid)):
					# Hold on Pro (owner, 2026-09-17): the installed build stays and
					# the updater says nothing until the account holds it again.
					rows.append({'package': child.name, 'state': 'held',
							 'installed': have, 'available': avail, 'variant': target_vid,
							 'note': 'installed %s build; your account no longer includes it '
							'-- kept as it is' % target_vid})
					continue
				best = self.BestVariant(child.name, man)
				if (self._variantRank(man, (vs.get(best) or {}).get('access'))
						> self._variantRank(man, (vs.get(target_vid) or {}).get('access'))):
					# the account grew: a swap upward at whatever version ships
					refuse = self._refuseReason(child)
					rows.append({'package': child.name, 'state': 'locked' if refuse else 'upgrade',
							 'installed': have, 'available': str((vs.get(best) or {}).get('version') or avail),
							 'variant': best,
							 'note': refuse or 'your account now holds the %s build' % best})
					if not refuse:
						updates.append(child.name)
					continue
				avail = str((vs.get(target_vid) or {}).get('version') or avail)
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
							 'installed': have, 'available': avail, 'variant': target_vid,
							 'note': refuse or man.get('release', '')})
				if not refuse:
					updates.append(child.name)
			else:
				rows.append({'package': child.name, 'state': 'current',
							 'installed': have, 'available': avail, 'variant': target_vid, 'note': ''})

		# Recorded as installed but no longer here -- the one thing the
		# audit trail still tells us that the live network cannot.
		for name, rec in sorted(self.Installed(target).items()):
			if name in seen or root.op(name) is not None:
				continue
			placement = (index.get(name) or {}).get('placement')
			if placement == 'none' and self._familyStoreStale(index.get(name)):
				# A family member's only home is the store file, which the
				# family folder mirrors: a missing or older copy is an update
				# like any other, applied by fetching and recording it
				# (docs/NewToolsAndFamilyFreshness.md, B). Before 2026-09-25
				# it read as 'component' forever and never moved.
				rows.append({'package': name, 'state': 'update',
							 'installed': rec.get('release', ''),
							 'available': str((index.get(name) or {}).get('version', '')),
							 'variant': 'base',
							 'note': 'FNS family operator: the store copy is '
									 'missing or older than this release'})
				updates.append(name)
				continue
			if placement in ('pane', 'root', 'none'):
				# Installed WITHOUT being a root child, two ways. A pane or
				# root spawn lives wherever the user put it; a 'none' package
				# is placed nowhere at all and is reached from the FNS tab and
				# the family folder on disk. Neither is missing, and neither is
				# auto-updated -- an instance is frozen at its spawn version by
				# design (palette semantics), and there is no instance to
				# update for 'none'. Leaving 'none' out of this tuple reported
				# every family member as missing (2026-09-19).
				rows.append({'package': name, 'state': 'component',
							 'installed': rec.get('release', ''),
							 'available': str((index.get(name) or {}).get('version', '')),
							 'note': ('on disk and in the FNS tab; nothing is '
									  'placed in a project')
							 if placement == 'none' else
							 ('spawned into your networks; reinstall '
							  'from the picker for the newest')})
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
		if name.endswith(PART_SUFFIX):
			# staged artifact: bookkeeping runs under the real name, the
			# bytes stay at the .part path until _verifyFetched promotes
			name = name[:-len(PART_SUFFIX)]
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
			job['inflight'][item['file']] = {'sha': item['sha'],
											 'gated': bool(item.get('gated'))}
			self._download(item['url'], item['file'] + PART_SUFFIX,
						   gated=item.get('gated'))
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

	def _verifyFetched(self, name, info, path):
		"""Bytes that do not match the manifest never enter the store.

		`path` is the .part staging file; the store file is untouched
		until the digest passes, so a failed fetch can never destroy the
		good bytes already there."""
		want = info.get('sha', '') if isinstance(info, dict) else info
		gated = bool(info.get('gated')) if isinstance(info, dict) else False
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
			# A gated fetch that mismatches is usually not corruption: a
			# revoked session serves a small JSON error body as the
			# "artifact". Say so, and drop the cached download token --
			# it outlives the session that minted it, and reusing the
			# corpse turns every retry in its 15-minute window into the
			# same silent failure (seen live after a launcher sign-out).
			refused = False
			if gated:
				try:
					with open(path, 'rb') as f:
						head = f.read(200).lstrip()
					refused = head.startswith(b'{') or os.path.getsize(path) < 2048
				except Exception:
					pass
			try:
				os.remove(path)
			except Exception:
				pass
			if refused:
				a = self._auth()
				if a is not None:
					a.DropCachedToken()
				job['failed'].append(
					'%s: the gate refused the download (session no longer '
					'valid?) -- sign in and run the update again' % name)
			else:
				job['failed'].append('%s: hash mismatch (deleted)' % name)
			return
		final = path[:-len(PART_SUFFIX)] if path.endswith(PART_SUFFIX) else path
		if final != path:
			try:
				os.replace(path, final)
			except Exception as e:
				job['failed'].append('%s: verified but could not enter the '
									 'store (%s)' % (name, e))
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
		# A stalled or aborted earlier pass can leave .part staging files
		# behind; they are dead weight and must never be mistaken for
		# store content, so each artifact pass starts clean.
		try:
			for stale in glob.glob('%s/*%s' % (self.StoreFolder(), PART_SUFFIX)):
				os.remove(stale)
		except Exception:
			pass
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
			# which BUILD each update lands (docs/TierVariants.md): the one
			# Compare chose -- the installed variant, or the upgrade
			job['plan_variants'] = {r['package']: r.get('variant', 'base')
					for r in cmp_['rows'] if r.get('package')}
		else:
			# a scoped refresh fetches just these; [] is manifest-only
			names = job.get('names')
		out = []
		for pkg in self._allRows(man, scoped=names is not None,
					plan_variants=job.get('plan_variants')):
			if names is not None and pkg['_base'] not in names:
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
			return self._placeFailed(name, 'an update job is running -- try again after it finishes')
		if getattr(self, '_place', None):
			return self._placeFailed(name, 'another community download is under way -- try again in a moment')
		row = self._communityRow(name)
		if row is None:
			return self._placeFailed(name, 'unknown community tool %r -- refresh the list first' % name)
		if not self._isPlaceable(row):
			return self._placeFailed(name, '%s is a link only; open %s to get it'
									 % (name, row.get('url', 'the author\'s page')))
		dest = self._root(target)
		if dest is None or not dest.valid:
			return self._placeFailed(name, 'no target COMP')
		os.makedirs(self._communityPath(), exist_ok=True)
		self._communityResult = {'name': name, 'state': 'fetching', 'target': dest.path}
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
			self._discard(path)
			return self._placeFailed(name, 'wrong size (%d bytes, expected %d) -- '
									 'the author may have republished it' % (size, want_size))
		if _sha256(path) != str(row['sha256']).strip().lower():
			# bytes nobody checked do not stay on disk either
			self._discard(path)
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
		self._communityResult = {'name': name, 'state': 'placed', 'placed': fresh[0].path}
		return {'ok': True, 'placed': fresh[0].path}

	def _discard(self, path):
		try:
			os.remove(path)
		except OSError:
			pass

	def _placeFailed(self, name, why):
		fnsLog('UPDATER: could not place %s -- %s' % (name, why), level='WARNING')
		self._status('%s: %s' % (name, why))
		self._communityResult = {'name': name, 'state': 'failed', 'why': why}
		return {'ok': False, 'why': why}

	# --- tdp: a community tool shipped as a Python package -----------------

	def _pyEnv(self):
		"""(env folder, its python) when the project has a linked Python
		environment (TD's TDPyEnvManager, or Embody's), else (None, None)."""
		try:
			h = app.pyEnvHelper
			env = str(h.envPath or '')
			exe = str(h.executablePath or '')
		except Exception:
			return None, None
		if env and exe and os.path.isfile(exe):
			return env.replace('\\', '/'), exe.replace('\\', '/')
		return None, None

	def PythonEnvStatus(self):
		"""Whether the project can take a tdp install: `ready` with the env, or
		where TD's environment manager stands (`none`, `creating`, `error`)."""
		env, exe = self._pyEnv()
		if env:
			return {'state': 'ready', 'env': env, 'python': exe}
		m = op('/').op('tdPyEnvManager') or op('/').op('TDPyEnvManager')
		if m is None:
			return {'state': 'none'}
		try:
			status = str(m.par.Status.eval())
		except Exception:
			status = ''
		low = status.lower()
		state = 'error' if 'error' in low else 'creating' if 'creating' in low else 'none'
		return {'state': state, 'status': status, 'manager': m.path}

	def SetUpPythonEnv(self):
		"""Give the project a Python environment with TouchDesigner's own
		TDPyEnvManager: drop it at `/` and switch it Active, which shows
		Derivative's disclaimer (their consent step, never bypassed), then
		press its Create vEnv. The same two clicks the user would make; the
		launcher does exactly this."""
		if self._pyEnv()[0]:
			return {'ok': True, 'state': 'ready'}
		root = op('/')
		m = root.op('tdPyEnvManager') or root.op('TDPyEnvManager')
		if m is None:
			tox = '%s/Palette/Tools/tdPyEnvManager.tox' % app.samplesFolder
			if not os.path.isfile(tox):
				return {'ok': False, 'why': 'tdPyEnvManager.tox is not in this TouchDesigner (%s)' % tox}
			wrapper = root.loadTox(tox)
			inner = wrapper.op(wrapper.name) if wrapper is not None else None
			if inner is not None and inner.isCOMP:
				# a palette tox is Wrapper/Wrapper: keep the inner, as a palette drag does
				wx, wy, want = wrapper.nodeX, wrapper.nodeY, wrapper.name
				wrapper.name = want + '_wrap'
				m = root.copy(inner, name=want)
				m.nodeX, m.nodeY = wx, wy
				wrapper.destroy()
			else:
				m = wrapper
		# Active shows a modal; never inside the caller's frame
		run('args[0]._activatePyEnvManager(args[1])', self, m.path,
			delayFrames=2, delayRef=op.TDResources)
		return {'ok': True, 'state': 'creating', 'manager': m.path}

	def _activatePyEnvManager(self, path):
		m = op(path)
		if m is None:
			return
		try:
			if not m.par.Active.eval():
				m.par.Active = True      # Derivative's disclaimer asks here
		except Exception as e:
			fnsLog('UPDATER: could not activate TDPyEnvManager: %s' % e, level='WARNING')
			return
		run('args[0]._pressCreateVenv(args[1], 5)', self, path,
			delayFrames=15, delayRef=op.TDResources)

	def _pressCreateVenv(self, path, tries):
		m = op(path)
		if m is None:
			return
		try:
			if not m.par.Active.eval():
				fnsLog('UPDATER: no Python environment -- the TDPyEnvManager disclaimer was declined')
				return
			if 'creating' in str(m.par.Status.eval()).lower() or self._pyEnv()[0]:
				return
			m.par.Createvenv.pulse()
		except Exception as e:
			fnsLog('UPDATER: could not start the Python environment: %s' % e, level='WARNING')
			return
		if tries > 1:
			run('args[0]._pressCreateVenv(args[1], args[2])', self, path, tries - 1,
				delayFrames=20, delayRef=op.TDResources)

	def InstallCommunityPackage(self, name, target=None):
		"""Install a tdp highlight into the project's venv and place its tox
		in `target`.

		Like PlaceCommunityTool, NOT an FNSTools install: nothing is recorded
		and no update pass touches it. The latest release installs, by name
		(owner, 2026-09-27: no pinned versions to keep up to date). A dry
		run goes first and the install is refused when it would add a
		package TouchDesigner ships itself (a second numpy or opencv is a
		known crash). Both steps run as subprocesses polled from the main
		thread, so TD keeps drawing."""
		row = self._communityRow(name)
		tdp = (row or {}).get('tdp') if isinstance((row or {}).get('tdp'), dict) else None
		if row is None:
			return self._placeFailed(name, 'unknown community tool %r -- refresh the list first' % name)
		if not tdp or not tdp.get('package') or not tdp.get('module'):
			return self._placeFailed(name, '%s is not a Python package' % name)
		if getattr(self, '_tdpJob', None):
			return self._placeFailed(name, 'another package is installing -- try again when it is done')
		env, exe = self._pyEnv()
		if not env:
			self._communityResult = {'name': name, 'state': 'noenv',
									 'why': 'this project has no Python environment yet'}
			return {'ok': False, 'why': 'no Python environment'}
		dest = self._root(target)
		if dest is None or not dest.valid:
			return self._placeFailed(name, 'no target COMP')
		os.makedirs(self._communityPath(), exist_ok=True)
		uv = shutil.which('uv') or next((p for p in (env + '/Scripts/uv.exe', env + '/bin/uv')
										 if os.path.isfile(p)), None)
		job = {'name': name, 'row': row, 'reqs': _tdpRequirements(tdp), 'uv': uv, 'exe': exe,
			   'env': env, 'target': dest.path, 'stage': 'check',
			   'log_file': self._communityPath(name + '.install.log'),
			   'report': self._communityPath(name + '.dryrun.json')}
		why = self._startTdpStage(job)
		if why:
			return self._placeFailed(name, why)
		self._communityResult = {'name': name, 'state': 'installing', 'target': dest.path}
		self._status('checking %s by %s...' % (name, row.get('author', '?')))
		return {'ok': True, 'why': 'installing %s (async)' % name}

	def _startTdpStage(self, job):
		"""Start the dry run ('check') or the install ('install'); '' or why not."""
		import subprocess
		cmd = _tdpInstallCommand(job['reqs'], job['exe'], job['uv'],
								 dry_run=job['stage'] == 'check', report=job['report'])
		try:
			log = open(job['log_file'], 'a' if job['stage'] == 'install' else 'w', encoding='utf-8')
			job['proc'] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
										   env=_tdpChildEnv(os.environ), cwd=job['env'],
										   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
		except Exception as e:
			return 'could not start the installer (%s)' % e
		job['log'] = log
		job['started'] = time.time()
		self._tdpJob = job
		run('args[0]._pollTdpInstall()', self, delayFrames=15, delayRef=op.TDResources)
		return ''

	def _pollTdpInstall(self):
		job = getattr(self, '_tdpJob', None)
		if not job:
			return
		code = job['proc'].poll()
		if code is None:
			if time.time() - job['started'] > TDP_INSTALL_TIMEOUT:
				job['proc'].kill()
			else:
				run('args[0]._pollTdpInstall()', self, delayFrames=15, delayRef=op.TDResources)
				return
		self._tdpJob = None
		try:
			job['log'].close()
		except Exception:
			pass
		name = job['name']
		try:
			text = open(job['log_file'], encoding='utf-8', errors='replace').read()
		except OSError:
			text = ''
		if code != 0:
			tail = text.strip()[-400:]
			return self._placeFailed(name, 'the %s failed%s' % (
				'check' if job['stage'] == 'check' else 'install',
				': ' + tail if tail else ' (timed out)' if code is None else ''))
		if job['stage'] == 'check':
			names = _dryRunNames(text)
			if not job['uv']:
				try:
					with open(job['report'], encoding='utf-8') as f:
						names = _reportNames(json.load(f))
				except (OSError, ValueError):
					names = []
			import sys
			clash = sorted(set(names) & _bundledNames(os.path.join(sys.base_prefix, 'Lib', 'site-packages')))
			if clash:
				return self._placeFailed(name, 'refused: it would install %s, which TouchDesigner '
										 'ships itself' % ', '.join(clash))
			job['stage'] = 'install'
			why = self._startTdpStage(job)
			if why:
				return self._placeFailed(name, why)
			self._status('installing %s by %s...' % (name, job['row'].get('author', '?')))
			return
		return self._placeTdp(name, job['row'], job['env'], job['target'])

	def _placeTdp(self, name, row, env, target):
		"""The lock is installed: make it importable in this session, find
		the tox the package names, and place it bound to that path."""
		import sys, importlib
		tdp = row['tdp']
		site = [env + '/Lib/site-packages'] + glob.glob(env + '/lib/python3*/site-packages')
		for sp in site:
			if os.path.isdir(sp) and not any(os.path.normcase(os.path.abspath(p)) ==
											 os.path.normcase(os.path.abspath(sp)) for p in sys.path):
				sys.path.insert(0, sp)
		importlib.invalidate_caches()
		module = str(tdp['module'])
		stale = module in sys.modules
		try:
			pkg = importlib.import_module(module)
			key = tdp.get('tox')
			if key:
				path = pkg._ToxFiles[key]
			else:
				path = getattr(pkg, 'ToxFile', None)
				if path is None:
					files = getattr(pkg, '_ToxFiles', {}) or {}
					key = next(iter(files)) if len(files) == 1 else None
					path = files[key] if key else None
			if path is None:
				raise LookupError('it names no tox (ToxFile / _ToxFiles)')
			path = str(path)
			if not os.path.isfile(path):
				raise LookupError('its tox is not on disk (%s)' % path)
		except Exception as e:
			return self._placeFailed(name, 'installed, but %s could not be read: %s' % (module, e))
		dest = op(target)
		if dest is None or not dest.valid:
			return self._placeFailed(name, 'installed, but the target went away')
		before = {c.id for c in dest.children}
		try:
			dest.loadTox(path)
		except Exception as e:
			return self._placeFailed(name, 'installed, but TouchDesigner refused the tox (%s)' % e)
		fresh = [c for c in dest.children if c.id not in before]
		if not fresh:
			return self._placeFailed(name, 'installed, but the tox loaded nothing -- it may need '
									 'a newer TouchDesigner build')
		comp = fresh[0]
		try:
			comp.par.externaltox.expr = _tdpToxExpression(module, key)
			comp.par.enableexternaltox = True
		except Exception as e:
			fnsLog('UPDATER: %s placed, left unbound to its package (%s)' % (name, e), level='WARNING')
		note = (' Restart TouchDesigner to use the new version: an older one was already imported.'
				if stale else '')
		fnsLog('UPDATER: installed and placed community package %s by %s at %s'
			   % (name, row.get('author', '?'), comp.path))
		self._status('placed %s by %s' % (name, row.get('author', '?')))
		self._communityResult = {'name': name, 'state': 'placed', 'placed': comp.path, 'note': note.strip()}
		return {'ok': True, 'placed': comp.path}

	def communityPlaceResult(self):
		"""The last community placement: {name, state: fetching|placed|failed,
		placed|why}, or None. The served picker polls it after asking the
		installer to place a tool, because the download is asynchronous and
		its answer arrives frames later."""
		return getattr(self, '_communityResult', None)

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
		for pkg in self._allRows(man):
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
		plan_variants = job.get('plan_variants') or {}
		for name in names:
			pkg = index.get(name)
			vid = plan_variants.get(name, 'base')
			art = _artifactFor(pkg, vid) or {}
			steps.append({'name': name, 'path': self._storePath(name, vid),
						  'sha256': art.get('sha256', ''),
						  'placement': (pkg or {}).get('placement', ''),
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
				self._announceRelease()
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

	def _announceRelease(self):
		"""Say what just landed, in the Textport, as the pass finishes.

		This used to set a flag that made the NEXT project open raise a
		`ui.messageBox` (owner, 2026-09-21: "at least not after a
		startup"). Three things were wrong with that. A modal blocks TD's
		main thread until someone clicks it, which the project's own rules
		say never to do in a load path. It arrived at a moment unrelated to
		the update, so it read as the toolkit updating itself on startup,
		which it never does -- the start hook only ever CHECKS. And the
		release-level notes are frequently empty (a release whose notes are
		all per-package lines leaves them so, as v3.2.47 did), so it often
		blocked startup to say nothing but a version number.

		The notes stay readable on the Hub's Updates tab either way; this
		is the courtesy line, at the moment it means something.
		"""
		show = getattr(self.ownerComp.par, 'Shownotes', None)
		if show is not None and not show.eval():
			return
		man = self.StoreManifest() or {}
		label = str(man.get('release', '') or '')
		notes = str(man.get('notes', '') or '').strip()
		head = 'FNSTools: updated%s' % (' to %s' % label if label else '')
		try:
			# print, not fnsLog: fnsLog is a silent no-op when the central
			# logger is absent or its Active par is off, which is most
			# installs. A pass the user asked for has to answer out loud.
			print(head + ('. ' + notes[:400] if notes else
						  ' -- per-package notes are on the Updates tab'))
		except Exception as e:
			debug('UPDATER: release notice failed: %s' % e)

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
		if step.get('placement') == 'none':
			# An FNS family member: nothing is placed, so there is nothing to
			# replace. The update IS the verified store copy; record it, and
			# the family sync at the end of the pass mirrors it into the
			# folder the FNS tab reads.
			path = step['path']
			if not os.path.exists(path):
				return {'package': name, 'ok': False, 'why': 'no artifact in the store'}
			digest = _sha256(path)
			if not step.get('sha256') or digest != step['sha256']:
				return {'package': name, 'ok': False, 'why': 'store copy fails its hash'}
			self.RecordInstalled(name, digest, step.get('release', ''), target)
			return {'package': name, 'ok': True, 'action': 'refreshed in the store'}
		root = self._root(target)
		dest = root.op(name)
		if dest is None and step.get('placement') in ('pane', 'root'):
			# the doorstep (see Compare): a pane spawn beside the toolkit
			# container updates in place like a root child
			home = root.parent()
			cand = home.op(name) if home is not None else None
			if cand is not None and cand.family == 'COMP':
				dest = cand
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
		# the comp's ACTUAL parent, so a doorstep pane spawn reloads where
		# it lives; for a root child this is the root, as before
		carrier = dest.parent()
		backup = self._backupPackage(dest, name)
		if not backup:
			# Refusing is the point: without a backup the destroy below is
			# unrecoverable. A store we cannot write to is a real signal
			# (full disk, permissions), not a reason to gamble the package.
			return {'package': name, 'ok': False,
					'why': 'could not back up the installed version -- '
						   'refusing to replace it (check the store folder is writable)'}
		dest.destroy()
		before = {c.id for c in carrier.children}
		try:
			carrier.loadTox(path)
		except Exception as e:
			restored = self._restorePackage(carrier, backup, name, nx, ny, color)
			return {'package': name, 'ok': False,
					'why': 'loadTox failed: %s%s' % (
						str(e)[:110],
						' (previous version restored)' if restored
						else ' AND THE BACKUP COULD NOT BE RESTORED: ' + backup)}
		fresh = [c for c in carrier.children if c.id not in before]
		new = fresh[0] if fresh else carrier.op(name)
		if new is None:
			restored = self._restorePackage(carrier, backup, name, nx, ny, color)
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
		# whatever the job was, what the store holds or the project has may
		# have changed: the installer's install-<Package> commands follow
		# (docs/CommandAvailability.md). A frame later, after every branch
		# below has run.
		run('args[0].valid and args[0].ext.ExtUpdater.askInstallerToRebuild()',
			self.ownerComp, delayFrames=1, delayRef=op.TDResources)

		if kind == 'refresh':
			st = self.StoreStatus()
			gated, why_gated = self._gatedWhy(job)
			if job.get('names') is None and not job.get('failed'):
				self._afterStoreComplete(st)
			elif job.get('names'):
				# a scoped fetch (a picker install) changed what the store
				# holds without completing it: the family folder follows
				self.SyncFamilyFolder()
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
		self.SyncFamilyFolder()
		self._keepStoreLater()
		return {'ok': not bad and not job.get('failed'), 'updated': done,
				'failed': bad + [{'why': f} for f in job.get('failed', [])],
				'gated': gated, 'gated_why': why_gated,
				'remaining': cmp_['updates']}

	def askInstallerToRebuild(self):
		"""Wiring: the sibling FNS_Installer re-announces its commands. Its
		install rows depend on the store, the install record and entitlement,
		all of which this updater changes. Guarded: an updater without an
		installer beside it is normal."""
		parent = self.ownerComp.parent()
		inst = parent.op('FNS_Installer') if parent is not None else None
		try:
			if inst is not None and hasattr(inst.ext, 'InstallerExt'):
				inst.ext.InstallerExt.rebuildInstallCommands()
		except Exception as e:
			fnsLog('could not refresh the install commands (%s)' % e, level='WARNING')

	# ------------------------------------------------------------------
	# a complete store (Keepstore)
	# ------------------------------------------------------------------
	# The store is machine-wide, and the picker fetches only the selection
	# it installs, so a machine that never pulsed Refresh Store holds only
	# what it installed. With Keepstore on (the default) every install and
	# every update pass finishes by mirroring the rest of the release (12 MB
	# free), so Pick Tools works offline afterwards and everything the store
	# can offer is already on disk: op alternatives today, the FNS operator
	# family when it lands (docs/OperatorFamilyFromStore.md, criterion 4).
	# A FULL mirror's completion is ONE hook, _afterStoreComplete, which is
	# where that family folder sync belongs. Nothing chains after a refresh
	# itself, so the mirror can never re-trigger. docs/StoreCompleteness.md.

	def KeepStore(self):
		"""Mirror the rest of the release into the store, when Keepstore says
		so and no job is running: what RefreshStore returns, or why not. Safe
		to call at the end of any rail; the installer does after an install."""
		if not self._parBool('Keepstore', True):
			return {'ok': False, 'why': 'Keepstore is off'}
		if self._job is not None and self._job.get('stage') not in ('done', 'failed'):
			return {'ok': False, 'why': 'a job is running (%s)' % self._job.get('kind')}
		return self.RefreshStore(names=None)

	def _keepStoreLater(self):
		# after the pass that called this has reported: the job dict is
		# still the finishing one, and _startJob refuses while it is
		if not self._parBool('Keepstore', True):
			return
		run('args[0].valid and args[0].extensionsReady and args[0].KeepStore()',
			self.ownerComp, delayFrames=5, delayRef=op.TDResources)

	def _afterStoreComplete(self, status):
		"""The one place that runs when a FULL mirror has finished (Keepstore
		or the Refresh Store pulse): the FNS operator family's folder is
		brought in step with the store, so members reach the FNS tab the
		moment the store holds them (docs/OperatorFamilyFromStore.md)."""
		debug('UPDATER: store complete for %s (%d verified)'
			% (status.get('release', '?'), status.get('verified', 0)))
		self.SyncFamilyFolder()

	# ------------------------------------------------------------------
	# the FNS operator family folder (docs/PaletteFolderContract.md,
	# docs/OperatorFamilyFromStore.md)
	# ------------------------------------------------------------------
	# TDFam lists a family's file-based operators from a folder of toxes
	# with manifest sidecars, and TouchDesigner's own Palette shows the
	# same folder: <user palette>/FNSTools/FNS. It is ONE folder because a
	# human browses it (owner, 2026-09-18): flat, one tox per member under
	# its public name (RandomCHOP.tox, not FNS_RandomCHOP_1.0.0.tox), the
	# category in the sidecar's op_group and not in a subfolder. TDFam
	# takes a loose file at the root as uncategorised and reads the group
	# and the version from the sidecar (measured 2026-09-18 on its
	# FileManager and OpFamRegistryExt), so the versioned filename its
	# default naming regex expects is not needed.
	#
	# The store is flat and holds the whole release, so this folder is a
	# DERIVED mirror of it: every member package (a manifest row with a
	# `family` block) whose tox the store holds lands here, built from the
	# row; stale files and non-members are removed, so no other store tox
	# ever appears as an operator, and the store stays untouched. The
	# store's own rules decide presence: a gated member is only there for
	# an account that holds it, so the FNS tab gates itself for free.
	#
	# Always the machine's own palette, never a relocated Storefolder:
	# TD's Palette reads app.userPaletteFolder and nothing else.
	_FAMILY_NAME = 'FNS'

	def FamilyFolder(self):
		"""Where the FNS family's operators live: <user palette>/FNSTools/FNS,
		or '' when this install has no user palette folder."""
		root = _fnsPaletteRoot()
		return '%s/%s' % (root, self._FAMILY_NAME) if root else ''

	def _familySidecar(self, pkg, fam):
		"""TDFam's per-op manifest for one member, from its manifest row:
		OpInfo plus the retain and shortcut blocks the tool declared."""
		info = {
			'op_fam': self._FAMILY_NAME,
			'op_version': str(pkg.get('version', '') or ''),
			'op_type': str(fam.get('op_type', '') or '').lower(),
			'op_name': str(fam.get('op_name', '') or fam.get('op_type', '') or ''),
			'op_label': str(fam.get('op_label', '') or pkg.get('title', '') or pkg.get('name', '')),
			'op_group': str(fam.get('op_group', '') or ''),
			'isFilter': bool(fam.get('is_filter', False)),
			'compatible_types': list(fam.get('compatible_types') or []),
			'summary': str(fam.get('summary', '') or pkg.get('description', '') or ''),
			'doc_url': str(pkg.get('help_url', '') or ''),
			'search_words': list(fam.get('search_words') or []),
		}
		return {
			'OpInfo': info,
			'ParRetain': dict(fam.get('par_retain') or {}),
			'StateRetain': dict(fam.get('state_retain') or {}),
			'Shortcuts': dict(fam.get('shortcuts') or {}),
		}

	def SyncFamilyFolder(self):
		"""Mirror every family member the store holds into the family folder
		(tox plus sidecar, public names), drop what no longer belongs, let
		TDFam re-read the folder and TD's Palette re-read its index. Cheap
		when nothing changed: bytes are compared by size and sha before a
		copy. Runs after every refresh and update pass and from the
		full-mirror hook; safe to call by hand."""
		# Nothing appears where the family is not installed (owner decision
		# 2026-09-17): no folder, no mirrored toxes. The family itself asks
		# for a sync when it initialises, so installing it fills the folder.
		if self._familyOwner() is None:
			return {'ok': True, 'skipped': 'the FNS family is not installed in this project',
					'folder': '', 'mirrored': [], 'removed': [], 'skipped_members': []}
		folder = self.FamilyFolder()
		if not folder:
			return {'ok': False, 'why': 'no user palette folder on this install'}
		man = self.StoreManifest()
		if not man:
			return {'ok': False, 'why': 'store has no manifest -- refresh first'}
		self._dropLegacyFamilyTree(folder)
		# the folder exists even with no members, so the family's Folder DAT
		# reads an empty folder instead of warning that it is not accessible
		try:
			os.makedirs(folder, exist_ok=True)
		except Exception as e:
			return {'ok': False, 'why': 'family folder not writable (%s)' % e}
		keep = set()
		mirrored, removed, skipped = [], [], []
		for pkg in man.get('packages', []):
			fam = pkg.get('family')
			if not isinstance(fam, dict) or not fam.get('op_type'):
				continue
			name = str(pkg.get('name', ''))
			src = self._storePath(name)
			if not os.path.exists(src):
				# not fetched: gated and not held, or never mirrored -- the
				# store's verdict, not the family's
				skipped.append(name)
				continue
			# the PUBLIC name: the palette reads FNS/SwitchTools
			stem = name[4:] if name.startswith('FNS_') else name
			dest = '%s/%s.tox' % (folder, stem)
			side = '%s/%s.json' % (folder, stem)
			keep.add(dest.lower())
			keep.add(side.lower())
			try:
				if (not os.path.exists(dest)
						or os.path.getsize(dest) != os.path.getsize(src)
						or _sha256(dest) != _sha256(src)):
					shutil.copyfile(src, dest)
					mirrored.append(name)
				text = json.dumps(self._familySidecar(pkg, fam), indent=4)
				cur = ''
				if os.path.exists(side):
					with open(side, 'r', encoding='utf-8') as f:
						cur = f.read()
				if cur != text:
					with open(side, 'w', encoding='utf-8') as f:
						f.write(text)
			except Exception as e:
				debug('UPDATER: family mirror of %s failed (%s)' % (name, e))
				skipped.append(name)
		# prune: former members, stale names, a category subfolder from
		# before 2026-09-18, anything else that is not a member's tox or
		# sidecar -- the folder is derived, never authored
		try:
			for fn in os.listdir(folder):
				fp = '%s/%s' % (folder, fn)
				if os.path.isdir(fp):
					shutil.rmtree(fp, ignore_errors=True)
					removed.append(fn + '/')
				elif fp.lower() not in keep and fn.lower().endswith(('.tox', '.json')):
					os.remove(fp)
					removed.append(fn)
		except Exception as e:
			debug('UPDATER: family prune failed (%s)' % e)
		self._refreshFamily(folder)
		idx = self.RebuildPaletteIndex()
		if mirrored or removed:
			fnsLog('UPDATER: family folder: %d mirrored, %d removed, %d skipped'
				   % (len(mirrored), len(removed), len(skipped)))
		return {'ok': True, 'folder': folder, 'mirrored': mirrored,
				'removed': removed, 'skipped': skipped, 'index': idx}

	def _dropLegacyFamilyTree(self, folder):
		"""The pre-2026-09-18 layout kept TDFam's copy under family/FNS/<group>/
		beside this folder, versioned. Derived, so it simply goes."""
		legacy = '%s/family' % os.path.dirname(folder)
		if os.path.isdir(legacy):
			shutil.rmtree(legacy, ignore_errors=True)

	# --- TD's Palette index -----------------------------------------------
	# Copying files into the palette is NOT enough. TD does not scan the
	# folder: it reads an INDEX, <userPalette>/paletteData.json, into the
	# Text DAT /ui/dialogs/palette/palette/cusPalette, and only at startup.
	# So the index is regenerated from a directory walk (wholesale, which is
	# how the launcher's own writer does it, so the two cannot fight and
	# nothing here needs re-asserting) and that DAT is then told to re-read.
	# Measured 2026-09-18: editing the file and pulsing `loadonstartpulse`
	# makes TD pick the change up; restoring the file and pulsing again
	# takes it away.

	# What never belongs in a palette index. Measured 2026-09-18: walking
	# everything made the file 427 KB against the 269 KB TD had written,
	# extra being .py/.pyc/.h/.lib/.pdb/.zip -- source and build artefacts
	# from repos that happen to live under the palette. They are not
	# components and they would clutter the browser as well as the file.
	# Machine directories only. 'backup', 'build' and 'dist' were in this
	# list for one draft and cost the user 50 .toe files that were simply
	# in a folder called Backup: a plausible NAME is not a machine folder.
	_PALETTE_SKIP_DIRS = ('node_modules', '__pycache__', 'site-packages')
	_PALETTE_SKIP_EXTS = ('.py', '.pyc', '.pyd', '.h', '.hpp', '.lib', '.pdb',
						  '.obj', '.dll', '.exe', '.zip', '.7z', '.tar', '.gz')

	def RebuildPaletteIndex(self):
		"""Regenerate <userPalette>/paletteData.json from a directory walk and
		ask TD to re-read it.

		Wholesale, never patched -- that is how the launcher writes it too,
		so the two cannot fight. The node shape is TD's own, read off the
		live file: {id, name, path, type} with `children` on a directory,
		`path` backslash-relative to the palette root with a leading
		backslash, ids dotted from the root's '2'. Dotfiles are skipped: a
		.git or .venv beside the components is not a component.

		The refresh is a COURTESY. TD reads this file at startup, so a
		failure to nudge it must never fail the mirror that called it.
		"""
		try:
			root = str(app.userPaletteFolder).replace('\\', '/').rstrip('/')
		except Exception:
			return {'ok': False, 'why': 'no user palette folder'}
		if not root or not os.path.isdir(root):
			return {'ok': False, 'why': 'user palette folder missing'}

		def walk(abs_dir, rel, node_id):
			kids = []
			try:
				names = sorted(os.listdir(abs_dir), key=lambda s: s.lower())
			except Exception:
				return kids
			i = 0
			for fn in names:
				if fn.startswith('.'):
					continue          # .git, .venv and friends
				if fn.lower() in self._PALETTE_SKIP_DIRS:
					continue
				if os.path.splitext(fn)[1].lower() in self._PALETTE_SKIP_EXTS:
					continue
				ap = os.path.join(abs_dir, fn)
				rp = rel + '\\' + fn
				i += 1
				kid_id = '%s.%d' % (node_id, i)
				if os.path.isdir(ap):
					kids.append({'children': walk(ap, rp, kid_id), 'id': kid_id,
								 'name': fn, 'path': rp, 'type': 'directory'})
				else:
					kids.append({'id': kid_id, 'name': fn, 'path': rp,
								 'type': 'file'})
			return kids

		doc = {'children': walk(root, '', '2'), 'id': '2',
			   'localRoot': 'app.userPaletteFolder', 'name': 'My Components',
			   'palette': 'My Components', 'path': 'app.userPaletteFolder',
			   'type': 'directory'}
		path = '%s/paletteData.json' % root
		try:
			with open(path, 'w', encoding='utf-8') as f:
				json.dump(doc, f, indent=4, sort_keys=True)
		except Exception as e:
			return {'ok': False, 'why': 'could not write the palette index (%s)' % e}
		refreshed = False
		try:
			dat = op('/ui/dialogs/palette/palette/cusPalette')
			if dat is not None and hasattr(dat.par, 'loadonstartpulse'):
				dat.par.loadonstartpulse.pulse()
				refreshed = True
		except Exception as e:
			debug('UPDATER: palette index written but TD not refreshed (%s)' % e)
		return {'ok': True, 'path': path, 'refreshed': refreshed}

	def _familyOwner(self):
		"""The registered FNS family COMP in this project, or None. By
		shortcut, never a path."""
		reg = getattr(op, 'FAMREGISTRY', None)
		if reg is None:
			return None
		try:
			return reg.GetFamilyOwner(self._FAMILY_NAME)
		except Exception:
			return None

	def _refreshFamily(self, folder):
		"""Tell TDFam to re-read the folder, when the family is in this
		project. By shortcut, never a path; a project without the family
		simply keeps the folder for the next one."""
		reg = getattr(op, 'FAMREGISTRY', None)
		if reg is None:
			return False
		try:
			owner = reg.GetFamilyOwner(self._FAMILY_NAME)
			if owner is None:
				return False
			reg.RefreshCache(self._FAMILY_NAME, owner, folder)
			return True
		except Exception as e:
			debug('UPDATER: family cache refresh failed (%s)' % e)
			return False

	# ------------------------------------------------------------------
	# parameter callbacks (extensionParExec dispatches par name -> method)
	# ------------------------------------------------------------------

	def Check(self, _=None):
		if self.ownerComp.par.Active.eval():
			self.CheckUpdates()

	def Update(self, _=None):
		if self.ownerComp.par.Active.eval():
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
