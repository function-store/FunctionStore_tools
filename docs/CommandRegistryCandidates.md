# FNS_CommandRegistry — command candidates survey

Survey of every FunctionStore tool for actions worth registering in the
TDXLU launcher's quick-launch palette (`>` / `?` prefixes) via
`FNS_CommandRegistry`. Compiled 2026-08-21 from the live network: tool-root
custom pars (pulses / toggles / menus) plus public methods in each tool's
extension DATs.

Contract: `C:/VJ/TD/Projects/TDXLPP/docs/fns-command-registry.md`
(registry 1.2.0 — decorator + announce). Authoring module `FNSCommand` is
in every tool's docked ExtUtils since the 2026-08-21 clone rollout, so any
tool below can adopt the two-touch pattern:

```python
FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand')

class MyToolExt:
	@FNSCommand.fns_command(help='...')
	def DoThing(self, amount: float = 1.0):
		...
	def onInitTD(self):
		run('args[0]._announceCommands()', self, delayFrames=60)
	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)
```

**How to read the tables** — `Status` is yours: mark `yes` / `no` /
`later`, add notes inline. `Source` names the existing par or ext method
the command would wrap. Labels are palette-row drafts; ids become muscle
memory (`? rec 1`), so bikeshed them here, not after shipping.

> **IMPLEMENTED 2026-08-21** — Tiers 1–5 + Second sweep are LIVE:
> 81 commands from 42 owners, saved to suspects + .toe. Skipped (need
> design): iopPromoter PromoteIop, PaneTypeRegistry RecallPanel,
> OpTemplates PlaceTemplate, AutoRes SetRes, MY_HOTKEYS search-palette
> mirror.
>
> **Built-in TD commands: DONE TDXLPP-side** (evening, registry 1.4.0 /
> utility 0.16.0) — implemented as `TD_UI` + `TD_Project` comps in the
> launcher companion, exactly the ownership this doc recommended. They
> carry the new `builtin=True` flag: badged COMMAND, ranked in `>` after
> tool commands, kept out of `?`. **FNS tools should not normally set
> `builtin`** — none of the 81 rows here do, which is correct as-is.

---

## Tier 1 — performance / global actions (run from anywhere, mid-set)

| Status | Tool | Command (label draft) | Source | Notes |
|---|---|---|---|---|
| | ResetPLS1 | Reset all generators | `Reset` pulse | The VJ panic button. Highest-value row in the whole survey |
| | HideTimeline | Toggle timeline | `Hidetimeline` / `Enabletimeline` | Classic. BorderlessTD root mirrors these toggles — register on HideTimeline, not both |
| | BorderlessWindow | Toggle borderless | `Borderless` toggle | |
| | BorderlessWindow | Toggle fullscreen | `Fullscreen` toggle | |
| | GlobalVolControl | Toggle mute | `Mute` toggle | |
| | GlobalVolControl | Set volume | slider widget value | `params`: `level` float 0–1, required |
| | QuickTime | Reset timer | `Reset` pulse | |
| | HydroHomie | Toggle reminder | `display` via ext (pattern proven 2026-08-21) | |
| | HydroHomie | Set reminder interval | `Intervalminutes` | `params`: `minutes` float, default from par |
| | OUTPUT | Toggle NDI output **(new)** | `ndiout1.active` | |
| | OUTPUT | Toggle Spout/Syphon output **(new)** | `syphonspoutout1.active` | Sender name `TD_FNS_OUT` |
| | OUTPUT | Toggle perform window **(new)** | `button_perform` | Confirmed: help DAT says "Perform Window" |

## Tier 2 — editing actions on current selection

