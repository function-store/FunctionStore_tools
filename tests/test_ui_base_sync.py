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
print('all checks passed')
