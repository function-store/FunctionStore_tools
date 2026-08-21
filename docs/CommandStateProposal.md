# Proposal: live state chips for quick-launch commands (registry 1.5.0)

For the TDXLPP side (FNS_CommandRegistry + launcher). Self-contained —
hand this to the agent working in that repo.

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
| `state={'method': 'GetState'}` | Name of a PROMOTED no-arg method returning bool or short str; escape hatch for non-par state (inverse pars, computed state) |

```python
@FNSCommand.fns_command(state='Active')
def ToggleActive(self):
	...
```

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
  raw text for strings. No chip when `state` absent.
- `fns_commands` protocol: items may carry `state` — additive, no
  version negotiation needed beyond the existing seen-catalog/struct
  field addition (same pattern as `hidden`/`builtin`).
- After a run, the palette already refetches/refreshes on rev... if it
  does not refetch post-run, do so for state-bearing rows — the run
  just changed the thing the chip shows.

## FunctionStore adoption plan (once this lands)

- The FNSCommand module master gains the `state` kwarg (additive — the
  attribute contract ignores unknown keys, so mixed versions are safe).
- ~25 commands declare state, mostly `state='Active'` one-liners on the
  Toggle wrappers; oddballs use the method form (HideTimeline's
  `Hidetimeline` par is inverted — a two-line `TimelineShown()` method
  reads better than an `invert` flag in the schema).
- No other changes: announcer, kit, and release pipeline are untouched.

## Explicitly out of scope

Push-updated chips while the palette is open (would need a state-change
event stream; the palette is summon-fetch today and that is fine).
