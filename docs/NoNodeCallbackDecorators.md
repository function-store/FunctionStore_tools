---
status: in-force
summary: Callbacks declared on the method with a decorator and collected by HarvestCallbacks — why the marker attribute must return the function untouched, why targets are strings, and why rebuilding beats deregistering.
since: 2026-09-01 (decorator scheme landed alongside the parfield layer)
---

# NoNode: declaring callbacks on the method

NoNode already had a way to wire a callback: `RegisterChopExec` and its
siblings, called from `__init__`. The decorator form is a second way to say the
same thing, and it exists for reasons the imperative form cannot address.

```python
@NoNode.onChopExec(NoNode.ChopExecType.ValueChange, 'null_audio', 'chan1')
def audioMoved(self, channel, sampleIndex, val, prev):
    ...
```

`NoNode.HarvestCallbacks(self)` then registers every marked method. It needs
nothing from CustomParHelper — `Init` + `HarvestCallbacks` is a complete tool.

## Why bother, when Register* works

- **The binding sits at the callback.** A registration block elsewhere drifts
  from the methods it names, and the method name stops carrying the meaning
  (`onParSpeed` is a naming convention doing a wiring job).
- **A target that does not resolve is REPORTED.** This is the real defect this
  addresses: `RegisterParExec` returns silently when the parameter does not
  exist, so a mistyped `Speeed` produces a callback that never fires and never
  complains. Harvest names it instead.
- **Rebuilding replaces deregistering.** Harvest reconstructs the registry from
  the class every time, so a callback deleted from the code disappears with it.
  Nothing is left stale, which is the defect class behind the stranded-entry
  work (items 2d/2e) rather than a new convenience.

It does **not** raise on a bad target. One mistyped declaration should not stop
a whole tool from loading, and the likely response to a raise is that someone
deletes the declaration rather than fixing it — the same argument that keeps
missing parameter help at a warning.

## INVARIANT: the decorator returns the function UNTOUCHED

The decorator records a spec in a marker attribute (`_nonode_callbacks`) and
hands the function straight back. It must never wrap.

Dispatch infers how many arguments a callback wants from
`__code__.co_argcount` — that is what lets you drop `prev`, or `val` and
`prev`, off the right of a signature. A wrapper's `co_argcount` describes the
wrapper, so every decorated callback would be called with the wrong arity.
`FNSCommand.fns_command` is built the same way for the same reason, and this is
the one property a future edit must not casually break. It is covered by
`deco_arity_is_preserved` in the harness.

## Targets are strings, resolved at harvest

`@NoNode.onChopExec(..., 'null_audio', 'chan1')` names its target as a string,
never `op('null_audio')`. A class body runs while the *class* is being
defined — there is no instance and no `ownerComp`, so an `op()` call there
resolves against nothing. This is exactly the constraint that pushed the
parameter fields to an init-time API (see
[CustomParHelperContract](CustomParHelperContract.md)); here the resolution can
simply be deferred to harvest, so the class-body form survives.

Strings resolve relative to the extension's COMP. Omitting the owner on
`onParExec` watches the extension's own COMP.

## Arming is implicit, and that is worth knowing

Registering does not point an exec DAT at anything by hand. Each NoNode exec
DAT's target parameter is an **expression over the registry** —

```
extChopValueChangeExec.chops =
    list(NoNode.CHOPEXEC_CALLBACKS.getRaw().get(ChopExecType.ValueChange, {}).keys())
```

— so a registration arms its DAT as a side effect of existing, and
`RegisterParExec` only has to flip `active`. The decorator needed no arming
code of its own for this reason. `__markOperatorAsWatched` is **not** part of
this: it sets the node colour and stores a move-survival token, nothing more.
`deco_arms_exec_dat` is the case that notices if the expression mechanism
stops holding, because every other case fires dispatch directly and would pass
against a DAT that watches nothing.

## It coexists with CustomParHelper — measured

"Without initing CustomParHelper" describes what the decorator does not
*require*, not what it is compatible with. The two are independent and both
fire.

They watch through different exec DATs: CustomParHelper's `extParExec` targets
the COMP and derives its `pars` from `customPars` filtered by `EXCEPT_PAGES` /
`PAR_CALLBACKS`, while NoNode's `extParExecNoNodeValueChange` derives `ops` and
`pars` from NoNode's registry. Neither reads the other's state.

Measured 2026-09-01 on a rig running both, with one real change to a custom
`Speed` parameter carrying an `onParSpeed` method *and* an `@onParExec`
decorator: **both handlers fired, once each**, no script errors, suite green.

The practical consequence is the thing to know: on the *same* parameter you get
**two** callbacks, so pick one style per parameter rather than both.

**Superseded, same day:** this doc first said a freely-named handler for your
own custom parameter had to go through NoNode, because CustomParHelper routes
by method name. CustomParHelper now has its own decorators
(`@CustomParHelper.onPar` and five siblings, see
[CustomParHelperContract](CustomParHelperContract.md)), and for a parameter on
your own COMP they are the better tool: they use the exec DATs already watching
it instead of adding a second watcher. Use NoNode's `onParExec` for parameters
on OTHER operators, which is what it is for.

Omitting the owner (`@NoNode.onParExec(event, None, 'Speed')`) watches the
extension's own COMP; covered by `deco_dispatch_own_par` and
`deco_own_par_arms_exec_dat`.

## Known: a transient expression error while a watched owner is destroyed

When a registered parameter's owner is destroyed, the par-exec DAT's target
expression evaluates over a `Par` whose owner is gone and the DAT errors until
the registry is rebuilt — one frame, in practice, after which it clears on its
own. Measured 2026-09-01 during a harness run, which destroys and recreates its
targets on every case.

The expression is stock NoNode, not decorator code; it was simply never
exercised before, because nothing in this project registered a *parameter*
callback through NoNode until now. Left as-is deliberately: it is transient and
self-healing, and hardening it means restamping the expression across all 65
shipped ExtUtils copies for a one-frame cosmetic error.

## Coverage

`NoNodeTest/nonode_harness.py`, 25 cases, all passing — the 15 that predate this
plus 10 for the decorator: dispatch for chop/DAT/par, coexistence with
`Register*` on one extension, exec-DAT arming, a bad target reported rather than
dropped, idempotent re-harvest, and arity preservation.

Two of the original 15 had to be **scoped**, not weakened: they asserted over
the whole registry (`len(keys) == 1`, `not keys`) and so assumed the rig carried
exactly one registration. They now assert about the operator under test, and
`move_prunes_when_gone` checks that every surviving key still resolves — a
stricter claim than an empty registry, and one that catches a prune that sweeps
too widely.
