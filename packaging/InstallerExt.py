"""FNS_Installer -- install a picked subset of the toolkit.

ONE implementation, two entry points:
  * as a COMP extension (drop FNS_Installer.tox into a project, set the two
    file parameters, pulse Plan then Install);
  * as a script, via packaging/install.py, for headless/Envoy use.

Consumes what the rest of the packaging track produces: `manifest.json`
(what exists) and a configurator `selection.json` (what you want). Step 3
of docs/ConfiguratorDistribution.md §4 -- the rail that needs no web
presence, because the artifacts can simply be local files.

ORDER MATTERS. Core lands first: every tool ships a stamped registry HOST
whose master lives in a core package, and a host with no master cannot
clone. The manifest's `requires` already encodes that, so the plan is a
topological walk of it rather than a hardcoded list.
"""

import hashlib
import json
import os
import shutil
import time

DEFAULT_MANIFEST = 'packaging/manifest.json'

# What each package was installed FROM. UPDATER/ExtUpdater.py reads exactly
# these four columns to decide what is stale, so the two must stay in step.
# It lives in the project because it is project state: it travels with the
# .toe, and it is what makes an interrupted pass safe to simply re-run.
INSTALLED_DAT = 'installed'
INSTALLED_COLS = ['package', 'sha256', 'release', 'when']


# --- pure helpers (no COMP required) ----------------------------------

