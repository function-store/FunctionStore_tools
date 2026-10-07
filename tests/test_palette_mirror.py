"""Family members reach one flat folder that TDFam and TD's Palette both read.

Owner, 2026-09-18: "the family operators should end up in FNSTools/FNS, no
subfolder for categories, they are decided by their own manifest" (and the
day before: "FNStools_ext/FNS/ should be enough, the categories can be
recorded in json manifests").

One folder, two readers. <user palette>/FNSTools/FNS holds one tox per
member under its PUBLIC name with TDFam's sidecar beside it; the category is
the sidecar's op_group, the version its op_version. TDFam takes a loose file
at the folder root as uncategorised and reads both from the sidecar (measured
2026-09-18 on the vendored FileManager / OpFamRegistryExt), so the versioned
filename its default naming regex expects is not needed.

Copying files there is NOT enough for the second reader. TD does not scan
the folder: it reads an INDEX, <userPalette>/paletteData.json, into the Text
DAT /ui/dialogs/palette/palette/cusPalette, and only at startup. So the
index is regenerated from a directory walk and that DAT is pulsed to
re-read. Measured live on 2026-09-18 (backed up and restored): writing the
file and pulsing `loadonstartpulse` makes TD pick it up.

    python tests/test_palette_mirror.py
"""
import io
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater',
                   'ExtUpdater.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


upd = io.open(UPD, encoding='utf-8').read()

print('1. one flat folder in the user palette, cleanly named')
check('the folder is <userPalette>/FNSTools/FNS, from the resolver, never a relocated store',
      "root = _fnsPaletteRoot()" in upd
      and "return '%s/%s' % (root, self._FAMILY_NAME) if root else ''" in upd
      and "_FAMILY_NAME = 'FNS'" in upd
      and '/family/' not in upd.split('def FamilyFolder')[1].split('def _familySidecar')[0])
check('the tox carries the PUBLIC name, not a versioned family filename',
      "stem = name[4:] if name.startswith('FNS_') else name" in upd
      and "dest = '%s/%s.tox' % (folder, stem)" in upd
      and "side = '%s/%s.json' % (folder, stem)" in upd)
check("the category rides the sidecar's op_group, and there is no category subfolder",
      "'op_group': str(fam.get('op_group', '') or '')," in upd
      and 'dest_dir' not in upd.split('def SyncFamilyFolder')[1].split('def _dropLegacyFamilyTree')[0]
      and "op_category" not in upd)
check('the sidecar is TDFam\'s shape and carries the version',
      "'OpInfo': info," in upd and "'ParRetain'" in upd and "'StateRetain'" in upd
      and "'Shortcuts'" in upd and "'op_version': str(pkg.get('version', '') or '')" in upd)
check('the folder is derived: strays, and a leftover category subfolder, are pruned',
      "removed.append(fn)" in upd and "removed.append(fn + '/')" in upd
      and "shutil.rmtree(fp, ignore_errors=True)" in upd)
check('the old family/ tree beside it is dropped',
      'def _dropLegacyFamilyTree(self, folder)' in upd
      and "legacy = '%s/family' % os.path.dirname(folder)" in upd
      and 'self._dropLegacyFamilyTree(folder)' in upd)
check('there is no second palette copy any more',
      'SyncPaletteFolder' not in upd and 'PALETTE_SUB' not in upd and 'def PaletteFolder' not in upd)

print('2. TD is told, because it only reads the index at startup')
check('the index is regenerated wholesale from a walk, never patched',
      'def RebuildPaletteIndex(self)' in upd
      and "path = '%s/paletteData.json' % root" in upd)
check("the node shape is TD's own",
      "'localRoot': 'app.userPaletteFolder'" in upd
      and "'palette': 'My Components'" in upd
      and "kid_id = '%s.%d' % (node_id, i)" in upd
      # the separator is a literal backslash, TD's format; written this way
      # so the assertion itself does not turn into an escaping puzzle
      and 'rp = rel + ' in upd and chr(92) + chr(92) + "' + fn" in upd)
check('the refresh is the cusPalette DAT load pulse',
      "op('/ui/dialogs/palette/palette/cusPalette')" in upd
      and 'loadonstartpulse' in upd)
check('a failed refresh never fails the sync (it is a courtesy)',
      'palette index written but TD not refreshed' in upd)
check('the sync rebuilds the index every time',
      'idx = self.RebuildPaletteIndex()' in upd.split('def SyncFamilyFolder')[1].split('def _dropLegacyFamilyTree')[0])

print('3. the walk does not bloat or strip the index')
check('machine directories are skipped, plausible NAMES are not',
      "_PALETTE_SKIP_DIRS = ('node_modules', '__pycache__', 'site-packages')" in upd
      and "'backup'" not in upd.split('_PALETTE_SKIP_DIRS')[1][:200])
check('build artefacts are skipped, documents are kept',
      "'.py', '.pyc'" in upd and "'.lib'" in upd and "'.zip'" in upd
      and "'.md'" not in upd.split('_PALETTE_SKIP_EXTS')[1][:220]
      and "'.pdf'" not in upd.split('_PALETTE_SKIP_EXTS')[1][:220])
check('dotfiles are skipped', "if fn.startswith('.'):" in upd)

print('4. it rides the pass that already keeps the store')
check('the full-mirror hook and the update pass call it',
      "self.SyncFamilyFolder()\n\t\tself._keepStoreLater()" in upd
      and upd.count('self.SyncFamilyFolder()') >= 3)
check('nothing appears where the family is not installed',
      upd.count('the FNS family is not installed in this project') >= 1)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all palette-mirror checks pass')
