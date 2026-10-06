"""The manifest's `launcher` block — what a bundler is allowed to gather.

Every FNS tool carries quick-launch commands. Only a few ask for a
surface BEYOND quick-launch, or mark themselves part of a blessed
capability. A launcher's bundler needs the second set, not the first, so
the predicate that separates them is worth pinning: get it wrong in the
"too generous" direction and the bundler gathers the whole fleet.

Static checks only — build_manifest needs a live TouchDesigner. The live
assertion (4 of 53 packages capable, all four being the ported launcher
capabilities) is recorded in docs/LauncherToolkitBoundary.md.

    python tests/test_launcher_surface.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(_ROOT, 'packaging', 'build_manifest.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


src = io.open(GEN, encoding='utf-8').read()
fn = src[src.index('def LauncherSurface'):src.index('def Hotkeys')]

print('1. the predicate is narrow')
check("'quick' alone never qualifies", "tok != 'quick'" in fn)
check('a capability qualifies on its own',
      re.search(r"cap = str\(s\.get\('capability'\)", fn) is not None
      and 'caps.add(cap)' in fn)
check('empty means empty -- no block for command-only packages',
      re.search(r"if not surfaces and not caps:\s*\n\s*return \{\}", fn)
      is not None)

print('2. both registration shapes are harvested')
check('FnsCommands() spec lists', "getattr(ext, 'FnsCommands', None)" in fn)
check('@fns_command decorated methods',
      "'_fns_command'" in fn and 'dir(cls)' in fn)
check('only promoted (uppercase) methods are considered',
      "name[:1].isupper()" in fn)
check('a broken FnsCommands cannot fail the build',
      re.search(r"try:.*?FnsCommands.*?except Exception", fn, re.S) is not None)

print('3. it is DERIVED and emitted presence-style')
check('emitted only when non-empty',
      re.search(r"launcher = LauncherSurface\(comp\)\s*\n\s*if launcher:",
                src) is not None
      and "entry['launcher'] = launcher" in src)
check('nothing reads it from the catalog (derived, never declared)',
      "meta.get('launcher'" not in src)

print('4. the shape a bundler consumes')
check('two keys, both sorted for a stable manifest',
      re.search(r"return \{'surfaces': sorted\(surfaces\),\s*\n?\s*"
                r"'capabilities': sorted\(caps\)\}", fn) is not None)

print('5. seedable is the safe predicate -- launcher alone is NOT')
# Most launcher-capable packages are gated (3 of 4 today), so a bundler
# gathering by `launcher` would ship paid bytes in a free app.
check('seedable is derived from access, not from the surface',
      re.search(r"launcher\['seedable'\] = \(comp\.name in curated\s*\n?\s*"
                r"and entry\['access'\] == 'free'\)", src) is not None)
check('it FAILS CLOSED: an uncatalogued package is never seedable',
      'comp.name in curated' in src and 'FAIL CLOSED' in src)
check('it is set BEFORE the block is attached to the entry',
      src.index("launcher['seedable']") < src.index("entry['launcher'] = launcher"))
check('the leak it prevents is written down, not just coded',
      'paid bytes' in src and 'freely downloadable' in src)
# NESTED, not top level. A consumer reading p.seedable gets undefined,
# and a predicate that ORs that with its own free check stays CORRECT
# while never running the cross-check -- which is exactly what happened
# to a live consumer against v3.0.13. Pin the position, not just the key.
check('seedable is nested in the launcher block, never top level',
      "launcher['seedable']" in src
      and "entry['seedable']" not in src)
check('and the nesting is documented where a consumer would look',
      'p.launcher.seedable' in io.open(
          os.path.join(_ROOT, 'packaging', 'CREATING.md'),
          encoding='utf-8').read())

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all launcher-surface checks pass')