| Status | Tool | Command (label draft) | Source | Notes |
|---|---|---|---|---|
| | SwapOps | Swap selected ops | `Swap` pulse | |
| | SetSmoothness | Smoothness → selected | `Selected` pulse / `OnSelected` | `params`: `value` float? Check what the pulses apply |
| | SetSmoothness | Smoothness → all | `All` pulse / `OnAll` | |
| | paste_from_clipboard | Paste image | `Pasteimage` pulse | Palette-perfect trio |
| | paste_from_clipboard | Paste as Script TOP | `Pastescriptop` pulse | |
| | paste_from_clipboard | Paste as annotate | `Pasteannotate` pulse | |
| | ParRandomizer | Randomize rollover par | `OnRandomizeRolloverPar` | Rollover-dependent — verify it still resolves when palette has focus |
| | ParRandomizer | Randomize all pars of op | `OnRandomizeOp(_op=None)` | Randomizes the whole op (defaults to current/rollover). Per-page filtering would be a small ext addition — `RandomizePar` exists as the per-par primitive |
| | ParRandomizer | Reset custom pars to defaults | `OnResetAllCustom` | |
| | ParRandomizer | Save custom defaults | `SaveAllCustomDefaults` | |
| | CustomParTools | Promote pars of selected | `Promote` pulse / `DoPromoteAll` | |
| | QuickCollapse | Collapse selected | `OnCollapse` | Currently hotkey-driven; palette row is a natural alias |
| | VSCodeTools | Externalize selected | `Externalizeselected` pulse | |
| | VSCodeTools | Deploy stubs | `Deploystubs` pulse | |
| | OpToClipboard | Copy op to clipboard | `OnCopy` | Selection/rollover-dependent — same caveat as ParRandomizer |
| | QuickExt | Create extension on selected **(new)** | `ExtQuickExt.CreateExtension` | The QuickExt core action — natural `? ext` row |
| | ClearPars | Clear custom pars of selected **(new)** | `ClearParsExt.ClearPars` | Destructive-ish — explicit `help` text |
| | QuickParent | Add parent shortcut **(new)** | `QuickParentExt.AddParentshortcut` | `params`: `name` str? Check whether it derives the name or asks |
| | iopPromoter | Promote iops of selected **(new)** | `ExtIopPromoter.PromoteIop` | |
| | OpenExt | Open extension of selected **(new)** | `ExtOpenExt.OnOpen` | Jump straight into a COMP's ext code |

## Tier 3 — navigation & quickmarks (inline args shine here)

| Status | Tool | Command (label draft) | Source | Notes |
|---|---|---|---|---|
| | QuickMarks | Go to quickmark | `RetrieveQuickmark` | `params`: `slot` int required → `? mark 3` runs instantly |
| | QuickMarks | Store quickmark | `StoreQuickmark` | `params`: `slot` int |
| | QuickMarks | Clear quickmark | `UnstoreQuickmark` | `params`: `slot` int |
| | FNS_PaneTypeRegistry | Floating network editor | `OpenFloatingNetworkEditor` | |
| | FNS_PaneTypeRegistry | Recall panel | `RecallPanel` | `params`: `panel` menu if the panel list is ≤16 |
| | PreviewPanel25 / POPtoDAT_panel | Open preview panel | `Winopen` pulse | |

## Tier 4 — UI openers, config & maintenance

| Status | Tool | Command (label draft) | Source | Notes |
|---|---|---|---|---|
| | FNS_HotkeyManager | Open hotkey UI | `Openui` / `OpenUI` | |
| | FNS_HotkeyManager | Save hotkeys | `Savehotkeys` | |
| | FNS_HotkeyManager | Load hotkeys | `Loadhotkeys` | |
| | ColorUI | Open color UI | `Openui` / `OpenUI` | |
| | ColorUI | Randomize colors | `Randomize` | With `UndoRandom` as sibling row |
| | ColorUI | Undo randomize | `UndoRandom` | |
| | ColorUI | Reset all colors | `ResetAll` | |
| | ColorUI | Import / Export palette | `Import` / `Export` pulses | Two rows |
| | FNS_Config (global) | Save all tool configs | `SaveAll` | Genuinely useful project-wide; owner = FNS_ConfigHost or the /sys global? Decide — /sys global would need its own announce leg |
| | FNS_Config (global) | Load all tool configs | `LoadAll` | |
| | FNS_Config (global) | Open settings UI | `OpenSettingsUI` | |
| | FNS_Toolbar | Open toolbar configurator | `Open` pulse / `OpenConfigurator` | |
| | FNS_Navbar | Open navbar configurator | `OpenConfigurator` (registry ext) | Owner should be the tool, not the /sys registry |
| | FNS_MainMenu | Open mainmenu configurator | `OpenConfigurator` | |
| | FNS_OpMenu | Resync op menu | `Resync` (OpMenuRegistryExt) | |
| | ExprHotStrings | Open hot-strings editor | `Open` pulse | |
| | OpTemplates | Open templates | `Opentemplates` / `OpenTemplatesFloating` | |
| | OpTemplates | Save templates | `Savetemplates` | |
| | OpTemplates | Refresh templates | `Refreshtemplates` | |
| | OpTemplates | Add to templates | `OpTemplateExt.TemplateSave` | Saves current selection as template (`DropOp(_op)` is the per-op entry) |
| | OpTemplates | Place template **(new)** | `PlaceTemplate(orig_op, template_ops)` | `params`: `template` menu from the template list if ≤16 — `? tpl noisefeedback` |
| | VSCodeTools | Open project in VSCode | `Open` pulse | |
| | FNS_Updater | Check for updates | `Check` | |
| | FNS_Updater | Update tools | `Update` | Long-running — must kick off with `run(delayFrames=1)` and return immediately |

