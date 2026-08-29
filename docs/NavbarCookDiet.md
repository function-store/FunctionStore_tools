---
status: open
summary: What the navbar/HydroHomie cook audit landed, why the containers/* freeze was reverted (it cost the navbar its whole installation for 2 operators), and parent_hierarchy's always-cook hover chain -- awaiting a hand test against a live control.
since: 2026-08-24 (branch cook-diet)
skill: fns-registry
---

# Navbar cook diet -- landed, and what is left

An audit of what the toolkit costs per frame while nobody is using it.
Numbers below are measured on `FunctionStore_tools_2025_DEV`, 4 pane bars,
60 fps (16.7 ms budget).

## Method, so the numbers can be reproduced

Cook *counts*, not cook *times*: `OP.totalCooks` snapshotted, then diffed over
a few hundred frames. `cpuCookTime` is a decaying rolling average and reads
high right after load, so it is useful for ranking and misleading as a total.
An operator "cooks every frame" when its delta matches the frame delta.

## Landed

| Fix | Effect |
|---|---|
| `OpTemplates/kindergaertner_mymod` observer walks immediate children, keyed by `OP.id` | 5.573 ms -> 0.009 ms per pass (623x); rename no longer fires a phantom create+delete |
| ~~`FNS_Navbar/containers/*` master templates frozen (`allowCooking`)~~ **REVERTED -- see below** | was 28 ops -> 0 |
| `PathCellClickInject/press` time-slicing gated by its panel execute, stopped 12 frames after release | 48 ops -> 0 across 4 bars |
| HydroHomie: disabling the reminder now takes `display` down with it | 0.55 ms -> 0.014 ms |

Navbar total: **112 -> 64 always-cooking operators** across four bars.

## Two invariants worth not re-learning

- **`allowCooking` can only be disabled on COMPs.** Setting it on a CHOP/DAT/TOP
  raises. This is why the press gate works (`press` is a baseCOMP) and why
  HydroHomie's LFO could not be gated the same way.
- **`allowCooking` is not inherited.** Freezing a parent container buys nothing;
  the flag has to go on each operator that should stop.
- **Reach for `timeslice` before `allowCooking`.** Time-slicing is usually the
  only thing in a widget cooking on its own, and it is a parameter, not a
  teardown. `press` was gated by flipping `allowCooking` on the whole COMP,
  which destroyed and rebuilt all 14 of its operators on every press to stop
  two of them -- coarse, and a hitch you can feel. Measured with the COMP awake:
  9 of 14 cooked every frame (the two Time-Sliced Speed CHOPs plus the seven
  they pull); `timeslice = False` on just those two took it to **1 cook in 505
  frames** with `allowCooking` left ON. The integrator still works when it is
  switched back on -- `State_long_fract` climbs 0.05 -> 1.0 over 23 frames at
  0.333s -- so the behaviour is unchanged. Verified across all 4 bars: **0
  always-cooking operators of 140**.
- **Never freeze a COMP that carries a registry host.** A host whose COMP comes
  up `allowCooking = False` cannot compile its extension at load, so it never
  registers -- and everything downstream is silently absent. Freezing the three
  `containers/*` masters cost the navbar its entire installation: all three were
  missing from the registry and from all 7 bars, while their `Regstatus` still
  read `Registered: ...` from the string saved in the tox. Once cooking is back
  on, the extension initializes, registers, and the next sync injects into every
  bar with no other change. (An already-compiled extension keeps working if you
  freeze it afterwards -- it is the *load* path that breaks, which is why this
  survives a session and only bites on the next open.)

## Why the container freeze was reverted

It was measured against a `parent_hierarchy` that had not yet had its flag work
(`cooktype = selective`, `timeslice` off, `chopexec5` inactive). With that
applied to the master, the freeze is no longer buying what the 28 in the table
says. Re-measured over 328 frames across all **416** operators under
`containers/`, with every container cooking:

**2 always-cooking operators** -- `hijack_dragdrop/null1` and
`parent_hierarchy/popMenu_bar/logic1`. Both are CHOPs, so `allowCooking` cannot
be set on them anyway (see the invariant above); 2 ops is the floor.

Trading the navbar's entire installation for 2 operators is not a trade, so the
masters cook. `PathCellClickInject/press` stays frozen -- it is a baseCOMP, it
is gated by its own panel execute, and it is not in a host's parent chain.

## Open: parent_hierarchy's hover chain

60 of the remaining 64 ops are `parent_hierarchy`, 15 per bar: four
`cooktype = always` nulls, three Time-Sliced logic CHOPs, two maths, a feedback
CHOP, and four chopexecs holding the whole thing in permanent demand. The
inputs are event-driven (a Panel CHOP on `../panenav/path`, plus hotkeys) -- so
the per-frame cooking comes from the flags, not from the work.

**Measured on a live bar:** setting the four nulls to `cooktype = selective`,
`timeslice` off on `logic1/logic2/logic5`, and `chopexec5` inactive took the
widget from 15 always-cooking ops to **0** (2 cooks in 359 frames), with no
errors. Disabling `chopexec5` is what silences `feedback1` -- a Feedback CHOP
cooks every frame for as long as anything demands it, and that chopexec was the
only consumer. Its own comment reads *"legacy in-bar placement only -- absent at
the mirror-scheme source"*, which is why it is a candidate at all.

Rolled out, that is **112 -> ~8 ops** for the whole navbar.

**Status: applied and awaiting a hand test.** It is on the master
(`FNS_Navbar/containers/parent_hierarchy`) and on **pane1's instance only**;
pane2, pane5 and `panebar_default` were deliberately left on the original flags
so there is a live control to compare against. pane1 measured **0
always-cooking operators over 3189 frames**, no errors.

The master carries it because `_injectItem` re-copies an instance whenever its
stored `nbsrc` does not match the source's `OP.id` -- and ids are reassigned on
reload, so a pane-only edit is silently wiped the next time the project opens.
Master + no `RefreshWidget` gives both: the A/B holds for now, and a reload
re-stamps every bar from the modified master.

### The hand test

In **pane1** (a NETWORKEDITOR pane -- never test this on a Textport pane, they
show no breadcrumb), against **pane2** as the control:

1. breadcrumb segments highlight on hover;
2. clicking a segment navigates to that parent;
3. the highlight clears when the mouse leaves -- **this is the `chopexec5` half**;
4. any hotkey+hover combo still fires.

If only (3) fails, re-enable `chopexec5` on the master and re-stamp; it costs 2
ops/bar back and keeps the rest. If (1) or (2) fails, the flags are
load-bearing -- revert the master to `cooktype = always` / `timeslice` on /
`chopexec5` active, then `RefreshWidget('ParentHierarchy')`. If all pass,
`RefreshWidget('ParentHierarchy')` rolls it to every bar immediately.

## Also open, deliberately deferred

- **Non-editor panes carry a full navbar.** A Textport pane was running 16
  ops/frame for a breadcrumb it never displays. Gating the registry so it skips
  pane types with no breadcrumb saves the whole per-bar cost on each one.
- **`panebar_default`** is TD's prototype bar and cooks like a live one (16
  ops). Freezing it is easy, but a newly created pane copies it and would come
  up frozen -- so it needs the pane-creation path checked first.
- **HydroHomie's floor** is `lfo1` + `timer1`, about 0.014 ms. An LFO CHOP is
  unconditionally time-dependent (928/931 frames with play off *and* viewer
  off), `allowCooking` will not take on a CHOP, and bypassing it starves the
  crossCHOP expressions into a TypeError. Not worth further surgery.
