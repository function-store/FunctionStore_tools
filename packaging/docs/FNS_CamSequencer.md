---
package: FNS_CamSequencer
summary: 'A Camera COMP with two sequencers inside: one for its own transform and lens, one for the Look At target. Frame, append, scrub; drive it from a CHOP; fly it with a joystick; or take over a palette camera viewport.'
features:
  - name: Quick start
    anchor: quick-start
  - name: Seq page
    anchor: seq-page
  - name: Viewport mode
    anchor: viewport-mode
  - name: LOOK AT MODE  (Seq page)
    anchor: look-at-mode-seq-page
  - name: Presets page
    anchor: presets-page
  - name: CONTROL AND MAPPING PAGES (joystick / controller)
    anchor: control-and-mapping-pages-joystick-controller
  - name: ROLL -- banking the camera
    anchor: roll-banking-the-camera
  - name: SURFACE COLLISION  (Control page, 2.0)
    anchor: surface-collision-control-page-2-0
  - name: Python api
    anchor: python-api
  - name: The lists
    anchor: the-lists
  - name: What's new
    anchor: what-s-new
---

A Camera COMP with two OpSequencers inside: one sequences the camera's
own transform and lens, the other sequences the Look At target. Every
control on the Seq page drives BOTH; open either inner sequencer
(Presets page: Open / Open2) for its preset list.

It can also take over a palette cameraViewport instead of being the
camera itself -- see VIEWPORT MODE.

## Quick start
1. Frame the camera, press APPEND. Move it, press APPEND. Repeat.
2. Scrub SELECT -- or drive it from a CHOP -- to move through the presets
   with the chosen easing.
3. Optional: set a Look At target (Xform page). Its position is
   sequenced by the second sequencer; the camera keeps aiming at it.
4. Optional: plug in a game controller and map it on the Control page
   (Learn Forward, move the stick...) to fly the camera and capture
   presets from the pad -- see CONTROL PAGE.

## Seq page
Append / Replace / Insert / Remove / Init   as in OpSequencer
Mode     Select (scrub) / A to B / Spline / Mix (weights), as in
         OpSequencer. Applied to both inner sequencers.
Select   the playhead (wraps). Whole numbers recall, fractions blend.
Easing / Override / Bind / Preset A / Preset B
         as in OpSequencer, applied to both inner sequencers.
         Per-parameter easing overrides work in both preset lists:
         right-click a cell for the easing menu, or use the easing
         strip below each list's buttons (the EASE button hides it) --
         see PER-PARAMETER EASING in OpSequencer's README. Each inner
         sequencer also carries the same controls on its Easing
         parameter page.
Mix page Weights / Map / Read -- one weight CHOP drives BOTH inner
         sequencers. See MIX in OpSequencer's README; under Mix the
         aim blends between the two HEAVIEST presets, in their own
         proportion.
Length   number of camera presets (read-only)

Rotation Blend
  Euler (legacy)            each rotation channel eased on its own
  Slerp (shortest)          quaternion blend, shortest arc. A 0 -> 350
                            yaw now turns -10, not +350.
  Slerp (preserve winding)  quaternion blend that keeps a sweep past
                            180 degrees going the long way round.
  Single angle parameters (roll, a lone rotation axis) take the shortest
  arc in the Slerp modes too.
  Existing projects keep Euler (legacy) until you switch.
  With a Look At target set, the camera's AIM is fixed by that target;
  rotation presets still swing the camera around its pivot and set roll.

## Viewport mode
The palette cameraViewport (the interactive tumble/pan/dolly camera)
does not use tx/ty/tz/rx/ry/rz: its pose is a matrix plus a tumble
pivot. CamSequencer can sequence it anyway. Two ways in:

  - drop this component INSIDE a cameraViewport         (zero setup)
  - or set Camera Viewport (Viewport page) to one       (side by side)

While a viewport is in charge:
  - the camera sequencer records Position / Rotate / Pivot / FOV
    (Viewport page) instead of this camera's own pars; the viewport's
    pose is mirrored there and written back from there, in both
    directions, without echo
  - navigate the viewport by hand at any time; Append captures what
    you see, including the tumble pivot, so recalling a preset makes the
    next tumble orbit the same point
  - the Look At sequencer idles (the pivot is the orbit center)
  - Follow Viewport makes THIS camera render the viewport's view through
    its Pre-Transform, so a Render TOP can keep using it in either mode.
    Clear this camera's Look At and keep its Translate/Rotate at zero
    (a warning on the node says when they are not).
  - Read Camera re-links the viewport and re-reads its state

Each mode has its own presets table: Camera Presets (normal) and
Viewport Presets (viewport), both on the Presets page. Switching modes
only changes which one the camera sequencer reads -- neither table is
ever touched, and the list shows the active one. The viewport's
Transform DAT par is pointed at transform_table inside this component
while linked and handed back when you leave the mode (if it already
points elsewhere the link is refused with a warning on this node).

Python: op('camSequencer1').ext.CamSeqExt.viewport / .ext.CamSeqExt.inViewportMode / .ext.CamSeqExt.linked,
        .PullFromCamera() / .PushToCamera() / .ext.CamSeqExt.applyMode()

## LOOK AT MODE  (Seq page)
Transform (move the target)   the second sequencer moves ONE Look At
         object around -- the historical behaviour.
Targets (object per preset)   each camera preset stores a Look At
         OBJECT instead: set Look At Target, Append. The camera's Look
         At is pointed at a small aim null docked to this component
         (<name>_Lookataim); during a blend the aim glides from the
         previous preset's object to the next one with the transition's
         easing, and it follows the objects LIVE. What it aims at is the
         GEOMETRY each target draws, not the COMP's origin -- move an
         object with a transform SOP and the origin stays behind, so
         aiming there can miss it entirely. Two Constant CHOPs inside
         carry those points and easeInterpolator1 blends between them.
         The aim null itself has to live outside: a child of the camera
         inherits the camera's transform, which makes the aim circular.
         It is docked to the component, as is the Look At Pick null, so
         both travel with it and stay out of the way. The Look At transform sequencer idles in this
         mode. Spline and Mix blends use a linear aim; A to B works.
         The Lookattarget column in the presets list is editable like
         any other cell (paths resolve like the par: siblings first).
         The camera's own Look At stays a valid entry point: point it
         at any object (type, drop, pick) and that object is adopted
         as Look At Target while the par returns to the aim null.
         NO look-at for a preset: leave its Look At Target empty. A
         transition whose presets are both empty releases the camera
         (Look At cleared, its Rotate rules again) and the tether
         re-engages when a targeted preset is involved. Turn the whole
         feature off with Look At Mode: Transform -- the previous Look
         At comes back.

## Presets page
Open / Open2             open the camera / Look At preset lists
Camera Presets + Create  table holding the camera presets. Create
                         clones it next to this component as
                         camSequencer1_Campresets so presets live in
                         your project (relocatable, externalizable).
