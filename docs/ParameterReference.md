---
status: in-force
summary: Every package's customization parameters are documented by their own `help` text — harvested live into packaging/parameters.json, rendered on each tool's docs page, and authored from the FNS_CMS Parameters tab. One string is the tooltip and the documentation. Also owns the surface vocabulary — what a package puts on screen — that the docs filter and the picker search share.
since: 2026-08-30 (rail built and the roster brought to 558/558 in one pass)
verified: 2026-08-30 — measured live across all 49 packages; site build emits 48 parameter tables and zero "Not documented yet" rows. Re-verified same day after the §6 removal: 555/555, three dead pars gone.
skill: fns-packaging
---

# The parameter reference: the tooltip *is* the documentation

A tool's customization surface is its custom parameters, and until this
landed the only place they were described was the parameter dialog — where
**61% of them said nothing at all**. Measured before the work: 362
user-facing controls, 141 with `help`. The two docs that did list
parameters ([VSCodeTools.md](../packaging/docs/VSCodeTools.md),
[FNS_ConfigRegistry.md](../packaging/docs/FNS_ConfigRegistry.md)) had
hand-written them, which is the arrangement that always drifts.

## 1. The rule

**A parameter's `help` is the single source of truth for what it does.**
It is the tooltip in TouchDesigner and the description on the docs page —
the same string, never a copy of one.

There is deliberately **no `help` field in `catalog.json`** and no
parameter table in a `packaging/docs/*.md`. This is the same decision
`build_manifest._helpUrl()` already made for help URLs and
[CmsResearch.md](CmsResearch.md) records: a second place to write
something is a second place for it to go stale. A tooltip written in
TouchDesigner reaches the site at the next build with no prose edited
anywhere.

## 2. What is derived, and where it goes

`build_manifest.Parameters(comp)` walks `comp.customPages` and returns one
row per **tuplet** — an RGBA swatch is four `Par`s behind one label, and
listing `Par`s would document a colour picker as four sliders. Each row
carries `page, name, label, style, default, help`, plus `size`,
`readonly`, `section` and `menu` where they apply.

`BuildParameters()` writes `packaging/parameters.json` in the same live
pass as the manifest, so the two can never describe different projects.

**It is a separate document from `manifest.json` on purpose.** The
manifest is the rolling pointer every installed toolkit re-fetches to ask
"is there a newer version"; it is uploaded, signed and cache-controlled,
and it was 54 KB. The parameter reference is ~200 KB of prose no client
needs to answer that question. It stays in the repo, feeds
`website/tools/build-site.mjs`, and is never uploaded.

| Document | Read by | Uploaded |
|---|---|---|
| `packaging/manifest.json` | every installed toolkit, on every update check | yes, signed |
| `packaging/parameters.json` | the docs build, and nothing else | no |

## 3. What belongs to the tool and what belongs to the toolkit

The boundary was drawn by **measuring**, not by page name, and one
plausible-looking shortcut turned out to be wrong.

* **`Registry` page — wholly stamped.** One section per registry a tool
  publishes into, every section the same stems behind that registry's
  two-character prefix. `Cfautoregister`, `Csautoregister` and
  `Hbautoregister` are one control described three times.
* **`About` page — only the read-only fields are stamped.** The first
  draft treated the whole page as boilerplate. That was wrong: authors
  have parked **19 real controls** there (`Bypass`, `Show Built-in
  Parameters`, `ChatTD Operator`, README pulses), and hiding the page
  would have hidden them from their own documentation. Read-only means
  identity stamp; anything editable stays with its package.
* **`Registration` page — NOT shared.** It exists only on the registry
  packages, where it *is* the package's user surface.
* **`Version Ctrl` — never documented.** `pre_release_common` destroys
  that page on every component before a package ships, so documenting it
  would describe controls no user can ever see.

**Registry sections are filed under the registry that stamps them, not
under one global table.** A tool's page says which registries it joined
and links out; `FNS_ToolbarRegistry`'s page explains what a toolbar
registration adds. The labels are the part that actually differs — the
same `Autoregister` reads "Show in Hub" on one registry and "Expose to
Console" on another — so a single merged table would have had to throw
away the only thing worth reading. The prefix→registry map is derived from
`RegistryBase.TOOL_PAGE_PREFIX` on the registries themselves, so an
eleventh registry needs no entry anywhere.

## 4. Authoring: the FNS_CMS Parameters tab

`/api/parameters` lists every package with its coverage; `/api/parhelp`
writes help onto the live pars and PI-saves the package **once**;
`/api/parexport` regenerates `parameters.json`. The tab is the
**Parameters** button in `website/tools/cms.html`.

Two rules the endpoint enforces:

* **Batched per package.** Each save re-exports the suspect tox, so
  per-keystroke saving would mean a tox write per sentence — and an
  unsaved live par change dies on the next reload (the pi-save discipline
  `_apiHelpurl` already follows).
* **`Registry` and `Version Ctrl` are refused.** They are authored once,
  in `RegistryBase`. Writing them per package would document one copy and
  leave the other 48 saying something else.

## 5. Gaps stay visible

