---
status: in-force
summary: 'How a tool contributes a tab to TouchDesigner''s Palette Browser through FNS_PaletteRegistry, and why the TDXLU/Patreon tabs appear without any registration.'
since: 4694cd0 2026-08-23 (registry externalized as the 9th)
skill: fns-registry
---

# Palette tabs — the contribution contract

`FNS_PaletteRegistry` is the ninth FNS registry. It manages TouchDesigner's
**Palette Browser** (`/ui/dialogs/palette/palette`): a tool publishes a native
panel COMP, and it appears as a tab beside TD's own *Palette* tab.

- Global shortcut: `op.FNS_PALETTEREGISTRY`
- Home: `/sys/FNS_Registries/FNS_PaletteRegistry` (per the
  [registry home contract](RegistryHomeContract.md))
- Master (dev): `/FNSTools/FNS_PaletteRegistry`
- Package category: **Core**

The general model — one promoted global manager, many host publishers — is
[the registry scheme](RegistryScheme.md). This document covers only what is
specific to the palette surface.

## The surface

TD's palette dialog is a vertical stack (`emptypanel`, spacing 2) whose
children are placed by `alignorder`. Its stock `list` is `panelh - 32` tall —
the 32 px TD leaves free is exactly a folder-tab row. The registry uses that
free row and nothing else:

| Injected op | Kind | `alignorder` | Role |
|---|---|---|---|
| `fnspal_tabs` | widgetCOMP | 0.5 | TD's shipped `folderTabs`, loaded from the install |
| `fnspal_tabs_exec` | parameterexecuteDAT | — | routes `Value0` changes to `ShowTab` |
| `fnspal_<canonical>` | selectCOMP | 2.5 | mirror showing the contributed panel where `list` stacks |

Everything injected sits on **panel layer 1**: the dialog is all layer 0 and
its full-size `emptypanel` background paints over later siblings.

Nothing stock is copied, moved or re-expressed. The stock panels (`list`,
`pathfield`, `explore`, `folder1`) only get their `display` flag toggled while
a contributed tab is showing, and it is restored when it is not.

Nothing about the surface is saved: `/ui` is rebuilt on every project open, so
the global re-injects on promotion, registration and heal.

## Contributing a tab

A contribution is a **native panel COMP**. The registry knows nothing about web
pages — a Web Render TOP in a container is just a panel like any other.

### The host way (normal)

Stamp an `FNS_PaletteRegistry` host into the tool and set its Registration page:

| Par | Label | Meaning |
|---|---|---|
| `Comp` | Tool COMP | the contributing tool; defaults to `..` |
| `Canonicalname` | Canonical Name | unique id (letters, digits, `_`, `-`); empty = the tool's name. `palette` is TD's own and is rejected |
| `Panel` | Tab Panel | the panel COMP to show; defaults to the tool itself |
| `Callback` | Callbacks DAT | optional; see below |
| `Tablabel` / `Taborder` | | strip label and position (default 50, then by label) |
| `Displayed` | Shown in Palette | registered but off-strip when false; the registry writes its choice back here so it persists with the tool |
| `Autoregister` | Expose in Palette | publish while the component exists |

`Promotepars` mirrors the key pars onto the parent tool as a bound **Registry**
page with the `Pl` prefix, so registration is configured on the tool itself.

### Several tabs from one host

The Registration pars define the **first** tab. The **Tab sequence** on the same
page adds one more per block:

| Block par | Meaning |
|---|---|
| `Name` | canonical name of this tab. **Empty = no tab** — TD forces a sequence to keep at least one block, so an empty block is how a host says it contributes nothing extra |
| `Source` | panel COMP for this tab. **Empty = reuse the primary `Panel`** — this is how one panel serves several tabs, routed by `onPaletteTab` |
| `Label` / `Order` | strip label and position, same meaning as the flat pars |
| `Shown` | on the strip, or registered-but-hidden |

The split is deliberate rather than historical: the tool-facing **Registry** page
proxies flat pars onto the parent tool, and a sequence cannot be proxied that
way — so the common single-tab case keeps its one-line setup on the tool itself,
and only genuinely multi-tab tools touch the sequence.

A block with a bad or duplicate name is reported in `Regstatus` and skipped; it
never costs the tool its primary tab.

**Which tabs a host owns is derived, not stored.** A renamed block, a deleted
block or a shrunk sequence leaves no trace in the parameters, so the host
reconciles against the global's own `source_registry` stamp after every apply.
Do not add a "my tabs" list to host storage — it will drift.

### The API way

```python
reg = getattr(op, 'FNS_PALETTEREGISTRY', None)
if reg is not None and hasattr(reg, 'RegisterTab'):
    reg.RegisterTab(comp, 'mytool', panel=comp.op('ui'), label='My Tool', order=20)
```

Always guarded, always through the shortcut — never a hardcoded `/sys` path.
Other public methods: `UnregisterTab`, `Tabs`, `SetTabDisplayed`, `ShowTab`,
`CurrentTab`, `PanelTarget`, `Resync`, `RemoveSurface`.

## The panel is sized to the slot

