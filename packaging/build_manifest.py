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
# The bucket's r2.dev development URL must stay DISABLED: it serves the
# whole bucket publicly and would hand out the gated plus/ prefix behind
# the Worker's back. upload.py's canary fails the release if it is on.
BASE_URL = 'https://storage.functionstore.tools/fnstools'
# Gated artifacts live under this prefix on the SAME host. The prefix is
# not publicly readable: a Worker in front of it checks entitlement and
# streams from the bucket. Free artifacts keep the plain release path and
# are served straight off the CDN, so nothing about the free rail changes.
PLUS_PREFIX = 'plus'

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
    'FNS_HubRegistry': 'FNS_HubRegistry',
    # The tenth registry. Listed here like the rest so a tool that hosts it
    # is FOUND (_hostedRegistries only looks for names in this map) and so
    # `requires` names it -- installing FNS_TimelineTools without the
    # registry that carries its panels is a broken install.
    'FNS_TimelineRegistry': 'FNS_TimelineRegistry',
}
# WHAT A PACKAGE GIVES YOU, keyed by the registry it hosts to give it.
#
# This is the toolkit's one surface vocabulary. A package's `surfaces` is
# how a reader answers "does this put a button somewhere, or is it a
# background behaviour" -- so it is what the picker chips, what the docs
# page states, and what both of them filter on. The LABELS live beside the
# ids on purpose: a second copy of the words in the picker and a third in
# the site is exactly how those two drifted apart before.
SURFACE_OF = {
    'FNS_ToolbarRegistry': 'toolbar',
    'FNS_NavbarRegistry': 'navbar',
    'FNS_MainMenuRegistry': 'mainmenu',
    'FNS_OpMenuRegistry': 'opmenu',
    'FNS_PaneTypeRegistry': 'panebar',
    'FNS_HubRegistry': 'hub',
    'FNS_Console': 'console',
    'FNS_TimelineRegistry': 'timeline',
    # FNS_ConfigRegistry is deliberately absent. 37 of the 49 packages host
    # it, so a chip for it would mark almost everything and separate
    # nothing -- and what it grants (settings that follow you between
    # projects) is the toolkit's default rather than a feature of any one
    # tool. See docs/ScopeAndPersistence.md.
    #
    # FNS_PaletteRegistry is absent because nothing hosts it: the palette
    # tabs it serves appear without any tool registering (PaletteTabContract).
}
# The words a reader sees. Phrased as what you GET, not as the machinery
# that puts it there -- "Toolbar button", never "hosts ToolbarRegistry".
SURFACE_LABEL = {
    'toolbar': 'Toolbar button',
    'navbar': 'Pane bar button',
    'mainmenu': 'Main menu entry',
    'opmenu': 'OP Create menu entry',
    'panebar': 'Custom pane type',
    'hub': 'Hub tab',
    'console': 'Console tab',
    'timeline': 'Timeline panel',
}
# Packages that ARE the infrastructure; always installed, never optional.
# Core = the raw registries plus two non-registry exceptions: FNS_Updater,
# because it is how an install ever becomes a newer install (leaving it
# optional means the one package that can fetch updates is the one a user
# can accidentally decline), and FNS_Hub, the FNS button + manager window
# that is the ONE affordance for every registry -- the surface configurators
# are its tabs, so a root without it has no way to manage its bars.
CORE = ('FNS_ConfigRegistry', 'FNS_ToolbarRegistry', 'FNS_NavbarRegistry',
        'FNS_MainMenuRegistry', 'FNS_OpMenuRegistry', 'FNS_PaneTypeRegistry',
        'FNS_Console', 'FNS_HubRegistry', 'FNS_Hub', 'FNS_Updater')


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
    fa = comp.op('FNS_About')
    if fa is not None:
        # the child is the authoritative copy (release bumps write it);
        # reading it directly means a severed comp-level mirror can never
        # invert who wins -- the comp par is display, not truth
        p = getattr(fa.par, 'Pkgversion', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
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


DOCS_SITE = 'https://functionstore.tools/docs'

# Where membership is bought -- the manifest's toolkit block carries it so
# every surface (picker chip, refusal sentences, the Become a supporter /
# Upgrade button) names the SAME door. This constant is the owner; the
# /plus/ page holds the human explanation of the same URL.
SUPPORT_URL = 'https://patreon.com/function_store'


def _entitlementRoutes():
    """(ladder, key_available_names): the tier ladder as [{'id','label'}]
    and the set of packages a Gumroad key unlocks. Projections of their
    OWNING files -- gate_package.py's TIER_LADDER and wrangler.toml's
    GUMROAD_PRODUCTS -- never a second authority; absent or unreadable
    sources degrade to empty (an old-style manifest, not a failure)."""
    ladder, keyed = [], set()
    try:
        # __name__ set on purpose: without it the exec'd module believes
        # it is __main__ and runs gate_package's CLI (measured: it did,
        # and died on TD's CWD being the install directory).
        ns = {'__name__': 'fns_gate_package'}
        exec(open(_repo('packaging', 'gate_package.py'),
                  encoding='utf-8').read(), ns)
        ladder = [{'id': str(t), 'label': str(l)}
                  for t, l in ns.get('TIER_LADDER', ())]
    except Exception as e:
        debug('packaging: tier ladder unavailable (%s)' % e)
    try:
        # gate_package's own readers resolve relative to CWD (a shell at
        # the repo root); under TD that is the install dir, so the toml
        # block is read here with an absolute path instead.
        import re as _re
        src = open(_repo('worker', 'wrangler.toml'), encoding='utf-8').read()
        m = _re.search(r'^GUMROAD_PRODUCTS\s*=\s*"""(.*?)"""',
                       src, _re.M | _re.S)
        keyed = {str(v) for v in (json.loads(m.group(1)) if m else {}).values()}
    except Exception as e:
        debug('packaging: gumroad map unavailable (%s)' % e)
    return ladder, keyed


def _docsSlug(name):
    """URL slug for a package page. Must match packageSlug() in
    website/tools/build-site.mjs and package_slug() in
    docs_seed_from_wiki.py -- the three of them agreeing is what makes
    help_url land on a page that exists."""
    return name.lower().replace('_', '-')


def LauncherSurface(comp):
    """What a consumer beyond quick-launch can do with this package.

    Returns {'surfaces': [...], 'capabilities': [...]} or {} — and {} is
    the answer for most packages, deliberately. **Having commands does
    not make a package launcher-surface capable.** Every FNS tool carries
    quick-launch commands; what a launcher's bundler needs to gather is
    the much smaller set that asks for a surface BEYOND quick-launch, or
    marks itself part of a blessed capability whose rich UI the consumer
    renders natively.

    So the predicate is: any `surface` token other than 'quick', or any
    `capability`. Derived by reflection, never declared in the catalog —
    same rule as `surfaces` and `hotkeys` (packaging/CREATING.md).

    Harvested from BOTH registration shapes, because the fleet uses one
    and the ported launcher capabilities use the other: a `FnsCommands()`
    spec list on the extension, and `@fns_command`-decorated promoted
    methods carrying `_fns_command`. Only the two fields are read; the
    full spec stays the registry's business, so this cannot drift into a
    second harvester.
    """
    if not comp.extensions:
        return {}
    ext = comp.extensions[0]
    specs = []
    try:
        fn = getattr(ext, 'FnsCommands', None)
        if callable(fn):
            specs = list(fn() or [])
    except Exception as e:
        debug('packaging: %s FnsCommands() failed (%s)' % (comp.name, e))
    if not specs:
        cls = type(ext)
        for name in dir(cls):
            if not name[:1].isupper():
                continue
            try:
                spec = getattr(getattr(cls, name), '_fns_command', None)
            except Exception:
                spec = None
            if isinstance(spec, dict):
                specs.append(spec)
    surfaces, caps = set(), set()
    for s in specs:
        if not isinstance(s, dict):
            continue
        raw = s.get('surface') or []
        if isinstance(raw, str):
            raw = [raw]
        for tok in raw:
            tok = str(tok).strip()
            if tok and tok != 'quick':
                surfaces.add(tok)
        cap = str(s.get('capability') or '').strip()
        if cap:
            caps.add(cap)
    if not surfaces and not caps:
        return {}
    return {'surfaces': sorted(surfaces), 'capabilities': sorted(caps)}


def Hotkeys(comp):
    """The package's real hotkeys, asked of FNS_HotkeyManager.

    Returns [{keys, op, par}] sorted for a stable manifest -- the keys as
    bound RIGHT NOW, never as someone remembered them. The manager owns
    discovery (which pars count, which ops are excluded); reimplementing
    that here would be a second rule to keep in step with the first.

    Deliberately no description: a HotkeyRecord carries (owner, par, val)
    and the par's label is TD's generic "Keys". Nothing in the project
    knows what a shortcut MEANS, so that sentence stays with the docs.
    """
    mgr = _root().op('FNS_HotkeyManager')
    if mgr is None or not mgr.extensions:
        return []
    try:
        records = mgr.extensions[0].Discover()
    except Exception:
        return []
    prefix = comp.path + '/'
    out = []
    for r in records:
        owner = getattr(r, 'owner', None)
        if owner is None:
            continue
        path = owner.path
        if path != comp.path and not path.startswith(prefix):
            continue
        par = str(getattr(r, 'par_name', ''))
        # A CHOP hotkey is a keys par PLUS a modifiers par; the modifiers
        # value ('ignore', 'shift'...) is not a shortcut and reads as
        # nonsense on a docs page.
        if par.lower().endswith('modifiers'):
            continue
        keys = str(getattr(r, 'val', '') or '').strip()
        if not keys:
            continue          # an unbound par documents nothing
        out.append({
            'keys': keys,
            # relative, because the absolute path is this project's
            # business and the manifest is public
            'op': path[len(comp.path) + 1:] or comp.name,
            'par': par,
        })
    # One shortcut, one row. A tool typically binds its own par AND an
    # internal keyboardin that mirrors it, which is one key to a reader.
    # Keep the shallowest op: that is the tool's own surface, and the
    # internal mirror is an implementation detail.
    best = {}
    for h in out:
        prev = best.get(h['keys'])
        if prev is None or h['op'].count('/') < prev['op'].count('/'):
            best[h['keys']] = h
    return sorted(best.values(), key=lambda h: (h['keys'], h['op']))


# What the TOOLKIT stamps on every package, as opposed to what a tool's
# author designed. Stamped controls mean the same thing everywhere, so they
# are published ONCE under the manifest's `parameter_reference` and the docs
# site renders them on one shared page instead of fifty times over.
#
# Only two things qualify, and the boundary was drawn by MEASURING rather
# than by page name:
#   REGISTRY_PAGE  -- RegistryBase.TOOL_PAGE_NAME. Wholly stamped: one
#       section per registry the tool publishes into, every section the
#       same stems behind a 2-char prefix.
#   ABOUT_PAGE, read-only pars only -- the identity stamps (Pkgversion,
#       Version, Build, Date, Touchbuild, author fields). The rest of that
#       page is NOT uniform: authors have parked real controls there
#       (Bypass, Show Built-in Parameters, ChatTD Operator, README pulses),
#       and treating the whole page as boilerplate would hide 19 working
#       controls from their own documentation.
# The host `Registration` page (RegistryBase.HOST_PAGE_NAME) is deliberately
# NOT shared: it exists only on the eight registry packages, where it IS the
# package's user surface -- what a host offers is the whole contract.
REGISTRY_PAGE = 'Registry'
ABOUT_PAGE = 'About'
# Dev-only. pre_release_common destroys this page on every component before
# a package ships, so documenting it would describe controls no user can
# ever see.
DEV_PAGES = ('Version Ctrl',)


def _plain(val):
    """JSON-safe. TD hands back its own objects for menus and colours."""
    if isinstance(val, (bool, int, float, str)):
        return val
    try:
        return str(val)
    except Exception:
        return ''


def _parDefault(par):
    try:
        return _plain(par.default)
    except Exception:
        return ''


def _parRows(page):
    """One row per TUPLET, in dialog order.

    A tuplet is what the user sees as ONE control: an RGBA swatch is four
    Pars behind a single label and a WH field is two, so listing Pars
    would document a colour picker as four sliders. `help` is taken from
    whichever member carries it -- TD shows one tooltip for the group.
    """
    rows, seen = [], set()
    pars = list(page.pars)
    for par in pars:
        tup = str(par.tupletName)
        if tup in seen:
            continue
        seen.add(tup)
        members = [p for p in pars if str(p.tupletName) == tup]
        row = {
            'name': tup,
            'label': str(par.label),
            'style': str(par.style),
            'help': next((str(p.help).strip() for p in members
                          if str(p.help or '').strip()), ''),
        }
        if len(members) > 1:
            row['size'] = len(members)
        if par.style != 'Pulse':
            row['default'] = _parDefault(par)
        if par.readOnly:
            row['readonly'] = True
        if par.startSection:
            row['section'] = True
        if par.style in ('Menu', 'StrMenu'):
            row['menu'] = [{'name': str(n), 'label': str(l)} for n, l
                           in zip(par.menuNames or [], par.menuLabels or [])]
        rows.append(row)
    return rows


def Parameters(comp):
    """The package's own customization surface, read live off the pars.

    Returns [{page, name, label, style, default, help, ...}] for what the
    tool's author designed -- the registry sections and the About page's
    identity stamps are published once for the whole toolkit (see
    SharedParameters) and DEV_PAGES never ship at all.

    The parameter's `help` IS the documentation -- not a copy of it. A
    tooltip written in TouchDesigner today is the sentence the docs page
    carries at the next build, with no prose edited anywhere. Nothing
    about a parameter is authored in catalog.json: a second place to
    write it is a second place for it to go stale, which is the same
    reasoning that killed the proposed `help` field in favour of
    _helpUrl() derivation.
    """
    out = []
    for page in comp.customPages:
        if page.name == REGISTRY_PAGE or page.name in DEV_PAGES:
            continue
        for row in _parRows(page):
            if page.name == ABOUT_PAGE and row.get('readonly'):
                continue          # identity stamp; documented once
            row['page'] = str(page.name)
            out.append(row)
    return out


def _stem(name):
    """A registry section par minus its 2-char prefix: Cfautoregister -> Autoregister."""
    return name[2:].capitalize() if len(name) > 2 else name


def _betterRegistryOwner(cand, prev):
    """FNS_ConfigHost and FNS_ConfigRegistry both answer to the 'Cf'
    prefix. A reader following "where is this section documented" wants
    the REGISTRY, not the host shell that carries a copy of it."""
    if cand in REGISTRY_OWNER:
        return prev not in REGISTRY_OWNER
    if cand.endswith('Registry'):
        return not prev.endswith('Registry')
    return False


def _registryPrefixes():
    """Section prefix -> the registry package that stamps that section.

    Read off the registries themselves (RegistryBase.TOOL_PAGE_PREFIX), so
    an eleventh registry needs no entry anywhere: it declares its prefix
    the same way the ten before it did and the docs follow.
    """
    out = {}
    for comp in _root().children:
        if comp.family != 'COMP':
            continue
        for ext in (comp.extensions or []):
            prefix = str(getattr(ext, 'TOOL_PAGE_PREFIX', '') or '')
            if not prefix:
                continue
            prev = out.get(prefix)
            if prev is None or _betterRegistryOwner(comp.name, prev):
                out[prefix] = comp.name
    return out


def RegistersWith(comp, prefixes=None):
    """Which registries this package publishes itself into.

    Taken from the section prefixes actually present on its Registry page,
    which is the same evidence the sections themselves are built from --
    so a tool cannot appear to register with something it does not.
    """
    prefixes = _registryPrefixes() if prefixes is None else prefixes
    page = next((pg for pg in comp.customPages
                 if pg.name == REGISTRY_PAGE), None)
    if page is None:
        return []
    found = {prefixes[str(par.name)[:2]] for par in page.pars
             if str(par.name)[:2] in prefixes}
    return sorted(found - {comp.name})


def RegistrySections(comps):
    """The section each REGISTRY stamps onto the tools that register with it.

    Grouped by the registry package that owns it, because that is where a
    reader looks it up: FNS_ToolbarRegistry's page explains the controls a
    toolbar registration adds, and a tool's own page just says which
    registries it joined. The alternative -- one global table of stems --
    loses the labels, which are the part that actually differs (the same
    Autoregister is "Show in Hub" on one registry and "Expose to Console"
    on another) and it puts the explanation nowhere near the thing being
    explained.

    Derived from the tools rather than from the registries, because the
    section as STAMPED is the truth; a registry's template is what it
    intends to stamp.
    """
    prefixes = _registryPrefixes()
    out = {}
    for comp in comps:
        page = next((pg for pg in comp.customPages
                     if pg.name == REGISTRY_PAGE), None)
        if page is None:
            continue
        for row in _parRows(page):
            owner = prefixes.get(row['name'][:2])
            if owner is None or row['style'] == 'Header':
                continue      # the Header names the registry, not a control
            row['name'] = _stem(row['name'])
            bucket = out.setdefault(owner, {})
            prev = bucket.get(row['name'])
            if prev is None:
                bucket[row['name']] = row
            elif row['help'] and not prev['help']:
                prev['help'] = row['help']
    return {k: list(v.values()) for k, v in sorted(out.items())}


def AboutStamps(comps):
    """The read-only identity block every package carries.

    The rest of the About page is NOT uniform -- authors have parked real
    controls there -- so only the read-only fields are pulled out; see the
    ABOUT_PAGE note above.
    """
    out = {}
    for comp in comps:
        page = next((pg for pg in comp.customPages
                     if pg.name == ABOUT_PAGE), None)
        if page is None:
            continue
        for row in _parRows(page):
            if not row.get('readonly'):
                continue
            prev = out.get(row['name'])
            if prev is None:
                out[row['name']] = row
            elif row['help'] and not prev['help']:
                prev['help'] = row['help']
    return list(out.values())


def _minTdBuild(comp):
    """The TD build this package needs, read off FNS_About.Touchbuild.

    The stamp lives ON THE COMPONENT rather than being computed here, so the
    floor travels INSIDE the .tox: an installer handed a raw artifact, with
    no manifest anywhere, can still refuse a build that cannot load it. It is
    read-only in the UI because it is a stamp, not a setting.

    Falls back to the build doing the export, which is the same answer for
    anything exported from this session and the right answer for a component
    that predates the stamp.
    """
    fa = comp.op('FNS_About')
    if fa is not None:
        p = getattr(fa.par, 'Touchbuild', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
    return app.build


def _helpUrl(comp):
    """The package's docs page: FNS_About.Helpurl, else derived from the name.

    DERIVATION IS THE NORMAL PATH, not the fallback. Measured across the
    fleet on 2026-08-26: every override tier was empty on every package --
    FNS_About.Helpurl (0 of 27), the component's own Helpurl/Url/Wikipage
    (0), a docsHelper (0). The derived URL was doing 100% of the work, so
    the ladder those tiers formed was speculative generality that had never
    once fired, and three of its four rungs are gone.

    Derivation is safe because it is gated on the page existing:
    packaging/docs/<Name>.md is the source the site is generated from, so a
    package with docs always has a working help URL with nobody entering
    one, and a package without docs gets '' rather than a 404.

    FNS_About.Helpurl stays as the ONE override, for the case derivation
    cannot serve: a page whose slug is not the package name, or docs hosted
    somewhere other than our site.
    """
    fa = comp.op('FNS_About')
    if fa is not None:
        p = getattr(fa.par, 'Helpurl', None)
        if p is not None and str(p.eval()).strip():
            return str(p.eval()).strip()
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


_REGHOST_RE = re.compile(r'/FNS_(Toolbar|Navbar|Config|OpMenu|MainMenu|PaneType|Hub)Registry(/|$)')
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
                if home and v.startswith(home):
                    shown = '~' + v[len(home):]
                else:
                    # Outside every known root. manifest.json is PUBLISHED, and
                    # this field only has to say THAT a parameter points
                    # somewhere machine-specific -- never where. Keep the
                    # filename (it names the reference) and drop the directory
                    # (it names only this disk). The pre_release hook cannot
                    # cover this: it runs on the staged copy during export,
                    # and these warnings are read off the LIVE comp before it.
                    shown = '<abs>/' + v.rsplit('/', 1)[-1]
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


def _minimumUpdater():
    """The oldest FNS_Updater Pkgversion still allowed to run, from
    release.json. '' means no floor.

    This is the KILL SWITCH. It rides in the discovery document, which is
    the one thing every install re-reads from a pinned URL, so a known-bad
    updater in the field can be stopped with a data edit and no component
    update. Raise it only when a shipped updater is actually dangerous:
    every install below the floor stops updating and says why.
    """
    path = _repo(PKG_DIR, 'release.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return str(json.load(f).get('minimum_updater', '')).strip()
        except Exception as e:
            debug('packaging: release.json minimum_updater unreadable (%s)' % e)
    return ''


def _notices():
    """Messages every install should see, from release.json. Normally []."""
    path = _repo(PKG_DIR, 'release.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                v = json.load(f).get('notices', [])
            if isinstance(v, list):
                return [str(n) for n in v if str(n).strip()]
        except Exception as e:
            debug('packaging: release.json notices unreadable (%s)' % e)
    return []


def _retired():
    """Packages this release DELIBERATELY drops, declared in release.json.

    The manifest is regenerated wholesale from whatever the live project
    holds, so a package that is simply not loaded -- or whose pi_suspect
    tracking lapsed -- vanishes from it silently, and every install stops
    being offered it. publish.py refuses that (its `removed` guard); this
    list is how a real retirement says so out loud.

    It rides into the published manifest rather than staying local: a
    client can eventually tell "retired upstream" apart from "your install
    is broken", which is exactly the distinction Compare()'s `missing`
    state cannot make today.
    """
    path = _repo(PKG_DIR, 'release.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                v = json.load(f).get('retired', [])
            if isinstance(v, list):
                return sorted({str(n).strip() for n in v if str(n).strip()})
        except Exception as e:
            debug('packaging: release.json retired list unreadable (%s)' % e)
    return []


def _presets(catalog, packages):
    """Curated preset bundles for the guided setup's welcome, validated
    against what THIS manifest actually ships.

    catalog.json may carry `presets`: [{name, blurb, packages}] -- named
    starting points the picker offers between Recommended and Everything
    (docs/InstallSurfaceDesign.md). Curation goes stale by nature (a tool
    renamed, retired, or not yet released), so an unknown name is dropped
    and REPORTED here rather than shipped -- a bundle must never put an
    uninstallable name in front of a user -- and a bundle the filter
    empties is dropped whole. Returns (bundles, problems).
    """
    known = {p['name'] for p in packages if p.get('kind') == 'tool'}
    out, problems = [], []
    for raw in catalog.get('presets', []) or []:
        if not isinstance(raw, dict):
            problems.append('preset %r: not an object' % (raw,))
            continue
        name = str(raw.get('name', '')).strip()
        pkgs = [str(n).strip() for n in (raw.get('packages') or []) if str(n).strip()]
        if not name or not pkgs:
            problems.append('preset %r: needs a name and a package list'
                            % (name or raw))
            continue
        gone = [n for n in pkgs if n not in known]
        keep = [n for n in pkgs if n in known]
        if gone:
            problems.append('preset %r: not shipped by this release: %s'
                            % (name, ', '.join(gone)))
        if keep:
            out.append({'name': name,
                        'blurb': str(raw.get('blurb', '')).strip(),
                        'packages': keep})
        else:
            problems.append('preset %r: empty after filtering -- dropped' % name)
    return out, problems

PARAMS_SCHEMA = 1
PARAMS_FILE = 'parameters.json'


def BuildParameters(out_path=None, release=None):
    """Write packaging/parameters.json -- every package's customization
    surface, with each parameter's own tooltip as its description.

    A SEPARATE document from manifest.json on purpose. The manifest is the
    rolling pointer every installed toolkit re-fetches to decide whether an
    update exists; it is uploaded, signed and cache-controlled, and it was
    54 KB before this existed. The parameter reference is ~160 KB of prose
    that no client needs in order to answer "is there a newer version" --
    putting it there would quadruple that fetch for every user, forever, to
    serve a docs build that runs from the repo anyway. So it stays in the
    repo, feeds website/tools/build-site.mjs, and is never uploaded.

    Written by Build() rather than by a step of its own: one live pass, two
    files, no way for them to disagree about which project they describe.
    """
    comps = Packages()
    prefixes = _registryPrefixes()
    doc = {
        'schema': PARAMS_SCHEMA,
        'release': release or _release(),
        'td_build': app.build,
        # what each tool's author designed, in dialog order
        'packages': {c.name: Parameters(c) for c in comps},
        # the section each registry stamps, filed under the registry that
        # owns it -- a tool's page points at these rather than repeating
        # them, so the explanation sits with the thing it explains
        'registry_sections': RegistrySections(comps),
        # Which registries put a section on THIS component's own Registry
        # page. Not the same question as `surfaces` in the manifest: a host
        # nested inside a widget (GlobalVolControl's toolbar button carries
        # its own) gives the package a toolbar button while leaving the
        # package root's Registry page empty. Measured: 5 packages differ.
        # This one answers "where are these parameters documented", which
        # is the only thing the docs page uses it for.
        'registry_pages': {c.name: RegistersWith(c, prefixes) for c in comps
                           if RegistersWith(c, prefixes)},
        # what the package gives the user, same derivation as the manifest
        'surfaces': {c.name: sorted({SURFACE_OF[h]
                                     for h in _hostedRegistries(c)
                                     if h in SURFACE_OF})
                     for c in comps},
        # the vocabulary itself, so the docs build needs no copy of it and
        # does not have to wait for a manifest rebuild to learn a new one
        'surface_meta': {sid: {'label': SURFACE_LABEL.get(sid, sid),
                               'registry': reg}
                         for reg, sid in sorted(SURFACE_OF.items())},
        # the read-only identity block, identical on every package
        'about_stamp': AboutStamps(comps),
    }
    out_path = out_path or _repo(PKG_DIR, PARAMS_FILE)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write('\n')
    return {
        'path': out_path,
        'packages': len(doc['packages']),
        'parameters': sum(len(v) for v in doc['packages'].values()),
        'registries': {k: len(v) for k, v in doc['registry_sections'].items()},
        'about_stamp': len(doc['about_stamp']),
    }


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
    tier_ladder, key_unlocks = _entitlementRoutes()

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

        # A hub tab is an FNS_HubRegistry host like any other surface
        # (SURFACE_OF -> 'hub'); the old tools_ui 'UI Tab' par sweep retired
        # with tools_ui on 2026-08-23.
        surfaces = {SURFACE_OF[h] for h in hosts if h in SURFACE_OF}

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
            # Entitlement, curated in catalog.json. `access` NAMES A TIER
            # ('free', or a tier id); it is not a flag, because the gate is
            # multi-tier. The tier -> packages map is NOT here and never
            # will be: it lives in the Worker, so there is exactly one
            # place that decides, and a client cannot be edited into
            # granting itself something.
            #
            # This field is safe to publish. It says a package is paid and
            # which tier covers it -- both of which the picker has to show
            # anyway to be honest about what the toolkit contains. What is
            # NOT here is any means of getting the bytes.
            'access': str(meta.get('access', 'free')) or 'free',
            # A Gumroad row exists for this package: a lifetime key is a
            # real second route, and every refusal should say so.
            # Projection of GUMROAD_PRODUCTS (via _entitlementRoutes).
            'key_available': comp.name in key_unlocks,
            'license': str(meta.get('license', '')),
            'seats': meta.get('seats', None),
            'integrates_with': integrations.get(name, []),
            'tox_carrier': 'root' if not comp.par.enableexternaltox.eval() else 'own',
            'cooking': bool(comp.allowCooking),
            # The TD build this artifact was exported from, and therefore the
            # floor for installing it. An OLDER TD loading a newer-build tox
            # returns nothing SILENTLY -- no exception, no error flag -- so
            # without this the failure only surfaces after the updater has
            # already destroyed the installed copy. Per package, not per
            # release: a package re-exported later has a later floor.
            'min_td_build': _minTdBuild(comp),
            # asked of the hotkey manager on every build, so a rebound key
            # reaches the docs without anyone editing prose
            'hotkeys': Hotkeys(comp),
        }

        # Only for packages that reach a consumer surface beyond
        # quick-launch (see LauncherSurface). Presence-style: absent means
        # "commands only", which is most of the fleet.
        launcher = LauncherSurface(comp)
        if launcher:
            # `seedable` is the SAFE bundling predicate, and it exists
            # because `launcher` is not one. Most launcher-capable
            # packages are gated (3 of 4 today), so a bundler gathering
            # "everything with a launcher block" would ship paid bytes
            # inside a freely downloadable app -- the same class of leak
            # as a release tox carrying a gated package into the public
            # mirror. Only a free package may be seeded into a store.
            #
            # Gated packages are not merely unseedable, they are
            # unseedABLE: a gated stock needs a download token minted by
            # the gate, so it requires the network whether or not the
            # bytes are local. Offline entitlement is a contradiction,
            # not a gap.
            # FAIL CLOSED. `access` defaults to 'free' for a package the
            # catalog does not mention, which is the right default almost
            # everywhere and exactly the wrong one here: a package whose
            # gating has not been decided yet would advertise itself as
            # safe to bundle. Verified live -- before the four ported
            # capabilities were catalogued, all four read seedable, and
            # three of them are meant to be gated. So seedable requires a
            # catalog entry that SAYS free, never the absence of one.
            launcher['seedable'] = (comp.name in curated
                                    and entry['access'] == 'free')
            entry['launcher'] = launcher
        warn = PortabilityWarnings(comp)
        if warn:
            entry['portability'] = warn

        # Save Backup of External: ON makes every parent save embed a full
        # backup of this externally-carried child, which is a leak vector
        # for gated packages (the root suspect publishes). Presence-style;
        # the public mirror's embedding guard reads it.
        try:
            if (comp.par.enableexternaltox.eval()
                    and comp.par.savebackup.eval()):
                entry['save_backup'] = True
        except Exception:
            pass

        # Where the package lands, curated in catalog.json. Absent (the
        # default) = a child of the toolkit container, update-tracked in
        # place. 'pane' = a reusable component: the installer spawns it
        # into the network the user is working in, presence is the install
        # record, and instances are frozen at their spawn version (like a
        # palette component). Stored as presence, like `recommended`.
        if str(meta.get('placement', '')) in ('pane', 'root'):
            entry['placement'] = str(meta['placement'])

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
            #
            # A gated package goes under the PLUS prefix on the SAME host.
            # Same host is load-bearing: ExtUpdater._artifactRel() derives
            # an artifact's path by stripping the manifest's base_url off
            # this URL, and re-bases everything onto the CONFIGURED base --
            # which is what makes the file:// and mirror rails work. A
            # second host would break that stripping for gated rows only,
            # which is the worst possible place for it to break.
            gated = entry.get('access', 'free') != 'free'
            prefix = ('%s/%s' % (base_url.rstrip('/'), PLUS_PREFIX)
                      if gated else base_url.rstrip('/'))
            art['url'] = '%s/%s/%s.tox' % (prefix, rel, entry['name'])

    doc = {
        'schema': MANIFEST_SCHEMA,
        'release': rel,
        'notes': ReleaseNotes(),
        'channel': _channel(),
        'base_url': base_url.rstrip('/'),
        'toolkit': {
            'name': _root().name,
            # app.build ('2025.33070'), NOT app.version -- which is the
            # version SERIES ('099') and says nothing about compatibility.
            # Every entry written before 2026-08-26 carries '099' here.
            'td_build': app.build,
            'project': project.name,
            # The funnel's routes, so every surface NAMES them instead of
            # a generic join link: where membership is bought, and the
            # tier ladder in ascending order (a package unlocks at its
            # `access` tier AND every tier above -- the labels let a
            # refusal say "unlocks at the Pro tier" instead of an id).
            # Projections: gate_package.py owns the ladder, this file's
            # SUPPORT_URL owns the door.
            'support_url': SUPPORT_URL,
            'tiers': tier_ladder,
            # The surface vocabulary: id -> the words to show and the
            # registry that documents it. Published so the picker and the
            # docs site render the same names without either one keeping
            # its own list.
            'surface_meta': {
                sid: {'label': SURFACE_LABEL.get(sid, sid), 'registry': reg}
                for reg, sid in sorted(SURFACE_OF.items())
            },
        },
        'core': [p['name'] for p in packages if p['kind'] == 'core'],
        # Deliberate retirements for this release -- see _retired(). Empty
        # is the normal case; publish.py compares it against what actually
        # disappeared between the last staged manifest and this one.
        'retired': _retired(),
        # Field-reach controls. They live here so publish.py can build the
        # discovery document from the manifest alone, but they belong to
        # the DISCOVERY document, not to the manifest -- a client that can
        # already read the manifest has, by definition, resolved an
        # endpoint and does not need them.
        'minimum_updater': _minimumUpdater(),
        'notices': _notices(),
        'categories': catalog.get('categories', []),
        # Presentation per category -- the glyph and the one-line pitch the
        # CMS curates beside the category list. Packaging does not read it;
        # it rides along so the configurator can head its sections the same
        # way the website does, including when the picker is served from
        # inside TouchDesigner with no site to fetch it from.
        'category_meta': catalog.get('category_meta', {}),
        # The picker's Recommended preset: every TOOL whose catalog entry
        # carries `recommended: true` (the CMS checkbox), in manifest
        # order. The page hides the preset when the list is empty or the
        # manifest predates it.
        'starter': [p['name'] for p in packages
                    if p['kind'] == 'tool'
                    and curated.get(p['name'], {}).get('recommended')],
        'packages': packages,
    }
    # Curated bundles for the guided setup (catalog `presets`, validated
    # against this very package list). Emitted only when curation exists,
    # so older manifests and an unauthored catalog stay byte-identical.
    preset_bundles, preset_problems = _presets(catalog, packages)
    if preset_bundles:
        doc['presets'] = preset_bundles
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write('\n')

    # Same run, second file: the parameter reference is derived from the
    # same live pass, so the two can never describe different projects.
    BuildParameters(release=rel)

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
            'preset_problems': preset_problems,
            'uncategorized': [p['name'] for p in packages
                              if p['category'] == 'Uncategorized']}
