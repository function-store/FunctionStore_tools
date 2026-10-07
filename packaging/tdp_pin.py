"""Check a tdp package for a community highlight: its module, its toxes,
and what it installs today.

docs/CommunityHighlights.md, section 4. Nothing is pinned (owner,
2026-09-27): a `tdp` row names the package and the installer takes its
latest release. This is the curator's look before the row goes up:

  * WHAT IT RESOLVES TO: `uv pip compile --universal --only-binary :all:`
    for TouchDesigner's Python (3.11), with `also` (what it imports without
    declaring) added.
  * A PACKAGE TOUCHDESIGNER BUNDLES IS REFUSED. A second numpy or opencv in
    the project's venv is a known crash class. The bundled set is read from
    the TouchDesigner install on this machine (its site-packages), plus a
    seed for what ships without dist-info (opencv as cv2, pyparsing). The
    installer runs the same check on its own dry run, at install time.
  * THE MODULE AND THE TOX are read from the wheel, not guessed: the
    top-level module that defines `ToxFile` or `_ToxFiles`, and the keys of
    `_ToxFiles` when there are several toxes.

Shell only (the CMS calls it): stdlib plus `uv` on PATH.

    python packaging/tdp_pin.py tdp-QrCodeCOMP [--also tdp-touchutilcollection]
"""

import glob
import io
import json
import os
import re
import subprocess
import sys
import urllib.request
import zipfile

TD_PYTHON = '3.11'

# Shipped by TouchDesigner without a dist-info folder, or under another
# import name; a dist-info scan alone misses them. Kept identical to the
# updater's copy (ExtUpdater.TD_BUNDLED_SEED); tests/test_community_tdp.py
# holds the two together.
TD_BUNDLED_SEED = ('numpy', 'opencv-python', 'opencv-contrib-python',
                   'opencv-python-headless', 'opencv-contrib-python-headless',
                   'pyparsing', 'pyyaml', 'requests', 'attrs', 'pip')


def canon(name):
    """PEP 503: `tdp-TauCeti`, `tdp_tauceti` and `TDP.TauCeti` are one name."""
    return re.sub(r'[-_.]+', '-', str(name)).lower()


def parse_lock(text):
    """Logical lock lines from `uv pip compile` output: continuations joined,
    comments dropped, whitespace collapsed."""
    out, cur = [], ''
    for raw in str(text or '').splitlines():
        line = re.sub(r'\s+#.*$', '', raw).strip()
        if not line or line.startswith('#'):
            continue
        cont = line.endswith('\\')
        cur = (cur + ' ' + (line[:-1] if cont else line)).strip()
        if not cont:
            out.append(re.sub(r'\s+', ' ', cur))
            cur = ''
    if cur:
        out.append(re.sub(r'\s+', ' ', cur))
    return out


def lock_names(lock):
    names = []
    for line in lock:
        m = re.match(r'^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)', line)
        if m:
            names.append(canon(m.group(1)))
    return names


def td_site_packages():
    """TouchDesigner's own site-packages on this machine: FNS_TD_SITE_PACKAGES,
    else the newest Windows install."""
    env = os.environ.get('FNS_TD_SITE_PACKAGES')
    if env:
        return env
    found = sorted(glob.glob('C:/Program Files/Derivative/TouchDesigner*/bin/Lib/site-packages'))
    return found[-1].replace('\\', '/') if found else None


def bundled_names(site_dir):
    names = {canon(n) for n in TD_BUNDLED_SEED}
    if site_dir and os.path.isdir(site_dir):
        for entry in os.listdir(site_dir):
            m = re.match(r'^(.+?)-\d[^-]*\.dist-info$', entry)
            if m:
                names.add(canon(m.group(1)))
    return names


def _get_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def resolve(package, also=()):
    """What the package installs today, as `name==version` lines. `also`:
    what it imports without declaring (tdp-TauCeti imports
    touchutilcollection without listing it)."""
    reqs = [package] + [str(a).strip() for a in also if str(a).strip()]
    out = subprocess.run(
        ['uv', 'pip', 'compile', '-', '--universal', '--python-version', TD_PYTHON,
         '--only-binary', ':all:', '--no-header', '--no-annotate', '-q'],
        input='\n'.join(reqs) + '\n', capture_output=True, text=True, timeout=300)
    if out.returncode != 0:
        raise RuntimeError('uv could not resolve %s: %s'
                           % (package, (out.stderr or out.stdout).strip()[-600:]))
    return parse_lock(out.stdout)


def inspect_wheel(files):
    """(module, tox keys, single) from the wheel's top-level packages."""
    wheels = [f for f in files if f.get('packagetype') == 'bdist_wheel']
    if not wheels:
        raise RuntimeError('no wheel on PyPI for this version')
    wheels.sort(key=lambda f: ('none-any' not in f['filename'], f['filename']))
    with urllib.request.urlopen(wheels[0]['url'], timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    tops = []
    for n in z.namelist():
        if n.endswith('.dist-info/top_level.txt'):
            tops = [t.strip() for t in z.read(n).decode('utf-8').splitlines() if t.strip()]
    if not tops:
        tops = sorted({n.split('/')[0] for n in z.namelist() if n.endswith('/__init__.py')})
    for mod in tops:
        try:
            src = z.read('%s/__init__.py' % mod).decode('utf-8', 'replace')
        except KeyError:
            continue
        keys = []
        m = re.search(r'_ToxFiles\s*=\s*\{(.*?)\}', src, re.S)
        if m:
            keys = re.findall(r'''["']([A-Za-z_]\w*)["']\s*:''', m.group(1))
        single = re.search(r'^\s*ToxFile\s*=', src, re.M) is not None
        if single or keys:
            return mod, keys, single
    raise RuntimeError('no top-level module defines ToxFile or _ToxFiles (%s)' % ', '.join(tops))


def check(package, site_dir=None, also=()):
    meta = _get_json('https://pypi.org/pypi/%s/json' % package)
    name = meta['info']['name']
    version = meta['info']['version']
    files = _get_json('https://pypi.org/pypi/%s/%s/json' % (package, version))['urls']
    module, keys, single = inspect_wheel(files)
    resolves = [line.split(' ;')[0].strip() for line in resolve(name, also)]
    site_dir = site_dir or td_site_packages()
    clash = sorted(set(lock_names(resolves)) & bundled_names(site_dir))
    if clash:
        raise RuntimeError('refused: it installs %s, which TouchDesigner ships itself; '
                           'a second copy in the venv can crash TD' % ', '.join(clash))
    return {'package': name, 'version': version, 'module': module,
            'toxes': keys, 'single': single, 'resolves': resolves,
            'td_site_packages': site_dir}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('package')
    ap.add_argument('--also', action='append', default=[],
                    help='a requirement the package needs but does not declare (repeatable)')
    ap.add_argument('--json', action='store_true', help='print the result as JSON')
    a = ap.parse_args()
    try:
        r = check(a.package, also=a.also)
    except Exception as e:
        if a.json:
            print(json.dumps({'error': str(e)}))
        else:
            print('error: %s' % e, file=sys.stderr)
        sys.exit(1)
    if a.json:
        print(json.dumps(r))
    else:
        print('%s %s  module %s  toxes %s  installs %s'
              % (r['package'], r['version'], r['module'], r['toxes'] or 'ToxFile', ', '.join(r['resolves'])))
