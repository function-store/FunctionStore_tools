---
package: FNS_ConfigRegistry
summary: 'There are a couple of components whose states/contents you''ll probably want to synchronize between your projects, such as OpTemplates, ExprHotStrings, or Global ResetPLS exceptions.'
features:
  - name: Settings UI
    anchor: settings-ui
  - name: Syncing/Externalizing
    anchor: syncingexternalizing
  - name: Custom Parameters
    anchor: custom-parameters
---

## Settings UI

Every installed tool's settings, on one page in your browser:

```python
op.FNS_CONFIGREGISTRY.OpenSettingsUI()
```

This is the toolkit's settings panel -- the replacement for the
hand-authored control parameters that used to live on the toolkit root.
It lists every tool that is registered, with its version and its
parameters, and writing a value there goes through the same filters and
persistence as any other change, so the page and the components can never
disagree.

Nothing in the page is hardcoded: there is no list of tools or parameters
in the HTML. It asks the registry what exists and renders that, which is
why it is always correct for the subset of tools you actually installed
and never grows dead entries for ones you removed. Each tool's `Registry`
page is skipped -- that is registration plumbing, not settings.

The page is served by **FNS_Console** — the toolkit's web front, a core
package of its own — on `127.0.0.1`, first free port in **36710-36759**,
only while you are looking at it (see `FNS_Console.md`). This registry
only answers the console's `/api/*` calls: `UiState`, `UiSet`,
`UiExport`, `UiImport`, `UiScope`. `op.FNS_CONFIGREGISTRY.OpenSettingsUI()`
still works — it forwards to `op.FNS_CONSOLE.Open()`.

> Tools carry a host copy of the registry, but every host forwards to the
> promoted `/sys` global, so there is exactly one source of settings
> however many tools you have installed.

## Syncing/Externalizing

FNS_ConfigRegistry aggregates every installed tool's Custom Parameters (plus optional extra state, e.g. from [OpTemplates](/docs/optemplates/) or [ExprHotStrings](/docs/exprhotstrings/#exprhotstrings)) into **one JSON file** inside your **User Palette** (`FNStools_ext/config/FNStools_config.json` by default, overridable per-install via the master's `Configfile` par) -- so your settings follow you across projects instead of living inside the `.toe`.

Each tool loads its own section once per session, ~30 frames after it registers (`Autoload`, on by default per tool -- turn it off on a tool that should keep project-local settings instead, e.g. one whose state should migrate with the project folder). Saving happens automatically on project pre-save, via the `Save All` pulse on any tool's Registry page (forwards to the FNS_ConfigRegistry master), and right before the updater replaces a package.

## Custom Parameters

FNS_ConfigRegistry is one of the toolkit's **core** packages -- always installed, never optional. Core is the six surface registries (Config, Toolbar, Navbar, MainMenu, OpMenu, PaneType) plus [FNS_Console](/docs/fns-console/) and [FNS_Updater](/docs/fns-updater/). It ships as its own package, promoted to `/sys` (global shortcut `op.FNS_CONFIGREGISTRY`). Every tool that wants its settings to persist carries a small **host** copy of it, visible as the tool's own `Registry` page (the `Cf`-prefixed section -- every control in it is listed under [What it adds to a registered tool](#registry-section)) -- removing a tool's host just means that tool's settings stop syncing, nothing else breaks.

Use `Save All` / `Load All` (on the FNS_ConfigRegistry master, or any host's forwarded pulse) to explicitly sync all tool settings to/from the JSON at once -- handy after a significant change you want to carry into other projects.
