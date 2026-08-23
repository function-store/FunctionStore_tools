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

`ctrl+shift+F` opens TouchDesigner's Palette Browser, brings its own tab to the front, and focuses the search field that [TDX_SearchPalette](/docs/tdx-searchpalette/) installs there — an optional package, vendored from [Yea Chen's TD-SearchPalette](https://github.com/yeataro/TD-SearchPalette).

All three steps matter: focusing a field inside a closed browser puts the caret where you cannot see it, and the search field lives inside the *stock* palette list, which any contributed tab hides. So the hotkey opens the browser, asks whichever palette-tab owner is installed ([FNS_PaletteRegistry](/docs/fns-paletteregistry/) and TDXLU's own injector are both feature-detected) to show TD's tab again, and only then takes focus — one frame later, since a browser opened this frame has not laid itself out yet.

The field itself is feature-detected too: without TDX_SearchPalette the hotkey still opens the palette, and says so in the textport rather than failing silently.
