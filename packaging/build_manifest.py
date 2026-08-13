"""Build packaging/manifest.json from the LIVE project.

Runs INSIDE TouchDesigner (needs `op`, `project`, `app`). Drive it from
Envoy with:

    exec(open('packaging/build_manifest.py').read()); result = Build()

or, to also export the per-package .tox artifacts (slower, and it stages a
copy per package -- do it in batches):

    exec(open('packaging/build_manifest.py').read())
    result = Build(export=['AutoRes', 'ColorUI'])      # named subset
    result = Build(export=True)                        # everything

WHAT IS DERIVED vs CURATED
    Derived live: which packages exist, version/build, which surfaces each
    contributes to, dependencies, optional integrations, op counts,
    artifact hashes. Curated in catalog.json: category and description --
    the two things the project cannot tell us.

THE DEPENDENCY MODEL (ConfiguratorDistribution.md 2.1)
    Tools depend only on CORE, never on each other, so the configurator
    needs no solver. That rule is enforceable here rather than asserted:
    registry MASTERS live in core and tools ship stamped HOSTS, so a
    tool's `requires` is exactly the set of core packages owning the
    registries it hosts. Anything a tool reaches for beyond that is an
    OPTIONAL integration (`integrates_with`) -- it must degrade when the
    other package is absent, and those call sites are guarded.
"""

import hashlib
import json
import os
import re

MANIFEST_SCHEMA = 1
PKG_DIR = 'packaging'
DIST_DIR = 'packaging/dist'
TOOLKIT = '/FunctionStore_tools_2025'

# Registry host name -> the core package that owns that registry's master.
REGISTRY_OWNER = {
    'ConfigRegistry': 'FNS_Config',
    'ToolbarRegistry': 'FNS_Toolbar',
    'NavbarRegistry': 'FNS_Navbar',
    'MainMenuRegistry': 'FNS_MainMenu',
    'OpMenuRegistry': 'FNS_OpMenu',
}
SURFACE_OF = {
    'ToolbarRegistry': 'toolbar',
    'NavbarRegistry': 'navbar',
    'MainMenuRegistry': 'mainmenu',
    'OpMenuRegistry': 'opmenu',
}
# Packages that ARE the infrastructure; always installed, never optional.
CORE = ('FNS_Config', 'FNS_Toolbar', 'FNS_Navbar', 'FNS_MainMenu',
        'FNS_OpMenu', 'FNS_HotkeyManager')


def _root():
    return op(TOOLKIT)


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def Packages():
    """Shippable packages = depth-1 COMPs that are tracked suspects with
    their own tox. That is already the project's own unit of distribution,
    so nothing new has to be invented or maintained by hand."""
    out = []
    for c in _root().children:
        if c.family != 'COMP':
            continue
        p = getattr(c.par, 'externaltox', None)
        if not (p and p.eval() and 'pi_suspect' in c.tags):
            continue
        out.append(c)
    return sorted(out, key=lambda c: c.name.lower())


def _vcData(comp):
    t = comp.op('vc_data')
    if not t or not t.numRows:
        return {}
    return {r[0].val: r[1].val for r in t.rows() if len(r) > 1}


def _hostedRegistries(comp):
    """Registry hosts at ANY depth inside the package.

    Most tools keep the host at depth 1 with its Comp par pointing at the
    widget, but that is convention, not law: a widget that travels with its
    own host carries it nested (midiMapper's button_midi_learn), and
    drop-to-register stamps hosts INTO dropped COMPs. Only looking at direct
    children silently under-reports the surfaces a package contributes to --
    and `requires` is derived from this, so it would under-report
    dependencies too.
    """
    found = {h.name for h in comp.findChildren() if h.name in REGISTRY_OWNER}
    return sorted(found)


