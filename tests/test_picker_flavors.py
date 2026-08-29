"""The picker's entitlement UI must never reach the published page.

packaging/configurator/index.html is served three ways: as /get/ on the
public website, from inside TouchDesigner by the installer, and as a
standalone file. Only the served flavor has an account, and the other
two must render exactly as they did before entitlement existed.

That is a property no code review holds onto for long, so it is pinned
here: the public build carries no account, and the chip's own decision
is evaluated -- in node, from the page's real source lines -- for all
three states.

    python tests/test_picker_flavors.py
"""
import io
import os
import re
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
BUILT = os.path.join(_ROOT, 'website', 'get', 'index.html')
INSTALLER = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


src = io.open(PAGE, encoding='utf-8').read()

print('1. the public build carries no account')
if os.path.exists(BUILT):
    built = io.open(BUILT, encoding='utf-8').read()
    check('no FNS_ACCOUNT assignment in /get/',
          'FNS_ACCOUNT = ' not in built)
    check('the read is present and defensive',
          'typeof window.FNS_ACCOUNT' in built)
else:
    print('  SKIP  website/get/ not built (npm run pages)')

print('2. only the SERVED response injects it')
inst = io.open(INSTALLER, encoding='utf-8').read()
# count EMISSIONS, not mentions: _accountGlobal's own docstring shows the
# line it produces, which is documentation, not a second code path
emits = [m.start() for m in
         re.finditer(r"return 'window\.FNS_ACCOUNT = %s", inst)]
check('exactly one place emits the global', len(emits) == 1, emits)
check('it is inside _accountGlobal', '_accountGlobal' in inst)
check('it returns empty when no updater rail is present',
      re.search(r"def _accountGlobal.*?if upd is None:\s*\n\s*return ''",
                inst, re.S) is not None)
check('the token never leaves the updater',
      'device_token' not in inst and 'CachedToken' not in inst)

print('3. the chip decides correctly in all three states')
# lift the page's real decision lines rather than restating them here
m = re.search(r"var own = entitled\(p\);\s*\n\s*var label = (.*?);\s*\n\s*"
              r"var extra = (.*?);", src, re.S)
assert m, 'could not find the chip decision in the page'
label_expr, extra_expr = m.group(1), m.group(2)

harness = """
function run(account, products, name) {
  function entitled(p) {
    return !!(account && (account.products || []).indexOf(p.name) >= 0);
  }
  var p = {name: name};
  var own = entitled(p);
  var label = %s;
  var extra = %s;
  return label + '|' + extra;
}
var out = [];
out.push(run(undefined, null, 'FNS_TimelineTools'));                  // site
out.push(run(null, null, 'FNS_TimelineTools'));                       // signed out
out.push(run({products:['FNS_TimelineTools']}, null, 'FNS_TimelineTools'));
out.push(run({products:['Other']}, null, 'FNS_TimelineTools'));
console.log(out.join('\\n'));
""" % (label_expr, extra_expr)

try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', harness],
                         capture_output=True, text=True, timeout=30)
    lines = [l for l in got.stdout.strip().split('\n') if l]
except Exception as e:
    lines = []
    print('  SKIP  node unavailable (%s)' % e)

if lines:
    check('site flavor (no global) -> plain "Plus", no state class',
          lines[0] == 'Plus|', lines[0])
    check('signed out -> plain "Plus", no state class',
          lines[1] == 'Plus|', lines[1])
    check('entitled -> unlocked, own class',
          'unlocked' in lines[2] and lines[2].endswith('| own'), lines[2])
    check('gated but not yours -> locked, locked class',
          'locked' in lines[3] and lines[3].endswith('| locked'), lines[3])
    check('the two states are distinguishable', lines[2] != lines[3])

print('4. the remedy controls ship hidden and stay hidden on the site')
for el in ('support', 'recheck', 'signin'):
    m = re.search(r'id="%s"[^>]*>' % el, src)
    check('%s is hidden in markup' % el, m and 'hidden' in m.group(0),
          m.group(0) if m else 'not found')
if os.path.exists(BUILT):
    for el in ('support', 'recheck', 'signin'):
        m = re.search(r'id="%s"[^>]*>' % el, built)
        check('%s still hidden in the built site page' % el,
              m and 'hidden' in m.group(0), m.group(0) if m else 'not found')
# every unhide must sit behind the guard, so the site cannot reach one
guard = src.find('if (!el || !hasAuthRail) { return; }')
check('the guard precedes every unhide',
      guard > 0 and all(src.find(u) > guard
                        for u in ('support.hidden = false',
                                  'recheck.hidden = false')),
      guard)

print('5. the account branches cannot run without the global')
check('hasAuthRail gates the account line',
      'if (!el || !hasAuthRail) { return; }' in src)
check('hasAuthRail is a typeof test, not a truthiness test',
      "typeof account !== 'undefined'" in src)

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
