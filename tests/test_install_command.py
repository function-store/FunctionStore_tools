"""The installer's command rail: minimal installs, and the removal guard.

Option A of docs/LauncherToolkitBoundary.md — the installer answers
install requests as registry commands, so a consumer never places toxes
itself and one owner keeps the records.

The load-bearing property is NEGATIVE and easy to lose in a refactor: a
minimal plan must never propose removals. Measured live 2026-08-31 on
this project, installing one package:

    minimal=True   ->  2 steps,  0 removals
    minimal=False  -> 11 steps, 38 removals

Without the guard, "install autosave" would have proposed uninstalling
38 packages. That is why the check below exists.

    python tests/test_install_command.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


src = io.open(INST, encoding='utf-8').read()

print('1. minimal installs exactly what was asked')
check('the core force is skipped under minimal',
      re.search(r"if not minimal:\s*\n\s*for c in manifest\.get\('core'", src)
      is not None)
check('requires are still honoured (_order walks them transitively)',
      re.search(r"for dep in index\[name\]\.get\('requires'", src) is not None)
check('the plan says whether it was minimal',
      "'minimal': bool(minimal)" in src)
# An existing integration must be able to opt in WITHOUT moving to the
# command rail: the launcher's fns_install verb already writes a
# selection.json and pulses Install, so one key beats a new code path.
check('a selection.json can ask for minimal too',
      "minimal = bool(minimal or sel.get('minimal'))" in src)

print('2. THE GUARD: a minimal plan never removes')
check('to_remove is empty under minimal',
      re.search(r"to_remove = \[\] if minimal else", src) is not None)
check('and the hazard is written down, not just coded',
      'would otherwise uninstall' in src or
      'treat the user' in src and 'removal candidates' in src)

print('3. installing from a caller-supplied artifact')
check('sources maps name -> local path', 'sources.get(name' in src)
check('a supplied path is never "stale" -- only the store can lie',
      re.search(r"if _inStore\(path\) and not supplied:", src) is not None)
check('a selection may be a dict, not only a file',
      "isinstance(selection_path, dict)" in src)

print('4. the command surface')
check('FnsCommands declares fns.install', "cap = 'fns.install'" in src)
check('install is DRY RUN by default',
      re.search(r"def CommandInstall\(self, package='', confirm=False",
                src) is not None
      and re.search(r"if not confirm:\s*\n\s*summary\['dry_run'\] = True", src)
      is not None)
check('a guarded announce, like every other package',
      "_registerLauncherCommands" in src
      and "getattr(op, 'FNS_COMMANDREGISTRY', None)" in src)
check('read-only companions for a consumer to query',
      'def CommandInstalled' in src and 'def CommandAvailable' in src)
check('existing locks still apply (source checkout refuses)',
      re.search(r"if plan\.get\('locked'\):\s*\n\s*return \{'ok': False", src)
      is not None)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all install-command checks pass')
