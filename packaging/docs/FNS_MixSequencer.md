---
package: FNS_MixSequencer
summary: 'A step sequencer of mixes for the OpSequencer family: each step is a weight vector over a target sequencer''s presets, the playhead crossfades between steps with easing, and the result rides out as one channel per preset.'
features:
  - name: Quick start
    anchor: quick-start
  - name: The grid
    anchor: the-grid
  - name: TRANSPORT  (Seq page)
    anchor: transport-seq-page
  - name: Notes
    anchor: notes
---

A sequencer of MIXES for the opSequencer family. Each STEP is a weight
vector over a target sequencer's presets; the Step Select playhead
scrubs across the steps, fractions crossfade into the next step with
that step's easing, and the crossfaded vector rides out of out1 as one
channel per preset. Wire that into any OpSequencer's Weights CHOP with
its Mode on Mix and the sequencer plays your sequence with all of Mix
mode's own blending -- renormalisation, quaternion rotation averages,
heaviest-preset-wins for menus.

ANY-TO-ANY sequencing, in any order, is the one-hot special case: a
step with a single 1.0 recalls that preset, and a run of one-hot steps
is a cue list whose transitions are Mix-mode crossfades -- which for
two presets follow exactly the same arc as A to B (verified to 1e-6
against the anytoany mode), so nothing is lost against the pairwise
mode. Paint several weights in a step and the same playhead sequences
BLENDS instead: sit a step at 0.5 / 0.5 and the sequence morphs through
it like any other step.

## Quick start
1. Point Sequencer at an opSequencer and pulse Sync Columns -- the
   weight columns (w0..wN) match its preset count.
2. On that sequencer: Mode = Mix, Weights From = CHOP, and point its
   Weights CHOP at this component's out1.
3. Author steps in the grid: click a # cell to put the playhead there,
   pulse Set One-Hot for a pure recall of One-Hot Preset, or
   double-click weight cells and type. Right-click an EASE cell for
   the easing menu.
4. Scrub Step Select -- or drive it from a CHOP; it wraps. Whole
   numbers are a step exactly, fractions crossfade with the NEXT
   step's EASE.
5. Append Step captures the playhead's CURRENT (eased) vector as a new
   last step: scrub to a blend that sounds right, then keep it.

## The grid
Rows are steps, columns are preset weights. # is the step index Step
Select uses (click to jump). EASE is the curve for the crossfade INTO
that step -- Linear, In/Out/InOut Quad, Cubic and Sine, Smoothstep;
type anything unknown and it falls back to Linear without breaking
playback. Weight cells edit in place; drag rows to reorder (the
indices renumber to match).

## TRANSPORT  (Seq page)
Step Select   the playhead, in steps; wraps; CHOP-drivable. Nothing in
              here owns a clock.
Next / Prev   step to the neighbouring whole step.
Append Step   capture the current (eased) vector as a new last step.
Remove Step   delete the step under the playhead.
Init Steps    wipe to a single one-hot step on preset 0.
One-Hot Preset / Set One-Hot
              make the step under the playhead a pure recall.
Preset Count / Sync Columns
              how many weight columns; Sync reads the Sequencer's
              Length. Weights are keyed by preset INDEX (Mix mode's
              own convention) -- reordering presets in the target
              changes what an index means.
Steps         read-only step count.
Steps (repo) / Create
              the steps table; Create clones it next to this component
              so sequences live in your project -- relocatable,
              externalizable, git-friendly.

## Notes
The out1 weights are RELATIVE -- Mix mode renormalises, so one-hot
steps recall exactly whatever their magnitude, and a step of all
zeros writes nothing at all (the target's parameters stay put; use it
as an explicit hold).

One matrix can drive several sequencers at once -- wire out1 into each
of them (camSequencer's mix, a GeoPilot body's OpSeq_body...) and one
playhead recalls whole multi-component shots.

Parameters are ensured from code through the shared parensure module.