Viewport Presets + Create same for viewport mode (Position / Rotate /
                         Pivot / FOV of the cameraViewport). Only the
                         table of the active mode is enabled. If the
                         other mode's presets already live outside the
                         component, entering a mode creates its external
                         table for you as well.
Look At Presets + Create same for the Look At target.

## CONTROL AND MAPPING PAGES (joystick / controller)
Two pages, because they are two jobs. MAPPING is which physical control is
which -- the Source CHOP, a + and a - channel per axis, a Learn pulse for
each, and how a channel is read. CONTROL is what the camera then does: the
two mode menus, the speeds, picking, collision, and the sequencer buttons.
They were one 70-parameter page until 1.11.0, of which 46 were mapping
plumbing you set once and never look at again.

Fly the camera from a game controller -- or any CHOP -- and drive the
sequencer from the same pad. Nothing is hard-wired to a pad layout: you
teach every control by moving it (Learn), so an Xbox pad, a DualShock,
a MIDI surface or an OSC app all work the same way. Everything the pad
does is applied to the live camera; presets only change when you
Capture.

  Typical layout      left stick  Forward / Strafe   right stick  Yaw / Pitch
                      triggers    Rise (two one-way controls, see AXES)
                      bumpers     Roll left / right, or Scrub back /
                                  forward -- or map Roll onto a stick
                                  you already use and gate it with a
                                  Roll Modifier button (see ROLL)
                      A           Capture       X   Teleport
                      LB (hold)   Orbit         Y   Look At Pick
                      d-pad       Next / Prev   1-4 Preset buttons

SOURCE  (Mapping page)
Source CHOP   the CHOP whose channels are the controls. Empty = the
              internal Joystick CHOP (joystick_internal: first game
              controller found, axes -1..1, buttons b1..b32). Point it
              at a MIDI In, OSC In, Keyboard In, your own Joystick CHOP
              or a Constant CHOP instead -- any channels will do.
              The internal one stays switched off until it has a
              reader: it arms while a Learn is listening, and once a
              channel is mapped with Active on. A project that never
              maps a controller never polls for one (3.0.5). If you plug
              a controller in and nothing moves, map an axis first.
Active        mutes every mapped control without losing the mapping.
Learn Status  what learn mode is waiting for / the last mapping made.

BODIES MOVED OUT (2.0)
The flight models that used to live here -- Assisted, Forces, Walking,
Driving, Aerobatic and the Ground contact under them -- are GeoPilot's
now: a Geometry COMP that flies ANYTHING, not only a camera, with the
same mapping, the same measured numbers and the same pages. Two ways to
put this camera on a body:

  - wire this component under a GeoPilot (object connectors): rigid
    coupling, and the pilot's HeadExt drives the free head, the chase
    spring and the bob.
  - point Source CHOP at the pilot's head bus (geoPilot1/null_headbus):
    the channels are named Yaw, Pitch, Roll, Zoom, Scrub, Capture, Next,
    Prev -- type those names into the Channel fields and you are mapped
    with nothing to learn.

What stays here is the camera-authoring kit: everything below, plus
SURFACE COLLISION.

Control Smoothing   the sticks ramp in and out instead of snapping, so
  Smoothing Time    rates never start or stop dead. The single biggest
                    change to how flying feels; 0.1 is crisp, 0.4 heavy.
                    Buttons are read before the filter and stay instant.

LEARNING  (Mapping page)
Every action has a Channel field (type a name, or learn it) and a
Learn pulse. Press Learn, move the control: the first source channel
that moves past the threshold is mapped. Buttons are done at that
point. Axes keep listening for a second control, see below. Pressing
another Learn, or changing the Source, abandons a learn in progress.
Learn Presets is a toggle: while on, every new button pressed is
appended to Preset Channels in order; turn it off to finish.

AXES -- Forward, Strafe, Rise, Yaw, Pitch, Roll, Zoom, Scrub
Each axis has a + channel and an optional - channel, so it is either
ONE stick axis that goes both ways, or a PAIR of one-way controls: the
two triggers for Rise / fall, the two bumpers for Scrub, two MIDI
buttons for Zoom in / out. Value = travel of the + control minus travel
of the - control. Each control's travel is measured from its own
RESTING value (recorded when it is learned, in table_axisrest -- a
trigger resting at -1 next to a stick resting at 0 is fine) and
normalised so a full pull is 1 whatever the range.
Learn <axis>  move the control for the + direction (mapped as +), then
              EITHER press the opposite control -> it becomes the -
              channel, done; OR let go and wait Learn Timeout seconds /
              move the same control again / press that Learn again ->
              one control for both directions, done. Letting a control
              go back to rest never counts as a move, so a trigger pair
              is never mistaken for a stick.
Learn Timeout seconds after the + control is released before the learn
              settles on it alone (default 1; 0 = wait for you).
Axis Centre   resting value assumed for a channel you TYPED in instead
              of learning (learned ones keep their own): 0 for -1..1
              sources, 0.5 for a 0..1 stick axis, 0 for a 0..1 trigger.
Dead Zone     travel around the centre that counts as centred; the rest
              is rescaled so full deflection still reaches full speed.
              (The internal Joystick CHOP has its own dead zone too.)

## ROLL -- banking the camera
Roll banks the camera about the axis it is looking down; a positive
control banks RIGHT, at Roll Speed degrees per second.

  Learn Roll        the control that banks. With a spare control (the
                    two bumpers, roll left and right) that is all you
                    need: Roll is then an ordinary always-live axis.
  Roll Modifier     a button that GATES Roll, for a pad with nothing
                    spare. Map Roll to a control you ALREADY use --
                    the strafe stick, the yaw stick -- and while the
                    button is held that control banks instead of doing
                    its usual job; let go and it strafes (or yaws)
                    again. Only the axis sharing that control is
                    suppressed, so the other hand keeps flying.
                    Learn Roll Modifier maps the button.
  Level Horizon     takes the bank back out (roll to 0) without moving
                    the camera or its aim -- a button, or the pulse.

So: hold the modifier and the shared control banks and does NOT
strafe; release it and Roll is idle. Without a modifier mapped, do not
point Roll at a control another axis uses -- it would do both at once.

Roll is a real third angle only when the camera applies its Z rotation
innermost, so the first roll sets this camera's Rotate Order to
"Rz Rx Ry". Under TD's default "Rx Ry Rz" the Z rotation is applied in
world space and would swing the AIM instead of banking. The switch
changes nothing while rz is 0 -- which it is on every preset made
before this, since nothing rolled the camera -- and it leaves Yaw,
Pitch and orbiting exactly as they were. Presets record the roll in
their rz column like any other value, and blend it with the rest.

