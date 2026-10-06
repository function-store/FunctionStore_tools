---
status: landed
summary: Generalising OpTemplates into an op-menu contribution -- any tool can declare itself an alternative for a stock operator type, and a tool that is only in the store can be offered and placed on demand.
since: 2026-09-10
---

# Op alternatives

Owner's idea, 2026-09-10: "each tool can define itself as an OpTemplate that
becomes an alternative for the specified optype, like OpTemplates already does.
Registry pattern. Tools in the CMS could define this too, so if available in
storage they show up as alternatives without being preloaded in the project."

This page pins what already exists, proposes the shape, and lists the three
decisions the owner has to make before it is built.

## What exists today, exactly

**OpTemplates owns the whole mechanism.** Four pieces, all inside one package:

1. **A library.** `OPTemplates1`, a base whose children are named after
   operator types (`lfoCHOP`, `moviefileoutTOP`, ...) and hold one or more
   template chains each. `Templates` derives `{optype: [ops]}` from that
   structure alone. Users keep their own libraries as `.tox` files under
   `Palette/FNSTools/OpTemplates/` (the `External` toggle).
2. **A watcher.** `kindergaertner_mymod` (a vendored olib component, target
   `/local`) fires `onCreate(new_ops)` for every operator created anywhere,
   and the callbacks DAT forwards each undocked one to `OnNewOp`.
3. **An engine.** `OnNewOp` is gated on the `Keys` hotkey (`alt ctrl`). One
   template: `placeOPchain` destroys the fresh op and copies the template in
   its place, restoring every input and output connection by connector index,
   carrying docked ops, and re-applying a family-convert parameter. Several
   templates: `popMenu` asks which, then places. A template may be a single
   op, a chain, or a `baseCOMP` whose `TEMPLATE_ROOT` / `TEMPLATE_IN` tagged
   children mark where the chain begins.
4. **A contribution.** `opmenu_callbacks`, published through the package's
   `FNS_OpMenuRegistry` host: `onDecorateLabel` appends `' >>>'` to types that
   have a template, `onMenuItems` adds `Edit Templates...`.

**OpMenuRegistry already merges per-optype contributions.** `SearchWords`
collects `onSearchWords() -> {optype: [words]}` from every contributor into
one dict, with per-contributor error isolation. That is the exact shape an
alternatives contribution needs, so the protocol extension is one more
callback, not a new registry.

**Two primitives for "not preloaded" already ship.**

- `placement: pane` (catalog, manifest, installer, updater, both pickers; see
  `tests/test_placement.py`): a package that spawns into the network the user
  is working in, whose presence is the install record and whose instances are
  frozen at their spawn version. No package declares it yet.
- `FNS_Updater.PlaceCommunityTool(name, target)`: download a tox, verify size
  and then hash, place it into a target COMP. Its docstring is explicit that
  this is a place, not an install. `StoreFolder()` is the machine-wide flat
  package store, `Palette/FNSTools/store`, which is the "storage" in the
  owner's phrasing.

**The manifest is derived live.** `surfaces`, `requires` and
`integrates_with` are read off the running project at build time. A new
per-package field can be derived the same way instead of curated.

## Proposed shape

### Layer 1: alternatives are an op-menu contribution

Add one callback to the OpMenuRegistry callbacks-DAT protocol:

```python
def onAlternatives():
	'''{optype: [alternative, ...]} this tool offers when that type is created.
	alternative = {'label': str, 'source': COMP | OP | callable, 'help': str}'''
	return {}
```

The registry merges it exactly as it merges `onSearchWords`. The label
decoration and the `Edit Templates...` item keep working unchanged.

- **OpTemplates becomes one contributor.** Its `onAlternatives` returns its
  `Templates` dict, label = template name, source = the template op. Its
  library, the external `.tox` files, and the editor stay where they are.
  Nothing a user has authored moves.
