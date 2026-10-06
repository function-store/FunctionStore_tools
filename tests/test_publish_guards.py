"""Offline test of publish.Stage()'s release guards.

Runs outside TouchDesigner: publish.py is loaded with the TD builtins it
touches stubbed, against a temporary repo tree. Covers the two guards that
decide whether a release may be staged at all --

  * the BUMP guard (pre-existing): a new release that moves no version
  * the REMOVED guard (2026-08-27): a release that silently drops a package
    the previous one published

-- because both fail in the same direction: they let a release through that
looks healthy and reaches installs wrong.

Run it from anywhere:

    python tests/test_publish_guards.py
"""
import json
import os
import shutil
import sys
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(_ROOT, 'packaging', 'publish.py')

FAILURES = []


def check(label, cond, detail=''):
    if cond:
        print(f'  ok   {label}')
    else:
        print(f'  FAIL {label}  {detail}')
        FAILURES.append(label)


# These tests exercise the release GUARDS against throwaway temp repos --
# signing belongs to test_release_signing.py, and requiring the real key
# here would couple guard tests to one machine's keystore.
os.environ['FNS_ALLOW_UNSIGNED'] = '1'


def load_publish(repo):
    """Exec publish.py with `project.folder` pointed at a temp repo."""
    mod = types.ModuleType('publish_under_test')
    mod.__dict__['project'] = types.SimpleNamespace(folder=repo)
    mod.__dict__['debug'] = lambda *a, **k: None
    with open(SRC, encoding='utf-8') as f:
        code = f.read()
    exec(compile(code, SRC, 'exec'), mod.__dict__)
    return mod


