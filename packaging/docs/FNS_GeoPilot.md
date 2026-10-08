---
package: FNS_GeoPilot
summary: 'A Geometry COMP that moves itself: map a game controller, the keyboard or any CHOP and it flies, walks or drives, from a stunt plane to a person on foot, with ground contact and a preset sequencer for its poses.'
features:
  - name: Which knob do I touch (the chain, top to bottom)
    anchor: which-knob-do-i-touch-the-chain-top-to-bottom
  - name: Coming from CamSequencer (read this first)
    anchor: coming-from-camsequencer-read-this-first
  - name: Quick start
    anchor: quick-start
  - name: Coupling (Coupling page)
    anchor: coupling-coupling-page
  - name: The buses
    anchor: the-buses
  - name: Presets (Presets page)
    anchor: presets-presets-page
  - name: Preset dropdowns
    anchor: preset-dropdowns
  - name: Mapping (Mapping page)
    anchor: mapping-mapping-page
  - name: The model pages
    anchor: the-model-pages
  - name: Assisted page
    anchor: assisted-page
  - name: 'Ground page (contact: standing on things)'
    anchor: ground-page-contact-standing-on-things
  - name: Walking page (first person on foot)
    anchor: walking-page-first-person-on-foot
  - name: Driving page (a car)
    anchor: driving-page-a-car
  - name: Forces page (force flight model)
    anchor: forces-page-force-flight-model
  - name: 'What''s new'
    anchor: whats-new
---

A Geometry COMP that flies itself: a game controller (or any CHOP) is
mapped by learning, and the component's OWN transform becomes a drone,
an aircraft, a person on foot or a car. Born at the GeoPilot split from
camSequencer 1.15, whose flight models grew up flying a camera and
turned out to be bodies all along -- the models here carry the same
pages, the same parameters and the same measured numbers, retargeted
from a camera's pose to this component's.

Parent your rendered geometry inside it (it IS a Geo COMP) or wire
your model underneath it, put a camera on it two ways (see COUPLING),
and sequence the body with the inner OpSequencer (see PRESETS).


## Which knob do I touch (the chain, top to bottom)
The Pilot page reads top-down, and each level only writes the ones
below it:

  Body Preset     a whole vehicle (Pilot page). Sets everything below
   + Apply Body   in one pulse, plus speeds, eye height and chase.
                  Each entry says what it is: stuntplane (Flight,
                  Forces), person (Walking). The menu is only a
                  picker; Current Body shows what was actually
                  applied, and adds (modified) once you change any
                  value it wrote.
  Flight Model    what the body IS: Off, Flight, Walking, Driving.
  Flight Physics  under Flight only: which physics, and so which page
                  tunes it -- Assisted (Flight page), Forces (Forces
                  page), Helicopter (Rotor page).
  page Preset     each model page has its own Preset menu and Apply,
   + Apply        writing that page only (a Forces feel, a walker, a
                  car). Pages that are not in use grey out, their
                  Preset menus included.

So: pick a Body for a ready vehicle; or set Flight Model (and Flight
Physics) yourself and load a page Preset; then tune the page.

A realistic aeroplane -- banked turns, energy, stalls -- is Forces:
Body Preset stuntplane, or Flight Model Flight, Flight Physics Forces
and a Forces Preset (sim or corsair for the real thing, standard for a
jet, arcade forgiving). Assisted banks too, but the bank is cosmetic:
the angles are chosen and eased toward, which is what a camera move
often wants.


## Coming from CamSequencer (read this first)
If you used camSequencer before its 2.0 split, one camera did everything:
it walked, flew and drove, and its transform WAS where you were. Now
that work is split in two, and a few things behave differently:

- GeoPilot is the BODY: walking, driving, flight physics, ground contact
  (Stick to Ground / Detach), jumping. camSequencer is the HEAD and LENS:
  looking about, zoom, Look At, and its own sequencer.
- The camera is a CHILD of the pilot. Wiring camSequencer under GeoPilot
  (object connectors) parents it, and in TouchDesigner a child's
  Translate / Rotate are measured from its parent, not from the world.
  So the camera's tx / ty / tz no longer say where you are; they say how
  far the camera sits from the body ("5 units in front of me"). When the
  body walks, the camera goes along and its own numbers do not change.
- That is why camera presets taken at different places come out
  IDENTICAL: they store the look relative to the body, and only the body
  moved. Where you stood goes in the BODY's presets (OpSeq_body), not the
  camera's.
- Record both at once with the mapped Capture button (Capture Body Preset
  on, the default): one press appends a body row and a camera row, in
  step. Replay both from one playhead with Select Sync (Presets page).
  Init / Append / Remove on only ONE of the two sequencers puts them out
  of step -- row N of one stops matching row N of the other.
- Pick the coupling that matches what you expect (Coupling page):
    Free    moving the camera moves it RELATIVE to the body (an offset,
            e.g. over the shoulder); the body stays put.
    Carry   moving the camera moves the BODY there instead; the camera's
            tx / ty / tz / ry hand over and return to 0.
  Rigid and Chase are for a plain camera: with a camSequencer on, use
  Free or Carry, so the pilot's head and camSequencer do not both write
  the camera's rotation. Rigid or Chase with a camSequencer on shows a
  warning in Head status instead of turning the head, and Head Return /
  Head Limit grey out under Free and Carry, where they do nothing. The
  camSequencer greys out its own controls that the pilot owns (its
  layouts, move channels and speeds, collisions, Dead Zone, Smoothing).
- The Pilot page's "Capture Preset" pulse is NOT the spot recorder: it
  saves a vehicle preset (Person, City Car...). Spots are Capture (the
  mapped button) or Append on OpSeq_body.
- Control Preset layouts carry the sequencer buttons too (1.6.0): the
  Keyboard layout records with R and steps with Z / X; the Xbox,
  DualShock and Generic layouts put Capture on a face button and Next /
  Prev on Back/Start, Share/Options and the shoulders (pad button numbers
  vary by driver -- Learn one if it is wrong; 8BitDo has none). Loading a
  pad layout over the keyboard switches Source back to the controller.
  Keyboard Panel (Mapping page) makes keys count only while a panel has
  focus, the palette cameraViewport's way: by default the pilot's own
  node viewer, a panel showing the carried camera's render. Click into
  the node to drive.
- camSequencer 3.0 and older ignored the BUTTONS of any external Source
  CHOP (a GeoPilot head bus, MIDI, OSC): Capture / Next / Prev never
  reached it. Fixed in the next FNSTools release; axes were never
  affected.


## Quick start
1. Plug in a game controller and map it on the Mapping page: press
   Learn Forward, move the stick, and so on -- the same learn protocol
   as camSequencer and one mapping serves everything below.
2. Pick a Body Preset and pulse Apply Body, or pick a Flight Model on
   the Pilot page yourself -- it says what the body IS (see WHICH KNOB
   DO I TOUCH):
   Off is a tripod on rails, Flight is an aircraft (Flight Physics
   right under it chooses the assisted angle model, the force model or
   the rotor, the way Driving chooses Arcade or Grip under Handling),
   Walking is a
   person (arms Stick to Ground), Driving is a car (throttle on
   Forward, the WHEEL on Strafe, arms the ground and leans with the
   road).
3. Wire a Camera COMP under this component (object connectors, top of
   the camera to the bottom of this) -- that is the whole rigid
   coupling. Under Driving and Walking the head is free: Yaw/Pitch
   ride the head bus and the pilot's HeadExt looks about while the
   body goes where it is pointed.
