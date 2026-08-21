"""Script entry point for installing a picked subset of the toolkit.

The implementation lives in `InstallerExt.py` -- the same file the
FNS_Installer COMP uses as its extension, so the script rail and the
droppable rail cannot drift apart. This is the thin wrapper for headless
/ Envoy use:

    exec(open('packaging/install.py').read())
    result = Plan('packaging/example-selection.json')     # dry run
    result = Install('packaging/example-selection.json')  # do it

Batching a large install keeps any single call clear of the MCP timeout:

    Install(sel, only=['FNS_Config', 'FNS_Toolbar'])

Install tests should target a COOKING-DISABLED container. A live copy of a
registry master will otherwise try to promote itself to the /sys global and
destroy the running one:

    t = op('/sys/quiet').create(baseCOMP, 'trial'); t.allowCooking = False
    Install(sel, target=t.path)
"""

import os as _os

_impl = {}
exec(open(_os.path.join(project.folder, 'packaging/InstallerExt.py'),
          encoding='utf-8').read(), _impl)

DEFAULT_MANIFEST = _impl['DEFAULT_MANIFEST']
ResolvePlan = _impl['ResolvePlan']
InstallPlan = _impl['InstallPlan']
DefaultTarget = _impl['DefaultTarget']
# what is promoted in /sys/FNS_Registries right now -- also ridden back on
# every InstallPlan result under the 'registries' key
PromotedRegistries = _impl['PromotedRegistries']


def Plan(selection_path, manifest_path=DEFAULT_MANIFEST, target=None):
    return ResolvePlan(selection_path, manifest_path, target)


def Install(selection_path, manifest_path=DEFAULT_MANIFEST, target=None,
            replace=False, only=None):
    plan = ResolvePlan(selection_path, manifest_path, target)
    return InstallPlan(plan, replace=replace, only=only)
