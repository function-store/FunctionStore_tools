#!/usr/bin/env python3
"""Are the discovery pins actually answering? Runs on the SHELL, not in TD:

    python3 packaging/check_pins.py           # check the live pins
    python3 packaging/check_pins.py --expect  # also compare against what
                                              # Stage() would emit locally
    python3 packaging/check_pins.py --quiet   # exit code only

WHY THIS EXISTS. Every other guard in this rail checks that the BYTES are
current: Preflight refuses a package whose code is newer than its .tox,
Stage() re-hashes everything it writes, upload.py reads each object back
out of the bucket. None of them ask the one question that matters before
any of that is reachable -- *does the endpoint answer at all*.

That gap is not theoretical. On 2026-08-27 all three pins returned 404:
pin 1 was never published (Stage() had not run since v2.11.2), pin 2's
apex 308-redirected to a host that does not serve the rewrite, and pin 3's
repo did not exist. Nothing in the toolkit would have said so, because the
updater is deliberately built to survive exactly this -- it falls back to
its cached document and carries on quietly. The fallback is correct. The
silence is the problem.

WHAT A DEAD PIN LIST COSTS. The discovery document is the only thing a
shipped component has a hardcoded address for, and it carries the only two
levers that reach an install already in the field:

    minimum_updater   the kill switch -- stops a dangerous updater
    notices           the one channel that reaches every install

Neither exists while the pins are dead, so a bad release cannot be
recalled. That is why this is a BLOCKER and not a warning.

THE PIN LIST IS NOT DUPLICATED HERE. It is parsed out of ExtUpdater.py,
because the shipped component's copy is the only one that matters -- a
second list in this file would drift, and would then be the second place
the answer lives. Same reason the tier map lives only in the Worker.

ACCEPTANCE MIRRORS THE CLIENT. A pin "answers" only if its body parses as
a dict AND names a non-empty endpoints.manifest -- byte for byte the rule
in ExtUpdater._readDiscovery. An error page, a truncated body or a half
document is a FAILED pin, not a new configuration: treating half a
document as success would override a working Baseurl with nothing.

INDEPENDENCE IS MEASURED AFTER REDIRECTS. Three names are not three
origins. Pin 2 is a 200-proxy to pin 1's origin by design, and a redirect
can quietly collapse two more into one, so origins are counted from the
FINAL url each pin resolves to -- which is what turns "three pins" into
the honest number.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

TIMEOUT = 10
UA = 'fnstools-check-pins/1'

# Where the shipped component keeps the list. Parsed, never re-declared.
UPDATER_SRC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir,
    'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')


def pins(src=UPDATER_SRC):
    """DISCOVERY_PINS as the shipped updater declares it.

    Parsed with a regex rather than imported, because importing
    ExtUpdater.py needs TouchDesigner builtins stubbed -- the offline
    suites do that, but this script must run anywhere, including a CI
    runner with no project checkout state.
    """
    with open(src, 'r', encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'DISCOVERY_PINS\s*=\s*\((.*?)\)', text, re.S)
    if not m:
        raise SystemExit('could not find DISCOVERY_PINS in %s' % src)
    found = re.findall(r'''['"](https?://[^'"]+)['"]''', m.group(1))
    if not found:
        raise SystemExit('DISCOVERY_PINS parsed but held no urls')
    return tuple(found)


def usable(doc):
    """The client's own acceptance rule, mirrored exactly.

    ExtUpdater._readDiscovery: a dict whose endpoints.manifest is a
    non-empty string. Anything else is treated as absent.
    """
    if not isinstance(doc, dict):
        return ''
    return str((doc.get('endpoints') or {}).get('manifest', '')).strip()


def probe(url):
    """Fetch one pin. Never raises -- every failure is a result."""
    row = {'url': url, 'final': url, 'status': None, 'ok': False,
           'endpoint': '', 'release': '', 'floor': '', 'notices': 0,
           'why': ''}
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            row['status'] = r.status
            row['final'] = r.url          # after redirects
            body = r.read(65536)
    except urllib.error.HTTPError as e:
        row['status'] = e.code
        row['final'] = getattr(e, 'url', url)
        row['why'] = 'HTTP %d' % e.code
        return row
    except Exception as e:
        row['why'] = '%s: %s' % (type(e).__name__, e)
        return row

    try:
        doc = json.loads(body.decode('utf-8'))
    except Exception as e:
        row['why'] = 'body did not parse as JSON (%s)' % type(e).__name__
        return row

    endpoint = usable(doc)
    if not endpoint:
        row['why'] = 'parsed, but names no endpoints.manifest -- half a document'
        return row

    row['ok'] = True
    row['endpoint'] = endpoint
    row['release'] = str(doc.get('release', ''))
    row['floor'] = str(doc.get('minimum_updater', '') or '')
    row['notices'] = len(doc.get('notices') or [])
    row['doc'] = doc
    return row


def expected():
    """What Stage() would publish right now, for comparison.

    A pin that answers with a STALE document is the failure mode the
    vercel.json rewrite exists to prevent, and it looks perfectly healthy
    from the outside -- so it is worth catching here rather than in a
    support conversation.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    man_path = os.path.join(here, 'manifest.json')
    if not os.path.exists(man_path):
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pub', os.path.join(here, 'publish.py'))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        with open(man_path, 'r', encoding='utf-8') as f:
            return mod._discoveryDoc(json.load(f))
    except Exception:
        return None


