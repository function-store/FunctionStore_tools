---
package: TDX_SearchPalette
summary: Search field for TouchDesigner's palette browser, installed into the palette on startup.
features:
  - name: TDX_SearchPalette
    anchor: tdx-searchpalette
  - name: Search hotkey
    anchor: search-hotkey
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

## Search hotkey

`ctrl+shift+f` (`cmd+shift+f` on macOS) brings TD's own palette tab to the
front and focuses the search field, ready to type.

It acts on the palette **in place**. It deliberately does not call
`ui.openPaletteBrowser()`, which pops the palette out into a floating window
— so if the browser is closed, the hotkey does nothing rather than rearranging
your workspace.

The tab step matters because the search field lives inside the *stock* palette
list, and any contributed tab hides that list. The hotkey asks whichever
palette-tab owner is installed to show TD's own tab again
([FNS_PaletteRegistry](/docs/fns-paletteregistry/) and TDXLU's own injector are
both feature-detected, neither required), then takes focus one frame later —
a tab switched back this frame is still hidden.

**Rebindable.** The combo lives on this package's own **Search Hotkey**
parameter, so it is listed under TDX_SearchPalette in FNS_HotkeyManager and can
be changed there or on the parameter directly; *Reset to Default* restores
`ctrl+shift+f`. It used to live in MY_HOTKEYS; keeping it with the tool that
owns the field means uninstalling this package takes its hotkey with it.

## Search behavior

Matching goes beyond the original module's prefix search:

- **Substring, case-insensitive** — `blur` finds `hsvBlur`, `radialBlur`
  and `barrel_blur`, not just names that start with it.
- **Multiple words AND together** — `audio an` finds `audioAnalysis`.
- **Ranked results** — an exact match first, then names starting with the
  query, then names where it starts a word (`blur` puts `hsvBlur` and
  `barrel_blur` above `unblurred`), then the rest, alphabetical within
  each group.
- **Wildcards still work** — a word carrying `*` or `?` is matched as a
  pattern, anchored at the front only, so a wildcard can only ever widen
  the search: `audio*` is still classic prefix search, `*fee` finds
  `feedbackGen` just like plain `fee` does, and `web*ser` finds
  `webBrowser`.
- **Exclude with `-`** — a word prefixed with a minus removes matches
  rather than requiring them: `blur -barrel` finds every blur except the
  `barrel_blur` pair.
- **Fuzzy fallback** — when nothing matches literally, each word is
  re-read as a *subsequence*, so initials find the component: `fbg` finds
  `feedbackGen`, `wbrsr` finds `webBrowser`. These only ever appear when
  the strict search came up empty, ranked tightest-match first.
- **Folder search** — a word containing `/` matches the palette *folder*
  instead of the name: `gen/ noise` finds `noise` in the Generators
  folder, and `tools/` alone lists a whole folder. Toggleable via the
  **Folder Search** parameter.
- **Latest version only** — numbered copies of one component (`tool`,
  `tool1`, `tool2`, or the same name in two folders) collapse to the
  latest-modified file. Toggleable via the **Latest Version Only**
  parameter.

The list stops at 200 rows, so a one-character query returns the 200
best-ranked components rather than the whole palette.

Clicking a folder in the tree clears the search, so the list falls back to
that folder's own contents instead of leaving a stale query in front of
what you just picked. The **X** button next to the field still clears it
without changing folder.
