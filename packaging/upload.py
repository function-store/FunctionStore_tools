#!/usr/bin/env python3
"""Upload packaging/publish/ to the R2 bucket. Runs on the SHELL, not in TD:

    python3 packaging/upload.py            # sync + refresh latest/ aliases
    python3 packaging/upload.py --dry      # print the plan, upload nothing
    python3 packaging/upload.py --force    # re-upload even existing objects
    python3 packaging/upload.py --prune 3  # also delete all but newest N releases

Immutable (release-pinned) objects already in the bucket are skipped -- a
public HEAD says whether the key exists, and existing means done. Only the
rolling manifest.json is always pushed. So a normal publish uploads the
new release's files once, and a re-run after a flaky connection touches
only what actually failed.

Layout mirrors Stage(): objects land under the `fnstools/` prefix in the
`fnstools` bucket, which is what BASE_URL points at.

CACHE POLICY (the reason this script exists instead of a bare sync):
  * release-pinned files (v*/...) are IMMUTABLE -- their URLs carry the
    release label, so they may cache forever.
  * the rolling manifest.json is the ONE mutable pointer. A CDN caching it
    would silently pin users to an old release, so it ships `no-cache`
    (revalidate every time). Set at upload time by design -- the client
    deliberately does not work around a stale manifest.
  * latest/<file> are HUMAN ALIASES of the current release's files --
    static links for the website and README (short max-age). The
    machinery never reads them: installers and updaters follow the
    manifest's PINNED urls, which is what keeps installs reproducible.
    A stale-cached latest/FNSTools.tox is harmless by construction --
    the bootstrap fetches the rolling manifest at runtime.

RETENTION (--prune N): storage is not the concern (~7 MB per release);
hygiene is. Release labels come from packaging/CHANGELOG.md; all but the
newest N release directories are deleted, enumerating each doomed
release's own pinned manifest for its keys. Never prune a release you
still want a support conversation to be able to reproduce.

Auth is wrangler's login (interactive OAuth); nothing secret lives here or
in any shipped artifact.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BUCKET = 'fnstools'
PREFIX = 'fnstools'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'publish')

RETRIES = 3           # wrangler drops connections now and then; retry, then fail
WORKERS = 8           # concurrent wrangler puts; startup overhead dominates

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


def _publicBase():
    """The bucket's public URL, read off the staged rolling manifest --
    the one place that already knows it."""
    with open(os.path.join(ROOT, 'manifest.json'), encoding='utf-8') as f:
        return json.load(f)['base_url'].rstrip('/')


def _remoteHas(base, key):
    """Does the bucket already hold this object? Immutable objects never
    change, so existence means done. ?exists= dodges any cached 404."""
    url = f'{base}/{key[len(PREFIX) + 1:]}?exists={int(time.time())}'
    # r2.dev 403s the default Python-urllib user-agent (bot filter)
    req = urllib.request.Request(url, method='HEAD',
                                 headers={'User-Agent': 'fnstools-upload/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False       # unsure = upload; a duplicate put is harmless


def _uploadOne(job, base):
    """(state, key, error). Skips immutable objects the bucket already
    has; retries transient connection drops."""
    full, key, cache, ctype = job
    if base and cache == IMMUTABLE and _remoteHas(base, key):
        return '-- ', key, ''
    cmd = ['npx', '--yes', 'wrangler', 'r2', 'object', 'put',
           f'{BUCKET}/{key}', '--file', full, '--remote',
           '--cache-control', cache, '--content-type', ctype]
    for attempt in range(RETRIES):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return 'ok ', key, ''
        time.sleep(2 * (attempt + 1))
    return 'FAIL', key, (r.stderr or r.stdout).strip()[-300:]


def upload(jobs, force=False):
    """Push what the bucket lacks. Release-pinned files are IMMUTABLE, so
    one that already exists remotely is skipped (--force overrides); the
    rolling manifest always uploads.

    Puts run CONCURRENTLY: each is its own wrangler process whose ~5s of
    node/auth startup dwarfs the bytes moved, so a serial pass took
    minutes for megabytes. Workers are processes, not shared state --
    nothing here needs coordinating beyond collecting results."""
    base = None if force else _publicBase()
    failed = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(_uploadOne, j, base) for j in jobs]
        for f in as_completed(futures):
            state, key, err = f.result()
            done += 1
            print(f'[{done}/{len(jobs)}] {state} {key}'
                  + (' (already in bucket)' if state == '-- ' else ''),
                  flush=True)
            if state == 'FAIL':
                failed.append((key, err))
    return failed


LATEST = 'public, max-age=300'


def _currentRelease():
    with open(os.path.join(ROOT, 'manifest.json'), encoding='utf-8') as f:
        return json.load(f)['release']


def latestJobs():
    """Mutable latest/<file> aliases of the CURRENT release's files --
    always re-uploaded (they must overwrite on every release)."""
    rel = _currentRelease()
    rel_dir = os.path.join(ROOT, rel)
    jobs = []
    for fn in sorted(os.listdir(rel_dir)):
        if fn.startswith('.'):
            continue
        ctype = CONTENT_TYPES.get(os.path.splitext(fn)[1].lower(),
                                  'application/octet-stream')
        jobs.append((os.path.join(rel_dir, fn),
                     f'{PREFIX}/latest/{fn}', LATEST, ctype))
    return jobs


def _changelogReleases():
    """Release labels, newest first, from packaging/CHANGELOG.md."""
    import re as _re
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CHANGELOG.md')
    if not os.path.exists(path):
        return []
    return _re.findall(r'^## (v[\d.]+) --', open(path, encoding='utf-8').read(),
                       _re.M)


def _deleteOne(key):
    cmd = ['npx', '--yes', 'wrangler', 'r2', 'object', 'delete',
           f'{BUCKET}/{key}', '--remote']
    r = subprocess.run(cmd, capture_output=True, text=True)
    return ('ok ' if r.returncode == 0 else 'gone'), key


def prune(keep, base):
    """Delete all but the newest `keep` release directories. Keys come
    from each doomed release's OWN pinned manifest (package names differ
    across eras), plus the rails and the manifest itself."""
    labels = _changelogReleases()
    current = _currentRelease()
    if current in labels:
        labels.remove(current)
    labels.insert(0, current)
    doomed = labels[keep:]
    if not doomed:
        print('prune: nothing to prune')
        return
    keys = []
    for rel in doomed:
        names = []
        try:
            url = f'{base}/{rel}/manifest.json?prune={int(time.time())}'
            req = urllib.request.Request(url, headers={'User-Agent': 'fnstools-upload/1.0'})
            with urllib.request.urlopen(req, timeout=20) as r:
                names = [p['name'] for p in json.load(r).get('packages', [])]
        except Exception:
            pass          # manifest already gone; still try the rails
        for n in names:
            keys.append(f'{PREFIX}/{rel}/{n}.tox')
        for rail in ('FNS_Installer.tox', 'FNSTools.tox',
                     'FunctionStore_tools_2025.tox', 'manifest.json'):
            keys.append(f'{PREFIX}/{rel}/{rail}')
    print(f'prune: {len(doomed)} release(s), {len(keys)} object(s): {", ".join(doomed)}')
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for state, key in pool.map(_deleteOne, keys):
            done += 1
            if done % 20 == 0 or state != 'ok ':
                print(f'  [{done}/{len(keys)}] {state} {key}', flush=True)
    print('prune: done')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='upload even what the bucket already has')
    ap.add_argument('--prune', type=int, metavar='N', default=0,
                    help='after syncing, delete all but the newest N releases')
    args = ap.parse_args()
    jobs = plan()
    alias = latestJobs()
    if args.dry:
        for full, key, cache, ctype in jobs + alias:
            print(f'{key}  [{cache}]  ({ctype})')
        print(f'{len(jobs)} objects + {len(alias)} latest aliases')
        sys.exit(0)
    failed = upload(jobs, force=args.force)
    # aliases are mutable: force past the skip-existing check
    failed += upload(alias, force=True)
    if args.prune:
        prune(args.prune, _publicBase())
    if failed:
        for key, err in failed:
            print(f'\nFAILED {key}\n{err}', file=sys.stderr)
        sys.exit(1)
    print(f'\n{len(jobs)} objects + {len(alias)} aliases synced to {BUCKET}/{PREFIX}/')
