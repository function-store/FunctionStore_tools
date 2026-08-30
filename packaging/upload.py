#!/usr/bin/env python3
"""Upload packaging/publish/ to the R2 bucket. Runs on the SHELL, not in TD:

    python3 packaging/upload.py            # sync + refresh latest/ aliases
    python3 packaging/upload.py --dry      # print the plan, upload nothing
    python3 packaging/upload.py --force    # re-upload even existing objects
    python3 packaging/upload.py --prune 3  # also delete all but newest N releases
    python3 packaging/upload.py --prune 3 --prune-only        # prune, no sync
    python3 packaging/upload.py --prune 3 --prune-only --dry  # preview the prune
    python3 packaging/upload.py --recommendations   # just the community list

Immutable (release-pinned) objects already in the bucket are skipped -- a
public HEAD says whether the key exists, and existing means done. Only the
rolling manifest.json is always pushed. So a normal publish uploads the
new release's files once, and a re-run after a flaky connection touches
only what actually failed.

EVERY OBJECT ACTUALLY UPLOADED IS READ BACK AND HASHED. wrangler's exit
code says the request was accepted, not that the bucket holds these bytes;
a truncated or half-written object exits 0 and is otherwise discovered by
a user. A mismatch fails the run and prints its own rollback command.

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
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# On Windows npx is npx.cmd: CreateProcess cannot resolve the bare name
# (the shell can, which is why the same command works in a terminal), so
# every subprocess call uses the which()-resolved path.
NPX = shutil.which('npx') or 'npx'

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
            # Staged for a human to commit into the pin-3 repo, never an
            # object in this bucket (it would be a fourth copy nothing reads).
            if rel.startswith('pin3-'):
                continue
            # The discovery document is the ONE thing shipped clients have a
            # hardcoded address for, so a cached copy pins the whole fleet to
            # a dead endpoint and defeats its own kill switch. It revalidates
            # every time, exactly like the rolling manifest.
            # A signature ages exactly like its document: a CDN serving a
            # fresh manifest with yesterday's cached .sig would fail
            # verification on every install at once.
            cache = (ROLLING if rel in ('manifest.json', 'manifest.json.sig',
                                        '.well-known/fnstools.json',
                                        '.well-known/fnstools.json.sig')
                     else IMMUTABLE)
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


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _isGatedKey(key):
    """Objects under the gated prefix are (correctly) unreadable over the
    public rail, so their existence and read-back checks must go through
    wrangler's authenticated path instead -- a public 403 on these is the
    privacy working, not the upload failing."""
    return key.startswith(f'{PREFIX}/plus/')


def _remoteShaAuth(key):
    """SHA-256 of a gated object via authenticated wrangler get, or None."""
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '.gated-readback.tmp')
    cmd = [NPX, '--yes', 'wrangler', 'r2', 'object', 'get',
           f'{BUCKET}/{key}', '--file', tmp, '--remote']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(tmp):
            return None
        return _sha256(tmp)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _remoteSha(base, key):
    """SHA-256 of what the bucket actually serves for `key`, or None if it
    cannot be fetched. Cache-busted: a CDN copy of the previous bytes would
    make this check pass on exactly the release it exists to catch."""
    url = f'{base}/{key[len(PREFIX) + 1:]}?verify={int(time.time())}'
    req = urllib.request.Request(url, headers={'User-Agent': 'fnstools-upload/1.0',
                                               'Cache-Control': 'no-cache'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                return None
            h = hashlib.sha256()
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                h.update(chunk)
            return h.hexdigest()
    except Exception:
        return None


def _rollback(key, full):
    return (f'npx wrangler r2 object put {BUCKET}/{key} '
            f'--file {full} --remote')


CANARY_KEY = f'{PREFIX}/plus/.privacy-canary'


def verifyPlusPrivate(base):
    """Prove the gated plus/ prefix is NOT publicly readable, or fail the run.

    This is the one deployment step whose failure is invisible
    (worker/README.md step 5): the bucket's public access covering plus/
    breaks nothing -- downloads work, hashes match -- the only symptom is
    that paying is optional. So the check has to be an assertion, not a
    checklist item: place one harmless canary object under plus/ and
    require that the PUBLIC rail refuses to serve it. The Worker streams
    gated artifacts through its own binding, so the canary never affects a
    real download either way.

    Returns '' when private, or a problem sentence for the failure list."""
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.plus-canary')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write('fnstools gated-prefix canary -- if you can read this over the '
                'public rail, the plus/ prefix is misconfigured as public\n')
    cmd = [NPX, '--yes', 'wrangler', 'r2', 'object', 'put',
           f'{BUCKET}/{CANARY_KEY}', '--file', tmp, '--remote']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.remove(tmp)
    if r.returncode != 0:
        return ('could not place the plus/ privacy canary: '
                + (r.stderr or r.stdout).strip()[-200:])
    url = f'{base}/plus/.privacy-canary?verify={int(time.time())}'
    req = urllib.request.Request(url, headers={'User-Agent': 'fnstools-upload/1.0',
                                               'Cache-Control': 'no-cache'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            served = resp.status == 200
    except Exception as e:
        if getattr(e, 'code', None) in (401, 403, 404):
            return ''          # refused without a token: exactly right
        return f'could not probe plus/ privacy ({e}) -- verify it by hand'
    if served:
        return ('plus/ IS PUBLICLY READABLE -- the entitlement gate is '
                "decorative. Exclude the plus/ prefix from the bucket's "
                'public access (worker/README.md, step 5).')
    return ''


def _uploadOne(job, base, skip_existing=True):
    """(state, key, error). Skips immutable objects the bucket already
    has; retries transient connection drops.

    VERIFIES WHAT LANDED. wrangler's exit code says the request was
    accepted, not that the bucket now holds these bytes -- a truncated or
    half-written object exits 0 and is discovered by a user. So every
    object we actually put is re-fetched and hashed against the local
    file, and a mismatch is a FAIL carrying its own rollback command.
    Skipped objects are not re-verified: they were verified when they were
    uploaded, and release-pinned keys are immutable.
    """
    full, key, cache, ctype = job
    gated = _isGatedKey(key)
    if (skip_existing and base and cache == IMMUTABLE and not gated
            and _remoteHas(base, key)):
        return '-- ', key, ''
    if skip_existing and gated and _remoteShaAuth(key) == _sha256(full):
        return '-- ', key, ''      # verified by hash, not mere existence
    cmd = [NPX, '--yes', 'wrangler', 'r2', 'object', 'put',
           f'{BUCKET}/{key}', '--file', full, '--remote',
           '--cache-control', cache, '--content-type', ctype]
    for attempt in range(RETRIES):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode == 0:
            if not base:
                return 'ok ', key, ''      # no public base known: nothing to read back
            want = _sha256(full)
            got = _remoteShaAuth(key) if gated else _remoteSha(base, key)
            if got == want:
                return 'ok ', key, ''
            if got is None:
                # Uploaded but unreadable. Do NOT retry the put -- a second
                # put cannot fix a read path, and a green line here would be
                # a claim we have not checked.
                return 'FAIL', key, ('uploaded but could not be read back for '
                                     'verification\n  ' + _rollback(key, full))
            return 'FAIL', key, (f'BYTES DIFFER after upload\n'
                                 f'  local  {want}\n  remote {got}\n'
                                 f'  {_rollback(key, full)}')
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
    # base is needed for BOTH the skip-existing check and the read-back
    # verification, so --force must only disable the former.
    base = _publicBase()
    failed = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(_uploadOne, j, base, not force) for j in jobs]
        for f in as_completed(futures):
            state, key, err = f.result()
            done += 1
            print(f'[{done}/{len(jobs)}] {state} {key}'
                  + (' (already in bucket)' if state == '-- ' else ''),
                  flush=True)
            if state == 'FAIL':
                failed.append((key, err))
    return failed


def uploadRecommendations(dry=False):
    """Publish packaging/recommendations.json on its own.

    Deliberately NOT part of a release. The whole point of the list is that
    adding -- and far more importantly REMOVING -- a recommendation reaches
    every install in minutes without cutting a release. A removal that has
    to wait for a release is not a safety valve.

    It ships `no-cache` for the same reason the rolling manifest does: it is
    a mutable pointer, and a CDN holding yesterday's copy would keep
    recommending something we pulled.

    Validated before it goes: this path has no build step in which a bad row
    would be noticed, so the publish IS the review.
    """
    import recommendations as rec
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    doc = rec.load(repo)
    problems = rec.validate(doc)
    if problems:
        print('recommendations.json has %d problem(s) -- nothing uploaded:'
              % len(problems), file=sys.stderr)
        for b in problems:
            print('  ' + b, file=sys.stderr)
        return 1

    body = json.dumps(rec.published(doc), indent=1) + chr(10)
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '.recommendations.upload.json')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(body)
    key = f'{PREFIX}/{rec.FILENAME}'
    n = len(doc.get('tools', []))
    if dry:
        print(f'{key}  [{ROLLING}]  ({n} tool(s), {len(body)} bytes)')
        os.remove(tmp)
        return 0
    try:
        # BASE_URL is not in this script; read it off the staged manifest when
        # there is one, so the upload is still read-back verified. Without a
        # staged tree we upload unverified rather than refuse -- this path
        # must work when no release has been staged.
        base = None
        try:
            base = _publicBase()
        except Exception:
            print('note: no staged manifest, so this upload is not read-back verified')
        state, _key, err = _uploadOne((tmp, key, ROLLING, 'application/json'),
                                      base, skip_existing=False)
    finally:
        os.remove(tmp)
    if state == 'FAIL':
        print('FAILED %s%s%s' % (key, chr(10), err), file=sys.stderr)
        return 1
    print(f'ok  {key}  ({n} tool(s))')
    return 0


LATEST = 'public, max-age=300'


def _currentRelease():
    with open(os.path.join(ROOT, 'manifest.json'), encoding='utf-8') as f:
        return json.load(f)['release']


def latestJobs():
    """Mutable latest/<file> aliases of the CURRENT release's files --
    always re-uploaded (they must overwrite on every release)."""
    rel = _currentRelease()
    rel_dir = os.path.join(ROOT, rel)
    # Only the PUBLIC release directory feeds latest/: gated artifacts
    # stage under plus/<release>/ and must never gain a public alias --
    # an alias would be the paid bytes on the free rail.
    jobs = []
    for fn in sorted(os.listdir(rel_dir)):
        if fn.startswith('.'):
            continue
        # The discovery document has exactly two live addresses (pins 1-2).
        # A latest/ alias would be a third that looks pinnable and is not.
        if fn == 'fnstools.json':
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
    cmd = [NPX, '--yes', 'wrangler', 'r2', 'object', 'delete',
           f'{BUCKET}/{key}', '--remote']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return ('ok ' if r.returncode == 0 else 'gone'), key


def prune(keep, base, dry=False):
    """Delete all but the newest `keep` release directories. Keys come
    from each doomed release's OWN pinned manifest (package names differ
    across eras), plus the rails and the manifest itself. `dry` prints
    the full plan -- releases and every key -- and deletes nothing."""
    labels = _changelogReleases()
    current = _currentRelease()
    if current in labels:
        labels.remove(current)
    labels.insert(0, current)
    doomed = labels[keep:]
    kept = labels[:keep]
    print('prune: keeping %d release(s): %s' % (len(kept), ', '.join(kept)))
    if not doomed:
        print('prune: nothing to prune')
        return
    keys = []
    for rel in doomed:
        pkgs = []
        try:
            url = f'{base}/{rel}/manifest.json?prune={int(time.time())}'
            req = urllib.request.Request(url, headers={'User-Agent': 'fnstools-upload/1.0'})
            with urllib.request.urlopen(req, timeout=20) as r:
                pkgs = json.load(r).get('packages', [])
        except Exception:
            pass          # manifest already gone; still try the rails
        for p in pkgs:
            # gated rows live under the plus/ prefix; the manifest's own
            # URL says which side each artifact is on
            gated = '/plus/' in str((p.get('artifact') or {}).get('url', ''))
            keys.append(f'{PREFIX}/plus/{rel}/{p["name"]}.tox' if gated
                        else f'{PREFIX}/{rel}/{p["name"]}.tox')
        for rail in ('FNS_Installer.tox', 'FNSTools.tox',
                     'FunctionStore_tools_2025.tox', 'manifest.json',
                     'fnstools.json'):
            keys.append(f'{PREFIX}/{rel}/{rail}')
    print(f'prune: {len(doomed)} release(s), {len(keys)} object(s): {", ".join(doomed)}')
    if dry:
        for key in keys:
            print(f'  would delete {key}')
        print('prune: DRY RUN -- nothing deleted')
        return
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
    ap.add_argument('--recommendations', action='store_true',
                    help='publish packaging/recommendations.json alone and exit '
                         '(no release needed)')
    ap.add_argument('--prune', type=int, metavar='N', default=0,
                    help='after syncing, delete all but the newest N releases')
    ap.add_argument('--prune-only', action='store_true',
                    help='skip the sync entirely and just prune (needs '
                         '--prune N; add --dry to preview the deletions)')
    args = ap.parse_args()
    if args.recommendations:
        sys.exit(uploadRecommendations(dry=args.dry))
    if args.prune_only:
        if not args.prune:
            sys.exit('--prune-only needs --prune N')
        prune(args.prune, _publicBase(), dry=args.dry)
        sys.exit(0)
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
    problem = verifyPlusPrivate(_publicBase())
    if problem:
        failed.append((CANARY_KEY, problem))
    else:
        print('plus/ privacy probe: private (public rail refuses the canary)')
    if args.prune:
        prune(args.prune, _publicBase())
    if failed:
        for key, err in failed:
            print(f'\nFAILED {key}\n{err}', file=sys.stderr)
        sys.exit(1)
    print(f'\n{len(jobs)} objects + {len(alias)} aliases synced to {BUCKET}/{PREFIX}/')