4. Fly somewhere, press Append on the inner sequencer (Presets page ->
   Pilotpresets Create makes the external table). Recall composes with
   whatever a coupled camera is doing.


## Coupling (Coupling page)
The camera is never INSIDE this component; it couples by wire or by
reference, and the coupling is a spectrum:

  Rigid (in-car)   wire the camera under this COMP -- the wire is the
                   setup. TD composits the transforms natively; the
                   pilot's HeadExt writes only the camera's LOCAL
                   rotation: the free head, integrated from the head
                   bus, with Head Limit and (under Driving) Head
                   Return easing a released head back to the road.
                   Head bob rides here too, distance-driven off the
                   state bus.
  Chase (spring)   the camera trails the body, looking up the road
                   past it -- camSequencer's chase view made
                   model-agnostic: chase a walker, chase the plane.
                   Chase Distance / Height / Lag / Aim, and the
                   In-Car <-> Chase change is a MIX eased on Chase
                   Lag, never a switch (worst measured frame: 4.75
                   percent of the offset).
  Aim Only         the camera stays put and its Look At is pointed at
                   this body: a tripod panning to follow the car.
  Free             no relationship. Pick this when a camSequencer is
                   wired on: it drives its own head with its full
                   authoring kit, and the wire alone carries the body.
  Carry            Free, plus the camera CARRIES the body (1.5.0):
                   move the wired camera -- drag it, type a value, fly
                   it -- and the body goes there instead. Position and
                   heading are handed over every frame and the camera
                   goes back to zero on the body; pitch, roll and lens
                   stay on the camera. A grounded body lands on the
                   ground at the new spot (probed from above, so a big
                   step uphill does not end inside the hill). Camera
                   presets then hold the look and lens only; where you
                   stood lives in the body presets. The natural pick for
                   a camSequencer on a walker.

The Camera parameter is the reference route for rigs a wire cannot
express; when both are present the parameter wins.

With a camSequencer riding the body, point its Source CHOP at this
component's null_headbus and type the channel names into its Mapping
page -- Yaw, Pitch, Roll, Zoom, Scrub, Capture, Next, Prev -- and it
is mapped with nothing to learn. Its presets then live in the BODY's
frame: "over the left shoulder" composes with wherever the body went.


## The buses
null_headbus   what the body does NOT consume, published per model and
               already normalised, dead-zoned, smoothed and
               roll-gated: Driving frees Yaw/Pitch/Roll (the driver's
               head), Walking frees Pitch/Roll (the eyes; feet follow
               the facing -- the FPS convention), Zoom and Scrub
               always ride (the body has no lens and no playhead),
               and Capture/Next/Prev pulse for whatever sequencer
               listens.
null_statebus  what the body is DOING: speed, grounded, airborne,
               bank, model index. HUDs, engine audio, camera shake --
               anything in your network can react to the body without
               a line of Python coupling.


## Presets (Presets page)
The body's memory is an ordinary OpSequencer (OpSeq_body) pointed at
this component's transform -- everything in opSequencer's README
applies: easing, per-parameter overrides, Spline, Mix, the lot.
Pilotpresets + Create is the same external-table pattern as
camSequencer's: Create clones the table beside this component
(relocatable, externalizable, git-friendly) and the inner sequencer
follows the parameter.

Each pilot owns its preset LIBRARIES (forces, rotor, assisted, walker,
car, layout, body): every <Kind>presets_RepoMaker's Owner is the
expression parent(), never a path. Before 1.6.0 the shared geoPilot1.tox
carried Owner as the constant '/geoPilot6', so every pilot loaded from it
read -- and captured into -- geoPilot6's tables; init now puts the
expression back whenever the mode has drifted.

Recalls are SOVEREIGN. A preset recall, or a hand on the transform,
beats every model: a jump larger than the motion could explain drops
the carried momentum and the model takes up the pose it finds -- the
car adopts the recalled heading and drives on. This is a rig for
sequencers before it is a simulator.

AUTHORING TOGETHER  (1.1.0)
Body and look stay separate tables on purpose -- a local look preset
composes with wherever the body went. Two opt-in wires join them when
you want the whole shot in one gesture:

Capture Body Preset   on by default: the mapped Capture button appends
         a BODY preset in the same press that pulses Capture on the
         head bus -- so a coupled camSequencer (listening on the bus)
         and the body table grow together, indices in step. Turn it
         off for a pad that drives the camera sequencer alone.
Select Sync           off by default: BINDS the body sequencer's
         Select to the coupled head's Select (the Camera par, else the
         wired camera). One playhead recalls the whole shot -- scrub
         either and both move, fractional blends included -- and
         switching it off hands the body its own playhead back where
         it stood. Toggle it again after changing the coupled camera
         to re-aim the bind. Leave it off to cut the camera between
         looks while the body keeps driving its own path.


## Preset dropdowns
Plain menus, applied by a pulse -- never by the menu itself, so
glancing at a list cannot wipe numbers you tuned (the Forces page set
the convention).

Body Preset  (Pilot page)  a whole vehicle in one pulse: the Flight
Model and Flight Physics, its page preset, and the cross-page dressing
(speeds, eye height, chase) that makes it read as a body. Each entry
is labelled with what it is -- airliner (Flight, Assisted) is not the
same kind of aeroplane as stuntplane (Flight, Forces). Current Body,
right under it, is the readout: the body last applied, (modified)
once a value it wrote changes, custom when none was. Apply Body reads
the Body library table, so a row you add there applies too. Sixteen of them:
FPV Drone, Cinema Drone, Helicopter, Heavy Helicopter, Airliner, Stunt Plane, Spaceship,
City Car, Sports Car, Drift Car, Semi Truck, Go-Kart, Person, FPS
Hero, Astronaut, Giant. The Flight/angles family is the whole
hover-and-reaction-craft space: the helicopter banks into its slide
and settles back to hover attitude, and the spaceship is Aerobatic
with every upright assist down and a LONG coast -- no horizon, no
stall, thrust and attitude only (Glide decays on its time constant,
so it approximates vacuum coasting rather than being truly
Newtonian).
Every number is reasoned -- the truck takes fourteen seconds to speed
and most of a second to wind its wheel, the astronaut jumps a TRUE
parabola (floating at the top is the point), the kart's eye sits at
bumper height because that is most of why karts read fast.

Preset  (Assisted / Walking / Driving pages)  the same vehicles'
page-scoped halves, for when you want the car without its chase
dressing or the walker without its eye height. Only that page is
written. The Forces page keeps its own Arcade / Standard / Sim.

