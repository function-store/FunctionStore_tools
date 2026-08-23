---
status: in-force
summary: What a tool must do to show a tab in FNS_Hub -- the FNS_HubRegistry host, RegisterTab, the three tab kinds, exposure, and the hazards the build paid for.
since: 2026-08-23 (FNS_Hub build, branch uniUI)
verified: 2026-08-23 -- Toolbar/Navbar/MainMenu configurators and the console viewer are the first four tabs; late registration and drop-to-register verified live
skill: fns-registry
---

# Contract: contributing a tab to FNS_Hub

What a tool must do to appear as a tab in the toolkit's one-stop manager
window. Source of truth:
[HubRegistryExt.py](../FNSTools/FNS_HubRegistry/HubRegistryExt.py) (`RegisterTab`,
`_validateTab`, `_syncSurface`) and [HubExt.py](../FNSTools/FNS_Hub/HubExt.py)
(the window side). The registry pattern this sits on is
[RegistryScheme.md](RegistryScheme.md); the promoted global lives per
[RegistryHomeContract.md](RegistryHomeContract.md). The console's web tabs are a
different surface with their own contract ([ConsoleTabContract.md](ConsoleTabContract.md));
the console itself is one hub tab.

## 1. The shape

`FNSTools/FNS_Hub` is a core package: the **FNS** button in TD's main-menu bar
(a widget published through `FNS_MainMenuRegistry` as canonical `FNS`) and a
window (`panel`: folder tabs on top, a `tabs` container below). **The hub
holds no tab knowledge.** `FNS_HubRegistry` -- the eighth registry, promoted to
`/sys/FNS_Registries`, shortcut `op.FNS_HUBREGISTRY` -- owns the entries, and
its `_syncSurface` injects one rendering op per entry into `panel/tabs`
(`hubtab_<canonical>`), prunes the stale ones, and calls `HubExt.RefreshTabs()`.
The hub only decides which `hubtab_*` is displayed and keeps the folder-tab bar
in step.

A tab is a **contribution** like every other surface: the tool carries a
stamped `FNS_HubRegistry` host whose Registration pars say what the tab shows.
**Nothing is discovered by scanning** -- the host registers at its own init, the
base healing tick re-asks unpublished hosts in the boot window, and a host
stamped while the hub is open appears without any rescan (verified).

## 2. The three kinds

| Registration pars | Kind | Rendered as |
|---|---|---|
| `Tab Content` empty, `Tool COMP` is a panel | `panel` | a Select COMP mirroring the tool -- it can live anywhere in the project |
| `Tab Content` = a panel COMP inside the tool | `panel` | a Select COMP mirroring that panel |
| `Tab Content` = a DAT / CHOP / TOP / SOP / POP / MAT | `opviewer` | an OP Viewer COMP (interactive) |
| `Tab Parameters` = a page scope (`*` = all) | `params` | a Parameter COMP on the tool, built-in pages off |

`Tab Parameters` wins over `Tab Content`. `Tab Label` defaults to the canonical
name; `Tab Order` defaults to 50 (the configurators sit at 10/20/30, the
console at 90); `Shown in Hub` (`Displayed`) is what the hub's close button
writes back to, so a hidden tab stays hidden across projects through the
tool's Registry page.

## 3. The call

```python
op.FNS_HUBREGISTRY.RegisterTab(comp, canonical, content=None, params='', label='',
                               order=50, displayed=True, help_url='', source_registry=None)
```

Guarded, like every registry; a host that is not the `/sys` global forwards.
`UnregisterTab(canonical)` (aliased `UnregisterPanel` for RegistryBase's host
teardown), `Tabs(include_hidden=False)`, `SetTabDisplayed(canonical, bool)`,
`Open(tab=None)`, `OpenDocs(canonical)` are the rest. Rejected (debug line, no
exception): no tool COMP; empty canonical; canonical not letters/digits/`_`/`-`;
content neither a panel nor a viewable operator; content gone.

