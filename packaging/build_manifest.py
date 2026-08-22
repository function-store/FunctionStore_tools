"""Build packaging/manifest.json from the LIVE project.

Runs INSIDE TouchDesigner (needs `op`, `project`, `app`). Drive it from
Envoy with:

    exec(open('packaging/build_manifest.py').read()); result = Build()

or, to also export the per-package .tox artifacts (slower, and it stages a
copy per package -- do it in batches):

    exec(open('packaging/build_manifest.py').read())
    result = Build(export=['AutoRes', 'ColorUI'])      # named subset
    result = Build(export=True)                        # everything

WHAT IS DERIVED vs CURATED vs DECLARED
    Derived live: which packages exist, which surfaces each contributes
    to, dependencies, optional integrations, op counts, artifact hashes.
    Curated in catalog.json: category and description. DECLARED by the
    author on the component itself: `Pkgversion` -- the one field a human
    must maintain, and the one the updater actually compares.

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
TOOLKIT = '/FNSTools'

# Where published artifacts live. Releases are PINNED: every artifact URL
# carries its release, so a manifest always resolves to the exact bytes it
# was built from. Never point an installer at a mutable "latest/" path --
# unreproducible installs make bug reports uncorrelatable (§3).
# Custom domain over the R2 bucket (objects under the fnstools/ prefix).
# The r2.dev dev URL keeps serving the same bucket as a fallback.
BASE_URL = 'https://storage.functionstr.com/fnstools'

# Registry host name -> the core package that owns that registry's master.
# Every registry package IS its master -- the raw registry, promoted to
# /sys, cloneable by anyone extending the toolkit. The FNS_* shells that
# used to carry them are ordinary optional tools now: requires point at
# the registries themselves, because that is all a host actually needs.
REGISTRY_OWNER = {
    'FNS_ConfigRegistry': 'FNS_ConfigRegistry',
    'FNS_ToolbarRegistry': 'FNS_ToolbarRegistry',
    'FNS_NavbarRegistry': 'FNS_NavbarRegistry',
    'FNS_MainMenuRegistry': 'FNS_MainMenuRegistry',
    'FNS_OpMenuRegistry': 'FNS_OpMenuRegistry',
    'FNS_PaneTypeRegistry': 'FNS_PaneTypeRegistry',
    'FNS_Console': 'FNS_Console',
}
SURFACE_OF = {
    'FNS_ToolbarRegistry': 'toolbar',
    'FNS_NavbarRegistry': 'navbar',
    'FNS_MainMenuRegistry': 'mainmenu',
    'FNS_OpMenuRegistry': 'opmenu',
    'FNS_PaneTypeRegistry': 'panebar',
}
# Packages that ARE the infrastructure; always installed, never optional.
# Core = the raw registries plus FNS_Updater -- the one non-registry
# exception, because it is how an install ever becomes a newer install:
# leaving it optional means the one package that can fetch updates is the
# one a user can accidentally decline.
CORE = ('FNS_ConfigRegistry', 'FNS_ToolbarRegistry', 'FNS_NavbarRegistry',
        'FNS_MainMenuRegistry', 'FNS_OpMenuRegistry', 'FNS_PaneTypeRegistry',
        'FNS_Console', 'FNS_Updater')


def _root():
    return op(TOOLKIT)


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


# Dev-root residents that are RAILS, not packages: they ship inside the
# bootstrap (build_installer.BOOTSTRAP_KEEP) and are published under the
# manifest's `rails`, never as installable packages -- even when Private
# Investigator tracks them like every other dev-root component.
RAILS = ('FNS_Installer', 'webBrowser')


def Packages():
    """Shippable packages = depth-1 COMPs that are tracked suspects with
    their own tox. That is already the project's own unit of distribution,
    so nothing new has to be invented or maintained by hand."""
    out = []
    for c in _root().children:
        if c.family != 'COMP' or c.name in RAILS:
            continue
        p = getattr(c.par, 'externaltox', None)
        if not (p and p.eval() and 'pi_suspect' in c.tags):
            continue
        out.append(c)
    return sorted(out, key=lambda c: c.name.lower())


def _version(comp):
    """The package's own version, from the `Pkgversion` par WE govern.

    Deliberately not `vc_data` / the `Vc*` pars: that table belongs to
    Private Investigator, is written by tooling outside this repo, and the
    data does not support the weight -- 1 of 39 packages had a version at
    all. Deliberately not a content fingerprint either: the only stable one
    available came from TDN, which is an external package.

    So the version is ours, stamped on the component, and it is the ONLY
    thing that answers "is a newer build available?". Artifact hashes
    cannot: two exports of an untouched COMP differ (verified -- 66198 /
    66190 / 66150 bytes, diverging at byte 9 of the container header), so
    a sha256 comparison would mark every package updated on every release.
    Hashes verify downloads; this decides updates.
    """
    p = getattr(comp.par, 'Pkgversion', None)
    return str(p.eval()).strip() if p is not None else ''


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


DOCS_SITE = 'https://tools.functionstore.xyz/docs'


def _docsSlug(name):
    """URL slug for a package page. Must match packageSlug() in
    website/tools/build-site.mjs and package_slug() in
    docs_seed_from_wiki.py -- the three of them agreeing is what makes
    help_url land on a page that exists."""
    return name.lower().replace('_', '-')


def _helpUrl(comp):
    """Discovery, not migration: read the conventions already in use.

    Falls back to the package's own page on the docs site when
    packaging/docs/<Name>.md exists. That file is the source the site is
    generated from, so a package with docs always has a working help URL
    without anyone hand-entering one; a component that declares its own
    URL still wins."""
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
    for regname in ('FNS_TOOLBARREGISTRY', 'FNS_NAVBARREGISTRY', 'FNS_MAINMENUREGISTRY'):
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
    if os.path.exists(_repo(PKG_DIR, 'docs', '%s.md' % comp.name)):
        return '%s/%s/' % (DOCS_SITE, _docsSlug(comp.name))
    return ''


def ReleaseNotes():
    """Curated prose for the CURRENT publish, from release_notes.md.

    Comments (<!-- -->) are instructions to the author, not notes --
    stripped here. Empty is fine: the changelog entry then carries just
    the auto-generated package list. release_one.py clears the file
    after a successful publish (the text moves to CHANGELOG.md and into
    the release's own manifest)."""
    path = _repo(PKG_DIR, 'release_notes.md')
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return text.strip()


def AttributedNotes():
    """Split release_notes.md into per-tool notes and general prose.

    The convention: a line starting with a package name and a colon
    ("AutoRes: fixed X", optionally bulleted) belongs to that tool;
    everything else is release-level prose. Attribution is by exact
    package name, so a typo silently demotes a line to general prose --
    the changelog still keeps it, nothing is lost."""
    names = {c.name for c in Packages()}
    per_tool, general = {}, []
    for line in ReleaseNotes().splitlines():
        m = re.match(r'^\s*[-*]?\s*([A-Za-z_][\w]*)\s*:\s*(.+)$', line)
        if m and m.group(1) in names:
            per_tool.setdefault(m.group(1), []).append(m.group(2).strip())
        else:
            general.append(line)
    per_tool = {k: ' '.join(v) for k, v in per_tool.items()}
    return per_tool, '\n'.join(general).strip()


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


_REGHOST_RE = re.compile(r'/FNS_(Toolbar|Navbar|Config|OpMenu|MainMenu|PaneType)Registry(/|$)')
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
            # REDACT the machine-specific prefix: the manifest is PUBLIC,
            # and a raw absolute path publishes the username and disk
            # layout. The classification plus the relative tail carries
            # everything the picker or a bug report needs.
            if palette and v.startswith(palette):
                kind, shown = 'palette', '<palette>' + v[len(palette):]
            elif v.startswith(here):
                kind, shown = 'project', '<repo>' + v[len(here):]
            elif tdroot and v.startswith(tdroot):
                kind, shown = 'tdinstall', '<td>' + v[len(tdroot):]
            else:
                kind = 'absolute'
                home = os.path.expanduser('~').replace('\\', '/')
                shown = '~' + v[len(home):] if home and v.startswith(home) else v
            hits.append({'op': o.path[len(comp.path) + 1:] or o.name,
                         'par': pname, 'kind': kind, 'path': shown})
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
    before = os.path.getmtime(dest) if os.path.exists(dest) else None
    ok = op.Embody.ExportPortableTox(target=comp, save_path=dest)
    # A failed export (aborted pre_release hook) leaves the OLD file on
    # disk. Hashing it would publish a stale artifact under a fresh version
    # -- the silent mismatch that bit v2.12.1 -- so a requested export that
    # did not rewrite the file returns None and Build reports it loudly.
    if not ok or not os.path.exists(dest):
        return None
    if before is not None and os.path.getmtime(dest) == before:
        return None
    return {'path': DIST_DIR + '/' + comp.name + '.tox',
            'bytes': os.path.getsize(dest),
            'sha256': _sha256(dest)}


def _release():
    """Human-facing release label for the whole toolkit, from
    packaging/release.json.

    Deliberately NOT a git tag: distribution is bucket + manifest (and
    native .exe/.dmg installers), so the label is ours to set. The root
    COMP's `Gittag` par remains only as a fallback for projects that have
    not adopted release.json.

    This label names the RELEASE; per-package `Pkgversion` decides
    updates. Both exist because they answer different questions: "which
    drop is this?" for changelogs and support, versus "does this package
    have a newer build than the one installed?" for the updater.
    """
    path = _repo(PKG_DIR, 'release.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                rel = str(json.load(f).get('release', '')).strip()
            if rel:
                return rel
        except Exception as e:
            debug('packaging: release.json unreadable (%s)' % e)
    p = getattr(_root().par, 'Gittag', None)
    return str(p.eval()).strip() if p is not None and str(p.eval()).strip() else 'untagged'


def _channel():
    path = _repo(PKG_DIR, 'release.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return str(json.load(f).get('channel', 'stable')).strip() or 'stable'
        except Exception:
            pass
    return 'stable'


def Build(export=False, out_path=None, base_url=BASE_URL, release=None):
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
    export_failed = []
    attributed, _general_notes = AttributedNotes()

    packages = []
    for comp in Packages():
        name = comp.name
        hosts = _hostedRegistries(comp)
        is_core = name in CORE
        meta = curated.get(name, {})

        requires = sorted({REGISTRY_OWNER[h] for h in hosts} - {name})
        if is_core:
            # core packages are installed as a unit; they do not "require"
            # each other in a way the picker should surface
            requires = []

        surfaces = {SURFACE_OF[h] for h in hosts if h in SURFACE_OF}
        # The 'UI Tab' capability section (Uitab* pars on the Registry
        # page) marks a tool that contributes a tab to the tools_ui panel
        # (tools_ui sweeps for it). Presence of the par, not its current
        # toggle state: the toggle is user preference that roams via
        # config, the capability is what the package ships.
        if getattr(comp.par, 'Uitab', None) is not None:
            surfaces.add('tools_ui')

        entry = {
            'name': name,
            'kind': 'core' if is_core else 'tool',
            'category': meta.get('category', 'Core' if is_core else 'Uncategorized'),
            'description': meta.get('description', ''),
            'version': _version(comp),
            'help_url': _helpUrl(comp),
            'surfaces': sorted(surfaces),
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

        # per-tool release note for the CURRENT version: freshly attributed
        # prose when this release moves the version, otherwise carried from
        # the previous manifest (it still describes the shipped version)
        if entry['version'] != previous.get(name, {}).get('version'):
            entry['whatsnew'] = attributed.get(name, '')
        else:
            entry['whatsnew'] = previous.get(name, {}).get('whatsnew', '')

        do_export = export is True or (want is not None and name in want)
        if do_export:
            art = ExportPackage(comp)
            if art:
                entry['artifact'] = art
            else:
                # no artifact key at all: Stage() then reports it missing
                # and refuses, instead of shipping yesterday's bytes
                export_failed.append(name)
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

    rel = release or _release()
    for entry in packages:
        art = entry.get('artifact')
        if art:
            # Pinned per release. The sha256 already in `art` is what an
            # updater compares against; the URL is just where to get it.
            art['url'] = '%s/%s/%s.tox' % (base_url.rstrip('/'), rel, entry['name'])

    doc = {
        'schema': MANIFEST_SCHEMA,
        'release': rel,
        'notes': ReleaseNotes(),
        'channel': _channel(),
        'base_url': base_url.rstrip('/'),
        'toolkit': {
            'name': _root().name,
            'td_build': app.version,
            'project': project.name,
        },
        'core': [p['name'] for p in packages if p['kind'] == 'core'],
        'categories': catalog.get('categories', []),
        # Presentation per category -- the glyph and the one-line pitch the
        # CMS curates beside the category list. Packaging does not read it;
        # it rides along so the configurator can head its sections the same
        # way the website does, including when the picker is served from
        # inside TouchDesigner with no site to fetch it from.
        'category_meta': catalog.get('category_meta', {}),
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
            'export_failed': export_failed,
            'uncategorized': [p['name'] for p in packages
                              if p['category'] == 'Uncategorized']}