def RepoPath(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def LoadJson(path, what):
    full = path if os.path.isabs(path) else RepoPath(path)
    if not os.path.exists(full):
        raise FileNotFoundError('%s not found: %s' % (what, full))
    with open(full, 'r', encoding='utf-8') as f:
        return json.load(f)


def _order(names, index):
    """Core-first topological order over `requires`.

    Cycles cannot arise while tools depend only on core (the rule the
    manifest generator enforces), but a cycle must never hang an
    installer, so a revisited name is emitted rather than spun on.
    """
    done, out = set(), []

    def visit(name, seen):
        if name in done or name not in index:
            return
        if name in seen:
            out.append(name)
            done.add(name)
            return
        for dep in index[name].get('requires', []):
            visit(dep, seen | {name})
        if name not in done:
            out.append(name)
            done.add(name)

    for n in names:
        visit(n, set())
    return out


ROOT_NAME = 'FNSTools'


def DefaultTarget(owner=None):
    """Where packages land.

    An installer that ships INSIDE a container (the bootstrap .tox)
    installs into that container, WHATEVER it is called -- TD numbers a
    second drop to FunctionStore_tools_20261, and matching the parent by
    its literal name sent that installer at the OTHER copy's root.
    Otherwise: the project's toolkit container if it has one, else a new
    one next to Embody (dev) or at / (a bare project).
    """
    if owner is not None:
        parent = owner.parent()
        if parent is not None and parent.path != '/':
            return parent.path
    existing = op('/' + ROOT_NAME)
    if existing is not None:
        return existing.path
    embody = getattr(op, 'Embody', None)
    home = embody.parent().path if embody is not None else '/'
    return home.rstrip('/') + '/' + ROOT_NAME


def PanePlacement(fallback_path):
    """Where a `placement: pane` package lands: the network the user is
    working in -- the current pane's owner when that pane is a network
    editor, else the first network editor's owner.

    Returns (path, note). Falls back to `fallback_path` (with the reason
    in the note) when no network editor is open, or when the visible
    network is one an install must not touch: a source checkout
    (SourceLock), or /ui and /sys, which TD rebuilds on open so anything
    landed there silently vanishes with the session.
    """
    try:
        pane = ui.panes.current
        if pane is None or pane.type != PaneType.NETWORKEDITOR:
            pane = next((p for p in ui.panes
                         if p.type == PaneType.NETWORKEDITOR), None)
        owner = pane.owner if pane is not None else None
    except Exception:
        owner = None
    if owner is None:
        return fallback_path, 'no network editor open'
    top = '/' + owner.path.lstrip('/').split('/', 1)[0] if owner.path != '/' else '/'
    if top in ('/ui', '/sys'):
        return fallback_path, ('%s is rebuilt on every project open -- '
                               'nothing lands there' % top)
    why = SourceLock(owner.path)
    if why:
        return fallback_path, 'the visible network is protected (%s)' % owner.path
    return owner.path, ''


def StoreFolder():
    """The machine-wide palette store. By contract a MIRROR of the bucket:
    nothing in it is anyone's work, so a file that disagrees with the
    manifest is stale cache, never a modification to preserve."""
    return ('%s/FNStools_ext/store' % app.userPaletteFolder).replace('\\', '/')


def DefaultManifest():
    """The manifest to read when none is given: the palette store's, if the
    store has ever been refreshed -- artifacts sit beside it, so a user
    project needs no further configuration -- else the repo's (dev)."""
    store = StoreFolder() + '/manifest.json'
    if os.path.exists(store):
        return store
    return DEFAULT_MANIFEST


def _inStore(path):
    return (os.path.normcase(os.path.dirname(os.path.abspath(path)))
            == os.path.normcase(os.path.abspath(StoreFolder())))


# --- the source-checkout lock ------------------------------------------
# The toolkit's own dev project carries an FNS_Installer too (the bootstrap
# is that root castrated), and the picker pre-checks every live child of
# its target -- so an Apply there would REMOVE authored masters. This
# mirrors the updater's _refuseReason, layer for layer: the source tree is
# detected by the packaging generator beside the .toe (no install has one)
# AND the target being the container it exports from; Embody-tracked rows
# under the target are the finer second lock. A scratch container elsewhere
# in the source project stays installable -- that is how installs are
# tested (ConfiguratorDistribution 4.1).

def _sourceHome():
    """The container the source checkout exports from, read off
    build_manifest.py's TOOLKIT constant; '' when this is not a source
    checkout."""
    gen = os.path.join(project.folder, 'packaging', 'build_manifest.py')
    if not os.path.exists(gen):
        return ''
    try:
        with open(gen, encoding='utf-8') as f:
            for line in f:
                if line.startswith('TOOLKIT'):
                    return line.split('=', 1)[1].strip().strip('\'"')
    except Exception:
        pass
    return ''


def _embodyRows(comp_path):
    """Externalization rows Embody tracks at or under this path."""
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
    except Exception:
        pass
    return hits


def SourceLock(target_path):
    """Why nothing may be installed into or removed from `target_path`,
    or '' when it is an ordinary install target."""
    home = _sourceHome()
    if home and target_path == home:
        return ('%s is the toolkit SOURCE root: its components are authored '
                'here, not installed, and the published .tox files are its '
                'output. Point Install Into at a scratch container instead.'
                % target_path)
    rows = _embodyRows(target_path)
    if rows:
        return ('Embody authors %d tracked file(s) under %s; installing or '
                'removing here would destroy work.' % (len(rows), target_path))
    return ''


def IsDevProject():
    """True when Private Investigator's DEV toggle says this is the toolkit's
    own development project. PI is the authoring apparatus (release toxes,
    the publish rails); the toggle is the owner's explicit declaration, so
    nothing here infers dev-ness from folder contents. Found by the par,
    not by a path: PI carries no shortcut and a root-level name is not a
    contract."""
    for c in op('/').children:
        if c.family != 'COMP':
            continue
        p = getattr(c.par, 'Dev', None)
        if p is not None:
            try:
                return bool(p.eval())
            except Exception:
                return False
    return False


def FolderLock(folder):
    """Why package files may not be written to `folder`, or ''.

    'project' mode copies artifacts into <project folder>/FNStools by
    default. In the toolkit's own development project that folder IS the
    externalized source tree (Embody writes every authored extension
    there -- and Windows does not distinguish FNStools from FNSTools), so
    a test install with the wrong menu value would bury generated .tox
    files among tracked sources. Gated on PI's DEV toggle; an explicit
    Package Folder OUTSIDE the project folder stays allowed."""
    if not folder or folder == 'shared':
        return ''
    if not IsDevProject():
        return ''
    root = os.path.normcase(os.path.abspath(project.folder))
    dest = os.path.normcase(os.path.abspath(folder if os.path.isabs(folder)
                                            else RepoPath(folder)))
    if dest == root or dest.startswith(root + os.sep):
        return ("Package Files 'project' would write into %s, inside the "
                "toolkit's development project (Private Investigator: DEV "
                "on) -- its source tree. Choose Embedded or Shared, or point "
                "Package Folder outside the project folder."
                % folder.replace('\\', '/'))
    return ''


def _artifactPath(art, name, manifest_path):
    """Where this artifact actually is.

    Artifacts sit NEXT TO the manifest that describes them -- that is true
    of the published bucket and of the palette store, so installing from
    either needs no extra configuration. The repo-relative `path` is the
    fallback, which is what a dev checkout (packaging/dist/) uses.
    """
    full_manifest = (manifest_path if os.path.isabs(manifest_path)
                     else RepoPath(manifest_path))
    beside = os.path.join(os.path.dirname(full_manifest), name + '.tox')
    if os.path.exists(beside):
        return beside.replace('\\', '/')
    return RepoPath(art['path']) if art.get('path') else beside.replace('\\', '/')


def ResolvePlan(selection_path, manifest_path=DEFAULT_MANIFEST, target=None,
                minimal=False, sources=None):
    """Resolve a selection into an ordered install plan. Never mutates.

    `selection_path` may be a dict, for callers that build a selection in
    memory rather than reading one off disk (the command rail).

    `minimal` installs EXACTLY what was asked plus its derived
    `requires`, skipping the core force -- for a request that arrives
    programmatically ("install autosave") rather than as a user picking a
    toolkit. See docs/LauncherToolkitBoundary.md: forcing 10 core
    packages onto someone who asked for one feature is a bait-and-switch,
    and these self-contained packages plug into none of it.

    `sources` maps package name -> a local artifact path, letting a
    caller install from bytes it already has (a launcher's bundled free
    artifact) instead of the store. Such a file is a hash_warning rather
    than `stale` when it disagrees with the manifest -- stale means "the
    store lied", which a deliberately-supplied path never is -- so it
    installs, records the sha that actually landed, and Compare() offers
    the manifest's version as an upgrade once the machine is online.
    """
    manifest = LoadJson(manifest_path, 'manifest')
    sel = (selection_path if isinstance(selection_path, dict)
           else LoadJson(selection_path, 'selection'))
    index = {p['name']: p for p in manifest['packages']}
    sources = {str(k): str(v) for k, v in (sources or {}).items()}
    # A SELECTION may ask for minimal too, not just a caller. That is what
    # lets an existing integration opt in without adopting a new code
    # path: anything that already writes a selection.json and pulses
    # Install (the launcher's fns_install verb does exactly this) gets
    # minimal behaviour by adding one key, rather than by moving to the
    # command rail.
    minimal = bool(minimal or sel.get('minimal'))

    wanted = list(sel.get('install') or (sel.get('core', []) + sel.get('tools', [])))
    unknown = [n for n in wanted if n not in index]
    # Core is not optional: a selection that omits it is a broken selection,
    # not a request to go without the infrastructure every tool plugs into.
    # UNLESS this is a minimal request, where the caller named what it
    # wants and `requires` still supplies anything those packages actually
    # depend on (_order walks it transitively).
    if not minimal:
        for c in manifest.get('core', []):
            if c not in wanted:
                wanted.append(c)

    ordered = _order([n for n in wanted if n in index], index)
    tgt = target or DefaultTarget()
    if isinstance(tgt, OP):
        tgt = tgt.path

    # Manifest TOOLS present in the target but not selected are removal
    # candidates -- the picker edits the project's state, not just adds to
    # it. Core is never a candidate (wanted always includes it), and
    # comps the manifest does not know (installer, webBrowser, DATs, the
    # user's own work) are never touched.
    # A minimal request is ADDITIVE and must never remove: `wanted` is one
    # package, so the ordinary "not selected means remove it" rule would
    # treat the user's whole toolkit as removal candidates. This is the
    # sharpest hazard in the minimal path -- a launcher asking for
    # autosave could otherwise uninstall everything else.
    tool_names = {p['name'] for p in manifest['packages'] if p['kind'] == 'tool'}
    root_comp = op(tgt)
    to_remove = [] if minimal else (
        sorted(c.name for c in root_comp.children
               if c.family == 'COMP' and c.name in tool_names
               and c.name not in wanted) if root_comp else [])

    # `placement: pane` packages land in the user's working network and
    # `placement: root` ones beside the toolkit container -- neither is a
    # target-root child, so "already installed" is the install RECORD (or
    # the doorstep comp), and unselecting one goes through RemoveTools'
    # doorstep branch: a copy beside the root is removed for real, copies
    # deeper in the user's networks are only forgotten. The ONE exception:
    # a spawn that fell back into the target root itself is already in
    # to_remove above and must not also appear here.
    spawn_names = {p['name'] for p in manifest['packages']
                   if p.get('placement') in ('pane', 'root')}
    recorded = set()
    rec_t = root_comp.op(INSTALLED_DAT) if root_comp else None
    if rec_t is not None:
        recorded = {rec_t[i, 0].val for i in range(1, rec_t.numRows)
                    if rec_t[i, 0].val}
    to_unrecord = sorted((recorded & spawn_names & tool_names)
                         - set(wanted) - set(to_remove))

    steps, missing, hash_warnings = [], [], []
    for name in ordered:
        pkg = index[name]
        art = pkg.get('artifact')
        if not art:
            missing.append(name)
            continue
        supplied = sources.get(name, '')
        path = supplied or _artifactPath(art, name, manifest_path)
        # an absent file is a DOWNLOAD, not a failure: the picker fetches
        # exactly the selection at install time, so planning must work
        # against a store that holds only the manifest
        have = os.path.exists(path)
        # a present store file is only trustworthy if its bytes are the
        # manifest's bytes -- the store is a mirror, and a mirror can lag.
        # Elsewhere (dev dist/, a hand-pointed manifest) a mismatch can be
        # deliberately staged local work, so it is reported, never refetched.
        stale = False
        if have and art.get('sha256'):
            try:
                matches = _fileSha(path) == art['sha256']
            except Exception:
                matches = True     # unreadable surfaces at loadTox instead
            if not matches:
                # `stale` means the STORE lied -- a mirror that lagged the
                # manifest. A path a caller deliberately supplied never
                # lies; it is simply older, so it warns and installs.
                if _inStore(path) and not supplied:
                    stale = True
                else:
                    hash_warnings.append(name)
        placement = pkg.get('placement', 'toolkit') or 'toolkit'
        # pane packages live wherever the user spawned them, so presence
        # is the install record; root ones live at a KNOWN address (beside
        # the toolkit container), so presence is the comp itself
        if placement == 'pane':
            present = name in recorded
        elif placement == 'root':
            home_path = tgt.rsplit('/', 1)[0] or '/'
            present = op(home_path + '/' + name) is not None
        else:
            present = op(tgt + '/' + name) is not None
        steps.append({'name': name, 'kind': pkg['kind'], 'path': path,
                      'sha256': art.get('sha256', ''),
                      'bytes': art.get('bytes', 0),
                      'release': manifest.get('release', ''),
                      'have': have, 'stale': stale,
                      'placement': placement,
                      'present': present})
    return {'target': tgt, 'steps': steps, 'order': [s['name'] for s in steps],
            # non-empty = every executor refuses; the reason is shown as-is
            'locked': SourceLock(tgt),
            'already_present': [s['name'] for s in steps if s['present']],
            # stale store copies re-download even when the package is
            # already present: Replace installs from the file, and healing
            # the mirror is never wrong
            'to_fetch': [s['name'] for s in steps
                         if s['stale'] or (not s['have'] and not s['present'])],
            'stale_store': [s['name'] for s in steps if s['stale']],
            'hash_warnings': hash_warnings,
            'to_remove': to_remove,
            'to_unrecord': to_unrecord,
            'minimal': bool(minimal),
            'missing_artifact': missing, 'unknown_packages': unknown}


def _verify(comp):
    """Installed means the COMP exists, its extensions are up and it
    reports no errors -- not merely that loadTox returned.

    An error is given ONE forced recook before it counts: expressions
    that reference the package's own extension (`ext.X...`) evaluate
    during loadTox BEFORE the extension exists, and the resulting error
    sticks on nodes that nothing recooks (seen on FNS_HotkeyManager's
    parexec). Recooking with the extension up separates that init-order
    noise from real breakage."""
    if comp is None or not comp.valid:
        return {'ok': False, 'why': 'comp missing after load'}
    errs = comp.errors(recurse=True)
    if errs:
        try:
            comp.cook(force=True, recurse=True)
        except Exception:
            pass
        errs = comp.errors(recurse=True)
    return {'ok': not errs, 'why': (errs.splitlines()[0][:120] if errs else ''),
            'ops': len(comp.findChildren()),
            'extensions_ready': bool(comp.extensionsReady)}


def _bindPackage(comp, step, bind):
    """Point an installed package at a .tox on disk, per `bind`:

        None        embedded -- the package lives inside the .toe. One file
                    to move and nothing to lose track of.
        'shared'    bind to the artifact where it already sits (the palette
                    store). One copy per machine: refreshing the store
                    updates every project that shares it.
        <folder>    copy the artifact into <folder> and bind there. Each
                    project owns its files, so a project can hold a
                    modified package without touching any other.

    Binding is what gives the updater its clean path: updating a bound
    package is a file write plus a reload, not COMP surgery.
    """
    if not bind:
        return ''
    src = step['path']
    if bind == 'shared':
        dest = src
    else:
        folder = bind if os.path.isabs(bind) else RepoPath(bind)
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, step['name'] + '.tox').replace('\\', '/')
        if os.path.normcase(os.path.abspath(dest)) != \
                os.path.normcase(os.path.abspath(src)):
            shutil.copyfile(src, dest)
    comp.par.externaltox = dest
    comp.par.enableexternaltox = True
    # Save Backup of External ON: the user's .toe embeds a backup, so a
    # bound package still loads when its file has vanished (a deleted
    # store, a moved project folder). The OPPOSITE of the dev-side rule --
    # there the flag would smuggle gated bytes into the published root
    # suspect; here the user owns both files and the backup is the
    # self-healing.
    p = getattr(comp.par, 'savebackup', None)
    if p is not None:
        p.val = True
    return dest


