---
status: in-force
summary: How a tool gets its custom parameters — reflection is the default, declaration is additive, and neither needs a base class. Includes the module-locality invariant that keeps generated properties from cross-wiring.
since: 2026-09-01 (parfield layer landed; backlog item 3)
skill: parameter-design
---

# CustomParHelper: reflect by default, declare when it helps

Two ways to get custom parameters onto a tool, and they are layers rather than
alternatives.

**Reflection is the default.** `CustomParHelper.Init(self, ownerComp)` reads
`ownerComp.customPars` and generates a property and callback routing for
whatever it finds. The parameters were made in the UI or by a build script;
the class discovers them.

**Declaration is additive**, and it happens at **init time**, where
`ownerComp` exists — so the call creates the parameter and returns the real
`Par`, and ordinary Python applies:

```python
class MyToolExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.Speed = CustomParHelper.Float(ownerComp, 'Speed', default=1.0,
                                           min=0, max=10, page='Settings',
                                           help='Playback speed multiplier.')
        if ownerComp.par.Advanced.eval():                 # conditionals
            self.Depth = CustomParHelper.Int(ownerComp, 'Depth', default=3,
                                             page='Settings', help='Depth.')
        for name in ('Alpha', 'Beta'):                    # loops
            CustomParHelper.Toggle(ownerComp, name, page='Flags',
                                   help='Flag %s.' % name)
        CustomParHelper.Init(self, ownerComp)
```

One helper per style — `Float` `Int` `Str` `Toggle` `Pulse` `Menu` `StrMenu`
`File` `Folder` `Header` `XYZ` `RGB` `RGBA` `OP` `COMP` `TOP` `CHOP` `SOP`
`DAT` `MAT` — each returning the `Par`, or a `ParGroup` for the multi-member
ones.

Order matters and is not incidental: **declarations must exist before
reflection runs**, so declare before `Init` (or use the class-body form, which
`Init` handles for you). Anything declared is then reflected like any other
parameter, which is why the layer needed almost no new surface.

### The class-body form

Still supported, and right for a purely static parameter set:

```python
class MyToolExt:
    Speed = CustomParHelper.ParFloat(default=1.0, page='Settings',
                                     help='Playback speed multiplier.')

    def __init__(self, ownerComp):
        CustomParHelper.Init(self, ownerComp)
```

**It cannot do conditionals, loops or computed values, and it cannot hand back
a Par.** A class body runs while the *class* is being defined — no instance, no
`ownerComp`, nothing to create a parameter on — which is why the init-time form
above is the general case and this is the convenience. The declaration object
stands in at class time and a descriptor resolves it at runtime; before `Init`
has created the parameter, touching it raises `AttributeError` naming the
reason rather than silently doing nothing.

### One implementation

Both forms go through `EnsurePar(ownerComp, name, field)` — the create /
refresh / restyle primitive. The init-time helpers are thin wrappers over it
and the class-body pass calls it per declaration, so the two styles cannot
drift apart in behaviour.

## What is guaranteed

- **Additive.** A class that declares no `ParField` is byte-identical to
  before — `EnsureParFields` returns immediately when it finds none. This is
  what let the layer land without touching a single existing tool.
- **A new parameter is seeded; an existing one is never clobbered.** On
  CREATION the declared `default` is written to the value as well, because TD
  otherwise leaves a fresh parameter at the style default — declaring
  `default=2.5` and reading `0.0` was the surprise this rule removes. On every
  run after that, `Init` refreshes label, help, range and menu entries and
  leaves the value alone, whatever the user or the saved `.toe` put there. So a
  declaration seeds a parameter once and describes it thereafter.
