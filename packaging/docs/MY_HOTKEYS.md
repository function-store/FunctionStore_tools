---
package: MY_HOTKEYS
summary: "There's a ton of hotkeys documented on each tool's own doc page, but here are some that might be not:"
features:
  - name: Hotkeys
    anchor: hotkeys
---

## Hotkeys

There's a ton of hotkeys documented on each tool's own doc page, but here are some that might be not:
- **Ctrl+Alt+W (Ctrl+Option+W for Mac):** Opens **Parent Component Editor**.
- **Ctrl+Alt+Q (Ctrl+Option+Q for Mac):** Opens **Parent Parameters**.
- **Shift+Alt+W (Mac: Shift+Option+W):** Opens **Selected COMP's Editor**.
- **Shift+Alt+Q (Mac: Shift+Option+Q):** Opens **Selected COMP's Parameters**.

These four are plain TouchDesigner conveniences — they call nothing but TD's own
`openParameters()` and `openCOMPEditor()`, so this package depends on no other
tool and works on its own.

Hotkeys that *drive a tool* live with that tool instead, where FNS_HotkeyManager
still finds them and uninstalling the tool takes its hotkey with it:

- `ctrl+shift+f` — palette search, now on
  [TDX_SearchPalette](/docs/tdx-searchpalette/).
- `ctrl+0` — Global ResetPLS, now on [ResetPLS1](/docs/resetpls1/#global-resetpls).
