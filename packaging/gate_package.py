"""Author gated packages: one command, both files, no drift.

    python packaging/gate_package.py --status
    python packaging/gate_package.py FNS_TimelineTools --tier 1234567
    python packaging/gate_package.py FNS_TimelineTools --gumroad abc123xyz
    python packaging/gate_package.py FNS_TimelineTools --free

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


def _is_placeholder(s):
    return 'PLACEHOLDER' in s.upper() or 'REPLACE' in s.upper()


def _load_catalog():
    with open(CATALOG, encoding='utf-8') as f:
        return json.load(f)


def _save_catalog(doc):
    with open(CATALOG, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, indent=1)
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


def Status():
    cat = _load_catalog()
    _, tiers, _, gumroad, _ = _maps()
    rows, problems = [], []
    for name, meta in sorted(cat.get('packages', {}).items()):
        acc = str(meta.get('access', 'free') or 'free')
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


def Gate(name, tier=None, gumroad_id=None):
    cat = _load_catalog()
    if name not in cat.get('packages', {}):
        sys.exit('%s is not in catalog.json -- add its entry first' % name)
    if tier and (_is_placeholder(tier) or not tier.isdigit()):
        sys.exit('--tier takes the NUMERIC Patreon tier ID (got %r). Display '
                 'names can be renamed and are not unique; find the id by '
                 'signing in once through /patreon/start -- a refusal returns '
                 'the tiers array it saw.' % tier)
    src, tiers, _, gumroad, _ = _maps()
    _prune(tiers, gumroad, name)
    if tier:
        cat['packages'][name]['access'] = tier
        tiers.setdefault(tier, [])
        if name not in tiers[tier]:
            tiers[tier].append(name)
    if gumroad_id:
        gumroad[gumroad_id] = name
        cat['packages'][name].setdefault('access', tier or 'gumroad')
    _save_catalog(cat)
    _save_maps(src, tiers, gumroad)
    print('gated %s%s%s -- remember: `wrangler deploy` for the map to take '
          'effect' % (name,
                      ' -> tier %s' % tier if tier else '',
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
    _save_catalog(cat)
    _save_maps(src, tiers, gumroad)
    print('%s is free again (removed from every grant)' % name)
    return Status()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('package', nargs='?')
    ap.add_argument('--tier', help='numeric Patreon tier ID')
    ap.add_argument('--gumroad', help='Gumroad product id (per-tool key)')
    ap.add_argument('--free', action='store_true', help='ungate the package')
    ap.add_argument('--status', action='store_true')
    a = ap.parse_args()
    if a.status or not a.package:
        sys.exit(Status())
    if a.free:
        sys.exit(Free(a.package))
    if not a.tier and not a.gumroad:
        ap.error('give --tier and/or --gumroad (or --free / --status)')
    sys.exit(Gate(a.package, tier=a.tier, gumroad_id=a.gumroad))
