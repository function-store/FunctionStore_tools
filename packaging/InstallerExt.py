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


def ResolvePlan(selection_path, manifest_path=DEFAULT_MANIFEST, target=None):
    """Resolve a selection into an ordered install plan. Never mutates."""
    manifest = LoadJson(manifest_path, 'manifest')
    sel = LoadJson(selection_path, 'selection')
    index = {p['name']: p for p in manifest['packages']}

    wanted = list(sel.get('install') or (sel.get('core', []) + sel.get('tools', [])))
    unknown = [n for n in wanted if n not in index]
    # Core is not optional: a selection that omits it is a broken selection,
    # not a request to go without the infrastructure every tool plugs into.
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
    tool_names = {p['name'] for p in manifest['packages'] if p['kind'] == 'tool'}
    root_comp = op(tgt)
    to_remove = sorted(c.name for c in root_comp.children
                       if c.family == 'COMP' and c.name in tool_names
                       and c.name not in wanted) if root_comp else []

    steps, missing, hash_warnings = [], [], []
    for name in ordered:
        pkg = index[name]
        art = pkg.get('artifact')
        if not art:
            missing.append(name)
            continue
        path = _artifactPath(art, name, manifest_path)
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
                if _inStore(path):
                    stale = True
                else:
                    hash_warnings.append(name)
        steps.append({'name': name, 'kind': pkg['kind'], 'path': path,
                      'sha256': art.get('sha256', ''),
                      'bytes': art.get('bytes', 0),
                      'release': manifest.get('release', ''),
                      'have': have, 'stale': stale,
                      'present': op(tgt + '/' + name) is not None})
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
    for name in plan.get('to_remove', []):
        comp = parent_comp.op(name)
        if comp is None:
            continue
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
        t = parent_comp.op(INSTALLED_DAT)
        if t is not None:
            for i in range(t.numRows - 1, 0, -1):
                if t[i, 0].val == name:
                    t.deleteRow(i)
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

    results = []
    for step in plan['steps']:
        name = step['name']
        if only and name not in only:
            continue
        existing = parent_comp.op(name)
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
        before = {c.id for c in parent_comp.children}
        try:
            parent_comp.loadTox(step['path'])
        except Exception as e:
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': str(e)[:140]})
            continue
        fresh = [c for c in parent_comp.children if c.id not in before]
        comp = fresh[0] if fresh else parent_comp.op(name)
        if comp is not None and comp.name != name:
            comp.name = name  # TD numbers on collision; the manifest name wins
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
        RecordInstalled(parent_comp, name, landed, step.get('release', ''))
        # inside the toolkit, console contributors expose by default --
        # decided here, once, as the package lands (artifacts ship dormant)
        exposed = ExposeConsoleHosts(comp)
        results.append({'name': name, 'action': 'installed', 'bound': bound,
                        'exposed': exposed, **_verify(comp)})
    return {'target': tgt,
            'installed': [r['name'] for r in results if r.get('action') == 'installed'],
            'failed': [r['name'] for r in results if not r.get('ok', True)],
            'results': results,
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

    def Configure(self):
        """Serve the picker and show it: the sibling webBrowser COMP if
        this installer ships inside the bootstrap root, else the system
        browser."""
        ws = self.ownerComp.op('webserver')
        if ws is None:
            self._status('no webserver DAT -- rebuild the installer')
            return
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
                # the picker needs only the MANIFEST -- artifacts download
                # per-selection at install time, so a lightweight drop
                # stays lightweight until the user actually picks
                if os.path.exists(full):
                    # the page pre-checks what THIS PROJECT actually has,
                    # so unchecking an installed tool reads as removal --
                    # the machine-wide selection.json is scratch, not truth
                    installed, locked = [], ''
                    tgt = op(self._par('Target')
                             or DefaultTarget(self.ownerComp))
                    if tgt is not None:
                        installed = sorted(c.name for c in tgt.children
                                           if c.family == 'COMP')
                        # the page disables Apply up front rather than
                        # letting the user pick and then get refused
                        locked = SourceLock(tgt.path)
                    with open(full, 'r', encoding='utf-8') as f:
                        response['data'] = ('window.FNS_SERVED = true;\n'
                                            'window.FNS_INSTALLED = %s;\n'
                                            'window.FNS_LOCKED = %s;\n'
                                            'window.FNS_MANIFEST = %s;\n'
                                            % (json.dumps(installed),
                                               json.dumps(locked), f.read()))
                else:
                    why = '' if self._refreshActive() \
                        else self._refreshStore(names=[])
                    response['data'] = ('window.FNS_REFRESHING = true;%s\n'
                                        % (' // ' + why if why else ''))
            elif method == 'POST' and uri == '/selection':
                sel_dir = ('%s/FNStools_ext' % app.userPaletteFolder).replace('\\', '/')
                os.makedirs(sel_dir, exist_ok=True)
                sel_path = sel_dir + '/selection.json'
                data = request.get('data', '')
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                json.loads(data)          # refuse to write junk
                with open(sel_path, 'w', encoding='utf-8') as f:
                    f.write(data)
                self.ownerComp.par.Selectionfile = sel_path
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
                if not fetching:
                    failed = list(job.get('failed', [])) if job else []
                    try:
                        plan = ResolvePlan(self._par('Selectionfile'),
                                           self._par('Manifestfile') or DefaultManifest(),
                                           self._par('Target')
                                           or DefaultTarget(self.ownerComp))
                        ready = not plan['to_fetch']
                    except Exception:
                        ready = False
                response['data'] = json.dumps(
                    {'fetching': fetching, 'fetched': done, 'togo': togo,
                     'ready': ready, 'failed': failed[:4]})
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
                    lines += ['  %s' % n for n in res['installed']]
                    lines += ['  removed %s' % n for n in res.get('removed', [])]
                    lines += ['  %s' % n for n in res.get('remove_notes', [])]
                    lines += ['  FAILED %s' % n for n in res['failed']]
                    response['data'] = json.dumps(
                        {'ok': not res['failed'], 'text': '\n'.join(lines)})
                    if not res['failed']:
                        # Done: stop serving, AFTER this response has gone
                        # out. Otherwise the server stays on forever and
                        # gets saved into the .toe still listening.
                        ws = self.ownerComp.op('webserver')
                        if ws is not None:
                            run("op(%r).par.active = False" % ws.path,
                                delayMilliSeconds=3000)
            else:
                response['statusCode'], response['statusReason'] = 404, 'Not Found'
                response['data'] = 'not found'
        except Exception as e:
            response['statusCode'], response['statusReason'] = 500, 'Error'
            response['data'] = 'server error: %s' % e
        return response
