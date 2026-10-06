"""New tools are announced once, and family operators stay current.

docs/NewToolsAndFamilyFreshness.md. Field report 2026-09-25: after an
update the FNS tab showed nothing new, and nothing told the user that a
release had added tools.

Part 1 runs the installer's seen-list rules (UnseenTools, MarkSeen) on a
scratch palette, with the first-install cases the owner asked to watch:
a first run is shown nothing, an install with no record yet sees only the
tools this release line introduced that it does not have, and after that
whatever the record lacks. Parts 2 to 4 pin the wiring in the installer,
the updater, the picker and the console.

    python tests/test_new_tools.py
"""
import io
import json
import os
import re
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
PAGE = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
CONSOLE = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Console', 'console_page.html')
CALLBACKS = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Console', 'console_server_callbacks.py')
FAILS = []


def check(label, cond, detail=''):
    print(('  PASS  ' if cond else '  FAIL  ') + label + ('' if cond else '   ' + str(detail)[:200]))
    if not cond:
        FAILS.append(label)


def read(p):
    return io.open(p, encoding='utf-8').read()


ins = read(INS)
block = ins[ins.index('# --- tools this machine has been shown'):ins.index('# --- pure helpers (no COMP required)')]
ns = {'os': os, 'json': json, '_fnsPaletteRoot': lambda: ''}
exec(compile(block, 'seen', 'exec'), ns)
Unseen, Seen, Mark = ns['UnseenTools'], ns['SeenPackages'], ns['MarkSeen']
Announce, SetAnnounce = ns['AnnounceNewTools'], ns['SetAnnounceNewTools']

MAN = {'packages': [
    {'name': 'A', 'kind': 'tool', 'whatsnew': 'tooltips.'},
    {'name': 'B', 'kind': 'tool', 'whatsnew': 'new package (Base). Does B.'},
    {'name': 'C', 'kind': 'tool', 'whatsnew': 'New package. Does C.'},
    {'name': 'Core1', 'kind': 'core'},
    {'name': 'Fam', 'kind': 'tool', 'companion': 'family', 'whatsnew': 'new package'},
]}


def pal():
    return tempfile.mkdtemp(prefix='fns-seen-').replace('\\', '/')


print('1. the seen list, first installs first')
r = pal()
check('a first run is shown nothing', Unseen(MAN, (), firstrun=True, root=r) == [])
check('and records every tool as shown', Seen(r) == ['A', 'B', 'C'], Seen(r))
check('companions and core are never tools to announce', 'Fam' not in Seen(r) and 'Core1' not in Seen(r))

r = pal()
got = Unseen(MAN, installed=['C'], firstrun=False, root=r)
check('no record yet: only introduced tools it does not have', got == ['B'], got)
check('the baseline holds everything else', Seen(r) == ['A', 'C'], Seen(r))
check('asking again without answering still shows them', Unseen(MAN, (), root=r) == ['B'])

Mark(['B'], root=r)
check('answered: nothing left', Unseen(MAN, (), root=r) == [])
MAN2 = {'packages': MAN['packages'] + [{'name': 'D', 'kind': 'tool', 'whatsnew': 'tooltips.'}]}
check('the next release shows only what it adds', Unseen(MAN2, (), root=r) == ['D'])
check('the record lives in the palette config folder',
      os.path.isfile(r + '/config/seen_packages.json'))
check('the window opens by itself unless turned off', Announce(r) is True)
SetAnnounce(False, root=r)
Mark(['D'], root=r)
check('turning it off survives marking tools shown', Announce(r) is False and 'D' in Seen(r))
SetAnnounce(True, root=r)
check('and it turns back on', Announce(r) is True)

# Field report 2026-10-06: a fresh machine installing through TDX Launcher
# Ultra (a headless Install, no picker) was greeted with "New since you
# last looked". Its install is a first run: everything is shown.
First = ns['RecordFirstInstall']
MAN3 = {'packages': MAN['packages'] + [{'name': 'P', 'kind': 'tool', 'preview': True,
                                        'whatsnew': 'new package'}]}
r = pal()
check('a headless first install records every current tool', First(MAN3, root=r) is True)
check('so the picker opened later shows nothing',
      Unseen(MAN3, installed=['A'], firstrun=False, root=r) == [], Unseen(MAN3, ['A'], root=r))
