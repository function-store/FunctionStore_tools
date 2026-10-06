"""An open picker window is never switched off under the reader.

Field report 2026-09-17: the "Installed" dialog was on screen and none of
its buttons answered a click. The picker is drawn by a Web Render TOP, and
that render was held on only while the picker server lives. Two things end
that hold -- the server stopping on silence (the page heartbeats only
while a mouse or key moved in the last two minutes, so reading a dialog
for three minutes is "idle"), and the console taking the panel over, which
sets no hold of its own. Either way a dormant render shows its last frame
and takes no clicks, with no way back: the wake signal would have been the
very input the dormant render no longer delivered.

The browser's own visibility watchers cannot cover this. Its Window Owner
is the Hub's panel and its Pane Owner is the Hub, because the console
mirrors the same browser, so a viewer opened on the browser itself matches
none of them. Its panel's `winopen` does track that window (measured on
2025.33070: False before openViewer, True after, False a frame after
closeViewer), so the idle timer now asks it, and an open picker outranks
silence. A closed window still stops the server on the same timer.

The second half of the fix is NOT checked here and cannot be: the browser
component's visibility rule (`webBrowser/watch_rules`) lives inside the
root tox, not in any file. It now counts a floating viewer opened on the
component ITSELF as a window showing it, so the render stays alive on an
open window even with no hold at all. Verified live instead, both ways:
hold off plus window open gives Active True (the exact state the field
report was stuck in), and closing the window gives Active False.

    python tests/test_picker_window_alive.py
"""
import io
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


ins = io.open(INS, encoding='utf-8').read()
body = ins[ins.index('    def _idleOff('):]
body = body[:body.index('\n    def ', 1)]

print('1. the picker asks whether anyone is looking at it')
check('the window question is its own method, off the browser panel',
      'def _pickerOnScreen(self, url):' in ins
      and 'return bool(browser.panel.winopen)' in ins)
check('it answers for THIS picker only, not whatever the browser shows now',
      "if addr is None or not str(addr.eval()).startswith(served or url):" in ins)
check('an absent browser or panel is not an open window',
      'if browser is None:\n            return False' in ins
      and 'except Exception:\n            return False' in ins)

print('1b. it compares the URL it SERVED, never one rebuilt from the port')
# Belt and braces, not the 2026-09-17 cause: that reading (:36710 on
# screen, :36760 in the parameter) turned out to be the CONSOLE serving at
# :36710 after taking the panel over, so this test answered correctly and
# the render is what went dark. Nothing stops a later Configure from
# moving the port while an older page is still up, though, so identity
# comes from what was served.
check('Configure remembers the served URL on the COMP',
      "self.ownerComp.store('picker_url', url)" in ins)
check('the guard reads that, and only falls back to the passed URL',
      "served = self.ownerComp.fetch('picker_url', '', search=False)" in ins
      and 'startswith(served or url)' in ins)
check('the port parameter is not the identity any more',
      "startswith(url)" not in ins.split('def _pickerOnScreen')[1].split('def ')[0])

print('2. an open window outranks silence')
check('the idle timer consults it before stopping anything',
      '_pickerOnScreen(url)' in body)
check('it reschedules instead of stopping, so a closed window still stops',
      'wait_ms = int(self.SERVER_IDLE_SECONDS * 1000)' in body
      and 'wait_ms = 0' in body
      and 'if wait_ms:' in body)
check('the stop is still reached on a silent, windowless picker',
      'ws.par.active = False' in body
      and 'browser.par.Holdactive = False' in body)
check('the question is asked BEFORE the server is deactivated',
      body.index('_pickerOnScreen(url)') < body.index('ws.par.active = False'))

print('3. the reason is written where the code is')
check('the field report is recorded against the rule',
      'field report 2026-09-17' in body)
check('the measurement behind winopen is recorded',
      'measured\n        2026-09-17' in ins or 'measured' in ins.split('def _pickerOnScreen')[1][:1200])

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all picker-window checks pass')
