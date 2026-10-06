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
    # The eleventh: contributed controls in each pane's find bar
    # (docs/PaneSearchRegistry.md).
    'FNS_PaneSearchRegistry': 'FNS_PaneSearchRegistry',
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
    'FNS_PaneSearchRegistry': 'findbar',
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
    'findbar': 'Find bar control',
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
        'FNS_Console', 'FNS_HubRegistry', 'FNS_Hub', 'FNS_Updater',
        # The registries added after this list was first written. The
        # catalog filed them under Core from the start, and a registry is
        # core by the definition above; left out of this tuple they were
        # kind 'tool' with category 'Core', which the picker never renders
        # (it draws Core by kind and skips the Core category), so they
        # installed only ever as somebody's dependency (2026-09-11).
        'FNS_CommandRegistry', 'FNS_PaletteRegistry', 'FNS_TimelineRegistry',
        'FNS_PaneSearchRegistry')


def _root():
    return op(TOOLKIT)


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


# Dev-root residents that are RAILS, not packages: they ship inside the
# bootstrap (build_installer.BOOTSTRAP_KEEP) and are published under the
# manifest's `rails`, never as installable packages -- even when Private
# Investigator tracks them like every other dev-root component.
RAILS = ('FNS_Installer', 'webBrowser')

# ---------------------------------------------------------------------------
# Curated link fields and FOREIGN packages (docs/ForeignPackages.md)
#
# A foreign package is one whose bytes and version are owned UPSTREAM --
# another repo, another release rail (TDXMap first). It is declared, not
# discovered: a catalog entry with a `source` block. `foreign_sync.py`
# mirrors the upstream artifact into packaging/dist/ and records what it
# fetched in packaging/foreign.lock.json; Build() reads ONLY the lock (no
# network on TD's main thread) and emits a manifest row that every consumer
# treats as an ordinary tool -- same `kind`, same store, same installer --
# plus `foreign: true` so the release rail knows there is no live COMP to
# bump, export or PI-save, and `updates` so the updater knows whether the
# tool keeps itself current after install.
#
# This is NOT the recommendations lane (packaging/recommendations.json):
# a recommendation is a LINK to someone else's page, never hosted, never
# versioned, refused from the manifest by its validator. A foreign package
# is hosted (mirrored bytes in our bucket, pinned by sha) and versioned
# (from the upstream manifest the sync polls). The line between them is
# whether we poll a source and keep a copy current.
# ---------------------------------------------------------------------------

FOREIGN_LOCK = 'foreign.lock.json'
# Curated on ANY package: presentation facts a machine cannot know.
CURATED_LINK_KEYS = ('author', 'homepage', 'changelog_url')
# Curated ONLY on a foreign entry -- on a live package each of these has a
# live authority (FNS_About.Helpurl, the export build) that must not fork.
FOREIGN_ONLY_KEYS = ('source', 'updates', 'help_url', 'min_td_build')
# One operator type as the op-menu registry keys it: `moviefileinTOP`.
ALT_TYPE_RE = re.compile(r'^[a-z0-9_]+(TOP|CHOP|SOP|DAT|MAT|COMP|POP)$')
# a variant id is a word (pro), never a tier number: those are Patreon's
VARIANT_ID_RE = re.compile(r'^[a-z][a-z0-9]*$')
UPDATES_MODES = ('self', 'store')


def _authorMeta(meta):
    """`author: {name, url}` normalised, or None when absent/empty."""
    a = meta.get('author')
    if isinstance(a, str):
        a = {'name': a}
    if not isinstance(a, dict):
        return None
    name = str(a.get('name', '')).strip()
    url = str(a.get('url', '')).strip()
    if not name:
        return None
    out = {'name': name}
    if url:
        out['url'] = url
    return out


def CuratedLinks(meta):
    """The link fields a catalog entry may carry onto its manifest row.
    Presence-style: absent stays absent, so an unauthored catalog row
    keeps the manifest byte-identical."""
    out = {}
    a = _authorMeta(meta)
    if a:
        out['author'] = a
    for k in ('homepage', 'changelog_url'):
        v = str(meta.get(k, '') or '').strip()
        if v:
            out[k] = v
    return out


def IsForeign(meta):
    return isinstance(meta, dict) and isinstance(meta.get('source'), dict)


def CuratedAlternatives(meta):
    """The catalog's `alternatives_for` as a sorted list of operator types.
    Accepts a list or one space-separated string (what the CMS input
    holds); malformed tokens are dropped here and reported by
    CatalogProblems."""
    raw = meta.get('alternatives_for') if isinstance(meta, dict) else None
    if isinstance(raw, str):
        raw = raw.replace(',', ' ').split()
    if not isinstance(raw, (list, tuple)):
        return []
    return sorted({str(x).strip() for x in raw
                   if str(x).strip() and ALT_TYPE_RE.match(str(x).strip())})


def OpMenuHostedNames():
    """Names of the live packages that carry an FNS_OpMenuRegistry host --
    the ones whose alternatives_for is DERIVED, so a curated list on them
    is a second source of truth. TD-only (walks the live project)."""
    try:
        return {c.name for c in Packages() if c.op('FNS_OpMenuRegistry') is not None}
    except Exception:
        return set()


# An FNS operator family member (docs/OperatorFamilyFromStore.md): the
# tool carries TDFam's own FamManifest/OpInfo, and the manifest's `family`
# block is DERIVED from it at build; a foreign or hostless entry may curate
# the same block in the catalog. The updater mirrors every member the store
# holds into the family's operator folder with a sidecar built from this
# block, so the FNS tab in the OP Create dialog lists it.
# lowercase: TDFam keys its folder cache by the lowercased type and a stub
# replace or an update looks the manifest's op_type up VERBATIM, so a type
# with capitals places fine and can never come back from a stub. op_name
# carries the readable spelling (it names the placed operator).
FAMILY_TYPE_RE = re.compile(r'^[a-z][a-z0-9_]*$')
FAMILY_NAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
FAMILY_GROUPS = ('COMP', 'TOP', 'CHOP', 'SOP', 'MAT', 'DAT', 'POP')
FAMILY_LIST_KEYS = ('compatible_types', 'search_words')
FAMILY_DICT_KEYS = (('par_retain', 'ParRetain'), ('state_retain', 'StateRetain'),
                    ('shortcuts', 'Shortcuts'))


def _familyBlock(opinfo, retain=None):
    """Normalise one OpInfo dict (plus optional retain dicts keyed by our
    manifest names) into the manifest's `family` block. Empty when there is
    no usable op_type: a block without a type names nothing."""
    if not isinstance(opinfo, dict):
        return {}
    op_type = str(opinfo.get('op_type', '') or '').strip()
    if not FAMILY_TYPE_RE.match(op_type):
        return {}
    out = {'op_type': op_type}
    op_name = str(opinfo.get('op_name', '') or '').strip()
    if FAMILY_NAME_RE.match(op_name) and op_name != op_type:
        out['op_name'] = op_name
    for k in ('op_label', 'op_group', 'summary'):
        v = str(opinfo.get(k, '') or '').strip()
        if v:
            out[k] = v
    out['is_filter'] = bool(opinfo.get('isFilter', opinfo.get('is_filter', False)))
    for k in FAMILY_LIST_KEYS:
        raw = opinfo.get(k)
        if isinstance(raw, str):
            raw = raw.replace(',', ' ').split()
        if isinstance(raw, (list, tuple)):
            vals = [str(x).strip() for x in raw if str(x).strip()]
            if vals:
                out[k] = vals
    for k, v in (retain or {}).items():
        if isinstance(v, dict) and v:
            out[k] = v
    return out