Control Preset  (top of the Mapping page)  a whole controller layout in one
pulse: Xbox Pad, DualShock Pad, 8BitDo, GTA Heli, Generic Pad, or
Keyboard (WASD + arrows: QE rises, Space jumps, LShift sprints, C
crouches, F drifts, R captures, Z / X step back and forth).
Applying clears the previous mapping so layouts never merge. The
keyboard targets the internal Keyboard In CHOP and is exact, and its
Keys list grows to whatever the layout names; pad axis and button names
vary by driver, so treat those as starting points -- re-learn or swap a
+/- pair if one arrives wrong.
A pad layout keeps your Source (a MIDI or OSC device stays connected),
except over a Keyboard In, which it swaps back to the controller -- a pad
loaded over the keyboard used to sit silent. The layouts are the
library table (Presets page, Layout): capture your own under a new name
and Apply loads it like a shipped one (before 1.6.0 Apply only knew the
shipped layouts). A library made before a layout gained a column (Next /
Prev in 1.6.0) gets the column on the next init, filled for the shipped
layouts only -- your own rows and edits are never touched.
To save your own: map the controller (Learn, or type channels), type a
new name into Control Preset and pulse Capture Preset; Delete Preset
removes one. A layout holds Source, Dead Zone and EVERY channel field,
so a control no shipped layout uses (Zoom, Scrub) is captured too; a
typed Source is kept as typed, so ./keyboardin_internal stays relative.
Current Layout, under it, is the readout: the layout last applied or
captured, (modified) once a channel, the Source or Dead Zone changes (a
Learn, say), custom when none was.

Keyboard Panel  where the keyboard counts, the palette cameraViewport's
way. By default it is ./renderView: a panel inside this component that
shows the render of the camera it carries. While the KEYBOARD drives
this body (Source is a Keyboard In) that panel is also its NODE VIEWER
(Node View = Operator Viewer, opviewer = me.par.Keyboardpanel.eval(),
exactly how cameraViewport shows its own panel); with a pad, MIDI, OSC
or an autopilot the usual geometry viewer stays. Node View is an
expression doing that switch; set it by hand to override. So click into the
node viewer to drive: the keys go to that panel and never to the
network editor (no geometry-viewer shortcuts) or the Textport, and
clicking outside hands them back. Point it at another panel -- the
renderView inside a camSequencer, a Container COMP, a Window COMP -- to
drive from there; the node viewer follows. Empty: keys count wherever
TouchDesigner has focus. A pilot made before this switches once to its
own renderView (flagged in storage, so a later choice is kept).
Mouse Look  drag inside the viewer panel (Keyboard Panel) to look, the
cameraViewport way: Off / Left Drag / Right Drag, Mouse Look Speed
(degrees per full viewer width), Invert Mouse X / Y (the mouse only),
Mouse Smoothing (seconds to catch up; 0 = exact, more glides and a
flick carries on after release, the total turn unchanged). Where the
drag goes:
    sideways   turns the BODY -- under Driving the driver's head instead
               (the wheel steers the car); Driving on Carry ignores it
    up / down  tilts the head: under Rigid with a plain camera through
               this component's free head (it composes with the stick
               look); otherwise straight onto the camera's rx, which is
               how a camSequencer on Free or Carry takes it
Under Chase the head is the chase rig's, so a vertical drag does
nothing there; a camSequencer has Mouse Look of its own in its viewer.
Pan and Dolly  the rest of cameraViewport's Camera navigation, moving
the BODY along its own axes (on by default): drag with the OTHER button
(right when Mouse Look is Left Drag) to strafe and rise, drag with the
middle button to move forward and back (vertical) or strafe
(horizontal), turn the wheel to move forward and back. Mouse Pan Speed
is scene units per full viewer width, Mouse Wheel Speed units per
notch; both ease through Mouse Smoothing. Walking moves on the ground
and never rises (the ground owns the height); Driving ignores it, so
the mouse never pushes the car about. The wheel is caught by
panelexec_wheel, a Panel Execute beside renderView watching the
Keyboard Panel.
Render TOP  what renderView shows. Empty: the render of the carried
camera (a camSequencer answers with its own Render TOP; any other
camera is matched to the Render TOP whose Camera it is). Set it when
that camera is rendered through something else, such as a rig that
switches between bodies.

The channel fields themselves are DROPDOWNS now (editable ones): each
lists the live source's channels, so hand-mapping is picking from what
the pad actually offers -- typing and learning both still work.


## Mapping (Mapping page)
The same learn system as camSequencer 1.15, one axis vocabulary for
every model: Forward, Strafe, Rise, Yaw, Pitch, Roll, Zoom, Scrub,
plus Capture / Next / Prev / Jump / Sprint / Crouch / Drift and the
Roll Modifier. Each axis is one bipolar stick or a pair of one-way
controls, measured from learned resting values; Dead Zone trims and
rescales; Control Smoothing gives the sticks inertia while buttons
stay instant. See camSequencer's LEARNING section for the full
protocol -- it is the same code.


### Measured
The numbers that were measured on the camera hold on the body,
re-verified at the split: Driving reaches Top Speed in exactly
Accelerate seconds (3.983 s sampled against 4.0, one frame of
quantisation) and holds 15.0 exactly; a stated Turn Radius of 6.0
traces at 6.000020; Walking's jump apex lands within 0.04 percent of
Jump Height and a fall can never pass through the floor (crossing
landings); Aerobatic round-trips a full loop at orientation dot
1.000004.


## The model pages
What follows moved here verbatim from camSequencer 1.15's README --
these pages grew up flying a camera, and the prose still says
"camera" where it means "this body": read it accordingly. Three
translation notes. Where the text says Flight Model = Assisted or
Forces, the menu now reads Flight, and FLIGHT PHYSICS (Pilot page,
under Flight Model) chooses between them -- the pages themselves (Flight, the old
Assisted; and Forces) are unchanged. Where the text speaks of a LOOK AT or an ORBIT
standing a behaviour down, that coupling belongs to the aim-anchor
phase of the split and does not exist here yet -- the free-flight
column is the one that applies. And where it speaks of the DRIVER'S
HEAD or HEAD BOB living on the camera pose, those live on the HEAD
BUS and the coupled camera now -- the body carries the car, the head
carries the eyes, and the wire composits the two.

FLIGHT MODEL  (Pilot page)
Fly Mode and Flight Model are the two halves of how the camera moves: Fly
Mode is how it is STEERED (free-fly or orbit), Flight Model is what physics
it has underneath.

Off       the sticks move the camera directly. A tripod on rails, which is
          what you want when the shot is the point.
Assisted  the Assisted page: bank into turns, a steered turn, auto-levelling,
          glide momentum, turbulence. Worked on the rotation angles.
Forces    the Forces page: thrust, drag, lift, weight and control moments.
          It owns the pose outright -- nothing on the Assisted page runs.
Walking   the Walking page: a person on foot. Walk, sprint, crouch and
          jump, with the Ground page finding the floor underneath. Owns the
          pose like Forces does, and arms Stick to Ground when you pick it.
Driving   the Driving page: a car. Throttle and brake on Forward, the
          steering wheel on Strafe, and the driver's head free on Yaw and
          Pitch. Arcade or Grip underneath, seen from the driver's seat or
          from a chase camera. Owns the pose and arms Stick to Ground too.

One menu, because only one of them can move the camera. This was three
separate toggles on three pages until 1.11.0, kept apart by code that
switched the other two off whenever you turned one on; correct, and
invisible, so the first anyone knew they were alternatives was when one
silently cleared another. There was a fourth, an energy model on a Physics
page, which the force model made redundant -- see WHAT'S NEW.

Control Smoothing   the sticks ramp in and out instead of snapping, so
  Smoothing Time    rates never start or stop dead. The single biggest
                    change to how flying feels; 0.1 is crisp, 0.4 heavy.
                    Buttons are read before the filter and stay instant.
                    Works under every Flight Model, Off included.

## Assisted page
Set Flight Model (Control page) to Assisted and the camera stops behaving
like a tripod on rails. Everything below is its own toggle, so you can take
only the parts you want, and everything greys out when another model is
flying -- including under Aerobatic, which stands the upright assists down.
Normal mode only.

