"""Mirror FOREIGN packages into packaging/dist/ and pin them in the lock.

A foreign package (docs/ForeignPackages.md) is a catalog entry with a
`source` block: its bytes and version are owned upstream, by another repo
and another release rail. This script is the ONLY place that talks to that
upstream. It runs on the shell -- never inside TouchDesigner -- so no
network I/O ever lands on TD's main thread; build_manifest.Build() reads
the lock this writes and nothing else.

    python packaging/foreign_sync.py              # every foreign entry
    python packaging/foreign_sync.py TDXMap       # just these
    python packaging/foreign_sync.py --check      # report, fetch nothing

Per entry, in order:
  1. GET `source.manifest` (JSON). Two shapes are understood:
       flat    {version|latest, url, sha256, notes_url?}       (TDXMap's)
       ours    {packages: [{name, version, artifact: {url, sha256}}]}
               with `source.package` naming the row (defaults to the entry
               name)
  2. Download the tox to packaging/dist/<Name>.tox.part, verify its
     sha256 against the manifest's, then rename into place. A mismatch
     leaves the previous dist file untouched and is reported as a
     failure -- the pin is the whole safety argument.
  3. Record {version, sha256, url, notes_url, fetched_at} under the entry's
     name in packaging/foreign.lock.json. The lock is committed: it is what
     the manifest build reads, and git shows exactly which upstream
     version each release mirrored.

Exit status is non-zero when any entry failed, so a CI or CMS caller can
tell. stdlib only, so it runs with any python on the PATH.
"""

import hashlib
import json
import os
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_DIR = os.path.join(REPO, 'packaging')
CATALOG = os.path.join(PKG_DIR, 'catalog.json')
LOCK = os.path.join(PKG_DIR, 'foreign.lock.json')
DIST = os.path.join(PKG_DIR, 'dist')
TIMEOUT = 30
UA = 'fnstools-foreign-sync/1'