def CuratedFamily(meta):
    """The catalog's `family` block, normalised -- for a foreign package,
    or a live one that carries no FamManifest. {} when absent or unusable;
    CatalogProblems reports the unusable case."""
    raw = meta.get('family') if isinstance(meta, dict) else None
    if not isinstance(raw, dict):
        return {}
    retain = {k: raw.get(k) for k, _ in FAMILY_DICT_KEYS if isinstance(raw.get(k), dict)}
    return _familyBlock(raw, retain)


def FamilyFor(comp):
    """The `family` block DERIVED from a live package's FamManifest (TDFam's
    manifest base: OpInfo plus ParRetain / StateRetain / Shortcuts DATs of
    JSON). {} when the package carries none, or its OpInfo does not parse:
    a member whose manifest is broken drops off the tab, never the build."""
    fm = comp.op('FamManifest')
    if fm is None:
        return {}
    info = fm.op('OpInfo')
    if info is None:
        return {}
    try:
        opinfo = json.loads(info.text or '{}')
    except Exception as e:
        debug('packaging: %s FamManifest/OpInfo is not JSON (%s)' % (comp.name, e))
        return {}
    retain = {}
    for key, dat_name in FAMILY_DICT_KEYS:
        d = fm.op(dat_name)
        if d is None:
            continue
        try:
            v = json.loads(d.text or '{}')
        except Exception as e:
            debug('packaging: %s FamManifest/%s is not JSON (%s)' % (comp.name, dat_name, e))
            continue
        if isinstance(v, dict) and v:
            retain[key] = v
    return _familyBlock(opinfo, retain)


def FamilyProblems(comp):
    """Why a live member's FamManifest cannot ship, as sentences. Empty is
    the normal answer, and so is a package with no FamManifest. A member
    that fails here would drop off the FNS tab (no usable op_type) or place
    and then never come back from a stub or an update (a type with
    capitals), so preflight blocks on it."""
    fm = comp.op('FamManifest')
    if fm is None:
        return []
    info = fm.op('OpInfo')
    if info is None:
        return ['%s: FamManifest has no OpInfo DAT' % comp.name]
    try:
        opinfo = json.loads(info.text or '{}')
    except Exception as e:
        return ['%s: FamManifest/OpInfo is not JSON (%s)' % (comp.name, e)]
    out = []
    ot = str((opinfo or {}).get('op_type', '') or '').strip()
    if not FAMILY_TYPE_RE.match(ot):
        out.append('%s: FamManifest op_type %r must be a lowercase word (TDFam '
                   'looks it up verbatim in a lowercased cache; op_name holds the '
                   'readable spelling)' % (comp.name, ot))
    og = str((opinfo or {}).get('op_group', '') or '').strip()
    if og and og not in FAMILY_GROUPS:
        out.append('%s: FamManifest op_group %r is not an operator family (%s)'
                   % (comp.name, og, ', '.join(FAMILY_GROUPS)))
    for _, dat_name in FAMILY_DICT_KEYS:
        d = fm.op(dat_name)
        if d is None:
            continue
        try:
            json.loads(d.text or '{}')
        except Exception as e:
            out.append('%s: FamManifest/%s is not JSON (%s)' % (comp.name, dat_name, e))
    return out


def FamilyHostedNames():
    """Names of the live packages that carry a FamManifest -- the ones whose
    `family` block is DERIVED, so a curated block on them is a second
    source of truth. TD-only (walks the live project)."""
    try:
        return {c.name for c in Packages() if c.op('FamManifest') is not None}
    except Exception:
        return set()


def ForeignEntries(catalog):
    """name -> catalog entry, for every entry that declares a `source`."""
    return {n: m for n, m in (catalog.get('packages') or {}).items()
            if IsForeign(m)}


def ForeignLock(path=None):
    """What foreign_sync.py last fetched: name -> {version, sha256, url,
    notes_url, fetched_at}. Missing file = empty."""
    path = path or _repo(PKG_DIR, FOREIGN_LOCK)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
    except Exception:
        return {}
    return doc.get('packages', doc) if isinstance(doc, dict) else {}