def make_repo(packages, release, retired=None, artifacts=True):
    """A temp repo holding packaging/manifest.json + packaging/dist toxes."""
    repo = tempfile.mkdtemp(prefix='fns_pub_')
    pkg = os.path.join(repo, 'packaging')
    dist = os.path.join(pkg, 'dist')
    os.makedirs(dist)
    entries = []
    for name, version in packages.items():
        path = f'packaging/dist/{name}.tox'
        full = os.path.join(repo, path)
        with open(full, 'wb') as f:
            f.write(f'{name}-{version}'.encode())
        import hashlib
        sha = hashlib.sha256(open(full, 'rb').read()).hexdigest()
        entries.append({
            'name': name, 'kind': 'tool', 'version': version,
            'artifact': {'path': path, 'bytes': os.path.getsize(full),
                         'sha256': sha,
                         'url': f'https://example.invalid/fnstools/{release}/{name}.tox'},
        })
    doc = {'schema': 1, 'release': release, 'base_url': 'https://example.invalid/fnstools',
           'packages': entries}
    if retired is not None:
        doc['retired'] = retired
    with open(os.path.join(pkg, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(doc, f)
    return repo


def stage(repo):
    return load_publish(repo).Stage()


def restage(repo, packages, release, retired=None):
    """Rewrite the manifest in place and stage again, keeping publish/ --
    which is how Stage() learns what the PREVIOUS release published."""
    fresh = make_repo(packages, release, retired)
    shutil.copyfile(os.path.join(fresh, 'packaging', 'manifest.json'),
                    os.path.join(repo, 'packaging', 'manifest.json'))
    for name in packages:
        shutil.copyfile(os.path.join(fresh, 'packaging', 'dist', f'{name}.tox'),
                        os.path.join(repo, 'packaging', 'dist', f'{name}.tox'))
    shutil.rmtree(fresh, ignore_errors=True)
    return stage(repo)


def main():
    print('publish.Stage() guards')

    # --- baseline: a first release stages cleanly -----------------------
    repo = make_repo({'Alpha': '1.0.0', 'Beta': '1.0.0'}, 'v1.0.0')
    r = stage(repo)
    check('first release stages', r.get('ok') is True, r)
    check('  reports no removals', r.get('removed') == [], r.get('removed'))

    # --- the bump guard (pre-existing behaviour must survive) -----------
    r = restage(repo, {'Alpha': '1.0.0', 'Beta': '1.0.0'}, 'v1.0.1')
    check('release bumping nothing is refused',
          'error' in r and 'no package version' in r['error'], r)

    # --- the removed guard ---------------------------------------------
    # Beta vanishes while Alpha bumps: the bump guard sees a healthy
    # release. This is the case that used to pass.
    r = restage(repo, {'Alpha': '1.1.0'}, 'v1.1.0')
    check('undeclared drop is REFUSED', 'error' in r, r)
    check('  error names the dropped package',
          'error' in r and 'Beta' in r['error'], r.get('error'))
    check('  error names the release', 'error' in r and 'v1.1.0' in r['error'],
          r.get('error'))
    check('  reports it as undeclared', r.get('undeclared') == ['Beta'],
          r.get('undeclared'))

    # nothing may have been staged for a refused release
    staged_dir = os.path.join(repo, 'packaging', 'publish', 'v1.1.0')
    check('  refused release stages no files', not os.path.isdir(staged_dir),
          staged_dir)

    # --- a DECLARED retirement is allowed ------------------------------
    r = restage(repo, {'Alpha': '1.1.0'}, 'v1.1.0', retired=['Beta'])
    check('declared retirement is allowed', r.get('ok') is True, r)
    check('  reports what was removed', r.get('removed') == ['Beta'],
          r.get('removed'))

    # --- a stale retired entry is reported, not fatal ------------------
    # Beta comes back while still listed as retired.
    r = restage(repo, {'Alpha': '1.2.0', 'Beta': '2.0.0'}, 'v1.2.0',
                retired=['Beta'])
    check('re-adding a retired package is allowed', r.get('ok') is True, r)
    check('  stale retired entry is reported',
          r.get('stale_retired') == ['Beta'], r.get('stale_retired'))

    # --- retiring one of several, with others bumping ------------------
    r = restage(repo, {'Alpha': '1.3.0'}, 'v1.3.0', retired=['Beta'])
    check('retire-one-of-two with a bump is allowed', r.get('ok') is True, r)

    shutil.rmtree(repo, ignore_errors=True)

    # --- a drop with NO retired key at all (manifests predating it) ----
    # Needs its own repo: by now Beta is long gone from the previous
    # release, so there would be nothing to drop.
    repo2 = make_repo({'Alpha': '1.0.0', 'Beta': '1.0.0'}, 'v2.0.0', retired=None)
    r = stage(repo2)
    check('legacy manifest (no `retired` key) stages', r.get('ok') is True, r)
    r = restage(repo2, {'Alpha': '1.1.0'}, 'v2.1.0', retired=None)
    check('drop with no `retired` key is refused (not a crash)',
          'error' in r and 'Beta' in r['error'], r)
    shutil.rmtree(repo2, ignore_errors=True)

    # --- gated staging: paid bytes NEVER land in the public dir --------
    repo3 = make_repo({'FreeTool': '1.0.0', 'PaidTool': '1.0.0'}, 'v3.0.0')
    man_path = os.path.join(repo3, 'packaging', 'manifest.json')
    with open(man_path, encoding='utf-8') as f:
        doc = json.load(f)
    for p in doc['packages']:
        if p['name'] == 'PaidTool':
            p['access'] = 'tier_test'
            p['artifact']['url'] = ('https://example.invalid/fnstools/plus/'
                                    'v3.0.0/PaidTool.tox')
    with open(man_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f)
    r = stage(repo3)
    pub = os.path.join(repo3, 'packaging', 'publish')
    check('gated release stages ok', r.get('ok') is True, r)
    check('gated package reported', r.get('gated') == ['PaidTool'], r.get('gated'))
    check('paid tox is UNDER plus/<release>/',
          os.path.exists(os.path.join(pub, 'plus', 'v3.0.0', 'PaidTool.tox')))
    check('paid tox is NOT in the public release dir',
          not os.path.exists(os.path.join(pub, 'v3.0.0', 'PaidTool.tox')))
    check('free tox stays public',
          os.path.exists(os.path.join(pub, 'v3.0.0', 'FreeTool.tox')))

    # --- entitlement guard: gated rows must be AUTHORIZABLE ------------
    # `access` is a stable tier ID; the Worker's TIERS map is what grants.
    # A placeholder, a wrong id, or an ungranted package = pays -> 403.
    wdir = os.path.join(repo3, 'worker')
    os.makedirs(wdir, exist_ok=True)

    def wrangler(tiers_json):
        with open(os.path.join(wdir, 'wrangler.toml'), 'w', encoding='utf-8') as f:
            f.write('TIERS = """\n%s\n"""\n\n'
                    'GUMROAD_PRODUCTS = """\n{}\n"""\n' % tiers_json)

    def set_access(value):
        with open(man_path, encoding='utf-8') as f:
            d = json.load(f)
        for p in d['packages']:
            if p['name'] == 'PaidTool':
                p['access'] = value
        with open(man_path, 'w', encoding='utf-8') as f:
            json.dump(d, f)

    wrangler('{"9999": ["PaidTool"]}')
    set_access('PLACEHOLDER_TIER')
    r = stage(repo3)
    check('placeholder access is refused by name',
          'error' in r and 'placeholder' in r['error'].lower(), r)
    set_access('9999')
    wrangler('{"9999": ["SomethingElse"]}')
    r = stage(repo3)
    check('access naming a tier that does not grant it is refused',
          'error' in r and 'PaidTool' in r['error'], r)
    wrangler('{"1234": ["OtherTool"]}')
    r = stage(repo3)
    check('gated with NO granting tier or product is refused',
          'error' in r and '403' in r['error'], r)
    wrangler('{"9999": ["PaidTool"]}')
    r = stage(repo3)
    check('id-matched tier grant stages clean', r.get('ok') is True, r)
    shutil.rmtree(repo3, ignore_errors=True)

    print()
    if FAILURES:
        print(f'{len(FAILURES)} FAILED: ' + ', '.join(FAILURES))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