- **Any tool can contribute.** A tool that is a better answer to a stock type
  returns `{'moviefileinTOP': [{'label': 'MediaBrowser', 'source': self}]}`
  from its own callbacks DAT, next to its existing `FNS_OpMenuRegistry` host.
  The code stays in the tool, which is the registry scheme's rule.
- **Placing a tool** reuses the `baseCOMP` branch of `placeOPchain`: the tool
  is copied where the op was and wired through its `TEMPLATE_ROOT` /
  `TEMPLATE_IN` tagged children, or, with no tags, through `in1` / `out1` by
  name. A tool that wants to be an alternative adopts one of those two
  conventions and nothing else.

**Where the engine lives is the first decision.** Two options:

| | Engine in the registry | Engine stays in OpTemplates |
|---|---|---|
| Who must be installed for alternatives to work | the registries (core) | OpTemplates |
| Fits the scheme | yes: a surface's behaviour is the registry's | no: one tool would host every other tool's surface |
| Cost | move `OnNewOp`, `placeOPchain`, the picker popup and the watcher into `FNS_OpMenuRegistry` (about 400 lines plus a vendored component) | one aggregation call in `OnNewOp`, plus `requires: FNS_OpTemplates` on every contributor |
| Risk | the registry masters ship raw and cloneable, so growth has to stay lean; the watcher is third-party olib code and needs a licence check before it moves | a contributor that installs without OpTemplates silently offers nothing |

Recommendation: the registry. A surface that every tool can plug into is
what the registries are for, and the second option makes OpTemplates a
dependency of tools that have nothing to do with templates.

### Layer 2: alternatives that are only in the store

- **Manifest field, derived.** `build_manifest` calls each live package's
  `onAlternatives()` at build time and records the keys as
  `alternatives_for: [optype, ...]`, alongside `surfaces`. A foreign package
  may curate the list in `catalog.json`, since there is nothing to reflect.
- **Gate: only `placement: pane` packages.** A store-backed pick has to land
  in the working network as a frozen instance, which is precisely what the
  pane contract already promises. A package that installs into the toolkit
  container is not an operator and should not pretend to be one. This rule
  costs nothing and removes every "is this an install?" question.
- **Decoration.** The registry reads the cached manifest the updater already
  keeps in `StoreFolder()`, and marks types that have an uninstalled
  alternative with a second, distinct mark (say `' v'` beside the `' >>>'`).
  The picker lists those under their own heading, "from the store", with the
  package's `title` and one line of `description`.
- **Fetch, then place.** If `<StoreFolder>/<name>.tox` exists, place it. If
  not, fetch it the way `PlaceCommunityTool` does, size then hash against the
  manifest, then place. Gated (`access` tier) packages appear and refuse with
  the route, which is the picker's existing rule: visible and locked, never
  hidden.
- **Nothing installs itself.** Placing is a place. No `Installed` record, no
  update pass, no toolkit-container copy. If the owner wants a placed
  instance to become a tracked install later, that is a separate action in
  the hub, and a separate design.

## Decisions, taken 2026-09-10

1. **Engine home: the registry.** `OnNewOp`, `placeOPchain`, the picker popup
   and the op-create watcher move into `FNS_OpMenuRegistry`. OpTemplates keeps
   the library and the editor and contributes through `onAlternatives`.
2. **"Available" means on disk in the store.** The owner's rule: once a tool
   has been downloaded into `StoreFolder()`, it is offered and placed from
   disk through the same mechanism. So the registry offers the intersection
   of the cached manifest's `alternatives_for` and the `.tox` files actually
   present in the store folder, and placing loads the tox from disk. Nothing
   is fetched on demand in this version; a package that is in the manifest
   but not yet downloaded is simply not offered. Fetch-on-demand, if wanted,
   is a later step on top of this one and changes nothing below it.
   Places stay places: no `Installed` record, no update pass.
