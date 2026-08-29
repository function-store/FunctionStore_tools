---
status: in-force
summary: The ownership rule for the two file-externalization mechanisms — Private Investigator owns externalization and release; Embody is the Envoy/MCP layer, and its file rows are an editing convenience, never a registry of record.
since: 2026-08-28 (owner decision; audits 2026-08-27 surfaced the ambiguity)
skill: externalize-operator
---

# Externalization ownership: PI owns it, Embody is the live layer

Two mechanisms in this project write operators to files, and until now
nothing in the repo said which one *owns* an operator. Both audits tripped
over it, and one of them initially mis-measured the whole project against
the wrong registry. This document is the rule.

## The rule

**Private Investigator owns externalization.** Its suspects table is the
registry of record for what is externalized; `modules/suspects/` is the
canonical export tree (162 `.tox`, 63 `.py` at time of writing, ~438
suspects); the release flow — the Pkg column, the per-package publish —
rides it. A package's shippable identity IS its PI suspect tox.

**Embody owns nothing but the Envoy/MCP layer.** Its real jobs are the MCP
server, TDN snapshots and diffs, the multi-session ledger and claims, and
the logs. It *also* has a file-sync feature, and its
`externalizations.tsv` (47 rows at time of writing, 43 of them `.py` text
DATs synced in place under the tools' own folders) is where that feature
does its bookkeeping — but that table is a **working set, not an ownership
registry**. A row there means "this source DAT is hot-sync-editable on
disk right now", nothing more.

The two are layers, not rivals: PI answers *"what ships, at what version,
from which bytes?"*; Embody's rows answer *"which source files reload live
when edited?"*. A DAT with an Embody row lives inside a COMP whose
shipping is owned by PI. The seam only hurts when someone mistakes one
layer's table for the other's question — which is exactly what the
2026-08-27 audit did on its first pass.

## What follows from it

- **Discoverability.** To know whether an operator is externalized, ask
  PI (the `pi_suspect` tag / the suspects table). An `externalizations.tsv`
  row never implies ownership, and its absence never implies "untracked".
- **One file binding per DAT.** A DAT's `file` parameter belongs to at
  most one system. Two systems pointing different paths at the same DAT is
  the FNS_PaletteRegistry bug (PI lists a suspect export that does not
  exist because the live binding is Embody's in-place path) — resolve such
  cases to one binding, never leave both standing.
- **Nothing ships from an Embody row.** Releases read PI's world plus the
  live parameters. The in-place `.py` files are *source*, reaching users
  only as the bytes baked into a PI-owned tox.
- **The split inside one component is legal.** FNS_Updater is the standing
  example: `ExtUpdater` is a PI suspect exporting to
  `modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py`, while `ExtAuth`,
  the auth callbacks and the `secure_storage` modules are Embody-synced in
  place under `FNSTools/FNS_Updater/`. Under this rule that is a layering,
  not a conflict — the component's shipping is PI's either way. What was
  wrong before this document was only that nothing said so.
- **New work registers with PI.** Embody in-place sync is added on top as
  an editing convenience during active development, and a row whose
  development has landed is a candidate for retirement, not a permanent
  fixture. The load-bearing exception is `scripts/shared/RegistryBase.py`
  — the clone-source DAT for every registry syncs from it, so editing that
  file *is* how RegistryBase changes reach the live session; that row
  stays for as long as the mechanism does.

## Known seams, still open

- **FNS_PaletteRegistry double claim** — its extension DATs are both PI
  suspects and Embody rows, with the live `file` par on the Embody path,
  so PI lists an export it does not own. Resolve to one binding.
- **PI cannot see itself.** PI is not a `pi_suspect`; it reloads from
  `modules/suspects/private_investigator1_withmyhacks.tox` on open, and
  its own lister never shows it dirty — the publish UI silently vanished
  once already (2026-08-14; `scripts/pi_publish_ui.py` exists solely to
  re-stamp it). The tracker is the one thing nothing tracks.
- **One Embody row points into PI's tree** (`/PreviewPanel25` →
  `modules/suspects/PreviewPanel25.tox`) — a cross-system binding that
  predates this rule; fold it to one owner when next touched.

## Sources

- 2026-08-27 audits (W-02 as corrected; the infrastructure audit's
  "code you can and can't read" section)
- `scripts/pi_publish_ui.py` header — the PI self-tracking incident
- `/externalize-operator` — the how-to for Embody's mechanism (per the
  project rule: how-to in the skill, reasoning here)
