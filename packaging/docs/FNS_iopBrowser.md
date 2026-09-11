---
package: FNS_iopBrowser
summary: Browse the internal operators and the OP tree of the network you are in, from a popup opened off the pane bar.
features:
  - name: iop Browser
    anchor: iop-browser
---

## iop Browser

Adds a button to the left of the path bar. Drop an operator on it to add that operator as an internal operator shortcut of the network you are in, the root included (CustomParTools asks for the shortcut name when it is installed; without it the operator's own name is used). Clicking it opens a popup listing the
`iops` available from the COMP you are currently in, which means the internal
operators of every parent, not just the nearest one.

You can drag any of them straight into your network editor, or use the list as a
quick overview and a way to navigate to them.

The popup also carries the OP tree for the network, with search, so it doubles as
a way to find an operator without leaving the pane.

**One browser, many bars.** Only the button is copied into each pane bar. The
browser itself exists once and every button calls into it, so adding panes costs
a button rather than a second browser.

Works on its own, and is opened for you by
[ParentHierarchy](/docs/fns-parenthierarchy/) when both are installed.
