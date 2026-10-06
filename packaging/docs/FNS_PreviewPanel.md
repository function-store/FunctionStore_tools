---
package: FNS_PreviewPanel
summary: 'A preview pane for whatever you drop on it: TOPs, POPs, SOPs, 3D textures, geometry, panels and other components render in place, and a POP can be opened as a live table or in its own viewer window.'
features:
  - name: PreviewPanel
    anchor: previewpanel
  - name: What you can drop
    anchor: what-you-can-drop
  - name: POP viewer and POP to DAT
    anchor: pop-viewer-and-pop-to-dat
---

## PreviewPanel

PreviewPanel is a pane type. Open one from the pane bar's type menu, where it
registers itself as **PreviewPanel**, then drag any operator onto it. What
lands there is shown the way it should be seen: a TOP as an image, geometry
rendered through a camera viewport you can orbit, a panel as itself, a POP as
points with its attributes one click away. Its command, *Open preview panel*,
opens the POP window from any command palette.

The pane keeps only one thing between drops, the operator it is showing, and
sheds even that when the package is shipped, so an installed copy never points
into the project it was authored in.

## What you can drop

| Dropped | Shown as |
|---|---|
| A TOP | The image, through a fit and a checkerboard background |
| A Render TOP | Its own render settings, adopted by the pane's render chain, seen through the pane's camera viewport |
| A 3D texture | Rendered on a surface through its own camera viewport |
| A POP | Rendered as geometry, with the POP viewer and the POP-to-DAT table available |
| A SOP | Rendered as geometry |
| A Geometry COMP | Rendered through the pane's camera viewport |
| A panel COMP | The panel itself, live |
| Another COMP with an operator viewer | That viewer |
| Anything else | The operator's own viewer |

## POP viewer and POP to DAT

The POP half has two modes. Viewer mode shows the points; POP-to-DAT mode
turns the POP into a table you can read attribute by attribute, and lets you
pick which attributes to convert. Either mode can pop out into its own window,
and the pane registers a second pane type, **PopViewer**, so the viewer can
live in a pane of its own. Cooking is switched on only for what is visible:
a closed window or a hidden mode costs nothing.