This is the ANGLE model: it decides what the bank should be and eases
towards it, decides what the turn rate should be and adds it to the
heading. Forces is the other one, and computes the angles from the forces
instead. Neither is the better of the two -- Assisted is cosmetic and
predictable, which is exactly what a camera move often wants.

(Control Smoothing used to live here. It is input filtering and belongs to
no flight model, so it sits with Dead Zone and Axis Centre on the Control
page now, where it also works with no flight model at all.)

Bank Into Turns     turning or strafing tilts the camera into the
  Bank Angle        movement and eases back level, the way an aircraft
  From Yaw          rolls into a turn. Bank Angle is the tilt at full
  From Strafe       input (20-30 reads as flight); From Yaw and From
  Roll Response     Strafe weight which control causes it -- From Strafe
  Roll Level Time   is the "lean into the slide" part. Roll Response is
                    how quickly the bank ARRIVES and Roll Level Time how
                    slowly it leaves. Cosmetic on its own: it changes how
                    the shot looks, not where you go.
                    Those two sit together because they are one pair --
                    the roll in and the roll out -- and BOTH are live
                    whenever Bank Into Turns or Auto-Level Roll is on.
                    Roll Level Time used to sit under Auto-Level Roll,
                    which read as that toggle owning it, and it was the
                    only dependent slider on the page with no enable
                    expression at all, so it never greyed out to say
                    otherwise.

Bank Steers         the full aircraft model: the bank angle TURNS the
  Steer Rate        camera, so you steer by rolling and yaw becomes a
                    rudder. Bank Into Turns is cosmetic on its own --
                    this is what makes the tilt mean something.
                    Steer Rate is the turn at FULL bank, meaning at your
                    Bank Angle whatever you set it to: 45 gives exactly
                    45 degrees per second at 25, 45 or 60 degrees of
                    bank alike. Below full it follows the tangent, so
                    steeper banks turn harder than proportionally (half
                    of a 25-degree bank gives 21.4, not 22.5).
                    Where you FEEL it is a strafe: strafing alone never
                    changes your heading, and with this it curves you
                    round 40 degrees over two seconds at the defaults.
                    Held on a yaw it is subtler, since you are already
                    turning -- 180 degrees becomes 249 over the same two
                    seconds.
                    It does nothing at all while a Look At is set. The
                    aim is locked, so there is no view left to turn.

Auto-Level Roll     let go and the horizon comes back by itself, over
                    Roll Level Time (above). A Look At does not stop
                    this -- it fixes the aim, not the bank.
                    REDUNDANT while Bank Into Turns is on, which is worth
                    knowing before you go looking for why an unlevelled
                    roll still levels: Bank already eases the bank to 0
                    whenever nothing is asking for one. Turn Bank Into
                    Turns off for a bank that stays where you put it.
                    Rolling in and rolling out are separate numbers on
                    purpose: going into a bank should answer the stick,
                    while coming out of one is the aircraft's own weight
                    taking the wing back. With a single time a snappy
                    bank could only have a snappy recovery. From 25
                    degrees, one second leaves you at 2.7 degrees at
                    0.45, or 15.2 at 2.0; the way IN is Roll Response
                    either way (-22.3 after a second, unchanged).
                    Equal to Roll Response is symmetric, and is what
                    this did before it had its own control.
                    Bank Into Turns levels out the same way whether
                    Auto-Level is on or not -- what Auto-Level adds is
                    the same recovery for a roll you flew by hand.
Level Pitch         the nose also settles back toward the horizon when
  Pitch Level Time  you are not pitching. Keep it slower than Roll
                    Level Time or it will fight your framing. Free
                    flight only -- see the table below.

Speed-Scaled Turning  control authority follows how fast you are really
  Authority At Rest   moving -- sluggish at a crawl, crisp at speed, like
                      airflow over the surfaces. Authority At Rest is how
                      much turn survives standing still. Free flight
                      only -- see the table below.

Glide               the camera accelerates up to speed and coasts to a
  Glide Time        stop instead of starting and stopping dead. Free
                    flight only: orbiting and a Look At hold the camera
                    on a path, where momentum has nowhere to go.

Turbulence          a constant small wander on the angles, as if the air
  Turbulence Amount were never quite still -- handheld life for a locked
  Turbulence Speed  off shot. It moves the rotation pars, so a preset
                    captured mid-gust keeps that fraction of a degree.
                    Locked on a subject the wander on pitch and yaw is
                    overwritten each frame by whatever owns the aim, so
                    what survives is the roll.

### The flight model and the locked modes
Assisted is built for free flight. A Look At or an orbit takes
control of the aim, and anything that would fight for the same angles
stands down rather than argue. What survives is what is still
meaningful once you are locked on:

                        free flight   Look At    orbit
  Control Smoothing         yes         yes       yes
  Bank Into Turns           yes         yes       yes
  Roll Response /
    Roll Level Time         yes         yes       yes
  Auto-Level Roll           yes         yes       yes
  Turbulence                yes      roll only  roll only
  Bank Steers               yes          no        no
  Level Pitch               yes          no        no
  Speed-Scaled Turning      yes          no        no
  Glide                     yes          no        no

Bank survives because a Look At fixes the AIM, not the bank -- the
camera can still lean into a turn while staring at its subject, and
that is most of what the airplane feel is for.

The three that stand down do so because their whole job is to move
angles the locked mode has already decided. Bank Steers turns the
camera, and there is no view left to turn. Level Pitch drags the nose
toward the horizon, and an orbit recomputes that same nose angle every
frame to hold the pivot -- left in, it put the subject permanently off
centre by 0.26 degrees at the default Pitch Level Time, and 10.66 from
a steep orbit at the fastest. Speed-Scaled Turning throttles Yaw and
Pitch by airspeed, but locked on a subject those do not turn anything,
they carry you round it and reel it in -- and with no Forward pushed
the airspeed read zero, so an orbit crawled at Authority At Rest, 27
degrees a second instead of 90.

Glide is the exception that is about position rather than angle, and
it stands down for the same kind of reason: orbiting and a Look At
hold the camera on a path, where momentum has nowhere to go.

Note on yaw: heading is deliberately NOT self-centring -- that would
undo every turn you make. What returns by itself is the roll (Auto-Level)
and, if you want it, the pitch. What makes yaw ease to a stop rather
than cut dead is Control Smoothing.

All the easings are frame-rate independent, so a Response or Glide Time
means the same thing at 30 or 60 fps. With everything centred and the
horizon back, the model stops touching the camera entirely.


### Aerobatic mode
Off by default. The ordinary path adds Yaw to ry and Pitch to rx and clamps
the latter at 89 degrees, which is what makes a loop impossible: those are
WORLD axes, and past vertical they stop describing an aircraft at all. With
Aerobatic on, orientation is carried as a matrix and every stick input turns
the camera about the axis the AIRCRAFT has -- pitch about its right, yaw about
its up, roll about its nose. Going over the top stops being a special case and
becomes more of the same rotation.

It is a matrix and not a quaternion, despite that being the obvious tool. On
this build quaternions cannot be composed at all -- q1 * q2 raises and cross()
takes vectors -- and tdu.Quaternion(rx, ry, rz) builds in XYZ while this camera
is zxy, which puts the same three numbers about 37 degrees from where they
belong. Neither eulerAngles('zxy') nor decompose() returns zxy either, so the
write-back extraction is derived by hand and reads the matrix transposed. The
quaternion survives only as a measuring stick.

