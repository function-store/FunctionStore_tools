---
package: OpenExt
summary: Press Ctrl+E on a COMP to open its promoted extension in your external editor.
features:
  - name: OpenExt
    anchor: openext
---

## OpenExt

Put the cursor on a COMP that has a **promoted extension** and press `Ctrl+E`
(`Cmd+E` on macOS): the extension's Python opens in your external editor,
straight from the network editor.

It saves the dive you would otherwise do a hundred times a day on the
component you are actively writing: into the COMP, find the extension DAT,
open it.

It acts on the **current** operator in the active pane, and only on a COMP. If
the component has several extensions it opens the first one marked *Promote*;
if it has none, nothing happens, so the key is safe to lean on while moving
through a network.

Opening is done by pulsing that DAT's own **Edit** parameter, which means the
file lands in whichever external editor TouchDesigner itself is set to use.
This tool has no editor setting of its own to get out of step with it.

For the full round trip, editing outside and syncing the changes back, see
[VSCodeTools](/docs/vscodetools/); the two tools sit alongside each other.

It is also published as a quick-launch command, **Open extension of current**,
so you can fire it from [FNS_CommandKit](/docs/fns-commandkit/) without the
hotkey.
