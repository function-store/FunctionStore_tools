---
package: FNS_OpSequencer
summary: 'Store any number of parameter states of one operator as presets in a table, then scrub, jump or morph between them with easing, or mix them by weight from a CHOP.'
features:
  - name: Quick start
    anchor: quick-start
  - name: PRESET BUTTONS  (Seq page and panel)
    anchor: preset-buttons-seq-page-and-panel
  - name: The list
    anchor: the-list
  - name: Playback
    anchor: playback
  - name: Per-parameter easing
    anchor: per-parameter-easing
  - name: Rotation
    anchor: rotation
  - name: MIX  (Mode = Mix, plus the Mix page)
    anchor: mix-mode-mix-plus-the-mix-page
  - name: THE MIX BLOCKS
    anchor: the-mix-blocks
  - name: PRESETS TABLE (repo)
    anchor: presets-table-repo
  - name: Restore
    anchor: restore
  - name: Non-numeric parameters
    anchor: non-numeric-parameters
  - name: What's new (2026-08)
    anchor: what-s-new-2026-08
---

Store any number of parameter states of ONE target operator as presets,
then scrub, jump or morph between them with easing. Presets live in a
table, so they are readable, editable and version-controllable.

## Quick start
1. Drop an operator onto the panel (or set the OP parameter).
   - Plain drop: keeps the preset columns if the new op has them.
   - ALT + drop: starts fresh and captures EVERY parameter of the op.
2. Drag parameters from the op's parameter dialog onto the panel to add
   them as preset columns. Pulse/Momentary/Sequence pars are skipped.
3. Set the op up how you like it and press APPEND. Repeat.
4. Scrub SELECT. Whole numbers recall a preset; in between blends toward
   the next one with the chosen easing.

## PRESET BUTTONS  (Seq page and panel)
Append   capture the op's current state as a new last preset
Replace  overwrite the selected preset with the current state
Insert   capture AFTER the selected preset and select the new one
Remove   delete the selected preset
Init     wipe all presets and capture one
Reset    wipe the table AND the columns (backed up: see RESTORE below)
Prune Stale Columns
         drop columns whose parameter no longer exists on the op
         (you will see a warning on the node when that happens)

