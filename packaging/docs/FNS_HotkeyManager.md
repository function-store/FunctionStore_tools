---
package: FNS_HotkeyManager
summary: 'Allows for externalized toolkit hotkeys:'
features:
  - name: HotkeyManager
    anchor: hotkeymanager
---

## HotkeyManager

A lister UI for discovering, rebinding and de-conflicting hotkeys across the whole project, not just the toolkit. Pulse `Open UI` on the component to open it.

   - **Discovery** scans every top-level component (except `ui`/`sys`/`local`) for hotkey-bearing `keyboardin` CHOPs/DATs and custom parameters named like a shortcut, and lists them one row per binding: Tool, Path, Par, Hotkey, Default, Persist, Status.
   - **Click a Hotkey cell** to capture a new binding (press the keys; `Esc` cancels). If the combo is already used elsewhere, the row asks for confirmation; press the same keys again to force it.
   - **Right-click a Hotkey cell** to reset that binding to its default.
   - **Conflicts** (the same combo bound by more than one tool) are flagged in the Status column; clicking a conflicted row's status jumps to (and cycles through) the other row(s) sharing that combo.
   - **Persist column**: toolkit hotkeys always persist. A hotkey outside the toolkit only persists across projects/updates if declared: tag its `keyboardin` (or a COMP containing it) `FNS_hotkeys`, or use the Persist cell to toggle it. Declared bindings are externalized into your user palette via [FNS_ConfigRegistry](/docs/fns-configregistry/) and restored on load; project-local bindings never persist.
   - `Save`/`Load`/`Load Default` pulses (and a `Force Default` toggle) are also exposed as the component's own custom parameters.