Presets are untouched by all of it. The orientation is written back to rx, ry
and rz every frame, so a preset recorded mid-loop stores three ordinary
numbers and recalls to the same orientation -- measured at dot 0.999999 across
a full loop with simultaneous roll. Where a single orientation has two valid
Euler triples, the one closer to last frame's is chosen, so the numbers stay
continuous for the HUD and the bank logic instead of flipping 180 degrees
through a manoeuvre the camera never made.

The upright assists stand DOWN while it is on: Bank Into Turns, Auto-Level
Roll, Level Pitch and bank steer -- and they grey out, so you can see that
they have. Every one of them is defined
against a horizon, and inverted they do not merely read wrong, they fight the
roll. Teaching six assists about being upside down is a different and larger
job than admitting they do not apply.

### Presets and momentum
Whichever model is carrying momentum, this holds. This component's day job
is recalling camera presets, and a preset recall
teleports the camera. Momentum from before a jump is not ours to carry
across it, so a jump larger than the current velocity could account for
drops the velocity and lets the engine spool back up. It is detected by the
size of the jump rather than by hooking every caller, which means it also
covers Teleport, a hand on the parameters, and whatever comes next.


## Ground page (contact: standing on things)
Off by default. Turn on Stick to Ground and the camera stops being a
flying thing that happens to be near the floor: it stands on whatever is
under it and walks. The ground owns the camera's HEIGHT and nothing
else, which is why free flight, a Look At, an orbit and both flight
models all keep steering exactly as they did -- this is a LAYER over
whatever is moving you, never a mode replacing it. Normal mode only.

That separation is why the walking simulator is a different page. This
one is CONTACT: where the floor is, how steep it may be, how smoothly to
follow it. Walking is LOCOMOTION: how fast a person goes over it and what
they can do -- and it needs this page, which is why choosing it arms Stick
to Ground. Keeping them apart is what lets a camera follow terrain while
orbiting a subject, with no walking model in sight.

There are three states, and the middle one is the point:

  grounded          the ground drives the eye
  airborne, ARMED   flying free, but coming back within Snap Distance
                    picks you up again
  free              the toggle off -- the ground is ignored until you
                    pulse Stick Now

That middle state is the difference between stepping off a hill and
turning walking off, so both gestures have somewhere to live.

Stick to Ground   arms it. Contact sticks, and after a detach you are
                  taken back when you come near again.
Stick Now         attach right now, whatever the toggle says. The camera
                  is not teleported -- it eases down to eye height the
                  way any landing arrives.
Detach            let go. The next re-attach is suppressed until you
                  have cleared Snap Distance. Without that, letting go
                  while standing still would be undone on the very next
                  frame and the pulse would do nothing at all.

Ground Geometry   what you can stand on. Empty means whatever the Render
                  TOP renders, so it follows the scene by itself. Point
                  it at one Geometry COMP to make only that walkable.
Eye Height        how far above the surface the camera rides. Eye level,
                  not foot level.
Ground Smooth     seconds to settle onto a new height. One number doing
                  two jobs, because they are the same job: it glides you
                  over small bumps instead of copying every polygon, and
                  it eases a landing instead of snapping to it. 0 pins
                  the camera rigidly to the surface.
Snap Distance     how close you must come, while armed, to be taken back
                  when you are rising towards the ground or hovering near
                  it. Coming DOWN it is not consulted: any frame that ends
                  at or below the ground has landed, however fast it
                  arrived. See "You cannot fall through" below.
Rise to Detach    how hard Rise must be pushed to lift you off the
                  ground. 0 means only Detach detaches.
Max Slope         degrees past which ground cannot be walked onto; the
                  move is refused the way Collision refuses one into a
                  wall. 90 climbs anything.
Slope Align       how far the camera leans toward the surface normal.
                  0, the default, keeps your head level, which is what
                  walking looks like; 1 lies the camera flat on the
                  hill, which is what a vehicle looks like.
Probe Distance    how far below the camera to look for ground.
Ground            read-only: what the model is doing, and what you are
                  standing on.

While grounded, Forward and Strafe run on the ground PLANE rather than
along the gaze. Walking is not flying with the height taken away: with
the aim borrowed whole, looking down would drive you into the floor and
looking up would stall you against it, and every glance would change
your pace. On foot the eyes are free and the feet keep going where the
body faces.

Glide, if you have it on, has its vertical taken out while you are
grounded. A carried velocity with a vertical component, fighting a
height that is re-pinned every frame, does not cancel -- it accumulates
into the constraint and comes back out as jitter.

### You cannot fall through
Landing used to be a proximity test -- come within Snap Distance and you
are taken back -- which is a WINDOW twice that wide that a fall has to
happen to land inside. A fast enough frame steps clean over it, and then
the camera is under the floor with a downward probe that can no longer
see the surface it went through, falling for ever. At the defaults a
single 0.1-second hitch after a quarter-second of falling was enough, and
at 30 fps so was any drop of about fifteen units.

Three things fixed it, and none of them needed a new parameter.

The probe now fires from the HIGHER of where you were and where you are
going, so its ray spans the whole frame's motion rather than starting
where you already are. Coming down, that is the difference between
looking for the floor from above it and looking for it from below.

Landing is a CROSSING rather than a proximity. While descending, any
frame that ends at or below the height the ground asks for has landed --
there is no speed at which you can outrun it. Snap Distance keeps its own
job for the other direction, where proximity is genuinely the question.

And a crossing landing puts the eye ON the surface rather than easing up
from wherever the step overshot to. Measured before that: a 200-unit drop
at 30 fps started its landing 2.3 units underground and rose out of it.
Ground Smooth still eases bumps and still softens a landing arrived at
from above; what it no longer has to do is unwind an integration
overshoot.

Measured after: drops of 20, 60, 200, 400 and 2000 units, at 60 fps, at
30 fps and with 0.1-second hitches throughout, all land -- the last of
them at 415 units per second -- and in none of them does the eye ever go
below the floor.

There is a backstop as well, for the camera that ends up under a surface
by some route the walking model never drove: a preset recall, a Teleport,
a hand on ty. While walking, if the ordinary probe finds nothing at all
AND you are below a floor you were recently standing on, it looks again
from that remembered height and puts you back. The memory is what keeps
it honest -- probing from overhead unconditionally would find whatever
happened to be above you and haul you onto it, and stepping off the edge
of the world would stop being a fall.


Head Bob moved to the Walking page in 1.12.0 -- it is locomotion rather
than contact -- but it still applies under ANY Flight Model whenever the
camera is standing on the ground, so a flying camera that lands gets it.

Head bob is driven by DISTANCE COVERED, never by a clock. A bob on a
clock is wrong in both directions at once: it keeps nodding while you
stand still, and it nods at the same rate whether you are strolling or
sprinting. Footfalls are a function of ground covered, so ground covered
is what drives it -- Bob Stride sets the rhythm and your own speed sets
the tempo, which is why slowing down slows the steps without a second
parameter for it.

The vertical runs at TWICE the stride while the sway runs at once. Two
footfalls to a stride means the head drops twice but leans left then
right, and it is that pairing -- a figure-eight rather than a sine --
that reads as walking instead of as being lifted up and down. The
amplitude follows how fast you are actually going, so it fades in as you
set off and out as you come to rest rather than stopping dead mid-stride
with the head off-centre.

