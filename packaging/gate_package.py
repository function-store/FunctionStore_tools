"""Author gated packages: one command, both files, no drift.

    python packaging/gate_package.py --status
    python packaging/gate_package.py FNS_TimelineTools --tier 1234567

`--tier` is the ENTRY tier: the package is granted to that tier and every
tier above it in TIER_LADDER, because Patreon memberships carry only
their own tier id.
    python packaging/gate_package.py FNS_TimelineTools --gumroad abc123xyz
    python packaging/gate_package.py FNS_TimelineTools --free
    python packaging/gate_package.py FNS_TimelineTools --preview
    python packaging/gate_package.py FNS_TimelineTools --release

`--preview` holds a package back from the public (docs/PreviewPackages.md):
catalog `preview: true`, and its only Patreon grant becomes the pseudo tier
PREVIEW_TIER, which the Worker gives the creator account alone. Its
`access` stays what it will ship at. `--release` clears the flag and
re-derives the real grants from that `access`. Gumroad rows are left alone
either way, so a key set up ahead of the launch survives the preview.

Gating a package is TWO edits that must agree -- `access` (a Patreon
TIER ID, never a display name) in packaging/catalog.json, and the grant
in worker/wrangler.toml's TIERS / GUMROAD_PRODUCTS map -- and
publish.Stage() refuses a release where they disagree. This command is
the authoring side of that contract: it writes both in one motion,
drops the REPLACE_/PLACEHOLDER_ scaffolding as real values land, and
prints the same authorizability verdict Stage() will enforce.

What it deliberately does NOT touch: `license` and `seats` in the
catalog (hand-curated policy), and the Worker's secrets/deploy --
changing the map still needs a `wrangler deploy` to take effect.
"""

import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(REPO, 'packaging', 'catalog.json')
WRANGLER = os.path.join(REPO, 'worker', 'wrangler.toml')

# The campaign's tiers, CHEAPEST FIRST. Patreon memberships are not
# hierarchical -- a Pro patron carries the Pro id only, never Base's --
# so "unlocks at Base and above" means every id from Base upward has to
# grant the package. --tier names the ENTRY tier and the rest is derived,
# because hand-listing three ids per package is how the maps drift.
#
# Which tier a given tool enters at is a per-tool decision; the ORDER is
# campaign-wide and belongs here.
TIER_LADDER = (
    ('8323905', 'Base'),
    ('8291595', 'Pro'),
    ('9796651', 'Coaching'),
)


# Never a Patreon tier id (those are numeric), so no membership can carry
# it: the Worker adds it to the creator account's tiers, nobody else's.
PREVIEW_TIER = 'preview'


def LadderFrom(tier):
    """`tier` and every tier above it. Unknown ids grant only themselves."""
    ids = [t for t, _ in TIER_LADDER]
    if tier not in ids:
        return [tier]
    return ids[ids.index(tier):]


def TierName(tier):
    if tier == PREVIEW_TIER:
        return 'Preview (creator only)'
    for t, label in TIER_LADDER:
        if t == tier:
            return label
    return tier


def _is_placeholder(s):
    return 'PLACEHOLDER' in s.upper() or 'REPLACE' in s.upper()


def _load_catalog():
    with open(CATALOG, encoding='utf-8') as f:
        return json.load(f)


def _save_catalog(doc):
    with open(CATALOG, 'w', encoding='utf-8', newline='\n') as f:
        # ensure_ascii=False keeps the catalogue's glyphs literal.
        # Without it every run rewrites 20-odd lines into escape
        # sequences -- a diff full of noise hiding the one line that
        # actually changed.
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')


def _read_block(src, name):
    m = re.search(r'^%s\s*=\s*"""(.*?)"""' % name, src, re.M | re.S)
    if not m:
        sys.exit('%s: no %s block found' % (WRANGLER, name))
    try:
        return json.loads(m.group(1)), m
    except Exception as e:
        sys.exit('%s: %s block is not valid JSON (%s)' % (WRANGLER, name, e))


def _write_block(src, match, data):
    body = json.dumps(data, indent=2) if data else '{\n}'
    return src[:match.start(1)] + '\n%s\n' % body + src[match.end(1):]


def _maps():
    src = open(WRANGLER, encoding='utf-8').read()
    tiers, tm = _read_block(src, 'TIERS')
    gumroad, gm = _read_block(src, 'GUMROAD_PRODUCTS')
    return src, tiers, tm, gumroad, gm


def _save_maps(src, tiers, gumroad):
    # re-locate after each rewrite: offsets move
    _, m = _read_block(src, 'TIERS')
    src = _write_block(src, m, tiers)
    _, m = _read_block(src, 'GUMROAD_PRODUCTS')
    src = _write_block(src, m, gumroad)
    with open(WRANGLER, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)


def _prune(tiers, gumroad, name):
    """Remove `name` from every grant; drop emptied or placeholder rows."""
    for k in list(tiers):
        tiers[k] = [p for p in tiers[k] if p != name]
        if not tiers[k] or _is_placeholder(k):
            del tiers[k]
    for k in list(gumroad):
        if gumroad[k] == name or _is_placeholder(k):
            del gumroad[k]


