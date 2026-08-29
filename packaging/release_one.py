"""Single-motion package releases: bump -> build -> stage (-> upload).

Runs INSIDE TouchDesigner. Private Investigator's lister Publish (cloud)
buttons drive this -- see scripts/pi_publish_ui.py, which stamps that UI
into PI and calls straight into ReleaseMany. Headless use is identical:

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


def _versionWritePar(comp):
    """The par a bump must WRITE, which is not the one everything READS.

    The version lives on the FNS_About child (docs/UpdaterHardening.md §4):
    a child is rebuilt by an update reload, so the version follows the
    artifact, which is what let `reloadcustom` go off fleet-wide. The tool's
    own Pkgversion mirrors it -- as an EXPRESSION on most packages, and on
    the registries as a BIND to their own Version par which is itself the
    expression.

    Reading is unaffected: `comp.par.Pkgversion.eval()` resolves through
    either. WRITING is not. Assigning `.val` to an expression par sets the
    constant underneath and leaves the expression in charge, so a bump aimed
    at the tool would appear to succeed, ship the OLD version, and every
    install would read "current" forever. Aim at the child.
    """
    fa = comp.op('FNS_About')
    if fa is not None:
        p = getattr(fa.par, 'Pkgversion', None)
        if p is not None:
            return p
    return comp.par.Pkgversion      # pre-migration component


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
        comp = by_name[n]
        p = _versionWritePar(comp)                 # write target: the child
        old_v = str(comp.par.Pkgversion.eval()).strip()   # read: through the mirror
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


# ------------------------------------------------------------- preflight
# The publish rails refuse bad releases; they cannot refuse a release you
# never thought to make. Everything below is about the OTHER failure: the
# step remembered too late -- a package edited live but never landed, a
# bootstrap built before the root it is a copy of, notes written after the
# changelog was already stamped. Preflight() answers "is anything about to
# be forgotten"; Release() refuses to ship past a blocker.
#
# Every check is mtime-and-file based on purpose: it must run before TD
# touches anything, and be as true from a terminal as from the Textport.

RAIL_SOURCES = (('packaging', 'build_installer.py'),
                ('packaging', 'InstallerExt.py'))
RAIL_ARTIFACTS = (('packaging', 'dist', 'FNSTools.tox'),
                  ('packaging', 'dist', 'FNS_Installer.tox'))
ROOT_SUSPECT = ('modules', 'suspects', 'FNSTools.tox')


def _mtime(*parts):
    path = _repo(*parts)
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


def _newestSource(name):
    """(own, vendored) newest .py mtimes under a package's source trees.

    Split because every package vendors a copy of the registry hosts it
    uses, and one propagation pass rewrites all of them at once. Counting
    those as the package's own work made a single registry edit read as
    eight packages needing a re-save, which is the kind of noise that
    teaches you to ignore the check."""
    own = vendored = 0.0
    for base in ('FNSTools', 'scripts'):
        root_dir = _repo(base, name)
        if not os.path.isdir(root_dir):
            continue
        for here, _dirs, files in os.walk(root_dir):
            rel = os.path.relpath(here, root_dir).replace('\\', '/')
            nested = any(part.startswith('FNS_') and part.endswith('Registry')
                         for part in rel.split('/'))
            for f in files:
                if not f.endswith('.py'):
                    continue
                mt = os.path.getmtime(os.path.join(here, f))
                if nested:
                    vendored = max(vendored, mt)
                else:
                    own = max(own, mt)
    return own, vendored


def _unlandedPackages(names):
    """(unlanded, rippled): packages whose sources outran their .tox.

    UNLANDED is the one that loses work. An externalized package reloads
    from its file on the next open, so a live edit that never reached the
    tox is not 'unsaved', it is gone.

    RIPPLED is softer: only the package's vendored registry copies are
    newer, which is what a propagation pass does to every package at once.
    Whether that needs a re-save depends on whether the tox embeds those
    bytes or externalizes to them, so it is raised rather than enforced."""
    unlanded, rippled = [], []
    for n in names:
        tox = _repo('modules', 'suspects', 'FNSTools', n + '.tox')
        if not os.path.exists(tox):
            continue
        tox_mt = os.path.getmtime(tox)
        own, vendored = _newestSource(n)
        if own and own > tox_mt:
            unlanded.append(n)
        elif vendored and vendored > tox_mt:
            rippled.append(n)
    return unlanded, rippled


def _staleRails():
    """Rail artifacts older than what they are built from.

    Stage() hashes the bootstrap and installer into the manifest as it
    goes, so a stale one publishes under fresh hashes -- the manifest
    promises bytes nobody built. The bootstrap is additionally a copy of
    the live root, so a root landed after the last build makes it stale
    too, even when no packaging code changed."""
    newest_src = max([_mtime(*p) for p in RAIL_SOURCES] + [_mtime(*ROOT_SUSPECT)])
    stale = []
    for parts in RAIL_ARTIFACTS:
        rel = '/'.join(parts)
        if not os.path.exists(_repo(*parts)):
            stale.append(rel + ' (never built)')
        elif _mtime(*parts) < newest_src:
            stale.append(rel)
    return stale


def _gitDirty():
    try:
        out = subprocess.run(['git', 'status', '--porcelain'],
                             cwd=project.folder, capture_output=True,
                             text=True, timeout=30).stdout
    except Exception:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def Preflight(names=None, quiet=False):
    """The checklist, run before anything ships. Nothing here mutates.

        exec(open('packaging/release_one.py').read())
        Preflight(['FNS_ConfigRegistry'])

    BLOCKERS are things that ship wrong bytes or wrong hashes. WARNINGS
    are things you can defensibly do anyway. `names=None` reports on every
    package instead of a selection, which is the 'what am I forgetting'
    view."""
    every = sorted(c.name for c in Packages())
    names = every if names is None else [
        n.name if isinstance(n, OP) else str(n) for n in names]
    unknown = [n for n in names if n not in every]
    known = [n for n in names if n in every]

    unlanded, rippled = _unlandedPackages(known)
    rails = _staleRails()
    per_tool, general = AttributedNotes()
    noted = [n for n in known if n in per_tool]
    unnoted = [n for n in known if n not in per_tool]
    published = _publishedVersions()
    dirty = _gitDirty()

    def _some(items, limit=6):
        items = sorted(items)
        if len(items) <= limit:
            return ', '.join(items)
        return ', '.join(items[:limit]) + f' (+{len(items) - limit} more)'

    blockers, warnings = [], []
    if unlanded:
        blockers.append(
            'not landed, own code newer than the .tox: ' + _some(unlanded)
            + ' -- Save these in PI, then save the project')
    if rails:
        blockers.append(
            'rails stale, Stage() would hash bytes nobody built: '
            + ', '.join(rails) + ' -- rebuild before publishing')
    if unknown:
        warnings.append('not shippable packages, will be skipped: '
                        + _some(unknown))
    if rippled:
        warnings.append(
            'vendored registry copies newer than the .tox: ' + _some(rippled)
            + ' -- a propagation pass touched these; re-save only if their '
              'host embeds those bytes')
    if unnoted and not general:
        warnings.append('no release notes for ' + str(len(unnoted))
                        + ' package(s): ' + _some(unnoted)
                        + " -- their changelog bullet and 'whatsnew' ship empty")
    if dirty:
        warnings.append(f'{len(dirty)} uncommitted file(s) in the repo -- '
                        'fine now, but step 4 is committing what this writes')

    report = {'ok': not blockers, 'packages': known, 'blockers': blockers,
              'warnings': warnings, 'unlanded': unlanded, 'rippled': rippled,
              'stale_rails': rails, 'noted': noted, 'unnoted': unnoted,
              'git_dirty': len(dirty)}
    if not quiet:
        print('\n--- preflight -------------------------------------------')
        print(f'  packages   {len(known)} selected'
              + (f', {len(unknown)} unknown' if unknown else ''))
        # Only the rows worth looking at: a clean package needs no line.
        for n in known:
            flags = []
            if n in unlanded:
                flags.append('NOT LANDED')
            if n in rippled:
                flags.append('registry ripple')
            if n not in per_tool and not general:
                flags.append('no notes')
            if not flags and len(known) > 12:
                continue
            pub = published.get(n, '(unpublished)')
            print(f'    {n:24} published {pub:10}'
                  + ('  [' + ', '.join(flags) + ']' if flags else ''))
        for b in blockers:
            print('  BLOCK      ' + b)
        for w in warnings:
            print('  warn       ' + w)
        if not blockers:
            print('  ready      nothing is being forgotten')
        print('---------------------------------------------------------\n')
    return report


def Release(names, bump='auto', label=None, upload=True, force=False):
    """Preflight, then publish, then tell you what is left to do.

    The one entry point worth remembering:

        exec(open('packaging/release_one.py').read())
        Release(['FNS_ConfigRegistry'])

    Refuses on a blocker rather than shipping something subtly wrong.
    force=True ships anyway, for when you know better than the heuristic."""
    pre = Preflight(names)
    if pre['blockers'] and not force:
        print('  refusing to publish. fix the blockers, or Release(..., '
              'force=True) if you know better.\n')
        return {'ok': False, 'why': 'preflight blocked', 'preflight': pre}

    result = ReleaseMany(names, bump=bump, label=label, upload=upload)
    result['preflight'] = pre
    if not result.get('ok'):
        print('  publish refused: ' + str(result.get('why')))
        return result

    print('\n--- published -------------------------------------------')
    print(f"  release    {result['release']}")
    for n, v in sorted(result.get('packages', {}).items()):
        print(f'    {n:24} {v}')
    if result.get('uploading'):
        print(f"  uploading  detached; watch {result.get('upload_log')}")
    print('  still to do')
    print('    1. wait for the upload to finish, then check the bucket')
    print('    2. git add the re-exported toxes, packaging/manifest.json, '
          'packaging/CHANGELOG.md')
    print('    3. commit')
    print('---------------------------------------------------------\n')
    return result
