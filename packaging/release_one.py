"""Single-motion package releases: bump -> build -> stage (-> upload).

Runs INSIDE TouchDesigner, from the Textport (or any button wired to it
-- nothing drives it automatically today; Private Investigator's lister
Release button is its own component-export motion, not this):

    exec(open('packaging/release_one.py').read())
    result = ReleaseOne('AutoRes')                    # auto bump + upload
    result = ReleaseMany(['AutoRes', 'QuickPane'])    # one release, N tools
    result = ReleaseMany([...], label='v2.13.0')      # name the drop yourself
    result = ReleaseOne('AutoRes', upload=False)      # stage only

A thin conductor over the same rails everything else uses --
build_manifest.Build, publish.Stage, upload.py -- so the buttons and the
manual flow cannot drift.

BUMPING ('auto', the default): a package whose live Pkgversion still
equals the last manifest's published version gets a patch bump; one the
author already hand-set (e.g. edited in the PI lister) releases AS-IS.
Explicit bump='patch'|'minor'|'major' forces, bump=None never bumps.

THE RELEASE LABEL just names the drop (nothing semantic hangs on it).
Left alone it auto-increments release.json; pass label= to name it
deliberately (minor/major milestones, changelog-worthy drops).

Upload runs as a DETACHED subprocess (40+ wrangler calls would block the
main thread for the better part of a minute) writing to
packaging/publish/.upload.log; the caller watches it (PI arms a poll
tick). upload=False lets several releases batch before one sync.
"""

import json
import subprocess
from datetime import date

# explicit encoding: a TD session launched without a UTF-8 locale
# defaults open() to ascii, and these files contain section marks/dashes
exec(open('packaging/build_manifest.py', encoding='utf-8').read())
exec(open('packaging/publish.py', encoding='utf-8').read())


def _verTuple(v):
    try:
        return tuple(int(x) for x in str(v).lstrip('vV').split('.')[:3])
    except Exception:
        return (0, 0, 0)


def _bumpedVersion(ver, kind):
    parts = [int(x) for x in (ver or '1.0.0').lstrip('vV').split('.')]
    while len(parts) < 3:
        parts.append(0)
    if kind == 'major':
        parts = [parts[0] + 1, 0, 0]
    elif kind == 'minor':
        parts = [parts[0], parts[1] + 1, 0]
    else:
        parts = [parts[0], parts[1], parts[2] + 1]
    return '.'.join(str(x) for x in parts)


def _publishedVersions():
    """name -> version from the last built manifest (what the world has)."""
    try:
        with open(_repo(PKG_DIR, 'manifest.json'), 'r', encoding='utf-8') as f:
            return {p['name']: p.get('version', '')
                    for p in json.load(f).get('packages', [])}
    except Exception:
        return {}


def _setReleaseLabel(label=None):
    path = _repo(PKG_DIR, 'release.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if label:
        label = str(label).strip()
        data['release'] = label if label.startswith('v') else 'v' + label
    else:
        parts = data.get('release', 'v0.0.0').lstrip('vV').split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        data['release'] = 'v' + '.'.join(parts)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)
        f.write('\n')
    return data['release']


NOTES_TEMPLATE = """<!--
Release notes for the NEXT publish. Write prose about what changed and
why -- do NOT write version numbers or the release label here: the
bumped packages and their version transitions are stamped automatically
at publish time (you see the exact numbers in the confirm dialog).

This file is CLEARED after each successful publish; your text becomes
that release's entry in packaging/CHANGELOG.md and ships inside the
release's manifest. An empty file is fine -- the entry then carries just
the auto-generated package list.
-->
"""