def Variants(meta):
    """{vid: block} from a catalog entry's `variants` (docs/TierVariants.md):
    one build per tier above the entry tier, each its own gate product."""
    v = (meta or {}).get('variants') or {}
    return {str(k): b for k, b in v.items() if isinstance(b, dict)}


def VariantProduct(name, vid):
    """The gate's product name for one variant build: FNS_Foo.pro. The
    Worker serves plus/<release>/FNS_Foo.pro.tox to an account whose
    products list carries exactly this name."""
    return '%s.%s' % (name, vid)


def _grantVariants(name, meta, tiers, gumroad):
    """Re-derive every variant product's grants from its own access."""
    granted = {}
    for vid, block in Variants(meta).items():
        product = VariantProduct(name, vid)
        _prune(tiers, gumroad, product)
        acc = str(block.get('access', '') or '')
        if not acc.isdigit():
            continue
        for t in LadderFrom(acc):
            tiers.setdefault(t, [])
            if product not in tiers[t]:
                tiers[t].append(product)
        granted[product] = LadderFrom(acc)
    return granted


def IsPreview(meta):
    return (meta or {}).get('preview') is True


def _previewGrants(name, meta, tiers):
    """While a package is a preview, PREVIEW_TIER is its only Patreon grant,
    for the package and each of its variant builds."""
    products = [name] + [VariantProduct(name, vid) for vid in Variants(meta)]
    for k in list(tiers):
        tiers[k] = [p for p in tiers[k] if p not in products]
        if not tiers[k]:
            del tiers[k]
    tiers.setdefault(PREVIEW_TIER, [])
    for prod in products:
        if prod not in tiers[PREVIEW_TIER]:
            tiers[PREVIEW_TIER].append(prod)


def _realGrants(name, meta, tiers, gumroad):
    """The public grants, from the catalog's access and variants."""
    products = [name] + [VariantProduct(name, vid) for vid in Variants(meta)]
    for k in list(tiers):
        tiers[k] = [p for p in tiers[k] if p not in products]
        if not tiers[k]:
            del tiers[k]
    acc = str(meta.get('access', '') or '')
    if acc.isdigit():
        for t in LadderFrom(acc):
            tiers.setdefault(t, [])
            if name not in tiers[t]:
                tiers[t].append(name)
    _grantVariants(name, meta, tiers, gumroad)


def Preview(name, on=True):
    """Hold a package back from the public, or release it."""
    cat = _load_catalog()
    if name not in cat.get('packages', {}):
        sys.exit('%s is not in catalog.json' % name)
    meta = cat['packages'][name]
    src, tiers, _, gumroad, _ = _maps()
    if on:
        meta['preview'] = True
        _previewGrants(name, meta, tiers)
    else:
        meta.pop('preview', None)
        _realGrants(name, meta, tiers, gumroad)
    _save_catalog(cat)
    _save_maps(src, tiers, gumroad)
    acc = str(meta.get('access', '') or 'free')
    print(('%s is a preview: only the creator account can see and install it '
           '(ships at %s when released)' % (name, TierName(acc) if acc != 'free' else 'free'))
          if on else
          ('%s is released at %s' % (name, TierName(acc) if acc != 'free' else 'free')))
    print('remember: `wrangler deploy` for the map to take effect')
    return Status()


def Status():
    cat = _load_catalog()
    _, tiers, _, gumroad, _ = _maps()
    rows, problems = [], []
    for name, meta in sorted(cat.get('packages', {}).items()):
        acc = PREVIEW_TIER if IsPreview(meta) else str(meta.get('access', 'free') or 'free')
        if acc == 'free':
            continue
        grants = sorted(t for t, pkgs in tiers.items() if name in pkgs)
        keys = sorted(k for k, v in gumroad.items() if v == name)
        rows.append((name, acc, grants, keys))
        if _is_placeholder(acc):
            problems.append('%s: access is a placeholder' % name)
        elif acc not in grants and not keys:
            problems.append('%s: access=%s but nothing grants it' % (name, acc))
        elif acc in tiers and name not in tiers[acc]:
            problems.append('%s: tier %s does not include it' % (name, acc))
    if not rows:
        print('no gated packages in the catalog')
    for name, acc, grants, keys in rows:
        print('%-24s access=%-16s tiers=%-20s gumroad=%s'
              % (name, acc, ','.join(grants) or '-', ','.join(keys) or '-'))
    if problems:
        print('\nNOT authorizable (Stage() will refuse):')
        for p in problems:
            print('  ' + p)
        return 1
    if rows:
        print('\nall gated rows authorizable')
    return 0