def origins(rows):
    """Distinct FINAL origins among the pins that answered."""
    seen = {}
    for r in rows:
        if not r['ok']:
            continue
        p = urlparse(r['final'])
        seen.setdefault('%s://%s' % (p.scheme, p.netloc), []).append(r['url'])
    return seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--expect', action='store_true',
                    help='also compare each answer against what Stage() '
                         'would emit from the local manifest')
    ap.add_argument('--quiet', action='store_true', help='exit code only')
    ap.add_argument('--min', type=int, default=1, metavar='N',
                    help='fail unless at least N pins answer usably '
                         '(default 1)')
    args = ap.parse_args(argv)

    urls = pins()
    rows = [probe(u) for u in urls]
    live = [r for r in rows if r['ok']]
    want = expected() if args.expect else None

    stale = []
    if want is not None:
        for r in live:
            if r.get('doc') != want:
                stale.append(r)

    if not args.quiet:
        print('\n--- discovery pins --------------------------------------')
        for i, r in enumerate(rows, 1):
            mark = 'ok  ' if r['ok'] else 'DEAD'
            print('  %s pin %d  %s' % (mark, i, r['url']))
            if r['final'] != r['url']:
                print('           -> redirected to %s' % r['final'])
            if r['ok']:
                bits = ['endpoint=%s' % r['endpoint']]
                if r['release']:
                    bits.append('release=%s' % r['release'])
                bits.append('floor=%s' % (r['floor'] or 'none'))
                if r['notices']:
                    bits.append('notices=%d' % r['notices'])
                print('           %s' % '  '.join(bits))
            else:
                print('           %s' % (r['why'] or 'no answer'))

        org = origins(rows)
        print('  %-4s %d pin(s) answering, %d independent origin(s)'
              % ('', len(live), len(org)))
        for o, us in org.items():
            if len(us) > 1:
                print('       note   %d pins share the origin %s -- one '
                      'outage takes them all' % (len(us), o))

        if stale:
            for r in stale:
                print('  BLOCK  pin serves a document that is NOT what '
                      'Stage() would publish: %s' % r['url'])
        if len(live) < args.min:
            print('  BLOCK  fewer than %d pin(s) answering -- the kill '
                  'switch and notices cannot reach any install' % args.min)
        elif len(live) < len(urls):
            print('  warn   %d of %d pins dead -- the fallback chain is '
                  'thinner than it looks' % (len(urls) - len(live), len(urls)))
        if len(live) >= args.min and not stale:
            print('  ok     discovery is reachable')
        print('---------------------------------------------------------\n')

    return 0 if (len(live) >= args.min and not stale) else 1


if __name__ == '__main__':
    sys.exit(main())
