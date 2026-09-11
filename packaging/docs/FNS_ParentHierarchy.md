---
package: FNS_ParentHierarchy
summary: Hover a parent in the pane-bar path with Alt to see its shortcuts, internal operators and parameters, and click any of them to copy a reference.
features:
  - name: Parent Hierarchy
    anchor: parent-hierarchy
  - name: Extensions
    anchor: extensions
---

## Parent Hierarchy

![](/docs/assets/icons/ParentHierarchy.png)

Hovering over individual elements in the navigation path bar and holding `Alt`
will show the **Parent Shortcut** (`P`), **Global Shortcut** (`G`) and **Internal
Operators** (`iop`) for that COMP only.

Furthermore holding `Ctrl` will show the relative path of the `iop` target as well
as all custom parameters and their values. You can hit `Ctrl` again to poll the
values.

- Clicking on any of the items will copy a reference to that object
- You can then paste this to any expression or script
- Right-Clicking on any of the parameters will open the parameter customization
  window of that param

This tool adds **no button** to the pane bar. It reads the path that is already
there, so the bar stays exactly as long as it was.

With [iopBrowser](/docs/fns-iopbrowser/) installed, the same hover also lists the
internal operators in its browser. Without it the hover works exactly as
described above, it simply does not reach the browser.

> The **Navbar** tab of [Hub](/docs/fns-hub/) (the **FNS** button in the main-menu
> bar) manages what else lives on the pane bar: reorder items, flip an item
> between the left/right side, show/hide it, and drop any panel COMP on the FNS
> button to register it as its own self-installing navbar package.

## Extensions

Each COMP in the hover list also shows its extensions, as `E1:`, `E2:` and so on.
The label is the **Extension Name** parameter when one is set, because that is
what `.ext.<Name>` resolves by, and it is often different from the class. With no
name set you get the class name, which is the only thing left to call it by.

**Hover an extension row and it expands**, listing the API TouchDesigner promotes
to the COMP: methods with their signature, properties, and attributes with their
type. Move off the row and it folds away again.

Capitalized class constants are left out. TouchDesigner promotes those too, but
they are a tool's own bookkeeping rather than something you call, and listing
them buries the methods you came for. The same goes for the accessors
CustomParHelper generates for each parameter: one row per parameter is not an
API, and on a tool with forty of them it is all you would see.

Clicking copies a reference you can paste straight into an expression or a
script: an extension row gives `ext.TimelineToolsExt`, and a member gives
`ext.TimelineToolsExt.AcceptsDrop(items)` with the signature intact.

The `ext.` form works whether or not the COMP sets an Extension Name, because
TouchDesigner registers an extension under that name when there is one and under
its class name when there is not, which is exactly what the row is labelled
with.

Members are read off the class and the instance dictionary, never by fetching
each attribute, so listing an extension cannot trigger a capitalized property and
run somebody else's code as a side effect of hovering.
