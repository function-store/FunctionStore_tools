"""Stage a release for upload to the artifact bucket.

Runs INSIDE TouchDesigner (it reads the manifest the live project built):

    exec(open('packaging/publish.py').read()); result = Stage()

Produces `packaging/publish/` — a tree that mirrors the bucket exactly, so
uploading is one sync with whatever CLI you already use:

    python3 packaging/upload.py        # R2, sets Cache-Control per file
    python3 packaging/upload.py --dry  # print the plan first

LAYOUT

    <release>/manifest.json     immutable snapshot of this release
    <release>/<Package>.tox     immutable artifacts, hashes in the manifest
    <release>/FNSTools.tox      one-drop bootstrap; hash in manifest `rails`
    <release>/FNS_Installer.tox bare installer; hash in manifest `rails`
    manifest.json               ROLLING pointer: a copy of the newest release

Releases are pinned: every artifact URL inside a manifest carries its
release, so a manifest always resolves to the exact bytes it was built
from. The rolling copy at the root exists only so a fresh install can ask
"what is current?" once; after that it follows pinned URLs. Never publish
a mutable `latest/<Package>.tox` — unreproducible installs make bug
reports uncorrelatable (ConfiguratorDistribution §3).

WHY A BUCKET AND NOT ONLY GITHUB RELEASES
    39 separate .tox assets per release is awkward as GitHub release
    assets and gives no directory semantics. The bucket holds the
    artifacts; GitHub keeps the tag and changelog. Both can coexist --
    `base_url` in the manifest decides where installers fetch from.

VERIFY BEFORE UPLOAD
    Stage() re-hashes every staged file and refuses to report success if
    any file disagrees with the manifest. Publishing bytes that do not
    match the hashes an installer will check is worse than not publishing.

    It also refuses a NEW release that bumps no package version. Versions
    are hand-maintained (`Pkgversion` on each component) because nothing
    machine-derivable was trustworthy -- a .tox re-exports to different
    bytes every time, so hashes cannot tell a change from a re-export --
    and the cost of hand-maintenance is forgetting. A release nobody's
    install would ever see is exactly what that looks like, so it is worth
    catching here rather than in a bug report.
"""

import hashlib
import json
import os
import shutil

PKG_DIR = 'packaging'
DIST_DIR = 'packaging/dist'
OUT_DIR = 'packaging/publish'


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


DISCOVERY_DIR = '.well-known'
DISCOVERY_NAME = 'fnstools.json'


def _discoveryDoc(manifest):
    """The document every install reads BEFORE the manifest.

    Small on purpose. It answers only the questions a client cannot answer
    for itself once its one hardcoded pin list is exhausted:

      endpoints.manifest  where the manifest lives NOW. Moving the bucket,
                          adding a mirror or changing host becomes a data
                          edit that reaches every install, with no
                          component update and no user action.
      minimum_updater     the kill switch. An updater below the floor
                          refuses to run and says why.
      notices             a message that reaches every install.

    It deliberately does NOT carry package data. Anything a client can get
    from the manifest belongs in the manifest, or the two drift and the
    smaller one wins by accident.
    """
    return {
        'schema': 1,
        'release': manifest.get('release', ''),
        'endpoints': {
            'manifest': str(manifest.get('base_url', '')).rstrip('/'),
        },
        'minimum_updater': str(manifest.get('minimum_updater', '') or ''),
        'notices': list(manifest.get('notices') or []),
    }


