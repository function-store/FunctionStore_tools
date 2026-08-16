---
package: FNS_MainMenu
summary: 'Main-menu extras: the menu Configurator UI.'
features:
  - name: Main Menu Configurator
    anchor: main-menu-configurator
---

## Main Menu Configurator

Click the gear (`Configure`) icon at the right end of TouchDesigner's main-menu bar to open the Main Menu Configurator.

- Lists every entry with **Name / Side / Show / Group / Origin** columns. TD's own built-in items (wiki, forum, tutorials, startstop, fps, gpuUsage, realtime, stringfield, OpFamUI, update) are adopted into the list too, so your own entries can be ordered between them -- the topbar's "Show TouchDesigner's own menu-bar items" button can right-click-restore their original order.
- Toggle **Show** to hide/show an entry without unregistering it.
- Select rows and use the topbar buttons to **Group** them into a collapsible bracket or **Ungroup** a selection (members stay put).
- **Refresh** re-reads the registry and rebuilds the list.
- Drag any panel COMP onto the gear to register it as a new, self-registering main-menu entry.
