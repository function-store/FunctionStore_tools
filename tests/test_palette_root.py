"""The toolkit's folder in the user palette is FNSTools, and the legacy
FNStools_ext folder migrates into it (docs/PaletteFolderContract.md).

Owner, 2026-09-18: "currently FNSTools externalizes many things to
FNStools_ext folder in the palette. We want to retire that folder and just
use FNSTools."

Two halves. The resolver is carried verbatim by every extension that reads
the folder (they ship as separate toxes and cannot share a module), so part 1
checks the copies agree with the master in ExtUpdater.py and that no reader
still spells the old folder. Part 2 runs the master resolver against a
scratch palette with a fake `app` and `debug`, and walks the three migration
cases the contract names: a lone legacy folder is renamed; both existing are
merged entry by entry, one level down into a folder both hold, a file both
hold kept as the new side has it; a locked entry is left for the next run
without stopping the others.

    python tests/test_palette_root.py
"""
import io
import os
import re
import shutil
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools')
MASTER = os.path.join(TOOLS, 'FNS_Updater', 'ExtUpdater.py')
COPIES = [
    os.path.join(TOOLS, 'FNS_Updater', 'ExtAuth.py'),
    os.path.join(_ROOT, 'packaging', 'InstallerExt.py'),
    os.path.join(TOOLS, 'FNS_ConfigRegistry', 'ConfigRegistryExt.py'),
    os.path.join(TOOLS, 'OpenExt', 'FNS_ConfigRegistry', 'ConfigRegistryExt.py'),
    os.path.join(TOOLS, 'FNS_Remote', 'FNSRemoteExt.py'),
    os.path.join(TOOLS, 'FNS_CommandPalette', 'CommandCuration.py'),
    os.path.join(TOOLS, 'OpTemplates', 'OpTemplateExt.py'),
    os.path.join(_ROOT, 'packaging', 'release_one.py'),
]
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(p):
    return io.open(p, encoding='utf-8').read()


