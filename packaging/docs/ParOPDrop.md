---
package: ParOPDrop
summary: Use this tool to create Param(Exec) CHOP/DATs inside of COMPs from their Custom Pars.
features:
  - name: ParOpDrop
    anchor: paropdrop
    icon: ParOpDrop.png
---

## ParOpDrop

Use this tool to create Param(Exec) CHOP/DATs inside of COMPs from their Custom Pars.

While being inside a COMP, drag the custom parameter of that COMP onto this toolbar button:

* **Ctrl+Alt(Opt)+DragDrop a param:** create Par CHOP in child
* **Ctrl+Shift+DragDrop a param:** create Par DAT
* **Alt(Opt)+Shift+DragDrop:** create ParExec DAT

You can also drop an **operator** on the same button to get its Execute DAT:

* **Drop a CHOP:** creates a CHOP Execute DAT watching every channel (`*`)
* **Drop a single channel:** creates a CHOP Execute DAT watching just that channel
* **Drop a DAT:** creates a DAT Execute DAT watching it

No modifier is needed here. Modifiers on a *parameter* drop choose between three
possible results; an operator drop has only one, and which channel to watch is
decided by what you dropped, with no setting involved. The new DAT is created in
the network you are looking at, already pointed at its source and with an event
turned on (Value Change for a CHOP, Table Change for a DAT) so it can fire
immediately.

Achieving the same result there are also hotkeys available when hovering over params:

* **Ctrl+Alt(Opt)+P over a param:** create Par CHOP in child
* **Ctrl+Shift+P over a param:** create Par DAT
* **Alt(Opt)+Shift+P over a param:** create ParExec DAT
