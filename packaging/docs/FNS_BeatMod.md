---
package: FNS_BeatMod
summary: 'Beat-synced modulation on any parameter: a wave, a CHOP channel or a recorded gesture, locked to the timeline tempo, gliding in instead of cutting, with a manager listing every one of them.'
hotkeys:
  - keys: alt.g
    does: LFO on the hovered parameter or group, with the default wave and period
  - keys: alt.shift.g
    does: Speed on the hovered parameter or group, a rate counting on from the current value
  - keys: ctrl.alt.g
    does: The modulation menu at the mouse for the hovered parameter or group
  - keys: ctrl.shift.g
    does: Remove the modulation from the hovered parameter or group, gliding back
  - keys: alt.t
    does: Tap tempo
  - keys: ctrl.alt.r
    does: 'Record a gesture on the hovered parameter or group: the first change starts it, the key again or a pause ends it, then it loops'
features:
  - name: Beat Mod
    anchor: beat-mod
  - name: Click or hold
    anchor: click-or-hold
  - name: What it builds
    anchor: what-it-builds
  - name: Tempo
    anchor: tempo
  - name: Defaults for new modulations
    anchor: defaults-for-new-modulations
  - name: From a CHOP
    anchor: from-a-chop
  - name: Record a gesture
    anchor: record-a-gesture
  - name: The manager
    anchor: the-manager
  - name: Commands
    anchor: commands
---

## Beat Mod

Hover a parameter, press `Alt+G`, and it starts swinging in time with the
project's tempo. Hover the group instead, the Translate row rather than one of
its fields, and the whole group swings, each member on its own channel: what is
under the mouse decides, a parameter or a group. `Alt+Shift+G` gives a Speed
instead, a rate that counts on from the current value. `Ctrl+Shift+G` glides the
parameter back to where it was and removes the modulator.

There are three kinds of modulation, and they all arrive the same way. A
**wave** runs on the beat. A **channel** of any CHOP drives the parameter
through a chain of shaping. A **recorded gesture** loops something you moved by
hand. Each one lands as its own small network beside the target operator.

Nothing is cut: the parameter keeps its current value on the first frame and the
modulation fades in over the **Default Tween** on the **Tween Curve**, driven by
the Tweener that ships inside the tool. Removing it is the same glide the other
way, after which the parameter is a plain constant again. Deleting a modulator
by hand does the same: the parameters it drove keep the value they showed at
that moment and glide back to where they were.

## Click or hold

`Ctrl+Alt+G` opens a menu at the mouse: every kind, the channels of your source
CHOP, Record a gesture, tick boxes for the beat division, beat sync, how far the
swing reaches and which way, Remove and Tap.

Every item on it answers to the same two gestures.

- **A click applies straight away**, with the settings as they stand. A wave
  goes down with the default period and swing, a channel starts driving the
  parameter, Record arms the recorder.
- **A press held for a moment opens that item's settings instead.** A wave gives
  an XY pad under the cursor, a channel gives the staged panel with its preview,
  and Record gives the Recording options. Let go before the moment passes and it
  is an ordinary click.

**A Plain Click Uses** decides what "the settings as they stand" means: the last
ones set anywhere, so what the pad, the settings strip or Recording options
changed carries on, or the shipped defaults, so a quick click is always the same
modulation and those surfaces only affect the visit they are used in. Either
way, anything you change during a visit to the menu counts as set, so
hold, set, click still applies what you just set.

**Hold Opens The Settings** turns the held gesture off altogether if you would
rather every press was a plain click. A channel is the one exception: with holds
off, clicking it opens the panel, which would otherwise be out of reach.

**Pad Stays Open** is for macOS, where a held button does not track into the
pad's window: with it on, the pad a hold opens stays up after you let go, so
you move freely and click to apply, Escape for nothing.

On the pad, drag right for a faster beat division and up for a wider swing
around the current value (for Speed, up is a faster climb: the rate as a share
of the slider range per division), with both numbers shown as you go, and
release to apply. The strip above the pad holds two rows of buttons, the range
strategy (Edge, Frac, Full) and the swing's polarity (+ up only, − down only, ±
both ways), the current ones lit; resting the pointer on one for a moment,
button still down, selects it. A right-click locks the page you are on, so you
can set several before letting go. Release at the bottom edge to apply nothing
(with Pad Stays Open, a click applies and Escape applies nothing).

## What it builds

Each modulation is a small network of stock TouchDesigner operators, dropped
right below the target operator and named after it: `beatmod_geo1_t` for the
translate group of `geo1`. The parameter's expression reads one channel of that
network's Out CHOP, `op('beatmod_geo1_t/out1')['tx']`, and nothing else. The
network does not depend on the toolkit, so a project keeps playing after
FNSTools is gone, and every setting is a parameter on the modulator itself:

- **Beats**: the cycle length in beats of the timeline tempo. 4 is a bar at 4/4,
  0.25 a sixteenth. The divisions the menu and the pad offer come from **Beat
  Divisions** on the tool, a list of beats in any order, fractions such as 1/3
  included; the tool sorts them.
- **Wave**: sine, triangle, ramp, square, pulse, a gaussian bump once per cycle,
  two random waves (one holds a new value each cycle, the other glides between
  them), or **Speed**: a real Speed CHOP counting on from the current value by
  Multiplier times the range per period, and per second with **Speed Syncs To
  Beat** off. Each modulator has its own **Seed**, so two random modulations
  never move together unless you give them the same seed. On a group, **Random
  Shared By Channels** makes every member draw the same value each cycle, so a
  translate group moves as one and a colour flickers as a whole; off, each
  member draws its own.
- **Phase** and **Spread**: shift the cycle, and stagger the members of a group
  by a fraction of a cycle each.
- **Range Min** and **Range Max**: the window the modulation sweeps. By default
  a wave swings around the value the parameter had, as far as the nearer end of
  its slider range, so it never leaves the slider; the menu can pick a smaller
  swing instead, a fraction of the slider range each way (**Default Fraction**,
  a tenth), or the whole slider range from end to end. **Relative To Rest** on
  the modulator says whether Min and Max are relative to each member's own rest
  value (the two swings around the value) or absolute (the slider range).
  **Multiplier** scales the sweep (1 is the whole window) and, for Speed, is the
  fraction of the slider range added per period; **Offset** shifts the output in
  the parameter's units. The value the parameter had is kept in a small CHOP
  inside, one channel per member: the glide starts from it and Remove returns to
  it.
- **Blend** and **Tween**: how much of the swing reaches the output, and the
  seconds a Blend change takes to arrive. This is the glide: the tool sets Blend
  to 0, applies the expression, then tweens Blend to 1 with Tweener on the
  tool's curve; a project without the tool glides Blend through the modulator's
  own Lag CHOP instead.

The modulator is placed on the grid under its target and moved down past
anything it would overlap, so the network stays readable, and coloured by kind:
a beat modulator is amber, one driven from a CHOP green, a recorded gesture
violet.

**Random speed** is Speed with its pace re-drawn every beat division and
held: the value keeps moving, but how fast, and by default which way, is a
new draw each division, so it wanders around where it started on the beat
grid. *Random Speed Either Way* on the tool decides whether it can turn
back or only runs forward, and *Random Speed Shared By Members* whether a
group drifts as one; both are on to begin with and editable on the
modulator afterwards (Speed Shape, Random Speed Either Way, Randomlink).
**Random jumps** is the same in discrete time: nothing moves between
beats, and on each division a random amount, up to the Speed Rate's share
of the range, is added at once. Hold either item for the same pad as
Speed.

## Tempo

Every modulator runs its own beat at TouchDesigner's global BPM, integrating the
tempo as it goes, so a tempo change only changes its speed from that moment on:
tapping a new tempo never makes a running modulation jump, and all modulators
keep their relative timing. A modulator's **Play Mode** can instead lock it to
the timeline (deterministic, but it jumps on a tempo change and pauses with the
timeline) or follow TouchDesigner's own global beat.

The tool's **BPM** parameter always shows the timeline's tempo, wherever it was
changed; set it there, or tap it: **Tap Tempo** (or `Alt+T`) takes the mean of
your last taps once four are in; a pause of more than two seconds starts a new
sequence. **First Tap Resets The Bar**, off by default, restarts every
modulator's beat together on the first tap so the bar lines up with your
downbeat. The manager carries the tempo and a Tap button too.

## Defaults for new modulations

**Beat Divisions**, **Default Period**, **Default Wave**, **Default Range**,
**Default Fraction**, **Default Multiplier**, **Default Speed**, **Speed Syncs
To Beat**, **Default Tween** and **Tween Curve** (every easing curve Tweener
ships, from linear to elastic and bounce) on the tool decide what a new
modulation starts with; the menu ticks the period, the sync, whether random
values are shared by the members, and the range. Fraction and Speed are
fractions of the parameter's slider range, so a fraction swing is a tenth of it
each way and Speed adds a tenth of it per period. These defaults roam with your
other FNSTools settings.

Apply to a parameter that already has one of these modulators and the modulator
changes in place instead: the period, the window and the multiplier glide to the
new settings over the modulator's Tween, and a new wave crossfades in from a
second wave bank inside the modulator, so nothing jumps. The tool still refuses
a parameter that carries an expression, export or bind it did not write, and a
member modulated in another grouping. A modulation of another kind on the same
parameter glides out first and the new one in after it.

## From a CHOP

Point **Source CHOP** on the tool's CHOP Mod page at any CHOP, one sample per
channel, and the menu's **From CHOP** opens a sub-menu of its channels. Click
one and the parameter is driven from it straight away. Hold it and a panel opens
with a staged modulator inside, driving nothing yet: the channel scrolls by at
the top, the staged result below it in the parameter's own units, and everything
is set up there before anything is applied.

