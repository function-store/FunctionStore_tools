---
package: FNS_OpMenuRegistry
summary: 'OP Create dialog surface registry: search words, row decorations, right-click items, filter stages. The raw master, promoted to /sys.'
features:
  - name: OpMenu Registry
    anchor: opmenu-registry
  - name: What tools contribute
    anchor: what-tools-contribute
---

## OpMenu Registry

The raw registry that manages TouchDesigner's **OP Create dialog**
(`/ui/dialogs/menu_op`) as a single surface. Several tools want to decorate that
one dialog at once, and without somewhere to arbitrate they would overwrite each
other's changes; the registry is that somewhere. Remove the tools and the dialog
goes back to stock.

It ships as its own core package, always installed,
promoted to `/sys` with the global shortcut `op.FNS_OPMENUREGISTRY`.

You do not open this package directly. The user-facing mods that ride on it are
documented under [FNS_OpMenu](/docs/fns-opmenu/#opmenu-mods).

## What tools contribute

Five kinds of contribution, and the code for every one of them lives in the
publishing tool, in a callbacks DAT that tool owns. The registry only holds a
reference, so it never names a tool and a tool's menu behaviour travels inside
its own `.tox`:

- **Search words**: extra words that match an operator type, so `music` finds
  Audio File In. See [Custom Search Keywords](/docs/fns-opmenu/#custom-search-keywords).
- **Node-table decorations**: relabel a row, such as the `>>>` that
  [OpTemplates](/docs/optemplates/) puts beside every type you have a template for.
- **Right-click menu items**: entries appended after TD's own three, such as
  OpTemplates' *Edit Templates...*.
- **Filter-chain nodes**: Script DATs spliced into the node table's filter
  chain to filter or rewrite the operator list itself. Greg Hermanovic's
  [IO filters](/docs/fns-opmenu/#gregs-io-filters) are the worked example.
- **Panel injection**: Panel COMPs wired into the dialog at a named anchor.