def _readJson(path, default):
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _fetch(url):
    """Bytes at `url`. https:// and file:// (tests, local mirrors)."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def _sha256Bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha256File(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def foreignEntries(catalog):
    return {n: m for n, m in (catalog.get('packages') or {}).items()
            if isinstance(m, dict) and isinstance(m.get('source'), dict)}


def resolve(name, source, doc):
    """Pick (version, url, sha256, notes_url, notes) out of an upstream
    manifest document. Raises ValueError with the reason when it cannot."""
    if not isinstance(doc, dict):
        raise ValueError('upstream manifest is not a JSON object')
    if isinstance(doc.get('assets'), list) and doc.get('tag_name'):
        # a GitHub release (source.manifest points at
        # .../repos/<owner>/<repo>/releases/latest): the tag is the version,
        # the asset named by source.tox is the artifact, and the asset's
        # `digest` (sha256:<hex>, served by GitHub for every uploaded
        # asset) is the pin. A release without it is refused like a flat
        # manifest without sha256.
        want = str(source.get('tox', '') or '').strip()
        if not want:
            raise ValueError('a GitHub release upstream needs source.tox to name the asset')
        tag = str(doc.get('tag_name') or '').strip()
        asset = next((a for a in doc['assets']
                      if isinstance(a, dict) and a.get('name') == want), None)
        if asset is None:
            raise ValueError('release %s has no asset %r' % (tag, want))
        digest = str(asset.get('digest', '') or '').strip().lower()
        sha = digest.split(':', 1)[1] if digest.startswith('sha256:') else ''
        if len(sha) != 64:
            raise ValueError('release asset %s carries no sha256 digest -- refusing '
                             'to mirror unpinned bytes' % want)
        url = str(asset.get('browser_download_url', '') or '').strip()
        if not url:
            raise ValueError('release asset %s has no download url' % want)
        version = tag[1:] if tag[:1] in ('v', 'V') and tag[1:2].isdigit() else tag
        if not version:
            raise ValueError('release carries no tag')
        notes = str(doc.get('body', '') or '').strip()
        return (version, url, sha, str(doc.get('html_url', '') or '').strip(),
                notes[:2000])
    if isinstance(doc.get('packages'), list):
        want = str(source.get('package', '') or name)
        row = next((p for p in doc['packages']
                    if isinstance(p, dict) and p.get('name') == want), None)
        if row is None:
            raise ValueError('upstream manifest has no package %r' % want)
        art = row.get('artifact') or {}
        return (str(row.get('version', '') or ''), str(art.get('url', '') or ''),
                str(art.get('sha256', '') or '').lower(),
                str(row.get('help_url', '') or ''),
                str(row.get('whatsnew', '') or ''))
    version = str(doc.get('version') or doc.get('latest') or '').strip()
    url = str(doc.get('url', '') or '').strip()
    if not url and source.get('tox'):
        # a manifest that names no url: the tox sits beside it
        base = str(source.get('manifest', '')).rsplit('/', 1)[0]
        url = base + '/' + str(source['tox'])
    sha = str(doc.get('sha256', '') or '').strip().lower()
    notes_url = str(doc.get('notes_url', '') or '').strip()
    if not version:
        raise ValueError('upstream manifest carries no version')
    if not url:
        raise ValueError('upstream manifest carries no artifact url')
    if len(sha) != 64:
        raise ValueError('upstream manifest carries no sha256 -- refusing '
                         'to mirror unpinned bytes')
    return version, url, sha, notes_url, ''


def syncOne(name, meta, lock, check=False, log=print):
    """Mirror one entry. Returns (ok, message). Mutates `lock` on success."""
    source = meta['source']
    murl = str(source.get('manifest', '') or '').strip()
    if not murl:
        return False, '%s: source has no manifest url' % name
    try:
        doc = json.loads(_fetch(murl).decode('utf-8'))
        version, url, sha, notes_url, notes = resolve(name, source, doc)
    except Exception as e:
        return False, '%s: upstream manifest unusable (%s)' % (name, e)
    prev = lock.get(name) or {}
    dest = os.path.join(DIST, name + '.tox')
    have = _sha256File(dest) if os.path.exists(dest) else ''
    if have == sha and prev.get('sha256') == sha and prev.get('version') == version:
        log('  %-22s v%s  unchanged' % (name, version))
        return True, ''
    if check:
        log('  %-22s v%s  -> would fetch (lock: v%s)'
            % (name, version, prev.get('version', '-')))
        return True, ''
    if have != sha:
        try:
            data = _fetch(url)
        except Exception as e:
            return False, '%s: download failed (%s)' % (name, e)
        got = _sha256Bytes(data)
        if got != sha:
            return False, ('%s: sha256 mismatch -- manifest says %s..., '
                           'bytes are %s... (dist left untouched)'
                           % (name, sha[:12], got[:12]))
        os.makedirs(DIST, exist_ok=True)
        part = dest + '.part'
        with open(part, 'wb') as f:
            f.write(data)
        os.replace(part, dest)
        log('  %-22s v%s  fetched %d bytes' % (name, version, len(data)))
    else:
        log('  %-22s v%s  bytes current, lock updated' % (name, version))
    lock[name] = {
        'version': version,
        'sha256': sha,
        'url': url,
        'notes_url': notes_url,
        'notes': notes,
        'fetched_at': int(time.time()),
    }
    return True, ''


def sync(names=None, check=False, log=print):
    """Sync every foreign entry (or `names`). Returns a report dict."""
    catalog = _readJson(CATALOG, {})
    entries = foreignEntries(catalog)
    if names:
        unknown = [n for n in names if n not in entries]
        if unknown:
            return {'ok': False, 'failed': [
                '%s: not a foreign package in catalog.json' % n
                for n in unknown], 'synced': []}
        entries = {n: entries[n] for n in names}
    lock_doc = _readJson(LOCK, {'schema': 1, 'packages': {}})
    lock = lock_doc.setdefault('packages', {})
    # drop lock rows whose catalog entry is gone -- the lock mirrors the
    # catalog, never outlives it
    for stale in [n for n in list(lock) if n not in foreignEntries(catalog)]:
        del lock[stale]
    failed, synced = [], []
    log('foreign sync: %d entr%s' % (len(entries), 'y' if len(entries) == 1 else 'ies'))
    for name, meta in sorted(entries.items(), key=lambda kv: kv[0].lower()):
        ok, msg = syncOne(name, meta, lock, check=check, log=log)
        if ok:
            synced.append(name)
        else:
            failed.append(msg)
            log('  ' + msg)
    if not check:
        with open(LOCK, 'w', encoding='utf-8') as f:
            json.dump(lock_doc, f, indent=1)
            f.write('\n')
    return {'ok': not failed, 'failed': failed, 'synced': synced,
            'lock': LOCK}


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    r = sync(names=args or None, check='--check' in sys.argv)
    if r['failed']:
        print('FAILED:')
        for m in r['failed']:
            print('  ' + m)
    sys.exit(0 if r['ok'] else 1)
