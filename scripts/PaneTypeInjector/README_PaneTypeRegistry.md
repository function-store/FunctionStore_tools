# PaneTypeRegistry

PaneTypeRegistry extends TouchDesigner’s panebar with **named, persistent pane-type entries**. Any COMP can appear in the pane-type dropdown and be recalled with a configurable combination of owner, pane type, window actions, and an optional Python callback.

Typical uses: pin a custom panel, open a tool as a Network Editor or Parameters pane, or restore a floating viewer from a single menu selection.

---

## Concepts

PaneTypeRegistry uses a **single authoritative runtime instance** plus optional **host instances** that publish into it.

| Role | Location | Responsibility |
|------|----------|----------------|
| **Global registry** | `/sys/PaneTypeRegistry` (`op.PANETYPEREGISTRY`) | Panebar menu contents, left-click selection, right-click menus, recall execution, entry healing |
| **Host registry** | Child of the COMP you want listed (often named `PaneTypeRegistry`) | Declares that COMP’s menu name, pane type, and default recall flags; registers and unregisters with the global registry |

Host instances do not maintain their own menu table or handle panebar selection. Registration and unregistration always target the global registry, including when called on an older host copy. That keeps menu behavior and recall logic on the installed `/sys` version.

On project open, a newer shipped component may install or replace `/sys/PaneTypeRegistry` (version-aware). After that, host instances only publish their COMP when Autoregister is enabled (or Register is pulsed).

---

## Quick start

1. Place a `PaneTypeRegistry` inside the COMP that should appear in the panebar (or use **Register…** from a builtin panebar row’s right-click menu — see below).
2. On the **Registration** page:
   - **Comp** — COMP to recall (default `..`, the parent)
   - **Canonical Name** — label shown in the dropdown
   - **Pane Type** — target `PaneType` (for example `PANEL`, `NETWORKEDITOR`, `PARAMETERS`)
   - Set the default recall flags (Set Owner, Change Type, and so on)
3. Enable **Autoregister**, or pulse **Register**.
4. Open a panebar pane-type dropdown; the canonical name should appear.

### Persistence

The global registry’s in-memory table is **not** saved with the `.toe`. Persistence comes from host registry components left inside your networks with **Autoregister** enabled. On open, each host republishes into `/sys`.

---

## Registration page

| Parameter | Description |
|-----------|-------------|
| **Autoregister** | When on, keep this host’s entry published while the component exists |
| **Register** | Publish once (works even if Autoregister is off) |
| **Regstatus** | Read-only status |
| **Comp** | COMP used as pane owner / target (default: parent) |
| **Canonical Name** | Unique panebar menu label |
| **Menu Order** | Preferred order among **registered** entries. `-1` = no preference (append; default). `0` = first custom row, `1` = second, and so on. Built-in rows are not moved. |
| **Pane Type** | `PaneType` applied on recall when Change Type is enabled |
| **Set Owner / Change Type / Maximize / Tear Away / Float / Open Parameters** | Default recall actions for this entry |
| **Callback** | Optional DAT implementing `onPaneRecall(ctx)` |
| **Create Callback** | Creates a skeleton callbacks DAT and assigns **Callback** |

### Pane types

Supported types include the standard TouchDesigner builtins, plus **OP Browser** (`PaneType.OPBROWSER`). OP Browser is valid in the API but omitted from TD’s default panebar table; the global registry inserts **OP Browser** into the dropdown immediately after **Textport and DATs**.

Validation:

- **PANEL** — host must be a Panel Component (`isPanel`)
- Other types — any COMP

---

## Panebar interaction

### Left-click

| Selection | Result |
|-----------|--------|
| Registered name | Runs that entry’s stored recall flags, then the callback if configured |
| Built-in TD rows | Standard panebar `desk` commands |
| **OP Browser** | `changeType(PaneType.OPBROWSER)` via the global registry |

### Right-click

**Registered rows**

- Recall (as registered)
- Owner + Type
- Set Owner / Change Type / Maximize / Tear Away / Float / Open Parameters
- Run Callback
- Open Floating Network Editor
- Unregister

**Built-in rows** (Network Editor, Panel, Textport and DATs, OP Browser, …)