## Tier 5 — mode toggles (one identical pattern, opt-in per tool)

Each of these exposes a single `Active` toggle; the command is
`Toggle <tool>` (`? altselect`). Cheap via the decorator, but 12 near-identical
rows — curate rather than blanket-enable.

| Status | Tool | Notes |
|---|---|---|
| | AltSelect | |
| | AutoRes | Also has `SetRes` ext method — a `Set resolution` command with `w`/`h` int params could be Tier 1 material |
| | AutoCombine | |
| | QuickCollapse | |
| | QuickParCustom | |
| | OpToClipboard | |
| | ParRandomizer | |
| | ParOPDrop | |
| | QuickPane | |
| | SwitchOPs | |
| | QuickMarks | |
| | mapTables / ExternalTables | |

## Second sweep — hog, hotkey mirrors, pane & config actions **(new)**

Mined 2026-08-21 (second pass): MISC buttons, MY_HOTKEYS keyboard handlers,
QuickPane's ext, ResetPLS1's config openers.

| Status | Tool | Command (label draft) | Source | Notes |
|---|---|---|---|---|
| | MISC/button_hog | Toggle hog | `button_hog` (Global Hog CHOP) | Deliberate frame-time eater for stress testing — help text should say so loudly |
| | MISC/input_mouse | Toggle global mouse input | `input_mouse` (Global Mouse CHOP) | Feeds the mouse CHOP used for mappings |
| | QuickPane | Split pane | `QuickPaneExt.OnOpenDir(dir='left')` | `params`: `dir` menu left/right/top/bottom → `? split right`. (Earlier guess "filesystem dir" was wrong — it splits the current pane) |
| | MY_HOTKEYS | Open current COMP parameters | `keyboardin_currparam` handler | Hotkey-only today; palette row makes it discoverable. Action body lives in keyboardin callbacks — wrap in a promoted method |
| | MY_HOTKEYS | Open parent COMP parameters | `keyboardin_parentparam` handler | |
| | MY_HOTKEYS | Customize current COMP | `keyboardin_currcompedit` handler | Component editor on current COMP |
| | MY_HOTKEYS | Customize parent COMP | `keyboardin_parentcompedit` handler | |
| | MY_HOTKEYS | Open search palette | `keyboardin_searchpalette` handler | Overlaps TDX_SearchPalette — one owner, not both |
| | ResetPLS1 | Edit static exceptions | `Open2` pulse ("Static Exceptions") | |
| | ResetPLS1 | Edit custom reset pars | `Open3` pulse ("Edit Custom Reset Pars") | |

## Built-in TD commands **(new)** — from the official Python API

