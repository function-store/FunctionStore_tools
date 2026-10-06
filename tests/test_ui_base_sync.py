"""The shared UI base must be identical everywhere it is inlined.

packaging/configurator/base.css is the single source for the family's
design tokens and shared components; every shell that must stay a
self-contained single file carries a generated copy between FNS:UIBASE
markers (see sync_base.py). A stale copy is exactly the hand-synced-palette
rot the base exists to end, so drift fails the suite.

    python tests/test_ui_base_sync.py
"""
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC = os.path.join(_ROOT, 'packaging', 'configurator', 'sync_base.py')

got = subprocess.run([sys.executable, SYNC], capture_output=True, text=True)
out = (got.stdout or '') + (got.stderr or '')
print(out.strip())
if got.returncode != 0:
    print('FAILED: a shell carries a stale copy of base.css -- run '
          'python packaging/configurator/sync_base.py --write')
    sys.exit(1)
# A dialog's action row must stay reachable: an install plan of 51 chips put
# Install below the fold (field report 2026-09-18). The rule belongs to the
# shared base, not to one shell -- a page-local copy would be deleted by the
# next sync, which is exactly how the FNS tab switch lost its styling.
BASE = os.path.join(_ROOT, 'packaging', 'configurator', 'base.css')
import io as _io
_css = _io.open(BASE, encoding='utf-8').read()
_i = _css.index('.dlg-actions {')
_rule = _css[_i:_css.index('}', _i)]
if 'position: sticky' not in _rule or 'bottom: 0' not in _rule:
    print('FAILED: .dlg-actions is not sticky in base.css -- a long dialog hides its buttons')
    sys.exit(1)
print('  PASS  the dialog action row is sticky, in the shared base')
print('all checks passed')