The panel's pages are **Swing** (smoothing and swing), **Norm** (the window a
normalisation looks back over, so a source of any scale drives the full swing),
**Thresh** (threshold and peak of a trigger envelope, shaped as
attack-and-release, held while the channel stays above the threshold, or
attack-and-decay, one shot per hit), **Atk** (attack, and release or decay),
**Range** (the source values that mean the bottom and top of the swing), **To**
(where those two land: 0 and 1 is the plain mapping, swap them to run the
channel backwards, or narrow them to sweep only part of the swing) and **Lim** (a
limit that clamps, loops or bounces what runs past). Drag in the pad to set a
page's two numbers, click the options above it, watch the preview, then
**Apply**: the modulator goes down beside the target with the usual glide, or
the one already there changes in place. **Cancel** or Escape drops it all.

## Record a gesture

Hover a parameter, press `Ctrl+Alt+R`, and move it: the first change starts a
recording of the gesture, every frame of it, on that parameter or on every
member of the hovered group.

Before you move anything you can mark more: hover another parameter, on the same
operator or any other one, and press `Ctrl+Alt+R` again to add it to the same
take. The key only marks while the recorder is waiting; the first change closes
the list and starts recording, and from then on the key ends the take. Each
marked operator gets its own modulator, all of them the same length, so a
gesture across four parameters of three operators stays together.

Press `Ctrl+Alt+R` again to end it, or just stop moving: after **Stop After**
seconds of stillness (two by default) the recording ends on its own, and that
still tail is cut off so the loop ends where the gesture did. The gesture then
loops on the parameter as a recorded modulator, gliding in from where the
parameter sits.

Played back over the beat, as it is by default, it takes the beat division
nearest its recorded length (a gesture of 1.3 seconds at 120 BPM loops over two
beats) and follows the tempo from then on; **Play Back** switches it to its own
speed, the seconds it was recorded in. The seam is a crossfade from the end of
the recording into its start, a bridge whose length is a share of the recording;
**Ping-pong** plays it forward then backward, and **Hard** cuts. Afterwards the
modulator's own parameters change any of it, Beats, Speed, Phase, Reverse and
the seam, and the take itself is a locked CHOP inside it: point it at any CHOP
and unlock it to loop that instead.

**Record a gesture** is on the menu too, and holds like a wave does: hold it and
**Recording options** opens instead of arming, a tick per setting, so a quick
click records with the settings as they are and a hold sets them first. That
submenu is also its own item beside Record a gesture, for reaching it without
holding. It covers how a take plays back, whether it rounds to a division, the
seam and its length, and when it stops, and it stays open, so several can be set
in one visit.

A parameter already modulated is refused: remove that first, then record. So are
two marked operators of the same name, because the take tells their channels
apart by that name.

## The manager

**Modulator Manager** on the tool, or the command of the same name, opens a
window listing every modulator in the project: the operator and parameters it
drives, whether it is an LFO, a Speed, a Channel or a Recorded gesture, how long
one cycle is, the wave or channel or take behind it, the source CHOP a channel
modulator reads from, and how far it is faded in. The tempo and a Tap button sit
at the top, with the count, a Refresh and Sweep orphans beside them, and
clicking a column header sorts by it.

Every cell is a way in. Clicking the **Target** opens that operator's
parameters, **Source** shows the source CHOP in the network, **Blend** mutes the
modulator and unmutes it again, gliding both ways so nothing jumps, and the
three narrow columns at the end **Go** to the modulator in the network, open its
own **Pars**, and remove it with **X**, which glides the parameters back to rest
exactly as Remove does. **Double-click a row** to reopen whatever set it up: the
XY pad for a wave or a rate, the staged panel for a channel, its own parameters
for a recording. A pad opened this way stays up, since no button is being held,
and the next click applies it.

The list keeps itself current while the window is open, so a modulator placed,
removed or faded anywhere in the project appears without asking. **Status**
marks a modulator as orphaned when nothing reads it any more, because the
operator it drove is gone or its parameters no longer point at it, and **Sweep
orphans** clears them: they are still cooking and driving nothing, so there is
nothing to glide back.

Modulators are tagged as they are placed, so the list finds them again after a
restart, wherever they sit and whatever they have been renamed to. Anything
placed by an older version is recognised by its shape and tagged on the way
past.

The manager is also a tab in **Hub**, listed as *BeatMod*, so it sits beside
the other toolkit managers instead of only in its own window. It behaves the
same either way, and it only keeps itself up to date while it is the tab you are
looking at.

## Commands

The quick-launch palette and the launcher list **LFO on hovered par**, **Speed
on hovered par**, **Modulation menu for hovered par**, **Remove modulation from
hovered par**, **Record a gesture on hovered par**, **Modulator manager**, **Tap
tempo** and **Set BPM**. From the palette, the hovered parameter is the one you
were over when you summoned it.
