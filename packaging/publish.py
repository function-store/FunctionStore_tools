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


def Stage(clean=True):
    """Lay out packaging/publish/ for upload. Verifies every hash."""
    with open(_repo(PKG_DIR, 'manifest.json'), 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    release = manifest.get('release', 'untagged')
    if release == 'untagged':
        return {'error': 'manifest has no release -- set one in packaging/release.json '
                         'and rebuild the manifest before publishing'}

    out = _repo(OUT_DIR)
    rel_dir = os.path.join(out, release)

    # What the last staged release published, read BEFORE the tree is wiped.
    # Versions are hand-maintained, so the one failure mode worth catching
    # mechanically is shipping a new release that bumps nothing: every
    # install would compare equal and no user would ever see it.
    previous, prev_release = {}, None
    prev_path = os.path.join(out, 'manifest.json')
    if os.path.exists(prev_path):
        try:
            with open(prev_path, 'r', encoding='utf-8') as f:
                prev = json.load(f)
            prev_release = prev.get('release')
            previous = {p['name']: p.get('version', '') for p in prev.get('packages', [])}
        except Exception as e:
            print('publish: previous manifest unreadable (%s)' % e)
    current = {p['name']: p.get('version', '') for p in manifest['packages']}
    bumped = sorted(n for n, v in current.items() if previous.get(n, v) != v)
    added = sorted(n for n in current if n not in previous)
    if previous and prev_release != release and not bumped and not added:
        return {'error': 'release %s changes no package version (previous: %s) -- '
                         'nothing would reach any install. Bump Pkgversion on what '
                         'changed, rebuild the manifest, then stage.'
                         % (release, prev_release)}

    if clean and os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(rel_dir, exist_ok=True)

    staged, missing, mismatched = [], [], []
    for pkg in manifest['packages']:
        art = pkg.get('artifact')
        if not art:
            missing.append(pkg['name'] + ' (no artifact in manifest)')
            continue
        src = _repo(art['path'])
        if not os.path.exists(src):
            missing.append(pkg['name'] + ' (artifact file absent)')
            continue
        dst = os.path.join(rel_dir, pkg['name'] + '.tox')
        shutil.copy2(src, dst)
        # Re-hash what was actually staged: publishing bytes that disagree
        # with the manifest hash breaks every installer that verifies.
        if _sha256(dst) != art.get('sha256'):
            mismatched.append(pkg['name'])
            continue
        staged.append(pkg['name'])

    # the install rails ride along: the bare installer, and the one-drop
    # bootstrap root (installer + UPDATER inside an empty toolkit
    # container) -- how a bare project starts. They are not packages (no
    # Pkgversion, never update-compared), but they ARE hashed here, per
    # release: the website's paste-script rail downloads the bootstrap and
    # must be able to verify the bytes like any other artifact.
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

    total = sum(os.path.getsize(os.path.join(rel_dir, f))
                for f in os.listdir(rel_dir))
    return {'release': release, 'out': out, 'staged': len(staged),
            'bumped': bumped, 'added': added, 'rails': sorted(rails),
            'rails_missing': [r for r in ('FNS_Installer.tox', 'FNSTools.tox')
                              if r not in rails],
            'missing': missing, 'hash_mismatch': mismatched,
            'total_mb': round(total / 1048576.0, 2),
            'ok': not missing and not mismatched,
            'upload': 'python3 packaging/upload.py'}
