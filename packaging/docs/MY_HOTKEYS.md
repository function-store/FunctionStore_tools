---
package: MY_HOTKEYS
summary: "There's a ton of hotkeys documented on each tool's own doc page, but here are some that might be not:"
features:
  - name: Hotkeys
    anchor: hotkeys
  - name: TDX_SearchPalette
    anchor: tdx-searchpalette
---

## Hotkeys

There's a ton of hotkeys documented on each tool's own doc page, but here are some that might be not:
- **Ctrl+Alt+W (Ctrl+Option+W for Mac):** Opens **Parent Component Editor**.
- **Ctrl+Alt+Q (Ctrl+Option+Q for Mac):** Opens **Parent Parameters**.
- **Shift+Alt+W (Mac: Shift+Option+W):** Opens **Selected COMP's Editor**.
- **Shift+Alt+Q (Mac: Shift+Option+Q):** Opens **Selected COMP's Parameters**.
- **Ctrl+Shift+F (Mac: Cmd+Shift+F):** Palette Search
- **Ctrl+0 (Mac: Cmd+0)**: Pulses [Global ResetPLS](/docs/resetpls1/#global-resetpls)

## TDX_SearchPalette

`ctrl+shift+F` focuses the search field that [TDX_SearchPalette](/docs/tdx-searchpalette/) installs into the Palette browser — an optional package, vendored from [Yea Chen's TD-SearchPalette](https://github.com/yeataro/TD-SearchPalette). The hotkey feature-detects the installed field, so it stays quiet if TDX_SearchPalette isn't installed.