def _helpUrl(comp):
    """Discovery, not migration: read the conventions already in use."""
    fa = comp.op('FNS_About')
    if fa is not None:
        p = getattr(fa.par, 'Helpurl', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
    for pn in ('Helpurl', 'Url', 'Wikipage'):
        p = getattr(comp.par, pn, None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
    dh = comp.op('docsHelper')
    if dh is not None:
        p = getattr(dh.par, 'Url', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
    # last resort: a registry entry published by this package carries one
    for regname in ('TOOLBARREGISTRY', 'NAVBARREGISTRY', 'MAINMENUREGISTRY'):
        g = getattr(op, regname, None)
        if g is None or not g.valid:
            continue
        ext = getattr(g.ext, regname.title().replace('registry', 'RegistryExt'), None)
        try:
            widgets = g.ext.__getattr__(
                [a for a in dir(g.ext) if a.endswith('RegistryExt')][0]).Widgets
        except Exception:
            continue
        for info in widgets.values():
            path = info.get('panel_path', '')
            if path.startswith(comp.path + '/') and info.get('help_url'):
                return info['help_url']
    return ''


def _shortcutOwners():
    """global shortcut -> owning package name (depth-1 only)."""
    owners = {}
    for o in op('/').findChildren(type=COMP):
        p = getattr(o.par, 'opshortcut', None)
        if p is None:
            continue
        v = p.eval()
        if v and o.path.startswith(TOOLKIT + '/'):
            owners[v] = o.path[len(TOOLKIT) + 1:].split('/')[0]
    return owners


_REGHOST_RE = re.compile(r'/(Toolbar|Navbar|Config|OpMenu|MainMenu|PaneType)Registry(/|$)')
# Both reference forms must be caught. `op.X` is the bare (raising) one;
# `getattr(op, 'X', ...)` is the GUARDED one an optional integration is
# supposed to use -- miss it and the manifest under-reports precisely the
# well-written integrations, which is backwards.
_SHORTCUT_RE = re.compile(
    r"""\bop\.([A-Za-z_][A-Za-z0-9_]*)"""
    r"""|getattr\(\s*op\s*,\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]""")


def _shortcutsIn(text):
    for bare, guarded in _SHORTCUT_RE.findall(text):
        yield bare or guarded


def Integrations():
    """package -> [packages it optionally reaches for].

    Same sweep as the ConfiguratorDistribution 1.1 audit: op.<SHORTCUT>
    references in DAT text and expression parameters, excluding stamped
    registry hosts (those point at core BY DESIGN and are already
    expressed as `requires`).
    """
    owners = _shortcutOwners()
    edges = {}
    for pkg in Packages():
        found = set()
        for o in [pkg] + pkg.findChildren():
            rel = o.path[len(pkg.path) + 1:] if o is not pkg else ''
            if _REGHOST_RE.search('/' + rel):
                continue
            if o.isDAT:
                try:
                    text = o.text
                except Exception:
                    text = ''
                if 'op.' in text or 'getattr(op' in text:
                    for line in text.splitlines():
                        if line.strip().startswith('#'):
                            continue
                        for m in _shortcutsIn(line):
                            t = owners.get(m)
                            if t and t != pkg.name:
                                found.add(t)
            for par in o.pars():
                if par.mode != ParMode.EXPRESSION:
                    continue
                try:
                    ex = par.expr or ''
                except Exception:
                    continue
                for m in _shortcutsIn(ex):
                    t = owners.get(m)
                    if t and t != pkg.name:
                        found.add(t)
        if found:
            edges[pkg.name] = sorted(found)
    return edges


def PortabilityWarnings(comp):
    """Absolute paths that would not survive a trip to another machine.

    Embody logs these during export and they scroll away. A package whose
    tables point at THIS machine's palette (or worse, at this repo's
    suspects tree) is a package that arrives subtly broken, so the finding
    belongs in the manifest where the installer and the picker can see it.

    Severity, worst first:
      project   -- points into THIS repo. A genuine packaging defect: the
                   path cannot exist on anyone else's machine.
      absolute  -- some other absolute path; needs a human look.
      tdinstall -- TD's own Samples/ (defcam.geo and friends). Present on
                   any install, but pinned to THIS TD version.
      palette   -- the user palette. Usually benign: these are per-user
                   data files the tool recreates.
    """
    palette = ''
    try:
        palette = app.userPaletteFolder.replace('\\', '/').rstrip('/')
    except Exception:
        pass
    tdroot = ''
    try:
        tdroot = app.installFolder.replace('\\', '/').rstrip('/')
    except Exception:
        pass
    here = project.folder.replace('\\', '/').rstrip('/')
    hits = []
    for o in [comp] + comp.findChildren():
        for pname in ('file', 'externaltox'):
            # The ROOT comp's externaltox is stripped by the portable export
            # (verified by loading the artifacts back); reporting it would be
            # a false positive. NESTED externaltox survives and is real -- an
            # OPTemplates artifact still expects OPTemplates1.tox to exist in
            # the installing user's palette.
            if pname == 'externaltox' and o is comp:
                continue
            p = getattr(o.par, pname, None)
            if p is None:
                continue
            try:
                v = str(p.eval() or '').replace('\\', '/')
            except Exception:
                continue
            if not v or not (':' in v[:3] or v.startswith('/')):
                continue  # relative == portable
            if palette and v.startswith(palette):
                kind = 'palette'
            elif v.startswith(here):
                kind = 'project'
            elif tdroot and v.startswith(tdroot):
                kind = 'tdinstall'
            else:
                kind = 'absolute'
            hits.append({'op': o.path[len(comp.path) + 1:] or o.name,
                         'par': pname, 'kind': kind, 'path': v})
    return hits


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def ExportPackage(comp):
    """Export one self-contained .tox (Embody metadata stripped) and hash it.

    Uses Embody's ExportPortableTox, which stages a COPY in /sys/quiet and
    runs the package's own pre_release hook -- so the live comp is never
    touched.
    """
    os.makedirs(_repo(DIST_DIR), exist_ok=True)
    dest = _repo(DIST_DIR, comp.name + '.tox')
    op.Embody.ExportPortableTox(target=comp, save_path=dest)
    if not os.path.exists(dest):
        return None
    return {'path': DIST_DIR + '/' + comp.name + '.tox',
            'bytes': os.path.getsize(dest),
            'sha256': _sha256(dest)}


def Build(export=False, out_path=None):
    """Write packaging/manifest.json. `export` may be False, True, or a
    list of package names to (re-)export artifacts for."""
    catalog_path = _repo(PKG_DIR, 'catalog.json')
    catalog = {}
    if os.path.exists(catalog_path):
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    curated = catalog.get('packages', {})

    out_path = out_path or _repo(PKG_DIR, 'manifest.json')
    previous = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, 'r', encoding='utf-8') as f:
                for entry in json.load(f).get('packages', []):
                    previous[entry['name']] = entry
        except Exception:
            previous = {}

    integrations = Integrations()
    want = set(export) if isinstance(export, (list, tuple, set)) else None

    packages = []
    for comp in Packages():
        name = comp.name
        vc = _vcData(comp)
        hosts = _hostedRegistries(comp)
        is_core = name in CORE
        meta = curated.get(name, {})

        requires = sorted({REGISTRY_OWNER[h] for h in hosts} - {name})
        if is_core:
            # core packages are installed as a unit; they do not "require"
            # each other in a way the picker should surface
            requires = []

        entry = {
            'name': name,
            'kind': 'core' if is_core else 'tool',
            'category': meta.get('category', 'Core' if is_core else 'Uncategorized'),
            'description': meta.get('description', ''),
            'version': vc.get('version', '') or '0',
            'build': vc.get('build', ''),
            'author': vc.get('author', ''),
            'help_url': _helpUrl(comp),
            'surfaces': sorted({SURFACE_OF[h] for h in hosts if h in SURFACE_OF}),
            'shortcut': str(comp.par.opshortcut.eval()),
            'ops': len(comp.findChildren()),
            'requires': requires,
            'integrates_with': integrations.get(name, []),
            'tox_carrier': 'root' if not comp.par.enableexternaltox.eval() else 'own',
            'cooking': bool(comp.allowCooking),
        }
        warn = PortabilityWarnings(comp)
        if warn:
            entry['portability'] = warn

        do_export = export is True or (want is not None and name in want)
        if do_export:
            art = ExportPackage(comp)
            if art:
                entry['artifact'] = art
        else:
            # Not re-exporting: hash whatever is already in dist/ so the
            # manifest describes the artifacts that actually exist on disk,
            # rather than only those built in this very run.
            built = _repo(DIST_DIR, name + '.tox')
            if os.path.exists(built):
                entry['artifact'] = {
                    'path': DIST_DIR + '/' + name + '.tox',
                    'bytes': os.path.getsize(built),
                    'sha256': _sha256(built),
                }
            elif previous.get(name, {}).get('artifact'):
                entry['artifact'] = previous[name]['artifact']
        packages.append(entry)

    doc = {
        'schema': MANIFEST_SCHEMA,
        'toolkit': {
            'name': _root().name,
            'td_build': app.version,
            'project': project.name,
        },
        'core': [p['name'] for p in packages if p['kind'] == 'core'],
        'categories': catalog.get('categories', []),
        'packages': packages,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write('\n')

    # Same data as a <script>-loadable file so configurator/index.html works
    # when opened straight off disk -- fetch() of a sibling .json is blocked
    # by CORS on file://, and a picker you cannot double-click is no picker.
    js_dir = _repo(PKG_DIR, 'configurator')
    payload = None
    if os.path.isdir(js_dir):
        payload = 'window.FNS_MANIFEST = ' + json.dumps(doc, indent=1) + ';'
        with open(os.path.join(js_dir, 'manifest.js'), 'w', encoding='utf-8') as f:
            f.write('// GENERATED by packaging/build_manifest.py -- do not edit.\n')
            f.write(payload + '\n')

    # Single-file build: the same picker with the manifest inlined, so it can
    # be handed to someone as ONE file -- no sibling manifest, no web server.
    standalone = None
    src_html = os.path.join(js_dir, 'index.html') if js_dir else None
    if payload and src_html and os.path.exists(src_html):
        with open(src_html, 'r', encoding='utf-8') as f:
            html = f.read()
        tag = '<script src="manifest.js"></script>'
        if tag in html:
            html = html.replace(tag, '<script>\n' + payload + '\n</script>', 1)
            standalone = _repo(PKG_DIR, 'configurator', 'configurator-standalone.html')
            with open(standalone, 'w', encoding='utf-8') as f:
                f.write(html)

    return {'written': out_path, 'standalone': standalone,
            'packages': len(packages),
            'core': len(doc['core']),
            'with_artifact': sum(1 for p in packages if 'artifact' in p),
            'uncategorized': [p['name'] for p in packages
                              if p['category'] == 'Uncategorized']}
