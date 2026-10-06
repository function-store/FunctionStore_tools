---
status: open
summary: FNS_CommandPalette — an in-TouchDesigner command palette over FNS_CommandRegistry, in a temporary Window COMP with native TD UI. What transfers from the launcher's quick-launch overlay, what cannot, and the decisions still open.
since: 2026-09-01 (logic 5c81a14; window, rows, keys and hotkey landed the same day)
---

# FNS_CommandPalette — design notes

A global tool that opens a temporary Window COMP housing a native TouchDesigner
UI (dynamic Text COMPs) over the commands `FNS_CommandRegistry` already serves.
`packaging/docs/FNS_CommandRegistry.md` anticipated this consumer in as many
words: *"the launcher palette today, an in-TouchDesigner palette next."*

The reference is the TDXLPP launcher's quick-launch overlay,
`TDXLPP/docs/quick-launch-ux.md`. **Built and verified on 2026-09-01: the
logic half in `5c81a14`, the window, rows, keys and summon hotkey the same
day (see Built, below). Open items are listed there too.**

## What we are consuming (measured 2026-09-01)

Registry **1.9.0**, **103 commands**. Every command carries `key`, `tool`, `id`,
`label`, `help`, `path`. Beyond that the set is sparse, and the palette has to
look good on a sparse set rather than assume the rich one:

| Field | Commands carrying it |
|---|---|
| `hidden` | field exists on the payload |
| `state` | 18 truthy |
| `context` | 25 (`current`, `network`, `rollover-par`, `selected`) |
| `capability` | 19 |
| `params` | **7** |
| `surface` | **4**, and only `context-menu` / `session` |

**No command declares a `quick` surface.** A palette that filtered by surface
would show an empty list. So `surface` must be opt-in *narrowing*, never a
requirement — which matches the launcher, where `?` means "tool commands, i.e.
whatever the registry announced".

Only 7 commands declare `params`, so the argument machinery (chips, inline
tokens, prompted walk) is real but rarely exercised. It should not be v1's
centre of gravity.

## What does NOT transfer

Most of the launcher overlay's row taxonomy is about *many sessions and an OS*.
Inside TD there is exactly one session — this one. These have no meaning here
and should not be ported:

`SESSION`, session verbs (Focus / Save / Snapshot / Relaunch / Kill), `PROJECT`,
`NEW`, `TEMPLATE`, `WINDOW` rows, Ctrl+Enter for TouchPlayer, the
fullscreen-app suppression rule, and the "summoned-over session" ranking bonus.

That removes the whole session drill-in, which is one of the overlay's two
drill-in mechanisms. Ours has one drill-in: **parameters**.

## What transfers cleanly

- One input, one list, one footer hint. Esc or blur dismisses.
- Prefixes as query scoping — though ours needs far fewer (see decisions).
- Fuzzy score with **small** nudges: enough to win a tie, never enough to bury a
  better match. Title first; help/tool at a discount.
- Keys: `↑`/`↓`, `Enter`, `→`/`←` for drill-in **only at caret start/end so
  they still edit text**, `Esc` to back out then dismiss, `Alt`+`↑`/`↓` for
  query history, `Ctrl+D` favourite.
- Inline args mapping onto declared `params` in order, with prompted fallback.
- Presets as user-authored aliases resolving against the **unfiltered** command
  set (authoring the preset is the opt-in).
- Destructive commands **arm** — second Enter to confirm, and anything that
  changes what Enter would hit disarms. We have no Kill, but we do have
  destructive tool commands.
- Selection-specific footer stating what Enter will do to *this* row.
- The user's hide/show choice beats the tool's declared `hidden` in both
  directions.

## THE TD-SPECIFIC CONSTRAINT: capture context before the window opens

The overlay captures the foreground TD pid *before* it steals focus, because
after that the answer is wrong. We have the exact same problem one level down,
and it is the single most load-bearing thing in this document.

25 commands declare a `context` — `network`, `selected`, `current`,
`rollover-par` — and a consumer is expected to resolve that subject before
invoking, and to grey the command out when it is absent. Every one of those
resolves against **what the user is looking at**:

- `network` → `ui.panes.current.owner`
- `current` / `selected` → that pane's `currentChild` / selection
- `rollover-par` → `ui.rolloverPar` / `ui.rolloverParGroup`

Opening a Window COMP moves focus and the mouse leaves the network editor, so
**every one of these reads differently once the palette is up** — `rollover-par`
becomes `None` immediately. Therefore:

> The palette must snapshot its context at **summon time**, before the window
> opens, and every command it runs must resolve against that snapshot — not
> against live `ui` state at Enter.

This also decides greying: a row's availability is computed from the snapshot,
so it is stable for the life of the palette instead of flickering as the mouse
moves. `get_focus` (Envoy) already models exactly this snapshot shape and is
worth mirroring.

## Existing pieces to build on (not from scratch)

- **`/sys/TDTox/popDialog`** — cloned in **6** places already
  (`QuickCollapse`, `VSCodeTools/ScriptSyncFile`, `CustomParTools` ×3,
  `QuickExt`). It is a borderless, always-on-top Window COMP (`winopen=False`
  until summoned) with `replicator1` + callbacks driving dynamic rows,
  `keyboardin1` + callbacks, `entry1`/`entry2` text entry, `header`, `buttons`,
  and `PopDialogExt`. That is the palette's shape already: **evaluate reusing or
  forking it before authoring a new window**.
- **`FNS_Hub/window`** — the precedent for a tool that owns a window.
- **`FNS_HotkeyManager`** — the summon hotkey belongs here, not in a private
  keyboardin. Load `/fns-hotkey-conformance` before binding.
- **`FNS_ConfigRegistry`** — favourites, hidden, presets and query history all
  persist. Load `/fns-config-scope` before choosing where they live; project vs
  roaming scope is a real decision, not a default.
- **Lister** (`FNS_Hub/*Configurator/lister`) — the toolkit's existing list UI.
  Likely *wrong* here (table-shaped, heavier than a palette row), but it is the
  incumbent and should be rejected deliberately rather than ignored.

## Decided (owner, 2026-09-01)

- **v1 = registry commands + TouchDesigner's own Palette components.** No
  discovery layer: TD already maintains the list (see below).
- **Bespoke UI**, not a `popDialog` fork. It keeps the palette free of a
  dialog shape and of a clone-master relationship, at the cost of re-solving
  window and keyboard plumbing.

## The palette data source — TD already keeps it

`/ui/dialogs/palette/palette/data` is the Palette Browser's own model, so it
covers user palette folders as well as Derivative's, and needs no scanning.

Measured 2026-09-01: **1592 rows — 1377 `tox` + 214 `Folder`, 0 deleted.**
Columns: `id, name, path, type, version, folderid, locked, deleted`.

`id` is a dotted hierarchy key and `folderid` names the parent, so a component's
category is a walk up the chain — `checker` → `1.1` *Generators* → `1`
*Derivative*. That category is what fuzzy matching should score at a discount,
exactly as the launcher scores category and tags at 0.85.

**Placement is `loadTox`**, verified live rather than assumed:

```
loadTox(filepath, unwired=False, pattern=None, password=None) -> OP
```

It loads the tox **as a child of the COMP it is called on** and returns the new
OP — `scratch.loadTox('.../checker.tox')` produced `/zz_pal_probe/checker`. So
placing means `targetNetwork.loadTox(path)` and then positioning the result;
the network-layout rules apply, and a component dropped at (0, 0) is the
failure mode they exist to prevent.

The target network comes from the **summon snapshot**, not from live `ui` state,
for the reason given above.

## Built (2026-09-01)

Inside `/FNSTools/FNS_CommandPalette`, all native TD UI, no replicator:

- `window` (borderless, always on top, centred by `justifyh/v`, `closeescape`
  off so Esc goes through `OnKey` and state resets) shows `panel`.
- `panel` is a `verttb` stack: `input` (Text COMP, `editmode =
  editablecontinuous`, placeholder, its callbacks DAT forwards
  `onValueChange` to `OnQuery`), `rows` (twelve fixed Text COMPs repainted in
  place -- `display` off past the last result, `bgalpha` 1 marks the
  selection, a `{#color}` code dims the category), `footer` (the
  selection-specific hint).
- `keyboardin` is active only while the palette is open and routes
  up / down / enter / esc to `OnKey`. `keyboardin_summon` follows the tool's
  `Hotkey` par (`ctrl.shift.p`) by expression and calls `Summon`, per
  `/fns-hotkey-conformance`: one row in the manager, a real default.
- `results` mirrors the rows on screen as a table; `opviewer_panel` renders
  the panel into a TOP so it can be captured and judged without a screenshot.

