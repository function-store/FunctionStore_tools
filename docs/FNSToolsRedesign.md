---
status: landed
summary: Decision record for the pre-release restructure and rename that shipped as v3.0.0. Supersedes naming and core-membership claims elsewhere.
since: 24ae195 2026-08-15
---

# FNSTools redesign — the pre-release scorched earth (2026-08-15)

Decision record for the restructure and rename executed before first
public release. This redesign ships as **v3.0.0** -- the first release
of the toolkit's public shape, with no migration path from pre-3.0
installs (there were none). Supersedes naming and core-membership statements in
`ConfiguratorDistribution.md` and `RegistryScheme.md` where they
conflict; the mechanics recorded there still stand.

## What changed

**The toolkit is FNSTools.** Root comp, bootstrap artifact
(`FNSTools.tox`), source trees (`FNSTools/`, `modules/suspects/FNSTools/`),
branding. The dev project file keeps its historical name (rename is
cosmetic and optional).

**Core is the raw registries plus one exception.** The requirable unit
was never `FNS_Toolbar` — it was the registry inside it. Six registry
masters ship as their own depth-1 packages, each package IS the master:

    FNS_ConfigRegistry   FNS_ToolbarRegistry   FNS_NavbarRegistry
    FNS_MainMenuRegistry FNS_OpMenuRegistry    FNS_PaneTypeRegistry

promoted to `/sys` under those names with matching global shortcuts
(`op.FNS_CONFIGREGISTRY`, …). They are deliberately raw and cloneable: a
curious user can clone one from `/sys` and extend the toolkit with it.
`FNS_Updater` (renamed from UPDATER) is the one non-registry core —
leaving the updater optional means the one package that fetches updates
is the one a user can decline. A tool's `requires` derives to exactly
the registries it hosts.

**The FNS_* shells demoted to ordinary tools.** FNS_Config was nothing
but its master and dissolved. Toolbar/Navbar/MainMenu/OpMenu keep their
widgets and configurators as optional tools hosting their own
registries; HotkeyManager (owns no registry) is a tool too.
PaneTypeRegistry was renamed on the PreviewPanel25 side as well — it is
the same shared component, and two differently-named copies would
coexist as separate registries.

## Mechanics that hold it together

- **Host clone resolution rides the root**: hosts carry
  `CLONE_EXPR = "op.FNS.op('FNS_XRegistry') if hasattr(op, 'FNS') else None"`,
  and `_masterComp` resolves the same way. No per-package shortcuts
  (which `_release_shipped_shortcut` strips anyway). The `/sys` global's
  healing rewrites any host whose clone stops resolving — this is what
  made the master extraction cost zero per-package edits.
- **A promoted global owns itself**: promotion sheds the master's clone
  binding (`_become_global_registry` scrub) and schedules its own settle
  `_syncSurface` (`_installGlobalRegistry`) — promotion replaces its
  predecessor and kills that copy's pending sync chains, so without the
  self-sync, late-merged registrations never reach the surface (the
  recurring two-button toolbar).
- **A raw depth-1 master never proxies Registration pars onto its
  parent** (`_ensureToolRegistryPage` guard) — its parent is the toolkit
  root, and decorating it re-creates the per-tool par surface this
  redesign removed.
- **parent.FNS is a guarded lookup, never a hard edge**:
  `tdu.tryExcept(lambda: parent.FNS.par.X, default)` in dev-following
  pars; extensions anchor at `ownerComp.parent()`.

## Hazards, learned expensively — encode, do not rediscover

1. **Externally-bound children are reference-only at every nesting
   level.** A parent tox does NOT embed an `enableexternaltox` child; a
   missing external loads an EMPTY SHELL. Any path change must repoint
   `externaltox`/`file` pars recursively AND re-land every bound comp
   deepest-first, or the next open hollows the fleet / resurrects old
   content from stale toxes.
2. **DAT file-sync is bidirectional and the session wins.** Editing a
   synced file while a live DAT holds old text gets clobbered; edit the
   FILE, then pulse the DATs' reload. Never push text into file-synced
   DATs.
3. **Embody move-detection follows DAT file pars.** A live DAT pointing
   at a dead path makes Embody re-create (drag) files there — the
   mechanism behind every "old tree resurrected" incident. When a source
   file vanishes, check `git log` before assuming; the answer is usually
   a stale file par somewhere (the last one hid in TDFam's nested host).
4. **Renames must reach call sites, not just definitions.** The
   SHORTCUT/REGISTRY_NAME sweep left ~45 consumers (`op.TOOLBARREGISTRY`
   in master Exts, configurators, callbacks, docs) that both broke
   behavior and kept re-promoting old-named globals via diverged
   per-host file copies.
5. **TD op access off the main thread wedges or crashes** — mutation
   (`bar.copy` spin, replaceOp crash) and even reads of comps the main
   thread is mutating (a poller froze the session). Marshal via `run()`,
   never poll during scheduled work; settle, then verify once.
   `TDF.replaceOp` of extension-bearing COMPs is retired in favor of
   destroy+`loadTox` everywhere (updater included).

## Pre-release gates (wire into the release flow)

- **Token gate**: zero un-prefixed registry shortcuts —
  `grep -rE "(TOOLBAR|NAVBAR|CONFIG|OPMENU|MAINMENU|PANETYPE)REGISTRY"`
  over the repo filtered for a missing `FNS_` prefix, PLUS the live
  sweep of all DAT texts and par expressions (embedded scripts never
  show in a file grep).
- **Version gate**: `release_one.py` clamps against the published
  manifest — a session reload reverts live `Pkgversion` pars, and a
  reverted par must never ship a downgrade.
- **From-zero test**: the first release after this redesign changes
  every package name and the core set; it requires the full
  bootstrap-drop → picker → install → update round-trip on a clean
  machine state.

## Open questions / deferred

- The one observed store refresh that completed "done" having fetched
  nothing (empty `_needed` on an empty store) was never root-caused; the
  picker's completeness gate makes it self-healing.
- Private Investigator ledger re-adoption: ~10 tracked comps flag `Vc*`
  bind errors until PI re-adopts the renamed tree; stale
  UPDATER/FNS_Config suspects entries fold into the same pass.
- TDFam's nested MainMenu host now syncs the new master file but its
  comp/product-side naming awaits a TDFam sync; PreviewPanel's palette
  distribution needs a re-release to ship FNS_PaneTypeRegistry.
- `OpColor` and `SearchWords` sit at the root empty and untracked —
  identify or remove.
- Splitting shell contents into standalone tools (parent-hierarchy nav,
  IOFilter, …) — per-tool product decisions.
- `Vc*` load-order error flags clear on first cook; a project-open
  settle recook would silence them until the PI pass lands.
