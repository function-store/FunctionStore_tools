# scripts/

Historical note: this directory was the toolkit's original externalization
root (the VSCodeTools sync folder). The v3 redesign moved every tool's
sources to live next to its `.tox` under `modules/suspects/FNSTools/<Tool>/`
-- **edit tool sources there, not here**. The stale per-tool copies that used
to sit in this directory were pruned; recover them from git history if ever
needed.

What still lives here, deliberately:

- `shared/` -- `RegistryBase.py`, the single shared source that every
  registry host clone's `RegistryBase` DAT points at (Embody-tracked).
- `QuickExt/templates/` -- the ExtUtils template files (CustomParHelper,
  NoNode, exec DATs) docked into extensions across the toolkit.
- `PaneTypeInjector/` -- `README_PaneTypeRegistry.md`, referenced by a doc
  DAT.
- `pi_publish_ui.py` -- the Private Investigator publish UI stamp script,
  referenced by `packaging/release_one.py`.