`StampHost` is the one way to put a host in a tool. `par_values` may carry
`Comp`/`Tabcontent` -- that is how the hub itself publishes the console tab
(`FNS_Hub/FNS_HubRegistry`, `Comp='../webBrowser'`), because the root's
`webBrowser` is a clone master (see §6).

## 4. Exposure

Only the shown tab's component is "live". When a tab is shown or hidden the hub
calls `OnHubExposure(exposed)` on the component's extension if it defines one;
otherwise, a component with `Active` and `Address` pars (a palette Web Browser)
has its `Active` switched directly. A component carrying a `Refresh` pulse par
is pulsed each time its tab is shown (the old tools_ui convention). Right-click
on a tab opens the owning tool's parameter window
(`HubExt.OpenTabParameters(index)`).

A mirrored root panel has no panel parent, so it must have a **fixed size**:
the tool tabs bind `w`/`h` to `op.FNS.op('FNS_Hub/panel/tabs')` with their old
standalone size as the fallback when no hub exists. Every tab is un-exposed when the window
closes: a windowCOMP has no close callback and the panel's `winopen` value
stays 0 under a windowCOMP, so `HubExt` runs a once-a-second `isOpen` check
**only while the window is open** (`_armCloseWatch`). The root `webBrowser`'s
own watchers (`Render Only While Window Open / Viewer Active`) are OFF: with
either on, its per-frame `sync()` fights the hub.

## 5. Drop-to-register

`panel/drop_callbacks` serves both the hub window and `select1` (the FNS
button; its main-menu Select mirror forwards drops -- verified). Nothing runs
in the drop-event stack: `RouteDrop` records paths and defers a frame; every
tab whose component promotes `AcceptsDrop` + `PackageDrop` is a target; one
target stamps directly, several open a `popMenu`; the configurator's
`_stampPackage` then calls the registry **master's** `StampHost`. A COMP that
belongs on two surfaces is dropped twice.

## 6. Hazards paid for here

- **Never stamp a host into a clone master.** `/FNSTools/webBrowser` is cloned
  by `ColorUI/webBrowser`; a host stamped into the master replicated into the
  clone, and the clone's copy won the registration. Hosts for shared chrome
  live in the hub and point at the content by path.
- **The `/sys` global runs a COPY of the extension DAT with no file sync.**
  Editing `HubRegistryExt.py` reaches the master only; push the master's DAT
  text into the global and reinit (or re-promote) to test.
- **Folder-tab labels cannot contain spaces** -- `masterFolderTabs` splits
  `Menulabels` on whitespace, so `Main Menu` became two tabs. Use `MainMenu`.
- **A retry loop that gives up must clear its queued flag** -- `_syncSurface`
  left `_pane_sync_queued` True after exhausting its attempts and nothing
  could ever re-arm the sync.
- **OP-reference par values resolve sibling-relative for a COMP owner**
  (`Comp='select1'`, not `'../select1'`), while `'..'` still means the parent.
- **The old `_stampPackage` addressed the host by its pre-v3 name** -- the
  configurators' drop-to-register had been dead since the `FNS_` rename;
  the port to `StampHost` fixed it and removed the dormant template hosts.

## 7. Persistence of the configurators

The three configurators are PI suspects of their own
(`modules/suspects/FNSTools/FNS_Hub/<Name>Configurator.tox`, `enableexternaltox`
on) nested under the hub's tox -- individually tracked and releasable.
Their `ConfiguratorExt` DATs are live, so that tox is the sole carrier of
the code. **Save order: configurator toxes, then `FNS_Hub`, then the root.**
A released configurator is a hub contribution (its `FNS_HubRegistry` host
stays live in the artifact, cloning off); dropped into a project with the
hub it registers its tab, alone it has no window.

## 8. Nothing here is durable

`/sys` is rebuilt every open: hosts re-register on init. The hub's tab order
and active tab roam as plain pars on its Hub page (config host canonical
`FNS_Hub`, `About` page excluded); the configurators' `state` tables roam
through the hub's `config_callbacks`, keyed by configurator name.
