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
"""

import json
import os
import re

FILENAME = 'recommendations.json'
SCHEMA = 1

REQUIRED = ('name', 'author', 'url')
OPTIONAL = ('author_url', 'description', 'category', 'note',
            # Placement. Present together or not at all -- see below.
            'tox_url', 'sha256', 'bytes', 'pinned_at')
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
    return problems


def published(doc):
    """What actually goes in the bucket: the curated rows and nothing else.

    The `_comment` block is for whoever edits the file and has no business
    being downloaded by every install on every check."""
    return {
        'schema': SCHEMA,
        'intro': str(doc.get('intro', '')),
        'tools': [{k: v for k, v in row.items() if k in ALLOWED}
                  for row in doc.get('tools', [])],
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
    n = sum(1 for t in tools if installable(t))
    print('recommendations.json valid -- %d tool(s), %d placeable, %d link-only'
          % (len(tools), n, len(tools) - n))
