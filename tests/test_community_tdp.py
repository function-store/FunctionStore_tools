"""Community highlights shipped as Python packages (tdp): check, install, place.

Since 2026-09-27 nothing is pinned (owner): a row names the package, the
installer dry-runs the latest release, refuses one that would add a package
TouchDesigner ships, and installs it. The notes below are from the earlier
pinned design, whose install and placement path is unchanged.

docs/CommunityHighlights.md, section 4. Verified live 2026-09-25 in TD
2025.33070 against a scratch venv (never the project's own): tdp-TauCeti
pinned with --also tdp-touchutilcollection installed with uv and its
TweenCHOP placed bound to mod.tdpTauCeti._ToxFiles['TweenCHOP'] with no
errors; the same package pinned WITHOUT that dependency placed a TweenCHOP
whose extension failed to import it (the author's package does not declare
it, hence `also`); a lock naming numpy was refused; a project with no
environment answered `noenv`. The picker's flow (install, set up an
environment, install, placed) was run on a stubbed page.

This test runs the updater's pure helpers outside TD and pins the wiring.
It needs no network: tdp_pin's PyPI and uv calls are not exercised here.

    python tests/test_community_tdp.py
"""
import io
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'packaging'))
import tdp_pin                          # noqa: E402
import recommendations as rec           # noqa: E402

FAILS = []


def check(label, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + ('' if ok else '   ' + str(detail)[:240]))
    if not ok:
        FAILS.append(label)


def read(*parts):
    return io.open(os.path.join(ROOT, *parts), encoding='utf-8').read().replace('\r\n', '\n')


