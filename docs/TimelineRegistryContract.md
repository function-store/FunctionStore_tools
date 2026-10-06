---
status: in-force
summary: FNS_TimelineRegistry -- the tenth registry. Publishes tool-owned panels into TD's timeline dialog, in two zones, without disturbing the native transport controls.
since: 2026-08-24 (branch cook-diet)
skill: fns-registry
---

# Contract: FNS_TimelineRegistry

The tenth registry (`/fns-registry` lists the other nine). Reached as
`op.FNS_TIMELINEREGISTRY`; master at `FNSTools/FNS_TimelineRegistry`, global
promoted to `/sys/FNS_Registries/FNS_TimelineRegistry` like every other.

## The surface, and why it is shaped this way

TD's timeline is `/ui/dialogs/timeline` -- **a singleton**, 2752x70. That is the
whole design decision: entries are **mirrors** (a `selectCOMP` pointing at the
tool's own widget), the way the toolbar does it, not per-instance **copies** the
way the navbar must (a breadcrumb has to show *its* pane's path, so every pane
bar needs its own).

TD does also keep per-pane timelines at `/ui/panes/pane_timeline/<pane>`, and
they were checked: 20px frame strips with **no transport row**. There is nothing
to contribute to, so they are deliberately not a target. If that changes, the
navbar's copy model — not this one — is the template.

### The Zone menu is DERIVED, never written down

A host's `Zone` menu was authored by hand on the host COMP, so adding a zone in
code left it unselectable: `graphheading` existed, worked when registered from
Python, and simply was not in the dropdown. A hand-kept list of something the code
already enumerates drifts on every addition.

`_syncZoneMenu` rebuilds `menuNames` from `ZONES` on every host registration pass.
Setting `menuNames` RESETS the parameter's value, so the current selection is read
first and restored -- otherwise syncing the menu would silently re-zone every
contributor.

**A new zone is therefore one entry in `ZONES` and nothing else.**

### Three zones

| Zone | Container | Layout | Mirror geometry |
|---|---|---|---|
| `transport` (default) | `/ui/dialogs/timeline/transport` | `horizlr`, 44px tall | height pinned to 39 (native control size), width follows the source, **right-aligned** |
| `background` | the dialog itself | absolutely placed | full content width, 14px, at the frame-ruler band |
| `graphheading` | `/ui/dialogs/keyframer/graphheading/textbg` | `align = none`, 18px tall | height pinned to 18, width follows the source, **right-aligned** |

### There is no zone for the properties block

The timeline's left-hand block cannot host a contribution, and the reason is
worth recording so it is not attempted again. The dialog stacks **three**
279x130 panels at (0, 0) -- `timeproperties`, `timeattributes` and
`emptypanel1` -- and only `timeattributes` draws: tinting each in turn and
counting pixels in a capture of the dialog gives **0 / 34344 / 0**. A
contribution sent to either of the other two is laid out correctly and then
covered, which is indistinguishable from never having registered.

`timeattributes` is no better a host. Its own children consume its `horizlr`
flow, so an appended section is laid out at x=276 inside a 279-wide block --
measured, 2 columns of a 120-wide contribution survived the clip. A section
placed over the block from the dialog, and one placed inside the block's empty
`emptypanel`, both measured **0 visible pixels**: TD's blocks draw over them.

A zone that cannot be seen is worse than no zone -- it reports success and
shows nothing -- so `properties` was removed rather than shipped broken.

### Sections span the host; TD justifies the contents

A section is **not** sized to its contents. It claims the host's full width --
`hmode = fill` inside an aligned parent, `w = parent().width` inside an
`align = none` one -- and `justifyh` packs the contributions against an edge.

This is why there is no spacer. An earlier design gave each contribution a
zero-opacity slack container to shove it rightwards; each sized its own slack
from `parent().width - <its mirror> - pad`, so the first consumed the row and
the second computed **zero** and was laid out past the right edge. Sizing the
section to its contents has the same flaw for a different reason: a container
exactly as wide as its children has no slack to justify *into*, so a second
contribution lands at a negative x and is clipped away.

### A mirror is a window, not a scaler

A Select mirror draws its source **at the source's size**. Setting only the
mirror crops: a 300x300 button registered at 200x18 rendered a 200x18 *corner*
of itself -- 306 lit pixels out of the 3400 the slot holds, which reads on
screen as "it did not show up" and as "it is always a limited height".

So registration sizes the SOURCE panel to `Barwidth` / `Barheight`. Only
declared axes are touched, and the original is recorded (`path|w|h`) so
unregistering hands the tool its panel back -- registering must not be a way to
silently resize somebody's widget on an axis they said nothing about.

### The background zone is not appended -- it is placed

TD's timeline has no free band, so a background is not flowed in after
something: it is *placed* in the frame-ruler band and drawn underneath it.
Three things make that work, and each was expensive to find:

- **`framebarslider` is transparent** (`bgalpha = 0`) and sits at alignorder
  2.0, so a strip just below that order shows through it. Panel `y` is measured
  from the BOTTOM of the dialog, so `y=56` on a 70-tall bar is the ruler band,
  not the floor.
- **The base IS the slot.** A placed zone must not add its sequence index to the
  base the way a flowed zone does -- a background at menu order 1 landed on 2.9
  and drew OVER the ruler it was meant to sit under. Placed strips stack in
  hundredths (`_mirrorOrder`).
- **A strip must be anchored to `transportpanel`.** Every one of TD's own
  full-width strips (`newhashrow`, `rangebar`, `framebarslider`) feeds its COMP
  input from `transportpanel`, and that connection is what puts it in the bar's
  content area. Unwired, a strip renders, reports the right size and the right
  alignorder, and still draws as a ~100px sliver in the corner. Its width should
  follow the anchor too (2473), not the dialog (2752) -- the difference is the
  properties block.

- **A `grow` zone gets its own row rather than stealing one.** Anchoring puts a
  strip in the layout flow, so without this it takes its height out of the
  transport row and clips the controls. The dialog height is recomputed as
  `BAR_BASE_HEIGHT + growth` on every sync, never incremented: `/sys` is rebuilt
  each project open but the DIALOG height is saved in the `.toe`, so an
  increment-and-restore scheme would creep taller every session. Because the
  added band is at the TOP (panel `y` counts from the bottom), a grow zone's
  strip pins its `y` to `parent().height - h` instead of a fixed number.
- **Growing the dialog is only half the job.** `timeproperties` and
  `transportpanel` already say `par("../panelh")` and follow along, but the
  left-hand blocks (`emptypanel1`, `timeattributes`) are fixed constants -- they
  keep their old height and leave a ragged edge down the left of a taller bar. A
  grow zone lists them in `follow_height` and points them at the same TD idiom.
  Their originals are remembered so a teardown restores them; losing that memory
  is survivable by design, because the expression evaluates correctly at *any*
  bar height, so a forgotten restore leaves a panel that tracks the bar rather
  than one that is broken.

## A host callback that silently did nothing

`Autoregister` is a Toggle, so CustomParHelper dispatches it through
`OnValueChange` with `(_par, _val, _prev)`. A one-argument `onParAutoregister`
is simply never called -- so switching Autoregister off left the entry, the
mirror and a stale "Registered" status, while `Register` (a Pulse, one argument)
worked fine and made it look like callbacks were wired.

The toolbar's host carries the same one-argument signature and gets away with it
because its Registration pars are BOUND to the tool's Registry page and fire from
there. These hosts are CONSTANT, so they need the real signature. **If you add a
Toggle to a Registration page, give its handler `(self, _par, _val=None,
_prev=None)`.**

A zone change **relocates** the mirror: TD cannot reparent, so the old one is
destroyed and remade in the new container (`_relocateMirror` +
`_findMirrorAnywhere`). Every prune and lookup walks *all* zones, or a mirror
orphaned by a zone change would be invisible to cleanup.

`Zone` is a menu par on the host's Registration page, mirrored onto the tool's
`Registry` page with the `Tl` prefix.

## Not fighting the native controls

TD's own transport occupies **alignorder 0..12**. `MIRROR_ORDER_BASE = 100`, so
a contribution is `100 + sequence index` and can never collide with a native
control or reorder one by accident.

`AdoptTimelineWidget` is the deliberate exception: it takes a control that is
*already* in the timeline (TD's own play/stop/step buttons) under management so
it can be reordered, grouped or hidden. Two things differ from the toolbar's
adopt, both on purpose:

- it writes the panel's **native** alignorder, not `MIRROR_ORDER_BASE + n` -- an
  adopted native control belongs among its native siblings;
- unregistering an adopted entry **restores `display = 1`**. A registry that
  hid a native control and then went away must not leave the user with a
  permanently missing Play button.

No mirror is ever made for an adopted entry -- that would draw the control twice.

## Managed sections: the registry puts down the container

Some surfaces have nowhere to put a contribution. The keyframer's `graphheading`
is `verttb` and 18 tall with its label already filling it, so a sibling gets
pushed out of the strip; the label (`textbg`) is `align = none`, so a child there
keeps its `x` -- but then every contributor has to work out its own placement.

`EnsureSection(host, name, height, x_expr, width)` puts down **one** container per
section and contributions live inside it. The container owns the awkward geometry
once; what goes in is a panel in a normal `horizlr` flow -- no per-contribution
spacer, no per-contribution `x` expression.

### A section grows to hold what is in it

`section_w` is the size for ONE contribution -- the starting size, not the rule.
`_sizeSections` sums the widths of a section's visible children after every
inject, so a second registration is not laid out inside a container still sized
for the first (and therefore never seen). Verified: 324 -> 384 on a second
contribution, back to 324 when it unregisters.

Summed at sync time rather than by expression: an expression cannot easily total a
variable set of children, and membership only changes on register/unregister,
which is when this runs. Hidden contributions are excluded, the same rule as an
empty section claiming no surface.

### A grow zone stacks, it does not share one band

The bar grows by the **SUM** of its grow-zone strips, not the tallest. Taking the
max gave two strips one band to share, so the second drew on top of the first and
the bar was too short for both.

Each strip then sits below the ones ordered before it -- `_bandAbove` totals their
heights and the y expression becomes `parent().height - me.par.h - <above>`.
Verified with two strips: 130 -> 160 tall, bands 70-130 and 130-160, no overlap;
removing one returns the bar to 130 and drops the offset.

Rank by the entry's OWN menu order with the canonical as a tiebreak, **not** by
`_mirrorOrder`: that needs a sequence index, and feeding it `0` for every entry
ranks them all equal -- so nothing is ever "above" anything and both strips land
on the same band anyway.

### The right edge is the GRAPH region, not the strip

For the graph heading the placement is

```
max(0, parent(3).width - parent(3).op('channels').width - me.par.w)
```

evaluated by the CONTAINER, so `parent(3)` is the keyframer dialog. The heading
strip runs **wider than the dialog** -- measured 680 against a 598 dialog -- so
right-aligning to the strip puts the block off-screen. The real right edge is the
dialog minus the channels column: 598 - 276 = 322, and a 134-wide block lands at
188.

### `opacity` on a container hides its CHILDREN

The timeline's right-align spacer uses `opacity = 0`, which is right for pure
slack with nothing inside it. A SECTION has children, and zero opacity hides the
lot -- the block was correctly sized and positioned and drew nothing. Sections use
`opacity = 1` with `bgalpha = 0`, which is a container's default anyway: the
section is a frame, and only what is in it draws.

## Right-aligning in a left-to-right row

The `transport` zone carries `'right_align': True`. Without it a contribution
lands immediately after TD's own controls and crowds them -- and the bar is
~2470 wide while TD uses barely a third of it, so there is a whole empty half
to move into.

**Setting `x` does not work.** An aligned container positions every child by the
flow and overrides the parameter, `align = none` on the child included. Measured
on the live panel: `par.x` read 2275 while the panel actually sat at 772. This is
not a quirk of one container -- it is what `horizlr`/`verttb` *mean*, and the same
wall is hit again in `TimelineToolsExt.AnimationUI`.

So `_applyRightAlign` takes up the slack with a **spacer**: a zero-opacity
`containerCOMP` named `tlspacer_<canonical>`, ordered just before the mirror, and
sized

```
max(0, parent().width - <mirror width> - 8 - me.x)
```

`me.x` is where the flow has reached by the time the spacer is laid out, and a
spacer's own `x` depends only on the siblings *before* it -- so this is not
circular. The bar can be resized and TD can gain or lose controls; the mirror
still lands on the right edge.

**The spacer's `alignorder` cannot be set in the geometry pass, and cannot be an
expression either.**

Geometry runs before the mirror's order is assigned, so there is nothing correct
to copy yet -- a copied value reads `0`, puts the spacer *first*, and shoves TD's
entire transport row off the end of the bar.

An expression tracking the mirror does not work either: **a panel's `alignorder`
expression is not re-evaluated when its target changes.** Measured, it sat frozen
at `119.999` from an earlier order while the mirror had moved to `101` -- so the
spacer sorted AFTER the mirror and filled the space beyond it instead of pushing
it there, leaving the controls mid-row with 1552px of empty bar to their right.

`_placeSpacer` sets it as a CONSTANT, from `_injectWidget`, immediately after the
mirror's real order is assigned -- and re-sizes the slack to the mirror's current
width at the same time, rather than the width it happened to have when the spacer
was created.

Verify this one in PIXELS, not parameters: `par.x` is meaningless in an aligned
container. The fix moved the blue toggles from x 921 to x 2426 in a 2473-wide row.

The spacer carries `MIRROR_TAG`, so the normal mirror sweep cleans it up with the
mirror it serves.

## Empty means invisible

Per the registry-home rules, an empty registry claims no surface: `_syncSurface`
prunes and returns before touching group markers when there are no entries.
Nothing is injected into TD's timeline until a tool registers, and the last
unregistration takes the last mirror with it. Verified: registering and then
destroying the publishing tool leaves the transport row byte-identical (22 panel
children, unchanged).

## API

`RegisterWidget(widget, canonical, order=, display=, callback=, source_registry=,
width=, help_url=, zone=)` / `UnregisterWidget` / `UnregisterPanel` (alias) /
`AdoptTimelineWidget` / `RegisterDivider` / `RemoveDivider` /
`SetWidgetZone` / `SetWidgetOrder` / `SetWidgetDisplay` / `SetWidgetWidth` /
`SetWidgetSequence` / `WidgetTarget` / `Widgets` / `WidgetSequence`.

Groups, dividers, drop-to-register and `StampHost` come from `RegistryBase`
unchanged. `OpenConfigurator` is a documented stub: there is no Timeline tab in
FNS_Hub yet.

Consume it guarded, by shortcut, never by path:

```python
reg = getattr(op, 'FNS_TIMELINEREGISTRY', None)
if reg is not None and hasattr(reg, 'RegisterWidget'):
    reg.RegisterWidget(op('mywidget'), 'MyTool', zone='transport', order=5)
```

## Verified live

Register -> mirror injected at alignorder 101 with a self-healing `selectpanel`
expression; zone move -> mirror relocated with the new zone's geometry; display
toggle; adopt a native `stepf` -> managed in place, no mirror, restored on
unregister; `StampHost` into a scratch tool -> registered with `externaltox`
severed and `pi_suspect` stripped; tool destroyed -> mirror pruned and the
zombie entry cleared by the heal tick. Portable tox exported and load-tested:
inert (Autoregister off, no shortcut, no clone, no tox binding, no tracker tag).

## Two hazards this build paid for

- **A copied registry master inherits its DATs' `file` bindings, not just
  `externaltox`.** `/fns-registry` warns about the tox binding; the DAT bindings
  bite the same way and harder. Writing the new extension into the copy wrote
  **through to `FNSTools/FNS_ToolbarRegistry/ToolbarRegistryExt.py`**, and the
  live ToolbarRegistry -- `syncfile=True` -- reloaded it and became a
  `TimelineRegistryExt`. Sever `file`/`syncfile` on every copied DAT *before*
  writing anything into it. `RegistryBase` is the exception: it is genuinely
  shared, stays bound, and must simply never be written to.
- **`Pkgversion` binds to `me.par.Version`** and raises a transient cook
  dependency loop warning during extension init. It clears on the next cook and
  the sibling registries carry the identical bind; do not "fix" it.

## A contributor can ask for its own height

`background` is a grow zone, and the height it grows BY was a constant on the
zone -- so every contributor was stuck with whatever the zone happened to be
written with (14 px). `RegisterWidget` now takes a `height`, stored on the entry
alongside `width`, and both the growth calculation and the mirror geometry read
the entry's height in preference to the zone's default. Hosts expose it as
`Barheight`, symmetric with the existing `Barwidth`.

Growth takes the **maximum** requested height across a zone's entries, not the
sum: a zone is one band that several contributors can share, so it has to be tall
enough for the tallest, not the total.

Changing the height has to **re-register**. The value rides in the stored entry,
so writing the host parameter alone leaves the bar at whatever the last
registration asked for -- which reads exactly like the parameter being ignored.
Verified across 24 -> 60 -> 14: the bar tracks to 70 + height each time and
returns to 84 with no creep.

## A grow zone's mirror must follow its OWN height

The mirror hugs the top of the bar, which panel-y-from-the-bottom makes
`parent().height - <its height>`. That height was written into the expression as
a LITERAL at inject time, so it was only ever right for the height in force when
the mirror was made: raising the strip to 120 left the band anchored to 60, with
its bottom in the right place and its top running off the end of the bar.

It reads `parent().height - me.par.h` now -- the mirror's own height, so any
height change is tracked with no re-inject. `h` is a constant here, so there is
no cycle. Verified flush to the bar top at 14, 60, 120 and 200.

Worth noting the comment directly above that line already warned against
"pinning a number that goes stale" -- and then pinned the height. A literal baked
from a live value is the same bug as a hardcoded constant; it just takes longer
to notice.

## The ruler needs a nudge, and it is empirical

`framebarslider` is positioned from the BOTTOM by a stock constant (`76-20`),
while `rangebar` anchors to the top (always `bar - 14`). Growing the bar pulls
them apart, and the ruler has to drop to stay readable against the added row.

`shift_y` on the zone spec applies `-12`, stored and restored like the height
followers, and guarded so repeated growth cannot stack it. The value is
**empirical** -- what looks right on screen, and equal to `rangebar`'s own height.
The geometry above explains why they separate; it does NOT derive the remedy, and
restoring the stock invariant (`slider_y == rangebar_top`) would move the ruler
the wrong way entirely.

## framebar is the PLAY MARKER, and it gets its own rule

`framebar` is **2 pixels wide**, its `x` tracks the playhead, and it is a fixed
**13** tall natively -- one ruler row. It was originally lumped into
`follow_height`, the mechanism for the bar's fixed-height **left-hand blocks**
(`emptypanel1`, `timeattributes`) that would otherwise leave a ragged edge when
the bar grows.

That was wrong, but so was simply removing it. Left at 13 on a grown bar the
marker becomes **a stub floating under the strip**, visually detached from the
ruler it marks -- which is what "the play marker has shrunk" was. Spanning the bar
is what a playhead drawn over a filmstrip should do.

So it is now `play_marker`, a separate zone key with its own store
(`play_marker_before`) and its own `_applyPlayMarker`. Same save/restore shape as
the height followers, deliberately NOT the same mechanism: that one is about a
ragged edge, this one is about the playhead staying legible, and conflating them
is exactly how the marker got reshaped by accident to begin with.

### The marker is clipped by its PARENT, so the parent is what must span

`framebar`'s panel parent is **`framebarslider`** (wired through its COMP input),
a 14px scrub bar. Its native `h` of 13 means "fill my parent" -- so setting the
marker to the bar height **does nothing on screen**. Measured the hard way: the
marker reported 130 tall while still drawing as a stub under the strip.

`_applyPlayMarker` therefore stretches `panelParent()` too, with
`par("../panelh") - par("y")` -- from the slider's own y to the top of the bar, so
it tracks the `shift_y` nudge instead of baking the offset in.

### These are TSCRIPT expressions

TD's stock timeline parameters evaluate as **tscript**, not Python -- which is why
`FOLLOW_HEIGHT_EXPR` is `par("../panelh")`. Writing Python fails at COOK time, not
at write time, so it looks like it worked: `me.par.y` gave *"Bad data type for
function or operation"* and evaluated the height to **0**, silently collapsing the
slider to nothing. `.eval()` gave *"Unknown function in expression"*. Anything
written into these parameters must be tscript.

**Removing a name from one of these lists does not fix a project that already ran
with it.** The live parameter stays on the expression and the saved original is
stranded in the store where nothing will ever restore it. A migration has to
repair both.

## framebar follows the bar too

`follow_height` now covers `framebar` alongside `emptypanel1` and
`timeattributes`. It is the playhead -- a 2px-wide column whose height is a stock
constant (95) rather than an expression, so on a grown bar it stopped partway up
and no longer spanned the row it points at.

It goes through the same store-and-restore as the other followers: the expression
`par("../panelh")` while a `grow` zone is registered, back to the stock 95 on
teardown. Verified across a full cycle -- 130 grown, 95 restored, 130 again.

`y` needs nothing: it is already 0, so a height that tracks the bar spans it from
the floor up, which is what the stock constant did at the stock height.

## Register and unregister must be symmetric

A `grow` zone gives its contributor a row of its own instead of stealing one from
the transport. `UnregisterWidget` always ended by recomputing that growth --
`RegisterWidget` did not, and the asymmetry was invisible for as long as nobody
re-registered.

`RegisterWidget` has a fast path: when the bar is already up it injects the mirror
directly and skips the sync pass that would have recomputed the height. So a
re-registered `background` contributor got its mirror **with no row to live in** --
the bar stayed at 70, the strip squeezed into the transport row, and nothing
re-ran the calculation. It looked like the mirror had failed; it had not.

Both fast-path inject sites now call `_applyGrowthSettled()`, which applies the
growth immediately *and* once more a frame later. The second pass matters because
registration lands in two steps: the entry is stored first, and its **zone**
arrives with the host's parameter a frame afterwards -- so growth computed in the
first step sees no `background` entry at all. Re-applying is free because the
computation is idempotent by construction (always `BAR_BASE_HEIGHT + growth`,
never incremented). Verified over three full register/unregister cycles:
84 -> 70 -> 84 with no creep, and the height followers tracking each time.

## Open

- No `FNS_Hub` tab, so ordering and visibility are API-only for now.
- Cold-boot bootstrap unverified: it needs a TD restart, which was not available
  (eleven live peer sessions). Everything else was verified in-session.
- The adjacent TODO items -- timeline background, and timelinetools (media load,
  sync timeline, drag-and-drop select, output) -- are the intended first real
  consumers.