The offset exists only between _writePose and _readPose: it is added on
the way out and taken off on the way in, so the ground model, the flight
model and every pick keep working on where the camera really is. Without
that, the ground smoothing would chase the bob and eat it.

### How the ground is found
A second camera -- orthographic and 0.02 units wide, a column rather
than a cone -- parked at the camera and pointed straight down into its
own 32x32 render, picked at the centre pixel. Its Parent Transform
Source is World Origin, so living inside the camera does not swing it
around with the camera's own aim.

Not a Ray SOP, deliberately. A ray only knows CPU-side SOP geometry:
POPs, GPU displacement and instanced copies are all invisible to it, and
it would confidently report a surface that is not the one being drawn.
The pick samples what was actually RENDERED, so it sees whatever the
scene happens to be made of -- and it names the object you are standing
on for free.

It costs about 0.4 ms a frame while you are actually on the ground, and
nothing at all otherwise: detached and disarmed, neither the probe
render nor the pick cooks even once.

One limitation worth knowing: the probe looks DOWN from the camera, so
it finds the first surface below you. Drive far enough into a hill that
the surface ends up above the lens and there is nothing below to find,
and you come off the ground until there is again.


## Walking page (first person on foot)
Flight Model = Walking. A person rather than an aircraft: walk, sprint,
crouch and jump, over whatever the Ground page is standing you on.
Choosing it arms Stick to Ground, because feet with nothing under them
are just a slower free-fly. Normal mode only.

Yaw and Pitch look about exactly as they do in free flight -- on foot the
eyes are free. Forward and Strafe are the FEET: they run on the ground
plane, never along the gaze, so looking down does not walk you into the
floor. Rise and Zoom do nothing here. Levitating is not something feet
do, and the way off the ground is Jump.

Walk Speed        units per second at full stick. Eye Height is 1.7 by
                  default, so these are person-sized units: 1.4 is a
                  stroll, 3.5 a brisk walk, 6 a jog. Move Speed on the
                  Control page is the FLYING speed and is not read here.
Sprint            Walk Speed is multiplied by this while the Sprint
                  control is held. 2.2 is about a run against a walk;
                  much past 3 reads as a vehicle.
Crouch Speed      and by this while crouched. Crouching should cost you
                  pace, or it is only a camera height change.
Accelerate        seconds to reach full speed from standing.
Stop              seconds to come to rest with the stick centred. Usually
                  shorter than Accelerate: feet stop faster than they
                  start, and those two numbers are the whole of how heavy
                  the walk feels.

Jump Height       peak height of a jump, in scene units.
Rise Time         seconds from leaving the ground to the top of it.
Fall Speed        gravity on the way DOWN as a multiple of gravity on the
                  way up. 1 is a true parabola; above 1 the fall is
                  quicker, which is what nearly every game does because a
                  symmetric jump hangs at the top.
Air Control       how much steering authority you keep in mid-air. 0
                  commits you to the arc you jumped with; 1 lets you turn
                  freely.
Jump Now          jump once from the parameter dialog, for tuning the arc
                  without a pad.

Crouch            Hold (the shooter convention, and safer on a pad) or
                  Toggle (a keyboard, a MIDI button, or a long crouched
                  shot).
Crouch Height     Eye Height is multiplied by this while crouched. Eye
                  Height itself stays on the Ground page -- it belongs to
                  standing on a surface rather than to walking about on
                  one.
Crouch Time       seconds to duck or rise. Quick but never instant: a snap
                  reads as a cut.

Head Bob          moved here from the Ground page in 1.12.0. See GROUND
Bob Stride        PAGE for how it works -- it is driven by distance
Bob Sway          covered, and applies under any Flight Model while you
                  are on the ground.

Wall Collision    stop walking through walls. Off by default, because it
Stand-off         costs a render and a pick every frame you are moving.
Slide             Stand-off is how far in front of a wall you stop --
                  your own width. Slide 1 keeps the part of your movement
                  that runs ALONG the surface, which is what makes a
                  corridor walkable rather than sticky; 0 stops you dead.
Walking           read-only: how fast, and what you are doing.

There is no gravity dial. A jump is fully described by how HIGH it goes
and how LONG it takes to get there, so gravity is derived from those two
-- g = 2h/t squared -- and Fall Speed scales it for the descent. Asking
for gravity as well would have meant a third number that has to agree
with the other two, and a World Scale on somebody else's page to make it
mean anything, which is exactly the trap the retired energy model left
behind.

Measured: the arc reaches Jump Height to within 0.04 percent and does it
at 30, 60 and 120 fps alike. It integrates the parabola in half-steps for
that reason -- taking the whole gravity kick and then stepping loses
g*dt squared over 2 of height EVERY frame, which at 60 fps costs a 1.10
jump about 0.05 of its apex, and a parameter called Jump Height should
mean the height.

Wall collision is ONE RAY along the direction you are travelling, fired
from a proxy render the same way the ground probe works -- and for the
same reason, since a Ray SOP sees only CPU-side SOP geometry and would
walk you straight through a POP, a displaced surface or an instance. It
is your centre line and not your width, so a wall clipped with a shoulder
while passing at an angle is not seen; three rays would be three renders
and three picks every frame. Stand-off is measured PERPENDICULAR to the
surface rather than along the ray: at a shallow angle the ray distance is
far longer than the gap actually between you, and clamping on it let a
diagonal approach close to 0.35 of a wall while Stand-off said 0.4.

Sliding projects the VELOCITY as well as the step. Without that you go on
accelerating into the wall for as long as the stick is held, and shoot
sideways the moment you clear it.


## Driving page (a car)
Flight Model = Driving. A vehicle rather than a person or an aircraft, over
whatever the Ground page is standing it on. Choosing it arms Stick to Ground
for the reason Walking does -- a car with nothing under it is only a slower
free-fly -- and raises Slope Align to 1 if it is still sitting at 0, because
leaning with the road is the one thing a walking camera was right to refuse
and a car cannot do without. A Slope Align you chose yourself is left alone.
Normal mode only.

Forward is the THROTTLE and the brake. Strafe is the STEERING WHEEL. That is
the thing to know before picking up a pad: under this model Strafe stops
meaning strafe, the way Rise and Zoom stop meaning anything under Walking.
Stick right turns right and stick right looks right, the same way round as
every other model here. Yaw and Pitch are the DRIVER'S HEAD -- look about the
cabin while the car goes on going where the wheels point, and let go and your
head comes back to the road by itself. A walker's facing and heading are one thing; a driver's are
two, which is the whole shape of this model.

Handling          Arcade or Grip. Arcade goes exactly where it points and
                  never slides; Grip gives the tyres a finite hold and lets
                  you past it.
Top Speed         units per second at full throttle. Eye Height is
                  person-sized, so these are person-sized units: 6 is a jog,
                  15 a town road, 40 a motorway.
Accelerate        seconds from a standstill to Top Speed, and it means the
                  seconds it says -- measured 0 to 15.000 with 0.0000 percent
                  error at 30, 60 and 120 fps alike.
Brake             braking force as a multiple of Accelerate. Above 1 the car
                  stops harder than it starts, which every car does.
Coast             seconds to roll to rest with the throttle centred.
Reverse           reverse top speed as a fraction of Top Speed. Brake to a
                  stop and hold the throttle back to engage it: one axis, no
                  reverse button.