def CatalogProblems(catalog, live_names, opmenu_hosted=None, family_hosted=None):
    """Authority rules the catalog must obey, as human sentences. Empty is
    the normal answer. Preflight blocks on these; Build() tolerates them
    (it drops the offending keys) so a broken catalog cannot brick the
    manifest build the CMS needs to SHOW the problem.

    `opmenu_hosted`: names of live packages carrying an op-menu host
    (OpMenuHostedNames()); None when the caller cannot tell (outside TD),
    in which case the derived-vs-curated collision is not checked.
    `family_hosted`: the same for packages carrying a FamManifest
    (FamilyHostedNames()); the `family` block on those is derived."""
    problems = []
    live = set(live_names or ())
    hosted = set(opmenu_hosted) if opmenu_hosted is not None else None
    fam_hosted = set(family_hosted) if family_hosted is not None else None
    for name, meta in sorted((catalog.get('packages') or {}).items()):
        if not isinstance(meta, dict):
            continue
        foreign = IsForeign(meta)
        raw_alts = meta.get('alternatives_for')
        if raw_alts not in (None, [], ''):
            tokens = (raw_alts.replace(',', ' ').split() if isinstance(raw_alts, str)
                      else list(raw_alts))
            bad_tokens = [str(t) for t in tokens if not ALT_TYPE_RE.match(str(t).strip())]
            if bad_tokens:
                problems.append('%s: alternatives_for holds %s -- an operator type '
                                'reads like moviefileinTOP or noiseCHOP'
                                % (name, ', '.join(bad_tokens)))
            if not foreign and hosted is not None and name in hosted:
                problems.append('%s: alternatives_for is curated but the live package '
                                'carries an FNS_OpMenuRegistry host, which derives it '
                                'from onAlternatives() -- drop the curated list'
                                % name)
        # `nopick` (explicit-pick only) is presence-style: true or absent.
        # A false or a string would read as set to one consumer and unset
        # to another, so only the boolean is accepted. It cannot also be
        # Recommended: the starter set is a bulk selection by definition.
        if 'nopick' in meta:
            if meta['nopick'] is not True:
                problems.append('%s: nopick must be true or absent, not %r'
                                % (name, meta['nopick']))
            elif meta.get('recommended'):
                problems.append('%s: a nopick package cannot be recommended -- '
                                'the Recommended set is a bulk selection' % name)
        # `placeonce` (docs/PlaceOnce.md) is presence-style too. It gives the
        # picker card a Place action beside the tick: placed tools join THIS
        # project only and never ride "Set up like last time" into the next.
        if 'placeonce' in meta and meta['placeonce'] is not True:
            problems.append('%s: placeonce must be true or absent, not %r'
                            % (name, meta['placeonce']))
        # `preview` (docs/PreviewPackages.md): shipped for the owner's testing,
        # hidden from everyone else. Presence-style. It OVERRIDES Recommended
        # (owner, 2026-09-25): the flag is kept for the release, and the
        # starter set leaves a preview out while it is one.
        if 'preview' in meta and meta['preview'] is not True:
            problems.append('%s: preview must be true or absent, not %r'
                            % (name, meta['preview']))
        raw_companion = meta.get('companion')
        if raw_companion not in (None, '') and raw_companion != 'family':
            problems.append('%s: companion %r is not known (the one kind is "family")'
                            % (name, raw_companion))
        if raw_companion == 'family' and meta.get('family'):
            problems.append('%s: a family companion cannot itself be a family member' % name)
        raw_family = meta.get('family')
        if raw_family not in (None, {}):
            if not isinstance(raw_family, dict):
                problems.append('%s: family must be an object (op_type, op_label, '
                                'op_group, ...)' % name)
            else:
                ot = str(raw_family.get('op_type', '') or '').strip()
                if not FAMILY_TYPE_RE.match(ot):
                    problems.append('%s: family.op_type %r must be a lowercase word '
                                    'like scenechanger (op_name holds the readable '
                                    'spelling)' % (name, ot))
                og = str(raw_family.get('op_group', '') or '').strip()
                if og and og not in FAMILY_GROUPS:
                    problems.append('%s: family.op_group %r is not an operator family '
                                    '(%s)' % (name, og, ', '.join(FAMILY_GROUPS)))
                if not foreign and fam_hosted is not None and name in fam_hosted:
                    problems.append('%s: family is curated but the live package carries '
                                    'a FamManifest, which derives it -- drop the curated '
                                    'block' % name)
            if str(meta.get('placement', '')) == 'root':
                problems.append('%s: a family member is placed into the working network '
                                '(placement pane), never at the root' % name)
        raw_variants = meta.get('variants')
        if raw_variants not in (None, {}):
            if not isinstance(raw_variants, dict):
                problems.append('%s: variants must be an object of id -> block' % name)
            else:
                for vid, block in raw_variants.items():
                    if not VARIANT_ID_RE.match(str(vid)):
                        problems.append('%s: variant id %r must be a lowercase word '
                                        'such as pro -- tier numbers are Patreon\'s'
                                        % (name, vid))
                    if not isinstance(block, dict):
                        problems.append('%s: variant %s must be an object' % (name, vid))
                        continue
                    if not str(block.get('access', '') or '').isdigit():
                        problems.append('%s: variant %s needs a numeric Patreon tier id '
                                        'in access (gate_package.py --variant %s --tier)'
                                        % (name, vid, vid))
                    src = str(block.get('source', '') or '').strip()
                    if src and src in (catalog.get('packages') or {}):
                        problems.append('%s: variant %s names %s as its source, but that '
                                        'is a catalog package of its own' % (name, vid, src))
                    wh = block.get('withhold')
                    if wh is not None and not (isinstance(wh, list)
                                               and all(isinstance(x, str) for x in wh)):
                        problems.append('%s: variant %s withhold must be a list of file '
                                        'names' % (name, vid))
        if foreign and name in live:
            problems.append('%s: declares a `source` but is also a live '
                            'package in this project -- a package is ours '
                            'or upstream\'s, never both' % name)
        if not foreign:
            bad = [k for k in FOREIGN_ONLY_KEYS if k in meta]
            if bad:
                problems.append('%s: %s only belong on a foreign entry '
                                '(the live package already owns them: '
                                'FNS_About.Helpurl, the export build)'
                                % (name, ', '.join(bad)))
            continue
        src = meta['source']
        if not str(src.get('manifest', '') or '').strip():
            problems.append('%s: source needs a `manifest` URL' % name)
        tox = str(src.get('tox', '') or '').strip()
        if tox and not tox.lower().endswith('.tox'):
            problems.append('%s: source.tox must name a .tox file' % name)
        mode = str(meta.get('updates', 'store') or 'store')
        if mode not in UPDATES_MODES:
            problems.append('%s: updates must be one of %s'
                            % (name, ', '.join(UPDATES_MODES)))
        if 'author' in meta and _authorMeta(meta) is None:
            problems.append('%s: author needs at least a name' % name)
    return problems


def ForeignPackages(catalog, lock=None, dist_dir=None, previous=None):
    """Manifest rows for every foreign catalog entry.

    Returns (rows, problems). A row carries what a consumer needs and
    nothing it cannot have: no surfaces, hotkeys, requires or op count
    (nothing to reflect over), `tox_carrier` 'own', and an `artifact`
    ONLY when the mirrored tox in dist/ matches the lock's sha -- a row
    without one makes Stage() refuse, the same as a failed export. The
    version is the lock's (the upstream's), never read from anywhere
    live.
    """
    lock = ForeignLock() if lock is None else lock
    dist_dir = dist_dir or _repo(DIST_DIR)
    previous = previous or {}
    rows, problems = [], []
    for name, meta in sorted(ForeignEntries(catalog).items(),
                             key=lambda kv: kv[0].lower()):
        rec = lock.get(name) or {}
        version = str(rec.get('version', '') or '').strip()
        if not version:
            problems.append('%s: not synced -- run foreign_sync.py '
                            '(no lock entry)' % name)
        mode = str(meta.get('updates', 'store') or 'store')
        if mode not in UPDATES_MODES:
            mode = 'store'
        entry = {
            'name': name,
            'title': str(meta.get('title', '') or PublicName(name)),
            'kind': 'tool',
            'foreign': True,
            'category': meta.get('category', 'Uncategorized'),
            'description': meta.get('description', ''),
            'version': version,
            'help_url': str(meta.get('help_url', '') or '').strip(),
            'surfaces': [],
            'shortcut': '',
            'ops': 0,
            'requires': [],
            'access': EffectiveAccess(meta),
            'key_available': False,
            'license': str(meta.get('license', '')),
            'seats': meta.get('seats', None),
            'integrates_with': [],
            'tox_carrier': 'own',
            'cooking': True,
            'min_td_build': str(meta.get('min_td_build', '') or '').strip(),
            'hotkeys': [],
            'updates': mode,
            # what the upstream's own manifest says about this version;
            # the CMS and picker show it as the release note
            'whatsnew': str(rec.get('notes', '') or ''),
            'upstream': {
                'manifest': str(meta['source'].get('manifest', '') or ''),
                'url': str(rec.get('url', '') or ''),
                'fetched_at': rec.get('fetched_at', 0),
            },
        }
        if str(meta.get('placement', '')) in ('pane', 'root', 'none'):
            entry['placement'] = str(meta['placement'])
        # A priced family product (catalog `pricing`): not gated by the
        # toolkit's tiers, so `access` stays free and it installs for
        # everyone, but not free either -- the picker, the site and the
        # counts must not call it that. Copy only, no derivation.
        pricing = meta.get('pricing')
        if isinstance(pricing, dict) and str(pricing.get('summary', '') or '').strip():
            entry['pricing'] = {k: str(pricing.get(k, '') or '').strip()
                                for k in ('summary', 'detail', 'url')}
        if meta.get('minor'):
            entry['minor'] = True
        # explicit-pick only; see the live projection for the reasoning
        if meta.get('nopick') is True:
            entry['nopick'] = True
        # placeable without joining the setup; see the live projection
        if meta.get('placeonce') is True:
            entry['placeonce'] = True
        # not released yet; see the live projection
        if meta.get('preview') is True:
            entry['preview'] = True
        # a foreign package has nothing to reflect, so this one is curated
        curated_alts = CuratedAlternatives(meta)
        if curated_alts:
            entry['alternatives_for'] = curated_alts
        # an FNS family member: curated here (nothing live to reflect); a
        # member is placed into the working network by definition
        curated_family = CuratedFamily(meta)
        if curated_family:
            entry['family'] = curated_family
            # A family member is NOT placed: it is reached from the FNS tab of
            # the OP Create dialog and from the family folder on disk, which is
            # the whole reason it ships as a family member. Spawning a copy into
            # the user's network at install was never wanted (owner 2026-09-18).
            # This read setdefault('placement', 'pane') until then.
            entry.setdefault('placement', 'none')
        links = CuratedLinks(meta)
        # the upstream's release notes URL is the default changelog link
        if 'changelog_url' not in links and rec.get('notes_url'):
            links['changelog_url'] = str(rec['notes_url'])
        entry.update(links)
        built = os.path.join(dist_dir, name + '.tox')
        want = str(rec.get('sha256', '') or '')
        if os.path.exists(built):
            have = _sha256(built)
            if want and have != want:
                problems.append('%s: packaging/dist/%s.tox does not match '
                                'the lock (re-run foreign_sync.py)'
                                % (name, name))
            else:
                entry['artifact'] = {
                    'path': DIST_DIR + '/' + name + '.tox',
                    'bytes': os.path.getsize(built),
                    'sha256': have,
                }
        elif version:
            problems.append('%s: lock says v%s but packaging/dist/%s.tox is '
                            'missing -- run foreign_sync.py'
                            % (name, version, name))
        rows.append(entry)
    return rows, problems


