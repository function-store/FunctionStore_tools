---
package: FNS_Misc
summary: 'Two global test CHOPs on the toolbar: a Hog to stress your network and a Mouse to drive interaction.'
features:
  - name: Global Hog CHOP
    anchor: global-hog-chop
    icon: HogCHOP.png
  - name: Global Mouse CHOP
    anchor: global-mouse-chop
    icon: QuickMouse.png
---

## Global Hog CHOP

Quick stress-testing for a network. The toolbar button opens the parameter
window of a global **Hog CHOP** so you can switch it on, dial in how much of
the frame it eats, and watch how the rest of your patch copes when it is
starved of cook time.

## Global Mouse CHOP

A handy tool for quick interaction tests: a global **Mouse In CHOP** whose
channels you can drag straight out of the popup and drop onto parameters,
with no operator to place first.

## Background Viewer

A toolbar toggle for the current pane's backdrop viewers: TOPs and CHOPs drawn
behind the network, on or off in one click. Right-clicking it turns off the
display flag on every TOP in the network you are in, which is the fast way back
from a pane full of previews.

All three live on the toolbar. Which widgets sit on the bar, in what order, and
which are shown is [ToolbarRegistry](/docs/fns-toolbarregistry/)'s business, not
theirs.