- **Register “\<owner\>” as \<type\>…** — prompts for a menu name, then:
  - Registers the pane’s current owner under that name
  - Adds a host `PaneTypeRegistry` inside the owner so the entry republishes on the next project open

### Menu name conflicts

Canonical names are unique in the global table.

- Same owner — update the existing entry
- Different owner — choose **Replace**, **Use Suggested**, or **Cancel**

---

## Recall flags

Recall is controlled by independent flags (the legacy Action menu is no longer used):

| Flag | Effect |
|------|--------|
| **Set Owner** | Assigns `pane.owner` to the registered COMP |
| **Change Type** | Calls `pane.changeType(...)` for the stored pane type |
| **Maximize** | Maximizes the pane |
| **Tear Away** | Calls `pane.tearAway()` (owner and type are applied first when those flags are on) |
| **Float** | Depends on pane type: viewers use `openViewer()`, Parameters uses `openParameters()`, otherwise opens a floating Network Editor via TD helpers |
| **Open Parameters** | Calls `openParameters()` on the COMP |

---

## Callbacks

Point **Callback** at a text DAT (or use **Create Callback**):

```python
def onPaneRecall(ctx):
    """Called after built-in recall flags when a callback DAT is set.

    ctx keys:
        pane       - ui.Pane (may be replaced after changeType)
        pane_comp  - panebar UI COMP that triggered the selection
        owner      - registered COMP, or None
        canonical  - menu name
        info       - registry entry dict
        registry   - PaneTypeRegistryExt instance (global)
    """
    owner = ctx.get('owner')
    if owner is not None and hasattr(owner, 'Open'):
        owner.Open()
```

---

## Python API

Prefer the global shortcut so calls always hit the installed `/sys` instance:

```python
reg = op.PANETYPEREGISTRY

reg.RegisterPanel(
    op('myComp'),
    'My Panel',
    pane_type='PANEL',
    set_owner=True,
    change_type=True,
    maximize=False,
    tear_away=False,
    float_pane=False,
    open_parameters=False,
    callback=op('myComp/callbacks'),          # optional
    source_registry=op('myComp/PaneTypeRegistry'),  # optional; aids heal / unregister
    menu_order=None,  # optional; None or -1 = append (default); 0, 1, … = sort among custom rows
)

reg.UnregisterPanel('My Panel')
reg.RecallPanel(pane_comp, 'My Panel')  # pane_comp: panebar pane UI COMP
```

`RegisterPanel` and `UnregisterPanel` invoked on a host instance are forwarded to the global registry. If the global registry is not available yet, the call is ignored (with a debug message) rather than creating a parallel local menu.

Host-side controls:

```python
host = op('myComp/PaneTypeRegistry')
host.par.Autoregister = True
# or
host.par.Register.pulse()
```

---

## Persistence and multiple entries

- A single COMP may contain **multiple** host registries (for example one for Parameters and one for Network Editor). Additional instances are named `PaneTypeRegistry_<legalName>` when required.
- Default menu names include the pane-type label to reduce collisions (for example `MyComp Parameters`).
- Destroying a host registry clears its registration (`onDestroyTD`).
- The global registry periodically heals entries: updates renamed paths, removes missing COMPs, and drops entries whose source host registry is gone.

---

## Documentation viewer

On the **About** page, pulse **View Readme** to:

1. Rebuild the markdown annotate from this document  
2. Open a floating panel viewer on `md/scroll`

Source file (synced into `md/readme`):

`scripts/PaneTypeInjector/README_PaneTypeRegistry.md`

---

## Operators (implementation reference)

| Operator | Purpose |
|----------|---------|
| `datexec1` | DAT Execute watching panebar `panetype/out1`; active only on the global `/sys` instance |
| `rclick_panereg` | Template Panel Execute for right-click menus; copied into each panetype dropdown (enabled and clone-immune when deployed) |
| `popMenu` / `popMenuConfig` | Context menu UI |
| `md` / `readme` / `scroll` | Markdown content and panel viewer |
| `annotate1` | Annotate used by the markdown viewer in the network |

---

## Versioning

The About page exposes **Version**, **Build**, and **Date**. When more than one registry could become the global instance, the higher semantic version is preferred. Major-version conflicts present a chooser dialog.