def _fileSha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def RemoveTools(plan):
    """Remove the plan's `to_remove` tools from the project.

    Scope rules, deliberately asymmetric:
      * PROJECT state goes: the COMP, its `installed` row, and a
        project-mode package file -- the file only when its bytes still
        match the published artifact (a modified copy is the user's work
        and stays, with a note).
      * MACHINE state stays: the store cache is other projects' business
        and a reinstall's shortcut; the tool's section in the palette
        config survives so preferences roam across remove/reinstall and
        across the user's other projects.
    """
    if plan.get('locked'):
        return {'removed': [], 'notes': ['REFUSED: ' + plan['locked']]}
    parent_comp = op(plan['target'])
    if parent_comp is None:
        return {'removed': [], 'notes': []}
    by_name = {s['name']: s for s in plan['steps']}
    removed, notes = [], []

    def destroy_and_clean(comp):
        """Destroy an installed COMP; a project-mode package file goes
        with it, but only while its bytes still match the published
        artifact -- a modified copy is the user's work and stays."""
        name = comp.name
        bound = ''
        p = getattr(comp.par, 'externaltox', None)
        if p is not None and comp.par.enableexternaltox.eval():
            bound = str(p.eval()).replace('\\', '/')
        comp.destroy()
        if bound:
            full = bound if os.path.isabs(bound) else RepoPath(bound)
            store_dir = os.path.dirname(by_name.get(name, {}).get('path', ''))
            in_store = store_dir and os.path.normcase(
                os.path.dirname(full)) == os.path.normcase(store_dir)
            if in_store:
                pass          # shared binding: the store file is machine-wide
            elif os.path.exists(full):
                want = by_name.get(name, {}).get('sha256', '')
                try:
                    pristine = bool(want) and _fileSha(full) == want
                except Exception:
                    pristine = False
                if pristine:
                    os.remove(full)
                else:
                    notes.append('%s: kept %s (modified)' % (name, full))

    def drop_record(name):
        t = parent_comp.op(INSTALLED_DAT)
        if t is not None:
            for i in range(t.numRows - 1, 0, -1):
                if t[i, 0].val == name:
                    t.deleteRow(i)

    for name in plan.get('to_remove', []):
        comp = parent_comp.op(name)
        if comp is None:
            continue
        destroy_and_clean(comp)
        drop_record(name)
        removed.append(name)
    # `placement: pane` packages: the spawned copies live in the user's
    # networks and are the user's work -- unselecting one clears only the
    # install record, so the picker stops reporting it as installed.
    # EXCEPT on the installer's own doorstep: a spawn sitting right beside
    # the toolkit container (a sibling at the network root, where the
    # no-editor fallback and a `/`-showing pane both land) is removed for
    # real, exactly like a root child.
    home = parent_comp.parent()
    for name in plan.get('to_unrecord', []):
        beside = home.op(name) if home is not None else None
        if beside is not None and beside.family == 'COMP':
            destroy_and_clean(beside)
            notes.append('%s: removed from %s' % (name, home.path))
        else:
            notes.append('%s: forgotten; the copies in your networks '
                         'stay yours' % name)
        drop_record(name)
        removed.append(name)
    return {'removed': removed, 'notes': notes}


def ExposeConsoleHosts(comp):
    """Flip Expose on for every FNS_Console host the landed package carries.

    Artifacts ship with console exposure OFF (packaging/pre_release_common.py
    explains why: a host whose exposure removes a local surface must not
    bootstrap itself in a bare project). Inside the toolkit, contributors
    expose by default -- and this is the ONE place that decides it: the
    install rail, as the package lands. The flag is the tool's own Registry
    page par, which the config registry persists, so a user who later turns
    it off keeps that choice across updates (an update pass never calls
    this; only a fresh install or an explicit Replace does).

    Returns the tool paths it exposed.
    """
    exposed = []
    if comp is None or not getattr(comp, 'valid', False):
        return exposed
    for tool in [comp] + comp.findChildren(type=COMP):
        host = tool.op('FNS_Console') if tool.name != 'FNS_Console' else None
        if host is None:
            continue
        # the tool-page par is the bind MASTER; the host's own par binds to
        # it once the registry's tool page exists, so write the master first
        # and the host only where no master is there yet
        p = getattr(tool.par, 'Csautoregister', None)
        if p is None:
            p = getattr(host.par, 'Autoregister', None)
        if p is None:
            continue
        try:
            if not p.eval():
                p.val = True
            exposed.append(tool.path)
        except Exception as e:
            debug('FNS_Installer: expose %s: %s' % (tool.path, e))
    return exposed


def RecordInstalled(parent_comp, name, sha256, release=''):
    """Upsert the install record. Written per package as it lands, so an
    interrupted install still leaves a truthful record of what is in the
    project -- which is the whole basis of the update comparison."""
    t = parent_comp.op(INSTALLED_DAT)
    if t is None:
        t = parent_comp.create(tableDAT, INSTALLED_DAT)
        t.nodeX, t.nodeY = -800, -400
        t.color = (0.35, 0.45, 0.55)
    # a fresh tableDAT already holds one empty row, so "no rows" is the
    # wrong test for "needs a header"
    if t.numRows == 0 or t[0, 0].val != INSTALLED_COLS[0]:
        t.clear()
        t.appendRow(INSTALLED_COLS)
    row = [name, sha256, release, time.strftime('%Y-%m-%d %H:%M:%S')]
    for i in range(1, t.numRows):
        if t[i, 0].val == name:
            for c, v in enumerate(row):
                t[i, c] = v
            return
    t.appendRow(row)


# Where a registry master promotes its global copy. One container instead of
# seven loose children of TD's own /sys, so anything that needs to know what
# is live -- this installer, the updater, a support dump -- reads one place.
SYS_REGISTRY_HOME = '/sys/FNS_Registries'


# The roaming config the toolkit root's own host (canonical `FNS`) writes
# into on every SaveAll -- its `last_install` state entry is what lets a
# fresh bootstrap offer "Set up like last time". Read here DIRECTLY, because
# a bare root has no registry yet to ask; the path is the registry's own
# default (ConfigRegistryExt.SUBFOLDER / FILE_NAME). A master's Configfile
# override cannot be known on a bare root and is not honoured here.
CONFIG_SUBPATH = 'FNStools_ext/config/FNStools_config.json'
ROOT_CANONICAL = 'FNS'


