---
package: "tools_ui"
summary: "Clicking this will open a collection of tools that have some minimal user interface."
features:
  - name: "tools_ui"
    anchor: "tools-ui"
    icon: "Fx.png"
  - name: "op_store"
    anchor: "op-store"
  - name: "Olib Browser"
    anchor: "olib-browser"
    icon: "Olib.png"
credit: {name: "AlphaMoonbase.berlin", url: "https://alphamoonbase.de/"}
---

## tools_ui

Clicking this will open a collection of tools that have some minimal user interface. They are accessible through the UI tabs. 
**Right-Clicking** on the tabs will open further customization of the respective tool *(very important for midi/oscMapper configuration)*.
The tabs can also be re-ordered by drag-dropping, and you can also add new tabs easily by parenting a container to `/FunctionStore_tools/tools_ui`.

## op_store

This component is a modified version of `AlphamoonBase.berlin`'s [Operator Store](https://td-olib.org/component/operator-store). You can drag and drop any operator or component from your network to this UI.
After that you can reference the dropped OP/COMP with a **Shortcut** of the Shortcut column.

The tool itself has a global shortcut of `STORE`, so drag-and-dropping a `KinectCHOP` named `kinect1` from `/SENSORS/KINECT/kinect1` onto the UI, you can easily reference that operator as follows:** `op.STORE.Kinect`
You can also drag and drop from the operator column onto your network editor to place a **Select OP **of the OP! You can also use the buttons on the right to:** open a viewer, open parameters, open a floating network at the referenced operator location.

This tool is a good way to keep clean references to project-wide operators, similar to Global OP Shortcuts, but for operators; or `iop`s for the whole project.

If enabled in the `FunctionStore_tools` base custom parameters, the contents of the table will be externalized to the project folder.

> **BEWARE:** Moving the referenced operator to a different location will break the references, and you'll have to manually update the `store_table` inside the component.

## Olib Browser

Opens the [Olib Browser](https://td-olib.org/) by AlphaMoonbase.berlin. You can browse and directly place tons of very useful components to your network.
