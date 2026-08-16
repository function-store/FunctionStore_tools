---
package: TDX_SearchPalette
summary: Search field for TouchDesigner's palette browser, installed into the palette on startup.
features:
  - name: TDX_SearchPalette
    anchor: tdx-searchpalette
credit:
  name: Yea Chen
  url: 'https://github.com/yeataro/TD-SearchPalette'
---

## TDX_SearchPalette

Adds a search field to TouchDesigner's palette browser, so palette
components can be found by typing instead of scrolling the folder tree.
This is [Yea Chen's TD-SearchPalette](https://github.com/yeataro/TD-SearchPalette),
vendored into the toolkit.

The component installs itself into the palette on project start while
**Auto Install** is on (the toggle roams with your config), and can be
installed or removed at any time with the **Install** / **Uninstall**
pulses on its parameters.

With [MY_HOTKEYS](/docs/my-hotkeys/) installed, `ctrl+shift+f` focuses the
palette search field directly. The hotkey feature-detects the installed
field, so it simply stays quiet when TDX_SearchPalette is absent.