Two things to know:
  - a Look At target does NOT stop roll (it fixes the aim, not the
    bank), but if the camera also has a non-zero Pivot it will swing
    slightly around that pivot as it rolls -- the node says so, and
    Reset Pivot makes roll exact (measured: pivot zeroed, a roll moves
    position and aim by exactly 0).
  - viewport mode has no roll: the palette cameraViewport navigates by
    matrix and its tumble assumes world up, so a rolled viewport would
    disagree with its own mouse. The Roll controls are disabled there.

FLYING
Flying        read-only: what the sticks are doing right now and around
              what -- "Flying free", "Flying free, looking at geo2",
              "Orbiting geo2", "Orbiting the point you picked". The
              three switches (Fly Mode, a Look At, the Orbit button)
              compose, so this says what they add up to.
Fly Mode      what the sticks do when the Orbit button is NOT held:
  Free-fly    FPS / drone: Forward / Strafe move along the camera's own
              axes, Rise is world up, Yaw / Pitch turn the camera in
              place (Pitch stops short of straight up / down).
  Orbit       the tether the Orbit button gives you, held permanently --
              but it needs something to orbit: a Look At target, or the
              viewport's tumble pivot. With neither it simply flies
              free and the Flying readout says so, rather than orbiting
              an invisible point ahead of you that drifts with wherever
              you face.
              Pinned to a sphere there are only three ways to move --
              the angle round, the angle above, and the distance -- so
              every axis is one of those: Yaw / Pitch swing you round
              at a fixed distance, Strafe / Rise do exactly the same,
              and Forward dollies in and out. The pivot itself never
              moves, so the subject cannot slide out of frame; press
              Orbit again to put it somewhere else.
              The two sticks keep their own conventions and therefore
              swing you OPPOSITE ways: the left one moves (push right,
              go right), the right one looks (push right and the world
              sweeps right, which carries you left). Push both the same
              way and they cancel. Pivot: the
              viewport's tumble pivot (viewport mode), else the Look At
              target, else a point Orbit Distance ahead of the camera
              (dolly then moves that point with you).
  Look At     a Look At target (Xform page, or Look At Pick below)
              locks the AIM and nothing else. The left stick flies
              exactly as it does without one: the camera keeps a heading
              of its own while the lens stays on the subject -- a drone
              with a gimbal. Forward is forward, wherever you happen to
              be looking, at free-flight speed; you can fly straight
              past the subject or through it. Only an orbit constrains
              where you can go, and only Collision stops you.
              Movement cannot borrow the gaze here, because a gaze
              locked to a target makes "forward" mean "towards the
              target" -- an attractor, not a direction. Every version of
              that misbehaves: it either dies at a fixed distance, or
              flies through and drags you out the far side staring
              backwards.
              The right stick has no view to turn while the aim is
              locked, so it works ON the subject instead, doing the two
              things you want of something you are locked onto: Yaw
              takes you round it at the radius you are already at, Pitch
              reels you in and lets you back out (push up to close in,
              at Move Speed, no nearer than 0.05). Both are real moves
              you watch happen -- nothing about the right stick is
              invisible any more. Going round carries your heading with
              it, so "forward" keeps its meaning as you walk around;
              changing the distance touches neither the direction to the
              subject nor the heading.
              Up and down is left to Rise, on the stick you fly with.
              Note that Rise is a translation, so it changes your
              distance as it lifts you (one second from 5.049 leaves you
              at 6.608). To arc over the top at a FIXED radius, hold the
              Orbit button -- that is the one thing the right stick no
              longer does, and Orbit is where it lives.
              With no subject to work on, Yaw / Pitch go back to
              steering the heading, and only while you are moving.
Move Speed    units per second at full deflection (Forward / Strafe /
              Rise) -- moving you through the world.
Dolly Speed   units per second at full deflection when a control changes
              your DISTANCE to what you are locked onto instead: Pitch
              under a Look At, Forward while orbiting. Separate because
              closing a gap is a much shorter journey than crossing a
              room -- at Move Speed 5 a 5-unit standoff is gone in a
              second, which reads as twitchy next to the circling on the
              same stick. At 1 the same second closes 5.049 to 4.049.
              Leave it equal to Move Speed to keep them in step.
Turn Speed    degrees per second at full deflection (Yaw / Pitch) --
              turning, tilting the heading, or going round a subject.
Roll Speed    degrees per second at full deflection of Roll.
Zoom Speed    Zoom drives whatever the projection really uses: FOV
              (perspective, in degrees per second), Focal Length when
              the Viewing Angle Method is Focal Length / Aperture, Ortho
              Width when orthographic (both by Zoom Speed PERCENT per
              second), both during a persp/ortho blend, the viewport's
              FOV in viewport mode.
Orbit Distance  how far ahead the pivot sits when nothing is picked.
Invert Pitch  push forward to look down.
Reset Pivot   zero this camera's own Pivot (Xform page) WITHOUT moving
              the view, so a turn is a turn in place. Flying already
              accounts for a pivot, but presets carry pivots too, and a
              recalled one makes TD's own tumble swing around it.

What gets written: the camera's own tx / ty / tz / rx / ry / rz (and
fov / focal / orthowidth) in normal mode; the Viewport page's Position /
Rotate / Pivot / FOV in viewport mode, so the cameraViewport follows.
Only constant-mode pars are written -- an expression or bind you put on
one is left alone.

PICKING -- what you are looking at
Render TOP    the render this camera renders through. Empty = the first
              Render TOP whose Camera is this component (or its
              cameraViewport). A Render Pick CHOP samples its CENTRE
              pixel: world position, surface normal, object hit.
Orbit         button, HELD (Orbit (hold) toggle from the UI): on press
              the point you are looking at becomes the pivot (nothing
              there: the point Orbit Distance ahead); while held Yaw /
              Pitch tumble around it, Strafe / Rise do the same (see
              below), Forward dollies in and out;
              let go and you are free again from wherever that
              left you. The pivot lives as long as the button, so there
              is nothing to reset. In viewport mode the press also sets
              the tumble pivot, which the viewport's own mouse tumble
              then uses. A Look At does not take this over: the aim
              stays locked on the target while you orbit and pan the
              point you actually picked.
Look At Pick  button (Look At Pick Now from the UI), toggles a tether to
              the object you are looking at: aim locked, Yaw / Pitch
              orbit it, Forward dollies. Press again to release. (While
              it holds you cannot look at nothing, so there is no
              sky-clear.) Viewport mode has no Look At: sets the tumble
              pivot.
              What it aims AT is the spot you picked, not the origin.
              TD's own Look At points at a COMP's origin, which is only
              where the object appears if it happens to be centred
              there -- move it with a transform SOP, or anywhere in the
              chain rather than on the COMP, and the origin is left
              behind. Two objects offset that way both aim you at the
              same empty spot, which reads as the pick being stuck on
              one target. So the camera is pointed at a small null
              (<name>_Lookatpick, docked beside this component) parked
              on the target's live geometry -- at the point you picked,
              carried as an offset from the geometry's centre. It
              follows the object however it moves: the COMP's transform,
              a transform SOP, deformation. Nothing has to be translated
              any particular way for this to work, and taking a target
              does not shift your framing (aiming at the bare centre
              swung the view 3 degrees from ten units out and 45 from
              one). Rotating the object slides the spot around it, but
              never off it.
              Neither end of that snaps the view:
Look At Capture  a Look At aims at the object's ORIGIN, which is rarely
              exactly where you were looking, so grabbing one is a real
              swing -- this is how long it takes, eased in and out, and
              it arrives exactly on time before the tether takes over.
              Press again mid-swing to stop where you are. 0 gives the
              old instant snap. Releasing needs no setting: the aim you
              had is written into the camera first, so letting go
              carries straight on from where you were looking (the
              rotation pars go stale while a Look At drives the camera,
              and would otherwise snap back to whatever they held).
              A camera with a Pivot is kept in place through both.
Mode Blend    seconds to ease the camera from one way of moving into
              another. Free flight, a Look At and an orbit read the
              sticks differently -- with yaw held, being locked on a
              subject moves you 0.26 units a frame and turns you 0
              degrees; the next frame after letting go it is 0 units and
              3 degrees. Nothing teleports, but your MOTION swaps in one
              frame, which is felt as a jolt. This rounds that corner,
              entering and leaving alike and between orbit and Look At
              too. 0 switches instantly.
Teleport      button (Teleport Now from the UI): jump to the point you
              are looking at, Teleport Distance off the surface along
              its normal, orientation kept.
Collision     while on, flying forward / dollying keeps a centre pick
              going and stops Stand-off short of what is ahead. Stand-
              off is never 0 (floor 0.05): a camera allowed onto the
              surface picks the far side next frame and walks through;
              keep it above the Near clip too. The pick is the CENTRE
              pixel only, so something you pass beside is not seen.
              Frustum only -- nothing guards the sides, the back, above
              or below. One extra pick render per frame while moving
              forward; off, picking costs nothing until a button asks.

SEQUENCER -- from the same pad
Scrub         axis (or pair): hold it and Select travels through the
              presets at Scrub Speed presets per second; let go and it
              stops. Wraps around the sequence.
Next / Prev   buttons: step Select to the neighbouring whole preset,
              wrapping at either end.
Capture       button: Append a preset from the current state (same as
              the Seq page Append pulse). Fly somewhere, press it.
Preset Channels  buttons that recall a preset directly: the first
              listed channel is preset 0, the second preset 1, ...
              Build it with Learn Presets or type the names.
These are applied as a step or delta to Select's own value -- nothing
is bound or exported -- so the list, a CHOP, Python and the pad all
keep working together. The A to B and Mix modes are not driven by
the pad -- they have no playhead for it to step.

The mapping is saved with the component; a different controller just
needs its controls learned again. The shipped .tox comes unmapped.

Python: op('camSequencer1').ext.CamJoyExt.learn('Forward') / .ext.CamJoyExt.stopLearn() /
        .ext.CamJoyExt.onFlyFrame() / .ext.CamJoyExt.orbitStart() / .ext.CamJoyExt.orbitEnd() / .ext.CamJoyExt.lookAtPick() /
        .Teleport() / .ext.CamJoyExt.resetPivot() / .LevelHorizon() / .Step(+1) /
        .GoTo(i) / .Capture()
        .ext.CamJoyExt.renderTop (the Render TOP in use)

## SURFACE COLLISION  (Control page, 2.0)
Stop flown motion at any surface in its way -- floors included. The old
Wall Collision walked; this one flies: the probe fires along the
direction you are actually MOVING, so descending into terrain lands on
it exactly the way flying into a wall does, and a climb can meet a
ceiling. Off by default, because it costs a render and a pick per frame
you are moving, and bypassed entirely while off.

Surface Collision   the toggle.
Stand-off           how far from a surface you are stopped, measured
                    PERPENDICULAR to the surface rather than along the
                    probe ray -- at a shallow angle the ray distance is
                    far longer than the gap actually between you, and
                    clamping on it let a diagonal approach get too
                    close. Keep it above the Near clip.
Slide               what happens when you meet a surface at an angle.
                    1 keeps the part of your movement that runs ALONG
                    it, so a corridor or a hillside stays flyable; 0
                    stops you dead.
Collision Geometry  what the probe can hit. Empty means whatever the
                    Render TOP renders, so it follows the scene by
                    itself.

One probe, one ray, along your centre line: a surface you clip with a
shoulder while passing at an angle is not seen, and that is the same
trade the walking probe made. It is a proxy render and a pick rather
than a Ray SOP, because a ray sees only CPU-side SOP geometry and would
fly you straight through a POP, GPU displacement or an instance.

The one rule worth knowing: collision constrains FLOWN motion only.
Preset recalls, Teleport and a hand on the parameters are sovereign --
if a recalled preset places the camera inside a rock, it goes inside
the rock. The alternative is preset playback that depends on what
happens to be in the scene, which is worse than the clipped frame you
can see and fix. (Momentum follows the same contract it always has: a
jump larger than the motion could explain drops the carried state.)

These parameters are ensured FROM CODE through the shared parensure
module (shared/parensure.py in the repo), so they exist on any copy of
this component the moment the extension initialises -- the first of
this component's pages to work that way.

## Python api
Three tiers, and the line between them is whether a caller outside this
component has any business with the name.

PROMOTED (op('camSequencer1').Name) is the API: generic verbs with no
parameter that already does the job. There are eight, and that is meant to
be the whole list --
    Step  GoTo  Capture  LevelHorizon  Teleport
    LinkCamera  PullFromCamera  PushToCamera
(StickGround, DetachGround and Jump moved to GeoPilot with the bodies.)

EVERYTHING ELSE lives on the extension: op('camSequencer1').ext.CamJoyExt.x
or .ext.CamSeqExt.x. That covers three kinds of thing which were promoted
before and should not have been. Anything a custom PARAMETER already does
(learn, lookAtPick, resetPivot, applyDynPreset -- the pulses are the API).
And internal plumbing: the callback
entries (onFlyFrame, onControlChange, onMixFrame), the sync helpers, and the
state properties expressions read (viewport, inViewportMode,
groundGeometry, renderTop). The HUD helpers (hudTape, hudSlide, hudText)
moved to GeoPilot with the instruments they read.

_leadingUnderscore stays what it was: private, and not for callers at all.

In parameter expressions that means me.ext.CamSeqExt.inViewportMode rather
than me.InViewportMode -- longer, but it says which extension owns the
answer, which the bare name never did.

## The lists
#  is the 0-based preset index SELECT uses. Click a row to recall it,
drag rows to reorder, middle-click a header to drop that column.
Inner sequencers also have Reset and Prune Stale Columns; both stash
the table first (RestorePresets() from Python brings it back).

