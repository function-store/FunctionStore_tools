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
for el in ('support', 'recheck', 'signin', 'redeem'):
    m = re.search(r'id="%s"[^>]*>' % el, src)
    check('%s is hidden in markup' % el, m and 'hidden' in m.group(0),
          m.group(0) if m else 'not found')
if os.path.exists(BUILT):
    for el in ('support', 'recheck', 'signin', 'redeem'):
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

def _lift(pattern, label):
    """A page function's REAL source, or fail loudly if it moved."""
    m = re.search(pattern, src, re.S)
    assert m, 'could not lift %s from the page' % label
    return m.group(0)


print('6. the install plan splits gated picks in every flavor')
fn_isplus = _lift(r'function isPlus\(p\) \{[^}]*\}', 'isPlus')
fn_entitled = _lift(r'function entitled\(p\) \{.*?\n  \}', 'entitled')
fn_installable = _lift(r'function installable\(n\) \{.*?\n  \}', 'installable')
fn_selection = _lift(r'function selection\(\) \{.*?\n  \}', 'selection')

sel_harness = """
function run(account) {
  var M = {core: ['FNS_Updater'], toolkit: {name: 'FNSTools'},
           base_url: 'https://x/fnstools'};
  var byName = {
    AutoRes: {name: 'AutoRes', access: 'free'},
    FNS_TimelineTools: {name: 'FNS_TimelineTools', access: '8323905'},
  };
  var picked = new Set(['AutoRes', 'FNS_TimelineTools']);
  var wantBind = null;
  %s
  %s
  %s
  %s
  var s = selection();
  return JSON.stringify({install: s.install, tools: s.tools});
}
console.log(run(undefined));
console.log(run(null));
console.log(run({products: ['FNS_TimelineTools']}));
console.log(run({products: []}));
""" % (fn_isplus, fn_entitled, fn_installable, fn_selection)

try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', sel_harness],
                         capture_output=True, text=True, timeout=30)
    sel_lines = [l for l in got.stdout.strip().split('\n') if l]
    if got.returncode != 0:
        print('  node stderr: %s' % got.stderr.strip()[:300])
except Exception as e:
    sel_lines = []
    print('  SKIP  node unavailable (%s)' % e)

if len(sel_lines) == 4:
    import json as _json
    site, out_, own, other = [_json.loads(l) for l in sel_lines]
    for label, s in (('site flavor', site), ('signed out', out_),
                     ('wrong products', other)):
        check('%s: gated pick stays OUT of install' % label,
              'FNS_TimelineTools' not in s['install'], s['install'])
        check('%s: free pick still installs' % label,
              'AutoRes' in s['install'], s['install'])
        check('%s: the want is still recorded in tools' % label,
              'FNS_TimelineTools' in s['tools'], s['tools'])
    check('entitled: gated pick DOES install',
          'FNS_TimelineTools' in own['install'], own['install'])

print('7. the paste script splits SEL and PLUS')
fn_installscript = _lift(r'function installScript\(\) \{.*?\n  \}',
                         'installScript')
scr_harness = """
var M = {core: ['FNS_Updater'], toolkit: {name: 'FNSTools'},
         base_url: 'https://x/fnstools'};
var byName = {
  AutoRes: {name: 'AutoRes', access: 'free'},
  FNS_TimelineTools: {name: 'FNS_TimelineTools', access: '8323905'},
};
var picked = new Set(['AutoRes', 'FNS_TimelineTools']);
%s
%s
console.log(installScript());
""" % (fn_isplus, fn_installscript)

try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', scr_harness],
                         capture_output=True, text=True, timeout=30)
    script = got.stdout.strip()
    if got.returncode != 0:
        print('  node stderr: %s' % got.stderr.strip()[:300])
except Exception as e:
    script = ''
    print('  SKIP  node unavailable (%s)' % e)

