---
package: FNS_Toolbar
summary: The toolbar installs automatically when the component is dropped onto a project or at startup of the project.
features:
  - name: Toggle Network Grid
    anchor: toggle-network-grid
    icon: Toggle Grid.png
  - name: Toggle Background Viewer
    anchor: toggle-background-viewer
    icon: ToggleBackdrop.png
  - name: Customising the bar
    anchor: customising-the-bar
---

![](/docs/assets/icons/main.png)

The toolbar installs automatically when the component is dropped onto a
project or at startup of the project. It provides easy access to some extra
features as well as existing ones. Most of what sits on it is contributed by
other packages. Each of those is documented on its own page, and the
**Toolbar button** badge at the top of a page tells you which. Many buttons
do different things on left, right and middle click and accept drops, so it
is worth reading a button's page before assuming it is a plain button.

This package also ships two stock widgets of its own.

## Toggle Network Grid

Three toggles on one button, one per mouse button:

- **Left click** shows or hides the network editor's grid.
- **Right click** shows or hides the window's title bar, the borderless
  window that [BorderlessTD](/docs/borderlesstd/) manages.
- **Middle click** shows or hides the timeline, likewise.

## Toggle Background Viewer

Shows or hides the pane's background viewer. Handy when you have split panes
and want the operator tiles on their own.

## Customising the bar

The way to arrange the bar is the **Toolbar** tab of
[FNS_Hub](/docs/fns-hub/) (the **FNS** button in the main-menu bar): reorder,
group, hide and show widgets and add dividers between them. Drag rows in the
list; right-click a name for its docs. Drop any panel COMP on the FNS button to
register it as a toolbar package of your own. The layout is saved and follows
you across project files.

The old lower-level route, an `Open Definition` pulse onto a `ToolbarDef`
table, is gone: the registry is the definition now, and the Configurator
edits it. **Install** re-installs the bar into TouchDesigner's UI by hand; it
also happens on project start.
