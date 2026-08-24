---
status: in-force
summary: Where promoted registry globals live (/sys/FNS_Registries) and the six invariants that govern the home.
since: a019218 2026-08-21
skill: fns-registry
---

# Contract: where promoted registry globals live

**Status:** in force since `a019218` (2026-08-21). Minor architecture change
— location only, no API change. Read this before touching registry promotion
code; the full scheme (roles, publishing, surfaces) is in
[RegistryScheme.md](RegistryScheme.md).

## What changed

Promoted registry globals used to sit as direct children of `/sys`
(`/sys/FNS_ToolbarRegistry`, …). They now live in one container:

```
/sys/FNS_Registries/
├── FNS_ConfigRegistry        op.FNS_CONFIGREGISTRY
├── FNS_MainMenuRegistry      op.FNS_MAINMENUREGISTRY
├── FNS_NavbarRegistry        op.FNS_NAVBARREGISTRY
├── FNS_OpMenuRegistry        op.FNS_OPMENUREGISTRY
├── FNS_PaneTypeRegistry      op.FNS_PANETYPEREGISTRY
└── FNS_ToolbarRegistry       op.FNS_TOOLBARREGISTRY
```

Nothing that *consumes* a registry changed: global OP shortcuts resolve from
any depth.

## Invariants

**C1 — One home.** `/sys/FNS_Registries`. A **bare `baseCOMP`**: no
extension, no DATs, no custom pages or pars, no tags, no shortcut, no clone,
no `externaltox`. It is a folder. Do not give it behavior — if you find
yourself wanting to, the logic belongs on `RegistryBase` or on a registry.

**C2 — One resolver.** `RegistryBase._sys_comp(create=False)` is the only
thing that knows the path, via `SYS_HOME = 'FNS_Registries'`. Never hardcode
`/sys/FNS_Registries` in registry code — go through `_sys_comp()`, and reach
a specific global through its shortcut. (Two deliberate exceptions, both
outside `RegistryBase`: `InstallerExt.SYS_REGISTRY_HOME` and the literal in
`registry_presave_exec.promotedRegistries()`. Keep them in step.)

**C3 — Reads never create.** Only the promotion path passes `create=True`.
Asking "is there a home?" must not grow one in a project that has no
registries.

**C4 — Consumers use the shortcut, never a path.** `op.FNS_TOOLBARREGISTRY`,
guarded — no registry is guaranteed to exist:

```python
reg = getattr(op, 'FNS_TOOLBARREGISTRY', None)
if reg is not None and hasattr(reg, 'Register'):
    ...
```

**C5 — This is per-process state.** `/sys` never saves with the `.toe`.
The home and everything in it are rebuilt on every project open by whichever
master promotes first. Never treat a global as durable storage.

**C6 — Bare `/sys` is legacy and gets absorbed.** A global found as a direct
child of `/sys` predates this change. It is relocated **regardless of
version**: merge its entries → destroy it → re-promote into the home. Two
branches, both verified:

| trigger | path |
|---|---|
| a host inits and sees it | `_installGlobalRegistry` sets `relocating`, calls `_replace_global_registry(force=True)` |
| the legacy copy inits itself | `_isLegacySysCopy()` → promote into home, then retire self on `run(..., delayFrames=5)` |

`_find_sys_registries()` deliberately scans **both** locations so parked
(shortcut-less) legacy copies are reconciled too, and
`_reconcile_parked_sys_registries` refuses to promote a winner that is not
already in the home.

## What this does NOT give you

- **Equal versions: the incumbent wins.** `_check_version_against` stands
  down on `our_version <= their_version` — the whole version, not just the
  major. A same-version reinstall leaves the old global live *inside the
  home*. Only the bare-`/sys` case is unconditional (C6).
- **A choice about which version to promote.** There is none to make: newest
  wins, silently. The comparison used to raise a `ui.messageBox` on a major
  mismatch; because promotion runs during project load once per registry
  copy, that surfaced as a stack of modal dialogs and wedged extension init
  (2026-08-24). Nothing in this path may prompt.
- **The installer reports, it does not force.**
  `InstallerExt.PromotedRegistries()` — exported from `install.py`, and on
  every `InstallPlan` result under the `registries` key — returns
  `{name, path, version, shortcut}` per global. It is a snapshot of the
  running process. Forced re-promotion was considered and deliberately not
  built; add it explicitly if you need it.
