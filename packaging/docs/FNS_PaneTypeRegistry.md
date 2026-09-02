---
package: FNS_PaneTypeRegistry
summary: 'Named, persistent pane-type entries for TD''s panebar: any COMP can appear in the pane-type dropdown and be recalled with configurable owner, type, window actions and callbacks.'
features:
  - name: Pane Type Registry
    anchor: pane-type-registry
  - name: For tool authors
    anchor: for-tool-authors
---

## Pane Type Registry

TouchDesigner's pane bar has a dropdown for switching a pane between Network
Editor, Geometry Viewer, Panel and the rest. This registry lets a COMP join that
list as a **named, persistent entry**: pick it from the dropdown and the pane
becomes that thing, with the owner, pane type, window behaviour and callbacks
the entry declares.

The point is that it survives. An entry is recalled by name, so the pane setup
you reach for every session is one dropdown pick away instead of a manual split,
navigate and configure each time.

It ships as its own core package, always installed,
promoted to `/sys` with the global shortcut `op.FNS_PANETYPEREGISTRY`.

## For tool authors

A tool that wants its UI available as a pane type ships a host copy of this
registry and registers on load, declaring which COMP is shown, what pane type to
use, and any window actions or callbacks that should fire on recall. Entries
appear in the dropdown for every pane, and right-clicking the pane-type menu
reaches the registered rows.