def LastInstall(root=None, path=None):
    """The machine's last recorded install -- {'packages', 'project', 'when',
    'bind'?} -- or None. None under project scope (the roaming file is never
    read there; the authored scope record is the root's Configscope, and a
    missing par reads as global), when there is no file, or when the file
    is unreadable or of another schema. Never raises."""
    scope = getattr(root.par, 'Configscope', None) if root is not None else None
    if scope is not None:
        try:
            if str(scope.eval()) == 'project':
                return None
        except Exception:
            pass
    path = path or (app.userPaletteFolder + '/' + CONFIG_SUBPATH)
    try:
        with open(path.replace('\\', '/'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get('schema') != 1:
            return None
        rec = data.get('tools', {}).get(ROOT_CANONICAL, {}).get('state', {}).get('last_install')
        if not isinstance(rec, dict) or not rec.get('packages'):
            return None
        return rec
    except Exception:
        return None


def PromotedRegistries():
    """The global registries live in this TD process, newest state first-hand.

    /sys is never saved with the .toe: every master re-promotes on open, so
    this is a snapshot of the running process, not of the project file. A
    freshly installed master replaces a lower-versioned global by itself
    (RegistryBase compares versions on init) -- this is how the installer
    REPORTS what happened, not how it makes it happen.
    """
    home = op(SYS_REGISTRY_HOME)
    if home is None:
        return []
    out = []
    for comp in home.children:
        version = ''
        for parname in ('Pkgversion', 'Version'):
            par = getattr(comp.par, parname, None)
            if par is not None:
                version = str(par.eval())
                break
        shortcut = getattr(comp.par, 'opshortcut', None)
        out.append({'name': comp.name,
                    'path': comp.path,
                    'version': version,
                    'shortcut': str(shortcut.eval()) if shortcut is not None else ''})
    return sorted(out, key=lambda r: r['name'])


def InstallPlan(plan, replace=False, only=None, bind=None):
    """Execute a plan from ResolvePlan. `only` limits to named packages,
    which is how a large install is batched under the MCP timeout. `bind`
    decides where the package files live -- see _bindPackage."""
    tgt = plan['target']
    if plan.get('locked'):
        return {'target': tgt, 'installed': [], 'failed': [], 'results': [],
                'locked': plan['locked'], 'registries': PromotedRegistries()}
    parent_comp = op(tgt)
    if parent_comp is None:
        home = op(tgt.rsplit('/', 1)[0] or '/')
        parent_comp = home.create(baseCOMP, tgt.rsplit('/', 1)[1])

    # Resolved ONCE per pass, not per step: every pane-placed package in
    # one install lands in the same network the user is looking at.
    pane_path, pane_note = '', ''
    if any(s.get('placement') == 'pane' for s in plan['steps']):
        pane_path, pane_note = PanePlacement(tgt)

    results = []
    for step in plan['steps']:
        name = step['name']
        if only and name not in only:
            continue
        pane = step.get('placement') == 'pane'
        rooted = step.get('placement') == 'root'
        if pane:
            # presence is the install record (ResolvePlan); the spawned
            # copy lives wherever the user put it, so there is nothing
            # to verify or destroy here
            if step.get('present') and not replace:
                results.append({'name': name, 'ok': True,
                                'action': 'skipped (already spawned)'})
                continue
            dest = op(pane_path) or parent_comp
        elif rooted:
            # the doorstep: beside the toolkit container, a known address
            # the installer owns -- present/replace work like a root child
            home = parent_comp.parent()
            dest = home if home is not None else parent_comp
        else:
            dest = parent_comp
        existing = None if pane else dest.op(name)
        if existing is not None and not replace:
            state = _verify(existing)
            # a skipped package is NOT a failure of this install -- its
            # pre-existing errors are reported, not counted (oscMapper's
            # busy OSC port kept reading as "failed 1" on every re-run)
            state['ok'] = True
            results.append({'name': name, 'action': 'skipped (present)',
                            **state})
            continue
        if not os.path.exists(step['path']):
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': 'artifact not downloaded (%s)' % step['path']})
            continue
        if step.get('stale'):
            # never load bytes the plan already knows are not the
            # manifest's; the picker flow re-downloads these before it
            # ever gets here, so this only fires on a manual Install
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': 'stale store copy (sha mismatch) -- '
                                   'Refresh Store in FNS_Updater, then re-Plan'})
            continue
        if existing is not None:
            existing.destroy()
        # loadTox loads the component INTO the given COMP -- it creates the
        # child itself. Pre-creating a container named after the package
        # nests it a level too deep (AutoRes/AutoRes), so load onto the
        # target and identify the new child by diffing.
        before = {c.id for c in dest.children}
        try:
            dest.loadTox(step['path'])
        except Exception as e:
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': str(e)[:140]})
            continue
        fresh = [c for c in dest.children if c.id not in before]
        comp = fresh[0] if fresh else dest.op(name)
        if comp is not None and comp.name != name:
            # TD numbers on collision; the manifest name wins -- except in
            # a pane spawn, where a same-named op is the USER'S and keeps
            # its name (the spawn stays numbered)
            if not (pane and dest.op(name) is not None):
                comp.name = name
        if (pane or rooted) and comp is not None:
            # a spawn must not land on top of the user's work: put it just
            # right of everything in the network, and hand it the selection
            try:
                sibs = [c for c in dest.children if c.id != comp.id]
                if sibs:
                    comp.nodeX = max(s.nodeX + s.nodeWidth for s in sibs) + 200
                    comp.nodeY = max(s.nodeY for s in sibs)
                comp.selected = True
                comp.current = True
            except Exception:
                pass
        bound = ''
        if comp is not None:
            try:
                bound = _bindPackage(comp, step, bind)
            except Exception as e:
                results.append({'name': name, 'action': 'installed', 'ok': False,
                                'why': 'bind failed: %s' % str(e)[:120]})
                continue
        # record the hash of the bytes that actually landed, not the
        # manifest's promise -- on a hash_warnings install they differ,
        # and the updater's comparison must start from the truth
        try:
            landed = _fileSha(step['path'])
        except Exception:
            landed = step.get('sha256', '')
        # ALWAYS on the plan target, even for a pane spawn: the record is
        # project state and the updater reads it there
        RecordInstalled(parent_comp, name, landed, step.get('release', ''))
        # inside the toolkit, console contributors expose by default --
        # decided here, once, as the package lands (artifacts ship dormant).
        # A pane spawn sits in the user's network, outside the toolkit, so
        # that default does not apply.
        exposed = [] if (pane or rooted) else ExposeConsoleHosts(comp)
        results.append({'name': name, 'action': 'installed', 'bound': bound,
                        'exposed': exposed,
                        'placed': dest.path if (pane or rooted) else '',
                        **_verify(comp)})
    return {'target': tgt,
            'installed': [r['name'] for r in results if r.get('action') == 'installed'],
            'failed': [r['name'] for r in results if not r.get('ok', True)],
            'results': results,
            # non-empty = pane placement fell back to the target, and why
            'pane_note': pane_note,
            'registries': PromotedRegistries()}


# --- COMP extension ---------------------------------------------------

