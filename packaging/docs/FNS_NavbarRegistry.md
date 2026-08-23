---
package: FNS_NavbarRegistry
summary: 'The pane-bar surface registry. The raw master, promoted to /sys -- clone it to add your own pane-bar widgets.'
features:
  - name: Navbar Registry
    anchor: navbar-registry
  - name: For tool authors
    anchor: for-tool-authors
---

## Navbar Registry

The raw registry behind the [FNS Navbar](/docs/fns-navbar/) mods: which widgets
appear in TouchDesigner's pane bars, their order, which side they sit on, and
whether they are shown.

A pane bar is not one object -- TD gives every pane its own, plus a default used
for new ones. The registry handles that for you: registered entries are stamped
into the default pane bar and into each live pane bar, so a widget you add shows
up in every pane and in panes you open later.

It ships as its own core package -- always installed, never optional --
promoted to `/sys` with the global shortcut `op.FNS_NAVBARREGISTRY`.

As a user you interact with the **Navbar** tab of [FNS_Hub](/docs/fns-hub/)
(the FNS button in the main-menu bar), where you reorder items, flip one
between the left and right side, and show or hide it. The layout roams with
your config through [FNS_ConfigRegistry](/docs/fns-configregistry/).

## For tool authors

A tool that wants a pane-bar widget ships a host copy of this registry and
registers on load. Dropping any panel COMP on the FNS button registers it as
its own self-installing navbar package.
