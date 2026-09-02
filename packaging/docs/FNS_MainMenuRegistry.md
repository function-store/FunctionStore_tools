---
package: FNS_MainMenuRegistry
summary: 'TD main-menu surface registry, including project-name display. The raw master, promoted to /sys.'
features:
  - name: Main Menu Registry
    anchor: main-menu-registry
---

## Main Menu Registry

The raw registry that manages TouchDesigner's main-menu bar as a single surface: order, visibility and left/right placement of every entry, both TD's own built-in items (wiki, forum, tutorials, fps, etc.) and the ones tools publish, live here in one place.

It ships as its own core package, promoted to `/sys` (global shortcut `op.FNS_MAINMENUREGISTRY`), one of the toolkit's six surface registries, which together with [FNS_Console](/docs/fns-console/), [FNS_Hub](/docs/fns-hub/) and [FNS_Updater](/docs/fns-updater/) make up the always-installed core. A tool that wants a main-menu entry, for example [BorderlessTD](/docs/borderlesstd/)'s project-name display or the hub's own **FNS** button, ships a small host copy of this registry alongside its widget. You don't interact with the registry directly: open the **MainMenu** tab of [FNS_Hub](/docs/fns-hub/#the-tabs) (the FNS button in the bar) to reorder, hide or group entries, TD's own items included.
