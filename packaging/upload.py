#!/usr/bin/env python3
"""Upload packaging/publish/ to the R2 bucket. Runs on the SHELL, not in TD:

    python3 packaging/upload.py            # upload everything staged
    python3 packaging/upload.py --dry      # print the plan, upload nothing

Layout mirrors Stage(): objects land under the `fnstools/` prefix in the
`fnstools` bucket, which is what BASE_URL points at.

CACHE POLICY (the reason this script exists instead of a bare sync):
  * release-pinned files (v*/...) are IMMUTABLE -- their URLs carry the
    release label, so they may cache forever.
  * the rolling manifest.json is the ONE mutable pointer. A CDN caching it
    would silently pin users to an old release, so it ships `no-cache`
    (revalidate every time). Set at upload time by design -- the client
    deliberately does not work around a stale manifest.

Auth is wrangler's login (interactive OAuth); nothing secret lives here or
in any shipped artifact.
"""

import argparse
import os
import subprocess
import sys

BUCKET = 'fnstools'
PREFIX = 'fnstools'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'publish')

IMMUTABLE = 'public, max-age=31536000, immutable'
ROLLING = 'no-cache'

CONTENT_TYPES = {
    '.json': 'application/json',
    '.tox': 'application/octet-stream',
    '.html': 'text/html',
    '.js': 'text/javascript',
}


def plan():
    if not os.path.isdir(ROOT):
        sys.exit(f'nothing staged: {ROOT} does not exist -- run Stage() first')
    jobs = []
    for dirpath, _dirs, files in os.walk(ROOT):
        for fn in sorted(files):
            if fn.startswith('.'):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, '/')
            cache = ROLLING if rel == 'manifest.json' else IMMUTABLE
            ctype = CONTENT_TYPES.get(os.path.splitext(fn)[1].lower(),
                                      'application/octet-stream')
            jobs.append((full, f'{PREFIX}/{rel}', cache, ctype))
    return jobs


def upload(jobs):
    failed = []
    for i, (full, key, cache, ctype) in enumerate(jobs, 1):
        cmd = ['npx', '--yes', 'wrangler', 'r2', 'object', 'put',
               f'{BUCKET}/{key}', '--file', full, '--remote',
               '--cache-control', cache, '--content-type', ctype]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0
        print(f'[{i}/{len(jobs)}] {"ok " if ok else "FAIL"} {key}')
        if not ok:
            failed.append((key, (r.stderr or r.stdout).strip()[-300:]))
    return failed


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()
    jobs = plan()
    if args.dry:
        for full, key, cache, ctype in jobs:
            print(f'{key}  [{cache}]  ({ctype})')
        print(f'{len(jobs)} objects')
        sys.exit(0)
    failed = upload(jobs)
    if failed:
        for key, err in failed:
            print(f'\nFAILED {key}\n{err}', file=sys.stderr)
        sys.exit(1)
    print(f'\n{len(jobs)} objects uploaded to {BUCKET}/{PREFIX}/')