check('previews stay out of the record', Seen(r) == ['A', 'B', 'C'], Seen(r))
check('an existing record is never overwritten', First(MAN2, root=r) is False and 'D' not in Seen(r))
r = pal()
check('without it, a bare-root install still announces introduced tools (unchanged)',
      Unseen(MAN3, installed=['A'], firstrun=False, root=r) == ['B', 'C'])

print('2. the installer')
check('manifest.js carries FNS_UNSEEN',
      "'window.FNS_UNSEEN = %s;\\n'" in ins and 'unseen = UnseenTools(json.loads(man_text), known_here, firstrun)' in ins)
check('POST /seen records, GET /newtools.json only reads',
      "uri == '/seen'" in ins and 'MarkSeen(names)' in ins
      and "uri == '/newtools.json'" in ins)
check('the console forwards both to the installer',
      "'/seen', '/newtools.json'" in read(CALLBACKS))
inst = ins[ins.index('    def Install(self, remove=None):'):ins.index('    def _firstInstallManifest(self, plan):')]
check('Install decides a first run BEFORE installing, records it after',
      inst.index('first_manifest = self._firstInstallManifest(plan)')
      < inst.index('res = InstallPlan(plan')
      < inst.index('RecordFirstInstall(first_manifest)'))
check('the first-run test is the picker\'s own',
      'return manifest if self._isFirstRun(op(plan[\'target\']), tools) else None' in ins)
check('A: a recorded family member with no file is fetched',
      "not s['present'] or s['placement'] == 'none'" in ins)

print('3. the updater keeps family members current (B)')
upd = read(UPD)
check('Compare reports a stale family member as an update',
      "if placement == 'none' and self._familyStoreStale(index.get(name)):" in upd
      and re.search(r"_familyStoreStale\(index\.get\(name\)\):.*?updates\.append\(name\)", upd, re.S) is not None)
check('stale = missing, or not the manifest bytes', 'def _familyStoreStale(self, pkg):' in upd
      and 'return _sha256(path) != want' in upd)
check('the apply records it, never replaces anything',
      re.search(r"def _replacePackage.*?if step\.get\('placement'\) == 'none':.*?"
                r"self\.RecordInstalled\(name, digest", upd, re.S) is not None)
check('the pass still ends with the family sync', upd.count('self.SyncFamilyFolder()') >= 3)

print('4. the picker and the console')
page = read(PAGE)
check('served, the installer decides; elsewhere the browser keeps the record',
      'return (window.FNS_UNSEEN || []).filter(' in page and "var SEEN_KEY = 'fns.seen';" in page)
check('a first visit or a frame records everything and shows nothing',
      "if (!stored('fns.visited', null) || FNS_EMBEDDED) { writeSeenLocal(names); return []; }" in page)
check('never on a first run or a first visit, never over a dialog',
      'if (!firstrun && !firstVisit && announceOn && unseenAtLoad.size && !(served && locked)) {' in page
      and "if (!document.querySelector('dialog[open]')) showNewTools();" in page)
check('every answer records them as shown', page.count('markSeen(names)') >= 2
      and "d.addEventListener('cancel', function () { markSeen(names); });" in page)
check('unseen tools carry the New badge and the New filter', 'return unseenAtLoad.has(p.name) ||' in page)
check('the window lists only what the viewer can get (no Patreon pestering)',
      '.filter(function (p) { return p && (!isPlus(p) || entitled(p)); }).sort(byTitle);' in page)
check('and the console count follows the same rule',
      "and (access.get(n, 'free') == 'free' or n in owned))" in ins and 'def _ownedProducts(self):' in ins)
check('the dialog exists', 'id="newtools"' in page and 'id="newadd"' in page and 'id="newlater"' in page)
check('a preference: the window opens by itself only while it is on',
      'if (!firstrun && !firstVisit && announceOn && unseenAtLoad.size' in page
      and 'id="newauto"' in page and "window.FNS_ANNOUNCE !== false" in page
      and "'window.FNS_ANNOUNCE = %s;\\n'" in ins)
check('and the New filter shows the way back', "'New-tools window: on' : 'New-tools window: off'" in page)
con = read(CONSOLE)
check('the console counts them on Install & remove',
      'data-view="view-tools"' in con and "fetch('/newtools.json'" in con
      and "if (e.data === 'fns:seen') loadNewTools();" in con)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all new-tools checks pass')
