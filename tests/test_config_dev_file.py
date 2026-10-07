"""The development checkout keeps its own user data, and none of it ships.

Owner, 2026-09-30: the toolkit's author also USES FNSTools, so the dev
project's settings, template library and tables must stop sharing files with
every project where the toolkit is merely used. Each gets a dev twin:

  settings JSON     config/FNStools_config.json -> config/FNStools_config.dev.json
  template library  OpTemplates/                -> OpTemplates_dev/
  every table       tables/                     -> tables_dev/

Project scope is the wrong tool for this: it stores settings in the packages'
own pars and state tables, and in the dev project those are exactly what gets
exported and shipped.

None of the dev values may leave the checkout. pre_release_common clears every
Configfile and rewrites any FNSTools/<name>_dev path on every operator of
every package; OpTemplates' own hook clears Libraryfolder; _severHost scrubs
the one host the bootstrap ships, since the bootstrap never runs the package
scrub. docs/ConfigScope.md has the reasoning.

    python tests/test_config_dev_file.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(_ROOT, 'packaging', 'pre_release_common.py')
REG = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                   'FNS_ConfigRegistry', 'ConfigRegistryExt.py')
RAILS = os.path.join(_ROOT, 'packaging', 'build_installer.py')
OPT = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'OpTemplates',
                   'OpTemplateExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


common = io.open(COMMON, encoding='utf-8').read()
reg = io.open(REG, encoding='utf-8').read()
rails = io.open(RAILS, encoding='utf-8').read()
opt = io.open(OPT, encoding='utf-8').read()

print('1. no artifact ships a Configfile override')
rule = re.search(r"for _c in \[_c0\] \+ _c0\.findChildren\(type=COMP\):\s*\n"
                 r"\s*_p = getattr\(_c\.par, 'Configfile', None\).*?"
                 r"_p\.val = _p\.default", common, re.S)
check('the common scrub resets Configfile to its default', rule is not None)
check('on the package root AND every COMP below it (hosts included)',
      rule is not None and '[_c0] + _c0.findChildren(type=COMP)' in rule.group(0))
# findChildren(depth=N) matches EXACTLY depth N; a depth-limited walk would
# miss a host nested inside a sub-tool and report nothing (td-python.md).
check('the walk is unlimited, never depth=',
      rule is not None and 'depth=' not in rule.group(0))
# CONSTANT alone leaves the expression TEXT on the par, dormant; the first
# version of this rule did exactly that and a real export read-back still
# carried the dev path (2026-09-30). The text has to be cleared too.
check('the expression text is cleared, not just made dormant',
      rule is not None and "_p.expr = ''" in rule.group(0))
check('and the value pinned in CONSTANT mode',
      rule is not None and '_p.mode = ParMode.CONSTANT' in rule.group(0))

# The bootstrap ships the root's own config host copied straight from the dev
# root, and it never passes through pre_release_common. StampHost copies the
# master, so a re-stamped host would carry the dev path into every new user's
# FNSTools.tox. _severHost is the rails' equivalent of the scrub.
print('1b. nor does the bootstrap, which skips the package scrub')
sever = re.search(r"^def _severHost\(host\):.*?^def ", rails, re.S | re.M)
check('_severHost clears Configfile on the root host it ships',
      sever is not None and "getattr(host.par, 'Configfile', None)" in sever.group(0))
check('expression text first, then the value in CONSTANT mode',
      sever is not None and "p.expr = ''" in sever.group(0)
      and 'p.mode = ParMode.CONSTANT' in sever.group(0)
      and 'p.val = p.default' in sever.group(0))

print('2. the override is the mechanism the dev project uses')
check('ConfigPath honours a non-empty Configfile over the palette default',
      re.search(r"def ConfigPath\(self\):.*?getattr\(self\.ownerComp\.par, "
                r"'Configfile', None\).*?if override:\s*\n\s*return override",
                reg, re.S) is not None)
check('the default is still <palette>/FNSTools/config/FNStools_config.json',
      "return _fnsPaletteRoot() + '/' + self.SUBFOLDER + '/' + self.FILE_NAME" in reg
      and "FILE_NAME = 'FNStools_config.json'" in reg)

# The template library and every table got the same separation as `_dev`
# twins. Their paths live in DAT file expressions, the OpTemplates base's
# externaltox, and ExternalTables' Foldername, which holds a BARE
# `FNSTools/tables_dev` with no slash on either side. One rule rewrites all of
# them; it is exercised here on the real shapes rather than pinned as text.
print('3. no artifact ships a _dev twin folder')
m = re.search(r"_DEV_TWIN = _re\.compile\(r'([^']+)'\)", common)
check('the twin rule is present', m is not None)
if m is not None:
    twin = re.compile(m.group(1))
    repl = 'FNSTools/' + chr(92) + '1'
    cases = {
        'app.userPaletteFolder+"/FNSTools/tables_dev/Hotkeys.tsv"':
            'app.userPaletteFolder+"/FNSTools/tables/Hotkeys.tsv"',
        "app.userPaletteFolder + '/FNSTools/OpTemplates_dev/OPTemplates1.tox'":
            "app.userPaletteFolder + '/FNSTools/OpTemplates/OPTemplates1.tox'",
        'FNSTools/tables_dev': 'FNSTools/tables',            # ExternalTables Foldername
        'FNSTools/tables_devices/x.tsv': 'FNSTools/tables_devices/x.tsv',   # not a twin
        'FNSTools/tables': 'FNSTools/tables',                # already shared
    }
    wrong = {k: twin.sub(repl, k) for k, v in cases.items() if twin.sub(repl, k) != v}
    check('it maps every real twin shape back, and leaves look-alikes alone',
          not wrong, wrong)
check('it walks EVERY operator, since the tables are DATs',
      'for _o in [_c0] + _c0.findChildren():' in common)
check('it covers file, externaltox, folder AND ExternalTables Foldername',
      "for _pn in ('file', 'externaltox', 'folder', 'Foldername'):" in common)
check('it rewrites expressions AND constants',
      '_p.expr = _DEV_TWIN.sub(' in common and '_p.val = _DEV_TWIN.sub(' in common)

print('4. OpTemplates can be pointed at its own library folder')
check('Libraryfolder is created get-or-create, empty by default',
      "p = self.ownerComp.par['Libraryfolder']" in opt
      and "page.appendStr('Libraryfolder'" in opt and "p.default = ''" in opt)
check('the folder follows the par (extFolder is a property, not fixed at init)',
      'def extFolder(self):' in opt
      and opt.split('def extFolder(self):')[0].rstrip().endswith('@property')
      and "self.extFolder = _fnsPaletteRoot() + '/OpTemplates'" not in opt)
check('the wired path expression carries the folder',
      "/FNSTools/{self._librarySubfolder()}/{name}.tox" in opt)
# Adoption copies the NEWEST candidate over the target, and the keep-aside
# folder holds the USER's pre-migration set: a redirected folder must never
# look there, or the dev library could be replaced by an old user one.
check('a redirected folder never adopts the migration keep-aside set',
      "legacy_dir = ('' if self._libraryFolderOverridden() else" in opt)
check('empty means the historical folder, so a user install is unchanged',
      "_DEFAULT_LIBRARY_SUBFOLDER = 'OpTemplates'" in opt
      and "return v or _DEFAULT_LIBRARY_SUBFOLDER" in opt)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all dev-config checks pass')
