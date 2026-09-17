---
package: FNS_ProSceneChanger
summary: 'The Pro scene changer: everything SimpleSceneChanger does, plus per-scene timing and easing, a cue table with play, timeline, timecode and CHOP drivers, CHOP output blending, and fleet follow. Its own package, beside the simple one.'
features:
  - name: Contents
    anchor: contents
  - name: Quick start
    anchor: quick-start
  - name: Inputs two ways to add scenes
    anchor: inputs-two-ways-to-add-scenes
  - name: Custom page
    anchor: custom-page
  - name: Cooking page
    anchor: cooking-page
  - name: Inputs page
    anchor: inputs-page
  - name: Callbacks and about pages
    anchor: callbacks-and-about-pages
  - name: The a/b fader
    anchor: the-a-b-fader
  - name: How cook control decides
    anchor: how-cook-control-decides
  - name: Python
    anchor: python
  - name: Troubleshooting and notes
    anchor: troubleshooting-and-notes
---

## Base and Pro

ProSceneChanger is the Pro package of the scene changer family. Everything below applies to it as it does to SimpleSceneChanger; the section at the end says what it adds. The two install side by side under their own names and find each other in the same fleet.

## Contents
1. Quick start
2. Inputs: two ways to add scenes
3. Custom page (what's showing, transition, output)
4. Cooking page (what cooks, and when)
5. Inputs page (wiring tools, colours)
6. Callbacks and About pages
7. The A/B fader
8. How cook control decides
9. Python
10. Troubleshooting and notes

## Quick start
1. Add scenes: wire scene COMPs into the input connectors, or reference COMPs or TOPs in the
   Inputs sequence at the bottom of the Custom page (see section 2).
2. Pick a Switch Mode and set Select (or Select Menu) to the scene you want. That's it.
3. On the Cooking page turn on Control Cook so idle scenes stop cooking, and Unload so their
   memory is released. Add Pre-Roll or Outro if a scene needs time before or after its switch.

The output is the changer's out1 TOP, at the resolution set by Res.

## Inputs: two ways to add scenes
Each input is one scene with an index, counting from 0. Use either or both:

Wired connectors    Connect a scene COMP to an input connector. TouchDesigner only offers a
                    COMP-level TOP connector when the COMP contains an Out TOP, so wired scenes
                    need one. The COMP on the other end of the wire is the scene.

Inputs sequence     Each block's TOP parameter takes a COMP or a TOP:
                    - a TOP is used as it is;
                    - a COMP is resolved to the Out TOP behind its first TOP output if it has
                      one, otherwise to a TOP inside it whose display flag is on (the left-most
                      if several), otherwise to the right-most TOP inside it.
                    A referenced COMP is the scene for cook control whichever TOP is shown.
                    A block reference takes precedence over a wire on the same index.

Add sequence blocks for more inputs; the connectors and the internal select TOPs follow. A bare
TOP that is not inside a scene COMP is shown but never uncooked or unloaded.

## Custom page
What's showing
Active            Master switch. Off: no transitions, every scene cooks, node colours restored.
Select            Scene index to show. Constant, expression, bind or exported CHOP channel all
                  work; changes are seen the frame they happen, even mid-transition.
Select Menu       Pick a scene by name. Available when Select is a constant or bind.
Loop Type         Out-of-range Select values: Clamp holds at the ends, Loop wraps around
                  (modulo), Zigzag bounces back and forth.
Current Select    Read-only: the scene currently visible.
Num Scenes        Read-only: number of inputs.
Progress          Read-only: 0-1 progress of the running timed transition.
Finish Transition Pulse: complete the switch under way right now. A running crossfade or fade
                  lands on its target, a Pre-Roll cuts straight to the scene it was warming, and
                  a half-moved A/B Fader completes. Does nothing when idle.

Transition
Switch Mode
   Crossfade              Blend from the current scene to the target over Crossfade Length.
   Fade Through Black     Fade the current scene out (Fade Out Time), then the target in
                          (Fade In Time).
   Cut                    Instant switch.
   A/B Fader Crossfade    Driven by the A/B Fader parameter, see section 7.
   A/B Fader Through Black
Crossfade Length  Seconds for Crossfade.
Easing            Curve applied to crossfades, fade-outs and fade-ins (not to the A/B fader).
Fade Out Time     Seconds to fade the current scene to black in Fade Through Black.
Fade In Time      Seconds to fade the target up from black in Fade Through Black.
Fade Style        What "black" means: To Black drives RGB to black and keeps alpha (opaque);
                  To Transparent fades opacity instead. Applies to both through-black modes.
A/B Fader         The manual control for the two A/B Fader modes.

Auto Advance
Auto Advance      Switch to the next scene every Interval. Off pauses the countdown where it is.
                  Choosing a scene by hand (Select, Select Menu, Switch()) restarts the countdown
                  from that scene, now or when Auto Advance is turned back on.
Advance On        Timer: every Interval, as above. A/B Fader: no countdown; each time the A/B
                  Fader completes a switch, Select moves on to the next scene, so the next push of
                  the Fader goes there (and its Pre-Roll starts at once). Pulling the Fader back
                  home does not advance; picking a scene by hand continues the order from there.
                  Only in the two A/B Fader modes.
Interval          Seconds between switches, the transition included (Advance On = Timer).
Order             Sequential steps through the scenes in Direction; Loop Type decides the ends
                  (Clamp stops, Loop wraps, Zigzag turns round). Random shows every other scene
                  once, in a shuffled order, before any repeats; it never "switches" to the scene
                  already visible.
Direction         Sequential order: Forward (next index) or Back (previous index).
Random Seed       Random order: the same seed always gives the same sequence.
Next Switch In    Read-only: seconds until the next Auto switch.

Per-scene times: a scene COMP carrying custom parameters named Fadeintime and/or Fadeouttime
overrides the changer's times for that scene (Fadeintime also overrides Crossfade Length).
Per-scene curves: Fadeincurve (arriving: the crossfade or the fade-up half) and Fadeoutcurve
(leaving: the fade-to-black half) name an Easing curve, e.g. 'OutBounce'. Unknown names are
ignored, so Easing applies.

Output
Res               Output resolution of the changer.
Inputs            The scene reference sequence described in section 2.

Only the parameters the current Switch Mode uses stay enabled.

## Cooking page
Control Cook      Only the visible scene (plus the incoming one during a transition) is allowed
                  to cook; every other scene COMP has cooking disabled. Everything else on this
                  page needs it.
Pre-Roll          Seconds the target scene cooks before its transition starts. On a Select change
                  the target COMP is allowed to cook right away and the switch is delayed by this
                  much, so feedback loops, movies or particles are warm when they appear. Changing
                  Select during the pre-roll re-targets it; choosing the visible scene cancels it.
                  In the A/B Fader modes any value above 0 warms the chosen scene as soon as Select
                  changes; the Fader still decides when it shows.
Outro             Seconds the outgoing scene keeps cooking after the switch completed, so an exit
                  animation can finish off-screen. Afterwards it is uncooked and unloaded as usual
                  (unless it has become visible again in the meantime).
Unload            When a scene stops cooking, release its CPU/GPU memory a few frames later.
                  Cancelled automatically if the scene is selected again before that.
Unload Method     Progressive = COMP.progressiveUnload() paced by Unload Budget; covers every
                  node type including POP buffers. Immediate = unload() on each unlocked TOP in a
                  single frame. Locked operators are never unloaded with either method.
Unload Budget     Milliseconds per frame the progressive unload may spend, so a heavy scene never
                  hitches the frame it stops cooking. 0 = everything in one frame.

## Inputs page
Wiring tools (they act on inputs wired into the connectors, not on Inputs sequence references;
each is a single undo step)
Reverse Inputs    Reconnect the wired inputs in reverse order.
Randomize Inputs  Reconnect the wired inputs in a random order.
NodeY to Order    Reconnect so the input order matches the sources' top-to-bottom position.
Order to NodeY    Swap the sources' positions so top-to-bottom matches the input order.
^ automatic       Keep NodeY to Order applied whenever a wired input COMP is moved.
Align Inputs      Toggle. While on, the wired sources are kept stacked in a column beside the
                  changer, input 0 on top, using Alignment Mode (Top / Center / Bottom) and
                  Adjust Offset (X, Y, YGap); changing either, or the wiring, re-aligns at
                  once. Re-toggle to re-align after moving things by hand.

Colours
Colorize Scenes   Tint the scene COMPs in the network editor: On Color for the visible (and
                  incoming) scene, Off Color for the rest. Each scene's original colour is
                  remembered the first time it is tinted and restored when Colorize is off.
Off = Keep Original Color   Idle scenes get their own original colour back instead of Off Color.

## Callbacks and about pages
Callbacks         Create Callbacks makes an editable callbacks DAT next to the changer, with each
                  callback documented inside. Each callback can also take an `info` dict with scene
                  names and indices; it is passed only when the function declares an `info`
                  parameter (or **kwargs), so older callbacks DATs keep working. Five callbacks:
                    onPrerollStart(target, current, seconds)        a scene starts its Pre-Roll
                        warm-up (only when Pre-Roll is above 0).
                    onTransitionStart(target, current, mode)        a switch has begun: after any
                        Pre-Roll, for cuts, when the A/B Fader leaves home, and again when a running
                        switch is redirected. target/current are the scene COMPs (or TOPs for bare
                        TOP scenes); mode is 'cross', 'fade', 'cut', 'manual' or 'manualfade'.
                    onTransitionCancel(target, current)             a pre-rolling or running switch
                        was abandoned (Select back or elsewhere, Fader home, Active off): target
                        will not arrive.
                    onSelectionChange(selected_ops, unselected_ops) a switch completed; the lists
                        hold the TOPs shown (a wired scene's In TOP, or the resolved TOP). The
                        leaving scene's Outro starts here.
                    onCookingChange(cooked_comps, uncooked_comps)   Control Cook enabled or disabled
                        scene COMPs; only changes are reported.
About             Open Documentation opens this text. Build Number, Build Date and Touch Build
                  are stamped at every release. Package Version is the version FNSTools compares
                  against the published release to offer updates.

## The a/b fader
The two A/B Fader modes work like a DJ crossfader:

- Whichever end the Fader rests at (0 or 1) is the current scene.
- Set Select to the next scene. Nothing changes yet.
- Move the Fader toward the opposite end: the blend (or the fade through black) follows the
  Fader position. Arriving at the far end completes the switch, and that end becomes the new
  resting end. Push up to switch, pick the next scene, pull down to switch again, so a
  physical fader never needs resetting.
- Turning back before arriving cancels and leaves the current scene untouched.
- Changing Select while the Fader is mid-way re-targets without a jump.
- Changing Switch Mode while a fader switch is armed keeps it armed; the new mode applies from
  the next switch.
- With Auto Advance on and Advance On = A/B Fader, Select lines up the next scene after every
  completed switch: just push and pull the Fader to walk through the scenes.

In A/B Fader Through Black the first half of the travel fades the current scene to black and
the second half fades the target up. Fade Style applies. Easing does not.

## How cook control decides
With Control Cook on, after every change the changer recomputes which scene COMPs may cook:

  the visible scene
  + the incoming scene while a transition runs
  + a scene pre-rolling for its turn (Pre-Roll)
  + scenes still inside their Outro window

Everything else has cooking disabled and, with Unload on, is unloaded a few frames later. Because
this is recomputed from scratch rather than tracked step by step, an interrupted, restarted or
dropped transition can never leave a scene cooking forever, and a scene selected again before its
unload lands simply keeps its memory.

Any Select change is honoured immediately, even in the middle of a running transition: the
transition restarts toward the new scene, snapping back to the scene that was fully visible.
Choosing the visible scene again while a transition runs cancels it.

Several changers on the same scenes (multi-screen output): every SceneChanger carries the tag
FNS_SceneChanger, so changers driving the same scene COMPs find each other and share cooking. A
changer never uncooks (or unloads) a scene another changer still needs: the scene it shows, the
one it brings in, one warming up for its Pre-Roll, one still in its Outro, or an Always Cook scene
(Pro). A changer with Active off still keeps the scene it shows. A scene nobody needs is uncooked
by whichever changer lets go of it last. With Colorize on, a scene shown on any screen is lit, and
each scene's original colour is remembered once for the group. Base always shares; Pro has a Fleet
toggle to opt out.

## Python
  op('SimpleSceneChanger1').Switch(target, mode=None, fadeouttime=None, fadeintime=None,
                                   easingout=None, easingin=None)
      target: scene index, scene name ('intro'), or the scene COMP / TOP itself. A string that is
      no scene name is tried as an operator path.
      mode: 'cross' | 'fade' | 'cut' | 'manual' | 'manualfade' (None = Switch Mode par).
      fadeouttime / fadeintime: per-call overrides in seconds (fadeintime is the crossfade
      length in 'cross' mode). Pre-Roll and Outro apply as usual.
      easingout / easingin: per-call curve names from the Easing menu (easingin is also the
      crossfade curve).
  op('SimpleSceneChanger1').FinishTransition()
      Complete the switch under way right now (same as the Finish Transition pulse).
  op('SimpleSceneChanger1').Next(**overrides) / .Previous(**overrides)
      Switch to the next / previous scene (from the incoming one while a switch runs). Loop wraps,
      Clamp stops at the ends, Zigzag turns back. Takes Switch()'s overrides; returns the index or None.
  op('SimpleSceneChanger1').SceneName(index)     the scene's name, or None for an empty slot
  op('SimpleSceneChanger1').SceneIndex(name)     the first scene with that name, or None
  op('SimpleSceneChanger1').Scene(target)        the scene operator for an index, name or operator
  A scene's name is its COMP's name, or the TOP's name for a bare TOP scene.
  The properties below are dependable and read-only: a parameter expression that reads them
  (e.g. op('SimpleSceneChanger1').CurrentName) updates on its own whenever they change.
  op('SimpleSceneChanger1').CurrentIndex     visible scene index (outgoing one during a switch)
  op('SimpleSceneChanger1').CurrentName      its name;  .CurrentScene  its operator
  op('SimpleSceneChanger1').IncomingIndex    target of a running switch, or None
  op('SimpleSceneChanger1').IncomingName     its name;  .IncomingScene its operator
  op('SimpleSceneChanger1').IsSwitching
  op('SimpleSceneChanger1').SceneNames       every scene's name by index ('' for an empty slot);
                                             follows rewiring and Inputs changes (a renamed scene COMP
                                             shows up at the next switch or input change)

Setting the Select parameter from Python is equivalent to using the dialog.

## Troubleshooting and notes
- Nothing switches when I change Select Menu: Select is driven by an expression or export.
  Select Menu only works while Select is a constant or bind; drive Select directly instead.
- A scene never stops cooking: it is a bare TOP (not a COMP), or Control Cook is off, or Active
  is off. Bare TOPs are shown but never controlled.
- A scene keeps cooking for a while after switching: that is Outro. Set it to 0 for an
  immediate stop.
- Fade times or curves feel wrong for one scene: check that scene COMP for Fadeintime /
  Fadeouttime / Fadeincurve / Fadeoutcurve custom parameters, which override the changer's.
- Use Loop Type = Zigzag with a counter or LFO to ping-pong through the scenes.
- The component re-derives its state from the network when its extension reloads, so a
  code edit or reinit mid-transition cannot leave a scene cooking forever.
- Unload never touches locked operators, so a frozen (locked) TOP inside a scene survives.

## What the Pro package adds

The full manual for both builds, with every parameter, lives on the product site: https://simplescenechanger.vercel.app/
