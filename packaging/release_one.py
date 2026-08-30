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
import time
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


def _storeManifest():
    """The last manifest the updater FETCHED from the bucket.

    The only local file that reflects what the world actually has: the
    updater writes it into its store on every refresh. Absent on a
    machine that has never refreshed, which the caller handles.
    """
    folder = ''
    try:
        upd = op.FNS.op('FNS_Updater')
        if upd is not None:
            folder = str(upd.par.Storefolder.eval() or '')
    except Exception:
        pass
    if not folder:
        try:
            folder = '%s/FNStools_ext/store' % app.userPaletteFolder
        except Exception:
            return None
    return os.path.join(folder, 'manifest.json').replace('\\', '/')


def _versionsIn(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return {p['name']: str(p.get('version', '') or '')
                    for p in json.load(f).get('packages', [])}
    except Exception:
        return {}


def _publishedVersions():
    """name -> the HIGHEST version any source says is already published.

    Do not read the repo manifest alone. Build() regenerates it FROM the
    live Pkgversion pars, so it reports the versions we are about to
    publish -- comparing a release against itself, which made auto-bump
    fire on every package unconditionally and would have shipped a
    deliberate 3.0.0 baseline as 3.0.1.

    Three sources, highest wins:
      store cache   what the updater last fetched from the bucket -- the
                    truth, when the machine has ever refreshed
      publish/      the last tree Stage() laid out

    The repo manifest is deliberately NOT consulted, not even as a last
    resort: it describes the versions this release is about to publish,
    so including it makes every comparison self-referential again. When
    neither real source exists we do not know what is published, and an
    empty answer says so honestly.

    Highest-wins is the safe direction between the two that remain.
    Over-reporting costs a needless patch bump; UNDER-reporting
    republishes a version the field already has, which reads as current
    everywhere and updates nobody.
    """
    out = {}
    paths = [_storeManifest(),
             _repo(PKG_DIR, 'publish', 'manifest.json')]
    for path in paths:
        if not path:
            continue
        for name, ver in _versionsIn(path).items():
            if not ver:
                continue
            if name not in out or _verTuple(ver) > _verTuple(out[name]):
                out[name] = ver
    return out


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


def _shellPython():
    """A python that actually RUNS. NOT sys.executable (inside TD that is
    TouchDesigner.exe), and never trusted from which() alone: Windows
    plants App-Store stub aliases named python/python3 on PATH that print
    an install nag and exit -- measured: which() found the stub and the
    upload log held only the nag. A stub cannot print 1, so candidates
    are validated by running them. FNS_PYTHON overrides everything."""
    import shutil
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    cand, tried = [], []
    if os.environ.get('FNS_PYTHON'):
        cand.append([os.environ['FNS_PYTHON']])
    if shutil.which('py'):
        cand.append([shutil.which('py'), '-3'])
    for name in ('python3', 'python'):
        p = shutil.which(name)
        if p:
            cand.append([p])
    for c in cand:
        try:
            r = subprocess.run(c + ['-c', 'print(1)'], capture_output=True,
                               timeout=10, creationflags=flags)
            if r.returncode == 0 and r.stdout.strip() == b'1':
                return c
        except Exception:
            pass
        tried.append(' '.join(c))
    raise RuntimeError(
        'no working python for the upload subprocess (tried: %s) -- '
        'install python.org Python or set FNS_PYTHON to a real python.exe'
        % (', '.join(tried) or 'nothing on PATH'))


def StartUpload():
    """Kick the bucket sync as a detached process. Returns (proc, log).

    Everything is pinned utf-8: wrangler prints characters the Windows
    locale codec cannot represent, and an unpinned child stdout (or log
    handle) turns a healthy upload into a stream of charmap errors."""
    py = _shellPython()
    log = _repo(PKG_DIR, 'publish', '.upload.log')
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    proc = subprocess.Popen(
        py + [_repo(PKG_DIR, 'upload.py')],
        stdout=open(log, 'w', encoding='utf-8', errors='replace'),
        stderr=subprocess.STDOUT, cwd=project.folder, env=env)
    return proc, log


def StartPrune(keep, dry=False):
    """Prune the bucket to the newest `keep` releases, detached, into the
    same log StartUpload uses -- one watcher covers both. `dry` previews
    the deletions and touches nothing."""
    py = _shellPython()
    log = _repo(PKG_DIR, 'publish', '.upload.log')
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    args = py + [_repo(PKG_DIR, 'upload.py'),
                 '--prune', str(int(keep)), '--prune-only']
    if dry:
        args.append('--dry')
    proc = subprocess.Popen(
        args,
        stdout=open(log, 'w', encoding='utf-8', errors='replace'),
        stderr=subprocess.STDOUT, cwd=project.folder, env=env)
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


def ReleaseMany(names, bump='auto', label=None, upload=True, rails=False):
    names = [n.name if isinstance(n, OP) else str(n) for n in names]
    by_name = {c.name: c for c in Packages()}
    skipped = [n for n in names if n not in by_name]
    todo = [n for n in names if n in by_name]
    if rails:
        # Rails ride into every release automatically (Stage hashes the
        # dist bytes as it goes); ticking them asserts they are WORTH a
        # release on their own, so hold that claim to the same honesty
        # as a package bump.
        stale = _staleRails()
        if stale:
            return {'ok': False, 'why': 'rails are stale (%s) -- rebuild '
                    'before releasing' % ', '.join(stale), 'skipped': skipped}
        if not todo and not _railsChanged():
            return {'ok': False, 'why': 'rails are identical to the staged '
                    'release -- nothing to ship', 'skipped': skipped}
    if not todo and not rails:
        return {'ok': False, 'why': 'nothing shippable in selection',
                'skipped': skipped}

    published = _publishedVersions()
    versions = {}
    bumped_live = []          # packages whose LIVE par this call rewrote
    for n in todo:
        comp = by_name[n]
        p = _versionWritePar(comp)                 # write target: the child
        old_v = _version(comp)     # read: child-first (build_manifest's),
                                   # so a severed mirror cannot feed the bump
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
            bumped_live.append(n)
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

    # Land the bump where git can see it. The bump rewrote a LIVE par;
    # the tracked source is the suspect tox, and unsaved the repo still
    # claims the old version while the bump dies with the session --
    # observed as "where are my .tox diffs?" after a real release. Same
    # pi-save discipline as every live par write. Saved only AFTER a
    # successful stage: a refused release must not land its bump. PI
    # absent (headless) degrades to reporting via pi_unsaved, never to
    # silence.
    # ... and not only the bump: the export shipped the LIVE state, so a
    # selected package left PI-dirty (or with file-synced sources newer
    # than its tox) just shipped bytes the suspect tox -- and git -- does
    # not hold, and a suspect-bound master reloads from its tox on the
    # next open, losing those edits entirely. Anything selected that any
    # signal says is unsaved gets saved here too.
    pi_comp = op('/private_investigator1')
    pi = (pi_comp.extensions[0]
          if pi_comp is not None and pi_comp.extensions else None)
    to_save = list(bumped_live)
    try:
        unlanded_sel, _rippled = _unlandedPackages(todo)
    except Exception:
        unlanded_sel = []
    for n in todo:
        if n in to_save:
            continue
        dirty = n in unlanded_sel
        if not dirty and pi is not None:
            try:
                dirty = bool(pi.Get_Dirt(by_name[n]))
            except Exception:
                dirty = False
        if dirty:
            to_save.append(n)
    pi_saved, pi_unsaved = [], []
    if to_save:
        for n in to_save:
            try:
                if pi is None:
                    raise RuntimeError('Private Investigator not found')
                pi.Save(by_name[n])
                pi_saved.append(n)
            except Exception as e:
                pi_unsaved.append('%s (%s)' % (n, e))
    if pi_unsaved:
        print('WARNING: bumped versions NOT saved to their suspect tox: '
              + ', '.join(pi_unsaved) + ' -- Save these in PI before '
              'closing, or the repo keeps the old version')

    # After the PI saves, so the recorded counter is the resting one --
    # the CMS compares live Build against this to flag "changed since
    # it last shipped" before any bump exists.
    try:
        _recordShippedBuilds(todo, by_name, r2['release'])
    except Exception as e:
        print('WARNING: shipped-builds record not written (%s)' % e)

    result = {'ok': True, 'packages': versions, 'release': r2['release'],
              'bumped': r2['bumped'], 'skipped': skipped,
              'rails_only': bool(rails and not todo),
              'pi_saved': pi_saved, 'pi_unsaved': pi_unsaved,
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
                ('packaging', 'InstallerExt.py'),
                # embedded page + vendored browser: both ship INSIDE the
                # rails, so an edit to either makes the built bytes stale
                # (a page-only edit used to slip past this check)
                ('packaging', 'configurator', 'index.html'),
                ('packaging', 'webBrowser.tox'))
RAIL_ARTIFACTS = (('packaging', 'dist', 'FNSTools.tox'),
                  ('packaging', 'dist', 'FNS_Installer.tox'))
ROOT_SUSPECT = ('modules', 'suspects', 'FNSTools.tox')


def _mtime(*parts):
    path = _repo(*parts)
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


# What each package's PI build counter read when its artifact last shipped.
# `Pkgversion` still governs updates and this never decides one -- it exists
# so the CMS can say "the tox changed since it last shipped" BEFORE anyone
# bumps: PI's Build increments on every suspect save, so live != recorded
# means new bytes with an old version, exactly the state worth selecting.
# Tracked in git, so the record travels between machines with the repo.
SHIPPED_BUILDS = ('packaging', 'shipped_builds.json')


def ShippedBuilds():
    """{package: {'build', 'saved', 'version', 'release', 'when'}} as
    recorded at each package's last release. {} when never recorded."""
    path = _repo(*SHIPPED_BUILDS)
    try:
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _recordShippedBuilds(names, by_name, release):
    """Upsert the shipped-build record for `names`, read AFTER the
    release's own PI saves so the recorded counter is the resting one.
    Bookkeeping only: a failure here must never fail a release."""
    pi_comp = op('/private_investigator1')
    pi = (pi_comp.extensions[0]
          if pi_comp is not None and pi_comp.extensions else None)
    doc = ShippedBuilds()
    for n in names:
        comp = by_name.get(n)
        if comp is None:
            continue
        info = {}
        try:
            info = (pi.Get_Info(comp) or {}) if pi is not None else {}
        except Exception:
            info = {}
        doc[n] = {'build': info.get('Build'),
                  'saved': info.get('Savetimestamp', ''),
                  'version': _version(comp),
                  'release': release,
                  'when': time.strftime('%Y-%m-%d %H:%M:%S')}
    with open(_repo(*SHIPPED_BUILDS), 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write('\n')


def _newestSource(name):
    """(own, vendored) newest .py mtimes under a package's source trees.

    Split because every package vendors a copy of the registry hosts it
    uses, and one propagation pass rewrites all of them at once. Counting
    those as the package's own work made a single registry edit read as
    eight packages needing a re-save, which is the kind of noise that
    teaches you to ignore the check."""
    own = vendored = 0.0
    # modules/suspects/FNSTools/<name>/ holds DATs externalized beside the
    # suspect tox itself (FNS_Updater's ExtUpdater.py lives there) -- a
    # file-synced edit there reloads the LIVE comp without touching PI's
    # dirty flag or build counter, so missing this tree made exactly those
    # edits invisible to every needs-a-save check.
    for root_dir in (_repo('FNSTools', name), _repo('scripts', name),
                     _repo('modules', 'suspects', 'FNSTools', name)):
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


def _railsChanged():
    """True when the built rails differ from the last STAGED release's.

    The one case a release legitimately ships with zero package bumps:
    the bootstrap and installer reach users through /get pastes and the
    native installers, not through package updates, so new rail bytes
    ARE a shippable change even when every Pkgversion stands still."""
    import hashlib
    try:
        with open(_repo(OUT_DIR, 'manifest.json'), encoding='utf-8') as f:
            prev = json.load(f).get('rails') or {}
    except Exception:
        return True     # nothing staged yet: rails are new by definition
    for parts in RAIL_ARTIFACTS:
        path = _repo(*parts)
        if not os.path.exists(path):
            return False   # unbuilt rails are _staleRails' report, not ours
        with open(path, 'rb') as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != (prev.get(parts[-1]) or {}).get('sha256', ''):
            return True
    return False


def RailsState():
    """The install rails' one-row summary for a release surface:
    stale (sources newer than the built bytes -- rebuild first),
    changed (built bytes differ from the staged release -- shippable),
    or current (nothing to ship)."""
    stale = _staleRails()
    changed = _railsChanged()
    return {'stale': stale,
            'changed': changed,
            'state': ('stale' if stale else
                      'changed' if changed else 'current')}


def _severedVersionMirrors(names=None):
    """Packages whose comp-level Pkgversion no longer FOLLOWS FNS_About.

    Who wins on a mismatch is the whole hazard: writes aim at the child
    (see _versionWritePar), but every read -- the updater compare, the
    manifest, the CMS row -- resolves the COMP par. A mirror in constant
    mode serves its stale constant forever, so a bump appears to succeed
    while the fleet reads the old version as current. The usual cause is
    an assignment to `.val`, which silently flips the par to constant.

    A bare-Pkgversion package (no FNS_About) has nothing to sever and is
    fine. Three tests, because the sever has more than one shape
    (verified live on FNS_TimelineTools): value divergence is the
    backstop that catches every mechanism; a comp par in CONSTANT mode is
    the direct sever while values still agree; and in the BIND shape
    (Pkgversion binds the tool's own Version par, which carries the
    expression to the child) a `.val` write pushes THROUGH the bind and
    severs the MIDDLE par while the comp par's own mode innocently stays
    BIND -- so the middle hop's mode is checked too."""
    bad = []
    for c in Packages():
        if names is not None and c.name not in names:
            continue
        fa = c.op('FNS_About')
        if fa is None or not hasattr(fa.par, 'Pkgversion'):
            continue
        p = getattr(c.par, 'Pkgversion', None)
        if p is None:
            continue
        truth = str(fa.par.Pkgversion.eval()).strip()
        if truth and str(p.eval()).strip() != truth:
            bad.append(c.name)
            continue
        if p.mode == ParMode.CONSTANT:
            bad.append(c.name)
            continue
        if p.mode == ParMode.BIND:
            # follow the ACTUAL bind master (today always the package's
            # own Version par, but resolved rather than assumed)
            try:
                mid = p.bindMaster
            except Exception:
                mid = None
            if mid is not None and getattr(mid, 'mode', None) == ParMode.CONSTANT:
                bad.append(c.name)
    return bad


def _gitDirty():
    try:
        out = subprocess.run(['git', 'status', '--porcelain'],
                             cwd=project.folder, capture_output=True,
                             text=True, timeout=30).stdout
    except Exception:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def _gatedLeakRisks():
    """Gated packages whose bytes would ride a PUBLISHED parent save.

    Two TD flags do it: `enableexternaltox` OFF embeds the child outright
    ('carried by the root tox'), and `savebackup` (Save Backup of
    External) ON embeds a full backup copy on every parent save EVEN WITH
    the external binding intact -- and TD defaults it ON. Either way the
    root suspect, which the public mirror publishes, would carry paid
    bytes no path rule can withhold. Checked for EVERY gated package
    regardless of selection: the root saves regardless.
    """
    try:
        with open(_repo(PKG_DIR, 'catalog.json'), encoding='utf-8') as f:
            cat = json.load(f).get('packages', {})
    except Exception:
        return []
    gated = {n for n, m in cat.items()
             if str((m or {}).get('access', 'free') or 'free') != 'free'}
    out = []
    for c in Packages():
        if c.name not in gated:
            continue
        try:
            if not c.par.enableexternaltox.eval():
                out.append('%s (enableexternaltox off -- embedded outright '
                           'in the root tox)' % c.name)
            elif c.par.savebackup.eval():
                out.append('%s (Save Backup of External on -- a full backup '
                           'embeds on every root save)' % c.name)
        except Exception:
            pass
    return sorted(out)


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
    severed = _severedVersionMirrors(known)
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
    if severed:
        blockers.append(
            'version mirror severed (comp Pkgversion no longer follows '
            'FNS_About): ' + _some(severed) + ' -- our readers are '
            'child-first, but the severed constant still ships INSIDE the '
            'artifact, shows on the parameter page, and feeds every '
            'already-shipped comp-first reader in the field; restore the '
            'mirror expression/bind before releasing')
    leak_risks = _gatedLeakRisks()
    if leak_risks:
        blockers.append(
            'gated bytes would ride the published root tox: '
            + '; '.join(leak_risks) + ' -- fix the flag(s), PI-save the '
            'package and the root, then rebuild the manifest')
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
              'stale_rails': rails, 'severed_mirrors': severed,
              'gated_leak_risks': leak_risks,
              'noted': noted, 'unnoted': unnoted,
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


def Release(names, bump='auto', label=None, upload=True, force=False,
            rails=False):
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

    result = ReleaseMany(names, bump=bump, label=label, upload=upload,
                         rails=rails)
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