def AlternativesFor(comp):
    """Operator types this package offers itself (or its library) for, read
    off its FNS_OpMenuRegistry host's callbacks DAT by calling
    onAlternatives() -- the same reflection that derives `surfaces` from
    hosts. Sorted; empty when the package publishes none. A callback that
    raises at build time costs that package its list, never the build:
    the registry applies the same isolation at runtime."""
    host = comp.op('FNS_OpMenuRegistry')
    if host is None:
        return []
    cb = getattr(host.par, 'Callback', None)
    dat = cb.eval() if cb is not None else None
    if dat is None or not getattr(dat, 'isDAT', False):
        return []
    try:
        # onShippedAlternatives, when a tool defines it, names what ships in
        # the tox; onAlternatives reads the ACTIVE set, which on a dev machine
        # can be a personal palette or project library (OpTemplates).
        # The callbacks template ships onShippedAlternatives as a stub that
        # returns None ("optional"), so a None from it means "not overridden"
        # and onAlternatives() is the answer; only a dict from it wins.
        # (ThresholdColor derived [] until the stub was deleted, 2026-09-23.)
        out = None
        fn = getattr(dat.module, 'onShippedAlternatives', None)
        if callable(fn):
            out = fn()
        if out is None:
            fn = getattr(dat.module, 'onAlternatives', None)
            if not callable(fn):
                return []
            out = fn() or {}
        # A key names one type, or several separated by spaces (a list or
        # tuple of names works too): the registry splits it the same way, so
        # 'tileTOP mirrorTOP' is two operator types here, never one string
        # (PrismTOP, 2026-09-23).
        types = set()
        for k in out.keys():
            if not out.get(k):
                continue
            names = list(k) if isinstance(k, (list, tuple)) else str(k).split()
            for n in names:
                n = str(n).strip()
                if n:
                    types.add(n)
        return sorted(types)
    except Exception as e:
        debug('packaging: %s onAlternatives() failed at build (%s)' % (comp.name, e))
        return []