- **A style change is applied, not refused.** The declaration is the source of
  truth, so declaring `ParStr` over an existing Float rebuilds the parameter
  rather than telling the author to go delete it — reintroducing a manual step
  is exactly what this layer exists to remove. A style cannot change in place,
  so the rebuild carries across page position and each member's mode,
  expression, bind expression and value.

  **An export cannot survive it.** That link is owned by the exporting CHOP,
  not the parameter, so destroying the parameter breaks it and nothing here can
  restore it. It is reported loudly instead of lost quietly, and it is the one
  real cost of a restyle.
- **Help is strongly expected but not enforced.** A missing tooltip logs a
  warning where the author will see it. It deliberately does not raise:
  refusing to compile an entire extension over a tooltip is out of proportion,
  and the likely result of raising is that someone deletes the declaration
  instead of writing the help.

## Declarative callbacks

Parameters are declared; the handlers for them were still found by NAME
(`onPar<Name>`). Six decorators close that gap — `onPar`, `onParGroup`,
`onSeq`, `onSeqBlock`, `onAnyValueChange`, `onAnyPulse` — so a handler can be
named for what it does.

**It changes no dispatch code.** Harvest binds the decorated method to its
CONVENTIONAL name on the extension instance, so every existing
`hasattr(comp, 'onParSpeed')` finds it unchanged. That buys the entire callback
surface at once — per-par, pulse, ParGroup, sequence par, sequence block and
both general callbacks — with all their arity variants intact, because arity is
still read off the original function. The alternative, threading a resolver
through six dispatch sites in a file that syncs to 232 copies, was strictly
more risk for the same result.

`Init` harvests, so the signature is unchanged and a class that declares
nothing is unaffected.

Two reports the convention cannot produce: a declaration naming a parameter
that does not exist (the mistyped-`onParSpeeed` case, which today is simply a
method that never runs), and a collision with an existing conventionally-named
method — where the **real method wins** and the declaration is reported as
ignored, because silently shadowing working code is worse than a declaration
that does not take effect. Neither raises.

**The same invariant as the parfields and NoNode: the decorator returns the
function UNTOUCHED.** Dispatch infers arity from `__code__.co_argcount`; a
wrapper would describe itself instead. This is papercut (3) below turned into a
load-bearing constraint.

Measured 2026-09-01 on a rig running both styles at once: a real change to each
of `Gain` (value), `Reset` (pulse) and `Translate` (ParGroup) fired its
freely-named handler exactly once, alongside a conventional `onParSpeed` and a
NoNode decorator on the same extension. All six kinds resolve to the correct
conventional name; `onSeq`/`onSeqBlock` are verified at that level but not yet
exercised end-to-end, since the rig has no sequence parameter.

## Why there is no base class

tdp-TouchUtilCollection pairs its `parfield` declarations with an
`EnsureExtension` base class. The declarations are the valuable half; the base
class is coupling. CustomParHelper's whole appeal is that it needs no
inheritance, so adopting one would forfeit the reason to use it. A `ParField`
is an ordinary class attribute, which is why declaring costs nothing
structural and a tool can mix declared and reflected parameters freely.

## INVARIANT: an extension's module reference must be LOCAL

Generated properties are set on the **class**
(`setattr(extension_self.__class__, ...)`), closed over the single `owner_comp`
that called `Init`. That is safe only because `.module` is per-DAT: a COMP
resolving its extension locally —

```python
op('./MyToolExt').module.MyToolExt(me)
```

— gets a distinct class object, and therefore its own properties.

Point two COMPs at **one** module and they share a class. The second `Init`
rebinds the first COMP's properties to the second COMP's parameters, and the
first silently starts reading the wrong values. Measured 2026-09-01: all **726**
extension parameters in this project resolve locally, so nothing is broken
today — it is one convention away, which is why it is written down rather than
left as a comment.

Callback **routing** no longer has this problem. It used to: `OnValueChange`
and friends resolved through `EXT_SELF`, a class attribute answering "the last
extension to call `Init`" rather than "the extension owning this COMP".
`_extForComp(comp)` now resolves per-comp, and the two ParGroup/Sequence loops
route by `_par.owner`. Measured at the same time: 652 COMPs carry extensions and
21 carry more than one, but no pair declares two CustomParHelper users — so the
fix is hardening rather than a repair.