## The list
#        0-based preset index  -  the same number SELECT uses
EASE     easing stored with the preset (used when Override is off)
click    recall that preset (sets SELECT)
drag     reorder presets; the index numbers follow the new order
middle-click a header   delete that parameter column (not # / EASE)
right-click a cell      easing menu. On EASE: the preset's base easing.
         On a parameter cell: that parameter's own easing for this
         preset (Inherit = follow the row). Overridden cells show in
         bold amber; hover them for the curve name.
Values are editable in place -- the EASE cell too, as text.

## Playback
Mode     how the presets are played back:
  Select (scrub)   the playhead. Whole numbers recall a preset, in
                   between blends toward the next one. Drive it from a
                   CHOP (LFO, Timer, Beat); it wraps around.
  A to B           morph between two arbitrary presets: Preset A ->
                   Preset B, driven by Selany (0..1).
  Spline           fit a periodic cubic spline through ALL presets
                   instead of easing pairwise. Smooth, loops, ignores
                   Easing.
  Mix (weights)    blend every preset at once, by weight. See MIX.
Easing   31 curves plus CustomEase. CustomEase reads the CHOP wired
         into the component's FIRST CHOP input (default: an S-curve).
Override on: the Easing menu applies to every transition.
         off: each preset's own EASE cell is used (the menu follows it).
Bind     off = sequencing stops writing to the op (values are kept).
Length   number of presets (read-only).
Parameters the current Mode does not use are greyed out.

## Per-parameter easing
A preset's EASE cell can re-ease single parameters on top of its base
curve: "InQuad | tx:OutBounce ry:InSine". The base eases every column;
each par:Easing token re-eases that ONE column for the morph INTO the
preset. Right-click cells to set them, or type the spec straight into
the EASE cell. Members of a rotation triple share the triple's BASE
name (r:OutQuad eases the whole arc -- set it from any of rx/ry/rz).
Unknown names fall back to the base at blend time, so a typo can never
break playback. Select and A to B only: Spline fits its own curve and
Mix is weight-driven, so neither reads easing at all. Override ON
flattens everything -- overrides included -- to the Easing menu.

The EASING STRIP (panel, below the buttons -- the EASE button hides
it) and the Easing parameter page are the same controls: they follow
the selected preset, showing its base easing and one row per override.
Set a row's Parameter to - to disable it, press + for another row,
Clear Overrides to drop them all. Everything stays in sync with the
right-click menus and the EASE cell -- they all read and write the
same spec.

## Rotation
Rotation Blend   how rotation triples (rx/ry/rz, Rx/Ry/Rz, Rotx/Roty/
         Rotz, Rotate...) are blended between presets.
  Euler (legacy)            each channel eased on its own
  Slerp (shortest)          proper quaternion blend along the shortest arc.
                            NOTE: a 0 -> 350 yaw now turns -10, not +350.
  Slerp (preserve winding)  quaternion blend that keeps a sweep authored
                            past 180 degrees going the long way round.
Rotation Groups  extra x/y/z tuplet bases to treat as rotations, space
         separated, case-exact (e.g. "Spin" for Spinx Spiny Spinz).
Periodic Columns single angle-like parameters blended along the shortest
         arc in the Slerp modes: rotate, roll, angle*, hue* and a lone
         rx/Rotz are detected as degrees, phase* as 0..1. Add others as
         name or name:period (e.g. "Twist Offset:1"). Hue 350 -> 10 now
         passes through 0 instead of sweeping back through 180.
Existing projects keep Euler (legacy) so nothing changes until you
switch. Single-axis moves are near-identical in every mode; multi-axis
moves and wrap-around angles are where Slerp matters.

## MIX  (Mode = Mix, plus the Mix page)
Every preset gets a WEIGHT and they all blend at once, so you can sit
between four presets at 0.3 / 0.1 / 0.9 / 0.2 instead of only on the
line between two. Weights come from a CHOP -- a fader bank, an LFO
bank, a Pattern CHOP, a DAT to CHOP -- or from Python.

Weights From
         Parameters       the Mix blocks at the bottom of the page.
         CHOP             the Weights CHOP, one value per preset.
         Parameters x CHOP
                          the blocks act as a per-preset trim or
                          enable and the CHOP drives on top, so a
                          block at 0 keeps that preset out of the mix
                          however hard the CHOP pushes.

## THE MIX BLOCKS
Each block names ONE preset and how hard it pulls, so the sequence can
hold a handful of presets rather than the whole table -- mix presets
3, 9 and 20 and leave the other forty-five out of it.

Preset   which preset this block weights, by its index in the list.
         A block pointing past the end of the table is ignored, and
         two blocks on the same preset add together.
Weight   how hard it pulls.
Populate All Presets
         rebuild the blocks as one per preset, in order. Weights you
         have already dialled are carried over, so repopulating never
         jumps the mix.
Clear Blocks
         drop back to a single empty block.

Reordering the list carries the weights with it: drag a preset and
every block still points at the preset it was dialled for, and the
blocks re-sort so the Mix page reads the same way round as the list.
Inserting and deleting presets shift the blocks the same way, and
deleting a preset removes its block.

Weights  the CHOP, for the CHOP modes. Leave it blank to use whatever
         is wired into the component's SECOND CHOP input.
Map      Exact    one source value per preset. Extra values are
                  trimmed; presets past the end of the source stay at
                  zero. Use this when your faders match your table.
         Stretch  the source is resampled across the whole table, so
                  four channels smear over forty presets. The jam one.
Read     which axis of the source carries the weights. Auto reads the
         SAMPLES of a single-channel CHOP (a Pattern CHOP, a DAT to
         CHOP of one column) and one value per CHANNEL otherwise.
Weights are purely RELATIVE. Every column renormalises by the weights
that actually reached it, so two blocks at 0.1 give the same blend as
two at 1.0, and one block on its own recalls that preset exactly
whatever its weight. With nothing pulling, nothing is written -- the
parameters stay where they are rather than drifting toward some
remembered state. There is no captured base.

How each kind of column blends:
  numbers     weighted average. A preset that left the cell empty
              drops out and the rest renormalise around it.
  rotations   rx/ry/rz triples blend as quaternions rather than per
              channel, whenever Rotation Blend is not Euler. Two
              presets follow exactly the same arc as A to B; three or
              more use a weighted quaternion average.
  angles      hue, phase, rotate, roll and lone rotation axes take the
              short way round, so 350 and 10 average to 0, not to 180.
              Two presets match A to B exactly; three or more fall back
              to a circular mean.
  menus,      cannot be blended, so the HEAVIEST preset wins. With
  toggles,    two presets that is the same midpoint switch the other
  strings     modes make.

Negative weights clamp to zero. From Python:
    seq = op('opSequencer1')
    seq.SetWeights([0, 0.5, 0, 1.0])   # takes over from the CHOP
    seq.SetWeights(None)               # hand it back to the CHOP
    seq.Weights()                      # {preset index: weight}

## PRESETS TABLE (repo)
Presets  the table DAT holding the presets. By default it is the
         prefab inside this component, so presets are saved with it.
Create   clones that table next to the component and points here, so
         presets live in your project (relocatable, externalizable,
         git-friendly). Point the parameter at any table DAT you like.

## Restore
Reset and Prune Stale Columns stash the table first. From Python:
    op('opSequencer1').RestorePresets()

## Non-numeric parameters
Menus, toggles and strings cannot be blended; they switch at the
midpoint of a transition.

## What's new (2026-08)
- Per-parameter easing: an EASE cell can carry "Base | par:Easing ..."
  overrides -- right-click any cell for the easing menu. Overridden
  cells show bold amber; rotation triples ease as one arc.
- Mix: blend presets at once by weight -- from the Mix blocks, from a
  CHOP, or the blocks trimming what the CHOP drives. Each block names
  the preset it weights, so you can mix a handful instead of the whole
  table, and reordering the list carries the weights along with their
  presets. Exact mapping for a fader bank that matches the table,
  Stretch to smear a few channels over the whole thing.
- The Spline and AnyToAny toggles are gone, replaced by one Mode menu
  (Select / A to B / Spline / Mix). They were always mutually
  exclusive; the toggles only hid it, and there was no room for a
  fourth. BREAKING: anything referencing par.Spline or par.Anytoany
  needs to read par.Playmode instead.
- Parameters a mode does not use are greyed out rather than left
  sitting there doing nothing.
- Rotation Blend: rx/ry/rz (and Rx Ry Rz, Rotx Roty Rotz...) blend as
  quaternions along the shortest arc; winding can be preserved.
- Periodic Columns: hue, phase, rotate, roll and lone rotation axes take
  the shortest arc too.
- The list shows 0-based indexes that match Select, and dragging rows
  really reorders the presets.
- Prune Stale Columns drops columns whose parameter was deleted.
- Reset and Prune back the table up; RestorePresets() undoes them.
- Presets table can live outside the component (Create).
- Spline mode is ~6x cheaper on big tables.
- Menus, toggles and strings switch at the midpoint of a transition.
- Insert adds AFTER the selected preset.

## For components that embed it

A shipped OpSequencer carries `Presetsrepo` as a constant empty value and
`Presets_RepoMaker`'s Name at its default. A host that wants the presets
kept in its own repository parameter (the GeoPilot family binds
`Presetsrepo` to its `Pilotpresetsrepo`) re-establishes that on its own
init, since a reloaded copy comes back at the shipped state. Both are
part of the package contract: a change to either is a deliberate one.

