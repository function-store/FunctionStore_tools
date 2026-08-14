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


ROOT_NAME = 'FunctionStore_tools_2025'


def DefaultTarget(owner=None):
    """Where packages land.

    An installer that ships INSIDE the toolkit root (the bootstrap .tox)
    installs into its own parent -- that is the whole point of the
    bootstrap: the container you dropped IS the install target, wherever
    you dropped it. Otherwise: the project's toolkit container if it has
    one, else a new one next to Embody (dev) or at / (a bare project).
    """
    if owner is not None and owner.parent() is not None \
            and owner.parent().name == ROOT_NAME:
        return owner.parent().path
    existing = op('/' + ROOT_NAME)
    if existing is not None:
        return existing.path
    embody = getattr(op, 'Embody', None)
    home = embody.parent().path if embody is not None else '/'
    return home.rstrip('/') + '/' + ROOT_NAME


def DefaultManifest():
    """The manifest to read when none is given: the palette store's, if the
    store has ever been refreshed -- artifacts sit beside it, so a user
    project needs no further configuration -- else the repo's (dev)."""
    store = ('%s/FNStools_ext/store/manifest.json'
             % app.userPaletteFolder).replace('\\', '/')
    if os.path.exists(store):
        return store
    return DEFAULT_MANIFEST


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

    steps, missing = [], []
    for name in ordered:
        pkg = index[name]
        art = pkg.get('artifact')
        if not art:
            missing.append(name)
            continue
        path = _artifactPath(art, name, manifest_path)
        if not os.path.exists(path):
            missing.append(name + ' (artifact file absent)')
            continue
        steps.append({'name': name, 'kind': pkg['kind'], 'path': path,
                      'sha256': art.get('sha256', ''),
                      'bytes': art.get('bytes', 0),
                      'release': manifest.get('release', ''),
                      'present': op(tgt + '/' + name) is not None})
    return {'target': tgt, 'steps': steps, 'order': [s['name'] for s in steps],
            'already_present': [s['name'] for s in steps if s['present']],
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


def InstallPlan(plan, replace=False, only=None, bind=None):
    """Execute a plan from ResolvePlan. `only` limits to named packages,
    which is how a large install is batched under the MCP timeout. `bind`
    decides where the package files live -- see _bindPackage."""
    tgt = plan['target']
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
            results.append({'name': name, 'action': 'skipped (present)',
                            **_verify(existing)})
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
        RecordInstalled(parent_comp, name, step.get('sha256', ''), step.get('release', ''))
        results.append({'name': name, 'action': 'installed', 'bound': bound,
                        **_verify(comp)})
    return {'target': tgt,
            'installed': [r['name'] for r in results if r.get('action') == 'installed'],
            'failed': [r['name'] for r in results if not r.get('ok', True)],
            'results': results}


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
        for s in plan['steps']:
            t.appendRow([s['name'], s['kind'],
                         'present' if s['present'] else 'to install',
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
        self._status('%d package(s) to install into %s%s'
                     % (len(plan['steps']), plan['target'],
                        '; MISSING: ' + ', '.join(plan['missing_artifact'])
                        if plan['missing_artifact'] else ''))
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

    def Install(self):
        """Install everything the plan resolves to."""
        plan = self.Plan()
        if plan is None:
            return None
        replace = bool(getattr(self.ownerComp.par, 'Replace', None)
                       and self.ownerComp.par.Replace.eval())
        res = InstallPlan(plan, replace=replace, bind=self._bindChoice())
        self._status('installed %d, failed %d%s'
                     % (len(res['installed']), len(res['failed']),
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
    # one yet the sibling UPDATER is asked to refresh the store while the
    # page shows "downloading" and polls.

    def _port(self):
        try:
            return int(self._par('Port') or 9877)
        except ValueError:
            return 9877

    def Configure(self):
        """Serve the picker and show it: the sibling webBrowser COMP if
        this installer ships inside the bootstrap root, else the system
        browser."""
        ws = self.ownerComp.op('webserver')
        if ws is None:
            self._status('no webserver DAT -- rebuild the installer')
            return
        ws.par.port = self._port()
        ws.par.active = True
        url = 'http://127.0.0.1:%d/' % self._port()
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

    def _refreshStore(self):
        """Kick the sibling UPDATER's store refresh; harmless if one is
        already running (it refuses)."""
        parent = self.ownerComp.parent()
        upd = parent.op('UPDATER') if parent is not None else None
        refresh = getattr(upd, 'RefreshStore', None) if upd is not None else None
        if refresh is None:
            return 'no UPDATER next to the installer -- refresh the store yourself'
        try:
            refresh()
        except Exception as e:
            return 'store refresh failed to start: %s' % e
        return ''

    def _planText(self, plan):
        lines = ['install into %s' % plan['target'], '']
        for s in plan['steps']:
            lines.append('%-26s %-5s %s' % (s['name'], s['kind'],
                         'present, kept' if s['present'] else 'install'))
        for n in plan['missing_artifact']:
            lines.append('%-26s %s' % (n, 'NO ARTIFACT'))
        for n in plan['unknown_packages']:
            lines.append('%-26s %s' % (n, 'NOT IN MANIFEST'))
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
                if os.path.exists(full):
                    with open(full, 'r', encoding='utf-8') as f:
                        response['data'] = ('window.FNS_SERVED = true;\n'
                                            'window.FNS_MANIFEST = %s;\n' % f.read())
                else:
                    why = self._refreshStore()
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
                if plan is None or plan['missing_artifact'] or not plan['steps']:
                    text = (self._planText(plan) if plan
                            else self._par('Status') or 'plan failed')
                    response['data'] = json.dumps({'ok': False, 'text': text})
                else:
                    response['data'] = json.dumps({'ok': True,
                                                   'text': self._planText(plan)})
            elif method == 'POST' and uri == '/install':
                res = self.Install()
                response['Content-Type'] = 'application/json'
                if res is None:
                    response['data'] = json.dumps(
                        {'ok': False, 'text': self._par('Status') or 'install failed'})
                else:
                    lines = ['installed %d, failed %d'
                             % (len(res['installed']), len(res['failed']))]
                    lines += ['  %s' % n for n in res['installed']]
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
