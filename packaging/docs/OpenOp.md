---
package: OpenOp
summary: 'A one-button shortcut to a deeply nested operator: drop the operator on it once, then a pulse opens its parameter window, its viewer window, or both.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Parameters
    anchor: parameters
---

## What it is

Some operators matter and sit six levels deep. OpenOp keeps a reference to one of them where you can reach it: drag the operator onto the Op field, tick which windows you want, and the Open pulse brings them up from wherever you are in the network. Place one beside a control panel, or several in a small dashboard, and the important nodes are one click away.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Parameters

### Custom

- **Op** (OP): the operator to open, or several separated by spaces. Drag from the network onto the field; names resolve from OpenOp, so a sibling is a bare name and a child of OpenOp is `./name`.
- **Parwindow** (Toggle): open the operator's parameter window.
- **Viewerwindow** (Toggle): open the operator's viewer window.
- **Open** (Pulse): open the windows ticked above.

### Info

- **Open2** (Pulse): opens the readme inside the component.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
