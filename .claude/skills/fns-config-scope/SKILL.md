---
name: fns-config-scope
description: "MUST READ before making an FNS tool persist settings, touching FNS_ConfigRegistry save/load, or writing anything that assumes the roaming config JSON exists. Global vs project scope, the escape hatches, SetConfigScope, and the updater gate."
---

# Config scope: where a tool's settings actually land

One menu par — **`Config Scope` (`Configscope`) on the `/FNSTools` root** — decides
whether the toolkit's persisted settings roam machine-globally or stay inside the
`.toe`. Every tool that persists anything is subject to it. The reasoning, flip
semantics in detail, and the implementation map are in
[docs/ConfigScope.md](../../../docs/ConfigScope.md).

| Scope | What happens |
|---|---|
| `global` (default) | Everything roams through one aggregated JSON in the user palette (`<userPaletteFolder>/FNStools_ext/config/FNStools_config.json`), shared by every project on the machine. **Last save wins across projects.** |
| `project` | The roaming file is **never read and never written**. The `.toe` is the whole store — host Registration pars, configurator `state` tables and tool custom pars all boot from the project itself. No sidecar file. |

The root par is the authored record; the `FNS_ConfigRegistry` master's and the
`/sys` global's own `Configscope` pars **bind** to it (`op.FNS.par.Configscope`,
two-way — edit any of the three).

## Rules you must not break

- **Never assume the JSON exists.** Under project scope there is no file, in
  either direction. Any code that "just reads the config" is wrong.
- **`onConfigSave` still runs under project scope** — only the file I/O is gated.
  This is load-bearing: the configurators' `SnapshotState()` freshens state-table
  group rows there, so a bar-side toggle still reaches the `.toe` before TD's
  pre-save. Do not "optimize" the snapshot loop away when the file is skipped.
- **The scope choice never roams.** Both hosts that snapshot the root carry
  `Excludepars = 'Configscope'`, so a roamed section can never overwrite a
  project's scope declaration. Keep that exclusion.
- **A missing par reads as global** (`_scopeIsProject` uses `getattr`), so stale
  promoted copies predating the par behave as before. Preserve that fallback.
- **Flip to `global` overwrites the shared layout** with this project's state.
  Interactive flips pop a confirmation (Push to Global / Adopt Global / Stay
  Project); flipping to `project` is silent because nothing is at risk.

## Programmatic API

```python
op.FNS_CONFIGREGISTRY.SetConfigScope('project', prompt=False)   # quiet by default
```

Promoted and callable on any copy — it routes to the master. **Keep
`prompt=False` in scripts, tests, and any automated handoff**; popping UI from a
script is the failure this default exists to prevent.

## Per-tool escape hatches

| Hatch | Effect |
|---|---|
| `Autoload` off | the tool ignores its roamed section entirely |
| `Excludepars` / `Excludepages` | named pars/pages never roam — e.g. excluding the `Registry` page keeps a tool's bar position out of the file while its settings still roam |

All moot under project scope: nothing loads.

## The updater gate — check this before touching the updater

The updater uses the config file as its save-before-replace / restore-after-replace
handoff. **Under project scope both directions are gated**, so a tool-replacement
flow must carry sections itself — its own snapshot/apply around the swap, or
temporarily forcing global scope with a temp `Configfile` for the duration.
Writing replacement logic that silently relies on the file will lose user state in
every project-scoped install.
