# P4 — First-Run Nudge Plan

**Approved 2026-08-21 (owner): dialog form.** After a successful install,
nothing currently points the user at the configurator. Add a one-shot
nudge.

## Design

- A `PopDialog` on first boot after install:
  "FNSTools installed — open the Configurator to arrange your toolbar."
  Buttons: **Open Configurator** / **Later** / **Don't show again**.
- **Open Configurator** opens the gear UI (same entry point as the
  toolbar gear button) and sets the seen-flag.
- **Later** leaves the flag unset — nudges again next boot.
- **Don't show again** sets the flag, no navigation.

## Seen-flag

- Lives in the machine-global config JSON via ConfigRegistry — a state
  entry (or Registration-page par) on the root `FNS` host. Fires once per
  **machine**, not per project, and roams correctly.
- Edge case: a project pinned to `Configscope = project` (.toe-only) does
  not load the global JSON — the flag then lives in whatever scope is
  active. Acceptable: worst case is one extra nudge in a project-scoped
  project. Do not special-case it.
- The dev project must never nudge: the dev machine's config already
  carries the flag after the first dismissal (or pre-seed it).

## Trigger

- **Boot window only** — hard NO-RECURRING-SCANS constraint (live-show
  toolkit; nothing discovery-shaped on a timer).
- Config applies ~30 frames after registration, so the flag is not
  readable at extension init. Defer the nudge check past the config-apply
  window (e.g. `run(..., delayFrames=...)` from the root ext's boot path,
  after the ConfigRegistry apply pass; idempotent, guarded if the check
  runs before config lands).
- Implementation home: the root FNSTools ext — it exists on every install
  rail (one-drop bootstrap, FNS_Installer, Textport), so all rails get the
  nudge without per-rail wiring.

## Implementation notes

- `PopDialog` is the same widget family used by the Configscope
  scope-flip confirm (see `FNS_ConfigRegistry`, commit 33b955d) — reuse
  that pattern rather than a custom panel.
- Landing changes to the root ext requires re-exporting the carrying
  toxes (root `FNSTools.tox` at minimum) — the externaltox-reload trap:
  live edits not exported to every carrying tox are silently reverted at
  next project open (see `docs/ConfiguratorPersistenceFixes.md` status
  note / commit 61748d9).

## Verification

1. Fresh scratch install (from `packaging/dist/`, palette config JSON
   without the flag): nudge appears exactly once.
2. **Open Configurator** lands on the gear UI; flag set; second boot
   silent.
3. **Later**: nudge reappears on next boot; **Don't show again**: never
   again.
4. Dev project: never nudged.
5. Cold boot after tox export: behavior identical from disk.
