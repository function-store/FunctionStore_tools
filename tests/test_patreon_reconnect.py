"""A dead Patreon grant offers "Sign in again" where the user is.

Field report 2026-09-17: in the bootstrap's picker, Check again answered
"The Patreon link on this install is no longer active -- sign in again to
reconnect." and nothing on the page could sign in. The gate answers a
recheck for a session whose Patreon refresh token is gone with 200
{connected: false}; the client only treated a 401 as a dead session, so the
picker kept the account, offered Check again and hid Sign in.

Now the connection state is stored with the account (not a sign-out: a
lapsed grant can still carry products for the stale-trust window), served
to the page, and the page offers Sign in again in the header and in the
Patreon dialog. Verified live on the dev installer with an isolated
keystore (the machine's real session untouched).

    python tests/test_patreon_reconnect.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater')
SS = os.path.join(UPD, 'secure_storage.py')
AU = os.path.join(UPD, 'ExtAuth.py')
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
IDX = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
WORKER = os.path.join(_ROOT, 'worker', 'src', 'index.js')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(p):
    return io.open(p, encoding='utf-8').read()


ss, au, ins, idx, wk = read(SS), read(AU), read(INS), read(IDX), read(WORKER)

print('0. the gate still answers a dead grant this way')
check('recheck reports connected (refresh token present) and the sign-in-again message',
      "const connected = !!(session.patreon_refresh_token" in wk
      and "'The Patreon link on this install is no longer active -- '" in wk)

print('1. the keystore can hold the state')
check('Store takes connected=None and writes it only when given',
      "checked_at=None, connected=None):" in ss
      and re.search(r"if connected is not None:\n\s*rec\['connected'\] = bool\(connected\)", ss) is not None)

print('2. a recheck remembers it, other writes keep it')
check('OnRecheckResponse passes the gate\'s connected answer through',
      "connected=(payload.get('connected')" in au and "if 'connected' in payload else None))" in au)
check('_rememberProducts keeps the stored state when a caller gives none',
      "connected=acct.get('connected') if connected is None else connected)" in au)
_recheck = au[au.index('def OnRecheckResponse('):au.index('def OnTokenResponse(')]
check('a dead grant is not a sign-out (products stay usable)',
      'SignOut(' not in _recheck and '_sessionDied(' not in _recheck.split("payload.get('connected') is False")[-1])
check('AuthStatus says sign in, and never claims a link lapsed that never existed',
      "no Patreon link on this session; sign in with Patreon" in au
      and "this session has no Patreon link -- sign in with " in au
      and "or 'your Patreon link is no longer active" not in au)

print('3. the installer serves it')
check('the account global carries connected (False only when the gate said so)',
      "'connected': rec.get('connected') is not False}" in ins)
check('/auth/status carries connected',
      "'connected': connected, 'label': label," in ins)

print('4. the page offers the way back in')
check('header: a dead grant says the link is lost and offers the sign-in',
      "if (account.connected === false) {" in idx
      and "el.appendChild(document.createTextNode(' · Patreon link lost'));" in idx
      and "if (btn && signInWanted()) {" in idx
      and "btn.textContent = signInLabel();" in idx
      and "if (recheck && account.connected !== false) {" in idx)
check('Patreon dialog: sign-in shown whenever the session entitles nothing, recheck only on a live one',
      "signin.hidden = !(hasAuthRail && signInWanted() && authActions.signIn);" in idx
      and "signin.textContent = signInLabel();" in idx
      and "recheck.hidden = !(hasAuthRail && account && !reconnect && authActions.recheck);" in idx)
check('the page reloads when the connection state changes, not only the products',
      "+ '|' + String(!(a && a.connected === false))" in idx
      and 'if (acctSig(st) !== before) {' in idx)

print('5. a session that entitles nothing offers the way in')
check('one rule decides it, for every surface',
      "function signInWanted() {" in idx
      and "return !account || account.connected === false" in idx
      and "|| !((account.products || []).length);" in idx
      and "function signInLabel() {" in idx)
check('the welcome offers sign-in, the join and (on a live session) I just pledged',
      "if (hasAuthRail && signInWanted() && authActions.signIn) {" in idx
      and "This install\\'s Patreon link is gone." in idx
      and "rc0.textContent = 'I just pledged';" in idx)
check('the tick dialog stops calling it a tier problem',
      "if (hasAuthRail && account && signInWanted()) {" in idx
      and "'signed in to a Patreon account that includes '" in idx)
check('an entitled account can still switch accounts, without signing out',
      "btn.textContent = 'Use a different account';" in idx)
check('the header says a session holds no Patreon packages',
      "' · no Patreon packages on this session'" in idx)
check('adoption asks for a recheck, whose answer carries connected',
      "run('args[0].ext.ExtAuth.Recheck()', self.ownerComp," in au
      and "ExtAuth.RequestToken()', self.ownerComp" not in au)

print('6. the sign-in wait ends by itself, and the page can be reloaded')
check('/auth/status reports the label and the check time, not only products',
      "'connected': connected, 'label': label," in ins
      and "'checked_at': checked_at})" in ins)
check('the watcher compares the WHOLE record, so a sign-in that unlocks nothing still lands',
      'function acctSig(a) {' in idx and 'var before = acctSig(account);' in idx
      and 'if (acctSig(st) !== before) {' in idx)
check('it waits ten minutes and says how long it has waited',
      'if (++authPolls > 400) {' in idx
      and "Still waiting, ' + secs + 's. You can leave this " in idx)
check('every auth dialog carries Reload picker; other dialogs do not',
      'id="dlgreload" hidden' in idx
      and "document.getElementById('dlgreload').hidden = !reloadable;" in idx
      and "function showDialog(text, installable, hint, reloadable) {" in idx)
check('the sign-in reply stops telling the reader to reload a page that has no reload',
      "'Finish signing in in your browser. '" in ins
      and 'then reload this page.' not in ins)

print('7. a gate call that never answers does not wedge the pass')
check('every gate request carries a timeout',
      "'timeout': GATE_TIMEOUT_MS}" in au and 'GATE_TIMEOUT_MS = 20000' in au)
check('the timeouts are module constants, not promoted class members',
      any(l == 'GATE_TIMEOUT_MS = 20000' for l in au.splitlines())
      and not any(l.strip().startswith('GATE_TIMEOUT') and l != l.strip()
                  for l in au.splitlines()))
check('a pending token or recheck callback is watched and refused on silence',
      "self._armGateTimeout('_token_cb', 'download token')" in au
      and "self._armGateTimeout('_recheck_cb', 'membership check')" in au
      and 'def _onGateTimeout(self, attr, what, token):' in au
      and "why = 'the gate did not answer in time (%s)' % what" in au)
check('a stale watchdog does nothing (a later call owns the wait)',
      "if getattr(self, '_gate_wait', 0) != token:" in au)
check('the sign-in claim, which has no callback, says so itself',
      'self._claim_pending = True' in au and 'def _onClaimTimeout(self) -> None:' in au
      and 'did not answer the sign-in in time' in au)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all patreon-reconnect checks pass')