upd = read('modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
block = upd[upd.index('TD_BUNDLED_SEED = ('):upd.index('# --- end tdp helpers')]
ns = {'os': os}
exec(compile(block, 'tdp-helpers', 'exec'), ns)

UV_DRY = """Using Python 3.11.15 environment at: .venv
Resolved 4 packages in 185ms
Would install 4 packages
 + numpy==2.4.6
 + opencv-python==5.0.0.93
 + tdp-tauceti==5.1.16
 + tdp-touchutilcollection==0.8.0
"""
PIP_REPORT = {'install': [{'metadata': {'name': 'tdp-QrCodeCOMP', 'version': '1.0.0'}},
                          {'metadata': {'name': 'Pillow', 'version': '12.3.0'}}]}

print('1. a package is named, not pinned (owner, 2026-09-27)')
tdp = {'package': 'tdp-TauCeti', 'module': 'tdpTauCeti', 'tox': 'PresetManager',
       'also': ['tdp-touchutilcollection']}
check('the requirements are names only: the package and what it imports undeclared',
      ns['_tdpRequirements'](tdp) == ['tdp-TauCeti', 'tdp-touchutilcollection'])
row = {'name': 'TauCeti', 'author': 'W', 'url': 'https://pypi.org/project/tdp-TauCeti/', 'tdp': tdp}
check('such a row validates', rec.validate({'schema': 1, 'tools': [row]}) == [], rec.validate({'schema': 1, 'tools': [row]}))
check('a lock is refused (nothing is pinned any more)', rec.validate({'schema': 1, 'tools': [
    dict(row, tdp=dict(tdp, lock=['tdp-tauceti==5.1.16 --hash=sha256:' + 'a' * 64]))]}) != [])

print('2. the dry run decides, and packages TouchDesigner ships are refused')
check('uv dry-run output is read', ns['_dryRunNames'](UV_DRY) == ['numpy', 'opencv-python', 'tdp-tauceti', 'tdp-touchutilcollection'])
check('pip --report JSON is read', ns['_reportNames'](PIP_REPORT) == ['tdp-qrcodecomp', 'pillow'])
check('the two seeds are identical', tuple(ns['TD_BUNDLED_SEED']) == tuple(tdp_pin.TD_BUNDLED_SEED))
site = tempfile.mkdtemp(prefix='fns-td-site-')
for d in ('numpy-2.1.2.dist-info', 'typing_extensions-4.16.0.dist-info', 'cv2', 'rpds_py-2026.6.3.dist-info'):
    os.makedirs(os.path.join(site, d))
b1, b2 = ns['_bundledNames'](site), tdp_pin.bundled_names(site)
check('both read dist-info names', {'numpy', 'typing-extensions', 'rpds-py'} <= b1 and b1 == b2, sorted(b1 ^ b2))
check('opencv is caught though it ships as cv2', 'opencv-python' in b1)
check('pillow is not bundled (QrCodeCOMP may bring it)', 'pillow' not in b1)
check('the refusal comes from the dry run, before the install starts',
      upd.index("clash = sorted(set(names) & _bundledNames(")
      < upd.index("job['stage'] = 'install'"))

print('3. the commands')
reqs = ['tdp-TauCeti', 'tdp-touchutilcollection']
dry = ns['_tdpInstallCommand'](reqs, 'C:/p/.venv/Scripts/python.exe', uv='uv', dry_run=True)
real = ns['_tdpInstallCommand'](reqs, 'C:/p/.venv/Scripts/python.exe', uv='uv')
check('uv: dry run, then the same install for real', '--dry-run' in dry and '--dry-run' not in real
      and dry[-2:] == reqs and real[-2:] == reqs)
check('wheels only, into the venv', '--only-binary' in real and '--python' in real)
check('no pins or hashes', '--require-hashes' not in real and '--no-deps' not in real and '-r' not in real)
pipdry = ns['_tdpInstallCommand'](reqs, 'C:/p/.venv/Scripts/python.exe', dry_run=True, report='r.json')
check('pip fallback: the venv python, its dry run writes a report',
      pipdry[:4] == ['C:/p/.venv/Scripts/python.exe', '-m', 'pip', 'install']
      and '--dry-run' in pipdry and pipdry[pipdry.index('--report') + 1] == 'r.json')
env = ns['_tdpChildEnv']({'VIRTUAL_ENV': 'x', 'PYTHONPATH': 'y', 'PYTHONHOME': 'z', 'PATH': 'p'})
check('the child does not inherit TD\'s Python settings', env == {'PATH': 'p', 'PYTHONUTF8': '1'}, env)
check('the tox binds to the package', ns['_tdpToxExpression']('tdpQrCodeCOMP') == 'mod.tdpQrCodeCOMP.ToxFile'
      and ns['_tdpToxExpression']('tdpTauCeti', 'TweenCHOP') == "mod.tdpTauCeti._ToxFiles['TweenCHOP']")

print('4. the updater')
check('no environment is answered, never created quietly',
      "'state': 'noenv'" in upd and 'app.pyEnvHelper' in upd)
check('an environment is set up with TD\'s own manager, its disclaimer shown',
      "'%s/Palette/Tools/tdPyEnvManager.tox' % app.samplesFolder" in upd
      and 'm.par.Active = True      # Derivative\'s disclaimer asks here' in upd
      and 'm.par.Createvenv.pulse()' in upd)
check('the modal never runs inside the caller\'s frame',
      "run('args[0]._activatePyEnvManager(args[1])', self, m.path," in upd)
check('both steps are polled from the main thread, not waited on',
      "run('args[0]._pollTdpInstall()', self, delayFrames=15" in upd and 'proc.wait' not in upd)
check('a hung step is given up', 'TDP_INSTALL_TIMEOUT' in upd and "job['proc'].kill()" in upd)
check('one install at a time', "another package is installing" in upd)
check('the new site-packages becomes importable now', 'importlib.invalidate_caches()' in upd)
check('an already-imported module says restart', 'Restart TouchDesigner to use the new version' in upd)

print('5. the installer, console, card, CMS and site')
ins = read('packaging', 'InstallerExt.py')
check('install and environment routes', "uri == '/community/install'" in ins and "uri == '/community/pyenv'" in ins)
check('noenv is answered before anything is scheduled',
      ins.index("'noenv': True", ins.index('def _installCommunity')) < ins.index('InstallCommunityPackage(args[1], args[2])'))
cb = read('modules', 'suspects', 'FNSTools', 'FNS_Console', 'console_server_callbacks.py')
check('the console forwards both', "'/community/install'" in cb and "'/community/pyenv'" in cb)
page = read('packaging', 'configurator', 'base.js')      # the shared card (console Community view)
check('the card offers Install for a named package, served only',
      "actionButton('install in this project'," in page and 'if (a.noenv) return offerEnv(btn, a.env || {});' in page
      and 'function locked(r) { return !!(r && r.tdp && r.tdp.package && r.tdp.module); }' in page)
check('and names Derivative\'s disclaimer before setting one up', "(Derivative's disclaimer)" in page)
mjs = read('website', 'tools', 'cms.mjs')
check('the CMS checks through tdp_pin.py', "path.join(REPO, 'packaging', 'tdp_pin.py')" in mjs and "p === '/api/pin-tdp'" in mjs)
html = read('website', 'tools', 'cms.html')
check('with Check and Also needs on the row, and no lock box', 'data-pintdp' in html and '>Check</button>' in html
      and 'data-tdp="also"' in html and 'data-tdp="lock"' not in html)
pin = read('packaging', 'tdp_pin.py')
check('the check refuses a bundled package and writes no hashes',
      'which TouchDesigner ships itself' in pin and '--generate-hashes' not in pin)
check('the post says it installs the latest', 'its latest release' in read('website', 'tools', 'build-site.mjs'))
check('the check reads the module from the wheel, not a guess', "_ToxFiles\\s*=\\s*\\{" in pin)

if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all community-tdp checks pass')
