---
package: FNS_ToolbarRegistry
summary: 'The toolbar surface registry and mirror rail. The raw master, promoted to /sys -- clone it to put your own tools on the bar.'
features:
  - name: Toolbar Registry
    anchor: toolbar-registry
  - name: For tool authors
    anchor: for-tool-authors
---

## Toolbar Registry

The raw registry behind the [FNS Toolbar](/docs/fns-toolbar/): which widgets sit
on the bar, in what order, and which of them are shown. That state lives here
rather than in per-widget parameters, which is why installing or removing a tool
never leaves a hole or a dead button behind.

It also owns the **mirror rail** -- the registry keeps TouchDesigner's own
bookmark bar (`/ui/dialogs/bookmark_bar`) in step with the registered set, so
the bar you see is a reflection of the registry rather than a pile of copied-in
button COMPs.

It ships as its own core package -- always installed, never optional --
promoted to `/sys` with the global shortcut `op.FNS_TOOLBARREGISTRY`.

You normally never touch it directly. Open the **Toolbar** tab of
[FNS_Hub](/docs/fns-hub/) (the FNS button in the main-menu bar) to reorder,
group, hide/show and add dividers between widgets; the layout is saved and
follows you across projects through
[FNS_ConfigRegistry](/docs/fns-configregistry/).

## For tool authors

A tool that wants a place on the bar ships a small **host** copy of this
registry alongside its widget and registers itself on load -- no installer
script, no editing a definition table. Dropping any panel COMP on the FNS
button stamps that host into it for you, which is the quickest way to put your
own tool on the bar.