3. **The `alt ctrl` gate stays.** A popup on every operator would be
   intolerable, and the `' >>>'` mark is how people learn the modifier
   exists. The only change is that the mark and the popup now cover every
   contributor.

## First contributors, once built

Pane-placement is the gate, so the first step is declaring it on the tools
that genuinely are reusable components: the ones whose whole job is to stand
in for a stock operator with a better one. Naming them here before the owner
has looked would be guessing.

## Not in scope

The external template `.tox` format, the `Edit Templates...` editor, and any
form of automatic installation.

## What landed (2026-09-10)

Steps 1 to 6 of `briefs/2026-09-10-op-alternatives.md`, in four commits.

- **Protocol.** `onAlternatives()` is one more callback in the op-menu
  callbacks-DAT protocol; `Alternatives` merges every contributor with the
  same per-contributor isolation as `SearchWords`. Each alternative normalises
  to `{label, source, help, contributor, unpack}`. A bare op is a library entry
  and unpacks; a dict naming a tool is placed whole unless it says `unpack`.
- **Engine, in the registry.** One `watch_children` opexecuteDAT on
  `ui.panes.current.owner` plus the in-house snapshot logic (immediate
  children keyed by `OP.id`); only the `/sys` global's copy is active. The gate
  is the `Shortcutalternatives` par on the registry's `Alternatives` page,
  default `alt ctrl`. The picker is `op.TDResources.PopMenu`, live entries
  first, the store's below a divider. Placement is `placeOPchain` ported whole
  for library entries, a whole-COMP copy with the clone-host crash recipe for a
  tool offering itself, and `loadTox` for a store tox.
- **Store.** `alternatives_for` is derived per live package at manifest build
  by calling its `onAlternatives()`; a foreign entry may curate it, and so may
  a live package with no op-menu host (2026-09-10: the content CMS gained an
  "Alternative for" input; a curated list beside a host is a preflight
  problem, so a tool never says two different things). The
  registry offers the intersection of the cached manifest and the toxes on
  disk in `StoreFolder()`, skipping packages live in the project, and places
  from disk. Nothing is fetched, nothing is installed.
- **One marker.** `' >>>'` for a type with a live alternative, `' >>'` for one
  whose only alternatives are in the store. OpTemplates' own decorator retired.
- **Multi-type keys** (2026-09-10). A key in the returned dict may name
  several types separated by spaces, or be a list of names; the merge expands
  it so the registry is still keyed by one type. Before this a tuple key was
  stringified and offered for nothing, silently.

### Paid for on the way

- `placeOPchain` only cleaned `TEMPLATE_*` tags in the destination network;
  every COMP template placement left `TEMPLATE_ROOT/IN/OUT` on the library's
  own children, and a stale `TEMPLATE_OUT` is what the next placement wires
  the outputs to. Forty-six library operators carried them. The port cleans
  every operator it tagged; the library was stripped once.
- The `/sys` global is a promotion-time copy of the master, not a clone: a
  child added to the master reaches it only when the master's `Version`
  is newer at boot. Bumped to 1.1.0 for exactly that.
- Every tool's `FNS_OpMenuRegistry` host has cloning on with an empty clone
  path, so hosts receive the ext by file sync and never receive children.
  Right for a watcher and a hotkey chain; recorded, not changed.

### What an existing OpTemplates install sees

The question after the move was what an OpTemplates user loses. Nothing they
made, and the one setting that would have gone stale is carried for them.

**Untouched.** The library `OPTemplates1`, the external `.tox` libraries under
`Palette/FNSTools/OpTemplates/` with the `External` toggle and its
save/load/overwrite flow, dragging an operator onto the toolbar icon, `Edit
Templates...` in the operator list, and the four quick-launch commands (Open,
Add selection, Save, Refresh). OpTemplates derives `Templates` from the library
exactly as before and hands that dict to the registry through
`onAlternatives()`. The registry reads it on demand and caches it per frame, so
a library edit is offered on the next placement with nothing to pulse.