**Twelve fixed rows, no replicator, on purpose.** Rebuilding operators on
every keystroke is the one cost a palette must never pay; twelve Text COMPs
repainted in place cost nothing.

Verified live: `Summon` snapshots context first, then paints; context-gated
commands render dimmed; the keyboardin received real key events while open;
writing the input's `text` par fired the Text COMP callback into `OnQuery`
and re-ranked (`che` -> `checker` and `Check for updates` at the top, mixed component and
command rows; with the relevance tiers a general command now edges a
component on a near-tie, which is the intended order);
two captures pass the visual rubric with the selected row as the single
focal point; 0 errors, 0 warnings.

Paid-for gotchas:

- **TD auto-creates `<name>_callbacks` when a Keyboard In DAT or a Text COMP is
  created.** A hand-made DAT of that name collides and is renamed `..1`,
  leaving the `callbacks` par pointing at TD's empty template. Write into the
  auto-created one instead; delete the ones you do not need (rows, footer).
- A TDAnnotate widget can carry a stale warning naming its template path
  (`.../annotate/annotation`) even though its `Component` pars evaluate
  correctly; force-cooking the widget's `back` container flushes it.
- **`save_project` does not re-export a PI suspect's tox.** With
  `enableexternaltox` on, TD reloads the COMP from that tox at project open,
  so a stale tox silently discards everything built since PI last saved it.
  After building inside a suspect, run `PrivateInvestigator.Save(comp)` (per
  operator) and commit the tox; this one went 41,566 -> 62,494 bytes.
- **An Op Viewer TOP of a panel can serve a stale frame.** After a repaint
  that flips rows from hidden to shown, a capture showed rows 5-11 stacked
  at the bottom while the panel's own geometry was correct; the viewer had
  rendered mid-relayout and nothing demanded another cook. Force-cook the
  panel and the viewer before capturing. Irrelevant in use: an open window
  cooks its panel every frame.
- Envoy's enclosure listing reports PI's `vc_data` as outside the Extension
  annotation at two placements that are geometrically inside. Left as an
  observed discrepancy, not a layout fault.

**Prefixes, relevance and colour (later the same day).** A leading `>` (or
`?`) scopes the query to commands, `=` to components, `/` navigates the
network, `~` lists a COMP's promoted methods; with nothing typed the footer
shows that strip, as the launcher
overlay does. Ranking carries a relevance tier from the snapshot, in the
owner's order: a command whose `rollover-par` context is satisfied outranks
one on `current` / `selected`, which outranks `network`, then general
commands, then components; a declared context the snapshot cannot satisfy
sinks to the bottom. Untyped, the tier is the sort key; typed, it is a nudge
(24 / 18 / 12 / 6 / 3 / -20 against the match score) that wins ties and
near-ties but not a clearly better match. Since 2026-09-11 the match score
comes from the shared tiered matcher (`scripts/shared/FuzzyMatch.py`, bound
as the `FuzzyMatch` DAT; see `docs/CoreToolsBacklog.md` item 31): a token
hits at one of seven tiers, exact / prefix / word start / substring /
initials / bounded typo / subsequence, the tier owns the thousands of the
score and the within-tier quality the hundreds, so a word-start hit always
lists above a typo hit and the nudges keep the reach they always had inside
a tier. A title hit outranks the same hit in the category (a 0.4 tier
penalty); the path stays substring-only. Each row's kind badge is coloured:
amber COMMAND, teal TOX, lavender for network rows (which show the COMP type),
lifted toward white on the selected row, with a `par` / `op` / `net` tag on
context commands so the reason for a row's rank is visible.

`/` navigates the network by the usual path conventions: `/` is the root,
`.` or `./` is the network you came from, and each `..` goes up one level to
any depth (`../../FNSTo` finds `/FNSTools` from three levels down). Rows are
the child COMPs of the path typed so far, one level deep, annotations
excluded, with the base itself first as "this network"; a partial name after
the last slash filters them. Right drills into the selected row and Left
backs out to the parent listing, both in whichever convention you are typing
(`./panel` drills to `./panel/`, `/FNSTools/Qu` backs out to `/`, `./` backs
out to `../`). Enter points the pane you summoned from at the row; the pane
is part of the snapshot for exactly that reason. The first cut guessed
"relative first with an absolute fallback"; the owner's correction to plain
path conventions is what shipped. A hot-sync reinit while the palette is open now
closes it rather than leaving a window with no state behind it.