def _entitlementProblems(manifest):
    """Gated rows must be AUTHORIZABLE, or paying is pays -> token -> 403.

    `access` is a STABLE TIER ID, never a display name (Patreon names can
    be renamed at any time and are not unique) -- and nothing else ever
    cross-checked it against the Worker's TIERS map, the one place that
    actually grants packages. This closes the drift channel: a placeholder
    left in, a wrong/renamed id, or a gated package no tier and no Gumroad
    product grants, all refuse the stage by name. Skipped when
    worker/wrangler.toml is absent (offline test repos have no worker)."""
    gated = [p for p in manifest.get('packages', [])
             if str(p.get('access', 'free') or 'free') != 'free']
    if not gated:
        return []
    toml_path = _repo('worker', 'wrangler.toml')
    if not os.path.exists(toml_path):
        return []
    import re
    src = open(toml_path, encoding='utf-8').read()

    def block(name):
        m = re.search(r'^%s\s*=\s*"""(.*?)"""' % name, src, re.M | re.S)
        try:
            return json.loads(m.group(1)) if m else {}
        except Exception:
            return {}

    def is_placeholder(s):
        return 'PLACEHOLDER' in s.upper() or 'REPLACE' in s.upper()

    tiers = {k: v for k, v in block('TIERS').items() if not is_placeholder(k)}
    gumroad = {k: v for k, v in block('GUMROAD_PRODUCTS').items()
               if not is_placeholder(k)}
    problems = []
    for p in gated:
        name, acc = p['name'], str(p.get('access'))
        if is_placeholder(acc):
            problems.append('%s: access %r is a placeholder -- put the real '
                            'Patreon tier ID in catalog.json' % (name, acc))
            continue
        if acc in tiers and name not in tiers[acc]:
            problems.append("%s: access names tier %s but that tier's TIERS "
                            'list does not include it' % (name, acc))
        if not (any(name in v for v in tiers.values())
                or name in gumroad.values()):
            problems.append('%s: gated, but no filled-in TIERS entry or '
                            'GUMROAD_PRODUCTS row grants it -- a buyer gets '
                            'a token and a 403' % name)
    return problems