**Same from the user's seat.** Same `alt ctrl` / `cmd ctrl` default, same
in-place swap with inputs and outputs restored, same `' >>>'` in the operator
list. Two visible differences: the picker for several templates is TD's shared
`TDResources.PopMenu`, so it no longer takes the operator family's colour as
its title, and every entry reads `name  (OpTemplates)` because other
contributors share the list now.

**Two things changed underneath; both handled in `ccd63f19`.**

1. *`Keys` was dead.* The gate moved to the registry's `Shortcutalternatives`,
   but OpTemplates' `Keys` par stayed, and ConfigRegistry kept restoring it at
   boot. A user who had customised the shortcut would have had it restored
   into a parameter nothing read. `adoptShortcut()`, scheduled 90 frames after
   init, carries a CONSTANT `Keys` onto `Shortcutalternatives` once, and only
   while the registry is still at its default (a registry the user already set
   wins), then turns `Keys` into a read-only expression that mirrors the
   registry's par, with help text saying where to edit it. One setting, shown
   in both places, edited on the registry. Verified three ways: a default
   `Keys` stays default and mirrors; `shift ctrl` on `Keys` lands on the
   registry and in the live hotkey chain; a later change on the registry flows
   back into `Keys`.
2. *The old watcher still cooked.* `kindergaertner_mymod` observed the current
   pane's children on every change in order to call what is now a no-op. Its
   `opexec1` is inactive; the component stays (next paragraph).

**Still carried, on purpose.** OpTemplates ships its idle engine until the
owner confirms removal: the vendored `kindergaertner_mymod` watcher, `popMenu`
and `popMenuConfig`, `table_pop_templates`, the `hotkey` chain and `null_hk`
(about 145 operators, all inert), and the original `placeOPchain` body in
`OpTemplateExt` from the `BULKY GOODS` marker down, about 400 lines that
nothing calls now that `PlaceTemplate` delegates to `PlaceAlternative`.
`kindergaertner_mymod1`, which watches the library for `OnTemplatesUpdate`, is
live and stays either way. `OnNewOp` stays as a named no-op: forwarding it to
the registry would fire a second placement for the same keypress.

**Version pairing.** The engine is in the registry, so a working install needs
FNS_OpMenuRegistry 3.1.0 (core, always installed) and FNS_OpTemplates 3.1.0
together. An older registry under the new OpTemplates offers and places
nothing, because OpTemplates no longer holds a watcher. The new registry under
an older OpTemplates works, with the old decorator's second `' >>>'` ignored.

**A user's own library files carry the leaked tags.** `placeOPchain` left
`TEMPLATE_ROOT/IN/OUT` on library children for years, so every external `.tox`
a user saved carries them too. Harmless until a stale `TEMPLATE_OUT` sits on
the wrong operator; the ported engine strips every tag it touches on both
sides, so a library heals as it is used. A one-shot strip on library load would
close it entirely and is not built.

### Paid for after landing (2026-09-10)

- **The mark was never reaching the dialog.** `_markAlternatives` hung off
  `DecorateLabel`, but the dialog's chain stage (OpMenuMods'
  `script_inject_callbacks`) resolves `Decorators` once per cook and applies
  them itself; it never calls `DecorateLabel`. With OpTemplates' own decorator
  retired, nothing appended `' >>>'` for anyone, old templates included, while
  `DecorateLabel('noiseCHOP', 'Noise')` kept answering `'Noise >>>'` in tests.
  Verify the surface, not the method: the stage now calls the public
  `MarkAlternatives(optype, label)` per row.