Verified live: tier ordering is monotone on a synthetic snapshot that
satisfies every context kind; `>` / `=` / `?` filter by kind; navigation rows
resolve relative and absolute paths, exclude annotations and never list the
whole tree; a navigation to the current network returns ok; the coloured
badges and tags render (captured). The owner typed into the field while it was
open, so the human keystroke path into the input is real.

**`~` runs a promoted extension method (later still).** The subject is a
selected COMP, else the current child if it is a COMP, else the network you
came from, preferring in that order one that actually carries extensions.
Rows are the public methods reachable ON the COMP (`comp.Method`, which is
what promotion means), shown as `Name(arg, opt=default)` with the docstring's
first line, filtered as you type. Enter calls the method through the COMP with
any inline arguments typed after the name (`~Rank che`), coerced to int /
float / bool / str. A method whose required arguments are missing is refused,
the footer saying how many it needs, instead of dismissing into a TypeError
nobody would see.

Verified live: the owner's promoted methods list with signatures (13, the
twelfth row being the cap until you type); `~Ran` filters; `~Rank che` carries
its argument and returns the ranked list; `IsOpen` runs through the COMP;
`~OnQuery` with no argument is refused with the footer message and the window
stays closed; selecting AltSelect swaps the subject to its own `OnSelectOP` /
`OnUpdate` / `ToggleActive`; captured.

Paid for: **`COMP.extensions` lists `None` for every empty slot**, so a COMP
with no extension at all is truthy on that test; `window` won the subject
choice over the owner and listed nothing until the `None`s were dropped. And
one 640px row at 15px holds about 70 characters, so the docstring is capped by
what the signature leaves (`max(20, 62 - len(title))`) or the badge clips.

**Favourites, history, `#`, and the parameter walk (later still).** Two
declared Str pars hold JSON, `Favouritekeys` and `Queryhistory`, created by
the parfield layer (`CustomParHelper.Init` is now in the palette's own
`__init__`) and persisted by an FNS_ConfigRegistry host stamped into the tool
through the master's `StampHost`, with `Hotkey` excluded because
FNS_HotkeyManager already persists that par and two rails writing one value
is the failure to avoid. So a starred command or a recalled query follows the
user between projects under global scope, and stays in the `.toe` under
project scope, per `/fns-config-scope`. `StampHost` left `Promotepars` off,
exactly as the registry notes warn; turned on afterwards and verified on the
tool, which now carries its `Cf*` pars.

- **Ctrl+D** stars the selected command or component; starred rows lead
  within their tier and carry a `*` marker.
- **Alt+Up / Alt+Down** cycle executed queries, shell style, newest last,
  capped at 50. The recall writes the input, whose callback is told apart
  from typing so the cursor survives it.
- **`#`** lists the tools, one row each with a command count, matched by name
  or by the `capability` their commands declare; a trailing space or the full
  name lists that tool's commands, filtered by what follows; Right drills in,
  Left backs out to the tool list.
- **The parameter walk.** Enter on a command that declares `params` walks
  them one at a time instead of running: a menu param becomes pick rows
  filtered as you type, the rest a text field whose placeholder names the
  param, its style and its default; Enter accepts (empty keeps the default),
  an int or float that will not parse is refused with the reason in the
  footer, Left steps back a param, Esc backs out to the list. Values go to
  the registry as `kwargs`, which coerces and validates them again and
  refuses a required one that is missing, so the walk is a courtesy on top of
  the contract, not the contract.

Verified live, the final command call stubbed so nothing fired: `#` in all
four forms; a star round-trips through the par and paints; history dedupes,
caps and recalls with the cursor kept; the walk on `splitpane` filters `ri`
to `right` and hands `{'dir': 'right'}` to the call, clears itself, restores
the placeholder and records the query; `gotomark` refuses `x` with "needs a
whole number" and Left at the first param cancels back to the previous
query.

**Mouse (later still).** A Panel Execute DAT (`panel/panelexec_rows`) watches
the twelve rows' `select` value and hands a click to `OnRowClick`, which
selects that row and then does exactly what Enter does, so clicks and keys can
never diverge: a command runs, a component places, a network row opens, a
tool row drills, a pick row is picked, an unavailable row just selects and
hints. If the palette stays open after a click the input takes keyboard focus
back a frame later, so typing keeps working. Verified from the callback
module with a stub panel value and directly.

