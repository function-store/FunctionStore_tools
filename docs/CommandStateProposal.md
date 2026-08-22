---
status: landed
summary: Design record for live state chips and param prefill on quick-launch commands (registry 1.5.0/1.6.0).
since: ce7b46e 2026-08-22
---

# Live state chips for quick-launch commands (registry 1.5.0/1.6.0)

> **STATUS: LANDED (2026-08-22).** Proposed in `c3c0029`, extended to values +
> param prefill in `d289c64`, adopted in `ce7b46e` — **24 commands ship live
> state chips** against registry 1.6.0. This file is kept as the design record:
> the problem, the query-time evaluation principle, and the rejected
> alternatives. It is **not** an open proposal; do not "hand it to the agent in
> that repo" as new work. Authoring guidance for the `state` kwarg lives in
> [CommandRegistration.md](CommandRegistration.md).

Written for the TDXLPP side (FNS_CommandRegistry + launcher).

## Problem

Toggle commands are blind: a palette row saying "Toggle AltSelect"
gives no clue whether AltSelect is currently on. Roughly a third of
FunctionStore's 81 registered commands are state-flippers (Active
toggles, mute, borderless, NDI/Spout out, timeline, hog...) — for all
of them the row is only half useful without the current state.

## Design principle: evaluate state at QUERY time, not announce time

`Commands()` already builds its wire list fresh on every call, and the
launcher fetches `fns_commands` when the palette is summoned. So if the
registry evaluates a declared state WHILE building each item, the chip
is always current — **no re-registration on state change, no staleness,
no rev churn**. Rejected alternatives, for the record:

- *State baked into labels + re-announce on every flip*: stale between
  announces (a wrong ON/OFF indicator is worse than none), noisy revs,
  and labels stop being stable muscle-memory anchors.
- *Tool-side dynamic labels via announcer-built specs*: duplicates the
  registry's harvest/derivation logic on the FunctionStore side — the
  exact single-source violation the FNSCommand module exists to avoid.

## Spec addition

New optional command field `state` (spec dict AND decorator kwarg):

| Form | Meaning |
|---|---|
| `state='Parname'` | Name of a custom par on the OWNER comp; registry evaluates `owner.par.Parname.eval()` at query time |
| `state={'method': 'GetState'}` | Name of a PROMOTED no-arg method; escape hatch for non-par state (inverse pars, child-widget values, computed state) |

State values are `bool`, `int`, `float`, or a short `str` (~16 chars) —
not just toggles. "Set volume" showing `0.8`, "Set BPM" showing `120`
are exactly as valuable as ON/OFF on a toggle.

```python
@FNSCommand.fns_command(state='Active')
def ToggleActive(self):
	...

@FNSCommand.fns_command(state={'method': 'GetVolume'})
def SetVolume(self, level: float):
	...
```

### Param prefill — the second half of the same idea

For value-setters the chip is half the win; the other half is the
prompt opening AT the current value. New optional param field:

| Field | Meaning |
|---|---|
| `current` | `'Parname'` or `{'method': 'GetX'}` — evaluated at fetch time like `state`; the launcher seeds the prompt with it instead of the static `default` (which remains the fallback when evaluation fails or the field is absent) |

`? volume` then opens pre-filled with `0.8` — nudge and enter, no blind
typing. Inline args are unaffected (`? volume 0.5` still runs
immediately). When a command has exactly one param and declares
`state`, the launcher MAY reuse the state value as the prefill without
a separate `current` declaration (they are almost always the same
value; explicit `current` wins when both exist).

Evaluation rules (registry-side, in the `Commands()` item build):

- Result rides the wire as `item['state']`: `True`/`False` (bool par or
  bool return) or a string capped at ~16 chars. Omitted entirely when no
  `state` is declared — fully backward compatible.
- **Guarded like everything else**: evaluation wrapped in try/except; a
  broken tool yields no `state` key (never breaks the listing). Method
  calls run on the main thread during a listing — the contract should
  say state methods must be trivially cheap (a par read, a bool), same
  spirit as the "handlers must be quick" rule.
- Harvest: the decorator stamps `state` into `_fns_command`; explicit
  specs carry the field directly; `_cleanSpec` validates (par exists is
  NOT checked at register time — owners may build pars late; the
  query-time guard covers it).

## Launcher side

- Row chip after the label: `ON` / `OFF` for bools (distinct colors),
  the value for numbers (floats trimmed, e.g. `0.8`, `120`), raw text
  for strings. No chip when `state` absent.
- Param prompts seed from `current` (or the single-param state reuse
  rule) instead of the static default.
- `fns_commands` protocol: items may carry `state` — additive, no
  version negotiation needed beyond the existing seen-catalog/struct
  field addition (same pattern as `hidden`/`builtin`).
- After a run, the palette already refetches/refreshes on rev... if it
  does not refetch post-run, do so for state-bearing rows — the run
  just changed the thing the chip shows.

## FunctionStore adoption (landed — ce7b46e)

- The FNSCommand module master gains the `state` kwarg (additive — the
  attribute contract ignores unknown keys, so mixed versions are safe).
- ~25 toggle commands declare state, mostly `state='Active'` one-liners
  on the Toggle wrappers; oddballs use the method form (HideTimeline's
  `Hidetimeline` par is inverted — a two-line `TimelineShown()` method
  reads better than an `invert` flag in the schema).
- Value-setters gain state + prefill: SetVolume (slider child value via
  method), HydroHomie SetInterval (`Intervalminutes`), QuickPane's
  split direction stays prompt-only. TDXLPP's own TD_Project built-ins
  (set cook rate, master volume) are natural adopters too.
- No other changes: announcer, kit, and release pipeline are untouched.

## Explicitly out of scope

Push-updated chips while the palette is open (would need a state-change
event stream; the palette is summon-fetch today and that is fine).
