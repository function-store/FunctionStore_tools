---
package: FNS_Hub
summary: 'The FNS button in the main-menu bar and the one-stop manager window behind it: every surface configurator, the console, and any tab a tool contributes.'
features:
  - name: The FNS button
    anchor: the-fns-button
  - name: The tabs
    anchor: the-tabs
  - name: Drop to register
    anchor: drop-to-register
  - name: Contributing a tab
    anchor: contributing-a-tab
---

FNS_Hub is the one place to manage the toolkit from inside TouchDesigner. It
puts an **FNS** button at the right end of the main-menu bar and, behind it, a
window with a tab per concern: the Toolbar, Navbar and Main Menu configurators
(the per-bar gear buttons are gone; this is where they went), the web
console, and whatever else a tool decides to show. It is a core package: a
root that has the registries has the hub.

## The FNS button

| Gesture | What happens |
|---|---|
| **Left-click** | opens the hub on the tab you were last on |
| **Right-click** | a menu: every tab, then the console's *Settings* and *Install & remove* pages |
| **Drop a panel COMP on it** | registers it into a surface; see [Drop to register](#drop-to-register) |

From Python, `op.FNS_HUBREGISTRY.Open()` opens the hub; `Open(tab='navbar')`
lands on a tab by its canonical name (`toolbar`, `navbar`, `mainmenu`,
`console`, or a contributed one). The quick-launch palette offers *Open FNS
Hub* and *Open main-menu configurator*.

## The tabs

- **Toolbar**: reorder, group, hide/show and add dividers between the
  widgets on TD's bookmark bar; drag rows, right-click a name for its docs.
- **Navbar**: the pane bars: reorder, flip an item between the left and
  right side, show/hide, group.
- **MainMenu**: the main-menu bar, TD's own items included, so your entries
  can sit between them; the *TD* button restores TD's original order.
- **OpMenu**: what the tools contribute to TD's OP Create dialog (search
  words, row decorations, right-click items, filters): reorder them, switch
  a contribution off without uninstalling its tool.
- **Console**: the toolkit's web front (settings, install & remove, tabs
  tools contribute) rendered inside the hub; its browser only runs while
  this tab is shown.
- **Commands**: every command the command registry serves, hidden ones and
  TouchDesigner's built-ins included, with its tool and context; star and
  hide from here, and your choice beats the tool's default. Contributed by
  [FNS_CommandPalette](/docs/fns-commandpalette/).
- **Tool tabs**: the larger tool UIs that used to live in the `Fx`
  tools panel: oscMapper, ExprHotStrings, GlobalOutSelect, SearchWords
  (FNS_OpMenu's keyword table), midiMapper and OpColor (ColorUI's palette
  editor). Exactly the ones you have installed.

**Right-click a tab** to open the owning tool's parameters; that is where
the mappers are configured. The bar comes in two styles (*Tab Bar* on the
hub's Hub page, roams with your settings): **Rows** wraps fixed-width tabs
into as many rows as needed; **Strip** is TouchDesigner's single-row folder
tabs with scroll arrows and a dropdown. Drag a tab onto another tab to reorder
in either style. There is no close button in either: hide a tab from the contributing tool's *Shown in Hub*
parameter on its Registry page, and bring any hidden tab back from the FNS
button's right-click menu ("Show …"). Tab order and the active tab roam with
your settings through [FNS_ConfigRegistry](/docs/fns-configregistry/), as do
the three configurators' layouts. A tool carrying a *Refresh* pulse is
refreshed every time its tab is shown.

## Drop to register

Drop any panel COMP on the FNS button (or anywhere on the hub window). The hub
offers every surface that can take it (Toolbar, Navbar, Main Menu) in a
small menu; pick one and the COMP receives a self-registering host of that
surface's registry, placed after the bar's last entry, and appears on the bar
immediately. A COMP that should live on two surfaces is dropped twice. Nothing
is copied into the bar: the COMP stays where it is and publishes into the
registry, exactly like every shipped tool.

## Contributing a tab

A tool that wants a tab in the hub carries a stamped `FNS_HubRegistry` host
(drop the tool on nothing; stamp it from the registry master with
`op.FNS.op('FNS_HubRegistry').StampHost(tool, canonical_name='mytool')`, or copy
the host out of any shipped tool). Its Registration page names what the tab
shows: the tool itself or any panel inside it (mirrored into the hub, so the
tool can live anywhere), a DAT/CHOP/TOP/SOP/POP (shown through an OP Viewer),
or a parameter page of the tool. Nothing is discovered by scanning: the host
registers itself when it initializes, so a tool added while the hub is open
simply appears. The developer-facing contract is
[docs/HubContract.md](https://github.com/function-store/FunctionStore_tools/blob/main/docs/HubContract.md).
