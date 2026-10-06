---
package: ParHoverMIDI_VSN1
summary: 'Adjust any parameter by hovering over it and turning an endless MIDI encoder, built for the Intech Studio VSN1 with screen and LED feedback: slots and banks, ParGroup control, step sizes, shortcuts, and network zoom when nothing is under the mouse.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Before you install
    anchor: before-you-install
  - name: Setup
    anchor: setup
  - name: Updates
    anchor: updates
---

## What it is

Hover the mouse over a parameter, twist an encoder, and the parameter follows. ParHoverMIDI_VSN1 is a hardware integration for the Intech Studio VSN1: the device's screen shows the parameter under the mouse, its LEDs show state, and its buttons switch step size, save the hovered parameter to a slot for instant recall across banks, and run shortcuts for reset, default and clamp. Parameter groups (RGB, XYZ) turn as one. With no parameter under the mouse the encoders zoom and pan the network editor. Any endless relative MIDI encoder works for the core hovering; the screen and LED feedback are VSN1 features.

It is a foreign package: its releases come from its own repository, and its built-in updater keeps it current from there. The store places it; the component governs itself afterwards.

## Before you install

- It lands at the network root, one instance per project, and only one project open at a time (the Grid connection is exclusive).
- It is never part of Select all, the Everything preset or a recommended set. Pick it yourself when you have the hardware.
- Requirements: TouchDesigner 2023.12120 or later (2025 for ParGroup control), a USB MIDI connection, and for the VSN1 the Grid Editor open with exclusive access to port 9642.

## Setup

1. Install the `TouchDesigner Par Hover Control` package in Grid Editor (Package Manager on recent versions) and import its configuration to the VSN1.
2. In TouchDesigner's MIDI Device Mapper set the VSN1 (Intech Grid MIDI Device) as input and output, and note the Grid device ID.
3. Enter that ID on the component's VSN1 / UI parameter page.
4. Hover a parameter and turn an encoder. Step size from the buttons under the screen, slots by long-pressing the primary buttons, banks by long-pressing the step buttons. Hold Alt (Option on Mac) over any custom parameter for its help.

The full documentation, including other controllers and the recovery system, is at the upstream docs site linked on this page.

## Updates

The component's About page checks GitHub releases and updates itself in place. Pressing Externalize Component there before updating keeps your slot data across updates. The FNS updater reports it as self-managed and does not replace it.
