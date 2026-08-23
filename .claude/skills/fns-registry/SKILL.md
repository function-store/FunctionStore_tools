---
name: fns-registry
description: "MUST READ before building, modifying or consuming an FNS registry (Toolbar, Navbar, MainMenu, OpMenu, PaneType, Config, Console), before stamping a registry host into a tool, and before copying any host-carrying or clone-bound COMP. Consumer rules, /sys home invariants, new-registry checklist, and the hazards paid for once."
---

# FNS registries — building, hosting, consuming

The scheme: one promoted global manager per surface, many host publishers. Tools
*publish into* central managers instead of surfaces hardcoding their contents.
Full model (surface specifics, entry data model, RegistryBase contract,
packaging, migration lessons) is in
[docs/RegistryScheme.md](../../../docs/RegistryScheme.md); the home rules in
[docs/RegistryHomeContract.md](../../../docs/RegistryHomeContract.md); publishing a
console tab in [docs/ConsoleTabContract.md](../../../docs/ConsoleTabContract.md).

## The eight registries

`FNS_PaneTypeRegistry`, `FNS_ToolbarRegistry`, `FNS_NavbarRegistry`,
`FNS_OpMenuRegistry`, `FNS_MainMenuRegistry`, `FNS_ConfigRegistry`, `FNS_Console`,
`FNS_HubRegistry` — each reached as `op.FNS_<NAME>` / `op.FNS_<NAME>REGISTRY`.

**Management UI = `FNSTools/FNS_Hub`** (core; the FNS main-menu button + a
tabbed window). The Toolbar/Navbar/MainMenu configurators are its tabs and
there are NO per-bar gear buttons. Tabs come only from `FNS_HubRegistry`
hosts -- never by scanning; contract in
[docs/HubContract.md](../../../docs/HubContract.md). Drop-to-register is the
hub's (drop on the FNS button or the window) and stamps through the
master's `StampHost`.

## Consuming a registry

```python
reg = getattr(op, 'FNS_TOOLBARREGISTRY', None)
if reg is not None and hasattr(reg, 'Register'):
    ...
```

- **Always guarded** — no registry is guaranteed to exist in a given project.
- **Shortcut, never a path.** `op.FNS_TOOLBARREGISTRY`, not
  `op('/sys/FNS_Registries/FNS_ToolbarRegistry')`. Globals have been relocated
  mid-session before; only shortcut-identity code survived.
- The unprefixed spellings (`op.TOOLBARREGISTRY`, …) are pre-v3.0.0 and resolve
  to `None`.

## Where the globals live — the invariants

1. **One home**: `/sys/FNS_Registries`, a bare `baseCOMP` — no extension, DATs,
   pars, tags, shortcut, clone or `externaltox`. It is a folder. If you want to
   give it behavior, the logic belongs on `RegistryBase` or on a registry.
2. **One resolver**: `RegistryBase._sys_comp(create=False)` via
   `SYS_HOME = 'FNS_Registries'`. Never hardcode the path in registry code. Two
   deliberate exceptions outside `RegistryBase` — `InstallerExt.SYS_REGISTRY_HOME`
   and the literal in `registry_presave_exec.promotedRegistries()`; keep them in step.
3. **Reads never create.** Only the promotion path passes `create=True`.
4. **Per-process state.** `/sys` never saves with the `.toe`; the home is rebuilt
   on every project open. Never treat a global as durable storage — re-register
   on init.
5. **Equal versions: the incumbent wins.** A same-version reinstall leaves the
   old global live. Only a bare-`/sys` legacy copy is relocated unconditionally.

## Adding a new registry — checklist

1. Copy an existing master (ToolbarRegistry is the smaller template); rename
   COMP + ext DAT to `MyRegistry` / `MyRegistryExt` (names must match
   `REGISTRY_NAME` / `EXT_NAME`).
2. Write the subclass: class constants, surface hooks, public API,
   `_applyHostRegistration` override if the Registration page differs.
3. Adjust the Registration page pars + help text; set About `Version` to
   `0.1.0`.
4. Externalize COMP (tdn) + both `.py` DATs; verify `get_op_errors` clean.
5. Reinit → confirm `/sys/FNS_Registries/MyRegistry` promotes, shortcut resolves,
   Registration page stripped on the global.
6. Pilot: copy the host into one tool, configure, `Autoregister` on; verify
   the entry + surface artifact + unregister cascade (wait a frame after
   par changes).
7. Add `pre_release` scrub hook; `ExportPortableTox` to `modules/release/`;
   load-test the tox in a scratch COMP.
8. Cold test: restart TD (or drop the tox in a bare project) and verify the
   full bootstrap.

## Hazards — paid for once, do not rediscover