def _catalogPackages():
    path = _repo(PKG_DIR, 'catalog.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('packages', {}) or {}
    except Exception:
        return {}


def Variants(meta):
    """{vid: block} from a catalog entry's `variants` -- one build per tier
    above the entry tier (docs/TierVariants.md). A block names its own
    `access`, optionally a `source` master (a second live COMP) or, absent
    that, the package's own master exported under the variant's file name
    so its pre_release hook builds that edition; `withhold` lists source
    files only that build may publish; `summary` is picker copy."""
    v = (meta or {}).get('variants')
    if not isinstance(v, dict):
        return {}
    return {str(k): b for k, b in v.items() if isinstance(b, dict)}


def VariantSources(catalog_packages=None):
    """Master COMP names that build a VARIANT of another package. They are
    live depth-1 suspects like any package, and must never be listed as
    packages of their own (no manifest row, no catalog entry, no doc)."""
    pk = catalog_packages if catalog_packages is not None else _catalogPackages()
    out = set()
    for name, meta in pk.items():
        for vid, block in Variants(meta).items():
            src = str(block.get('source', '') or '').strip()
            if src:
                out.add(src)
    return out


def VariantSourceComps():
    """The live COMPs behind VariantSources(), in name order."""
    root = _root()
    out = []
    for n in sorted(VariantSources()):
        c = root.op(n)
        if c is not None:
            out.append(c)
    return out


def Packages():
    """Shippable packages = depth-1 COMPs that are tracked suspects with
    their own tox. That is already the project's own unit of distribution,
    so nothing new has to be invented or maintained by hand."""
    out = []
    sources = VariantSources()
    for c in _root().children:
        if c.family != 'COMP' or c.name in RAILS:
            continue
        if c.name in sources:
            continue      # a variant master ships INSIDE another package's row
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


# A preview package (catalog `preview: true`, docs/PreviewPackages.md) ships
# in the release for the owner to test in production, gated to a pseudo tier
# no Patreon membership can carry: the Worker grants PREVIEW_TIER to the
# creator account alone. The catalog's own `access` keeps the tier it will
# ship at, untouched while it waits.
PREVIEW_TIER = 'preview'


def EffectiveAccess(meta):
    """The access a package ships with: PREVIEW_TIER while it is a preview,
    else its catalog access (absent = free)."""
    if (meta or {}).get('preview') is True:
        return PREVIEW_TIER
    return str((meta or {}).get('access', 'free')) or 'free'


def PublicName(name):
    """The name a user reads: the package name with a leading FNS_ removed.

    The prefix is an operator-name convention. It groups the toolkit in a
    network and keeps a dropped COMP from colliding with a user's own
    `Console`, and it earns none of that in a LIST: sorted by name, every
    FNS package collapses under "F" and the letter that tells them apart
    is the fifth character. So the manifest carries both -- `name` is the
    identity (the .tox file name, the install record, the Worker's
    entitlement map) and `title` is what every picker and page prints.

    A curated `title` in catalog.json wins, for the case derivation
    cannot serve. See docs/PublicToolNames.md.
    """
    return name[4:] if name.startswith('FNS_') else name


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


# What is not a shortcut on its own.
#
# Same vocabulary as FNS_HotkeyManager.ignored_keys, which the manager
# applies ONLY to a Keyboard In DAT's `keys` par -- and rightly so: a COMP
# par named `Keys` holding `alt` is a real, rebindable row in its UI. It
# just is not a shortcut anyone can be told to press, so it must not reach
# a docs page.
#
# The two sets are NOT interchangeable, which is the trap. `esc`, `enter`
# and `tab` are KEYS: bare, they are a listen list ("fire on any of these"),
# but as part of a combo they are the key being bound -- SwitchOPs is
# `ctrl.tab` and folding tab in with the modifiers deleted it.
MODIFIERS = frozenset(('ctrl', 'alt', 'shift', 'cmd',
                       'lctrl', 'rctrl', 'lalt', 'ralt',
                       'lshift', 'rshift', 'lcmd', 'rcmd'))
BARE_LISTEN_KEYS = frozenset(('esc', 'enter', 'tab'))


def _looksLikeKeys(value):
    """False for a value that is not a key combo at all.

    Discovery is by NAME (`*key*`, `*shortcut*`, `*hotkey*` on a Str par),
    so a Str par that merely stores data about keys is found too:
    FNS_CommandPalette's `Favouritekeys` holds a JSON list of starred
    command ids and reached the manifest as the shortcut `[]`, which the
    docs then set in a <kbd>. A combo has at least one letter or digit and
    never starts like JSON.
    """
    v = str(value).strip()
    if not v or v[0] in '[{':
        return False
    return any(ch.isalnum() for ch in v)


def _isModifierOnly(value):
    """True when every combo in `value` is a modifier-LISTEN setup ("hold
    Alt while you drop an operator") rather than a binding.

    Five packages carry one: AutoCombine, AutoRes, SetSmoothness,
    OpTemplates and QuickPane -- the last of which ALSO has a real binding,
    so the test is per-combo, never per-parameter.
    """
    combos = [c for c in str(value).split() if c]
    if not combos:
        return True
    for combo in combos:
        parts = [p.lower() for p in combo.replace('+', '.').split('.') if p]
        if not parts:
            continue
        if all(p in MODIFIERS for p in parts):
            continue                        # ctrl / alt.shift -- listen
        if len(parts) == 1 and parts[0] in BARE_LISTEN_KEYS:
            continue                        # a bare esc/enter/tab list
        return False                        # a real key is in there
    return True


def Hotkeys(comp):
    """The package's real hotkeys, asked of FNS_HotkeyManager.

    Returns [{keys, op, par}] sorted for a stable manifest -- the keys as
    bound RIGHT NOW, never as someone remembered them. The manager owns
    discovery (which pars count, which ops are excluded); reimplementing
    that here would be a second rule to keep in step with the first. It
    also owns EVALUATION: see the note on `.current` below, which is what
    makes "right now" true for an expression-driven binding.

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
        # `.current` -- the record's EVALUATED value -- not `.val`, which
        # the manager documents as "constant/bind value ('' when
        # expression-driven)". Five packages bind their shortcut through
        # the OS-switch expression the conformance contract asks for
        # (`'ctrl.e' if app.osName == 'Windows' else 'cmd.e'`), so `.val`
        # was empty for every one of them and the `if not keys` below
        # dropped it: OpenExt, SwitchOPs, OpToClipboard, TDX_SearchPalette
        # and VSCodeTools shipped with no Shortcuts section at all, while
        # their docs correctly described a key you could press. Reading
        # `.val` also silently reported the WINDOWS half only, had it been
        # populated -- `.current` is what the binding actually is on the
        # machine the build runs on.
        keys = str(getattr(r, 'current', '') or getattr(r, 'val', '') or '').strip()
        if not keys:
            continue          # an unbound par documents nothing
        if _isModifierOnly(keys):
            continue          # "hold Alt", not a shortcut you can press
        if not _looksLikeKeys(keys):
            continue          # a Str par NAMED like a binding, holding data
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
# The identity fields the toolkit stamps on an About page, by NAME. Not all
# of them are read-only: the Author / Link / Package Version trio stamped by
# every adoption is editable, and so is FNS_About's Authorname / Openauthor
# pair, so the read-only test alone let them into every package's own
# reference as undocumented rows (iopBrowser's whole list was "Link",
# 2026-09-24). A control an author parked on the page under another name is
# still that tool's own.
ABOUT_STAMPS = frozenset((
    'Author', 'Authorname', 'Authorurl', 'Link', 'Openauthor', 'Pkgversion',
    'Pkgvariant', 'Helpurl', 'Openhelp', 'Version', 'Build', 'Date',
    'Touchbuild',
))


def _isAboutStamp(row):
    return bool(row.get('readonly')) or row.get('name') in ABOUT_STAMPS
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
            if page.name == ABOUT_PAGE and _isAboutStamp(row):
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


# Chrome that lives INSIDE a widget but is not the widget's icon: TD's own
# pop-menu furniture (the tick, the submenu caret) and the lister config
# strip draw from the same icon font, so every tool carrying a pop-menu
# would otherwise "have" the same checkbox glyph -- measured: 4 packages
# reported the identical check/subMenu set. Matched against the path
# RELATIVE to the widget, so a tool whose own button is named `config`
# is untouched.
ICON_CHROME = ('popmenu', 'popdialog', 'config/', 'configdefault',
               'expando', 'lister', 'keymodifiers')
# The faces a glyph icon is drawn in. A Text COMP in Verdana is a label.
ICON_FONTS = ('material design icons', 'material icons')


def _iconEvidence(widget):
    """What a registered widget actually draws as its icon.

    Read off the live widget rather than authored anywhere: an FNS bar
    button is a Text COMP whose `font` is the Material Design Icons face
    and whose `text` is a single private-use codepoint. That is the icon a
    user sees -- until this existed the docs site showed a hand-typed
    `icon: SwapOPs.png` from the wiki era instead, a different picture from
    the button it claimed to describe.

    The SHALLOWEST match wins: a bar button keeps its glyph at
    `<widget>/text`, and anything deeper is furniture (see ICON_CHROME).
    Returns None when a widget draws no glyph, which is a real answer --
    sliders, panels and whole-COMP tabs have none.
    """
    if widget is None:
        return None
    best = None
    for k in widget.findChildren(maxDepth=3):
        font = getattr(k.par, 'font', None)
        text = getattr(k.par, 'text', None)
        if font is None or text is None:
            continue
        rel = k.path[len(widget.path) + 1:] or k.name
        probe = (rel + '/').lower()
        if any(c in probe for c in ICON_CHROME):
            continue
        face = str(font.eval() or '')
        if face.lower() not in ICON_FONTS:
            continue
        val = str(text.eval() or '')
        # Exactly one character. Two would be a word set in the icon font,
        # which is not an icon; zero is an empty slot.
        if len(val) != 1:
            continue
        depth = rel.count('/')
        if best is None or depth < best[0]:
            best = (depth, {'op': rel, 'font': face,
                            'codepoint': 'U+%04X' % ord(val)})
    return best[1] if best else None


def _surfaceIconFile(pkg_name, surface, seq):
    """Stable filename for a rendered glyph. `seq` disambiguates a package
    that puts two things on one bar -- MISC ships two toolbar buttons."""
    stem = '%s-%s' % (pkg_name, surface)
    return '%s%s.png' % (stem, '' if seq == 0 else '-%d' % (seq + 1))


def SurfaceEntries(comp):
    """Every ON-SCREEN contribution this package makes, one per registry
    host: which surface, which widget, what the bar calls it, where it
    sits, and the icon it draws.

    `surfaces` answers "does this put anything on screen at all"; this
    answers "what, exactly, and where" -- the question a reader with the
    toolbar open in front of them is actually asking. Both derive from the
    same registry hosts, so the two can never disagree.

    Everything is read off the host and its target: `Comp` is the widget
    the registry publishes, `Canonicalname` is the name the bar knows it
    by, and the order/side pars are the ones the surface configurator
    writes. Nothing here is authored in a doc.
    """
    out = []
    seen = {}
    for host in comp.findChildren():
        sid = SURFACE_OF.get(host.name)
        if sid is None:
            continue
        cpar = getattr(host.par, 'Comp', None)
        widget = cpar.eval() if cpar is not None else None
        rel = None
        if widget is not None:
            # A host whose target is the package itself contributes the
            # whole component (a Hub tab); one pointing at a child
            # contributes that widget. The relative path is what a reader
            # can actually find in the network.
            if widget.path.startswith(comp.path):
                rel = widget.path[len(comp.path) + 1:] or comp.name
            else:
                rel = widget.path      # a host pointing outside its package
        entry = {'surface': sid, 'widget': rel}
        # The name the SURFACE shows. A hub or console host carries a
        # `Tablabel` that overrides the canonical name on the tab bar
        # (its own tooltip: "Empty = the canonical name") -- ColorUI's tab
        # reads OpColor and the palette's reads Commands, and a page that
        # said otherwise was contradicting the screen.
        label = None
        for par_name in ('Tablabel', 'Canonicalname'):
            par = getattr(host.par, par_name, None)
            if par is not None and str(par.eval()).strip():
                label = str(par.eval()).strip()
                break
        if label:
            entry['label'] = label
        for par_name, key in (('Menuorder', 'order'), ('Taborder', 'order'),
                              ('Align', 'side')):
            par = getattr(host.par, par_name, None)
            if par is None:
                continue
            val = par.eval()
            # -1 is the registry's "no preference" sentinel, not a position.
            if key == 'order' and int(val) < 0:
                continue
            entry[key] = _plain(val)
        icon = _iconEvidence(widget)
        if icon:
            seq = seen.get(sid, 0)
            seen[sid] = seq + 1
            icon['file'] = _surfaceIconFile(comp.name, sid, seq)
            entry['icon'] = icon
        out.append(entry)
    return sorted(out, key=lambda e: (e['surface'], str(e.get('widget') or '')))


# Where rendered glyphs land: inside the generated docs tree, beside the
# repo icons the site already copies. website/docs/ is wiped and rebuilt on
# every site build, so the site build re-copies them from here.
GLYPH_DIR = ('packaging', 'docs', 'surface-icons')
GLYPH_PX = 64


def RenderSurfaceIcons(entries_by_pkg, out_dir=None):
    """Rasterize each gathered glyph to a PNG the docs site can show.

    Rendered by a throwaway Text TOP rather than by PIL, for two reasons:
    PIL is not in TouchDesigner's Python (numpy and requests are; measured
    on 2025.33070), and a Text TOP set to the same face at the same
    codepoint is not a lookalike of the toolbar button -- it is the same
    renderer drawing the same glyph. Nothing has to know where the font
    file lives, either: `font` takes the family name the button already
    names, so a TD upgrade that moves Samples/Fonts cannot break this.

    White on transparent at GLYPH_PX. The site is dark and tints it in CSS,
    and a white master survives a light theme later.

    Returns {'written', 'skipped'}. A glyph that renders EMPTY is reported
    rather than written: an all-transparent frame means the face has no
    glyph at that codepoint, so the live button is showing tofu and someone
    should know.
    """
    out_dir = out_dir or _repo(*GLYPH_DIR)
    os.makedirs(out_dir, exist_ok=True)
    written, skipped, kept = 0, [], set()

    home = op(TOOLKIT).parent() or op('/')
    tmp = home.create(textTOP, 'fns_tmp_surface_glyph')
    try:
        # Positioned out of the way and destroyed in the finally below --
        # it exists for the length of this call and is never saved.
        tmp.nodeX, tmp.nodeY = 20000, 20000
        tmp.par.outputresolution = 'specifyres'
        tmp.par.resolutionw = tmp.par.resolutionh = GLYPH_PX
        tmp.par.fontautosize = False
        tmp.par.fontsizex = int(GLYPH_PX * 0.72)
        tmp.par.alignx = 'center'
        tmp.par.aligny = 'center'
        tmp.par.wordwrap = False
        tmp.par.fontcolorr = tmp.par.fontcolorg = tmp.par.fontcolorb = 1
        tmp.par.fontalpha = 1
        tmp.par.bgalpha = 0
        # Straight alpha: the site composites these over its own background,
        # and premultiplied white would fringe on any other colour.
        tmp.par.premultrgbbyalpha = False

        for name, entries in sorted(entries_by_pkg.items()):
            for entry in entries:
                icon = entry.get('icon')
                if not icon:
                    continue
                try:
                    char = chr(int(icon['codepoint'][2:], 16))
                except (KeyError, ValueError):
                    skipped.append('%s: unreadable codepoint' % name)
                    continue
                tmp.par.font = icon['font']
                tmp.par.text = char
                tmp.cook(force=True)
                if float(tmp.numpyArray()[:, :, 3].max()) <= 0.0:
                    skipped.append('%s: %s renders empty in %s'
                                   % (name, icon['codepoint'], icon['font']))
                    continue
                tmp.save(os.path.join(out_dir, icon['file']))
                kept.add(icon['file'])
                written += 1
    finally:
        tmp.destroy()

    # A renamed package or a re-pointed host leaves an orphan behind, and a
    # stale icon on a docs page is worse than no icon at all.
    for stale in sorted(set(os.listdir(out_dir)) - kept):
        if stale.endswith('.png'):
            os.remove(os.path.join(out_dir, stale))
            skipped.append('removed stale %s' % stale)
    return {'written': written, 'skipped': skipped}


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
            if not _isAboutStamp(row):
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


# Private Investigator's markers. A released artifact is a COPY, and a copy
# that still carries them is a user's placed tool that PI treats as a dev
# original: `pi_suspect` makes it a tracked suspect, `Vcoriginal` True is
# what PI's Scan looks for. PI's own release scrub
# (CompReleaseManager.prepare) removes exactly these; the publish rail
# exports through Embody, which strips only Embody's tags, so every artifact
# shipped them (measured 2026-09-17: eight store toxes, root and 2-25 inner
# operators each). They are removed from the ARTIFACT, never the live
# master: stripping and restoring on the master was tried and marks it
# modified, so every export left masters PI-dirty with unchanged content.
PI_RELEASE_TAGS = ('pi_suspect', 'FNS_externalized')


def StripReleaseMarkers(comp):
    """Remove PI's markers from `comp` and its whole subtree -- meant for a
    COPY (ScrubArtifact's loaded artifact), never a live master. Returns
    the paths it changed."""
    changed = []
    for o in [comp] + list(comp.findChildren()):
        hit = False
        for t in PI_RELEASE_TAGS:
            if t in o.tags:
                o.tags.remove(t)
                hit = True
        vco = getattr(o.par, 'Vcoriginal', None) if o.isCOMP else None
        if vco is not None and vco.eval():
            vco.val = False
            hit = True
        if hit:
            changed.append(o.path)
    return changed


def ScrubArtifact(path):
    """Load a saved artifact into a cooking-disabled holder in /sys/quiet
    (the staging class Embody's own export uses), strip PI's markers from
    that copy, save it back over `path`, destroy the holder. Returns the
    number of operators changed; raises when the artifact cannot be loaded
    or saved, so the export reports it instead of hashing marked bytes.
    An artifact with nothing to strip is left byte-identical."""
    quiet = op('/sys/quiet') or op('/sys')
    holder = quiet.create(baseCOMP, 'fns_release_scrub')
    # cooking off on the HOLDER only: a flag set on the loaded copy would
    # be saved into the artifact
    holder.allowCooking = False
    try:
        loaded = holder.loadTox(path)
        changed = StripReleaseMarkers(loaded)
        if changed:
            loaded.save(path)
        return len(changed)
    finally:
        holder.destroy()


def ExportPackage(comp, suffix=''):
    """Export one self-contained .tox (Embody metadata stripped) and hash it.

    `suffix` names a variant build ('.pro'): the file is <name><suffix>.tox
    and the package's pre_release hook reads the edition off that save
    path (docs/TierVariants.md).

    Uses Embody's ExportPortableTox, which stages a COPY in /sys/quiet and
    runs the package's own pre_release hook -- so the live comp is never
    touched. PI's markers (PI_RELEASE_TAGS, Vcoriginal) are then scrubbed
    from the written artifact (ScrubArtifact), so it ships without them
    while the master keeps them; a scrub that fails fails the export.
    """
    os.makedirs(_repo(DIST_DIR), exist_ok=True)
    dest = _repo(DIST_DIR, comp.name + suffix + '.tox')
    before = os.path.getmtime(dest) if os.path.exists(dest) else None
    ok = op.Embody.ExportPortableTox(target=comp, save_path=dest)
    if ok and os.path.exists(dest) and (before is None or os.path.getmtime(dest) != before):
        try:
            ScrubArtifact(dest)
        except Exception as e:
            debug('packaging: %s artifact kept PI markers, scrub failed (%s)' % (comp.name, e))
            return None
    # A failed export (aborted pre_release hook) leaves the OLD file on
    # disk. Hashing it would publish a stale artifact under a fresh version
    # -- the silent mismatch that bit v2.12.1 -- so a requested export that
    # did not rewrite the file returns None and Build reports it loudly.
    if not ok or not os.path.exists(dest):
        return None
    if before is not None and os.path.getmtime(dest) == before:
        return None
    return {'path': DIST_DIR + '/' + comp.name + suffix + '.tox',
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
    nopick = {p['name'] for p in packages if p.get('nopick')}
    # a preview package is visible to its owner alone: a public bundle
    # never carries it (docs/PreviewPackages.md)
    preview = {p['name'] for p in packages if p.get('preview')}
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
        # a bundle is a bulk selection: an explicit-pick-only package
        # (`nopick`) is dropped from it and reported, like a lost name
        barred = [n for n in pkgs if n in nopick]
        hidden = [n for n in pkgs if n in preview]
        keep = [n for n in pkgs if n in known and n not in nopick and n not in preview]
        if gone:
            problems.append('preset %r: not shipped by this release: %s'
                            % (name, ', '.join(gone)))
        if barred:
            problems.append('preset %r: nopick packages are picked only one at a '
                            'time, dropped: %s' % (name, ', '.join(barred)))
        if hidden:
            problems.append('preset %r: preview packages are not released yet, '
                            'dropped: %s' % (name, ', '.join(hidden)))
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
    _surface_entries = {c.name: e for c, e in
                        ((c, SurfaceEntries(c)) for c in comps) if e}
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
        # WHAT it puts there, not just whether: one entry per registry
        # host, carrying the widget, the name the bar knows it by, its
        # position, and the icon glyph read off the live button. `surfaces`
        # above is the same evidence collapsed to a yes/no per surface.
        'surface_entries': _surface_entries,
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
    # Rasterized here, in the same live pass that gathered the codepoints:
    # anywhere else and the picture could describe a different project from
    # the data beside it.
    icons = RenderSurfaceIcons(_surface_entries)
    return {
        'path': out_path,
        'packages': len(doc['packages']),
        'parameters': sum(len(v) for v in doc['packages'].values()),
        'registries': {k: len(v) for k, v in doc['registry_sections'].items()},
        'about_stamp': len(doc['about_stamp']),
        'surface_entries': sum(len(v) for v in _surface_entries.values()),
        'surface_icons': icons,
    }


def _quiz(catalog, packages):
    """The guided setup's questionnaire, validated against what this
    manifest ships.

    catalog.json may carry `quiz.questions`: [{id, prompt, multi,
    options: [{id, label, tags}]}]. Each package may carry `fits`, the
    tags it answers. Emitted only when there is at least one question with
    options; an option tag that NO shipped package fits is reported (the
    question would promise a tool that does not exist), and a question
    left with no options is dropped. Returns (questions, problems).
    """
    fit_tags = set()
    for p in packages:
        if p.get('kind') == 'tool':
            fit_tags.update(p.get('fits') or [])
    out, problems = [], []
    raw_q = (catalog.get('quiz') or {}).get('questions') or []
    seen_q = set()
    for q in raw_q:
        if not isinstance(q, dict):
            problems.append('quiz: question is not an object: %r' % (q,))
            continue
        qid = str(q.get('id', '')).strip()
        prompt = str(q.get('prompt', '')).strip()
        if not qid or not prompt or qid in seen_q:
            problems.append('quiz: question needs a unique id and a prompt: %r' % (qid or q,))
            continue
        seen_q.add(qid)
        opts, seen_o = [], set()
        for o in q.get('options') or []:
            if not isinstance(o, dict):
                continue
            oid = str(o.get('id', '')).strip()
            label = str(o.get('label', '')).strip()
            if not oid or not label or oid in seen_o:
                problems.append('quiz %s: option needs a unique id and a label: %r' % (qid, oid or o))
                continue
            seen_o.add(oid)
            tags = [str(t).strip() for t in (o.get('tags') or []) if str(t).strip()]
            dead = [t for t in tags if t not in fit_tags]
            if dead:
                problems.append('quiz %s/%s: no shipped package fits: %s'
                                % (qid, oid, ', '.join(dead)))
            opts.append({'id': oid, 'label': label, 'tags': tags})
        if not opts:
            problems.append('quiz %s: no options, dropped' % qid)
            continue
        out.append({'id': qid, 'prompt': prompt, 'multi': bool(q.get('multi')),
                    'options': opts})
    return out, problems


def _searchIndex():
    """packaging/search_index.py, loaded by path: this file is exec'd into
    TD's namespace, so there is no package to import it from."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'fns_search_index', _repo(PKG_DIR, 'search_index.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
            # what a reader sees: `name` minus a leading FNS_ (or a
            # curated override). Identity stays in `name`.
            'title': str(meta.get('title', '') or PublicName(name)),
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
            'access': EffectiveAccess(meta),
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
        # author / homepage / changelog_url -- curated presentation facts,
        # presence-style (docs/ForeignPackages.md §1b). The picker byline
        # and the website badge both read the manifest, so the catalog is
        # the ONE home; doc-frontmatter `credit` is refused by the site
        # build.
        entry.update(CuratedLinks(meta))

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
        if str(meta.get('placement', '')) in ('pane', 'root', 'none'):
            entry['placement'] = str(meta['placement'])
        # A companion (catalog `companion: family`): infrastructure that
        # exists only for other packages. The FNS operator family is the
        # one today: the picker never offers it, and the installer adds it
        # exactly when the selection holds a family member and removes it
        # when none is left (InstallerExt.ResolvePlan). Presence-style.
        if str(meta.get('companion', '')) == 'family':
            entry['companion'] = 'family'
        # A priced family product (catalog `pricing`): not gated by the
        # toolkit's tiers, so `access` stays free and it installs for
        # everyone, but not free either -- the picker, the site and the
        # counts must not call it that. Copy only, no derivation.
        pricing = meta.get('pricing')
        if isinstance(pricing, dict) and str(pricing.get('summary', '') or '').strip():
            entry['pricing'] = {k: str(pricing.get(k, '') or '').strip()
                                for k in ('summary', 'detail', 'url')}

        # A minor tool, curated in catalog.json. A small convenience that
        # should not compete for attention with the tools someone came for:
        # the picker ranks it last inside its category and draws it compact.
        # Presence-style like `placement`, so an unauthored row stays
        # byte-identical. Deliberately NOT hidden and NOT uncategorised --
        # it is a real package a real person may want, and a picker that
        # hides packages lies about what the toolkit contains (same
        # reasoning as the Plus tier being marked rather than hidden).
        if meta.get('minor'):
            entry['minor'] = True

        # Explicit-pick only (catalog `nopick: true`): a hardware-specific
        # integration, say, that must never arrive because someone asked for
        # "everything". A real package with a normal card, installable and
        # updatable, but every BULK selection leaves it out -- Select all,
        # Everything, Recommended (`starter` below), the bundles and the
        # questionnaire. Presence-style: only `true` is ever written, and
        # only the boolean is copied (CatalogProblems refuses anything else).
        if meta.get('nopick') is True:
            entry['nopick'] = True

        # Place once (catalog `placeonce: true`, docs/PlaceOnce.md): the
        # picker card offers Place beside the tick. A placed tool is
        # installed and updated here like any other, but its install record
        # says remember = 0, so the root's last_install never carries it and
        # "Set up like last time" never places it in the next project. The
        # tick stays available for anyone who does want it every time.
        if meta.get('placeonce') is True:
            entry['placeonce'] = True

        # Not released yet (docs/PreviewPackages.md): the picker, the site and
        # the new-tools notice leave it out for everyone but the creator,
        # whose account is the only one entitled to PREVIEW_TIER.
        if meta.get('preview') is True:
            entry['preview'] = True

        # What the guided setup's questionnaire can match this package on
        # (catalog `fits`, a list of tags). Presence-style; the tags
        # themselves are validated against the quiz in _quiz().
        fits = [str(t).strip() for t in (meta.get('fits') or []) if str(t).strip()]
        if fits:
            entry['fits'] = fits

        # Operator types this package is an alternative for, DERIVED from its
        # op-menu callbacks (AlternativesFor) when it carries an op-menu host;
        # a package with NO host may curate the list in the catalog instead
        # (the CMS input). Presence-style. The registry offers a store tox
        # for these types when the package is not live, which is the only
        # way it can know that without loading the tox.
        alternatives_for = AlternativesFor(comp)
        if not alternatives_for and comp.op('FNS_OpMenuRegistry') is None:
            alternatives_for = CuratedAlternatives(meta)
        if alternatives_for:
            entry['alternatives_for'] = alternatives_for

        # An FNS operator family member (docs/OperatorFamilyFromStore.md):
        # DERIVED from the package's FamManifest/OpInfo when it carries one,
        # curated in the catalog otherwise. Membership implies `placement`
        # pane -- a family op is placed into the working network by
        # definition -- so an unauthored placement becomes pane here, and a
        # curated `root` is a catalog problem. The updater builds the
        # family folder's sidecar from this block; nothing else reads it.
        family = FamilyFor(comp)
        if not family and comp.op('FamManifest') is None:
            family = CuratedFamily(meta)
        if family:
            entry['family'] = family
            # not placed -- see the curated branch above
            entry.setdefault('placement', 'none')

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
        # Variant builds (docs/TierVariants.md): one artifact per tier
        # above the entry tier, from a second master (`source`) or from
        # this master exported under the variant's file name. The row
        # stays ONE package; `artifact` is the Base build.
        variants = Variants(meta)
        if variants:
            entry['variants'] = {}
            prev_vars = previous.get(name, {}).get('variants') or {}
            for vid, block in sorted(variants.items()):
                src_name = str(block.get('source', '') or '').strip()
                src_comp = _root().op(src_name) if src_name else comp
                vrow = {'access': (PREVIEW_TIER if meta.get('preview') is True
                                   else str(block.get('access', '') or '')),
                        'summary': str(block.get('summary', '') or '')}
                if src_comp is None:
                    export_failed.append('%s.%s (source %s missing)' % (name, vid, src_name))
                elif do_export:
                    vart = ExportPackage(src_comp, suffix='.' + vid)
                    if vart:
                        vrow['artifact'] = vart
                    else:
                        export_failed.append('%s.%s' % (name, vid))
                else:
                    built = _repo(DIST_DIR, '%s.%s.tox' % (name, vid))
                    if os.path.exists(built):
                        vrow['artifact'] = {
                            'path': '%s/%s.%s.tox' % (DIST_DIR, name, vid),
                            'bytes': os.path.getsize(built),
                            'sha256': _sha256(built),
                        }
                    elif (prev_vars.get(vid) or {}).get('artifact'):
                        vrow['artifact'] = prev_vars[vid]['artifact']
                if src_comp is not None:
                    vrow['version'] = _version(src_comp)
                entry['variants'][vid] = vrow
        packages.append(entry)

    # Foreign packages: declared in the catalog, mirrored by foreign_sync,
    # versioned by the lock. Appended AFTER the live rows so a live package
    # always wins a name (CatalogProblems reports the collision).
    live_names = {p['name'] for p in packages}
    foreign_rows, foreign_problems = ForeignPackages(
        catalog, ForeignLock(), previous=previous)
    for entry in foreign_rows:
        if entry['name'] in live_names:
            continue
        if 'artifact' not in entry and previous.get(entry['name'], {}).get('artifact'):
            # the same fallback a non-exported live row gets: describe
            # the artifact that shipped last time rather than none
            entry['artifact'] = previous[entry['name']]['artifact']
        packages.append(entry)
    catalog_problems = CatalogProblems(catalog, live_names,
                                       opmenu_hosted=OpMenuHostedNames(),
                                       family_hosted=FamilyHostedNames()) + foreign_problems

    # The words each package's user-facing doc adds to the picker's search
    # (packaging/search_index.py, docs/PickerSearch.md): someone typing
    # "midi" or "lag" finds a tool whose card never says it. Presence-style,
    # like `fits`: a row whose doc adds nothing carries no key, and the
    # picker searches every other field without it. A preview row carries
    # none either: the published manifest names a preview and describes it
    # in one line (docs/PreviewPackages.md, Limits), and its doc's words
    # are more than that line promises.
    index = _searchIndex().BuildIndex(packages, _repo(PKG_DIR, 'docs'))
    for entry in packages:
        words = index.get(entry['name'])
        if entry.get('preview'):
            continue
        if words and (words['head'] or words['body']):
            entry['search'] = words

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
        # a variant build is always gated: its key sits under plus/ too
        for vid, v in sorted((entry.get('variants') or {}).items()):
            vart = (v or {}).get('artifact')
            if vart:
                vart['url'] = '%s/%s/%s/%s.%s.tox' % (base_url.rstrip('/'), PLUS_PREFIX,
                                                     rel, entry['name'], vid)

    doc = {
        'schema': MANIFEST_SCHEMA,
        'release': rel,
        # The RELEASE-level half only. A "Package: ..." line already rides
        # that package's own `whatsnew` (see `attributed` above), so the raw
        # text would show it twice -- and worse, a line written for a
        # package that is NOT in this release has no bullet to ride, so the
        # changelog drops it while the raw text shipped it to every user as
        # general prose. That is how an unshipped FNS_CommandKit note went
        # out in v3.2.31 and again in v3.2.34.
        'notes': AttributedNotes()[1],
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
                    if p['kind'] == 'tool' and not p.get('nopick')
                    and not p.get('preview')
                    and curated.get(p['name'], {}).get('recommended')],
        'packages': packages,
    }
    # Curated bundles for the guided setup (catalog `presets`, validated
    # against this very package list). Emitted only when curation exists,
    # so older manifests and an unauthored catalog stay byte-identical.
    preset_bundles, preset_problems = _presets(catalog, packages)
    if preset_bundles:
        doc['presets'] = preset_bundles
    # The questionnaire, same discipline: emitted only when authored.
    quiz_questions, quiz_problems = _quiz(catalog, packages)
    if quiz_questions:
        doc['quiz'] = {'questions': quiz_questions}
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
            'quiz_problems': quiz_problems,
            'foreign': [p['name'] for p in packages if p.get('foreign')],
            # the docs index's share of the manifest (raw, gzipped bytes)
            'search_bytes': _searchIndex().Sizes(
                {p['name']: p['search'] for p in packages if 'search' in p}),
            'catalog_problems': catalog_problems,
            'uncategorized': [p['name'] for p in packages
                              if p['category'] == 'Uncategorized']}
