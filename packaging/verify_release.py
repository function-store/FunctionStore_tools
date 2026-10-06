"""Verify every published artifact matches the manifest's digest.

The failure this exists to catch: a restage rewrites the mutable latest/
alias and the manifest, but release-pinned v<rel>/ objects are immutable
and get skipped, so the manifest promises a digest the versioned path
does not serve and every download is rejected.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = 'https://storage.functionstore.tools/fnstools'
REL = sys.argv[1] if len(sys.argv) > 1 else 'v3.2.0'
STAGED = os.path.join('packaging', 'publish', REL)


def fetch(url):
    r = subprocess.run(['curl', '-s', '--max-time', '90', url],
                       capture_output=True)
    return r.stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def local_sha(name):
    p = os.path.join(STAGED, name + '.tox')
    if not os.path.exists(p):
        return None
    return sha(io.open(p, 'rb').read())


def check(name):
    want = local_sha(name)
    if want is None:
        return (name, 'NO_LOCAL', '', '')
    got_v = sha(fetch('%s/%s/%s.tox' % (BASE, REL, name)))
    got_l = sha(fetch('%s/latest/%s.tox' % (BASE, name)))
    ok = (got_v == want) and (got_l == want)
    return (name, 'ok' if ok else 'MISMATCH', got_v[:12], got_l[:12])


def main():
    m = json.loads(fetch('%s/latest/manifest.json' % BASE).decode('utf-8'))
    pk = m.get('packages')
    if isinstance(pk, list):
        pk = {e.get('name'): e for e in pk if isinstance(e, dict)}
    free = [n for n, e in pk.items()
            if str(e.get('access', 'free') or 'free') == 'free'
            and os.path.exists(os.path.join(STAGED, n + '.tox'))]
    print('release %s -- checking %d free artifacts' % (m.get('release'), len(free)))
    bad = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for name, state, gv, gl in ex.map(check, sorted(free)):
            if state != 'ok':
                bad.append((name, state, gv, gl))
    # The install files matter most: the website's Get button serves
    # latest/FNSTools.tox, and a broken bootstrap strands every new user.
    rails_ok = 0
    for rail, r in sorted((m.get('rails') or {}).items()):
        if not isinstance(r, dict):
            continue
        local = os.path.join('packaging', 'dist', rail)
        if not os.path.exists(local):
            bad.append((rail, 'NO_LOCAL', '', ''))
            continue
        want = sha(io.open(local, 'rb').read())
        if r.get('sha256') and r['sha256'] != want:
            bad.append((rail, 'MANIFEST_DISAGREES', r['sha256'][:12], want[:12]))
            continue
        got_v = sha(fetch('%s/%s/%s' % (BASE, REL, rail)))
        got_l = sha(fetch('%s/latest/%s' % (BASE, rail)))
        if got_v != want or got_l != want:
            bad.append((rail, 'MISMATCH', got_v[:12], got_l[:12]))
        else:
            rails_ok += 1
            print('rail %s v%s matches on both paths' % (rail, r.get('version')))
    if bad:
        print('\n*** %d MISMATCH ***' % len(bad))
        for n, s, gv, gl in bad:
            print('   %-24s %s  versioned=%s latest=%s' % (n, s, gv, gl))
        return 1
    print('all %d match the staged bytes on BOTH the versioned and latest paths' % len(free))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
