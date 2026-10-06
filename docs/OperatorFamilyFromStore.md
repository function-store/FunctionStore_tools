---
status: landed
summary: The FNS operator family, built 2026-09-17: FNS_OpFamily (TDFam) in the toolkit, seven members declaring TDFam's FamManifest, a derived `family` manifest block, the updater mirroring members from the store into the family folder, commands without dialogs, a guard for the toolkit's own copies, and a CMS section that edits the manifest in the tool. The research below it is kept as the record.
since: 2026-09-10
---

# An FNS operator family, fed from the store

> **2026-09-18:** the palette folder is now `FNSTools` and the family folder
> is flat: `<user palette>/FNSTools/FNS/<Name>.tox` with the sidecar beside
> it, no `family/` tree, no category subfolders, the category in the
> sidecar's `op_group`. The layout below is the record of what was built on
> 2026-09-17; the contract in force is docs/PaletteFolderContract.md.

## What was built (2026-09-17)

Door B only; Door A (rows in TD's own COMP tab) stays researched and unbuilt.

- **The family is a package.** `FNS_OpFamily`, free, Surfaces: the TDFam
  family named `FNS` moved from `/TDFam_create` into the toolkit, colour
  black, Install On Start on, its registry promoting to `/sys` as TDFam
  designs. `Opfolder` is an expression on
  `<palette>/FNStools_ext/family/FNS`. TDFam's updater file bindings, which
  pointed at a folder this repo does not have, are severed. `LICENSE` in it
  is TDFam's NOTICE; `LICENSE_Apache` holds the full Apache-2.0 text.
- **Members declare themselves.** RandomCHOP (new package, Base tier),
  SimpleSceneChanger, ProSceneChanger, SwitchTools, MixSequencer,
  OpSequencer and CamSequencer carry TDFam's `FamManifest`. `op_type` is a
  lowercase word and `op_name` the readable spelling (next section).
- **The manifest derives a `family` block** (`build_manifest.FamilyFor`):
  `op_type`, `op_name`, `op_label`, `op_group`, `is_filter`,
  `compatible_types`, `search_words`, `summary`, and `par_retain`,
  `state_retain`, `shortcuts` when non-empty. A foreign or hostless entry may
  curate it (`CuratedFamily`); a member implies `placement: pane`.
  `CatalogProblems` refuses a curated block beside a live FamManifest, a
  member at the root, a bad type or group; preflight blocks on
  `FamilyProblems` (an unparseable DAT, a type with capitals, a bad group).
- **The updater keeps the family folder** (`FNS_Updater.SyncFamilyFolder`):
  every member the store holds lands at
  `family/FNS/<op_group>/<name>_<version>.tox` with a TDFam sidecar built
  from the row; stale versions and non-members are removed; TDFam re-reads
  the folder through `op.FAMREGISTRY`. It runs from `_afterStoreComplete`,
  after a scoped refresh (a picker install) and after an update pass. The
  store's own rules decide presence, so a gated member is on the tab only for
  an account that holds it. TDFam's default naming regex has no `v`.
- **Commands without dialogs** on `FNS_OpFamily`: Stub Family Operators,
  Replace Family Stubs, Update Family Operators, Sync Family From Store.
  They call TDFam's batch methods, which its own Stubs pulses wrap in modal
  dialogs.
- **The CMS edits the facts where they live.** A live package's family
  section reads and writes its FamManifest through FNS_CMS
  (`/api/familyread`, `/api/familywrite`, PI-saved, validated by
  build_manifest's rules) and says why when TD is not connected; a foreign
  package's block rides the catalog save.

## Only when needed (2026-09-17)

Owner decision: the family, its TDFam registry and the FNS tab do not
appear unless a family operator is installed. FNS_OpFamily is a
`companion: family` package in the catalog:

- **The picker never offers it.** One `pickable()` test excludes
  companions from every list a pick can come from (the tool list, installed,
  last setup, wanted, the starter set, bundles, stored picks), and it
  carries no `fits`, so the questionnaire cannot choose it.
- **The installer decides.** `ResolvePlan` drops companions from whatever a
  selection says and adds them exactly when the selection holds a package
  with a `family` block, minimal requests included. An installed family with
  no member left is then an ordinary removal candidate.
- **No folder without it.** `SyncFamilyFolder` skips, creating nothing, in a
  project where the FNS family is not registered; the family asks for a sync
  when it initialises, so installing it fills the folder.
- `CatalogProblems` refuses an unknown companion kind and a companion that
  is itself a member.

## Optional, and easy to turn off (2026-09-17)

Owner decision: some users want the family operators in their palette
without a new tab in the OP Create dialog. A member no longer forces the
family.

- **The picker asks.** While a family operator is ticked, the selection bar
  shows "Add FNS tab to OP Create", on by default. The selection always
  carries `family` when the release has a companion. Served, the switch
  starts from the project: members installed without the family read as
  off. Turning it off (or unticking the last member) counts as a change,
  so Apply removes the family.
- **The installer honours it.** `ResolvePlan` adds the companion only when a
  member is selected AND `FamilyWanted` agrees. A bool `family` decides. A
  selection that does not say (an agent's minimal request, an older
  selection.json) keeps the project as it is, so adding a member never
  brings back a tab someone removed. A project with no member yet gets it.
- **It is remembered.** The root's `last_install` record carries `family`
  (was FNS_OpFamily installed), so "Set up like last time" and Always Set
  Up Like Last Time repeat it. The site's paste script adds the family with
  a free family pick unless the switch is off.
- **Turning it off later** is the same switch in Pick Tools, or the family's
  **Remove Operator Family** command, which calls the installer's
  `RemoveFamily()`. That refuses the source checkout, removes through
  `RemoveTools` like any picker removal, and runs a frame after the command
  returns because it destroys the component the command lives on.
- **A root toggle.** The toolkit root's FNSTools page has **FNS Tab in OP
  Create** (`Opfamily`, `build_installer.ROOT_PROJECT_TOGGLES`). It mirrors
  the project: `InstallerExt.SyncFamilyToggle` runs after every install and
  removal and on the installer's init. Flipping it calls `SetFamily(on)`
  through the root forwarder, deferred a frame. Off is `RemoveFamily`. On
  installs the family beside the family operators already there (a minimal
  plan with `family: true`), downloads it first when the store lacks it and
  finishes when the store job ends (`familyWhenFetched`), and refuses with
  no family operator installed. A refusal puts the toggle back. The root's
  config host excludes it (`Excludepars`), so it never roams: restoring
  settings in another project must not add or remove anything there.
- **The tab leaves at once.** TDFam never prunes a destroyed owner, so
  `RemoveTools` unregisters every family a component owns before it destroys
  it (`_releaseFamilies`). The `/sys` TDFam registry itself stays until
  TouchDesigner restarts; with no family registered it shows nothing.

## Measured on the way

- **Never read a promoted member of the owner in `onDestroyTD`.** The first
  cut released the family from TDFam in the family's own `onDestroyTD` and
  read `self.ownerComp.Properties` there. A reinit runs that hook too, and
  the promoted lookup waited on the extensions being rebuilt: TouchDesigner's
  main thread parked on that line with flat CPU (py-spy, 2026-09-17) and
  never came back. The release moved into the installer, before the destroy.

- **A type with capitals never comes back from a stub.** TDFam keys its
  folder cache by the lowercased type, and `replace_stub` and the updater
  look the manifest's `op_type` up verbatim. `switchTools` placed, stubbed,
  and then `replace_stubs_batch` returned nothing. With `switchtools` the
  round trip worked: 4 connectors as a stub, 32 children back, `Index` kept.
- **TDFam finds placed operators across the whole project by manifest tag,
  so it found the member masters in the toolkit container.** Its own Create
  Stubs (All) would have stubbed them and Update (All) replaced them from
  the family folder. The family's callbacks DAT now returns False from
  `onPreStub`, `onPreReplace` and `onPreUpdate` for anything inside the
  container that holds the family (masters and doorstep copies belong to the
  FNS updater), and the commands filter the same way.
- **A copy of the family initialises while the old one still holds the
  name**, so it neither registers nor installs; unregister the old owner
  (`UnregisterFamily(owner)`, which takes the COMP, not the name), then
  `RegisterFamily(new)` and `Install(True)`.
- **One boot-path modal remains in TDFam**: two TDFamRegistry copies whose
  major versions differ prompt "Registry Version Conflict" during
  promotion. Not changed here (TDFam is upstream); a project that mixes
  TDFam majors will see it.

## Still open

- ParRetain and StateRetain are empty on every member: which parameters and
  state survive a stub or an update is the owner's to curate in the CMS.
- The FNS tab is empty until a release publishes the family blocks: the
  store's manifest (v3.2.25) predates them, and the sync mirrors only rows
  that declare one. RandomCHOP has never been released.
- A cold boot with the family in the toolkit has not been run.
- Whether the Hub should offer "stub all" before a project is handed over.

## The research (2026-09-10)


Owner's question, 2026-09-10: "similarly to how we register a tool to install
as an OpTemplate from disk, we could dedicate some tools as part of a new
operator family" -- TDFam, dotsimulate/TDFam, folder-based families with
manifests.

## What TDFam is, exactly (read 2026-09-10)

Source: the README and `docs/{concepts,manifest-reference,callbacks-and-api,
licensing}.md` of dotsimulate/TDFam, plus the live `/TDFam_create` (package
1.0.1) and `/T3D_1_13_2` in this project.

- **One `TDFam_create` COMP per family.** It carries the family name, colour,
  `Index` (tab order in the OP Create dialog), the operator sources, a
  callbacks DAT and a nested `TDFamRegistry` template that promotes itself to
  `/sys/TDFamRegistry` (`op.FAMREGISTRY`); highest registry version wins.
- **Two operator sources, either or both.** Embedded: COMPs inside the
  `Opcomp` folder. File-based: `.tox` files in `Opfolder`, named by a
  configurable regex whose default is `(.+)_v(\d+\.\d+\.\d+)\.tox$`; a
  subfolder is a category. When both sources carry the same op, the higher
  version wins; ties go to embedded.
- **Manifests.** Every op carries a `FamManifest` base with four DATs:
  `OpInfo` (identity and menu: `op_type`, `op_name`, `op_label`,
  `op_version`, `fam_version`, `op_fam`, `op_group`, `summary`, `doc_url`,
  `op_color`, `isFilter`, `compatible_types`, `search_words`, `pop_menu`),
  `ParRetain` (which pars survive a stub or an update), `StateRetain`
  (extension storage, COMP storage, DAT contents that survive), `Shortcuts`
  (`{"ctrl.shift.b": "Bypass", ...}`). File-based ops carry the same as a
  sidecar `<tox name>.json` (`{"OpInfo": {...}, "ParRetain": {...}, ...}`) or
  a folder-level `manifest.json` keyed by normalised op name.
- **Surface.** `Install` on: the family registers, and `GlobalUIInjector`
  gives it a tab in the OP Create dialog (`inject_opfam_registry` sits at the
  head of the node-table chain, before our `families` anchor -- the two
  injections coexist today, T3D is installed here). `PlaceOp(target,
  op_type, name, x, y)` prepares a clone, validates the manifest, applies
  colour and shortcuts, places.
- **Lifecycle we do not have.** `StubOp` turns a placed op into a
  lightweight placeholder that keeps wiring, position and the retained pars
  and state, so a project can travel without the family; `UpdateOp` upgrades
  a placed op in place to the newest version with `ParRetain`/`StateRetain`
  applied. Hooks: `onPlaceOp`/`onPostPlaceOp`, pre/post stub, replace,
  update, install, `onDeployManifest`, and manifest-declared pop-menu
  callbacks.
- **Licence.** Apache-2.0, copyright Lyell Hintz and Dan Molnar. Redistribution
  inside a third-party toolkit, commercially, is allowed provided the
  Apache-2.0 notices and the `NOTICE` file ship, with the suggested visible
  credit "Built with TDFam".

## What we already have that lines up

- **A family named `FNS` already exists** at `/TDFam_create` in this project:
  installed, UI installed, `Index -1`, zero operators (`Opcomp` and
  `Opfolder` empty), tagged `<FAM>`. Its tab is live and empty in the OP
  Create dialog now.
- **The store** (`Palette/FNStools_ext/store/<name>.tox`, flat) plus the
  cached manifest with `name`, `version`, `title`, `description`,
  `category`, `placement`, `alternatives_for`, `help_url`. Presence on disk
  is the availability rule for alternatives (docs/OpAlternatives.md) and would
  be for family membership.
- **A derivation rail.** `build_manifest` reads facts off the live package at
  build (`surfaces`, `alternatives_for` via a callbacks hook); a hostless or
  foreign package curates the same key in the catalog and the content CMS
  edits it. Family membership fits the identical pattern.
- **A placement class.** `placement: pane` already means "an operator-like
  component spawned into the working network, frozen at its spawn version".
  A family member is that class of tool, with a better answer to the frozen
  version (TDFam's `UpdateOp`).

## The proposed shape

1. **Membership is declared in the tool, derived at build.** A member tool
   carries TDFam's own `FamManifest/OpInfo` (TDFam's `DeployManifests` writes
   it; the fields are TDFam's, not ours). `build_manifest` reads it and writes
   a `family` block into our manifest: `{op_type, op_label, op_group,
   isFilter, compatible_types, summary}`. A foreign or hostless package may
   curate the block in the catalog, edited in the CMS, under the same
   "derived beats curated, never both" rule as `alternatives_for`. One
   source of truth per package.
2. **The updater maintains the family folder.** For every member package
   whose tox is in the store, `FNS_Updater` mirrors it into
   `Palette/FNStools_ext/family/FNS/<op_group>/<name>_v<version>.tox` with a
   sidecar `<name>_v<version>.json` built from the manifest's `family` block
   (`OpInfo`) and any `ParRetain`/`StateRetain`/`Shortcuts` the tool ships.
   Download, update and removal keep the mirror in step and drop stale
   versions. Only members are mirrored, so no other store tox ever appears
   as an operator (TDFam lists every tox it finds in `Opfolder`). The store
   stays flat and untouched.
3. **The family ships as a package.** `FNS_OpFamily`: the `TDFam_create` COMP
   named `FNS`, network-root placement, `Opfolder` an expression on the user
   palette folder, `Installonstart` on, its nested `TDFamRegistry` promoting
   as TDFam designed. `NOTICE` and the Apache-2.0 text ride inside it; the
   About and the docs page carry the "Built with TDFam" credit.
4. **Alternatives and family are two doors to one tox.** A member is its own
   type in the FNS tab; it may also declare `alternatives_for` and be offered
   when a stock type is created. Neither mechanism needs the other; both
   read the same store.

### Considered and rejected

- **Embedded members** (`Opcomp`): copying member tools into the family COMP
  makes every member resident in every project that has the family. The
  point of the store is placement from disk.
- **Pointing `Opfolder` at the store itself** with a permissive naming
  regex: TDFam would list every store tox as an operator, and versions live
  in our manifest, not in file names. A derived mirror keeps both models
  whole.

## Decisions that are the owner's

- **Which tools.** Only operator-like components qualify: something that
  reads as one node with inputs and outputs (the whole-COMP alternative
  convention, In/Out ops of one family). Naming candidates here would be
  guessing.
- **Family name and colour.** `FNS` exists; keep it, or a product name.
- **Whether membership implies `placement: pane`.** It probably should: a
  family op is placed into the working network by definition.
- **What `ParRetain`/`StateRetain` each member declares.** Without them an
  update keeps nothing; with them TDFam's in-place update is the answer to
  "instances stay at their spawn version".
- **Stubs in shipped projects.** Whether the FNS Hub should offer "stub all
  FNS family ops" before a project is handed to someone without the toolkit.

## The other door: rows inside TD's own COMP family (researched 2026-09-10)

Before building the family, the owner asked what it would take to list tools
inside the COMP tab itself. Read off `/ui/dialogs/menu_op` in 2025.33070:

- **Rows are a table.** `nodetable/families` (a Script DAT fed by TD's
  built-in op-type list, objects with `.type .label .OPType .isFilter
  .isCustom .licenseType ...`) emits one row per type for the current
  family: `name, label, type, subtype, mininputs, maxinputs, ordering,
  level, lictype, os, score, family, opType`. `type` is the layout
  (`layouts/COMP/defGenerator`, `defFilter`, `...Disable`). Our registry's
  chain stages (`onChainNodes`, `script_inject`) already rewrite this table
  downstream of `families`; appending rows for family `COMP` is the same
  mechanism, with the dialog's search string applied by the stage since the
  native scoring ran upstream.
- **A click runs a Tscript, and it has a hook for exactly this.**
  `node_script` (panel execute on `nodetable`, `cellselectid`) switches to
  `create_node`, which reads the clicked row from `node_detail` and, when
  the row's `ordering` is `custom`, does `run $controlpanel/customCOMPs/$operator
  $menu_pane` and exits, never touching `opadd`. `customCOMPs` still exists
  in the dialog with one legacy script (`camwlookat`, TD's old Camera+Lookat
  custom COMP, Tscript ending in `opplace -p $pane`). A Python DAT there
  receives the pane as `args[0]`, so a registry-owned `customCOMPs/<name>`
  script can load the tool (live COMP copy or store tox, the alternatives
  engine's two placements) and hand it to `ui.panes[pane].placeOPs`, then
  close the dialog (`parent.OPCREATE.par.winclose`), which the custom branch
  does not do itself.
- **Hover help is a table too.** `summaries[family + ' ' + label]` feeds the
  help strip; rows can be added for ours.
- **TDFam does not use this hook.** It substitutes the whole table for its
  own families, patches `create_node` (`# OPFAM_START ... exit`) to keep
  `opadd` out, and places from its own panel execute. Nothing in it appends
  to a native family; adding that would mean teaching its interceptor about
  COMP clicks, which is more invasive than the dormant native hook.

So a COMP-family listing is a registry contribution, not a family: an
`onCompRows()` hook (or the store's manifest block) naming `{label, source,
isFilter, help}`, a stage that appends the rows under `COMP` with
`ordering=custom`, one registry-managed script per row in `customCOMPs`
(tagged and pruned like chain stages), and a `summaries` row. Placement
reuses `_placeComp` / `_placeTox`; the watcher re-baselines after. About a
day, no TDFam involved, no manifests beyond the catalog. What it does not
give: stubs and in-place updates, which are TDFam's. The two are
complementary, and one tool can be both a COMP-tab row and a family member.

## Cost

The updater mirror is the only real code: a folder writer keyed off the
manifest's `family` block, run at download, update and remove (about a day
with tests). The build derivation and the CMS field are the `alternatives_for`
pattern again, an hour each. The package is a `TDFam_create` with three
parameters set. Nothing in TDFam needs changing.

## Not in scope

Changing TDFam itself; migrating T3D; making every FNS tool a family op.

## Consideration, 2026-09-17: the store is complete now

`docs/StoreCompleteness.md`: with the updater's `Keepstore` toggle (default
on) every install and update pass ends by mirroring the rest of the release
into the machine's store, and a full mirror's completion calls one hook,
`ExtUpdater._afterStoreComplete(status)`. Two things follow for this plan:
criterion 4's "every member whose tox is in the store" becomes every
member on any machine with the default on, so the FNS tab is complete
offline; and the family folder sync has one place to run from (that hook)
instead of three (after download, update and remove), since a remove pass
does not change what the store holds. Nothing here is built yet; the hook
only logs.