**Persistence, checked rather than assumed.** Scope is global; the roaming
file (`<userPaletteFolder>/FNSTools/config/FNStools_config.json`) carries a
`tools/FNS_CommandPalette` section whose `pars` block holds `Favouritekeys`,
`Queryhistory` and `Visibilityoverrides` and not `Hotkey`, exactly as the host
was stamped. Under global scope the last save on the machine wins across
projects, per `/fns-config-scope`. The section also carries four pars the
owner promoted from the window to the tool's Palette page --
`Justifyoffsetto`, `Ignoretaskbar`, `Dpiscaling`, `Single` (the window's own
pars read them by expression, `Single = cursordisplay` opening the palette on
the display under the cursor). They are the owner's, they roam, and they
were nearly mistaken for stray junk: the rail's `_applyPars` never creates
pars and no code here names them, which is what made looking before deleting
the right call. Two query-history entries left by tests were removed.

Still open: presets; dismiss on blur; arrowing off the top
returning to nothing selected; and a human end-to-end Enter on each mode
(every mechanism is verified from code, the keystroke path only as far as
the input).

## Manager tab (built 2026-09-01)

A **Commands** tab in FNS_Hub, published the toolkit way: an FNS_HubRegistry
host stamped into FNS_CommandPalette through the master's `StampHost`, with
`Comp='manager'` (sibling-relative, as HotkeyManager's host names `HotkeyUI`),
canonical `CommandPalette`, label `Commands`, order 40. Nothing is discovered
by scanning; the host registered at its own init and the global's `Tabs()`
lists it between MainMenu and OpMenu. `StampHost` left `Promotepars` off
again; turned on afterwards.

The panel is a TD Lister loaded from the palette's `UI/lister.tox` with
`loadTox(..., pattern='lister listerConfig')`, which lands the list COMP and
its config directly in the container: no wrapper base (a base cannot be laid
out in a panel) and no copy (the Lister carries a cloned `docsHelper`, and
copying a COMP with an enabled clone inside is the documented crash). It
lists ALL registry commands, hidden ones included, from `table_commands`,
which `RefreshManager` rebuilds from the registry and the prefs: Tool |
Command | Context | Star | Hidden | Key. Clicking Star or Hidden toggles the
same pars the palette reads, so the tab and the palette cannot disagree; the
config host already stamped in persists them. Rows are identified in the
callbacks by `lister.Data[row]['Key']`, never by table index, so sorting or
filtering cannot mis-target a click. A filter field drives `Filterstring`;
Refresh, Open palette and Clear history are Text COMP buttons through one
Panel Execute DAT; a `Refresh` pulse par on the panel answers the hub each
time the tab is shown; `onInitRow` tints hidden rows dark and starred rows
amber through the overlay system on layer 40 (Advanced Callbacks on).

Hidden got its first real model: `Visibilityoverrides`, a declared JSON dict
of key -> bool. The effective state is the override when present, else the
tool's declared `hidden`, and an override equal to the tool default is
dropped so the dict only holds real choices.

Verified live: 103 rows built, 29 of them hidden; a tool-hidden command
toggled shown (catalogue 74 -> 75) and back with the override dropped; a
simulated Star click through the real callbacks starred and unstarred a row;
the tab opened in the hub and the panel captured with rows, striping,
context tags and the hidden tint. No errors, no warnings.

Paid for:

- **The palette Lister ships with `display` OFF.** Rows, columns and data all
  looked right while the panel showed only the toolbar; the list COMP's own
  display flag was the whole story.
- **OP-reference pars on a COMP resolve sibling-relative.** `Inputtabledat =
  'table_commands'` from the lister meant a sibling INSIDE the panel; the
  table had been created one level up and came back None until it was moved
  beside the lister.
- The first capture of the panel was a stale pre-layout viewer frame, as
  before: text-bearing widgets blank. Force-cook, then capture.

Still to come here: presets once they exist, and the hotkey read-only with a
pointer to the HotkeyManager tab.

## Packaged (2026-09-01)

Catalogued as `Core` (installed as a unit, free tier) with `Pkgversion` `0.1.0` as a bare
About-page par, and documented in `packaging/docs/FNS_CommandPalette.md`. The site build's
prose-key checker flagged the in-window keys (Ctrl+D) as unbound hotkeys; the doc now
declares them under `local_keys:` and the checker exempts declared panel-local keys, which
is the same category its Shortcuts hint-line already excludes. The page's Shortcuts block
lists Ctrl+Shift+P once `build_manifest` regenerates the manifest from FNS_HotkeyManager.

## Built-in commands (2026-09-02)

The registry now serves TouchDesigner's own commands flagged `builtin` (see
`docs/CommandRegistration.md`). The palette applies the wire contract's consumer rules:
a `TD` badge in its own hue (`COL_BUILTIN`), a tier below general tool commands
(`TIER_BUILTIN`) so they list after them in `>` and the untyped list, and `?` now means
tool commands only. The Commands tab marks them `built-in` in the Context column.

