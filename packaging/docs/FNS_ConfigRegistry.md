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

A Web Server DAT inside the master serves it on `127.0.0.1`, taking the
first free port in **36710-36719**. It only runs while you are looking at
it: `OpenSettingsUI()` starts it and opens your browser, every request
re-arms an idle timer, and after **10 minutes** of silence it shuts itself
off. `op.FNS_CONFIGREGISTRY.CloseSettingsUI()` closes it immediately.

> Only the master serves the page. Tools carry a host copy of the registry,
> but calling `OpenSettingsUI()` on one forwards to the promoted `/sys`
> master, so there is exactly one server and one page however many tools
> you have installed.

## Syncing/Externalizing

FNS_ConfigRegistry aggregates every installed tool's Custom Parameters (plus optional extra state, e.g. from [OpTemplates](/docs/optemplates/) or [ExprHotStrings](/docs/exprhotstrings/#exprhotstrings)) into **one JSON file** inside your **User Palette** (`FNStools_ext/config/FNStools_config.json` by default, overridable per-install via the master's `Configfile` par) -- so your settings follow you across projects instead of living inside the `.toe`.

Each tool loads its own section once per session, ~30 frames after it registers (`Autoload`, on by default per tool -- turn it off on a tool that should keep project-local settings instead, e.g. one whose state should migrate with the project folder). Saving happens automatically on project pre-save, via the `Save All` pulse on any tool's Registry page (forwards to the FNS_ConfigRegistry master), and right before the updater replaces a package.

## Custom Parameters

FNS_ConfigRegistry is one of the toolkit's six **core registries**: it ships as its own package, promoted to `/sys` (global shortcut `op.FNS_CONFIGREGISTRY`), the same as the Toolbar/Navbar/MainMenu/OpMenu/PaneType registries. Every tool that wants its settings to persist carries a small **host** copy of it, visible as the tool's own `Registry` page (`Cf`-prefixed pars: `Cfautoload`, `Cfregister`, `Cfregstatus`, etc.) -- removing a tool's host just means that tool's settings stop syncing, nothing else breaks.

Use `Save All` / `Load All` (on the FNS_ConfigRegistry master, or any host's forwarded pulse) to explicitly sync all tool settings to/from the JSON at once -- handy after a significant change you want to carry into other projects.
