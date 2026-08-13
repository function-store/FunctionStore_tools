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

DEFAULT_MANIFEST = 'packaging/manifest.json'


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


def DefaultTarget():
    """Where packages land: the toolkit container if this project has one,
    else a new sibling of Embody -- the project's stable home."""
    existing = op('/FunctionStore_tools_2025')
    if existing is not None:
        return existing.path
    return op.Embody.parent().path + '/FunctionStore_tools_2025'


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

    steps, missing = [], []
    for name in ordered:
        pkg = index[name]
        art = pkg.get('artifact')
        if not art:
            missing.append(name)
            continue
        path = RepoPath(art['path'])
        if not os.path.exists(path):
            missing.append(name + ' (artifact file absent)')
            continue
        steps.append({'name': name, 'kind': pkg['kind'], 'path': path,
                      'sha256': art.get('sha256', ''),
                      'bytes': art.get('bytes', 0),
                      'present': op(tgt + '/' + name) is not None})
    return {'target': tgt, 'steps': steps, 'order': [s['name'] for s in steps],
            'already_present': [s['name'] for s in steps if s['present']],
            'missing_artifact': missing, 'unknown_packages': unknown}


def _verify(comp):
    """Installed means the COMP exists, its extensions are up and it
    reports no errors -- not merely that loadTox returned."""
    if comp is None or not comp.valid:
        return {'ok': False, 'why': 'comp missing after load'}
    errs = comp.errors(recurse=True)
    return {'ok': not errs, 'why': (errs.splitlines()[0][:120] if errs else ''),
            'ops': len(comp.findChildren()),
            'extensions_ready': bool(comp.extensionsReady)}


def InstallPlan(plan, replace=False, only=None):
    """Execute a plan from ResolvePlan. `only` limits to named packages,
    which is how a large install is batched under the MCP timeout."""
    tgt = plan['target']
    parent_comp = op(tgt)
    if parent_comp is None:
        home = op(tgt.rsplit('/', 1)[0])
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
        results.append({'name': name, 'action': 'installed', **_verify(comp)})
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
        try:
            plan = ResolvePlan(self._par('Selectionfile'),
                               self._par('Manifestfile') or DEFAULT_MANIFEST,
                               self._par('Target') or None)
        except Exception as e:
            self._status('Plan failed: %s' % e)
            return None
        self._writePlan(plan)
        self._status('%d package(s) to install into %s%s'
                     % (len(plan['steps']), plan['target'],
                        '; MISSING: ' + ', '.join(plan['missing_artifact'])
                        if plan['missing_artifact'] else ''))
        return plan

    def Install(self):
        """Install everything the plan resolves to."""
        plan = self.Plan()
        if plan is None:
            return None
        replace = bool(getattr(self.ownerComp.par, 'Replace', None)
                       and self.ownerComp.par.Replace.eval())
        res = InstallPlan(plan, replace=replace)
        self._status('installed %d, failed %d%s'
                     % (len(res['installed']), len(res['failed']),
                        ': ' + ', '.join(res['failed']) if res['failed'] else ''))
        return res

    def onParPlan(self, _par):
        self.Plan()

    def onParInstall(self, _par):
        self.Install()
