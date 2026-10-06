"""Open Settings opens Settings, on the page it says it is opening.

Field report 2026-09-17, macOS: Open Settings opened the Hub's Console tab
showing the TOOL PICKER, with no console tab strip on it and so no Settings
to click; only closing and reopening the hub fixed it. Two separate faults,
both measured on 2025.33070:

1. `Open(tab='settings')` built a BARE url. Settings got no fragment from
   when it was the first tab and a bare url meant Settings; Install &
   remove leads now, and the page falls back to the first shown tab when
   there is no fragment, so Open Settings quietly landed on Install &
   remove. Verified live before and after: bare url drew Install & remove,
   '#settings' drew Settings with its tab selected.

2. Assigning Address does not always navigate. The render can come back
   showing the document it already had while the parameter reads the new
   one. Reload does NOT rescue that -- pointed at one server and showing
   another's page, a Reload pulse re-loaded the CURRENT document and left
   the divergence untouched. Clearing the parameter and setting it on the
   NEXT frame is a real change, and that navigated. Two writes in one
   frame collapse into no change, which is why the delay is the point.
   Verified end to end: render parked on a foreign page, Open(tab=
   'settings') then drew the console's Settings tab.

    python tests/test_console_open_tab.py
"""
import io
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CON = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Console',
                   'ConsoleRegistryExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


con = io.open(CON, encoding='utf-8').read()


def method(name):
    i = con.index('\tdef %s(' % name)
    j = con.index('\n\tdef ', i + 1)
    return con[i:j]


print('1. every named tab carries a fragment')
for m in ('Open', 'Serve'):
    body = method(m)
    check('%s builds the fragment from the builtin set' % m,
          "builtin = {t['name'] for t in self.BUILTIN_TABS}" in body
          and "url += ('#' + tab) if tab in builtin else ('#t-' + tab)" in body)
    check('%s no longer leaves settings without one' % m,
          "elif tab != 'settings':" not in body, m)
check('settings is still a builtin tab, so it takes the plain fragment',
      "{'name': 'settings', 'label': 'Settings'" in con)

print('2. the handover really navigates')
nav = method('_navigate')
check('it clears the address first',
      "browser.par.Address = ''" in nav)
check('and sets it on the NEXT frame, or the change collapses',
      "if args[0].valid: args[0].par.Address = args[1]" in nav
      and 'delayFrames=1' in nav and 'delayRef=op.TDResources' in nav)
check('a failure is reported, never swallowed',
      'except Exception as e:' in nav and 'could not point the browser' in nav)
show = method('_showUrl')
check('both surfaces go through it, neither assigns Address itself',
      show.count('self._navigate(browser, url)') == 2
      and 'browser.par.Address = url' not in show)

print('3. the measurements are recorded where the code is')
check('why Reload is not the answer',
      'reloads the CURRENT document' in nav or 'reloaded the CURRENT' in nav
      or 're-loaded the CURRENT' in nav)
check('what the symptom looked like',
      'field report 2026-09-17' in nav.lower() or 'TOOL PICKER' in nav)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all console open-tab checks pass')