Scoured 2026-08-21 from the offline doc mirror: [UI Class](https://docs.derivative.ca/UI_Class),
[Project Class](https://docs.derivative.ca/Project_Class),
[App Class](https://derivative.ca/UserGuide/App_Class),
[Pane Class](https://docs.derivative.ca/Pane_Class),
[Undo Class](https://docs.derivative.ca/Undo_Class),
[TDFunctions](https://docs.derivative.ca/TDFunctions).
These aren't tool actions — they're TD itself. **Ownership question to
decide first**: the natural owner is the launcher's own companion
(TDXLauncherUtility ships an `FNS_TDCommands` base registering them), NOT a
FunctionStore tool — they should work in projects with no FNS tools
installed. Note the 24-commands-per-tool cap: the full list below exceeds
it, so either curate or split across two owners (`td-dialogs` +
`td-session`).

> **IMPLEMENTED 2026-08-21** (TDXLPP utility 0.15.0): two owners inside
> the companion — **`TD_UI`** (dialogs & windows + panes, 22 commands)
> and **`TD_Project`** (project & session + performance + files, 16),
> both decorator-based with vendored `fns_command`, self-tagging +
> announcing on init. Every API name verified against the live runtime;
> PaneType turned out to have NINE members (adds `opbrowser` +
> `parameters` to the list below). `set cook rate` and `toggle power`
> ship `hidden=True`; undo/redo skipped per the note; "load recent"
> became an int `index` param (1 = most recent) since spec menus are
> registration-time snapshots and recent files churn. Window openers
> defer a frame so the bus reply escapes; load/quit defer 30. Status
> `yes` below = shipped in `TDXLPP/utility/TDXLauncherUtility/
> TD_UI/TDUIExt.py` + `TD_Project/TDProjectExt.py`.

### Dialogs & windows (`ui.open*` — one-liners, zero risk)

| Status | Command (label draft) | Source | Notes |
|---|---|---|---|
| yes | Open textport | `ui.openTextport()` | |
| yes | Open errors dialog | `ui.openErrors()` | |
| yes | Open console window | `ui.openConsole()` | The OS-level console, not textport |
| yes | Open performance monitor | `ui.openPerformanceMonitor()` | |
| yes | Open beat dialog | `ui.openBeat()` | Tap-tempo — mid-set relevant |
| yes | Open bookmarks | `ui.openBookmarks()` | |
| yes | Open key manager | `ui.openKeyManager()` | |
| yes | Open MIDI device mapper | `ui.openMIDIDeviceMapper()` | Pairs with midiMapper tool |
| yes | Open palette browser | `ui.openPaletteBrowser()` / `ui.showPaletteBrowser` toggle | Toggle form is nicer |
| yes | Open operator snippets | `ui.openOperatorSnippets(optype=?)` | `params`: optional `optype` str → `? snip noiseTOP` |
| yes | Open preferences | `ui.openPreferences()` | |
| yes | Open window placement | `ui.openWindowPlacement()` | |
| yes | Open search/replace | `ui.openSearch()` | Overlaps TDX_SearchPalette/MY_HOTKEYS rows — pick one |
| yes | Import file… | `ui.openImportFile()` | |
| yes | Export movie… | `ui.openExportMovie(path)` | `params`: `op` str path, default current/selected |
| yes | Open version info | `ui.openVersion()` | |

### Project & session ([Project Class](https://docs.derivative.ca/Project_Class))

| Status | Command (label draft) | Source | Notes |
|---|---|---|---|
| yes | Save project | `project.save()` | Increments filename — the standard save. The single most palette-worthy built-in |
| yes | Save project + external toxes | `project.save(saveExternalToxs=True)` | Separate row; explicit help text |
| yes | Load recent file | `project.load(path)` + `app.recentFiles` | `params`: `file` menu from `app.recentFiles[:16]` → `? recent 2`. Quits current session — confirm-worthy |
| yes | Quit TouchDesigner | `project.quit()` | Prompts for unsaved changes by default (never `force=True` from a palette) |
| yes | Toggle realtime | `project.realTime` | Classic render-mode flip |
| yes | Set cook rate | `project.cookRate = x` | `params`: `fps` float |
| yes | Toggle window on top | `project.windowOnTop` | |
| yes | Toggle perform-on-start | `project.performOnStart` | |

### Performance & playback

| Status | Command (label draft) | Source | Notes |
|---|---|---|---|
| yes | Toggle perform mode | `ui.performMode` | Overlaps OUTPUT `button_perform` row — decide which owns it |
| yes | Toggle power | `app.power` | The big master switch — halts ALL processing. Footgun-adjacent; loud help text |
| yes | Set master volume | `ui.masterVolume = x` | Overlaps GlobalVolControl — pick one owner |
| no | Undo / Redo | `ui.undo.undo()` / `.redo()` | Ctrl+Z exists; palette value dubious — mark no unless wanted for macros |

### Panes & navigation ([Pane Class](https://docs.derivative.ca/Pane_Class), TDFunctions)

| Status | Command (label draft) | Source | Notes |
|---|---|---|---|
| yes | Maximize current pane | `ui.panes.current.maximize` toggle | |
| yes | Tear away current pane | `ui.panes.current.tearAway()` | |
| yes | Change pane type | `pane.changeType(PaneType.X)` | `params`: `type` menu (8 PaneType values) → `? pane topviewer` |
| yes | Floating copy of pane | `ui.panes.current.floatingCopy()` | |
| yes | Show op in floating pane | `TDFunctions.showInPane(op, pane='Floating')` | `params`: `path` str → `? show /project1/geo1`. Navigation gem |
| yes | Home network view | NetworkEditor `home()` | Verify exact signature on NetworkEditor Class before building |

### Clipboard, files & folders ([App Class](https://derivative.ca/UserGuide/App_Class), `ui.viewFile`)

| Status | Command (label draft) | Source | Notes |
|---|---|---|---|
| yes | Open project folder | `ui.viewFile(project.folder)` | Explorer/Finder on the .toe's folder — daily-driver row |
| yes | Open TD folder… | `ui.viewFile(app.<x>Folder)` | `params`: `folder` menu — userPalette / desktop / temp / preferences / bin / samples / install |
| yes | Copy current op path | `ui.clipboard = <op>.path` | Uses selected/rollover op; pairs with OpToClipboard tool |
| yes | Open selected op parameters | `op.openParameters()` ([OP Class](https://docs.derivative.ca/OP_Class)) | Floating par dialog — overlaps MY_HOTKEYS currparam row |
| yes | Open selected op viewer | `op.openViewer()` | |

### Ruled out from the API sweep

- `TDU_Class` / most of `TDFunctions` — math/utility functions
  (`clamp`, `remap`, `getShortcutPath`…), no user-facing actions.
- `project.addPrivacy` / `addNonCommercialLimit` / `addResolutionLimit` —
  destructive session-level restrictions; never palette material.
- `ui.messageBox` / `chooseFile` / `chooseFolder` — building blocks for
  command params, not commands themselves.

## Deliberately excluded

- **Registry plumbing** — `Register`, `Createcallbacks`, `Presaveheal`,
  `Promotepars` on every `FNS_*Registry` host: infrastructure, not user
  actions.
- **FNS_About boilerplate** — `Deploy` / `Openhelp` / `Openauthor` exist on
  ~40 About boxes. Registering them all floods the palette. Alternative:
  ONE `Open tool help` command with a `tool` menu param (menu cap is 16 —
  would need a curated list or `str` free-typing).
- **midiMapper / oscMapper roots** — cook-disabled COMPs
  (`allowCooking=False`) cannot compile extensions, so they cannot own
  commands (RegistryScheme hazard list). Their actions surface via
  MIDIResetPLS, or need an always-cooking wrapper.
- **docsHelper / private_investigator / kindergaertner** — dev-time tooling,
  not launcher material.
- **tools_ui internals** — panel chrome, no standalone actions. (OUTPUT
  turned out to carry real candidates — NDI/Spout toggles, promoted to
  Tier 1 above.)
- ~~MISC/button_hog / input_mouse~~ — moved to the Second sweep section
  above at user request.
- **PreviewPanel25 ext internals** — all drop-handler plumbing
  (`onOpDrop`, `set*State`); the only palette action is the `Winopen` row
  already in Tier 3.

## Implementation notes (read before building)

1. **Registry version gate** *(updated 2026-08-21 evening)*. The live
   `/sys` global is now **1.2.0** (shipper Repromoted) — decorator
   harvest + `params` work TODAY. The **1.3.0** contract (`hidden` on
   the wire, launcher-side curation + presets) needs the utility 0.14.0
   companion injected; the `FNSCommand` module side is already 1.3.0
   everywhere (master + all 66 clones carry `hidden=`), so decorated
   code written now with `hidden=True` is forward-compatible — the
   field simply starts riding once the newer registry lands.
2. **`hidden=True` defaults (registry ≥ 1.3.0)** — "advanced" rows the
   palette hides until the user opts in (Settings → Quick Launch).
   Suggested: ClearPars, hog/mouse toggles, ResetPLS1's two config
   editors, FNS_OpMenu Resync, VSCodeTools Deploy stubs, FNS_Config
   Load-all, `app.power`, set-cook-rate. Curation can override either
   way, so this is a default, not a lockout.
3. **Ids are permanent** — launcher curation AND user-authored presets
   key on `tool#id`; a renamed id (or COMP) orphans the user's history,
   visibility overrides, and presets in one stroke. Treat every id in
   this doc as shipped API once implemented.
4. **Handlers must be quick.** `Run` is synchronous on the main thread —
   `FNS_Updater.Update` and anything opening windows should
   `run(..., delayFrames=1)` and return.
5. **Rollover/selection-dependent commands** (ParRandomizer,
   OpToClipboard, SwapOps) act on `ui.panes` state — verify the palette
   overlay doesn't steal the context they read before promising them.
6. **Owner choice for registry-backed tools**: register on the TOOL comp
   (FNS_Navbar, FNS_OpMenu…), not the /sys globals — globals get replaced
   on version bumps and are stripped of Registration state.
7. **Per-tool cap is 24 commands, 6 params each, menu ≤16** — nothing
   above approaches the cap.
8. **Suggested first batch** (pattern-proving spread): ResetPLS1 (pulse),
   HideTimeline (toggle), QuickMarks (int param + inline args),
   GlobalVolControl (float param), FNS_HotkeyManager (UI opener).

---

*Edit freely — Status column + inline notes are the contract for the
implementation pass.*
