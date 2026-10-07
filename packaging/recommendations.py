"""Read and validate packaging/recommendations.json.

Shared by the CMS's save path, the uploader, the site build and the tests,
so the rules are stated once. Runs on the SHELL and inside TD -- no TD
builtins, no imports beyond the stdlib.

WHY VALIDATION AT ALL, for a hand-curated list: because this file is
published straight to every install with no release in between, so there is
no build step in which a bad row would be noticed. The publish path IS the
review, which means it has to say no.

The rules that matter, in the order they matter:

  * PACKAGE-SHAPED FIELDS ARE REFUSED. `version`, `requires`, `artifact`,
    `Pkgversion` and friends are rejected outright rather than ignored.
    They are how this list would quietly become a package list -- someone
    pastes a manifest row, nothing complains, and six months later
    something downstream treats it as ours to keep current.
  * PLACEMENT NEEDS A PINNED HASH. A row may carry `tox_url` + `sha256` +
    `bytes`, and then it can be downloaded and placed. The pin is the
    entire safety argument: it promises these are the exact bytes a
    curator looked at. If the author republishes, the hash stops matching
    and the row degrades to a link rather than installing something nobody
    vetted. Placement never enters the store or the manifest, so no update
    mechanism can see what it placed.
  * URLS MUST BE https. These open in a user's browser on our say-so.
  * NAMES MUST BE UNIQUE, so a row can be removed by name and a UI can key
    on it.
  * A PYTHON PACKAGE IS NAMED, NOT PINNED. A `tdp` row names a package on
    PyPI, its module, and whatever it imports without declaring (`also`).
    The latest release installs (owner, 2026-09-27: no versions to keep up
    to date); the installer's dry run refuses one that would add a package
    TouchDesigner ships. A `lock` is refused as an unknown field.

Rows are also blog posts on the website (docs/CommunityHighlights.md): a
`slug`, a `date`, an `image`, a `platform` and the `author_license`, with
the write-up in website/content/community/<slug>.md.
"""

import json
import os
import re

FILENAME = 'recommendations.json'
SCHEMA = 1

REQUIRED = ('name', 'author', 'url')
OPTIONAL = ('author_url', 'description', 'category', 'note',
            # Placement. Present together or not at all -- see below.
            'tox_url', 'sha256', 'bytes', 'pinned_at',
            # The website post (docs/CommunityHighlights.md).
            'slug', 'date', 'image', 'platform', 'author_license',
            # A tox shipped as a Python package, named (latest installs).
            'tdp',
            # Being written: kept out of the site and out of what installs
            # download until it is cleared.
            'draft')
ALLOWED = set(REQUIRED) | set(OPTIONAL)

# Fields that would make a row look like one of OUR packages -- something
# the updater versions, compares and keeps current. Refused, never ignored:
# that is the failure that would not look like one.
#
# `sha256`/`bytes` are deliberately NOT here. They were, on the reasoning
# that they are how a manifest row sneaks in -- but they are integrity
# facts, not update machinery, and PLACEMENT needs them. What makes a row
# updatable is a version and a source we poll, and neither is allowed.
FORBIDDEN = ('version', 'artifact', 'requires', 'kind', 'pkgversion',
             'access', 'license', 'surfaces', 'shortcut', 'min_td_build',
             'tox_carrier', 'seats')

HEX64 = re.compile(r'^[0-9a-f]{64}$')
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
IMAGE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*\.(?:png|jpg|jpeg|webp|gif)$')
PLATFORMS = ('github', 'patreon', 'gumroad', 'itch', 'pypi', 'other')
MAX_LICENSE = 200

# A PyPI project name (PEP 508), a dotted module path, a tox key.
PYPI_NAME = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$')
MODULE = re.compile(r'^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$')
TOX_KEY = re.compile(r'^[A-Za-z_]\w*$')
TDP_FIELDS = ('package', 'module', 'tox', 'also')


def _canon(name):
    """PEP 503 normalised name: `tdp-TauCeti` and `tdp_tauceti` are one."""
    return re.sub(r'[-_.]+', '-', str(name)).lower()


def delivery(row):
    """How a user gets it: 'tdp' (a pinned Python package), 'tox' (a
    pinned file we place) or 'link' (their page, nothing else)."""
    if isinstance(row.get('tdp'), dict) and row['tdp'].get('package') and row['tdp'].get('module'):
        return 'tdp'
    return 'tox' if installable(row) else 'link'


