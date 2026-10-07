---
package: FNS_Misc
summary: 'Two toolbar utilities: a global Mouse CHOP to drive interaction, and a toggle for the network backdrop.'
features:
  - name: Global Mouse CHOP
    anchor: global-mouse-chop
    icon: QuickMouse.png
  - name: Background Viewer
    anchor: background-viewer
---

## Global Mouse CHOP

A handy tool for quick interaction tests: a global **Mouse In CHOP** whose
channels you can drag straight out of the popup and drop onto parameters,
with no operator to place first.

## Background Viewer

A toolbar toggle for the current pane's backdrop viewers: TOPs and CHOPs drawn
behind the network, on or off in one click. Right-clicking it turns off the
display flag on every TOP in the network you are in, which is the fast way back
from a pane full of previews.

Both live on the toolbar. Which widgets sit on the bar, in what order, and
which are shown is up to
[ToolbarRegistry](/docs/fns-toolbarregistry/).

The Global Hog CHOP that used to sit here moved to
[CookBar](/docs/cookbar/): Ctrl+right-click its toolbar button.
