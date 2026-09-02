---
package: FNS_PaletteRegistry
summary: 'Contribute tabs to TouchDesigner''s Palette Browser: a tool publishes a native panel COMP and it appears beside the stock Palette tab, sized to the slot and notified on every tab change.'
features:
  - name: Palette Registry
    anchor: palette-registry
  - name: For tool authors
    anchor: for-tool-authors
  - name: Several tabs from one tool
    anchor: several-tabs-from-one-tool
---

## Palette Registry

TouchDesigner's Palette Browser leaves a 32 px strip free above its component
list, exactly a folder-tab row. This registry puts a tab strip there: TD's own
*Palette* first, then one tab per contribution, each showing a panel from the
tool that published it.

Nothing stock is copied, moved or re-expressed. The registry loads TD's own
`folderTabs` widget into the free row and shows each contributed panel through a
Select COMP mirror; the stock panels only get their display flag toggled while a
contributed tab is in front. `/ui` is never saved with a project, so the whole
surface is rebuilt on every load.

It ships as its own core package, promoted to `/sys` (global shortcut
`op.FNS_PALETTEREGISTRY`), alongside the other surface registries.

**With nothing contributed it claims nothing at all**: no strip, no mirrors, an
untouched palette dialog. The surface appears with the first registration and
disappears with the last.

## For tool authors

A tool that wants a palette tab ships a small **host** copy of this registry,
the same shape as a toolbar or navbar entry. The host's Registration page names
the tab:

- **Tool COMP**: the contributing tool (defaults to the host's parent).
- **Canonical Name**: unique id for the tab; empty uses the tool's name.
  `palette` is TD's own tab and is rejected.
- **Tab Panel**: the panel COMP to show; defaults to the tool itself.
- **Callbacks DAT**: optional; `onPaletteTab(canonical, previous)` fires on
  every tab change.
- **Expose in Palette / Shown in Palette / Tab Label / Tab Order**: the usual
  publishing controls. *Shown in Palette* is written back to the host, so a
  hidden tab stays hidden with the tool.

From Python, `op.FNS_PALETTEREGISTRY.RegisterTab(comp, 'mytool', panel=panel,
label='My Tool', order=20)` does the same; `Tabs()`, `SetTabDisplayed()`,
`ShowTab()`, `CurrentTab()` and `UnregisterTab()` are the rest of the API.

**Your panel is resized while it is registered.** A Select COMP cannot push its
size into its source, so the registry rewrites the panel's width and height to
slot expressions and restores the originals when the tab goes away. Do not
re-point them behind its back.

The tool's panel keeps its state across tab switches, a Web Render's browser
process included, because mirrors are views of the same panel.

## Several tabs from one tool

The Registration pars define the first tab; the **Tab** sequence on the same
page adds one more per block:

- **Canonical Name**: empty means *no tab*, which is how a block stays inert
  (TouchDesigner always keeps at least one block in a sequence).
- **Tab Panel**: empty **reuses the first tab's panel**. That is how one panel
  serves several tabs: register them all, then route on `onPaletteTab`.
- **Tab Label / Tab Order / Shown in Palette**: as above.

A block with a bad or duplicate name is reported in *Registration Status* and
skipped; it never costs the tool its first tab.

## Hotkey

[TDX_SearchPalette](/docs/tdx-searchpalette/)'s `ctrl+shift+f` calls
`ShowTab('palette')` on this registry before focusing its search field; that
field lives in the stock palette list, which a contributed tab hides. Any tool
whose UI is hidden by a contributed tab can do the same.