Turn Radius       the tightest circle the car will hold, at full lock and low
                  speed -- the one number saying how big it handles. Measured
                  at 6.000 against a stated 6.0, at all three frame rates.
Steer Rate        seconds to wind the wheel from centre to full lock. Small
                  is twitchy, large is a bus.
Speed Steer       how much steering authority falls away with speed, 0 to 1.
                  At 0 the car turns as tightly at eighty as it does parking,
                  which no car does.

Grip              how hard the tyres pull sideways before letting go, in units
Slide             per second squared, and how much hold is left once they
Countersteer      have. A corner needs v squared over r: at 15 u/s round a
                  6-unit radius that is 37.5, so a Grip of 8 slides and a Grip
                  of 40 does not. Past the limit the car UNDERSTEERS onto the
                  radius the tyres can really keep while the nose goes on
                  turning, and the angle opening between those two is the
                  slide -- measured, a 6.0 corner opens out to 6.996.
                  Countersteer feeds a little of it back into the wheel, which
                  is what makes a slide catchable on a thumbstick rather than
                  a spin. Grip handling only.
Drift             how far the Drift control breaks the back loose while it is
                  held. Learn it on the Mapping page like Jump or Sprint.
                  Under Grip it drops the tyres' hold; under Arcade, which has
                  no slip angle to break, it swings the nose instead.

View              In-Car or Chase. In-Car is the driver's eye; Chase trails
Eye Height        the car on a spring and looks up the road past it. Eye
Chase Distance    Height is the driver's and replaces the Ground page's while
Chase Height      driving -- a driver sits, and sits lower than a walker
Chase Lag         stands. Chase Distance and Height are measured from the car,
Chase Aim         Chase Aim is how far up the road the camera looks past it,
                  and Chase Lag is how loosely the camera follows.
Driving           read-only: how fast, and what the car is doing.

The slip is carried as an ANGLE and not as a sideways speed, and that is the
whole of why Grip is stable. Carrying the velocity instead -- the tyres
subtracting each frame what they could -- runs away: at 15 u/s round a 6-unit
corner the turn adds about 0.65 of lateral every frame while 4 units of grip
take back 0.067. That measured 90 u/s sideways on a car doing 15, and still
read 3.5 after the car had stopped. An angle cannot do either. It is bounded
by the geometry, it decays on the grip the corner is not using, and a
stationary car has none of it by construction.

Changing View is a MIX and not a switch. As a switch it is a jump of Chase
Distance the instant the menu changes, and Mode Blend on the Control page
cannot help: its business is the STEERING mode -- free, orbit, Look At -- which
does not change when the view does. Eased on Chase Lag instead, so no new
parameter: the worst single frame of a full In-Car to Chase move measures 0.30
against an offset of 6.5.

The car carries its own position, so anything else moving the camera -- a
preset recall, a Teleport, a hand on tx -- would otherwise be undone on the
very next frame, the car dragging the view back to where it left it. It is
not. A jump of more than two units is taken as somebody else's doing and the
car takes up the pose it finds: this is a SEQUENCER before it is a driving
model, and a recalled preset losing to the car would be the wrong one of the
two winning.


## Forces page (force flight model)
The other flight model: Flight Model = Forces. Everything above -- Bank Into
Turns, bank steer, Auto-Level, Aerobatic -- belongs to Assisted and is
untouched by this, and greys out while this one is flying. Flip between them
mid-flight and compare.

World Scale sits on this page because this model is the only thing that
reads it. It says how many scene units make one metre, which is what turns
9.81 into a number that means something in your scene -- 0.1 suits a scene
100 units across. It described the scene rather than the aircraft even when
it lived on the Physics page, which is why the airframe presets never
touched it.

The difference is not more physics, it is where the physics lives. The first
model computes ANGLES: it decides what the bank should be and eases towards
it, decides what the turn rate should be from g tan(phi) / v and adds it to
the heading. This one computes FORCES and lets the angles be whatever falls
out. It carries an angular velocity and a velocity vector as state, and every
frame it adds up four accelerations -- thrust along the nose, lift across the
flight path, drag back along it, weight straight down -- and three moments:
your stick, the airflow damping whatever rate you already have, and the
airframe weathervaning its nose back into the wind.

An aeroplane turns by ROLLING, and that catches out any controller mapped for
the other model. There, Bank Into Turns quietly converted the Yaw axis into a
banked turn, so the stick you learned to turn with WAS the turn control. Here
Yaw is the rudder and nothing else -- measured, full rudder held for four
seconds moves the heading 0.02 degrees and does nothing but sideslip six and
lose 23 metres.

So Stick Layout defaults to GTA, which is the layout most people already have
in their hands:

    Right trigger      throttle
    Left trigger       airbrake
    Left stick fwd     nose DOWN        (back for nose up)
    Left stick sides   roll
    Right stick sides  rudder
    Roll axis / b3     roll, in every layout

GTA puts rudder on the bumpers. This component uses those for Orbit and Look
At, so rudder sits on the right stick instead -- GTA leaves that to the camera,
and a camera that IS the aeroplane has none to point. Buttons are not remapped
at all, so Orbit, Look At and Teleport stay where they were.

Turn Stick Rolls is the smaller change, for a controller already mapped to the
other model: the Yaw axis banks instead of yawing and the Strafe axis becomes
the rudder, everything else as it was. Axes As Named leaves each axis literal,
for a yoke and pedals.

One consequence worth knowing: Rise Detach is ignored while the force model is
flying. Rise is how a WALKING camera leaves the ground, but here it is the
throttle, and leaving that armed tore the aircraft off the runway at zero knots
the moment the throttle passed 0.6. The aeroplane leaves the ground on lift
instead.

Two things still differ from the other model, and they are the model rather
than the mapping. Roll is a RATE, not an angle: hold the stick and you keep
rolling, so a turn is roll in, centre the stick, pull. And an unassisted
airframe SPIRALS -- measured, a hands-off 30-degree bank wound itself to 58
in four seconds. Wings Level is what stops that, and it is why the arcade end
of the range is flyable with one thumb.

Nothing in it computes a turn rate. Bank the aircraft and the lift vector
tilts with it; the horizontal part has nothing to balance it and pulls the
flight path round. Measured against g tan(phi) / v, which appears nowhere in
the code:

    bank     measured    g tan(phi)/v     error
     20      2.0457        2.0458       -0.002%
     40      4.7157        4.7163       -0.014%
     60      9.7321        9.7354       -0.034%

Roll past vertical and the same bank turns the other way, because the same
lift vector now points the other way: 49.2 degrees swept upright against
-47.8 inverted on the identical stick input. A loop conserves energy to
0.20 percent with drag and thrust at zero -- 360 degrees of flight path, 743
metres tall, back to within 0.2 m of its starting height and 0.7 m/s of its
starting speed.

The stall is the lift curve, not a speed test. There is no "if slower than X"
anywhere in the model. Lift climbs with the angle the wing meets the air at,
peaks at Stall Angle and falls away past it, so you stall by asking for an
angle the wing cannot hold -- which is what happens by itself when you slow
down and have to pull harder to stay up. Flown, that reads as: zoom-climb, run
out of speed at the top, the nose drops on its own, speed builds, the wing
bites again. Nobody wrote that recovery.

Rotation has inertia. A stick deflection is an angular ACCELERATION and the
airflow takes rate back out in proportion to the rate you already have, so
holding the stick balances at Power / Damping and getting there takes
1 / Damping seconds. Let go and the same term decays it. Measured at the
defaults: roll peaks at 200.0 deg/s and decays with a 0.225 s time constant,
pitch 100.0 and 0.283, yaw 48.0 and 0.400. Three axes, three different
answers, none of them an ease towards a target angle.