class InstallerExt:
    """Parameter front-end over the helpers above."""

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

    def _par(self, name, default=''):
        p = getattr(self.ownerComp.par, name, None)
        return str(p.eval()).strip() if p is not None else default

    def _status(self, text):
        p = getattr(self.ownerComp.par, 'Status', None)
        if p is not None:
            p.val = text[:400]

    def _writePlan(self, plan):
        t = self.ownerComp.op('plan')
        if t is None:
            return
        t.clear()
        t.appendRow(['package', 'kind', 'state', 'MB', 'artifact'])
        if plan.get('locked'):
            t.appendRow(['(target)', '', 'LOCKED', '', plan['locked']])
        for s in plan['steps']:
            state = ('stale cache -> re-download' if s.get('stale')
                     else 'present' if s['present']
                     else 'to install' if s.get('have') else 'to download')
            t.appendRow([s['name'], s['kind'], state,
                         '%.2f' % (s.get('bytes', 0) / 1048576.0),
                         os.path.basename(s['path'])])
        for n in plan['missing_artifact']:
            t.appendRow([n, '', 'NO ARTIFACT', '', ''])
        for n in plan['unknown_packages']:
            t.appendRow([n, '', 'NOT IN MANIFEST', '', ''])

    def Plan(self):
        """Dry run: fill the plan table, change nothing."""
        selection = self._par('Selectionfile')
        if not selection:
            self._status('Set Selection to a selection.json from the '
                         'configurator first.')
            return None
        try:
            plan = ResolvePlan(selection,
                               self._par('Manifestfile') or DefaultManifest(),
                               self._par('Target')
                               or DefaultTarget(self.ownerComp))
        except Exception as e:
            self._status('Plan failed: %s' % e)
            return None
        # a refused package folder locks the plan like a refused target, so
        # every consumer -- Install, the served picker -- sees one answer
        if not plan.get('locked'):
            why = FolderLock(self._bindChoice())
            if why:
                plan['locked'] = why
        self._writePlan(plan)
        if plan.get('locked'):
            self._status('LOCKED -- ' + plan['locked'])
            return plan
        note = ''
        other = op('/' + ROOT_NAME)
        if other is not None and other.path != plan['target'] \
                and not plan['target'].startswith(other.path + '/'):
            note = ' (NOTE: this project already has a toolkit at %s)' % other.path
        if plan.get('stale_store'):
            note += ('; %d stale store cop%s to re-download'
                     % (len(plan['stale_store']),
                        'y' if len(plan['stale_store']) == 1 else 'ies'))
        if plan.get('hash_warnings'):
            note += ('; HASH MISMATCH kept as-is (not the store): '
                     + ', '.join(plan['hash_warnings']))
        self._status('%d package(s) to install into %s%s%s'
                     % (len(plan['steps']), plan['target'],
                        '; MISSING: ' + ', '.join(plan['missing_artifact'])
                        if plan['missing_artifact'] else '', note))
        return plan

    def _bindChoice(self):
        """Where package files go, from the Package Files menu.

        Embedded is the default: one .toe to move, nothing to lose. The two
        bound modes exist because a package that lives in a file can be
        updated by rewriting that file -- no COMP surgery -- and 'project'
        additionally lets one project hold a modified package without
        touching any other install on the machine.
        """
        mode = self._par('Packagefiles', 'embedded') or 'embedded'
        if mode == 'embedded':
            return None
        if mode == 'shared':
            return 'shared'
        folder = self._par('Packagefolder')
        return folder or (project.folder + '/FNStools').replace('\\', '/')

    def Install(self, remove=None):
        """Install everything the plan resolves to; with `remove` (or the
        Remove Unselected toggle) also remove manifest tools the
        selection no longer includes -- the picker's apply semantics."""
        plan = self.Plan()
        if plan is None:
            return None
        if plan.get('locked'):
            self._status('REFUSED -- ' + plan['locked'])
            return None
        replace = bool(getattr(self.ownerComp.par, 'Replace', None)
                       and self.ownerComp.par.Replace.eval())
        if remove is None:
            p = getattr(self.ownerComp.par, 'Removeunselected', None)
            remove = bool(p and p.eval())
        res = InstallPlan(plan, replace=replace, bind=self._bindChoice())
        res['removed'], res['remove_notes'] = [], []
        if remove and plan.get('to_remove'):
            rm = RemoveTools(plan)
            res['removed'] = rm['removed']
            res['remove_notes'] = rm['notes']
        self._status('installed %d, removed %d, failed %d%s'
                     % (len(res['installed']), len(res['removed']),
                        len(res['failed']),
                        ': ' + ', '.join(res['failed']) if res['failed'] else ''))
        return res

    def onParPlan(self, _par):
        self.Plan()

    def onParInstall(self, _par):
        self.Install()

    # --- command rail (FNS_CommandRegistry) ---------------------------
    # The installer answers install requests as COMMANDS, so a consumer
    # (the launcher) never places toxes itself. One owner of placement
    # means one install record, one update path, and no duplicates --
    # docs/LauncherToolkitBoundary.md, Option A.

    def FnsCommands(self):
        """Spec list for FNS_CommandRegistry.

        `install` is DRY RUN by default. A request arriving from another
        application is not the same as a user agreeing to it, so the
        default answer is a plan describing what would land; `confirm`
        performs it. Same shape as fns.collect, which consumers already
        know how to render.
        """
        cap = 'fns.install'
        return [
            {'id': 'install', 'label': 'Install an FNS package…',
             'help': 'Plan an install (dry run); pass confirm=True to apply',
             'method': 'CommandInstall',
             'surface': ['session'], 'capability': cap},
            {'id': 'installed', 'label': 'Installed packages',
             'help': 'What this project has, as the install record knows it',
             'method': 'CommandInstalled', 'hidden': True, 'capability': cap},
            {'id': 'available', 'label': 'Available packages',
             'help': 'What the manifest offers, with launcher reach',
             'method': 'CommandAvailable', 'hidden': True, 'capability': cap},
        ]

    def onInitTD(self):
        # Deferred: a registry may still be promoting its /sys global, and
        # on a fresh bootstrap drop this COMP's own siblings are still
        # arriving. Guarded inside, so no registry is never an error.
        run('args[0]._registerLauncherCommands()', self, delayFrames=60)

    def _registerLauncherCommands(self):
        """Announce to a registry if one is present. Guarded: no registry
        is ever guaranteed, and the tag makes one that arrives LATER
        rediscover this COMP by rescan."""
        try:
            self.ownerComp.tags.add('fnscommands')
        except Exception:
            pass
        try:
            reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
            if reg is not None and hasattr(reg, 'Register'):
                return reg.Register(self.ownerComp, self.FnsCommands())
        except Exception:
            pass
        return None

    def CommandInstall(self, package='', confirm=False, source=''):
        """Install ONE package by name, minimally.

        `source` is an optional local artifact path, so a caller holding
        bytes already (a launcher's bundled free artifact) installs from
        them rather than the store -- a real install with a record and an
        update path, not a dropped tox. A supplied file older than the
        manifest installs with a warning and records the sha that landed,
        so the next online Compare() offers the upgrade.
        """
        name = str(package).strip()
        if not name:
            return {'ok': False, 'error': 'no package named'}
        try:
            plan = ResolvePlan(
                {'schema': 1, 'install': [name], 'tools': [name], 'core': []},
                self._par('Manifestfile') or DefaultManifest(),
                self._par('Target') or DefaultTarget(self.ownerComp),
                minimal=True,
                sources={name: source} if source else None)
        except Exception as e:
            return {'ok': False, 'error': str(e)[:160]}
        if plan.get('unknown_packages'):
            return {'ok': False, 'error': '%s is not in the manifest' % name}
        if plan.get('locked'):
            return {'ok': False, 'error': plan['locked']}
        would = [s['name'] for s in plan['steps']]
        summary = {'ok': True, 'package': name, 'target': plan['target'],
                   'would_install': would,
                   'already_present': plan['already_present'],
                   'needs_download': plan['to_fetch'],
                   'older_than_manifest': plan['hash_warnings']}
        if not confirm:
            summary['dry_run'] = True
            return summary
        if plan['to_fetch']:
            why = self._refreshStore(names=plan['to_fetch'])
            summary.update({'ok': not why, 'fetching': True,
                            'error': why or '',
                            'text': why or 'downloading %d artifact(s); '
                                           'run again when it settles'
                                    % len(plan['to_fetch'])})
            return summary
        res = InstallPlan(plan, replace=False, bind=self._bindChoice())
        summary.update({'ok': not res['failed'], 'dry_run': False,
                        'installed': res['installed'], 'failed': res['failed']})
        return summary

    def CommandInstalled(self):
        """The install record: what landed here, at which sha and release."""
        tgt = op(self._par('Target') or DefaultTarget(self.ownerComp))
        t = tgt.op(INSTALLED_DAT) if tgt is not None else None
        rows = []
        if t is not None and t.numRows > 1:
            for i in range(1, t.numRows):
                rows.append({c: t[i, n].val for n, c in enumerate(INSTALLED_COLS)})
        return {'ok': True, 'target': tgt.path if tgt else '', 'packages': rows}

    def CommandAvailable(self):
        """What the manifest offers, with the `launcher` block passed
        through so a consumer can show only what reaches its surfaces.

        NOTE the shape difference, confirmed against a live consumer: the
        MANIFEST omits `launcher` for a package that has none
        (presence-style, like `placement`), but this projection always
        emits the key, `null` when absent. That is deliberate here — a
        consumer iterating packages gets a stable shape and can read
        `p['launcher']` without a membership test — but it means "absent"
        and "null" both mean not-launcher-capable, and a consumer must
        tolerate whichever it meets depending on whether it is reading the
        manifest or asking us.
        """
        try:
            man = LoadJson(self._par('Manifestfile') or DefaultManifest(),
                           'manifest')
        except Exception as e:
            return {'ok': False, 'error': str(e)[:160]}
        out = []
        for p in man.get('packages', []):
            out.append({'name': p['name'], 'version': p.get('version', ''),
                        'access': p.get('access', 'free'),
                        'launcher': p.get('launcher') or None})
        return {'ok': True, 'release': man.get('release', ''), 'packages': out}

    # --- the served configurator (bootstrap rail) ---------------------
    #
    # A Web Server DAT inside this COMP serves the picker page and takes
    # the selection back as a POST -- no file leaves the browser, no par
    # has to be pointed anywhere. The page lives in ./configurator_html
    # (embedded at build time); the manifest it shows is whatever
    # DefaultManifest() resolves to, and when neither store nor repo has
    # one yet the sibling FNS_Updater is asked to refresh the store while the
    # page shows "downloading" and polls.

    def _port(self):
        try:
            return int(self._par('Port') or 36760)
        except ValueError:
            return 36760

    # Fifty wide, like the console's block: Windows reserves ~16-port
    # ranges for Hyper-V/WSL at semi-random places, and a narrow scan that
    # starts inside one finds nothing free on an idle machine.
    PORT_SPAN = 50

    def _freePort(self):
        """First free port from Port upward (PORT_SPAN tries). Several
        open projects each carry an installer -- and the FNS console scans
        36710-36759 the same way -- so a fixed port would make the second
        server fail to bind; a bind test picks a live one instead."""
        import socket
        base = self._port()
        for port in range(base, min(base + self.PORT_SPAN, 65535)):
            s = socket.socket()
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
            finally:
                s.close()
        return None

    BIND_ADDRESS = '127.0.0.1'

    def _bindLoopback(self, ws):
        """Pin the picker's Web Server DAT to loopback.

        A BLANK Local Address makes a Web Server DAT listen on EVERY
        interface (Derivative: "When left blank, the Web Server DAT will
        listen on all interfaces"). The bind test in _freePort above uses
        127.0.0.1 and reads like the thing that keeps this private -- it is
        not; that socket is closed again and constrains nothing. Left blank,
        /selection and /install were drivable by anyone on the same network.

        Applied on every Configure(), not once at build time: installers
        already in the field carry the old blank value, and re-asserting is
        the only thing that repairs them. Restart if it was already serving
        -- the DAT reads this at bind time, not per request.
        """
        if ws is None:
            return
        try:
            if str(ws.par.localaddress.eval()) == self.BIND_ADDRESS:
                return
            ws.par.localaddress = self.BIND_ADDRESS
            if ws.par.active.eval():
                ws.par.restart.pulse()
        except Exception as e:
            debug('INSTALLER: could not pin %s to %s (%s) -- it may be '
                  'reachable from the network' % (ws.path, self.BIND_ADDRESS, e))

    def Configure(self):
        """Serve the picker and show it: the sibling webBrowser COMP if
        this installer ships inside the bootstrap root, else the system
        browser."""
        ws = self.ownerComp.op('webserver')
        if ws is None:
            self._status('no webserver DAT -- rebuild the installer')
            return
        self._bindLoopback(ws)
        port = ws.par.port.eval() if ws.par.active.eval() else self._freePort()
        if port is None:
            self._status('no free port in %d-%d -- close another picker or '
                         'change Configurator Port'
                         % (self._port(), self._port() + self.PORT_SPAN - 1))
            return
        if not ws.par.active.eval():
            ws.par.port = int(port)
            ws.par.active = True
        url = 'http://127.0.0.1:%d/' % int(port)
        parent = self.ownerComp.parent()
        browser = parent.op('webBrowser') if parent is not None else None
        if browser is not None:
            act = getattr(browser.par, 'Active', None)
            if act is not None and not act.eval():
                act.val = True
            # Declare the serve: an openViewer window satisfies NONE of
            # the browser's visibility watchers (measured -- not winopen,
            # not viewer-active, not a pane), so without the hold the
            # watchers switch the render back off one frame after this
            # method turns it on, and Pick Tools opens a blank panel.
            # Released by _serverOff when the picker server stops.
            if hasattr(browser.par, 'Holdactive'):
                browser.par.Holdactive = True
            browser.par.Address = url
            browser.openViewer()
        else:
            import webbrowser
            webbrowser.open(url)
        self._status('configurator at %s' % url)

    def onParConfigure(self, _par):
        self.Configure()

    def _updaterComp(self):
        parent = self.ownerComp.parent()
        return parent.op('FNS_Updater') if parent is not None else None

    def _refreshStore(self, names=None):
        """Kick the sibling FNS_Updater's store refresh; harmless if one is
        already running (it refuses). `names` scopes the fetch ([] is
        manifest-only -- the picker; a list is the selection at install).

        Scheduled via run(), never called inline: this fires from the web
        server's request callback, and the one observed refresh that
        started inside that callback finished 'done' having fetched
        nothing, while the identical call from the textport fetched the
        whole store. Marshaling out of the callback context is the same
        cure the updater itself applies everywhere else."""
        upd = self._updaterComp()
        if upd is None or getattr(upd, 'RefreshStore', None) is None:
            return 'no FNS_Updater next to the installer -- refresh the store yourself'
        run("op(%r).RefreshStore(names=%r)" % (upd.path, names), delayFrames=1)
        return ''

    def _refreshJob(self):
        """The sibling FNS_Updater's current job dict, or None."""
        upd = self._updaterComp()
        try:
            return getattr(upd.ext.ExtUpdater, '_job', None) if upd else None
        except Exception:
            return None

    def _refreshActive(self):
        job = self._refreshJob()
        return bool(job) and job.get('stage') not in ('done', 'failed')

    def _planText(self, plan):
        lines = ['install into %s' % plan['target'], '']
        if plan.get('locked'):
            lines = ['REFUSED -- ' + plan['locked'], ''] + lines
        fetch_bytes = 0
        for s in plan['steps']:
            if s.get('stale'):
                state = ('present, stale cache -> re-download' if s['present']
                         else 'install (stale cache -> re-download)')
                fetch_bytes += s.get('bytes', 0)
            elif s['present']:
                state = 'present, kept'
            elif s.get('have'):
                state = 'install'
            else:
                state = 'install (download)'
                fetch_bytes += s.get('bytes', 0)
            lines.append('%-26s %-5s %s' % (s['name'], s['kind'], state))
        for n in plan.get('to_remove', []):
            lines.append('%-26s %-5s %s' % (n, 'tool',
                         'REMOVE (settings kept for reinstall)'))
        for n in plan['missing_artifact']:
            lines.append('%-26s %s' % (n, 'NO ARTIFACT'))
        for n in plan['unknown_packages']:
            lines.append('%-26s %s' % (n, 'NOT IN MANIFEST'))
        if fetch_bytes:
            lines.append('')
            lines.append('%.1f MB to download' % (fetch_bytes / 1048576.0))
        return '\n'.join(lines)

    # The bootstrap's own residents: a root holding nothing but these has
    # never been installed into, and the page runs its guided first run.
    RAILS = ('FNS_Installer', 'FNS_Updater', 'webBrowser')

    def _isFirstRun(self, tgt):
        """True when the target holds no package yet (rails aside)."""
        if tgt is None:
            return False
        return not any(c.family == 'COMP' and c.name not in self.RAILS
                       for c in tgt.children)

    def _openSettings(self):
        """Hand the panel over to the FNS console's Settings tab -- the
        root's own Open Settings pulse, so the routing (console, or an
        older registry's forward, in-TD panel or system browser) stays in
        one place. Returns an error string, '' on success."""
        root = self.ownerComp.parent()
        par = getattr(root.par, 'Opensettings', None) if root else None
        if par is None:
            return 'this installer is not inside a toolkit root -- use the ' \
                   'FNS console directly'
        if getattr(op, 'FNS_CONSOLE', None) is None \
                and getattr(op, 'FNS_CONFIGREGISTRY', None) is None:
            return 'no FNS console installed yet'
        # deferred: the pulse navigates the very panel this request came
        # from, and the response must leave first
        run("op(%r).par.Opensettings.pulse()" % root.path, delayFrames=2)
        return ''

    def _serverOff(self, delay_ms):
        """Deactivate the picker server later -- and release the browser
        hold with it: Holdactive means "being served", and a stopped
        server is the definition of not being served."""
        ws = self.ownerComp.op('webserver')
        parent = self.ownerComp.parent()
        browser = parent.op('webBrowser') if parent is not None else None
        if ws is not None:
            run("op(%r).par.active = False" % ws.path,
                delayMilliSeconds=delay_ms)
        if browser is not None and hasattr(browser.par, 'Holdactive'):
            run("op(%r).par.Holdactive = False" % browser.path,
                delayMilliSeconds=delay_ms)

    def _accountGlobal(self):
        """`window.FNS_ACCOUNT = ...;` for the served page, or ''.

        Omitted entirely when there is no updater beside us, so the page
        can tell "no auth rail here" from "signed out" -- the first has
        no sign-in to offer, the second does.

        Derived facts only. The device token and the download token stay
        in the updater: this page is rendered, not trusted.
        """
        upd = self._updaterComp()
        if upd is None:
            return ''
        acct = None
        try:
            a = upd.ext.ExtAuth
            if a is not None:
                rec = a.Account()
                if rec:
                    acct = {'label': rec.get('label') or 'supporter',
                            'products': sorted(rec.get('products') or []),
                            'checked_at': rec.get('checked_at') or 0,
                            # a BOOLEAN on purpose -- whether they hold
                            # any Patreon tier at all decides the button
                            # copy (Upgrade vs Become a supporter); the
                            # ids themselves stay in the keystore
                            'tier': bool(rec.get('tiers'))}
        except Exception:
            # never let an auth problem stop the picker from being served
            acct = None
        return 'window.FNS_ACCOUNT = %s;\n' % json.dumps(acct)

    def ServeRequest(self, request, response):
        """onHTTPRequest for the embedded Web Server DAT."""
        uri = request.get('uri', '/')
        method = request.get('method', 'GET')
        response['statusCode'], response['statusReason'] = 200, 'OK'
        try:
            if method == 'GET' and uri in ('/', '/index.html'):
                page = self.ownerComp.op('configurator_html')
                response['Content-Type'] = 'text/html; charset=utf-8'
                response['data'] = page.text if page else 'configurator_html missing'
            elif method == 'GET' and uri == '/manifest.js':
                response['Content-Type'] = 'text/javascript; charset=utf-8'
                path = self._par('Manifestfile') or DefaultManifest()
                full = path if os.path.isabs(path) else RepoPath(path)
                tgt = op(self._par('Target') or DefaultTarget(self.ownerComp))
                firstrun = self._isFirstRun(tgt)
                # the picker needs only the MANIFEST -- artifacts download
                # per-selection at install time, so a lightweight drop
                # stays lightweight until the user actually picks
                if os.path.exists(full):
                    # the page pre-checks what THIS PROJECT actually has,
                    # so unchecking an installed tool reads as removal --
                    # the machine-wide selection.json is scratch, not truth
                    installed, locked = [], ''
                    if tgt is not None:
                        installed = sorted(c.name for c in tgt.children
                                           if c.family == 'COMP')
                        # pane-placed packages are installed WITHOUT being
                        # root children: their truth is the install record.
                        # Without this they re-arrive unchecked and a
                        # re-apply spawns a second copy.
                        try:
                            man_doc = LoadJson(full, 'manifest')
                            spawn_names = {p['name']
                                           for p in man_doc.get('packages', [])
                                           if p.get('placement') in ('pane', 'root')}
                            rec_t = tgt.op(INSTALLED_DAT)
                            if rec_t is not None and spawn_names:
                                installed = sorted(set(installed) | {
                                    rec_t[i, 0].val
                                    for i in range(1, rec_t.numRows)
                                    if rec_t[i, 0].val in spawn_names})
                        except Exception:
                            pass
                        # the page disables Apply up front rather than
                        # letting the user pick and then get refused
                        locked = SourceLock(tgt.path)
                    # the machine's last install, for the first run's
                    # "Set up like last time" -- only offered on a bare
                    # root, so only read there
                    last = LastInstall(tgt) if firstrun else None
                    # Plus picks the user WANTED but could not install --
                    # every selection writer records them in `tools` while
                    # keeping them out of `install`. Resurfacing them here
                    # is what makes the wish survive sign-in, instead of
                    # living exactly one Textport line and evaporating.
                    wanted = []
                    try:
                        # Read the file THIS rail installs from -- the
                        # paste points Selectionfile at its own write in
                        # the store, and /selection re-points it at the
                        # palette copy. The machine-wide palette file is
                        # only the fallback: reading it unconditionally
                        # let a stale scratch copy from another session
                        # swallow a fresh paste's Plus picks (seen live:
                        # a wanted FNS_TimelineTools arrived unchecked).
                        selp = str(self._par('Selectionfile') or '')
                        if not (selp and os.path.exists(selp)):
                            selp = ('%s/FNStools_ext/selection.json'
                                    % app.userPaletteFolder).replace('\\', '/')
                        if os.path.exists(selp):
                            with open(selp, 'r', encoding='utf-8') as sf:
                                seldoc = json.load(sf)
                            wanted = sorted(set(seldoc.get('tools') or [])
                                            - set(seldoc.get('install') or [])
                                            - set(installed))
                    except Exception:
                        wanted = []
                    with open(full, 'r', encoding='utf-8') as f:
                        response['data'] = ('window.FNS_SERVED = true;\n'
                                            'window.FNS_FIRSTRUN = %s;\n'
                                            'window.FNS_LAST = %s;\n'
                                            'window.FNS_INSTALLED = %s;\n'
                                            'window.FNS_WANTED = %s;\n'
                                            'window.FNS_LOCKED = %s;\n'
                                            '%s'
                                            'window.FNS_MANIFEST = %s;\n'
                                            % (json.dumps(firstrun),
                                               json.dumps(last),
                                               json.dumps(installed),
                                               json.dumps(wanted),
                                               json.dumps(locked),
                                               self._accountGlobal(), f.read()))
                else:
                    why = '' if self._refreshActive() \
                        else self._refreshStore(names=[])
                    response['data'] = ('window.FNS_REFRESHING = true;\n'
                                        'window.FNS_FIRSTRUN = %s;%s\n'
                                        % (json.dumps(firstrun),
                                           ' // ' + why if why else ''))
            elif method == 'POST' and uri == '/auth/recheck':
                # "I just pledged" -- forces the gate past its six-hour
                # entitlement cache. The outcome arrives asynchronously:
                # the page polls /auth/status for the sentence and reloads
                # ITSELF when the products change (it does now -- this
                # comment used to promise that falsely).
                upd = self._updaterComp()
                why = ''
                if upd is None:
                    why = 'no FNS_Updater next to the installer'
                else:
                    try:
                        upd.ext.ExtAuth.Recheck()
                    except Exception as e:
                        why = str(e)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': not why,
                     'text': why or 'Checking with Patreon…'})
            elif method == 'POST' and uri == '/auth/signin':
                # the picker is where someone MEETS a Plus tool, so it is
                # where they will want to sign in. Starting it is all this
                # does: the updater owns the browser round trip, and the
                # page learns the outcome on its next load.
                upd = self._updaterComp()
                why = ''
                if upd is None:
                    why = 'no FNS_Updater next to the installer'
                else:
                    try:
                        upd.ext.ExtAuth.SignIn()
                    except Exception as e:
                        why = str(e)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': not why,
                     'text': why or 'Check your browser to finish signing in, '
                                    'then reload this page.'})
            elif method == 'POST' and uri == '/auth/redeem':
                # The lifetime-key door, on the same rail as Sign in: the
                # /plus/ page promises keys are redeemed "in the same
                # place as the Patreon connection", and before this route
                # that place was a parameter page the funnel never
                # pointed at. The page sends the PACKAGE name (a buyer
                # knows the tool, not Gumroad's product id); the gate
                # resolves it through its own map. Outcome is async --
                # the page's /auth/status watcher shows it and reloads
                # on product changes, same as sign-in.
                upd = self._updaterComp()
                why = ''
                raw = request.get('data', b'')
                try:
                    doc = json.loads(raw.decode('utf-8')
                                     if isinstance(raw, bytes) else str(raw))
                except Exception:
                    doc = {}
                if upd is None:
                    why = 'no FNS_Updater next to the installer'
                else:
                    try:
                        r = upd.ext.ExtAuth.RedeemKey(
                            key=str(doc.get('key') or ''),
                            package=str(doc.get('package') or ''))
                        if not r.get('ok'):
                            why = r.get('why', 'redeem refused')
                    except Exception as e:
                        why = str(e)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': not why, 'text': why or 'Checking your licence…'})
            elif method == 'GET' and uri == '/auth/status':
                # The sign-in/recheck OUTCOME, readable by the page. The
                # auth extension writes its result to Authstatus
                # asynchronously, and before this route the sentence
                # landed on a par nobody rendered while the dialog said
                # only "reload in a moment" -- a throttled user reloaded,
                # saw an unchanged chip, and concluded it was broken. The
                # page polls this after a recheck/sign-in, shows the
                # sentence, and reloads itself when products changed.
                upd = self._updaterComp()
                status_txt, products = '', None
                if upd is not None:
                    try:
                        p = getattr(upd.par, 'Authstatus', None)
                        status_txt = str(p.eval()) if p is not None else ''
                    except Exception:
                        status_txt = ''
                    try:
                        a = upd.ext.ExtAuth
                        rec = a.Account() if a is not None else None
                        if rec:
                            products = sorted(rec.get('products') or [])
                    except Exception:
                        products = None
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': True, 'status': status_txt, 'products': products})
            elif method == 'POST' and uri == '/settings':
                # the page's "Open Settings" after an install: the console
                # takes the panel over, and this server has nothing left
                # to serve
                why = self._openSettings()
                response['Content-Type'] = 'application/json'
                # A real sentence on success: the page falls back to
                # "could not open the console" for EMPTY text, so the old
                # '' success read as a failure in the field.
                response['data'] = json.dumps(
                    {'ok': not why,
                     'text': why or 'Opening the FNS console…'})
                if not why:
                    self._serverOff(1500)
            elif method == 'POST' and uri == '/selection':
                sel_dir = ('%s/FNStools_ext' % app.userPaletteFolder).replace('\\', '/')
                os.makedirs(sel_dir, exist_ok=True)
                sel_path = sel_dir + '/selection.json'
                data = request.get('data', '')
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                sel = json.loads(data)    # refuse to write junk
                with open(sel_path, 'w', encoding='utf-8') as f:
                    f.write(data)
                self.ownerComp.par.Selectionfile = sel_path
                # "Set up like last time" carries the bind mode the last
                # install used; an ordinary selection leaves the par alone
                bind = sel.get('bind') if isinstance(sel, dict) else None
                pf = getattr(self.ownerComp.par, 'Packagefiles', None)
                if bind and pf is not None and bind in pf.menuNames:
                    pf.val = bind
                plan = self.Plan()
                response['Content-Type'] = 'application/json'
                if (plan is None or plan.get('locked')
                        or plan['missing_artifact'] or not plan['steps']):
                    text = (self._planText(plan) if plan
                            else self._par('Status') or 'plan failed')
                    response['data'] = json.dumps({'ok': False, 'text': text})
                else:
                    response['data'] = json.dumps({'ok': True,
                                                   'text': self._planText(plan)})
            elif method == 'GET' and uri == '/status':
                # the page's fetch-then-install poll: how far along is the
                # scoped download, and is the selection installable yet?
                response['Content-Type'] = 'application/json'
                job = self._refreshJob()
                fetching = bool(job) and job.get('stage') not in ('done', 'failed')
                done = len(job.get('fetched', [])) if job else 0
                togo = (len(job.get('queue', [])) + len(job.get('inflight', {}))
                        if job else 0)
                ready, failed = False, []
                # A gated skip is a REFUSAL with a sentence, not a download
                # failure -- and its artifact will never arrive, so `ready`
                # must stop waiting for it or the page reports the refusal
                # as an unknown failure forever (field-confirmed on the
                # first real walk). Stamped reasons (gate unreachable,
                # session expired) speak verbatim; the local entitlement
                # skip falls back to MissingFor.
                gated, gated_why = [], []
                if job:
                    gated = sorted(set(job.get('gated') or []))
                    reasons = job.get('gated_reasons') or {}
                    aut = None
                    try:
                        upd = self._updaterComp()
                        aut = upd.ext.ExtAuth if upd is not None else None
                    except Exception:
                        aut = None
                    for n in gated:
                        gated_why.append(
                            reasons.get(n)
                            or (aut.MissingFor(n) if aut
                                else '%s needs a supporter account.' % n))
                if not fetching:
                    failed = list(job.get('failed', [])) if job else []
                    try:
                        plan = ResolvePlan(self._par('Selectionfile'),
                                           self._par('Manifestfile') or DefaultManifest(),
                                           self._par('Target')
                                           or DefaultTarget(self.ownerComp))
                        ready = not [n for n in plan['to_fetch']
                                     if n not in set(gated)]
                    except Exception:
                        ready = False
                # The updater's own Status par narrates the pass hop by hop
                # ("refresh: authorising...", "fetching 3 artifact(s)...").
                # Relaying it means a wedge NAMES ITS HOP in the page dialog
                # instead of looping a counter that says "Downloading" even
                # while the pass is authorising (0.5's observability half).
                detail = ''
                try:
                    upd2 = self._updaterComp()
                    if upd2 is not None:
                        detail = str(upd2.par.Status.eval())
                except Exception:
                    detail = ''
                response['data'] = json.dumps(
                    {'fetching': fetching, 'fetched': done, 'togo': togo,
                     'ready': ready, 'failed': failed[:4],
                     'gated': gated[:8], 'gated_why': gated_why[:4],
                     'detail': detail[:200]})
            elif method == 'POST' and uri == '/install':
                plan = ResolvePlan(self._par('Selectionfile'),
                                   self._par('Manifestfile') or DefaultManifest(),
                                   self._par('Target')
                                   or DefaultTarget(self.ownerComp))
                if plan.get('locked'):
                    response['Content-Type'] = 'application/json'
                    response['data'] = json.dumps(
                        {'ok': False, 'text': 'REFUSED -- ' + plan['locked']})
                    return response
                if plan['to_fetch']:
                    # download exactly the selection, then the page polls
                    # /status and re-posts /install once it is all here
                    mb = sum(s.get('bytes', 0) for s in plan['steps']
                             if s['name'] in plan['to_fetch']) / 1048576.0
                    why = self._refreshStore(names=plan['to_fetch'])
                    response['Content-Type'] = 'application/json'
                    response['data'] = json.dumps(
                        {'ok': not why, 'fetching': True,
                         'text': why or 'downloading %d package(s), %.1f MB...'
                                 % (len(plan['to_fetch']), mb)})
                    return response
                res = self.Install(remove=True)
                response['Content-Type'] = 'application/json'
                if res is None:
                    response['data'] = json.dumps(
                        {'ok': False, 'text': self._par('Status') or 'install failed'})
                else:
                    lines = ['installed %d, removed %d, failed %d'
                             % (len(res['installed']), len(res.get('removed', [])),
                                len(res['failed']))]
                    placed = {r['name']: r.get('placed', '')
                              for r in res.get('results', [])}
                    lines += ['  %s%s' % (n, ' → ' + placed[n]
                                          if placed.get(n) else '')
                              for n in res['installed']]
                    if res.get('pane_note'):
                        lines.append('  (%s -- spawned into the toolkit '
                                     'container instead)' % res['pane_note'])
                    lines += ['  removed %s' % n for n in res.get('removed', [])]
                    lines += ['  %s' % n for n in res.get('remove_notes', [])]
                    lines += ['  FAILED %s' % n for n in res['failed']]
                    response['data'] = json.dumps(
                        {'ok': not res['failed'], 'text': '\n'.join(lines)})
                    if not res['failed']:
                        # Done: stop serving, AFTER this response has gone
                        # out. Otherwise the server stays on forever and
                        # gets saved into the .toe still listening. A
                        # minute, not seconds: the page's done step offers
                        # Open Settings (POST /settings), which needs a
                        # server to answer.
                        self._serverOff(60000)
            else:
                response['statusCode'], response['statusReason'] = 404, 'Not Found'
                response['data'] = 'not found'
        except Exception as e:
            response['statusCode'], response['statusReason'] = 500, 'Error'
            response['data'] = 'server error: %s' % e
        return response
