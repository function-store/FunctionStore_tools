---
status: landed
summary: Where a user's OpTemplates library lives -- one active library, chosen global or project, the project one a tagged COMP at the network root outside the toolkit; shipped templates are only the seed. Decided and built 2026-09-10.
since: 2026-09-10
---

# OpTemplates library scope

Owner's question, 2026-09-10: shipped templates are fine as a starting point,
but what if a user wants to externalize their library, or keep it per project
instead of machine-global?

## What exists, and where it bites

- **Global is real.** `External Templates Sync` on writes the library to
  `<userPaletteFolder>/FNSTools/OpTemplates/<name>.tox` and reloads it
  from there at boot (`_2023` suffix on a 2023 build). Same home as the global
  config scope; roams across every project on the machine.
- **Project is an accident.** With sync off the library lives inside the tool
  COMP and saves with the `.toe`. An update rebuilds the tool's children from
  the artifact (docs/ProjectStateAcrossUpdates.md), so an in-tool library is
  lost on the next toolkit update. The only update-proof project library today
  is `Advanced` plus a `Templates` base outside the tool, which the user doc
  tells people not to use.
- **The project path roams.** `Templates` and `Root` are op-reference pars and
  the tool's config host has no exclusions, so under global config scope a
  project-local library path is written into the shared JSON and applied in
  every other project, where it resolves to nothing. The QuickMarks bug again
  (docs/ScopeAndPersistence.md), live now.
- **The dev machine derives the store list from its own palette.** The
  manifest's `alternatives_for` for OpTemplates comes from `Templates` at
  build, which on the dev machine is the palette file, not the shipped set.

## Decisions, taken 2026-09-10

1. **One active library. No merge.** Whichever library the scope names is the
   whole set: loaded from there, saved to there, edited there, offered to the
   op-menu registry from there. Merging shipped, global and project layers
   was considered and rejected: it adds three resident libraries, labelled
   duplicates in the picker, a save-target menu and a collision rule to solve
   problems that a seed rule solves.
2. **Scope is a setting on OpTemplates**: follow config scope (default),
   global, project. Following means a project-scoped install gets project
   templates without a second decision; a user can still split the two.
3. **The project library is a COMP at the network root, outside
   `/FNSTools`, found by a tag, never by a path.** It survives updates
   because the updater only rebuilds the tool's children, and it saves with
   the project because it is the project. No sidecar file beside the `.toe`:
   the config project scope already says the `.toe` is the whole store, and
   the toolkit already has a "network root, beside the toolkit container"
   placement class. Files were proposed and rejected on exactly that
   consistency (the folder model and the argument are in the session record;
   a library remains one `.tox` per library where files exist at all).
4. **Shipped templates are a seed, nothing more.** When the active library
   does not exist yet it is created from what is loaded now: the global set
   when one exists, the shipped set otherwise. No "import missing from
   shipped" step: anything we want to push later ships through the store as
   an alternative, which is what the store layer is for.
5. **Overwrites are prompted**, as today: writing over an existing global file
   asks. A scope flip never overwrites anything by itself, but the
   interactive project -> global flip, with a project library and a global
   file both present, asks Push to Global / Adopt Global / Stay Project, the
   config-scope flip's shape: without it a project set would silently drop
   out of view. Scripts and boot never see a modal.

## The model

| Scope | Library lives | Loads from | Saves to |
|---|---|---|---|
| global | the tool's library base, `externaltox` on the palette file | the palette file at boot | the palette file (`Save templates`, middle-click) |
| project | a root COMP tagged `FNS_OpTemplatesLibrary`, docked to nothing the updater touches | the `.toe` | the `.toe` (project save) |

- `Templates` (the op reference) becomes read-only, showing what the scope
  resolved to, or goes away. `Advanced` and `Create Templates` retire; the
  scope menu and the tag replace them.
- `Root` keeps its meaning (which network the watcher covers) but is excluded
  from roaming like `Templates`.
- The op-menu contribution (`onAlternatives`) reads the active library, as it
  reads `Templates` now.
- `alternatives_for` in the manifest is derived from the SHIPPED base
  explicitly, so the store never advertises a developer's personal set.

## Migration

- An existing palette file: unchanged, it is the global library.
- An existing `Advanced` base: tagged, becomes the project library; the
  `Templates` path stops mattering.
- `Excludepars = 'Templates Root'` on the config host lands first, on its own:
  it closes the live roaming bug and has no design dependency.

## What landed (2026-09-10)

- `Libraryscope` menu (follow / global / project) and a `Pushtoglobal` pulse on
  OpTemplates; `External`, `Advanced` and `Create Templates` retired with
  their parexec DATs; `Templates` is a read-only mirror of the resolved
  library, and `kindergaertner_mymod1` (the library watcher) follows it.
- `applyScope(prompt=False)` loads what exists or creates the missing side
  from the loaded set (the global file from the project library when that is
  active, the project library from the tool's base). The menu's parexec
  passes `prompt=True`: a project -> global flip with both sides present asks
  Push / Adopt / Stay (`_confirmGlobalFlip`, a method so tests can stand in
  for the modal; Stay reverts the menu). `Libraryscope` is excluded from
  roaming like `Configscope`, so boot never flips it and never prompts.
- The project library is `root.copy(OPTemplates1)` named `OpTemplatesLibrary`,
  tagged `FNS_OpTemplatesLibrary`, cooking off, severed from the palette
  binding the copy inherits, placed one grid step right of the toolkit
  container. Found by tag with `findChildren(tags=..., maxDepth=1)` on the
  toolkit's parent. An `Advanced` base outside the tool is adopted by tag on
  the first init.
- `Excludepars = 'Templates Target'` on the tool's config host: neither op
  path roams any more.
- `onShippedAlternatives()` in the tool's op-menu callbacks returns the types
  of the tool's own base; `build_manifest.AlternativesFor` prefers that hook
  when a tool defines it, so the store advertises what ships, never a
  developer's active set.
- Verified live: project flip creates the root library (17 types, no
  overlaps), alternatives are offered from it, the watcher target follows;
  the tool reloaded from its tox keeps the root library and the scope; flip
  back to follow re-wires the palette file; cold boot in follow scope offers
  the same 17 types as before.

## Open

- "Push to global" landed as a pulse and as the first choice of the flip
  prompt.
- Whether the root COMP should carry an `FNS_About` for the hub to list it as
  project content. Not done.