- **CustomParHelper `EXT_SELF` is class-level** — with a shipped host plus a
  `/sys` copy, callbacks can hit the wrong instance. Always route through
  `_hostExtFromPar(par)` (resolve the ext from the parameter's owner).
- **First-compile fragility**: a copy's extension initializes DURING
  `copy()`, before docked ExtUtils resolves; the CustomParHelper import line
  needs the `me.parent().op('ExtUtils')` fallback, and promotion needs the
  reinit retry loop.
- **Storage pickling**: strings only (see §3).
- **Par callbacks fire a frame late** — never assert their effects in the
  same script that set the parameter.
- **`list.extend()` returns None**; build `panes`-style lists with `+`.
- **Panebar specifics**: TD's `cellselectid` fires on right-click too — the
  pane registry rewrites dropdowns to `celllselectid` (left-only); panelexec
  templates copied into dropdowns lose relative `panels` wiring and must be
  re-pointed after copy.
- **`run()` scheduling**: always `delayRef=op.TDResources` so delays survive
  timeline stops.
- **Externalizing a DAT that carries a foreign file binding** (tags/file par
  from another project) can raise a modal that blocks TD's main thread —
  expect it when adopting components from other projects.
- **Cook-disabled tools cannot host widgets or registries.** A COMP with
  `allowCooking=False` (e.g. midiMapper) can't compile extensions and its
  panels don't render — so its toolbar button must live OUTSIDE it (toolbar
  chrome, or a small always-cooking wrapper). Check `allowCooking` before
  moving a widget into a tool.
- **execute_python rollback restores only ops the script CREATED — not ops
  it destroyed.** A batch that destroys legacy state and then fails leaves
  the destroyed ops gone. Destroy last, or keep a restore source (the
  external .tox) at hand.
- **Widgets sized by their panel parent** (`me.panelParent(1).height - 5`)
  break when moved out of the bar into a non-panel tool COMP — constify
  `w`/`h` on migration.
- **A copy of a suspect-bound master INHERITS its externaltox binding --
  and boot reloads the WRONG tox into it.** Copying OpMenuRegistry to seed
  ConfigRegistry carried `externaltox=.../OpMenuRegistry.tox` +
  `enableexternaltox=on`; the first cold boot reloaded OpMenu content into
  every ConfigRegistry copy (master became a hybrid, hosts became pure
  OpMenu, the removed `pi_suspect` tag came back). EVERY stamp recipe must
  sever it: `enableexternaltox=False`, `externaltox=''`, strip
  `pi_suspect` -- and when the master doubles as a bound host, also fall
  its copied Registration-par BINDs back to CONSTANT before setting values
  (assigning through a dangling bind raises).
- **Tools with `enableexternaltox=False` are carried by the ROOT toolkit
  tox, not their own.** Their own `.tox` saves are dead files at boot; the
  root `FunctionStore_tools_2025.tox` is their real persistence. Landing
  discipline: save the ROOT tox too, not just the per-tool suspects
  (paid for: 4 tools + the root host lost their ConfigRegistry hosts on a
  cold boot because only per-tool toxes were saved).
- **Execute DATs gate every callback behind its own toggle par.** A
  `projectpresave` callback never fires until `par.projectpresave = True`
  -- writing the function into the DAT is not enough (paid for: the
  config pre-save hook silently did nothing on the first project save).
- **Never stamp a host into a clone MASTER** -- `/FNSTools/webBrowser` is
  cloned by `ColorUI/webBrowser`; a host stamped into it replicated into the
  clone and the clone's copy won the registration. Hosts for shared chrome
  live in the hub (`FNS_Hub/FNS_HubRegistry`, `Comp='../webBrowser'`).
- **The /sys global runs a COPY of the registry ext DAT with NO file sync.**
  Editing `<X>RegistryExt.py` reaches the master only -- push the master's
  DAT text into the global and reinit (or re-promote) before testing.
- **OP-reference par VALUES on a COMP owner resolve sibling-relative**
  (`Comp='select1'`), while `'..'` still means the parent -- `'../select1'`
  is invalid.
- **A deferred retry loop that gives up must clear its "queued" flag**, or
  nothing can ever re-arm the sync (paid for in HubRegistry).
- **TD's parameter-expression evaluator mangles the `-(-n // c)` ceil idiom**
  (evaluates to 1 on a par where `evalExpression` gives the right answer);
  write `(n + c - 1) // c`. Also: a par expression is NOT re-evaluated when a
  DAT's row count changes -- route counts through a custom par.
- **A COMP's size expression must not read its own width** (stale mid-layout);
  read `parent().width`. TD's Grid Rows alignment scales cells to fit rather
  than wrapping -- the hub's tab bar lays its cells out by expression instead.
- **A Select mirror forwards clicks but NOT drag/drop** -- the mirror's own
  Drag/Drop pars decide. `RegistryBase._mirrorDragDrop(mirror, source)` copies
  a source's callback-mode settings onto its mirror; call it from every
  mirror inject (Toolbar/MainMenu do). `onDragStartGetItems` must return a
  plain LIST; a textCOMP needs `dragdropmode='panel'`.
- **A Select mirror draws its source at the SOURCE's size; `fill` on a source
  with no panel parent collapses to nothing.** Size the source with
  `w`/`h` expressions on the container it is mirrored into.
- **Copying ANY COMP whose subtree contains an enabled clone host crashes
  TD** — not just clone copies inside drop-event stacks. Copying
  NavbarConfigurator (which ships its clone-bound gear host) via a plain
  MCP copy hard-crashed TD 2025.33070 (mainmenu port, 2026-08-10). Before
  copying a configurator or any host-carrying package: set the inner
  host's `enablecloning=False` (and the source's `initextonstart=False` so
  the copy's extensions stay quiet), copy, then restore — wrapped in
  try/finally.
