---
package: tools_ui
summary: The tabbed panel that hosts the toolkit's larger tool UIs.
features:
  - name: tools_ui
    anchor: tools-ui
    icon: Fx.png
---

## tools_ui

Clicking the **Fx** toolbar button opens a tabbed panel collecting the
toolkit's larger tool UIs — the mappers, hotstrings, palette editors and
friends. **Right-clicking** a tab opens the owning tool's parameters
*(very important for midi/oscMapper configuration)*. Tabs can be
re-ordered by drag-and-drop, and closed with their **✕** button (closing a
tab switches the tool's *UI Tab* toggle off; re-enable it on the tool's
parameters to bring the tab back). Tab order and the active tab roam with
your config.

Tabs are **discovered, not hardcoded**: tools_ui sweeps its sibling tools
for a `UI Tab` parameter page and builds exactly the tabs of the tools you
have installed. Installing or removing tools never leaves dead tabs — the
panel rebuilds on startup and every time it opens.

## Contributing a tab

Any depth-1 COMP next to tools_ui can contribute a tab by carrying a
**UI Tab** section on its `Registry` parameter page (a `Uitabsection`
header plus these parameters — the same page that hosts the registry
sections like `Cf*`/`Tb*`):

| Parameter | Meaning |
|---|---|
| `Uitab` (toggle) | contribute a tab at all |
| `Uitablabel` (str) | tab label; empty = the COMP's name |
| `Uitaborder` (int) | default ordering (user re-ordering wins) |
| `Uitabpanel` (str) | what the tab shows — see below |

`Uitabpanel` accepts three forms:

- **empty** — the tool root itself is the tab's panel (it must be a panel
  COMP; tools_ui wires it in as a panel child).
- **`./somePath`** — a DAT/CHOP/TOP inside the tool, shown through a
  viewer (the SearchWords table works this way).
- **`params:<pages>`** — a parameter view of the tool root scoped to the
  named custom pages, e.g. `params:Families Colors` (bare `params:` shows
  all pages). The ColorUI tab works this way.

A tool that also wants a **refresh on show** simply carries a `Refresh`
pulse parameter — tools_ui pulses it by capability, never by name.
