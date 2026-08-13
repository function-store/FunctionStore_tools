"""Install a picked subset of the toolkit into a TouchDesigner project.

Runs INSIDE TouchDesigner. Consumes the two artifacts the rest of the
packaging track produces: `manifest.json` (what exists) and a
`selection.json` from the configurator (what you want).

    exec(open('packaging/install.py').read())
    result = Plan('packaging/selection.json')        # dry run, always safe
    result = Install('packaging/selection.json')     # actually install

Step 3 of docs/ConfiguratorDistribution.md §4. This is the rail that needs
no web presence: point it at local artifacts in `packaging/dist` and
pick-and-choose already works.

ORDER MATTERS. Core goes in first: every tool ships a stamped registry
HOST whose master lives in a core package, and a host with no master
cannot clone. The manifest's `requires` already encodes that, so the plan
is a topological walk of it rather than a hardcoded list.

WHAT THIS DOES NOT DO
    It does not fetch over the network (artifacts are local files today),
    and it does not uninstall. Removing a package is `comp.destroy()` plus
    a registry heal tick -- worth a real Uninstall() once the install path
    has been exercised on more than one machine.
"""

import json
import os

DEFAULT_MANIFEST = 'packaging/manifest.json'


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def _load(path, what):
    full = path if os.path.isabs(path) else _repo(path)
    if not os.path.exists(full):
        raise FileNotFoundError('%s not found: %s' % (what, full))
    with open(full, 'r', encoding='utf-8') as f:
        return json.load(f)


def _index(manifest):
    return {p['name']: p for p in manifest['packages']}


def _order(names, index):
    """Core-first topological order over `requires`.

    Cycles cannot happen while tools only depend on core (the rule the
    manifest generator enforces), but a cycle must not hang an installer,
    so unresolved names are appended rather than spun on.
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


def Plan(selection_path, manifest_path=DEFAULT_MANIFEST, target=None):
    """Resolve a selection into an ordered install plan. Never mutates."""
    manifest = _load(manifest_path, 'manifest')
    sel = _load(selection_path, 'selection')
    index = _index(manifest)

    wanted = list(sel.get('install') or (sel.get('core', []) + sel.get('tools', [])))
    unknown = [n for n in wanted if n not in index]
    # core is not optional: a selection that omits it is a broken selection,
    # not a request to skip the infrastructure
    for c in manifest.get('core', []):
        if c not in wanted:
            wanted.append(c)

    ordered = _order([n for n in wanted if n in index], index)
    tgt = target or _installTarget()

    steps, missing = [], []
    for name in ordered:
        pkg = index[name]
        art = pkg.get('artifact')
        if not art:
            missing.append(name)
            continue
        path = _repo(art['path'])
        if not os.path.exists(path):
            missing.append(name + ' (artifact file absent)')
            continue
        steps.append({'name': name, 'kind': pkg['kind'], 'path': path,
                      'sha256': art.get('sha256', ''),
                      'present': op(tgt + '/' + name) is not None})
    return {'target': tgt, 'steps': steps, 'order': [s['name'] for s in steps],
            'already_present': [s['name'] for s in steps if s['present']],
            'missing_artifact': missing, 'unknown_packages': unknown}


def _installTarget():
    """Where packages land. The toolkit container if this project already
    has one, else a new sibling of Embody -- the project's stable home."""
    existing = op('/FunctionStore_tools_2025')
    if existing is not None:
        return existing.path
    return op.Embody.parent().path + '/FunctionStore_tools_2025'


def _verify(comp, expect_sha):
    """A package is installed when its COMP exists, its extensions are up,
    and it reports no errors -- not merely when loadTox returned."""
    if comp is None or not comp.valid:
        return {'ok': False, 'why': 'comp missing after load'}
    errs = comp.errors(recurse=True)
    return {'ok': not errs, 'why': (errs.splitlines()[0][:120] if errs else ''),
            'ops': len(comp.findChildren()),
            'extensions_ready': bool(comp.extensionsReady)}


def Install(selection_path, manifest_path=DEFAULT_MANIFEST, target=None,
            replace=False, only=None):
    """Install the selection. `only` limits to named packages (batching a
    big install keeps any one call well clear of the MCP timeout);
    `replace` re-loads packages that are already present."""
    plan = Plan(selection_path, manifest_path, target)
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
                            **_verify(existing, step['sha256'])})
            continue
        if existing is not None:
            existing.destroy()
        # loadTox loads the component INTO the given COMP, i.e. it creates
        # the child itself. Pre-creating a container named after the package
        # nests it one level too deep (AutoRes/AutoRes), so load onto the
        # target and identify the child by diffing.
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
        results.append({'name': name, 'action': 'installed',
                        **_verify(comp, step['sha256'])})
    return {'target': tgt, 'installed': [r['name'] for r in results
                                         if r.get('action') == 'installed'],
            'failed': [r['name'] for r in results if not r.get('ok', True)],
            'results': results}