## Known rough edges

Neither is urgent; both hold for TD's conventions and neither is principled.

- **Callback arity is inferred from `__code__.co_argcount`.** It mis-dispatches
  for a method with default arguments, `*args`, or any decorator that wraps
  rather than returns the original function. `FNSCommand.fns_command` is safe
  here only because it returns the function untouched — a genuine wrapper would
  break routing.
- **ParGroup detection is `len(_par.parGroup) > 1`**, and group naming is
  positional (`Parname[:-1]`), both carrying the original author's own
  "Is there no better way?".

## Field types

`ParFloat` `ParInt` `ParStr` `ParToggle` `ParPulse` `ParMenu` `ParStrMenu`
`ParFile` `ParFolder` `ParHeader` `ParXYZ` `ParRGB` `ParRGBA`, and the
OP-reference family `ParOP` `ParCOMP` `ParTOP` `ParCHOP` `ParSOP` `ParDAT`
`ParMAT`.

All reachable off `CustomParHelper` (`CustomParHelper.ParFloat`), so the
existing single import line still suffices. `ParMenu` and `ParStrMenu` take
`names` and optional `labels` positionally.

### Keywords

Every keyword is a TouchDesigner **`Par` member**, set straight through —
`default`, `label`, `help`, `readOnly`, `startSection`, `min`, `max`,
`clampMin`, `clampMax`, `normMin`, `normMax`, `menuNames`, `menuLabels`,
`order`, `page`. There is no second vocabulary to learn and nothing here
re-documents them: see [Par Class](https://docs.derivative.ca/Par_Class) for
what each one does and which styles honour it.

Two are used at CREATION time rather than read off a finished parameter, so
they behave slightly differently from the `Par` member of the same name:

- **`page`** is the page NAME (a string) to create the parameter on, and the
  page is created if it does not exist. On a live `Par`, `.page` returns the
  Page object instead.
- **`order`** also fixes declaration order within the class. Omit it and
  fields are created in the order they are written.

A multi-member field (`ParXYZ`, `ParRGB`, `ParRGBA`) takes either one value
for every member or a sequence, one per member: `ParRGB(default=(0.2, 0.4,
0.6), ...)`.

Pass `enable_parfields=False` to `Init` to skip the pass entirely.

## Landing a change to CustomParHelper.py

The file syncs into every ExtUtils copy (239 under the root and 20 under
`/sys` at last count), and each copy's par exec DATs reach the class through
`mod(me.dock.name)` on EVERY call, so a saved edit is picked up everywhere at
once. That is the point of the single source. It also means the class object
is REBUILT in every copy, and everything `Init` had stored on it -- `EXT_SELF`,
`EXT_OWNERCOMP`, the callback filters -- is back to its class-body default.

What TD does about that, measured 2026-09-02 on the arity/group-name landing:
an extension whose imported module changed is marked dirty and re-initialised
LAZILY, on its next access. A `/sys` FNS_About nobody had touched still had an
unbound class an hour after the reload; reading its `extensions` re-ran its
`__init__`, and the class was bound to the right owner. The registry globals
were already bound because every re-registering host had touched them.
`_extForComp` reads `comp.extensions` when the class is unbound, so the first
callback after a reload goes through that lazy re-init and is delivered.

So a landing is: save the file, then reinitialise every owner that calls
`Init` (pulse `reinitextensions`, chunked across frames -- 227 owners took 12
chunks of 20) so the state is deterministic and an init error shows up now
rather than on someone's first click, then verify with a real callback:
`op('/NoNodeTest/nonode_harness').module.RunAll()` drives the decorator paths.
Expect a reinit burst in every tool, so do it when no other session is
mid-work. Owners that never call `Init` (32 tools, whose ExtUtils merely
carries the module) stay unbound by design.
