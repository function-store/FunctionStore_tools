---
package: FNS_MainMenuRegistry
summary: 'TD main-menu surface registry, including project-name display. The raw master, promoted to /sys.'
features:
  - name: Main Menu Registry
    anchor: main-menu-registry
---

## Main Menu Registry

The raw registry that manages TouchDesigner's main-menu bar as a single surface: order, visibility and left/right placement of every entry -- both TD's own built-in items (wiki, forum, tutorials, fps, etc.) and the ones tools publish -- live here, not in ad-hoc per-widget parameters.

It ships as its own core package, promoted to `/sys` (global shortcut `op.FNS_MAINMENUREGISTRY`), one of the toolkit's six core registries. A tool that wants a main-menu entry -- for example [BorderlessTD](/docs/borderlesstd/)'s project-name display, or [FNS_MainMenu](/docs/fns-mainmenu/)'s own Configurator gear -- ships a small host copy of this registry alongside its widget. You don't interact with the registry directly: open the [Main Menu Configurator](/docs/fns-mainmenu/#main-menu-configurator) (the gear icon in the bar) to reorder, hide or group entries.