## Follow-ups built (2026-09-02)

- **Presets** (`Presets` par, JSON list of `{id, label, key, args}`, roams with the
  other prefs). Alt+S authors one: mid-walk it bakes the values entered so far, the
  current field included when it parses, plus defaults; on a plain command row it
  is an alias. The name prompt reuses the walk (`_pending['naming']`, a synthetic
  param list). Rows resolve against the UNFILTERED command set, rank at
  `TYPE_WEIGHT` 11 just above their command, carry its context for relevance,
  show a `PRESET` badge in their own hue, and are included by `>` and `?`.
  A preset whose command is gone stays listed as unavailable; Ctrl+H deletes it.
  Trap paid for: a method named `Presets()` shadowed the `Presets` parfield in
  the class body, so Init never created the par -- the accessor is `ListPresets()`.
- **Ctrl+H** hides the selected command (`ToggleHidden`, the same override the
  Commands tab edits) or deletes a preset.
- **Curation identity is `tool#id`** (later on 2026-09-02, after the launcher's
  agent pointed out the latent bug): favourites, hidden overrides and presets
  were keyed by the wire key `path#id`, which encodes the owner's location, so
  moving a tool would have silently detached all three. They now key by
  `tool#id`, derived from the wire's `tool` + `id` exactly as the launcher's
  `command_identity` does (agrees 141/141); rows carry `ident` beside the wire
  `key` that `Run()` still takes, and entries stored before the switch migrate
  on first read. The Commands tab's Key column is the identity. A shared
  no-owner curation file (per-entry merge, tombstones, mtime reload, schema
  version) is the proposed next step, pending the owner.
- **Shared curation file** (2026-09-02, owner-directed, after the identity
  switch): favourites, hidden/shown overrides and presets moved off the pars
  into `<user palette>/FNSTools/config/command-curation.json`, shared
  with the launcher and merged per entry with tombstones -- the contract is
  `docs/CommandCuration.md`. The `CommandCuration` module DAT holds the file
  protocol; the three pars stay declared only to be adopted once and emptied,
  and are excluded from the config host. Query history still roams by par.
- **Dismiss on blur.** `panel/input_callbacks.onFocusEnd` -> `OnInputBlur()` ->
  a check three frames later: still open, input has no keyboard focus, and the
  mouse is not inside the palette panel -> `Dismiss()`. The delay is what keeps a
  click on our own rows (which blurs the input before it refocuses) from closing
  the palette.

## Rank by usage (2026-09-23)

Commands the user runs often rank higher, on by default (`Rankbyusage` on the
Palette page, roaming with the config host). A second machine-wide file shared
with the launcher, `command-usage.json`, holds per-consumer decayed scores; the
bonus is 0..8, below `FAVOURITE_BONUS`, so it sorts after favourites untyped
and only breaks ties typed. Contract, math and test vectors:
[CommandUsage.md](CommandUsage.md).

## Decisions (all closed by 2026-09-02)

1. **Prefixes.** Built: `>` commands (presets included), `?` tool commands
   only, `=` components, `/` `./` `../` navigate, `~` promoted methods, `#`
   by tool. Nothing collapsed; each earns its keystroke.
2. **Surface token.** Serve every command; no `palette` token was introduced.
3. **Where it lives.** `/FNSTools/FNS_CommandPalette`, parent shortcut
   `Palette`, catalogued Core (installed as a unit, free tier), `Pkgversion`
   0.1.0.
4. **Hotkey.** `ctrl.shift.p` on the tool's `Hotkey` par, rebindable through
   FNS_HotkeyManager. Behaviour in Perform Mode is untested.
5. **Enter with nothing typed** runs the top-ranked row, which with an empty
   query is the most context-relevant command.

## Explicitly out of scope for v1

Anything requiring a second TD session, OS window enumeration, launching
processes, or the freemium Pro-gating split. Also **no component discovery** —
if it is not in TD's palette table, the palette does not know about it.
