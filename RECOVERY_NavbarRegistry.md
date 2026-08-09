# Navbar Registry — status + supervised cold-boot checklist

**RESOLVED 2026-08-09 ~13:49.** The freeze/crash pair was **Embot** — Envoy's
opt-in build visualization (`envoy_viz.assembleStep:754`, frame-end hook):
one incident pinned the main thread in an infinite loop (py-spy verified,
same line across samples), one hard-crashed TD, both while processing
`set_dat_content` inside the NavbarConfigurator subtree. Mitigation applied:
`/Embody` `Embotenable` + `Envoyfollow` are now **OFF** (they were both on).
Re-enable at your own risk until Embody fixes the assembler; report the bug
with: py-spy dump of a frozen TD shows
`assembleStep (envoy_viz:754) / assembleTick / vizTick / _vizTick / _onRefresh`.

The externaltox-revert hazard (copies inheriting `externaltox` +
`pi_suspect` from their toolbar sources, PI save flow reloading them) is
fixed at the root: bindings cleared on all six comps, tags stripped, both
pre_release hooks scrub `externaltox`, and a full save cycle was verified
revert-free. Suspects toxes + .toe + release toxes all re-saved clean.

## Remaining: ONE supervised cold-boot test (restart TD while present)

After restart verify:
1. `op.NAVBARREGISTRY` resolves to `/sys/NavbarRegistry`; master + hosts show
   `Registered:` statuses.
2. Every pane bar (`/ui/dialogs/panebar/panebar_default` +
   `/ui/panes/panebar/*`) contains the five `nbitem_*` items:
   ParentHierarchy (left of the path area), CustomParTools + Configure gear
   (right of it), PathCellClickInject overlay, HijackDragdrop.
3. No unprefixed legacy copies (`parent_hierarchy`, `button_custompar_tools`)
   reappear.
4. Master Registration page still has **Align + Kind**; `op.FNS_NAVBAR`
   resolves.
5. Click the gear → Navbar Configurator opens; rows show Name/Side/Show/Origin.

If anything is missing at boot, the self-heal layers (healing watch armed on
promotion + `_ensurePackageShortcut`) should catch up within ~2s; a
`reinitextensions` pulse on `FNS_Navbar/NavbarRegistry` force-fixes.
Delete this file once the cold boot passes.
