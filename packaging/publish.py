"""Stage a release for upload to the artifact bucket.

Runs INSIDE TouchDesigner (it reads the manifest the live project built):

    exec(open('packaging/publish.py').read()); result = Stage()

Produces `packaging/publish/` — a tree that mirrors the bucket exactly, so
uploading is one sync with whatever CLI you already use:

    aws s3 sync  packaging/publish/ s3://<bucket>/fnstools/ --delete
    rclone sync  packaging/publish/ remote:fnstools/

LAYOUT

    <release>/manifest.json     immutable snapshot of this release
    <release>/<Package>.tox     immutable artifacts, hashes in the manifest
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
        return {'error': 'toolkit has no Gittag -- tag the release before publishing'}

    out = _repo(OUT_DIR)
    rel_dir = os.path.join(out, release)
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

    # the installer COMP rides along -- it is how a bare project bootstraps
    inst = _repo(DIST_DIR, 'FNS_Installer.tox')
    if os.path.exists(inst):
        shutil.copy2(inst, os.path.join(rel_dir, 'FNS_Installer.tox'))

    with open(os.path.join(rel_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1)
        f.write('\n')
    # rolling pointer: "what is current?" asked once, then pinned URLs
    shutil.copy2(os.path.join(rel_dir, 'manifest.json'),
                 os.path.join(out, 'manifest.json'))

    total = sum(os.path.getsize(os.path.join(rel_dir, f))
                for f in os.listdir(rel_dir))
    return {'release': release, 'out': out, 'staged': len(staged),
            'missing': missing, 'hash_mismatch': mismatched,
            'total_mb': round(total / 1048576.0, 2),
            'ok': not missing and not mismatched,
            'upload': 'aws s3 sync %s/ s3://<bucket>/fnstools/ --delete' % OUT_DIR}