A control with no help is still listed, and its cell says *"Not documented
yet."* A blank cell is indistinguishable from a documented one, and
nobody ever goes back to fill in what they cannot see. The site build
currently emits zero of them.

## 6. What the sweep found

Three things only a complete pass surfaces:

* **`Presaveheal` was undocumented on all ten registries.** Fixed at the
  source — `RegistryBase._ensurePresaveHealPar` now carries the text and
  **re-asserts it on an existing par** instead of returning early, so
  every already-installed registry heals itself on init rather than
  staying blank forever.
* **`paste_from_clipboard`'s `Creator`/`Website` could not be
  documented.** The vendored `dot_chat_util` recreates them on every init
  (`create_parameter(..., replace=True)`), so help assigned afterwards was
  destroyed each time — they were the last two blank controls in the
  toolkit. Fixed by passing the helper's own `help_text=` argument.
* **Three vestigial controls were still shipping — REMOVED 2026-08-30.**
  `FNS_Toolbar`'s `Open Definition` and `Reset Defs` both acted on a
  `ToolbarDef` table that no longer exists, and nothing anywhere read
  `FNS_Updater`'s `Global OP Shortcut`. Documenting them truthfully was the
  stopgap; the pars are now destroyed, both suspects PI-saved, and
  `parameters.json` plus the site rebuilt (24 lines out, nothing else
  touched). Coverage went 558/558 -> **555/555** — the roster shrank, the
  gap stayed zero.

  Two corrections the removal itself produced, both worth keeping because
  the stopgap wording got them wrong:

  * **`Reset Defs` never raised.** The `OnResetdefs` that would have hit
    `None.clear()` lives in
    `modules/suspects/FNSTools/FNS_Toolbar/ExtToolbar.py`, and **that file
    is an orphan** — no DAT in the project binds it, it has no
    `externalizations.tsv` row, and the live extension is a 700-char
    `FNSToolbarExt` whose only method is `OpenToolbarConfigurator`. Measured
    live before removal: `hasattr(comp, 'OnResetdefs')` was `False` and
    pulsing either par produced no error at all. They were **inert**, not
    broken — which is worse, because an inert control looks like it works.
  * **The toolkit root's own `opshortcut` is untouched and stays that way.**
    `Globalopshortcut` was an informational duplicate on `FNS_Updater`;
    `/FNSTools.opshortcut = 'FNS'` is what actually registers `op.FNS`, and
    it is verified still resolving after the removal.

  Verification that the pars were genuinely dead, before destroying them: a
  project-wide sweep of **19,933 operators / 49,311 non-constant parameters**
  found zero expression or bind reference to any of the three, and a
  12,600-DAT text sweep found only Embody's own log FIFO plus the two
  auto-cooked Parameter DATs that regenerate themselves. The earlier sweep
  had only reached `maxDepth=4` inside `/FNSTools`, which would have missed
  the toolbar's `/ui/dialogs/bookmark_bar` copies. The stale
  `Globalopshortcut` key left behind in the roaming config JSON is harmless:
  `ConfigRegistryExt._applyPars` skips a saved par the tool no longer has and
  never recreates it.

## 7. Surfaces: what a package puts on screen

The neighbouring derivation, in the same file and the same document,
because it answers the question a reader has *before* they care about a
parameter: does this tool add a button somewhere, or does it change how
TouchDesigner behaves without appearing anywhere?

`SURFACE_OF` maps a registry to what hosting it gives the user, and
`SURFACE_LABEL` gives the words — **"Toolbar button", never "hosts
ToolbarRegistry"**. Both are published as `surface_meta` (id -> label plus
owning registry) in the manifest's toolkit block and in
`parameters.json`, so the picker and the docs site render the same names
without either keeping a list of its own. Measured today: toolbar 16, hub
8, mainmenu 2, navbar 2, opmenu 2, console 1, timeline 1 — and 23
packages with no surface at all, which is its own useful answer.

Two registries are deliberately outside the vocabulary.
**FNS_ConfigRegistry** is hosted by 37 of 49 packages, so a chip for it
would mark almost everything and separate nothing — and what it grants is
the toolkit's default, not a feature of one tool.
**FNS_PaletteRegistry** has no hosts: the palette tabs it serves appear
without any tool registering
([PaletteTabContract.md](PaletteTabContract.md)).

`surfaces` and `parameters.json`'s `registry_pages` answer **different
questions and must not be merged.** A registry host nested inside a widget
— GlobalVolControl's toolbar button carries its own — earns the package a
toolbar button while leaving the package root's Registry page empty.
Measured: 5 packages differ. `surfaces` says what you get;
`registry_pages` says where those parameters are documented, and using one
for the other points a reader at a page that does not exist.

Two defects fell out of covering the whole vocabulary instead of six of
the ten registries. **FNS_TimelineRegistry** was missing from
`REGISTRY_OWNER`, so `_hostedRegistries` never found it: FNS_TimelineTools
reported no surface *and* did not `require` the registry that carries its
panels — a broken install waiting to happen. **FNS_Console** was in
`REGISTRY_OWNER` but not `SURFACE_OF`, so ColorUI's console tab was
invisible to every surface that lists what a package contributes.