## What's new
2.0.0 (2026-08)
- The split. Everything that was a BODY rather than a camera -- the
  Assisted, Forces, Walking and Driving models, Aerobatic, Ground
  contact, wall collision, head bob, the HUD -- moved to GeoPilot, a
  Geometry COMP that flies anything with the same mapping, pages and
  measured numbers (verified there: 0-to-15 in Accelerate seconds, turn
  radius 6.000, jump apex to 0.04 percent). This component keeps the
  camera-authoring kit -- free flight, orbit, Look At, picking, zoom,
  viewport mode, roll, turbulence, the sequencer -- and works with a
  GeoPilot two ways: wire it under one (rigid coupling; the pilot's
  HeadExt drives the free head, chase spring and bob), or point Source
  CHOP at the pilot's head bus and map by channel NAME with nothing to
  learn.
- SURFACE COLLISION replaces Wall Collision and generalises it: the
  probe fires along the direction of travel, so floors and ceilings
  collide the same way walls always did, with the same perpendicular
  stand-off and the same slide. Flown motion only -- preset recalls,
  Teleport and a hand on the pars are sovereign.
- Turbulence stayed (it is shot dressing, not physics), moved to the
  Control page, and no longer needs a flight model switched on.
- Roll stayed too, as the dutch tilt it always was; the BANK of a
  moving body -- bank-into-turns, bank-steer -- is GeoPilot's now, and
  a camera wired under a banking pilot composits the two through the
  wire, which is a shot the single-rz world could not make.
- The Surface Collision parameters are ensured from code via the shared
  parensure module rather than authored by hand -- values and modes of
  existing parameters are never touched by the ensure.

1.16.0 (2026-08)
- A driving simulator, as a fifth Flight Model, on a new Driving page. Two
  handling models under one menu -- Arcade goes where it points, Grip gives
  the tyres a finite hold -- and two views, the driver's seat or a chase
  camera on a spring. Forward is throttle and brake, Strafe is the steering
  wheel, and Yaw and Pitch become the driver's HEAD: a walker's facing and
  heading are one thing, a driver's are two, so the heading is carried
  separately and the head is an offset on top of it that returns to the road
  when you let go.
- Measured rather than felt: 0 to Top Speed in exactly Accelerate seconds
  (0.0000 percent error), and a stated Turn Radius of 6.0 traced at 6.000 --
  both identical at 30, 60 and 120 fps. Grip understeers a 6.0 corner out to
  6.996 rather than sliding on rails.
- Grip carries the slip as an ANGLE, not as a lateral velocity. The velocity
  version ran away: at 15 u/s round a 6-unit corner a turn adds about 0.65 of
  lateral per frame while 4 units of grip take back 0.067, which reached 90
  u/s sideways on a car doing 15 and still read 3.5 after it had stopped. An
  angle is bounded by the geometry, decays on the grip the corner is not
  using, and is zero at rest by construction.
- Changing View is eased on Chase Lag rather than switched. Mode Blend could
  not do it -- its key is the steering mode and does not change when the view
  does -- so a Chase to In-Car move that was a 6.5-unit jump now has a worst
  frame of 0.30, with no new parameter for it.
- A preset recall, a Teleport or a hand on tx beats the car. The model carries
  its own position, which without a guard means the car drags the camera back
  on the next frame; a jump past two units is now taken as somebody else's and
  the car takes up the pose it finds. This component is a sequencer first.
- Picking Driving arms Stick to Ground, as Walking does, and raises Slope
  Align to 1 when it is still at its walking default of 0 -- a walking camera
  that leans on a hill reads as a vehicle, which is precisely the point here.
  A Slope Align you set yourself is never overwritten.
- Head bob stands down while driving. A car has suspension, not a gait.
- Three bugs fixed on the way, none of them new to this release:
  Walking's viewport guard read CamSeqExt's viewport off the COMP rather than
  through _seq, so it always saw None and disagreed with the force model's --
  the seventh instance of the trap 1.13.0 named and fixed six of, and by
  measurement the last one left in either extension; _flyWalk's docstring and
  this file have both said since 1.12.0 that
  Zoom does nothing on foot while the code went on passing it through; and
  _clearIdleStatus only ever cleared Dynstatus, so switching off Walking left
  ' 0.00 u/s standing' sitting on the page. Also corrected: the Forces
  docstring claimed Strafe and Rise were ignored in all three stick layouts,
  when GTA puts the throttle on Rise and rolls with Strafe and Turn Stick
  Rolls makes Strafe the rudder.

1.13.1 (2026-08)
- Walking cannot fall through the ground. Landing was a proximity test --
  within Snap Distance -- which is a window a fast frame steps clean over,
  and once under the floor the downward probe could no longer see the
  surface it had gone through. At the defaults a single 0.1-second hitch
  after a quarter-second of falling was enough. The probe now spans the
  frame's motion, landing is a crossing rather than a proximity while
  descending, and a crossing puts the eye on the surface instead of easing
  up out of an integration overshoot. Drops of 20 to 2000 units, at 60 and
  30 fps and with 0.1-second hitches, all land, and the eye never goes
  below the floor. No new parameters.
- A backstop for a camera that ends up under a surface by some other route
  -- a preset recall, a Teleport, a hand on ty: while walking, if nothing
  is found below AND you are under a floor you were recently standing on,
  it looks again from that remembered height. The memory is the guard;
  without it, stepping off the edge of the world would stop being a fall.

1.13.0 (2026-08)
- The promoted surface went from 47 names to 11. What stays is generic verbs
  with no parameter equivalent; what moved to .ext.CamJoyExt / .ext.CamSeqExt
  is anything a pulse already does, anything opinionated about this HUD, and
  the internal callbacks and state properties. See PYTHON API.
- Migrated in three passes so the extension was never half-renamed while it
  hot-reloaded: rename with capitalised aliases kept, rewrite all 118 call
  sites, then drop the aliases. 94 of those were parameter ENABLE
  expressions, which a normal expression search does not see.
- Two traps worth naming. CamJoyExt reached CamSeqExt's Viewport through the
  COMP six times, and a demoted name read off the COMP does not raise -- it
  answers None, and the viewport branch would have quietly disappeared; it
  now goes through a guarded _seq() helper. And .Source appears both as a
  demoted property and as a real custom parameter, so the rewrite had to
  leave me.par.Source alone.

1.12.0 (2026-08)
- A walking simulator, as a fourth Flight Model. Walk, sprint, crouch and
  jump, on a new Walking page. Forward and Strafe run on the ground plane
  rather than along the gaze, so looking down does not walk you into the
  floor; Yaw and Pitch look about as freely as they do in free flight;
  Rise and Zoom do nothing, because levitating is not something feet do.
