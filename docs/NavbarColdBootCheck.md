---
status: consumed
summary: The navbar-registry supervised cold-boot check — inherited from the root recovery note, PASSED 2026-08-28 on a supervised restart (two checklist items had gone stale since 2026-08-09; recorded below).
since: 2026-08-28 (checklist inherited from RECOVERY_NavbarRegistry.md, incident resolved 2026-08-09; verified 2026-08-28)
skill: fns-registry
---

# Navbar registry — supervised cold-boot check

The 2026-08-09 freeze/crash incident behind the original root-level
`RECOVERY_NavbarRegistry.md` is **resolved** (cause was Embot/Envoy-viz's
frame-end assembler pinning the main thread; `Embotenable` + `Envoyfollow`
are OFF on `/Embody` until Embody fixes it — re-enable at your own risk).
The externaltox-revert hazard is fixed at the root: bindings cleared, tags
stripped, both `pre_release` hooks scrub `externaltox`, save cycle verified
revert-free.

**What remains is one supervised cold-boot test** — restart TD while
present and verify:

1. `op.NAVBARREGISTRY` resolves to `/sys/NavbarRegistry`; master + hosts
   show `Registered:` statuses.
2. Every pane bar (`/ui/dialogs/panebar/panebar_default` +
   `/ui/panes/panebar/*`) contains the five `nbitem_*` items:
   ParentHierarchy (left of the path area), CustomParTools + Configure
   gear (right of it), PathCellClickInject overlay, HijackDragdrop.
3. No unprefixed legacy copies (`parent_hierarchy`,
   `button_custompar_tools`) reappear.
4. Master Registration page still has **Align + Kind**; `op.FNS_NAVBAR`
   resolves.
5. Click the gear → Navbar Configurator opens; rows show
   Name/Side/Show/Origin.

If anything is missing at boot, the self-heal layers (healing watch armed
on promotion + `_ensurePackageShortcut`) should catch up within ~2 s; a
`reinitextensions` pulse on `FNS_Navbar/NavbarRegistry` force-fixes.

## Verified — 2026-08-28, supervised restart

**PASSED**, with two checklist items stale relative to the 2026-08-09
wording rather than broken:

1. The global shortcut is now **`op.FNS_NAVBARREGISTRY`** (the FNS_ prefix
   migration renamed it; `op.NAVBARREGISTRY` no longer exists and its
   absence is correct). Resolves to `/sys/FNS_Registries/FNS_NavbarRegistry`,
   13 entries registered.
2. The default pane bar carries the expected `nbitem_*` set — ParentHierarchy,
   CustomParTools, PathCellClickInject, HijackDragdrop — plus
   `nbitem_GroupStart_G1` (the hideable-groups feature, added after this
   checklist was written) and `nbitem_button4`, which is the stale
   `/button4` test host at project root publishing a real entry (its removal
   is the P2-9 cleanup item, not a navbar fault).

No unprefixed legacy copies; master Registration page intact;
`op.FNS_NAVBAR` resolves; zero errors project-wide. The same restart also
cold-boot-verified the RegistryBase mixin split (RegistryScheme §4).