- **A pane switch read as a hundred creations.** The watcher follows
  `ui.panes.current.owner`, and there is no tick on the switch itself, so its
  first tick after entering a network diffed against the previous network's
  snapshot and handed every child to the engine (measured: 100 from one
  navigation into `/`). Harmless with the modifier up, but the obvious fix,
  "a changed owner only re-baselines", swallows the very creation that
  caused that first tick (verified: the first op created after entering a
  network was never offered). The watcher now keeps a watermark, the highest
  OP id seen at its last tick; ids only grow within a session, so on a
  changed owner the candidates are the children above the watermark: the op
  just created, and nothing that already existed. Verified: enter a network
  holding two older ops, create one, exactly one offer.
- **A tool inside itself.** Testing `/randomCHOP1`'s alternative from inside
  `/randomCHOP1` asked the engine to copy the COMP into its own network.
  `PlaceAlternative` refuses when the fresh op sits inside the source.
- **A copied host is registered hidden.** A host copied out of another tool
  keeps that tool's Registration values (`Canonicalname`, `Displayed`, help
  URL). `Displayed` off drops the entry from `_activeNames()`, and with it
  every hook the tool defines, alternatives included. `StampHost` is the
  route; a copied host needs `Displayed` on and its own canonical name.

- **A placed copy published itself.** A tool offering itself is copied
  whole, hosts included, and the copy's hosts autoregistered on init: each
  placement added one more alternative for the type, and with a canonical
  name set, the copy took over the original's entry (three placements, the
  entry pointing at the last copy). A placed copy is an instance, not a
  tool: `_placeComp` now switches Autoregister off on every registry host
  inside the copy before its extensions init. The store path is unchanged,
  since a store alternative is only offered for a package that is not live
  in the project, so there is no original to displace.

- **A chain landed corner-first.** `ui.pasteOPs(parent, x, y)` anchors the
  pasted group's corner at the point, so the render template put its box SOP
  where the user had clicked and the Render TOP a thousand units to the
  right; it read as "a disconnected box". Inherited from OpTemplates, which
  pasted the same way. The real defect was the lost wire (next bullet);
  for the layout the owner chose the leftmost operator, the start of the
  chain, exactly under the cursor, which is what the paste roughly did and
  is now exact.

- **A wire vanished on a name collision.** Placing the render template at
  `/`, where a `box1` already exists, pasted the box as `box2` with its wire
  into `attribcreate1` gone; in an empty network the same placement was
  fully wired. A bare `ui.copyOPs`/`pasteOPs` with the same collision keeps
  the wire, cooking on or off, so the trigger inside the engine is not
  isolated. The engine now records the library's own wiring by index before
  the copy (a `TEMPLATE_IDX_n` tag per op, cleaned on both sides) and
  reconnects any input the paste left empty, so a rename can never cost a
  connection whatever the cause.

- **Hosts carried the Alternatives page.** Every stamped host is a copy of
  the master, so each carried its own `Shortcutalternatives`, read by
  nothing, and the hotkey manager listed five 'alt ctrl' rows for one
  setting. Hosts now shed the page at init alongside the engine ops.

### The list lives in a table (2026-09-25)

The eight tools that offer themselves (ChopBank, ChopProcess, ConstantCHOP,
ExpressionPOP, FeedbackDisplace, RandomCHOP, PrismTOP, ThresholdColor) keep
the operator types in an `alternatives` table beside their callbacks DAT:
`type | label | help`, one row per type. `onAlternatives()` is the same
reader in all eight. The content CMS's "Alternative for" field reads the
live list through FNS_CMS (`/api/altread`) and, where the table exists,
rewrites it and PI-saves the tool (`/api/altwrite`). Before this the field
was empty for every one of them, because the list was code and the field
only showed the catalog. OpTemplates computes its list from its library,
has no table, and shows read-only. A tool with no op-menu host keeps the
catalog value as before.

### Still open

- Which real tool becomes the first contributor after OpTemplates. Owner's call.
- Fetch-on-demand for a package in the manifest but not yet in the store.
- OpTemplates' idle engine, listed under "Still carried" above, stays until
  the owner confirms its removal.