- Jump is specified by height and rise time, not by gravity. Those two
  numbers fully determine the arc, and a third would only have to agree
  with them -- and would have wanted a World Scale from another page to
  mean anything, which is the trap the energy model left behind. Measured
  to within 0.04 percent of Jump Height, identically at 30, 60 and 120 fps.
- Optional wall collision, with a slide. One ray along the direction of
  travel, from a proxy render like the ground probe, bypassed unless you
  are walking with it switched on. Stand-off is measured perpendicular to
  the surface rather than along the ray -- clamping on ray distance let a
  diagonal approach close to 0.35 of a wall while Stand-off said 0.4 -- and
  the velocity is projected as well as the step, or you go on accelerating
  into the wall and shoot sideways the moment you clear it.
- Jump, Crouch and Sprint are learnable like every other control, on the
  Mapping page. Crouch is Hold or Toggle.
- The Ground page is now purely CONTACT and the Walking page is
  LOCOMOTION. Keeping them apart is deliberate: the ground stays a layer
  under every model, so a camera can still follow terrain while orbiting a
  subject with no walking model in sight. Head Bob moved to Walking, being
  locomotion, but still applies under any model while you are grounded.

1.11.0 (2026-08)
- One Flight Model menu on the Control page -- Off, Assisted, Forces -- in
  place of Airplane Feel, Energy Model and Force Flight Model. They were
  always mutually exclusive; a menu cannot be in two states, so the rule
  stops being something the code enforces behind your back and becomes the
  shape of the parameter. The Flight page is now Assisted and the Dynamics
  page is Forces, so the pages are named after the menu that picks them.
- The energy model is retired and the Physics page with it. The force model
  does everything it did -- gravity as a vector, lift going with the square
  of speed, the nose settling onto the path, the stall -- from the forces
  themselves rather than from angles, so keeping both meant two ways to
  describe one aircraft in two sets of units: Physics asked for an engine in
  SECONDS, Forces asks in force. Airframe presets went with it; the Forces
  page has its own three, on its own axis (Arcade / Standard / Sim).
- Parameters that do nothing now grey out. Under Forces the whole Assisted
  page greys; under Aerobatic the eleven upright assists that already stood
  down in code grey too; the Ground page finally gates on the ground, which
  1.8.0 missed. Sixteen Assisted parameters used to sit lit and editable
  while the force model ignored every one of them.
- World Scale is reachable again. It was gated on the Physics toggle, which
  the force model switched OFF -- so the one parameter scaling gravity to
  your scene was unreachable in exactly the configuration that read it. It
  lives on the Forces page now, beside its only reader.
- The status readouts stopped contradicting each other. Each model wrote its
  own line and simply stopped writing when switched off, leaving the last
  thing it said on the page: a camera flying on forces displayed 'Mushing --
  20.6 under flying speed' beside a Physics toggle that was off. There is
  one Flying line, the model that is flying keeps its own, and the rest are
  blanked. If a Look At or an orbit stands the force model down, the page
  says so instead of showing an airspeed it is no longer computing.
- Control Smoothing moved to the Control page and answers to no flight
  model. It is input filtering, like Dead Zone beside it, and it was behind
  the flight toggle only because it was born on that page.
- The Control page split in two. It had grown to 70 parameters, 46 of them
  a + channel, a - channel and a Learn pulse for each of seventeen actions
  -- plumbing you set once and never look at again, filed with the speeds
  and modes you touch constantly. Mapping is which control is which;
  Control is what the camera does. Nothing was renamed and no mapping is
  lost, and the pages are ordered Control, Mapping, Assisted, Forces,
  Ground now, with Callbacks and About at the end where they belong.

1.10.0 (2026-08)
- A second flight model, on a new Dynamics page, off by default. It carries
  angular velocity and a velocity vector as state and adds up thrust, lift,
  drag and weight; banked turns, the spiral, the stall and inverted flight
  come out of that rather than being written as formulas. Measured against
  g tan(phi) / v -- which appears nowhere in it -- the turn is within 0.034
  percent at 20, 40 and 60 degrees of bank, and a loop conserves energy to
  0.20 percent.
- Nothing on the Fly, Flight or Physics pages changed. With the switch off
  every measured behaviour is identical: bank-steer 4.7163 deg/s at 40
  degrees, pitch clamping at 89.0, the airbrake taking 100 m/s to 17.12
  airborne and 4.08 on the ground, and an Aerobatic loop returning exactly.
- Exactly one model writes the pose. Force Flight Model, Energy Model and
  Glide switch each other off, and with the force model on the old model's
  two writers ran 0 times in 60 frames -- checked by instrumentation, not by
  reading the code. Two writers on one value caused the levelled roll, the
  spiral and back-stick commanding full throttle.
- Trim, so letting go leaves it flying rather than falling. Weathervaning
  towards zero angle of attack meant the wing made no lift hands-off and the
  aircraft descended at a third of g; it now settles at a trim angle and
  therefore holds height at one speed, climbs above it and sinks below.
- Ground Stick works with it: taxi, rotate, lift off when lift beats weight,
  and be caught again on landing -- one clean transition at 75 m/s, no bounce.
- Stick Layout, defaulting to GTA: triggers for throttle and airbrake, left
  stick to fly, right stick for rudder. A controller mapped for the other
  model arrives here with its turn control wired to the rudder, which cannot
  turn an aeroplane -- full rudder for four seconds moves the heading 0.02
  degrees. Buttons are untouched, so Orbit and Look At stay put, and Rise
  Detach is ignored while the force model flies, since Rise is now the
  throttle and would otherwise lift the aircraft off at zero knots.
- Wings Level, because the bare airframe spirals -- a hands-off 30-degree bank
  wound itself to 58 in four seconds. Real aircraft get this from dihedral,
  which needs a side force this model has none of, so it is supplied directly
  and fades out as you feed in roll.
- Turn Hold became Level Hold, twice over. It was a feedback term chasing the
  sag and did nothing measurable -- 0 to 1 changed the sink in a 40-degree
  bank by 0.9 m in four seconds -- so it was fed forward into the trim angle
  instead: 22.8 m of sink became 11.6 and the rate went 3.59 to 4.51 deg/s
  against an ideal 4.72. Then it turned out that commanding one g HOLDS a
  climb angle rather than removing it, so holding the throttle still climbed
  away. It now also asks for the acceleration that nulls the climb rate, over
  a two-second time constant.
- Thrust, Drag and Trim repaired across all three presets. Each airframe keeps
  the top speed it had, at half the thrust-to-weight, and Trim is now the
  angle that holds level flight at that speed. Before: full throttle and
  nothing else flew a complete loop in seventeen seconds. After: Arcade
  settles at 84 m/s climbing 1.6 m/s, Standard at 100 m/s climbing 1.8.

1.9.0 (2026-08)
- Aerobatic mode. The camera turns in its OWN frame with no pitch limit,
  so it loops and rolls continuously instead of stopping at 89 degrees.
  Measured: a full loop returns to within 0.333 degrees of where it
  started, a full roll to 0.000, with no frame step larger than the
  configured turn rate.
