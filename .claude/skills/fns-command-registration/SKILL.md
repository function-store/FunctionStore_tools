---
name: fns-command-registration
description: "MUST READ before authoring, editing, or debugging an FNS quick-launch command, or touching ExtUtils / FNSCommand / the announcer / extutils_distributor. Authoring recipe, announcer guards, the ten paid-for traps, health check."
---

# Authoring FNS quick-launch commands

How to ship a command. **Why it is shaped this way** — clone-distribution vs
vendoring, announcer vs explicit lifecycle, and the costs accepted — is in
[docs/CommandRegistration.md](../../../docs/CommandRegistration.md); read that
before proposing a change to the scheme itself. The wire contract lives in the
TDXLPP repo (`docs/fns-command-registry.md`); this is the FunctionStore side.

## Author a command

**Internal tool (has a root ExtUtils)** — two lines, no lifecycle code:

```python
FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand')  # import

class MyToolExt:
	@FNSCommand.fns_command(help='Set the project tempo')
	def SetBpm(self, bpm: float = 120, sync: bool = False):
		...
```

Registration is automatic — the `FNSCommandAnnouncer` in your ExtUtils announces
the tool ~60 frames after load. Label derives from the CamelCase name, help from
the docstring's first line, prompted params from the signature (type hints →
styles, `typing.Literal[...]` → menu, no default → required).

- Extras: `fns_command(label=…, help=…, hidden=True, params=[…])`.
- **Never set `builtin=`** — that flag is for TD/system commands (TDXLPP-side).
- Changed your command set at runtime: `op('ExtUtils/FNSCommandAnnouncer').Announce()`.
- **Third-party tool**: drop `modules/release/FNS_CommandKit.tox` inside the
  tool, then the same two lines with `FNSCommand = op('FNS_CommandKit').mod('FNSCommand')`.

**Live state chips** (registry ≥ 1.6.0) — declare `state='Parname'` (custom par
on the owner) or `state={'method': 'GetX'}` (promoted no-arg method; use it for
inverted pars, child-widget values, computed state). Evaluated at QUERY time, so
it is always fresh and needs no re-announce. bool → ON/OFF chip; number/str →
value chip. A single-param command with `state` reuses it as prompt prefill;
otherwise a param may declare `current`.

## Hard rules

- **Ids are permanent.** Launcher curation, history and user presets key on
  `tool#id`. Renaming a shipped id — or the tool COMP — orphans all three. Treat
  every shipped id as public API.
- **Caps**: 24 commands/tool, 6 params/command, menus ≤ 16 entries.
- **Handlers run synchronously on the main thread.** Return fast; kick long work
  off with `run(..., delayFrames=1)`. Returning a dict with `ok: False` marks the
  run failed in the palette footer.
- **Registry-family exts are the deliberate exception**: their hosts carry slim
  ExtUtils with no announcer, and only the `/sys` GLOBAL may register. Keep the
  `_isCommandOwner()` guard comparing `self.ownerComp is op.FNS_<NAME>REGISTRY`
  — identity via shortcut, **never** path.

## Traps — all paid for, do not rediscover

1. **Cloning does not carry dock relationships.** A clone whose children get
   rebuilt comes out undocked, breaking `extParameter`'s Pages expression
   (`mod(me.dock.name)`). Run the distributor after any clone surgery.
2. **Cloning forces CHILDREN, never the clone COMP's own pars.** Wire
   `extension1` on each clone once. (This is also *why* the announcer works: it
   is a child of ExtUtils, so its own `extension1` IS forced.)
3. **`root.findChildren` does not see `/sys`.** Sweeps and the registry's
   `RescanTools` miss it — and RescanTools PRUNES owners it cannot rediscover.
   After any rescan, re-announce the `/sys` globals via their `op.FNS_*` shortcuts.
4. **Address `/sys` globals by shortcut, never path.** A peer session relocated
   them mid-work; only shortcut-identity code survived.
5. **A DAT's cached module recompiles only on DAT change.** Making a missing
   module resolvable is not enough — touch the importing DAT (no-op text write)
   or its class keeps stub bindings.
6. **Batch text surgery: never cut to a searched terminator.** Cutting "to the
   second `return None`" truncated 6 exts (5 silently valid); excising "def →
   next def" ate the DECORATOR line of the following method (3 commands vanished
   with zero errors). Verify any batch edit with an AST parse AND a `def`-name
   diff against git HEAD.
7. **syncfile DATs write through to disk immediately** — the on-disk `.py` is
   NOT a pre-edit backup. Git HEAD is.
8. **PI's dirty flag does not trip on clone-driven child changes.** After clone
   surgery build the save list from every suspect that OWNS an affected instance,
   never from the Dirty column — 47 tools would have silently reverted on boot.
9. **PI's release scrub is tag-gated by history.** Keep the generic rules in
   `CompReleaseManager.prepare()` when touching PI.
10. **`mod()` is path-relative, not search-up** — from a sibling COMP use
    `mod('../FNSCommand')`.

## Operations

Health check, after anything ExtUtils/command related:

```python
m = op('/FNSTools/CustomParTools/QuickExt/extutils_distributor').module
m.survey()             # healthy=True, or a precise list of what is wrong
m.rollout(apply=True)  # fixes clone links, dock drift, slim modules
```

Inventory: `op.FNS_COMMANDREGISTRY.Commands()` / `.Run(key)`. Baseline **81
commands from 42 owners** — the per-tool mapping and the deliberate skips are in
[docs/CommandRegistryCandidates.md](../../../docs/CommandRegistryCandidates.md).

**Saving**: the suspect regime — PI `Save()` per owner, leaves first, `/FNSTools`
root last. PreviewPanel25 and private_investigator1 persist via their OWN
externaltox pars, not PI's table.

**"My command doesn't show"** — in this order:

1. Does `op.FNS_COMMANDREGISTRY` resolve? No launcher companion means nothing
   surfaces, by design. Check this first, not last.
2. Is the method decorated AND promoted (uppercase)? Does the tool ext compile?
3. `'fnscommands' in tool.tags`? If not, the announcer's guard did not see your
   commands at +60 frames — call `op('ExtUtils/FNSCommandAnnouncer').Announce()`
   and read its return.
4. Row present but stale after an edit → `Announce()` again. Ext reinit does
   NOT re-register (the legs were removed).
5. `/sys`-owned rows missing after a rescan → trap #3.