def _tdpProblems(where, t):
    if not isinstance(t, dict):
        return ['%s: tdp must be an object' % where]
    out = []
    for f in t:
        if f not in TDP_FIELDS:
            out.append('%s: tdp has an unknown field `%s`' % (where, f))
    pkg = str(t.get('package', '')).strip()
    if not PYPI_NAME.match(pkg):
        out.append('%s: tdp.package must be a PyPI project name' % where)
    if not MODULE.match(str(t.get('module', '')).strip()):
        out.append('%s: tdp.module must be the importable module (tdpFoo)' % where)
    if 'tox' in t and not TOX_KEY.match(str(t.get('tox', '')).strip()):
        out.append('%s: tdp.tox must name one entry of the package\'s _ToxFiles' % where)
    also = t.get('also', [])
    if not isinstance(also, list) or not all(PYPI_NAME.match(str(a).strip()) for a in also):
        out.append('%s: tdp.also must be a list of PyPI project names' % where)
    return out


def installable(row):
    """Can this row be PLACED, or is it link-only?

    Placement requires a pinned hash, and the pin is the whole safety
    argument: it is a promise that these are the exact bytes a curator
    looked at. If the author republishes, the hash stops matching and the
    tool degrades to a link rather than silently installing something
    nobody vetted."""
    return bool(str(row.get('tox_url', '')).strip()
                and HEX64.match(str(row.get('sha256', '')).strip().lower() or ''))

MAX_DESCRIPTION = 400


def path(repo_dir):
    return os.path.join(repo_dir, 'packaging', FILENAME).replace('\\', '/')


def load(repo_dir):
    with open(path(repo_dir), 'r', encoding='utf-8') as f:
        return json.load(f)


# Operator families built with TDFam (docs/CommunityHighlights.md,
# "Built with TDFam"): a website-only list, shown on /community/#tdfam and
# never downloaded by installs. `tool` names a row in `tools`, and the card
# links that row's post; `ours` marks FNSTools' own family, counted from the
# catalog at build.
FAMILY_REQUIRED = ('name', 'author', 'url')
FAMILY_FIELDS = ('name', 'author', 'author_url', 'url', 'description', 'ops', 'tool', 'ours')


def _familyProblems(families, tool_names):
    if families is None:
        return []
    if not isinstance(families, list):
        return ['`families` must be a list']
    out, seen = [], set()
    for i, row in enumerate(families):
        where = 'families[%d]' % i
        if not isinstance(row, dict):
            out.append('%s is not an object' % where)
            continue
        name = str(row.get('name', '')).strip()
        if name:
            where = '%s (%s)' % (where, name)
        for f in FAMILY_REQUIRED:
            if not str(row.get(f, '')).strip():
                out.append('%s: %s is required' % (where, f))
        for f in row:
            if f not in FAMILY_FIELDS:
                out.append('%s: unknown field `%s`' % (where, f))
        url = str(row.get('url', '')).strip()
        if url and not (url.startswith('https://') or url.startswith('/')):
            out.append('%s: url must be https, or a page on this site (/...)' % where)
        aurl = str(row.get('author_url', '')).strip()
        if aurl and not aurl.startswith('https://'):
            out.append('%s: author_url must be https' % where)
        if 'ops' in row and (not isinstance(row['ops'], int) or isinstance(row['ops'], bool) or row['ops'] <= 0):
            out.append('%s: ops must be a positive whole number' % where)
        if 'ours' in row and not isinstance(row['ours'], bool):
            out.append('%s: ours must be true or false' % where)
        if 'tool' in row and str(row['tool']) not in tool_names:
            out.append('%s: tool %r is not a row in tools' % (where, row['tool']))
        if len(str(row.get('description', ''))) > MAX_DESCRIPTION:
            out.append('%s: description is over %d characters' % (where, MAX_DESCRIPTION))
        if name:
            if name.casefold() in seen:
                out.append('%s: duplicate name' % where)
            seen.add(name.casefold())
    return out