- Presets are unaffected. Orientation is written back to rx/ry/rz every
  frame, and a preset recorded mid-loop reproduces the orientation at
  dot 0.999999. The slerp recall path is not touched at all.
- The upright assists stand down while it is on -- Bank Into Turns,
  Auto-Level Roll, Level Pitch, pitch trim and bank steer. Level means
  nothing inverted, and a camera upside down should not have its horizon
  quietly corrected.
- With Aerobatic off nothing changes: pitch still clamps at 89 and a
  40-degree bank still steers at 4.72 deg/s.

1.8.0 (2026-08)
- An airbrake. Back-stick used to command FULL THROTTLE -- the throttle
  read the magnitude of a signed axis -- so the only way to slow down
  was to centre the stick and wait out Coast Time, and on a runway
  nothing slowed you at all. Pulling back now asks for no speed and
  shortens the time constant to Brake Time in proportion to how far you
  pull. You still cannot brake to nothing in the air: braking sinks you,
  and sinking hands altitude back as speed.
- Roll Level Time sits with Roll Response, where it belongs -- the pair
  is the roll in and the roll out -- and finally has an enable
  expression. It was the only dependent slider on the Flight page
  without one, so it never greyed out to contradict its placement under
  Auto-Level Roll, which does not own it.
- The whole Physics page is gated too: nothing on it had an enable
  expression either. It greys out with the Energy Model off, apart from
  the status line, which has to stay readable to say why it is idle.
- Bank Steers is bounded to a level turn. Clamped at 80 degrees it fed
  tan 5.67, three times the turn a 60-degree bank earns, and past 90 the
  tangent flips sign -- so a held roll yawed one way, reversed and came
  back. It now stops at 60 and stands down past 90, where there is no
  level turn to compute and a roll is simply a roll.

1.7.0 (2026-08)
- Pitch trim: the nose follows the flight path. Gravity bent the
  trajectory down and nothing bent the nose after it, so letting go gave
  a flat descent -- the aircraft sank while still pointing at the
  horizon. It aims at path + Trim Angle, and that offset is what keeps
  it stable: aimed straight down its own path an aircraft has nothing
  left to lift with.
- Trim Angle became the CAP rather than a fixed offset. The angle the
  wing takes is the one it NEEDS at the current speed -- 3 degrees at
  full throttle, 5 at half, 11 with it closed -- instead of parking the
  nose 12 degrees up in cruise for ever.
- Airframe presets: Arcade, Trainer, Airliner, Jet, Glider. Ten numbers
  across three pages, loaded on a pulse so tuning is never wiped by a
  glance at the menu.
- A HUD. Numeric readout first, then the glass: an attitude ladder that
  pitches and banks, speed and altitude tapes, a heading ribbon,
  boresight and carets. Flaps, gear and yoke are deliberately absent --
  nothing models them, and instruments for state that does not exist are
  a lie on the glass.
- Throttle is the FORWARD axis. It was the length of the whole movement
  vector, so Rise and Strafe counted as thrust and a trigger on Rise had
  to be held alongside the stick to reach full speed.
- Control authority reads AIRSPEED, not the throttle stick. The test
  only trusted carried velocity under Glide, and Glide is off whenever
  the energy model is on -- so flying fast with the throttle closed cut
  yaw, pitch and roll to the floor, which is how "I cannot roll" began.
- Grounded pitch eases to level: landing off a nose-down glide used to
  leave the aircraft parked staring into the tarmac.

1.6.0 (2026-08)
- Physics page: an energy model, off by default and mutually exclusive
  with Glide. Climbing spends speed and diving buys it back, at exactly
  g sin(theta). Forward still asks for a speed, so Move Speed and every
  existing preset keep their meaning. Below Flying Speed it mushes and
  recovers itself rather than departing -- losing control is the game in
  a simulator and the failure in a set.
- Physical Turn: the coordinated turn becomes omega = g tan(bank)/speed,
  so a fast pass turns wide and a slow one turns tight with no dial.
- World Scale, because a TD unit is not a metre and 9.81 dropped straight
  into this project would fall twice as fast as the camera flies.
- A preset recall no longer fights carried momentum: a jump larger than
  the velocity can account for drops it.

1.5.0 (2026-08)
- Ground page: a walking simulator laid over the flying one, off by
  default. Stick to Ground arms it and the ground then owns the
  camera's height -- free flight, a Look At and an orbit all keep
  steering underneath. Three states rather than two, so stepping off a
  hill (Detach, re-attach on the way back) and turning walking off
  (the toggle) are different gestures. Eye Height, Ground Smooth for
  the bumps and the landings, Snap Distance, Rise to Detach, Max
  Slope, Slope Align. Grounded, Forward and Strafe run on the ground
  plane, so looking about never changes your pace.
- Head Bob, with Bob Stride and Bob Sway. Driven by distance covered
  rather than by a clock, so the step rate follows your speed and the
  head is still when you are.
- The ground is found by a downward orthographic proxy render picked
  at its centre, not by a Ray SOP: a ray sees only CPU-side SOP
  geometry and would miss POPs, GPU displacement and instancing.
  Costs ~0.4 ms a frame on the ground and nothing at all off it.

1.4.0 (2026-08)
- Flight page: an airplane feel for the controller, off by default and
  toggle by toggle. Control Smoothing (the sticks ramp, buttons stay
  instant), Bank Into Turns with Auto-Level Roll, an optional Bank
  Steers for a real coordinated turn, Level Pitch, Speed-Scaled
  Turning, Glide momentum and Turbulence. All the easings are
  frame-rate independent, and an idle camera costs nothing.
- Look At Pick no longer snaps the view at either end: taking a target
  swings onto it over Look At Capture seconds, and releasing one keeps
  the aim you had instead of jumping back to stale rotation values.
- Fixed: the Roll, Roll Modifier and Level Horizon learn buttons did
  nothing -- the Control page's parameter filter never reached them.
- Fixed: Strafe and Rise did nothing during a held Orbit, so that mode
  was flown on one stick while every other mode used two. They now swing
  you round the pivot at a fixed distance, exactly as Yaw and Pitch do --
  on a sphere those are the only moves there are, so the left stick can
  only be another way of making them. (They used to carry the pivot
  along instead, which quietly walked the orbit centre off whatever you
  were orbiting.) Note the two sticks swing opposite ways, each true to
  its own convention: left moves, right looks.
- Fixed: Look At Pick appeared to grab the same target no matter what
  was in front of you. The pick was right; the AIM was not. TD's Look At
  points at a COMP's origin, and geometry moved by a transform SOP
  leaves that origin behind -- both objects here sit at (0,0,0) while
  what they draw is 1.8 and 2.5 units away, so either pick aimed the