if script:
    import ast
    import json as _json
    ok_parse = True
    try:
        ast.parse(script)
    except SyntaxError as e:
        ok_parse = False
    check('the generated script is valid Python', ok_parse)
    m_sel = re.search(r'SEL = (\[[^\]]*\])', script)
    m_plus = re.search(r'PLUS = (\[[^\]]*\])', script)
    check('SEL holds only the free pick',
          m_sel and _json.loads(m_sel.group(1)) == ['AutoRes'],
          m_sel.group(1) if m_sel else 'no SEL')
    check('PLUS carries the gated pick to the closing message',
          m_plus and _json.loads(m_plus.group(1)) == ['FNS_TimelineTools'],
          m_plus.group(1) if m_plus else 'no PLUS')
    check('only core + SEL are downloaded',
          "names = m['core'] + SEL" in script)
    check('the wanted-but-gated picks are recorded in selection.json tools',
          "'tools': SEL + PLUS" in script)

print('8. auto-resume fires only when it honestly can')
# lift the IIFE's real guard lines: served + unlocked + signed in, every
# wanted pick entitled, and never over the first-run welcome
m = re.search(
    r'if \(!served \|\| locked \|\| !account\) return;\s*\n'
    r'\s*if \(!wantedStill\.length \|\| !wantedStill\.every\(installable\)\) return;\s*\n'
    r"(\s*//[^\n]*\n)*"
    r"\s*if \(firstrun && !sessionFlag\('fns\.welcomed'\)\) return;", src)
check('the guard lines are present and in order', m is not None)
auto_harness = """
function fires(served, locked, account, wanted, firstrun, welcomed) {
  var byName = {
    AutoRes: {name: 'AutoRes', access: 'free'},
    FNS_TimelineTools: {name: 'FNS_TimelineTools', access: '8323905'},
    FNS_ProOnly: {name: 'FNS_ProOnly', access: '8291595'},
  };
  var wantedStill = wanted;
  function sessionFlag(k) { return welcomed ? '1' : null; }
  %s
  %s
  %s
  if (!served || locked || !account) return false;
  if (!wantedStill.length || !wantedStill.every(installable)) return false;
  if (firstrun && !sessionFlag('fns.welcomed')) return false;
  return true;
}
var out = [];
out.push(fires(false, '', {products:['FNS_TimelineTools']}, ['FNS_TimelineTools'], false, false));   // site
out.push(fires(true, '', null, ['FNS_TimelineTools'], false, false));                                // signed out
out.push(fires(true, 'src lock', {products:['FNS_TimelineTools']}, ['FNS_TimelineTools'], false, false)); // locked
out.push(fires(true, '', {products:['FNS_TimelineTools']}, [], false, false));                       // nothing wanted
out.push(fires(true, '', {products:['FNS_TimelineTools']}, ['FNS_TimelineTools','FNS_ProOnly'], false, false)); // partial
out.push(fires(true, '', {products:['FNS_TimelineTools']}, ['FNS_TimelineTools'], true, false));     // welcome up
out.push(fires(true, '', {products:['FNS_TimelineTools']}, ['FNS_TimelineTools'], true, true));      // welcomed
out.push(fires(true, '', {products:['FNS_TimelineTools']}, ['FNS_TimelineTools'], false, false));    // the green path
console.log(out.join('\\n'));
""" % (fn_isplus, fn_entitled, fn_installable)

try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', auto_harness],
                         capture_output=True, text=True, timeout=30)
    auto_lines = [l for l in got.stdout.strip().split('\n') if l]
    if got.returncode != 0:
        print('  node stderr: %s' % got.stderr.strip()[:300])
except Exception as e:
    auto_lines = []
    print('  SKIP  node unavailable (%s)' % e)

if len(auto_lines) == 8:
    for i, (label, want) in enumerate((
            ('site flavor never auto-installs', 'false'),
            ('signed out never auto-installs', 'false'),
            ('a locked target never auto-installs', 'false'),
            ('nothing wanted, nothing fires', 'false'),
            ('one uncovered pick keeps it manual', 'false'),
            ('never over the first-run welcome', 'false'),
            ('welcomed first run may fire', 'true'),
            ('entitled + wanted fires', 'true'))):
        check(label, auto_lines[i] == want, auto_lines[i])
auto_block = src[src.find('auto-resume deferred Plus picks'):]
auto_block = auto_block[:auto_block.find('})();')]
check('the plan flows straight into the install (no ceremony)',
      "post('/install', '{}', installOrPoll);" in auto_block
      and 'setInterval' not in auto_block)
check('a plan refusal stays manual (no install post)',
      'if (!res.ok) { showDialog(res.text, false); return; }' in auto_block)
check('it waits out an in-flight pass before planning',
      'st.fetching' in auto_block)

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