def Stage(clean=True):
    """Lay out packaging/publish/ for upload. Verifies every hash."""
    with open(_repo(PKG_DIR, 'manifest.json'), 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    release = manifest.get('release', 'untagged')
    if release == 'untagged':
        return {'error': 'manifest has no release -- set one in packaging/release.json '
                         'and rebuild the manifest before publishing'}

    entitlement = _entitlementProblems(manifest)
    if entitlement:
        return {'error': 'gated packages are not authorizable -- refusing to '
                         'stage: ' + '; '.join(entitlement)}

    out = _repo(OUT_DIR)
    rel_dir = os.path.join(out, release)

    # What the last staged release published, read BEFORE the tree is wiped.
    # Versions are hand-maintained, so the one failure mode worth catching
    # mechanically is shipping a new release that bumps nothing: every
    # install would compare equal and no user would ever see it.
    previous, prev_release, prev_rails = {}, None, None
    prev_path = os.path.join(out, 'manifest.json')
    if os.path.exists(prev_path):
        try:
            with open(prev_path, 'r', encoding='utf-8') as f:
                prev = json.load(f)
            prev_release = prev.get('release')
            previous = {p['name']: p.get('version', '') for p in prev.get('packages', [])}
            prev_rails = {n: (r or {}).get('sha256', '')
                          for n, r in (prev.get('rails') or {}).items()}
        except Exception as e:
            print('publish: previous manifest unreadable (%s)' % e)
    current = {p['name']: p.get('version', '') for p in manifest['packages']}
    bumped = sorted(n for n, v in current.items() if previous.get(n, v) != v)
    added = sorted(n for n in current if n not in previous)
    # New rail bytes ARE a shippable change with zero package bumps: the
    # bootstrap and installer reach users through /get pastes and the
    # native installers, which always fetch the CURRENT release's rails.
    rails_changed = prev_rails is not None and prev_rails != {
        n: (r or {}).get('sha256', '')
        for n, r in (manifest.get('rails') or {}).items()}
    if (previous and prev_release != release
            and not bumped and not added and not rails_changed):
        return {'error': 'release %s changes no package version and no rail '
                         '(previous: %s) -- nothing would reach any install. '
                         'Bump Pkgversion on what changed (or rebuild the '
                         'rails), rebuild the manifest, then stage.'
                         % (release, prev_release)}

    # A package that DISAPPEARS is the silent one, and the bump guard above
    # cannot see it: other packages moved, so the release looks healthy.
    # build_manifest.py regenerates the manifest wholesale from the live
    # project, so a package that is not loaded -- or whose pi_suspect
    # tracking lapsed -- simply is not in it, and Stage() would publish a
    # rolling manifest that no longer offers it to anyone. Every install
    # stops seeing it, with nothing to notice.
    #
    # Not hypothetical: DOTsimulate's live registry was replaced by a
    # projection missing one product's row on 2026-08-19 and every shipped
    # updater for that product broke for a week (docs/DistributionComparison.md
    # §2.4). A real retirement declares itself in release.json.
    removed = sorted(n for n in previous if n not in current)
    retired = set(manifest.get('retired') or [])
    undeclared = [n for n in removed if n not in retired]
    if undeclared:
        return {'error': 'release %s DROPS %d package(s) that %s still published: %s. '
                         'If that is accidental (a package not loaded, or its '
                         'pi_suspect tag lost) load it and rebuild the manifest. '
                         'If it is a real retirement, add the name(s) to "retired" '
                         'in packaging/release.json and rebuild.'
                         % (release, len(undeclared), prev_release or 'the previous release',
                            ', '.join(undeclared)),
                'removed': removed, 'undeclared': undeclared,
                'retired_declared': sorted(retired)}
    # Declared but not actually gone: the list is stale and would quietly
    # authorise a future accidental drop of a package that is still shipping.
    stale_retired = sorted(n for n in retired if n in current)

    if clean and os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(rel_dir, exist_ok=True)

    # Gated packages stage under plus/<release>/, NEVER under the public
    # release directory: everything in rel_dir ends up publicly readable,
    # and one copy2 into the wrong folder would publish the paid bytes on
    # the free rail while the manifest politely points buyers at the gate.
    # The layout mirrors the bucket (key = path), same as everything else.
    plus_dir = os.path.join(out, 'plus', release)
    staged, gated_staged, missing, mismatched = [], [], [], []
    for pkg in manifest['packages']:
        art = pkg.get('artifact')
        if not art:
            missing.append(pkg['name'] + ' (no artifact in manifest)')
            continue
        src = _repo(art['path'])
        if not os.path.exists(src):
            missing.append(pkg['name'] + ' (artifact file absent)')
            continue
        gated = str(pkg.get('access', 'free') or 'free') != 'free'
        if gated:
            os.makedirs(plus_dir, exist_ok=True)
        dst = os.path.join(plus_dir if gated else rel_dir,
                           pkg['name'] + '.tox')
        shutil.copy2(src, dst)
        # Re-hash what was actually staged: publishing bytes that disagree
        # with the manifest hash breaks every installer that verifies.
        if _sha256(dst) != art.get('sha256'):
            mismatched.append(pkg['name'])
            continue
        (gated_staged if gated else staged).append(pkg['name'])

    # the install rails ride along: the bare installer, and the one-drop
    # bootstrap root (installer + UPDATER inside an empty toolkit
    # container) -- how a bare project starts. They are never
    # update-compared like packages, but they ARE hashed here, per
    # release: the website's paste-script rail downloads the bootstrap and
    # must be able to verify the bytes like any other artifact. Each rail
    # also carries the installer version it was built at (sidecar written
    # by build_installer -- this script has no TD to ask), so a bad
    # installer in the field is recallable by a number a human can read,
    # not only by hash.
    try:
        with open(_repo(DIST_DIR, 'rails_versions.json'), encoding='utf-8') as f:
            rail_versions = json.load(f)
    except Exception:
        rail_versions = {}
    rails = {}
    for rail in ('FNS_Installer.tox', 'FNSTools.tox'):
        src = _repo(DIST_DIR, rail)
        if os.path.exists(src):
            dst = os.path.join(rel_dir, rail)
            shutil.copy2(src, dst)
            rails[rail] = {
                'bytes': os.path.getsize(dst),
                'sha256': _sha256(dst),
                'url': '%s/%s/%s' % (manifest.get('base_url', '').rstrip('/'),
                                     release, rail),
            }
            if rail_versions.get(rail):
                rails[rail]['version'] = str(rail_versions[rail])
    # Stamped into the STAGED manifests only (release snapshot + rolling
    # copy), not the repo's: build_manifest.py cannot know these hashes --
    # the rails are built afterwards by build_installer.py.
    manifest['rails'] = rails

    with open(os.path.join(rel_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1)
        f.write('\n')
    # rolling pointer: "what is current?" asked once, then pinned URLs
    shutil.copy2(os.path.join(rel_dir, 'manifest.json'),
                 os.path.join(out, 'manifest.json'))

    # The discovery document -- the layer ABOVE the rolling manifest, and
    # the only thing a shipped client has a hardcoded address for. Written
    # twice on purpose: the bucket copy is what pins 1 and 2 serve, and the
    # release-pinned copy is the historical record of what that release
    # announced (never fetched by anything; it costs 200 bytes).
    disco = _discoveryDoc(manifest)
    wk = os.path.join(out, DISCOVERY_DIR)
    os.makedirs(wk, exist_ok=True)
    for dest in (os.path.join(wk, DISCOVERY_NAME),
                 os.path.join(rel_dir, DISCOVERY_NAME)):
        with open(dest, 'w', encoding='utf-8') as f:
            json.dump(disco, f, indent=1)
            f.write('\n')
    # Pin 3 is a static copy in a separate repo and is the ONLY genuinely
    # independent origin, so it must never be updated by hand -- a stale
    # pin 3 serves a wrong answer forever and looks perfectly healthy.
    # Staged here so the release step can publish it; RailHardening 2.1.
    with open(os.path.join(out, 'pin3-' + DISCOVERY_NAME), 'w',
              encoding='utf-8') as f:
        json.dump(disco, f, indent=1)
        f.write('\n')

    # SIGN the two documents everything else trusts -- every staged copy
    # of each (artifact hashes verify downloads AGAINST the manifest; the
    # signature is what verifies the manifest itself). The private key
    # lives outside the repo (sign_release.py); a machine without it may
    # not stage a release, because an unsigned release teaches the fleet
    # that unsigned is normal -- exactly what the client's transition
    # policy exists to age out. FNS_ALLOW_UNSIGNED=1 is the offline-test
    # hatch, never the release path.
    try:
        import sys as _sys
        _pkg = (os.path.dirname(os.path.abspath(__file__))
                if '__file__' in globals() else _repo(PKG_DIR))
        if _pkg not in _sys.path:
            _sys.path.insert(0, _pkg)
        import sign_release
    except ImportError:
        sign_release = None          # offline test harness; the hatch decides
    to_sign = [os.path.join(rel_dir, 'manifest.json'),
               os.path.join(out, 'manifest.json'),
               os.path.join(wk, DISCOVERY_NAME),
               os.path.join(rel_dir, DISCOVERY_NAME),
               os.path.join(out, 'pin3-' + DISCOVERY_NAME)]
    signed = []
    if sign_release is None or sign_release.load_seed() is None:
        if os.environ.get('FNS_ALLOW_UNSIGNED') != '1':
            return {'error': 'no signing key%s -- run '
                             'packaging/sign_release.py --init (or set '
                             'FNS_SIGNING_KEY). Refusing to stage an '
                             'UNSIGNED release; FNS_ALLOW_UNSIGNED=1 is '
                             'the offline-test hatch only.'
                             % (' at ' + sign_release.key_path()
                                if sign_release else '')}
        print('WARNING: staging UNSIGNED (FNS_ALLOW_UNSIGNED=1) -- '
              'never upload this')
    else:
        for path in to_sign:
            signed.append(os.path.basename(sign_release.sign_file(path)))

    total = sum(os.path.getsize(os.path.join(rel_dir, f))
                for f in os.listdir(rel_dir))
    return {'release': release, 'out': out, 'staged': len(staged),
            'gated': sorted(gated_staged),
            'bumped': bumped, 'added': added,
            # Declared retirements that actually happened, and names left in
            # release.json that are still shipping -- a stale entry there
            # would silently pre-authorise a future accidental drop, so it is
            # reported rather than ignored (not fatal: re-adding a retired
            # package is legitimate).
            'removed': removed, 'stale_retired': stale_retired,
            'discovery': disco,
            'rails': sorted(rails),
            'rails_missing': [r for r in ('FNS_Installer.tox', 'FNSTools.tox')
                              if r not in rails],
            'missing': missing, 'hash_mismatch': mismatched,
            'signed': signed,
            'total_mb': round(total / 1048576.0, 2),
            'ok': not missing and not mismatched,
            'upload': 'python3 packaging/upload.py'}