- Fly Mode = Orbit now requires something to orbit -- a Look At target
  or the viewport pivot -- and otherwise flies free, with a new Flying
  readout saying which. It used to orbit an invisible point Orbit
  Distance ahead, which drifted with wherever you faced; and dollying
  in that mode wrote the shrinking distance back to the parameter every
  frame until it reached 0.05, at which point the pivot sat inside the
  lens and orbiting was spinning on the spot. That distance now stops
  at 0.5.
- Fixed: the controller composed rotations in xyz order regardless of
  the camera's own Rotate Order -- which Roll switches to Rz Rx Ry. Any
  roll then made its idea of "forward" disagree with the one TD renders
  (at 30 degrees of roll, forward was out by 0.4 in Y), so flying went
  slightly sideways and the orbit loop, which places its pivot along
  forward, fed that error back on itself and wandered.
- Fixed: flying with a Look At set was not free. Movement was taken
  from the gaze, and a gaze locked to a target makes "forward" mean
  "towards the target" -- an attractor rather than a direction. Held
  against Strafe it settled at a fixed distance and decayed to 0.00001
  units a frame after five seconds, against 0.118 in free flight; with
  the clamp lifted it flew through the subject and carried on away.
  The camera now keeps a heading of its own while the lens stays on the
  subject -- a drone with a gimbal. Every axis moves you at free-flight
  speed in a straight line.
- Fixed: with the aim locked, steering the heading showed nothing on
  screen -- so a turn made while parked was a change you could not see
  and only met later, when the next nudge of the left stick sent you
  somewhere unexpected. With a subject, the right stick now works ON it
  instead: Yaw takes you round it at the radius you are already at
  (5.049 held to three decimals through a full 180 degrees, and the
  heading carried with it, so forward from there still travels its full
  10 units rather than stalling), and Pitch reels you in and out -- one
  second closes 5.049 to the 0.05 floor or opens it to 10.069, and
  holding it at the floor stays there rather than passing through.
  Up and down is left to Rise, which already did it on the stick you fly
  with. Arcing over the top at a fixed radius is now the Orbit button's
  job alone: Rise is a translation and grows the distance as it lifts
  you, 5.049 to 6.608 in a second.
  With no subject to work on, the sticks go back to steering the
  heading, and only while you are moving.
- Fixed: preset-driven Look At targets aimed at each object's COMP
  origin too, for the same reason -- so a preset pointed at an object
  moved by a transform SOP looked past it. The blend now reads the
  targets' live geometry through two Constant CHOPs inside the
  component.
- Fixed: Look At Pick's tether was swallowed by Targets mode the moment
  it landed (adopted as the preset's target, then overwritten on the
  next Select change), which is why the swing looked right and the
  landing did not. A pick now owns the aim until released.
- Fixed: Look At Pick appeared to grab the same target no matter what
  was in front of you. It now aims through a small docked null
  at the exact point you picked, carried with the object's live geometry,
  so it tracks whether the object is moved by its COMP, by a SOP, or
  deformed -- and taking a target no longer shifts your framing.
- Mode Blend: changing between free flight, a Look At and an orbit used
  to swap your motion on a single frame -- sweeping around a subject
  became spinning on the spot instantly. The movement now eases from one
  into the other, so leaving a Look At is as gentle as taking one (until
  now only taking one was eased at all).
- Fixed: with a Look At (or an orbit) holding the aim, Strafe traced a
  circle around the subject instead of a line past it -- a second of it
  from 5 units away came back at 5.08 units, 57 degrees round. The
  strafe direction is now taken at the start of a stroke and held, so
  you walk straight and the head turns to follow. Free flight is
  unchanged: there the view only turns because you turned it.
- Fixed: with a Look At set, a held Orbit ignored the point you picked
  and went back to having no pan -- so whether Strafe did anything
  depended on which preset happened to be tethered. An Orbit press now
  owns the pivot either way; the Look At still only fixes the aim.
- Fixed: Rise moved along the camera's up while orbiting and world up
  everywhere else -- it is world up in both now, so looking steeply
  down no longer turns "rise" into a sideways slide.

1.3.2 (2026-08)
- Roll on the Control page: bank the camera with a spare axis (the
  bumpers are the natural pair), or map Roll onto a control you already
  use and gate it with a Roll Modifier button -- held, that control
  banks and its usual job is suppressed. Roll Speed sets the rate and
  Level Horizon takes the bank back out.
  The first roll switches the camera's Rotate Order to Rz Rx Ry so roll
  turns about the view axis instead of swinging the aim -- a no-op for
  every preset made before it. Normal mode only.

1.3.1 (2026-08)
- Look At Mode: Targets -- a Look At OBJECT per camera preset. Set Look
  At Target, Append; the aim glides between the presets' objects with
  the transition's easing and follows them live (Object CHOP pair +
  easeInterpolator). The transform Look At sequencer is unchanged.

1.3.0 (2026-08)
- Control page: fly the camera from a joystick / gamepad / any CHOP.
  Learn-mapped controls (move it to map it), so any pad layout works;
  axes are a stick or a pair of one-way controls (triggers, bumpers),
  with per-control resting values. Free-fly or Orbit, pivot-aware, in
  normal and viewport mode; Zoom drives FOV / focal length / ortho width
  as the projection dictates; Reset Pivot.
- Picking through the Render TOP: hold Orbit to tumble around what you
  are looking at, Look At Pick to tether the aim to the object hit,
  Teleport to jump there, Collision to stop short of it.
- Sequencer from the same pad: Next, Prev, Capture, preset buttons and a
  rate-mode Scrub axis.

1.2.0 (2026-08)
- Viewport mode: sequence a palette cameraViewport (drop inside one, or
  set Camera Viewport). Position, rotation, tumble pivot and FOV are
  recorded; quaternion rotation blend applies. Follow Viewport renders
  the viewport's view through this camera.
- Viewport mode has its own Viewport Presets table; Camera Presets are
  never touched by a mode switch.
- An empty Look At no longer raises a warning on the Look At sequencer.

1.1 (2026-08)
- Mix: blend EVERY camera preset at once by weight from a CHOP, not
  just scrub between two. The aim follows the two heaviest presets.
- The Spline and AnyToAny toggles are gone, replaced by one Mode menu
  (Select / A to B / Spline / Mix). BREAKING: anything referencing
  par.Spline or par.Anytoany needs par.Playmode instead.
- Rotation Blend on the Seq page drives both inner sequencers:
  quaternion blending along the shortest arc, optional winding.
- Single angle parameters (roll, a lone axis) take the shortest arc too.
- Camera Presets / Look At Presets can live beside this component
  (Create) instead of inside it.
- Every Seq-page control now really reaches both inner sequencers
  (Override, Easing and the playback Mode were not linked before).
- Lists show 0-based indexes matching Select; drag-reorder works.
- Prune Stale Columns and RestorePresets() on the inner sequencers.