def resolver_source(text):
    """The resolver function's body, indentation normalised to tabs."""
    m = re.search(r"^([ \t]*)def _fnsPaletteRoot\(\):.*?^\1(?:\t|    )return new\n", text, re.S | re.M)
    if not m:
        return None
    body = m.group(0)
    if m.group(1) == '' and '    ' in body and '\t' not in body:
        body = re.sub(r'^((?:    )+)', lambda mm: '\t' * (len(mm.group(1)) // 4), body, flags=re.M)
    return body


print('1. one resolver, carried verbatim')
master_text = read(MASTER)
master = resolver_source(master_text)
check('ExtUpdater.py holds the master resolver', master is not None)
check("the folder is FNSTools and the legacy name is FNStools_ext",
      "PALETTE_DIR = 'FNSTools'" in master_text and "LEGACY_PALETTE_DIR = 'FNStools_ext'" in master_text)
for p in COPIES:
    t = read(p)
    check('%s carries the same resolver' % os.path.relpath(p, _ROOT).replace('\\', '/'),
          resolver_source(t) == master,
          'body differs from the master' if resolver_source(t) else 'no resolver')
for p in [MASTER] + COPIES:
    t = read(p)
    # FILE_HELP_STALE is the one other DELIBERATE mention: the marker the
    # Configfile tooltip heal matches on. Anything else naming the old
    # folder outside the resolver is a path someone forgot to migrate.
    stray = [l for l in t.split('\n') if 'FNStools_ext' in l
             and 'LEGACY_PALETTE_DIR' not in l and 'this was FNStools_ext' not in l
             and 'legacy FNStools_ext' not in l
             and 'FILE_HELP_STALE' not in l]
    check('%s spells the old folder only as the legacy name' % os.path.basename(p), not stray, stray[:2])
check('the store, the family folder and the config derive from the resolver',
      "v = '%s/store' % _fnsPaletteRoot()" in master_text
      and "root = _fnsPaletteRoot()" in master_text
      and "_fnsPaletteRoot() + '/' + self.SUBFOLDER" in read(COPIES[2]))
check('the shared sign-in file sits under the resolved config folder',
      "return '%s/config/gate-session.json' % _fnsPaletteRoot()" in read(COPIES[0]))
check('the installer reads and writes selection.json at the root',
      "sel_dir = _fnsPaletteRoot()" in read(COPIES[1])
      and "selp = '%s/selection.json' % _fnsPaletteRoot()" in read(COPIES[1])
      and "CONFIG_SUBPATH = 'config/FNStools_config.json'" in read(COPIES[1]))


print('2. the migration, run against a scratch palette')


def load_resolver(palette):
    """The master resolver compiled with a fake TD `app` and `debug`."""
    ns = {'os': os, 'debug': lambda *a: ns['_debug'].append(' '.join(str(x) for x in a)), '_debug': []}
    ns['app'] = types.SimpleNamespace(userPaletteFolder=palette)
    code = "PALETTE_DIR = 'FNSTools'\nLEGACY_PALETTE_DIR = 'FNStools_ext'\n" + master.replace('\t', '    ')
    exec(compile(code, 'resolver', 'exec'), ns)
    return ns


def scratch():
    d = tempfile.mkdtemp(prefix='fns-palette-')
    return d.replace('\\', '/')


def touch(path, text='x'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(text)


# a) nothing there: the path is named, nothing is created
pal = scratch()
ns = load_resolver(pal)
r = ns['_fnsPaletteRoot']()
check('fresh palette: the new path is named and not created',
      r == pal + '/FNSTools' and not os.path.exists(r))

# b) a lone legacy folder, odd casing, is renamed into place
pal = scratch()
touch(pal + '/FNSTools_ext/store/manifest.json', '{}')
touch(pal + '/FNSTools_ext/config/FNStools_config.json', '{}')
ns = load_resolver(pal)
r = ns['_fnsPaletteRoot']()
check('lone legacy folder (any casing) is renamed to FNSTools',
      r == pal + '/FNSTools' and os.path.isfile(pal + '/FNSTools/store/manifest.json')
      and not os.path.exists(pal + '/FNSTools_ext'))
check('a second call is a no-op', ns['_fnsPaletteRoot']() == r and not ns['_debug'])

# c) both exist: entries move, namesake folders merge one level down, a
#    namesake file stays as the new side has it, the legacy folder goes
pal = scratch()
touch(pal + '/FNStools_ext/store/AutoRes.tox', 'legacy autores')
touch(pal + '/FNStools_ext/store/manifest.json', 'legacy manifest')
touch(pal + '/FNStools_ext/OpTemplates/OPTemplates1.tox', 'the user library')
touch(pal + '/FNStools_ext/OpTemplates/my_templates.tox', 'more')
touch(pal + '/FNStools_ext/selection.json', 'sel')
touch(pal + '/FNSTools/store/manifest.json', 'new manifest')
touch(pal + '/FNSTools/OpTemplates/OPTemplates1.tox', 'freshly seeded')
touch(pal + '/FNSTools/config/gate-session.json', 'token')
ns = load_resolver(pal)
r = ns['_fnsPaletteRoot']()
check('the legacy folder is gone once merged', not os.path.exists(pal + '/FNStools_ext'))
check('entries the new side lacked moved over',
      read(pal + '/FNSTools/store/AutoRes.tox') == 'legacy autores'
      and read(pal + '/FNSTools/selection.json') == 'sel'
      and read(pal + '/FNSTools/OpTemplates/my_templates.tox') == 'more')
check('a file both sides held stays as the new side has it',
      read(pal + '/FNSTools/store/manifest.json') == 'new manifest'
      and read(pal + '/FNSTools/OpTemplates/OPTemplates1.tox') == 'freshly seeded')
check('what the new side already had is untouched',
      read(pal + '/FNSTools/config/gate-session.json') == 'token')
# the legacy copy of a file both held is KEPT ASIDE, never deleted: the new
# side's file can be a seed while the legacy one is the user's work (a user
# library was lost this way, 2026-09-18; fixed 2026-09-25)
check('the legacy copy of a shared file is kept under legacy_FNStools_ext/',
      read(pal + '/FNSTools/legacy_FNStools_ext/OpTemplates/OPTemplates1.tox') == 'the user library'
      and read(pal + '/FNSTools/legacy_FNStools_ext/store/manifest.json') == 'legacy manifest')
check('a clean merge logs nothing', not ns['_debug'], ns['_debug'])

# d) a locked entry is left behind and does not stop the others
pal = scratch()
touch(pal + '/FNStools_ext/family/FNS/CHOP/x.tox', 'watched')
touch(pal + '/FNStools_ext/store/AutoRes.tox', 'autores')
touch(pal + '/FNStools_ext/tables/Hotkeys.tsv', 'keys')
touch(pal + '/FNSTools/config/x.json', 'new side')
ns = load_resolver(pal)
real_rename = os.rename


def locked_rename(a, b):
    if a.replace('\\', '/').endswith('/FNStools_ext/family'):
        raise PermissionError(13, 'held open')
    return real_rename(a, b)


ns['os'] = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith('_')})
ns['os'].rename = locked_rename
ns['os'].path = os.path
r = ns['_fnsPaletteRoot']()
check('the locked entry stays in the legacy folder',
      os.path.isfile(pal + '/FNStools_ext/family/FNS/CHOP/x.tox'))
check('every other entry still moved',
      read(pal + '/FNSTools/store/AutoRes.tox') == 'autores'
      and read(pal + '/FNSTools/tables/Hotkeys.tsv') == 'keys')
check('the legacy folder is kept while it is not empty, and the miss is logged',
      os.path.isdir(pal + '/FNStools_ext') and ns['_debug'] and 'family' in ns['_debug'][0])
check('the new folder is still the answer', r == pal + '/FNSTools')

# The /get paste rail writes the store itself, BEFORE the toolkit exists, so
# it cannot call _fnsPaletteRoot -- it has to name the folder. It named the
# legacy one for three days after the rename (fixed 2026-09-21), and the
# bootstrap's first read then migrated the folder out from under it: on a
# clean machine the selection file it hands the installer stopped resolving,
# and on a machine that had installed before its fresh manifest.json lost the
# merge to the incumbent. Writing the NEW name puts the paste on the winning
# side and moves nothing.
print('5. writers that NAME the folder instead of resolving it')
SNIPPET = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
snip = read(SNIPPET)
check('the /get paste writes to the current folder',
      "app.userPaletteFolder, " + chr(39) + "FNSTools" + chr(39) + ", " + chr(39) + "store" + chr(39) in snip)
check('and never to the legacy one',
      "'FNStools_ext', 'store'" not in snip)
CMS = os.path.join(_ROOT, 'FNS_CMS', 'CmsExt.py')
if os.path.exists(CMS):
    check('the CMS store fallback names the current folder too',
          'FNStools_ext' not in read(CMS))
# Configfile's help is authored on the parameter, so the rename could not
# reach the 45 stamped hosts; healed at init like Configscope.
CFG = os.path.join(TOOLS, 'FNS_ConfigRegistry', 'ConfigRegistryExt.py')
cfg = read(CFG)
check('a stale Configfile tooltip is healed on init, not hand-swept',
      'def _ensureFileParHelp(self)' in cfg
      and "FILE_HELP_STALE = 'FNStools_ext/config/'" in cfg
      and 'self._ensureFileParHelp()' in cfg
      and "default (FNSTools/config/%s)" in cfg)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all palette-root checks pass')