def _writeChangelog(release, versions, per_tool, general):
    """Prepend this release's entry to packaging/CHANGELOG.md: the label
    and package list are derived; per-tool prose (the "Tool: ..." lines
    from release_notes.md) rides each tool's bullet, general prose
    follows. Written after a successful Stage (before upload -- a failed
    upload is retryable with upload.py and the entry still describes the
    staged bytes)."""
    path = _repo(PKG_DIR, 'CHANGELOG.md')
    header = '# FNS tools changelog\n\n'
    body = ''
    if os.path.exists(path):
        old = open(path, 'r', encoding='utf-8').read()
        body = old[len(header):] if old.startswith(header) else old
    pkgs = '\n'.join(
        '- %s %s%s' % (n, v, (' -- ' + per_tool[n]) if per_tool.get(n) else '')
        for n, v in sorted(versions.items()))
    entry = '## %s -- %s\n\n%s\n' % (release, date.today().isoformat(), pkgs)
    if general:
        entry += '\n%s\n' % general
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header + entry + '\n' + body)


def _clearReleaseNotes():
    with open(_repo(PKG_DIR, 'release_notes.md'), 'w', encoding='utf-8') as f:
        f.write(NOTES_TEMPLATE)


def StartUpload():
    """Kick the bucket sync as a detached process. Returns (proc, log)."""
    log = _repo(PKG_DIR, 'publish', '.upload.log')
    proc = subprocess.Popen(
        ['python3', _repo(PKG_DIR, 'upload.py')],
        stdout=open(log, 'w'), stderr=subprocess.STDOUT,
        cwd=project.folder)
    return proc, log


def ReleaseMany(names, bump='auto', label=None, upload=True):
    names = [n.name if isinstance(n, OP) else str(n) for n in names]
    by_name = {c.name: c for c in Packages()}
    skipped = [n for n in names if n not in by_name]
    todo = [n for n in names if n in by_name]
    if not todo:
        return {'ok': False, 'why': 'nothing shippable in selection',
                'skipped': skipped}

    published = _publishedVersions()
    versions = {}
    for n in todo:
        p = by_name[n].par.Pkgversion
        old_v = str(p.eval()).strip()
        pub = published.get(n, '')
        if bump == 'auto':
            if pub and _verTuple(old_v) <= _verTuple(pub):
                # equal = unchanged since publish -> patch bump. BELOW =
                # a REVERTED par (a tox reload restores old page state,
                # observed live), never an intent: publishing a version
                # the world already has reads as "current" everywhere
                # and the release updates nobody.
                new_v = _bumpedVersion(pub, 'patch')
            else:
                new_v = old_v
        elif bump:
            new_v = _bumpedVersion(old_v, bump)
            if pub and _verTuple(new_v) <= _verTuple(pub):
                new_v = _bumpedVersion(pub, 'patch')
        else:
            new_v = old_v
        if new_v != old_v:
            p.val = new_v
            p.default = new_v
        versions[n] = (f'{old_v} -> {new_v}' if new_v != old_v else new_v)

    rel = _setReleaseLabel(label)

    r1 = Build(export=todo)
    if r1.get('export_failed'):
        return {'ok': False, 'why': f"export failed: {r1['export_failed']}",
                'release': rel, 'skipped': skipped}
    r2 = Stage()
    if not r2.get('ok'):
        return {'ok': False, 'why': 'stage refused', 'stage': r2,
                'release': rel, 'skipped': skipped}

    per_tool, general = AttributedNotes()
    _writeChangelog(r2['release'], versions, per_tool, general)
    _clearReleaseNotes()

    result = {'ok': True, 'packages': versions, 'release': r2['release'],
              'bumped': r2['bumped'], 'skipped': skipped,
              'notes': bool(per_tool or general), 'uploading': False}
    if upload:
        _proc, log = StartUpload()
        result['uploading'] = True
        result['upload_log'] = log
        result['_proc'] = _proc
    return result


def ReleaseOne(name, bump='auto', label=None, upload=True):
    r = ReleaseMany([name], bump=bump, label=label, upload=upload)
    if r.get('ok'):
        n = name.name if isinstance(name, OP) else str(name)
        r['package'] = n
        r['version'] = r['packages'][n]
    return r