- **Shipped artifacts lag, but do not guess how much.** Ask the tooling, not
  your instincts: `exec(open('packaging/release_one.py').read()); Preflight()`
  is read-only and authoritative. It distinguishes *registry ripple* (a
  vendored host copy merely looking newer — a warning, not a blocker; empty
  as of `790be63`) from `unlanded` (a package whose own code is genuinely
  newer than its `.tox` — a blocker). After the move that was six packages:
  CustomParTools and the five registry packages. Landing them is PI's
  per-package **Save** button; there is no script API, and every scriptable
  path in `release_one.py` publishes. See
  [packaging/RELEASING.md](../packaging/RELEASING.md).

  Mixed old/new hosts converge safely regardless (an old one promotes to bare
  `/sys`, a new one relocates it), which is what C6 buys. C6 can be deleted
  once no shipped artifact predates the move.

## Editing the registry code

`scripts/shared/RegistryBase.py` is shared by **83 DATs** with
`syncfile=True`. Saving it hot-reloads every one and reinitializes the whole
registry family — including the live globals driving the toolbar, navbar,
main menu and op menu. So:

1. Patch a **copy**, `py_compile` it, then move it into place. A syntax error
   landed directly takes down every registry at once.
2. Check `get_sessions` first — one writer per checkout.
3. After landing, verify (below) before doing anything else.

**If a shared-source edit does not reach a host, check its `file` par.** The
par value is the carrier — 62 of the 83 DATs have no tags at all and still
resolve to the shared file, so tags prove nothing. button_hog's
`FNS_ToolbarRegistry/RegistryBase` was the one host pointing at a per-op copy
and therefore sat out this whole change; repaired in `790be63` (par re-pointed,
stray `text` tag dropped, duplicate `.py` deleted). Worth re-running the
census in the recipe below after any bulk registry work.

## Family members outside RegistryBase

`FNS_CommandRegistry` does **not** subclass `RegistryBase`. Its source lives
in the **TDXLPP** repo
(`utility/TDXLauncherUtility/FNS_CommandRegistry/FNSCommandRegistryExt.py`,
its own Envoy on port 9879) and it reaches this project only through
`../TDXLPP/release/TDXLauncherUtility.tox`. It carries a hand-ported copy of
the same shape — `SYS_HOME`, `_sysHome(create=False)`, and the same
relocate-if-parked rule — so it lands in the same home. **A source edit there
does nothing here until TDXLPP re-releases its tox**; `Repromote()` is its
dev helper.

Any future non-`RegistryBase` member must honour C1–C6 the same way.

## Verification recipe

Every block below was run against the live project at `a019218` and passes.

```python
home = op('/sys/FNS_Registries')
assert home and not home.extensions[0]           # C1: bare folder
for c in home.children:                           # shortcut points into home
    assert getattr(op, c.par.opshortcut.eval()).path.startswith(home.path)

# C6: nothing left parked in bare /sys. FNS_CommandRegistry is the one
# expected holdout until TDXLPP re-releases -- see "Family members" above.
strays = [c.name for c in op('/sys').children
          if 'Registry' in c.name and c is not home]
assert strays in ([], ['FNS_CommandRegistry']), strays
```

Then confirm entries survived and surfaces still render — a relocation that
loses registrations looks identical to a healthy one from the outside:

```python
{c.name: len(next(e for e in c.extensions if hasattr(e, 'stored'))
              .stored['PaneRegistry']) for c in home.children}
# baseline at a019218: Config 45, Toolbar 37, Navbar 13,
#                      MainMenu 11, OpMenu 3, PaneType 2
len([c for c in op('/ui/dialogs/bookmark_bar').children
     if c.name.startswith('tbmirror_')])   # 22 at a019218
```

`op('/FNSTools/registry_presave_exec').module.healAllRegistries()` should
return all six names. `get_op_errors` on `/sys/FNS_Registries` must be clean.

Finally, confirm no host has drifted off the shared source — this is what
caught button_hog:

```python
import collections
c = collections.Counter(d.par.file.eval()
                        for d in op('/').findChildren(name='RegistryBase'))
assert list(c) == ['scripts/shared/RegistryBase.py'], dict(c)
```