def Gate(name, tier=None, gumroad_id=None, variant=None):
    cat = _load_catalog()
    if name not in cat.get('packages', {}):
        sys.exit('%s is not in catalog.json -- add its entry first' % name)
    if tier and (_is_placeholder(tier) or not tier.isdigit()):
        sys.exit('--tier takes the NUMERIC Patreon tier ID (got %r). Display '
                 'names can be renamed and are not unique; find the id by '
                 'signing in once through /patreon/start -- a refusal returns '
                 'the tiers array it saw.' % tier)
    src, tiers, _, gumroad, _ = _maps()
    if variant:
        # One build above the entry tier: `variants.<vid>.access` records
        # its own entry tier and the product FNS_Foo.<vid> is granted
        # from there up; the Base grants are left exactly as they are.
        if not tier:
            sys.exit('--variant needs --tier: the tier the %s build unlocks at' % variant)
        meta = cat['packages'][name]
        blocks = meta.setdefault('variants', {})
        block = blocks.setdefault(variant, {})
        block['access'] = tier
        granted_v = _grantVariants(name, meta, tiers, gumroad)
        if IsPreview(meta):
            _previewGrants(name, meta, tiers)
        _save_catalog(cat)
        _save_maps(src, tiers, gumroad)
        shown = ', '.join('%s (%s)' % (t, TierName(t))
                          for t in granted_v.get(VariantProduct(name, variant), []))
        print('gated %s from %s up: %s -- remember: `wrangler deploy` for the '
              'map to take effect' % (VariantProduct(name, variant), TierName(tier), shown))
        return Status()
    _prune(tiers, gumroad, name)
    granted = []
    if tier:
        # access records the ENTRY tier -- the meaningful, stable fact
        # ("unlocks from Base up"). The grants below carry the rest.
        cat['packages'][name]['access'] = tier
        for t in LadderFrom(tier):
            tiers.setdefault(t, [])
            if name not in tiers[t]:
                tiers[t].append(name)
            granted.append(t)
    if gumroad_id:
        gumroad[gumroad_id] = name
        cat['packages'][name].setdefault('access', tier or 'gumroad')
    # a variant's grants follow its own access, re-derived on every
    # regate of the base so the two maps never drift apart
    _grantVariants(name, cat['packages'][name], tiers, gumroad)
    # a preview records the access it will ship at, but grants only
    # PREVIEW_TIER until it is released
    if IsPreview(cat['packages'][name]):
        _previewGrants(name, cat['packages'][name], tiers)
    _save_catalog(cat)
    _save_maps(src, tiers, gumroad)
    if granted:
        shown = ', '.join('%s (%s)' % (t, TierName(t)) for t in granted)
        entry = ' from %s up: %s' % (TierName(tier), shown)
    else:
        entry = ''
    print('gated %s%s%s -- remember: `wrangler deploy` for the map to take '
          'effect' % (name, entry,
                      ' + gumroad %s' % gumroad_id if gumroad_id else ''))
    return Status()


def Free(name):
    cat = _load_catalog()
    if name not in cat.get('packages', {}):
        sys.exit('%s is not in catalog.json' % name)
    for k in ('access', 'license', 'seats'):
        if k == 'access':
            cat['packages'][name].pop('access', None)
    src, tiers, _, gumroad, _ = _maps()
    _prune(tiers, gumroad, name)
    for vid in Variants(cat['packages'][name]):
        _prune(tiers, gumroad, VariantProduct(name, vid))
    cat['packages'][name].pop('variants', None)
    if IsPreview(cat['packages'][name]):
        _previewGrants(name, cat['packages'][name], tiers)
    _save_catalog(cat)
    _save_maps(src, tiers, gumroad)
    print('%s is free again (removed from every grant)' % name)
    return Status()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('package', nargs='?')
    ap.add_argument('--tier', help='numeric Patreon tier ID of the ENTRY '
                                   'tier -- every tier above it is granted '
                                   'too')
    ap.add_argument('--gumroad', help='Gumroad product id (per-tool key)')
    ap.add_argument('--variant', help='gate one variant build (pro) at --tier '
                                      'instead of the package itself')
    ap.add_argument('--free', action='store_true', help='ungate the package')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--preview', action='store_true',
                    help='hold the package back: only the creator account '
                         'sees and installs it')
    ap.add_argument('--release', action='store_true',
                    help='end the preview: grant it at its catalog access')
    ap.add_argument('--ladder', action='store_true',
                    help='print the tier ladder as JSON (cheapest way for '
                         'another tool to offer NAMES while writing ids)')
    a = ap.parse_args()
    if a.ladder:
        print(json.dumps([{'id': t, 'label': label}
                          for t, label in TIER_LADDER]))
        sys.exit(0)
    if a.status or not a.package:
        sys.exit(Status())
    if a.preview:
        sys.exit(Preview(a.package, True))
    if a.release:
        sys.exit(Preview(a.package, False))
    if a.free:
        sys.exit(Free(a.package))
    if not a.tier and not a.gumroad:
        ap.error('give --tier and/or --gumroad (or --free / --status)')
    sys.exit(Gate(a.package, tier=a.tier, gumroad_id=a.gumroad, variant=a.variant))
