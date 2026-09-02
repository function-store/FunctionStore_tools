---
package: QuickPane
summary: 'Peek into a COMP without splitting panes by hand: hold the modifiers and drag, or press an arrow shortcut.'
hotkeys:
  - keys: ctrl.shift.left ctrl.shift.right ctrl.shift.up ctrl.shift.down
    does: Split the pane on that side and open the selected COMP in it; press again to close it
features:
  - name: QuickPane
    anchor: quickpane
---

## QuickPane

This component lets you quickly peek into COMPs without manually splitting
panes and navigating into them.

Select a COMP and hold `Alt+Ctrl+Shift` (`Cmd+Ctrl+Shift` on macOS), then
drag your mouse in the direction you want the split. A new pane opens on that
side, already inside the COMP and homed. To close it, hold the same keys and
drag in the same direction again.

The same thing on the keyboard: with a COMP selected, `Ctrl+Shift+Left`,
`Right`, `Up` or `Down` splits on that side and drops you into the component;
the same key again closes the pane it opened. Nothing happens unless the
current operator is a COMP, so the keys are safe to lean on.

How much of the pane the new split takes is the **Ratio** parameter: the
first value for a horizontal split, the second for a vertical one.

It is also a quick-launch command, **Split pane**, which asks for the direction
and defaults to right, so it can be fired from
[FNS_CommandKit](/docs/fns-commandkit/) or the palette without either gesture.