def validate(doc):
    """Return a list of problems. Empty means publishable."""
    problems = []
    if not isinstance(doc, dict):
        return ['recommendations.json must be a JSON object']
    if doc.get('schema') != SCHEMA:
        problems.append('schema must be %d (got %r)' % (SCHEMA, doc.get('schema')))
    tools = doc.get('tools')
    if not isinstance(tools, list):
        return problems + ['`tools` must be a list']

    seen = {}
    slugs = {}
    for i, row in enumerate(tools):
        where = 'tools[%d]' % i
        if not isinstance(row, dict):
            problems.append('%s is not an object' % where)
            continue
        name = str(row.get('name', '')).strip()
        if name:
            where = '%s (%s)' % (where, name)

        for f in REQUIRED:
            if not str(row.get(f, '')).strip():
                problems.append('%s: %s is required' % (where, f))

        for f in row:
            if f.lower() in FORBIDDEN:
                problems.append(
                    '%s: `%s` is not allowed here -- this is a link, not a '
                    'package. If it needs a version it belongs in '
                    'catalog.json.' % (where, f))
            elif f not in ALLOWED:
                problems.append('%s: unknown field `%s`' % (where, f))

        for f in ('url', 'author_url'):
            v = str(row.get(f, '')).strip()
            if v and not v.startswith('https://'):
                problems.append(
                    '%s: %s must be https (opening it is our recommendation)'
                    % (where, f))

        # Placement fields travel together: a tox_url with no pinned hash
        # would install unverified bytes, and a hash with no url is inert.
        tox = str(row.get('tox_url', '')).strip()
        sha = str(row.get('sha256', '')).strip().lower()
        size = row.get('bytes')
        if tox or sha or size is not None:
            if not tox:
                problems.append('%s: sha256/bytes given without tox_url' % where)
            elif not tox.startswith('https://'):
                problems.append('%s: tox_url must be https' % where)
            elif not tox.lower().endswith('.tox'):
                problems.append('%s: tox_url must point at a .tox file' % where)
            if not sha:
                problems.append(
                    '%s: tox_url needs a pinned sha256 -- placement installs '
                    'exactly the bytes a curator checked, or it does not '
                    'install at all' % where)
            elif not HEX64.match(sha):
                problems.append('%s: sha256 must be 64 lowercase hex characters' % where)
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                problems.append('%s: bytes must be a positive integer' % where)

        if 'tdp' in row:
            problems.extend(_tdpProblems(where, row.get('tdp')))
            if str(row.get('tox_url', '')).strip():
                problems.append('%s: a row is a tox or a tdp package, not both' % where)

        slug = str(row.get('slug', '')).strip()
        if 'slug' in row and not SLUG.match(slug):
            problems.append('%s: slug must be lowercase words joined by hyphens' % where)
        elif slug:
            if slug in slugs:
                problems.append('%s: slug %s is also tools[%d]' % (where, slug, slugs[slug]))
            slugs[slug] = i
        if 'date' in row and not DATE.match(str(row.get('date', ''))):
            problems.append('%s: date must be YYYY-MM-DD' % where)
        if 'image' in row and not IMAGE.match(str(row.get('image', ''))):
            problems.append('%s: image must be a file name in website/content/'
                            'community/images (png, jpg, webp, gif)' % where)
        if 'platform' in row and row.get('platform') not in PLATFORMS:
            problems.append('%s: platform must be one of %s' % (where, ', '.join(PLATFORMS)))
        if 'draft' in row and not isinstance(row.get('draft'), bool):
            problems.append('%s: draft must be true or false' % where)
        if len(str(row.get('author_license', ''))) > MAX_LICENSE:
            problems.append('%s: author_license is over %d characters; link to it instead'
                            % (where, MAX_LICENSE))

        desc = str(row.get('description', ''))
        if len(desc) > MAX_DESCRIPTION:
            problems.append('%s: description is %d chars, max %d'
                            % (where, len(desc), MAX_DESCRIPTION))

        if name:
            if name.casefold() in seen:
                problems.append('%s: duplicate name (also tools[%d])'
                                % (where, seen[name.casefold()]))
            else:
                seen[name.casefold()] = i
    problems.extend(_familyProblems(doc.get('families'),
                                    {str(t.get('name', '')) for t in tools if isinstance(t, dict)}))
    return problems


def published(doc):
    """What actually goes in the bucket: the curated rows and nothing else.

    The `_comment` block is for whoever edits the file and has no business
    being downloaded by every install on every check. A `draft` row is not
    published at all: it is still being written."""
    return {
        'schema': SCHEMA,
        'intro': str(doc.get('intro', '')),
        'tools': [{k: v for k, v in row.items() if k in ALLOWED and k != 'draft'}
                  for row in doc.get('tools', []) if row.get('draft') is not True],
    }


if __name__ == '__main__':
    import sys
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        doc = load(repo)
    except Exception as e:
        sys.exit('recommendations.json unreadable: %s' % e)
    bad = validate(doc)
    if bad:
        print('%d problem(s):' % len(bad))
        for b in bad:
            print('  ' + b)
        sys.exit(1)
    tools = doc.get('tools', [])
    kinds = [delivery(t) for t in tools]
    print('recommendations.json valid -- %d tool(s): %d tox, %d tdp, %d link-only'
          % (len(tools), kinds.count('tox'), kinds.count('tdp'), kinds.count('link')))