Strafe and Rise do nothing here. An aeroplane has a throttle and a stick;
sliding sideways and levitating are not forces it can produce. Move Speed is
not read either -- this page carries its own Thrust.

Flight Model        set it to Forces (Control page). The Assisted page
                    greys out while it is chosen -- nothing on it runs.
World Scale         how many scene units make one metre. THE number to get
                    right first: it is what turns 9.81 into a figure that
                    means anything in your scene, and 0.1 suits a scene
                    about 100 units across. It describes the SCENE rather
                    than the aircraft, which is why no preset touches it.
Stick Layout        GTA (default) puts throttle and airbrake on the triggers
                    and flies on the left stick, with rudder on the right.
                    Turn Stick Rolls is a smaller change for a pad already
                    mapped to the other model -- the Yaw axis banks, the
                    Strafe axis rudders. Axes As Named leaves every axis
                    literal, for a yoke and pedals.
Preset / Apply      Arcade, Standard or Sim, written on the pulse. See below.
Gravity             multiplier on 9.81, itself scaled by World Scale
                    above. 1 is Earth; 0 is weightless.
Thrust              acceleration along the nose at full throttle, m/s^2.
Drag                deceleration from drag at Lift Speed. It grows with the
                    square of airspeed, so this one number sets it
                    everywhere. Induced drag rides on top automatically,
                    which is why a hard pull costs you speed.
Airbrake            extra drag at full back-stick, as a multiple of Drag.
Lift Speed          the airspeed at which the wing, at its best angle, makes
                    exactly 1 g. NOT a stall threshold -- nothing is ever
                    tested against it. It calibrates the wing at every speed,
                    and below it the wing simply cannot hold the aircraft up.
Stall Angle         where lift peaks, in degrees of attack. Past it the flow
                    separates and lift falls away.
Stability           how hard the airframe weathervanes, deg/s^2 per degree.
                    Two jobs, and the second one matters more than it looks:
                    Pitch Power divided by Stability is the angle of attack
                    full back-stick ASKS for. Under Stall Angle and pulling as
                    hard as you like cannot stall you; over it and it can.
                    That ratio is most of the arcade/sim difference.
Trim                the angle of attack it flies at with the stick centred.
                    The trim wheel. Hands off, it settles here and therefore
                    holds height at one particular speed -- faster it climbs,
                    slower it sinks, exactly as a trimmed aeroplane does. At 0
                    the wing makes no lift with the stick centred and you
                    descend unless you pull, which is honest, and is also how
                    you get a glider.

                    Each preset sets it to Stall Angle x Drag / Thrust, which
                    is the angle that holds level flight at that airframe's
                    own top speed. Getting that pairing wrong is what made the
                    first Arcade preset fly an unattended loop in seventeen
                    seconds on nothing but held throttle: it was trimmed for
                    60 m/s and cruised at 86.
Wings Level         how hard the wings roll back to level when you are not
                    asking for roll, 0 to 1. A real aircraft gets this from
                    dihedral, which needs a side force this model does not
                    have, so it is supplied directly. It fades out as you feed
                    in roll, so full stick keeps full authority, and it passes
                    through zero inverted rather than flipping you out of a
                    loop. At 0 you have the bare airframe, which spirals.
Auto-Coordinate     how much of the sideslip is taken out for you, 0 to 1. A
                    real aircraft has a yaw damper doing exactly this.
Level Hold          how much of the angle of attack LEVEL FLIGHT needs is
                    supplied for you, 0 to 1 -- one g for whatever bank you
                    are in, plus whatever nulls the climb rate you already
                    have. At 1 the stick centred returns to level whatever the
                    throttle is doing; at 0 you fly the bare trimmed
                    aeroplane, which holds height at one speed only and climbs
                    on any thrust left over. It goes into the trim angle
                    rather than chasing you with a servo: level flight at bank
                    phi needs 1/cos(phi) times the lift and the wing makes
                    lift in proportion to angle of attack, so the angle is
                    arithmetic. Capped so it can never ask past the stall, and
                    gone once the wings pass vertical, so a loop is untouched.
                    A deliberate pull still climbs -- your stick moment dwarfs
                    a trim offset -- it just comes back to level when you let
                    go, over about two seconds.

                    Measured in a 40-degree bank: 0 sinks 22.8 m in four
                    seconds and turns at 3.59 deg/s, 1.0 sinks 11.6 and turns
                    at 4.51 against an ideal 4.72. Thrown into a 30 m/s climb,
                    Arcade nulls it to 1.7 m/s in ten seconds without
                    overshooting.
Roll / Pitch / Yaw Power and Damping
                    Power is the angular acceleration at full stick; Damping
                    is how fast the airflow kills the rate. Peak rate is
                    Power / Damping and the time to reach it is 1 / Damping.
Status              airspeed, angle of attack, sideslip, and whether the wing
                    is still flying. A readout only -- it computes nothing and
                    so cannot disagree with the model.

  Arcade    cannot be stalled by pulling: full stick asks for 11.1 degrees
            against a 24-degree stall (measured peak 14.8 with the overshoot).
            Heavily damped, fully coordinated, full level hold.
  Standard  full stick lands right at the stall angle. Most assists on.
  Sim       full stick asks for 25 degrees against a 14-degree stall, so it
            will depart if you pull like that. No coordination, no level hold,
            no wings level, a third the damping -- rates are carried rather
            than commanded -- and the axes go back to their literal meanings,
            on the grounds that anyone asking for Sim has pedals.

Measured, Arcade against Sim: roll rate decays with a 0.071 s time constant
against 0.308, and mean sideslip through a banked turn is 0.20 degrees against
0.30 (peak 1.14 against 2.24). Sideslip stays small in both because the model
has no side force -- sideslip makes a yawing moment but no sideways push -- so
coordination is a real difference here rather than a dramatic one.

Ground Stick works with it. The aircraft taxis, rotates, and leaves the ground
the moment lift beats weight; it lands and is caught again within Snap
Distance. That lift-off is not a special case bolted on -- the comparison
already exists as the sign of the vertical velocity. It is needed because the
ground model's only automatic release is the Rise axis crossing Rise Detach,
and an aeroplane has no Rise: without it the aircraft rolls down the runway at
278 km/h with the nose up and never leaves.

An honest limitation: the first pass of any flight model is a mechanism, not a
feel. The mechanism here is measured and correct; the CONSTANTS are a starting
point, and the page exists so you can move them.

## What's new
1.8 (2026-10)
- Joined FNSTools as FNS_GeoPilot, from the OpSeqDev family, and the
  FNS operator family (the FNS tab of the OP Create dialog). It ships
  unmapped, at its designed defaults, with the ground and wall probes
  bypassed until you turn them on.
- The chain reads top-down on the Pilot page: Body Preset and Apply
  Body, Current Body, Flight Model, Flight Physics. Control Preset sits
  at the top of the Mapping page with Current Layout under it.
- Mouse Look in the node viewer, with its own invert and smoothing, and
  Pan and Dolly on the other buttons and the wheel (1.7).
- Control layouts carry Capture, Next and Previous (R, Z and X on the
  keyboard), and Keyboard Panel makes keys count only while the
  component's own viewer has focus (1.6).
