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

## Search behavior

Matching goes beyond the original module's prefix search:

- **Substring, case-insensitive** — `blur` finds `hsvBlur`, `radialBlur`
  and `barrel_blur`, not just names that start with it.
- **Multiple words AND together** — `audio an` finds `audioAnalysis`.
- **Ranked results** — exact matches first, then names starting with the
  query, then everything containing it, alphabetical within each group.
- **Wildcards still work** — a word carrying `*` or `?` is matched as a
  pattern (`audio*` = classic prefix search).
- **Folder search** — a word containing `/` matches the palette *folder*
  instead of the name: `gen/ noise` finds `noise` in the Generators
  folder, and `tools/` alone lists a whole folder. Toggleable via the
  **Folder Search** parameter.
- **Latest version only** — numbered copies of one component (`tool`,
  `tool1`, `tool2`, or the same name in two folders) collapse to the
  latest-modified file. Toggleable via the **Latest Version Only**
  parameter.