A Select COMP cannot push its size into its source, and a panel whose network
parent is a plain baseCOMP has nothing to fill. So while a panel is registered
the registry rewrites its `w`/`h` to `SlotWidth()`/`SlotHeight()` expressions
and forces `hmode`/`vmode` to `fixed` — the same move TD's own dialog makes
when it docks the palette. The original mode/expr/value is stored in the entry
under `orig_size` and restored on unregister.

**Consequence for tool authors:** do not expect to control the tab panel's size
while it is registered, and do not re-point `w`/`h` behind the registry's back.

## Tab-change callbacks

The optional Callbacks DAT receives every tab change, for **every** registered
entry — so one tool sharing a single panel across two tabs can route it:

```python
def onPaletteTab(canonical, previous):
    if canonical == 'mytool_a':
        ...
```

Mirrors are views: the tool's panel keeps its state — a Web Render's browser
process included — across tab switches and across registry reinits, because the
global rebuilds only the strip and the mirrors, never the panel.

## Inert until something registers

**An empty registry owns no surface.** With zero contributed tabs, `_syncSurface`
tears down its own ops and returns without touching the dialog. This matters for
two reasons:

1. A strip carrying only TD's own *Palette* tab is pure noise.
2. The free row is contended (see below) — claiming it while contributing
   nothing stacks two tab strips in one 26 px row.

Teardown restores the stock panels **only if the registry is the one holding
them hidden**, tracked in `_stock_hidden`. It cannot be inferred from the
current tab: `UnregisterTab` resets the current tab *before* it syncs, so
inferring left TD's palette permanently blank.

## Why TDXLU and Patreon tabs appear with nothing registered

They are **not** registry entries. They come from a separate, pre-registry
implementation of this same surface that ships with a different product:

- `/TDXLauncherUtility/TDXLUPalette` (the TDXLPP launcher, whose `externaltox`
  points outside this repo at `../TDXLPP/release/TDXLauncherUtility.tox`)
- `TDXLUPaletteExt.__init__` schedules `_postInit` and `AUTO_INSTALL = True`, so
  it re-installs on **every** project load and every extension reinit
- its tab list is hardcoded: `TABS = (('palette','Palette'), ('tdxlu','TDXLU'),
  ('patreon','Patreon'))`
- it copies its own `folderTabs` and `web` masters into the dialog as
  `TDXLU_tabs`, `TDXLU_tabs_exec` and `TDXLU_web`

So the tabs carry by default because that injector auto-installs itself, not
because anything was promoted or registered. `FNS_PaletteRegistry` is the later,
generalized rewrite of exactly this mechanism — the constants line up
one-for-one.

### They collide

Both implementations claim the same slots, and the older one is not
registry-aware:

| | TDXLU injector | FNS_PaletteRegistry |
|---|---|---|
| strip `alignorder` | 0.5 | 0.5 |
| panel `alignorder` | 2.5 | 2.5 |
| panel layer | 1 | 1 |
| stock ops hidden | `list`, `pathfield`, `explore`, `folder1` | identical |

Observed live on 2026-08-23: reiniting the registry global while TDXLU's
injection was present put two folder-tab strips in the same 26 px row. The
inert-by-default rule above removes the collision *for now* — the registry
claims nothing until a tool contributes — but it does not resolve the
duplication.

### The generalization gap

Migrating TDXLU onto the registry is the right end state, and it is **not yet
done**. Only one thing is still in the way:

1. **The launcher is a different product.** `/TDXLauncherUtility` persists to
   `../TDXLPP/release/TDXLauncherUtility.tox`, outside this repo. The change
   belongs to that product's tree, not this one.
2. ~~One host publishes one tab.~~ **Closed** — the Tab sequence above lets one
   host publish TDXLU's two tabs over a shared panel, with `Source` left empty
   on the second block. Nothing on the registry side blocks the migration now.

Until then, treat the two as mutually exclusive: whichever installs owns the
free row.

## Lineage hazard, paid for once

The registry was authored inside the TDXLPP project and arrived here still
bound to it — `pre_release` and `PaletteRegistryExt` carried
`TDXLauncherUtility/...` file paths (TD warned *File not found for sync* on
every touch) and `RegistryBase` was an unbound, 1.1 KB-stale fork of
`scripts/shared/RegistryBase.py`.

**When adopting a COMP from another project, audit every DAT's `file`/`syncfile`
par before externalizing.** Externalizing a DAT that carries a foreign file
binding can raise a modal that blocks TD's main thread. Clear the binding first,
then let Embody resolve the path.

## Two silent TD behaviours around sequences

Both cost real time here; neither raises:

- **A block par whose base name collides with an existing flat par is silently
  dropped** — no error, no parameter, `blockSize` simply does not grow. Block
  base names must be distinct from *every* flat par on the COMP (which is why
  they are `Name`/`Source`/`Label`/`Order`/`Shown` and not `Panel`/`Displayed`).
- **Setting the sequence header's `order` makes TD swallow whatever follows it
  into the block.** Moving the header to sit after `Taborder` absorbed
  `Helpurl`, `Promotepars` and `Presaveheal` into `Tab0*` and took `blockSize`
  from 5 to 8. Moving the header back released them — but `Presaveheal` could
  not reclaim its name and returned as a duplicate `Presaveheal2` that had to
  be destroyed. Append the sequence LAST and leave its order alone.
