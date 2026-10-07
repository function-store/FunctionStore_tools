---
status: open
summary: Backlog for nine core-tool defects and features raised 2026-08-31 — SwapOps connector loss (landed), NoNode's identity defect, stuck modifier keys, QuickMarks naming, command authority, ParOPDrop #127, non-roaming registry groups, rolloverParGroup. Every claim measured live; per-item status in the table up top.
since: 2026-08-31 (owner raised nine items; scoped and measured the same day)
verified: 2026-09-01 — all behavioural claims measured live in TD 2025.33070 via Envoy. See the Appendix for the raw probes.
---

# Core tools backlog

Nine items raised by the owner on 2026-08-31, scoped the same day against the
live project (TD 2025.33070, root `/FNSTools`). This document is the record of
that discussion and the actionable list. Items 1 and 2a are built; everything
else is open. Per-item state is in the table below.

Several of these had been carried as folklore ("NoNode is a bit fucky",
"`isMultiInputs` is the opposite for some reason"). The point of this pass was
to replace the folklore with measurements, so the fixes can be designed instead
of guessed at. Where a long-standing belief turned out to be half-right, that is
said plainly rather than quietly corrected.

Each item is **Symptom → Measured → Fix → Open**. "Measured" means a probe was
run in the live session; the Appendix carries the raw output.

## Status at a glance

**This table is the status of record.** The frontmatter `status:` is
per-document and `docs_index.py` validates nothing finer, so per-item state
lives here — move an item here first, then update its section. The bracket tag
on each heading is the *kind* of work, never its state.

| # | Item | Kind | Status |
|---|---|---|---|
| 1 | SwapOps connector indices + COMP connectors | bug | **DONE** — 16/16, `3365c5e` + `e01b657` |
| 2a | NoNode: OP objects are unstable dict keys | bug | **DONE** — 11/11, intermittent bug, one file |
| 2b | NoNode: "exec DATs never targeted" | — | **WITHDRAWN** — the claim was wrong |
| 2c | NoNode has no internal callers | finding | informs priority; no action |
| 2d | NoNode: Deregister* was hash-based | bug | **DONE** — raised KeyError, not just leaked |
| 2e | NoNode: moved FOREIGN watched op | bug | **DONE** — Heal() on dispatch, 1.6us; singleton case residual |
| 2f | Pasted COMP never initialises its extension | bug | **DONE** — extAutoInit in master ExtUtils; `.toe` saved 2026-09-01 |
| 3 | CustomParHelper + TouchUtilCollection | todo | **DONE** — parfield layer + fix (2) + invariant (1); (3)(5) papercuts |
| 4 | Stuck modifier keys | bug | **DONE (Windows)** — shared helper; macOS unverified, falls back |
| 5 | QuickMarks names + command/hotkey key mismatch | feature + bug | **DONE** — sequence store, names, migrated |
| 6 | Command authority (`context` field) | feature | **DONE** — field + resolver + registry 1.8.0 harvest |
| 6b | FNS_CommandRegistry adopted from TDXLPP | — | **DONE** — PI-owned, promoted, 99 cmds, 97 byte-identical |
| 6c | Kit vs registry split | question | **RESOLVED** — keep apart; drift premise measured false |
| 7 | ParOPDrop: drop a CHOP/DAT (issue #127) | feature | **DONE** — type decides; no `*`-vs-channel setting |
| 8 | Registry group structure does not roam | — | **WITHDRAWN** — it already roams via FNS_Hub |
| 9 | `rolloverParGroup` in QuickParCustom + ParOPDrop | feature | **ParOPDrop DONE**; QuickParCustom needs a hover test |
| 10 | Version commands; dedupe by package | feature | **DONE** — opt-in `canonical` + registry 1.9.0 arbitration |
| 11 | Sweep commands for context/surface/capability | feature | **DONE** — context 2→25/103, help 103/103 |
| 12 | ExtUtils: minimal variant unbound, Stubser, name collision | bug | **DONE** — `716d194` + `4196273` |
| 13 | Three-way `.py` split: `FNSTools/` vs `modules/suspects/` vs `scripts/` | refactor | **DONE** — one tree per role; `FNSTools/*.py` retired |
| 14 | 3 RegistryBase copies frozen; `get_op_errors` misses script errors | bug | **DONE** — 106/106 on the sync rail |
| 15 | NoNode: declarative callback decorators | feature | **DONE** — harvest + 10 harness cases, 25/25 |
| 16 | 63 ExtUtils clones watched the MASTER's pars | bug | **DONE** — self-inflicted; 378 pars → `../..` |
| 17 | CustomParHelper declarative callbacks | feature | **DONE** — 6 decorators, no dispatch changes |
| 18 | Follow-ups batch: palette presets / blur / hide, QuickMarks double retrieve + auto-name, CustomParHelper arity + group naming | feature + bug | **DONE** 2026-09-02 — see §18; blur's click-outside half is a hand test |
| 19 | ExtUtils fleet rollout + observer guard + doc hygiene | maintenance | **DONE** 2026-09-02 — see §19 |
| 20 | FNS_PreviewPanel: PreviewPanel25 becomes a gated package | packaging | **DONE** 2026-09-02 — see §20 |
| 21 | Shared command curation file (palette + launcher) and config hygiene | config | **DONE** 2026-09-02 (launcher side pending their owner) — see §21 |
| 22 | FNS_CommandRegistry 0.1.1 re-release: annotations out, pre_release hook, cooking-enabled verification | packaging | **DONE** 2026-09-02 — see §22 |
| 23 | FNS_BeatMod: beat-synced parameter modulation (Base-gated) | tool | **DONE** 2026-09-02 — see §23 |
| 24 | ConfigRegistry: the roaming file carries a schema beside each value | feature | **DONE** 2026-09-10 — built in `_parSchema`; reaches the file at the next boot, see §24 |
| 25 | FNS_BackupCleaner: TDBackupCleaner adopted as a Base-gated hub tool | tool | **DONE** 2026-09-10 — see §25 |
| 26 | FNS_GlobalOutSelect: fastOpFind scanned the project twice and replicated a finder per shortcut | perf | **DONE** 2026-09-10 — see §26 |
| 27 | FNS_Remote: a toolbar button that takes a component by drop (Alt adds) | tool | **DONE** 2026-09-10 — see §27 |
| 28 | A host loaded mid-session never autoregisters | bug | OPEN — see §28 |
| 29 | ParentHierarchy draws a dead button beside iopBrowser's in every pane bar | bug | **DONE** 2026-09-11 — see §29 |
| 30 | IOP promotion cannot target the root; the path-bar drop was dead since the split | bug | **DONE** 2026-09-11 — see §30 |

Nothing in this document is shipped: item 1's change lives in the hot-synced
extension source, and re-exporting the PI suspect tox is a release step (see
`/fns-packaging`) that has not been run.

---

## 1. SwapOps — connector restoration is index-erased  `[BUG]` — DONE

**Symptom.** Swapping operators mangles wiring in several shapes: multi-input
destinations come back in the wrong order, fixed-input ops land on the wrong
slot, and COMPs lose wiring outright.

**Measured.** [`SwapOpsExt.swapConnectorsMult`](../modules/suspects/FNSTools/SwapOps/SwapOpsExt.py)
rebuilds wiring from `op.inputs` / `op.outputs`. Those are **index-erased OP
lists** — they say *what* is connected, never *to which connector*.
`connector.connect(someOP)` then lands on the destination's **first free slot**,
not the original one. Every one of the ~80 lines of `isMultiInputs` branching
and the "annoying edge case" middle-op dance exists to paper over that one lossy
step.

The index-preserving API exists and was verified:

    Connector attrs: connect, connections, description, disconnect,
                     inOP, index, isInput, isOutput, outOP, owner

`Connector.connections` returns the **far-side Connector objects**, each
carrying `.owner` and `.index` — the full mapping, both directions.

Two long-standing beliefs, now settled:

- **`isMultiInputs` really is inverted from its name.** Measured: `nullCHOP`,
  `overTOP`, `nullSOP`, `textDAT` and *every COMP* report `True` (fixed,
  individually-addressable connectors); `mergeCHOP`, `mathCHOP`, `switchCHOP`,
  `compositeTOP`, `switchTOP`, `mergeSOP`, `mergeDAT` report `False` (one
  growing multi-input connector, `maxInputs 9999`). The code comment guessed
  right. For non-COMPs the honest discriminator is `maxInputs == 9999`, not the
  boolean.
- **COMPs carry two connector sets SwapOps never touches** —
  `inputCOMPConnectors` / `outputCOMPConnectors`, the vertical ones. An empty
  `baseCOMP` is 0/0 horizontal but 0-in / 1-out vertical. Swapping two wired
  Geometry COMPs silently drops their vertical wiring today.

A COMP's *horizontal* connectors are also not intrinsic: they are created by the
In/Out operators inside it, indexed by those operators, and
`Connector.description` returns the In op's name. Adding an `inCHOP` then an
`inTOP` took a base COMP from 0 to 1 to 2 input connectors.

**Fix — LANDED 2026-08-31, corrected 2026-09-01. 16/16.** `swapConnectorsMult`
rewritten around a
single observation: **every edge touching op1 or op2 is some operator's
INPUT**. So the swap reduces to — capture the input wiring of op1, op2 and
every operator they feed; rebuild each from its counterpart's, with the pair
exchanged. Rebuilding the *destinations* too is what preserves a growing
multi-input's slot order, which reconnecting a single wire into a compacted
merge can never do. All four connector sets are handled. The
`isMultiInputs` branching and the "annoying edge case" middle-op dance are
gone; the discriminator is `maxInputs >= 9999` (and COMPs are always
positional, since their connectors come from the In/Out ops inside them).

**Capacity policy: surplus inputs STAY WHERE THEY ARE.** Operators of
different input capacity cannot exchange every wire — a 1-input null has
nowhere to put a merge's second source. Only the first `min(capacity)` slots
change hands; the rest keep their existing connections.

This was got wrong first. The initial rewrite *dropped* the surplus, which
cost the user a wire they never asked to remove, and the owner caught it
within the hour on `middle_op_multi`: swapping a merge fed by `(a, other)`
with the null it feeds silently disconnected `other`. Worth recording that
**the original implementation handled that case correctly** — the maligned
`middle_op` special-casing existed precisely for it — so this was a
regression introduced by the rewrite, not a pre-existing defect. The original
still failed the *non-adjacent* variant of the same shape
(`multi_surplus_apart`), which is why the hand-rolled special case was not
worth keeping; the general rule covers both.

The `dropped` list and its `ui.status` message survive as a backstop for a
shape that genuinely cannot be rebuilt. With surplus retention it should
never fire. `ui.messageBox` is not an option — it would wedge the main
thread — and the whole swap sits inside an undo block.

**Open.** Test coverage is the gating requirement, not the rewrite. Build a
`/SwapTest` COMP holding every shape as an explicit case:

- fixed 1-in (`nullCHOP`) with fixed 1-in
- fixed 2-in (`overTOP`) with fixed 2-in, including a *sparse* case where only
  input 1 is wired and input 0 is empty
- growing multi-in (`mergeCHOP`) with growing multi-in, order-sensitive
- fixed with growing, both directions (this is where today's code branches)
- adjacent ops (A feeds B directly)
- ops with an op *between* them (the `middle_op` case)
- fan-out: one source feeding several destinations at specific indices
- COMP with COMP, horizontal In/Out wiring
- COMP with COMP, vertical (`inputCOMPConnectors`) wiring
- COMP with non-COMP
- unequal connector counts (the truncation policy)
- swap of 3+ selected ops (the middle-out loop in `OnSwap`)

Each case wants a before/after connection assertion, not a visual check.

**Built 2026-08-31.** `/SwapTest/swap_harness`
([`SwapTest/swap_harness.py`](../SwapTest/swap_harness.py), 14 cases) builds a
throwaway network per case, snapshots the index-aware topology, swaps through
SwapOps' own `swapConnectorsMult`, and compares against the only correct
oracle — the before-snapshot with the two operators' names exchanged. No
hand-written per-case expectations, so the expectations cannot themselves be
wrong.

    op('/SwapTest/swap_harness').module.RunAll()

**Baseline against the current implementation: 6 pass / 8 fail.**

| Case | Result |
|---|---|
| `chain_simple`, `adjacent`, `middle_op`, `middle_op_multi`, `multi_in_order`, `three_way` | PASS |
| `fixed_two_in` | FAIL — slots scrambled |
| `sparse_fixed` | FAIL — empty slot 0 collapses the wiring |
| `fixed_to_multi` | FAIL — inputs dropped entirely |
| `multi_to_fixed` | **CRASH** — `IndexError` at `SwapOpsExt.py:115` |
| `fan_out` | FAIL — destination input indices swapped |
| `comp_horizontal` | FAIL — destination indices swapped, one input lost |
| `comp_vertical` | **CRASH** — `IndexError` at `SwapOpsExt.py:141` |
| `comp_vs_top` | FAIL — destination indices swapped |

**After the rewrite: 16/16** (16 cases — two capacity-mismatch cases were
added when the owner caught the surplus-dropping regression).

The oracle changed twice, and each change was verified against the original
implementation rather than assumed. It began as a pure name exchange, which
demanded a `nullCHOP` hold a `mergeCHOP`'s two inputs — impossible in TD. It
now models the capacity rule directly (first `min(capacity)` slots swap, the
rest stay put) and derives every `out` record from the `in` records, so a
moved or kept wire is consistent at both ends.

**Control runs are the guard against an oracle that drifts toward whatever
the code does.** Reverting to the original implementation and re-running:

| Oracle | Original impl | Rewrite |
|---|---|---|
| pure exchange (14 cases) | 6/14 | — |
| capacity clamp (14 cases) | 6/14, same failures | 14/14 |
| surplus retention (16 cases) | **7/16** | **16/16** |

The original picks up `multi_surplus_adjacent` in the last row — that is the
case its `middle_op` special-casing was built for — and still fails the
non-adjacent variant.

**Not done: shipping.** The change lives in the hot-synced, git-tracked
extension source. Re-exporting the PI suspect tox is a release step, per
`/fns-packaging`, and was not run.

Two findings the harness added that the reading pass had not predicted:

- **Two shapes crash outright** rather than mis-wiring, both `IndexError`.
- **The swap invents a connection that never existed.** Six of the eight
  failures show `b.out` gaining `(0, 'a', 0)` — a spurious wire between the two
  swapped operators. It comes from the `else` branch's
  `new_female_op.inputConnectors[0].connect(orig_female_op.outputConnectors[0])`,
  where `orig_female_op` is the *new male*, so the line wires the pair to each
  other whenever they were not already adjacent.

---

## 2. NoNode — two independent identity defects  `[BUG]`

The owner's standing note was: *"OP's `.id` doesn't change between renames, but
it does if you move it somewhere else — maybe cache the id instead of the
reference."* That is **half right, and the half that is wrong matters**: it
identifies the right key but the wrong failure mode, and it misses a second
defect in a different layer entirely.

### 2a. Dispatch — OP objects are unstable dict keys  — DONE

**Symptom.** Registered callbacks silently stop firing after network edits —
*sometimes*. See the probabilistic finding below; the intermittency is the
whole reason this was folklore rather than a filed bug.

**Measured.** `OP.__hash__` is **path-derived** — `hash(o) == hash(o.path)`,
confirmed directly. On a plain rename:

    id_stable: True          hash_stable: False
    stored_ref_still_key: False
    fresh_is_stored: True    fresh_eq_stored: True

The op is *literally the same Python object* and still compares equal to the
key — but its hash changed, so the entry is orphaned in the wrong bucket and is
unreachable. It is not deleted; `len(dict)` still reports 1.

So the breakage is **not** move-specific. `CHOPEXEC_CALLBACKS[event_type][chop]`
and its DAT/Par siblings are dicts keyed by live OPs, which means **a rename
breaks them** — and so does renaming *any ancestor*, since that changes the
path too. That is the common case the folklore was describing.

**And it is INTERMITTENT, which is the real reason this stayed folklore.**
CPython's `lookdict` compares the probed slot's key by *identity* before it
compares hashes, so a stranded entry is still reachable whenever the new
hash's probe sequence happens to land on its slot. Measured 2026-09-01 over
many trials:

| Dict shape | Still reachable after rename | Stranded |
|---|---|---|
| one entry | 9 | 51 |
| five entries | 28 | 72 |

So a renamed registration keeps working roughly a quarter of the time and
silently dies the rest. That is exactly the "works on my machine, broke
yesterday, fine again today" signature — and it means **any test of this
must repeat**, or it passes on luck about one run in four. The harness runs
twelve trials per rename case for that reason.

**A second correction.** Renaming the extension's OWN comp is *not* exposed:
measured, TD reinitialises the extension on that rename — it even re-imports
NoNode, handing back a fresh class with empty registries — and the
extension's `__init__` re-registers from scratch a frame later. It self-heals
regardless of any of this. The exposed case is an ancestor that carries **no
extension**: nothing reinitialises, and the stranded key is all that stands
between the event and the callback. An early version of the test got this
wrong and was measuring a race against a deferred reinit.

Confirmed for the move case as well: a move is destroy + create, so `.id` does
change (350308 to 350309), and moving a *parent* changes descendant ids too
(350329 to 350331).

**Fix — and why pruning is not it.** Dropping stale entries would delete the
registration; the callback stays gone, which is not a fix. Tags are the answer.
Measured:

    tags_survive_move: ['nonode:abc123']    old_id_dead_after_move:   True
    tags_survive_copy: ['nonode:def456']    orig_id_alive_after_copy: True
    discriminator_works: True

Tags survive move, copy, rename and ancestor moves. And because a **move** kills
the original id while a **copy** leaves it alive, the two are exactly
distinguishable. So:

- **Primary key: `op.id`** (int). Fast, exact, survives rename and ancestor
  rename. `op(<int id>)` resolves.
- **Recovery key: a `nonode:<token>` tag** stamped at registration.
- **On dispatch:** look up by id. On a miss, read the op's `nonode:` tag and
  find its registration, then check whether that registration's stored id is
  still alive — **dead means a move**, so rebind to the new id and dispatch
  (self-healing); **alive means a copy**, so the original is still watched and
  the duplicate is a policy decision.
- Same treatment for the `Par` keys in `PAREXEC_CALLBACKS`, which have the same
  hash instability → key on `(owner_id, par_name)`.
- `__checkAndResetOperatorColor` walks possibly-dead refs. `.valid` is the only
  safe guard: a destroyed op still returns its stale `.path` string without
  raising.

NoNode already mutates the watched op's **colour**, so a tag is comparably
intrusive — arguably less. It must be removed on deregistration.

**LANDED 2026-09-01. Harness 3/11 → 11/11**
([`NoNodeTest/nonode_harness.py`](../NoNodeTest/nonode_harness.py)), with a
control run confirming the original scores 3/11 under the same cases, and no
errors across any of the 57 ExtUtils clones.

What shipped, all inside
[`NoNode.py`](../modules/suspects/FNSTools/QuickExt/ExtUtils/NoNode.py):

- **Every data shape was kept exactly as it is.** The exec DATs' target
  parameters *are* `list(registry.keys())`, and the Par exec's `pars`
  expression calls `_par.name` on the inner keys, so re-keying by id would
  have meant editing parameters on the master ExtUtils and propagating
  through all 57 clones. Instead the **lookups** were made tolerant. One
  file, hot-synced, nothing else touched.
- `_entryFor` / `_parEntryFor` — hash lookup first, then an identity/id (or
  parameter-name) scan over the handful of watched operators. Free in the
  normal case.
- `Heal()` — rebinds a moved registration through its `nonode:` tag and
  prunes one whose operator is simply gone. The project-wide tag search is
  paid for **only when a dead key exists**; otherwise it is a cheap scan that
  writes nothing. Called at the top of every `Register*`.
- Registration reuses a stranded entry instead of adding a second key for the
  same operator. The original produced literal duplicates:
  `[('chop_renamed', 351650), ('chop_renamed', 351650)]`, which made the exec
  DAT watch one operator twice.
- `.valid` guards on the colour/marking helpers, which previously walked
  destroyed operators.

### 2f. The real cause of "it stops working when I move it" — lazy extension init

**This is the one that actually bit the owner, twice, and it is not an
identity bug at all.** It sits one layer below: after a copy/paste, the
COMP's extension is never constructed, so **nothing registers in the first
place**.

**Measured 2026-09-01, non-invasively**, on a rig the owner had cut and
pasted to the root:

    exec_target:      'None'      registry_keys:    []
    chopexec_enabled: False       EXT_OWNER_COMP:   None      errors: NONE

`NoNode.Init()` had never run. Forcing a cook fixed it instantly:

    0_initial:          None
    1_after_comp_cook:  /rig/chop_watched     <- r.cook(force=True)

TD initialises extensions **lazily** — on cook, or on access. A COMP that
nothing pulls from never cooks, so after a paste its extension stays dormant
**indefinitely**. This is not a one-frame gap. Most real tools survive it by
carrying a panel or UI that cooks; a headless component does not.

**A methodological warning, because this cost two wrong answers.** An earlier
entry here claimed the move "self-heals in one frame". It does not. That
measurement read `moved.extensions` in the probe — and *reading* `.extensions`
is itself what forces the initialisation. The probe caused the healing it then
reported. Any check of extension state must avoid `.ext` and `.extensions`;
the exec DAT's target parameter is a safe observable, since it evaluates
NoNode's registry from the DAT's own context and touches no extension.

**Fix — LANDED 2026-09-01 in the master ExtUtils.** `extAutoInit`, an Execute
DAT with **Start** and **Create** enabled, deferring a touch of the owner
COMP's `.extensions`. The TD docs are explicit that `create()` fires *"on
start, by loading a component from disk, by copying & pasting"*.

    def onStart():
        _arm()

    def onCreate():
        _arm()

    def _arm():
        comp = me.parent().parent()
        if comp is None:
            return
        run('args[0].extensions if args[0] and args[0].valid else None',
            comp, delayFrames=2)

Cloning carried it to **56 of 57** ExtUtils instances. The holdout is
`/PreviewPanel25/FNS_PaneTypeRegistry/FNS_About/ExtUtils`, which has
`enablecloning` on but an EMPTY Clone Master — so it is not a clone of
anything and receives nothing. Pre-existing, outside FNSTools, and not
introduced here.

**Verified with the owner's own gesture:** paste the rig, touch neither `.ext`
nor `.extensions`, and it comes up on its own — target
`/rig_pastetest2/chop_watched`, `chopexec_enabled: True`,
`EXT_OWNER_COMP: /rig_pastetest2`, and a real value change gives
`{'chop': 1}`. Both harnesses stayed green (NoNode 11/11, SwapOps 16/16) and
no ExtUtils reported an error.

**This lives in the `.toe`, not on disk.** `extAutoInit` follows its sibling
exec DATs, which are not externalized (only the module DATs — `NoNode`,
`CustomParHelper`, `FNSCommand` — are). **It does not survive until the
project is saved.**

Two smaller things this pass turned up, neither shipped-tool-affecting:

- Assigning a clone master by object (`eu.par.clone = master`) makes TD store
  it as a **relative** path, which breaks the moment the COMP moves
  (`Invalid path for node "../../FNSTools/..."`). The shipped tools store it
  absolutely; only the test rig was affected. Set the path as a string.
- Extension init being lazy also means **`.ext` / `.extensions` must never be
  used to inspect extension state** — reading them performs the very
  initialisation being measured.

**What a MOVE does once the extension IS initialised.** Two cases, only one of
them a NoNode problem:

- **Moving the COMP that owns the extension** re-registers from scratch: TD
  reinitialises the extension, re-imports NoNode with fresh registries, and
  `__init__` registers again. Correct at the new path — *provided the
  extension initialises at all*, which is 2f above.
- **Moving a watched operator that lives OUTSIDE the extension's COMP does
  NOT self-heal**, because nothing reinitialises. Measured: the dead key
  lingers, the operator drops out of the exec DAT's target list, and dispatch
  returns `{}`. `NoNode.Heal()` recovers it fully — dispatch `{'chop': 1}`,
  target back to the new path — but something has to call it. Registration
  does; otherwise it is manual.

Calling `Heal()` from inside dispatch would close that gap automatically, and
was rejected: it would write to a `DependDict` **during** the exec DAT's own
cook, while that DAT's target parameter is an expression reading the very dict
being written. Not worth the reentrancy risk for a narrow case with an
explicit remedy.

**The report that prompted all this was the harness, not NoNode.** The owner
cut and pasted the rig to the root and it "stopped working". It had not:
the harness hard-coded `me.parent().op('rig')` and crashed with
`AttributeError` — the same path-identity mistake it exists to catch. It now
finds the rig by tag and scores 11/11 with the rig at `/NoNodeTest/rig` and
11/11 with it at `/rig222`.

### 2d. Deregistration — DONE 2026-09-01

Deregistering a **renamed** operator did not deregister it. `del inner[op]` is
a hash lookup like any other, so it cannot reach a stranded entry: the guard
in front of it (`chop in ...`) skipped silently and left the callback live.
Worse than the leak that was predicted — measured, the CHOP path **raised
`KeyError`** outright, so a deregister after a rename could take the caller
down.

Fixed with `_withoutKey` / `_withoutParKey`: the entry is dropped by
*rebuilding* the dict, which is the only way to remove a key whose hash has
moved. Par keys are matched by name, since they strand exactly as OP keys do.

**One trap inside the fix, worth its own line.** The first attempt still
failed, in `_entryFor` — a `DependDict`'s `Mapping.items()` iterates through
its own `__getitem__`, which raises `KeyError` on precisely the stranded keys
the scan exists to find. Every registry read now normalises through `_raw()`
to the plain dict first.

### 2e. Moved foreign operator — DONE 2026-09-01, and the earlier refusal was wrong

An earlier revision of this document rejected calling `Heal()` from inside
dispatch, reasoning that it writes to a `DependDict` **during** the exec DAT's
own cook while that DAT's target parameter is an expression reading the very
dict being written. That was asserted, not tested, and it was wrong.

Measured on the real frame-driven path with a dead key present: the dispatch
completed, the moved operator was rebound automatically, the exec DAT's target
came back as `[chop_watched, /NoNodeTest/moved/foreign]`, and nothing anywhere
reported an error. `Heal()` now runs at the top of `OnChopExec`,
`OnDatExec` and `OnParExec`.

**Cost, measured**: `Heal()` is **1.6 µs** on a clean registry and **2.6 µs**
across eleven watched operators, and dispatch timings with it neutralised are
indistinguishable from timings with it active. It is also self-limiting — the
expensive project-wide tag search only runs while a dead key exists, and the
first Heal either rebinds or prunes it away.

**Residual.** An extension whose *only* registration is the moved operator
still has no trigger: nothing else fires, so nothing carries the repair.
`Heal()` remains callable by hand for that case.

### 2c. Who actually uses this — nobody, internally

**Measured.** All 12,088 DATs in the live project were scanned for
`RegisterChopExec` / `RegisterDatExec` / `RegisterParExec` /
`RegisterKeyboardShortcut` / `NoNode.Init`. Every one of the 235 hits is either
an `ExtUtils/description` DAT (documentation prose) or the `NoNode` module
itself. **No shipped FNSTools tool registers a NoNode exec or shortcut.** The
tools' hotkeys go through `FNS_HotkeyManager`; their parameter callbacks go
through `CustomParHelper`, whose exec DATs target
`CustomParHelper.EXT_OWNERCOMP` and are unaffected by this bug.

So NoNode is **user-facing API shipped through QuickExt**, not an internal
dependency of the toolkit. That does not make the bug unimportant — it is
published surface that users build extensions on — but it does mean fixing it
carries **no internal urgency and no internal regression risk**, and it
contradicts the "foundation every ExtUtils tool sits on" framing this document
was first written under.

**Scale, for whoever does the work.** 56 full ExtUtils instances exist, all 56
cloned from the master at
`/FNSTools/CustomParTools/QuickExt/ExtUtils`. The master's `NoNode` DAT is
`syncfile=True` bound to `modules/suspects/FNSTools/QuickExt/ExtUtils/NoNode.py`
— **that file is the one to edit**, not the `scripts/QuickExt/templates/` copy.
Clone-forcing is not continuous: a write to a clone's child parameter sticks
through normal operation and through a master edit, but is reverted by an
explicit clone re-assert (`comp.par.clone = master`), which is what
`extutils_distributor.rollout()` does. Anything NoNode needs applied per
instance must therefore be (re)applied at `Init`, not once.

### 2b. WITHDRAWN — "the exec DATs are never targeted"

**This section previously claimed a second, independent targeting defect. It was
wrong, and it is left here rather than deleted so the mistake is not made
again.**

The claim rested on reading `Par.val` on an exec DAT and taking it for the
expression. `Par.val` on an EXPRESSION-mode parameter is a **stale cached
display string**, not the expression. The actual `Par.expr` is:

    list(mod(me.dock.name).NoNode.CHOPEXEC_CALLBACKS.getRaw()
         .get(mod(me.dock.name).NoNode.ChopExecType.ValueChange, {}).keys())

Every one of the eleven CHOP/DAT/Par exec DATs is targeted this way — the par
*is* the registry's key list, fed straight to TD. It is reactive by
construction: `CHOPEXEC_CALLBACKS` is a `DependDict`, so registering re-cooks
the expression and the exec DAT starts watching. Nothing needs to write the
par, which is why nothing does. The design is sound.

Two things made the misreading easy, and both are worth knowing:

- **On the master ExtUtils the expression legitimately evaluates to `None`** —
  the master is not docked to any extension, so `me.dock` is None. Probing the
  master looks exactly like a broken target. Probe a *docked clone* instead.
- `__setOwnerCompToDocked` is indeed commented out in `Init`, which reads like
  a disabled targeting step. It is not; targeting never went through it.

**What this changes for 2a.** Nothing weakens — it tightens. The targeting par
is literally `dict.keys()`, so both symptoms come from the one root cause.
Python dict *iteration* still yields a hash-orphaned entry, so after a rename
`.keys()` still contains the op and the exec DAT **keeps firing** — but the
`.get(chop)` lookup inside `OnChopExec` misses. The precise symptom is
therefore **the exec fires and the callback silently does not run**, which is a
much better match for "fucky" than a dead exec would be.

---

## 3. CustomParHelper — reading pass  `[TODO]` — ANALYSED 2026-09-01

522 lines. **No code changed under this item**; this is the reading pass the
entry was waiting on, so the work can be decided rather than guessed at.

### It does not have 2a's bug

CustomParHelper keys nothing by OP or Par. Its state is four class slots
(`EXT_SELF`, `EXT_OWNERCOMP`, and the exec DATs), and its exec DATs target
`CustomParHelper.EXT_OWNERCOMP` rather than a registry key list. The
hash-instability that broke NoNode does not reach it.

### What it actually is, versus TouchUtilCollection

CustomParHelper **reflects**: it reads `ownerComp.customPars` and generates
properties and callback routing from whatever it finds.
[tdp-TouchUtilCollection](https://github.com/PlusPlusOneGmbH/tdp-TouchUtilCollection)
**declares**: `parfield` definitions (`ParFloat`, `ParMenu` with ranges,
labels, bind expressions) autocreate the custom parameters from the class, and
typed wrappers give `par.Foo` / `parGroup.Somergb[0].val`. It also has an
`autocallback` system (`on_[Name]_Value_Change`) closely equivalent to
`onPar<Name>`.

The two are not competitors so much as opposite directions through the same
seam, and the owner's instinct — take the parfield definitions, leave
`EnsureExtension` — is the right cut: the declarations are the valuable half,
the base class is the coupling. CustomParHelper's whole appeal is that it needs
no inheritance, and adopting a base class would forfeit it.

### Findings worth acting on

1. **Properties are set on the CLASS, closed over one `owner_comp`**
   (`setattr(extension_self.__class__, ...)` in `_create_propertyEval` /
   `_create_propertyPar`). Two COMPs sharing one extension DAT's module would
   silently cross-wire: the second `Init` rebinds the first's properties to the
   second COMP's parameters. **Measured safe today** — all **726** extension
   parameters in the project resolve their module locally (`op('./X').module`),
   and `.module` is per-DAT, so every COMP gets a distinct class. It is one
   convention away from breaking, and deserves an invariant: *an extension's
   module reference must be local.*

2. **`OnValueChange` discards the `comp` it is handed** —
   `comp = cls.EXT_SELF  # a bit hacky`. Routing therefore always goes to
   whichever extension called `Init` last. Fine while one COMP has one
   CustomParHelper extension; a COMP with two extensions sharing one ExtUtils
   would send the first's callbacks to the second. *How many COMPs have more
   than one extension was not measured — the probe hung TD and was not
   retried.*

3. **Callback arity is inferred from `__code__.co_argcount`** — the same
   pattern NoNode uses. It silently mis-dispatches for a method with default
   arguments, `*args`, or any real decorator (`co_argcount` would then describe
   the wrapper). `FNSCommand.fns_command` is safe here only because it returns
   the original function untouched rather than wrapping it.

4. **Properties are generated once, at `Init`.** A parameter added afterwards
   has no property until someone calls `UpdateCustomParsAsProperties()` by
   hand. This is exactly what declarative parfields would fix for free — the
   declaration is the source of truth, so the two cannot drift.

5. **`__isParGroup` is `len(_par.parGroup) > 1`**, carrying the author's own
   comment *"Is there no better way?"*. Group naming is likewise positional:
   `Parname[:-1]` assumes the group name is the member name minus its last
   character. Both hold for TD's conventions and neither is principled.

### Recommendation

Adopt parfield-style declarations as an **optional additive layer** — a class
may declare its parameters and have them created — while leaving reflection as
the default so no existing tool changes. Take no base class. Fix (1) as an
invariant and (2) by honouring the `comp` argument that is already being
passed. Items (3) and (5) are papercuts, not urgent.

---

## 4. Stuck modifier keys  `[BUG, cross-toolkit]`

**Symptom.** Alt/Cmd/Ctrl/Shift latch on after alt-tabbing in and out of TD.
Affects ParentHierarchy most visibly but is a TouchDesigner-wide behaviour, and
is far worse on macOS.

**Measured.** `ui` exposes **no** modifier state at all — the full `dir(ui)`
dump contains `rollover`, `rolloverOp`, `rolloverPar`, `rolloverParGroup`,
`rolloverPage`, `rolloverPanel`, and nothing for keys. The stickiness comes from
Keyboard In CHOP **event integration**: the app loses focus, the keyup event is
never delivered, and the channel stays at 1. That is unfixable at that layer.

ParentHierarchy's read point is
[`ParentHierarchyExt`](../modules/suspects/FNSTools/FNS_Navbar/containers/parent_hierarchy/ParentHierarchyExt.py)
`self.ownerComp.op('null_hk1')[0][0]`, fed by `constant1 → replace1 → out1 →
null_hk1`. QuickParCustom reads `null_hk['shift']`; ParOPDrop reads
`null_mod_*`.

**Options.** The owner's reaction to the first proposal was *"that seems
whacky"*, which is fair — recorded here with the alternatives rather than as a
recommendation.

1. **Read the OS directly at the moment of use.** Verified working inside TD on
   Windows: `ctypes.windll.user32.GetAsyncKeyState(0x10/0x11/0x12)`. macOS
   equivalent with no extra dependency would be `CGEventSourceFlagsState(...)`
   from ApplicationServices via `ctypes.cdll.LoadLibrary`. **Authoritative and
   immune to missed keyups**, one call per shortcut evaluation rather than per
   frame — but platform-forked, and the Mac leg is unverified and untestable
   from Windows. This is the "whacky" one.
2. **Timeout decay.** If a modifier reads held for longer than N seconds with no
   other keyboard activity, clear it. Zero dependencies, cross-platform, crude,
   and it cannot distinguish a genuinely-held key from a stuck one.
3. **Reconcile on the next real event.** Cheap, but it does not clear the stuck
   window — it only ends it once the user presses something.
4. **Check whether TD 2025 exposes anything newer** (Keyboard In CHOP reset
   behaviour, a panel-level modifier value). Not yet investigated; should be
   done before committing to any of the above.

**Open.** Pick an approach. Whichever wins should land as **one shared helper**
used by all three tools, not three copies.

---

## 5. QuickMarks — names, and a broken command path  `[FEATURE + BUG]`

**Feature — LANDED 2026-09-01.** Quickmarks now live on a custom parameter
sequence, which is what makes a *name* possible at all: storage neither roams
nor is visible in the UI, so there was nowhere for a user-editable label to
live. Sequence pars travel with the `.toe`, roam through the ConfigRegistry
`pars` rail, and each block's Name is free text.

Shape: sequence `Mark`, `blockSize 2`, ten blocks — `MarkNname` (the label) and
`MarkNdata` (the location as JSON). Block N is the slot ctrl+N reaches, so the
first ten line up with the hotkeys; the sequence can grow past that and the
extra blocks are reachable by command. Storing an unnamed slot auto-labels it
with the network's own name, and never overwrites a label the user has set.

**The TD API here is a three-step idiom that is easy to get wrong**, and worth
recording since nothing else in this repo uses `appendSequence`:

    page.appendSequence('Mark')     # creates the COUNT par, not the block
    page.appendStr('Name')          # appended to the PAGE, not the sequence
    page.appendStr('Data')
    comp.seq.Mark.blockSize = 2     # absorbs the two ParGroups into the block

Without the `blockSize` line the sequence reports `numBlocks 0` and
`blockPars []` and the appended parameters just sit on the page as ordinary
pars — which is exactly what the first attempt produced. TD names the results
`Mark0name`, `Mark0data`, and so on.

**Migration ran and was verified against the owner's live data.** All three
stored marks moved across with their networks intact, the legacy
`StorageManager` is left untouched as a backup that nothing reads, and a
read-only `Migrated` par guards against a second run. Store, auto-name,
rename, hotkey-convention lookup and clear were all exercised on an empty
slot rather than on the owner's marks.

Two new commands come with it: `NameMark(slot, name)` and `ListMarks()`.

**Known weak spot:** the auto-name is the network's own name, which for the
owner's three deeply nested `base1` COMPs produced three identical labels.
Honest, but not useful there — renaming is the point, and now possible.

**Bug — CONFIRMED and FIXED 2026-09-01.** The hotkey path and the command path
disagreed about the storage key. `HandleShortcut` builds
`f"Quickmark{key_number}"`; the registered commands `StoreMark` / `GoToMark` /
`ClearMark` passed a bare `int(slot)`. Proven read-only against the owner's
live marks — `stored.get(3)` misses while `stored.get('Quickmark3')` returns
`/project1/base7/base1/base1/base1` — so all three quick-launch commands were
blind to every mark stored by hotkey. `StoreMark` was the worse half: it wrote
an **undeclared** key straight into the `StorageManager` rather than the
declared slot.

Fixed with a `_slotKey` normaliser accepting `3`, `'3'` or `'Quickmark3'`,
applied in `StoreQuickmark`, `RetrieveQuickmark` and `UnstoreQuickmark`, so
both calling conventions address the same entry. The owner's three stored
marks were verified untouched.

**The naming feature itself is still open** — the sequence-par rework above.

**Also noted.** `HandleShortcut` calls `RetrieveQuickmark` **twice** with the
comment *"need to call twice to get the correct position"* — an unexplained
workaround that a rework should either justify or remove.

---

## 6. FNS_Commands — declare a command's authority  `[FEATURE]`

**Goal.** Let a command declare **what it acts on**, so a palette can
contextualise: gray out or hide commands whose subject is absent, and
pre-resolve the subject before invoking.

**Measured.** [`FNSCommand.py`](../FNSTools/CustomParTools/QuickExt/ExtUtils/FNSCommand.py)
already carries `surface` (registry 1.7.0), but that names **where a command is
shown** — an orthogonal axis. Nothing today describes the subject.

**LANDED 2026-09-01 (registry 1.8.0).** A `context` field on `fns_command`,
plus a resolver. The owner confirmed new command consumers are coming, which
is what makes the field worth declaring ahead of them.

    'network'       the current pane's owner COMP
    'selected'      the operator(s) selected in that pane
    'current'       the single current operator
    'rollover-op'   the operator under the cursor
    'rollover-par'  the parameter under the cursor

A token or a **list** of tokens — `context=['selected', 'current']` for a
command happy with either.

**The vocabulary matches Envoy's `get_focus` on purpose**, so the two systems
answer "what is the user looking at?" with the same words instead of inventing
a second dialect.

**`resolve_context(context)` ships with it**, returning `(token, subject)` for
the first token that resolves and `(None, None)` otherwise. It touches only
`td` — no registry, nothing FNS-specific — so a consumer can call it knowing
nothing about the toolkit, and a vendored copy keeps working, which is this
module's whole contract. `rollover-par` returns the ParGroup only when
genuinely multi-component, the same "decide from what is hovered" rule item 9
settled.

**A consumer should grey out a command whose context does not resolve, not
hide it** — the user can still see the command exists and learn what it wants,
which a missing entry cannot teach.

Verified: the bare `@fns_command` decorator still works and reports
`context: None`; single-token and list forms round-trip; the resolver returns
the live pane owner for `network`, `(None, None)` for an absent subject or an
unknown token without raising, and falls through a list to the first that
resolves.

**Annotation is deliberately incremental.** Only `SwapOps.SwapSelected`
(`selected`) and `QuickMarks.StoreMark` (`network`) carry it so far, as proof
of shape. Annotating the remaining ~79 commands is a follow-up best done as
each tool is touched — a project-wide sweep would mean re-saving every suspect
for metadata that costs nothing to add later.

### 6b. The registry came in-house — adopted 2026-09-01

The owner brought `FNS_CommandRegistry` over from TDXLPP. Until then this
repo shipped only the **authoring** half (the `FNSCommand` decorator,
`announce()`, the `fnscommands` tag) and the harvester lived in the launcher's
companion tox — which is why `announce()` is written to no-op with no registry
present, and why 42 carriers sat tagged and dormant.

Adoption, with the hazards `/fns-registry` warns about:

- It arrived **carrying its TDXLPP file bindings** (`TDXLauncherUtility/...`),
  paths that do not exist here. Severed BEFORE anything could write through —
  an edit would otherwise have created a foreign directory tree in this repo.
  Its inherited `externaltox` (enabled, empty path) and a stray
  `enablecloning` with no master were cleared the same way.
- It is **PI-owned**, not Embody-owned. The first attempt externalized it onto
  Embody's rail; that was wrong and was undone — `modules/suspects/` is the
  canonical tree and PI is the registry of record. See
  [ExternalizationOwnership.md](ExternalizationOwnership.md).
- PI wrote a **mixed path separator** (`modules\suspects/FNSTools/...`) where
  every other tool has forward slashes, and dropped `vc_data` on top of
  `parexec_registry`. Both corrected.
- The **`/sys` global runs a copy with no file sync**, so editing the ext
  reaches the master only; `Repromote()` then `RescanTools()` is what makes an
  edit real.

Now at `/sys/FNS_Registries/FNS_CommandRegistry`, the eleventh global,
serving 99 commands from 43 tools.

**The 1.8.0 fork, and why it is safe.** Teaching the harvester `context` forks
the implementation from TDXLPP's. The owner's condition was that existing
commands keep working, so that was measured rather than assumed: a full
`Commands()` baseline was captured before the change and diffed after.

    count 99 -> 99, keys lost [], keys gained []
    changed: 2, both purely additive
      /FNSTools/QuickMarks#storemark  + context: ['network']
      /FNSTools/SwapOps#swapselected  + context: ['selected']

97 commands byte-identical. `context` follows `surface` exactly — same three
integration sites, shape-only validation, `CONTEXT_TOKENS` as blessed
vocabulary rather than a whitelist — so a 1.7.0 registry ignores the key in
`_fns_command` and a 1.7.0 consumer ignores it on the wire.

**Caveat worth remembering:** both registries promote into the same
`/sys/FNS_Registries` and **newest wins, never prompting**. At 1.8.0 against
TDXLPP's 1.7.0 ours takes the global whenever the launcher is also injected.
That is fine while we are ahead, but the version number is now a namespace
shared across two repos, and whoever bumps last silently wins.

### 6c. OPEN: the kit / registry split

Two components now cover one system and nothing says where the line is.

- **`FNS_CommandKit`** is author-facing: it ships `FNSCommand`, the announcer
  and `example_ext` — what a tool imports to *declare* commands.
- **`FNS_CommandRegistry`** is consumer-facing: it harvests, validates and
  serves them. The owner's framing is that **the registry belongs to
  consumers**, and the plan is to rebuild the palette (today an external
  application in TDXLPP) inside TD.

Arguments for keeping them apart: a tool needs the kit and *no* registry —
precisely why `announce()` no-ops — so folding them would make every tool
depend on a consumer-side component.

Arguments for merging, or at least tightening: the kit's `README` still points
at TDXLPP, and it carries its own `FNSCommand` DAT file-synced to the ExtUtils
master, making it a **third** copy of one contract (master, ExtUtils clones,
kit). Three copies of a contract is how contracts drift.

**RESOLVED 2026-09-01: keep them apart.** The merge argument rested on the kit
being a third drifting copy of `FNSCommand`. Measured, it is not: the kit's
`FNSCommand` is file-bound to the same canonical
`modules/suspects/FNSTools/CustomParTools/QuickExt/ExtUtils/FNSCommand.py`,
`syncfile=True`, and current. There are not three contracts — there is **one
file with 170 mirrors**, all of them bound and synced as of this date. With the
drift premise gone, the keep-apart argument stands unopposed: a tool needs the
kit and *no* registry (which is why `announce()` no-ops), so folding them would
make all 45 registering tools depend on a consumer-side component.

The dependency shape already reflects the split and confirms it — **224 DATs
reference the registry shortcut; 3 reference the kit, all of them inside the kit
itself.** The palette therefore depends on `FNS_CommandRegistry`, and tools
depend on `FNS_CommandKit`, with no component depending on both.

Two follow-ups came out of it, both done:

- **`FNS_CommandRegistry` had no version at all** — no `FNS_About`, no bare
  `Pkgversion` — which by `/fns-packaging` made it not-a-package, and left item
  10's arbitration with no value to read. It now carries a bare `Pkgversion`
  (`0.1.0`, the `/fns-registry` checklist's starting value for a registry that
  has never shipped), on an `About` page, editable because here the par IS the
  source of truth rather than a mirror of an `FNS_About` child. Note it is a
  different axis from `REGISTRY_VERSION` (`1.8.0`), which versions the
  harvest/serve protocol, not the package. Added to the `/sys` global too so the
  live session matches; a cold boot regenerates that copy from the master anyway.
- **The kit's README** described only the TDXL launcher and never mentioned
  `FNS_CommandRegistry`. Rewritten to say the registry harvests and serves
  whatever consumers are present (launcher today, in-TD palette next), to
  document `context` / `surface` / `state` / `capability` — all four postdate the
  original text — and to point at `docs/CommandRegistration.md` for the
  FunctionStore side while keeping the TDXLPP pointer for the consumer WIRE
  contract, which genuinely does live there.

**Resolved 2026-09-01/02** -- `FNS_CommandRegistry` now has both a `catalog.json`
entry (Core) and a `packaging/docs/` page, and ships TD's built-in commands
(`CommandRegistration.md`, 2026-09-02). The paragraph below is the state it
resolved from.

**Was open, and deliberately so:** `FNS_CommandRegistry` is the only one of the
eleven registries with no `catalog.json` entry and no `packaging/docs/` page. All
ten surface registries have both. Adding them would offer it to users through the
configurator and the site, which is a shipping decision rather than cleanup — the
site build does not fail on a package that has neither, only on a mismatched
pair, so the current state is safe. Owner's call.
This is groundwork for the eventual TD-internal command palette that replaces
the launcher dependency.

---

## 7. ParOPDrop — CHOP/DAT drop creates an Execute DAT  `[FEATURE]`

[Issue #127](https://github.com/function-store/FunctionStore_tools/issues/127):
*"Would be cool if its possible to also drop a chop(Channel)/dat on the drop
Icon that then creates a execute dat with maybe the Channel inside or `*`?"*

**Measured.** [`ExtParOPPlace`](../modules/suspects/FNSTools/ParOPDrop/ExtParOPPlace.py)
already has the three-mode switch this needs (`parameterCHOP` / `parameterDAT` /
`parameterexecuteDAT`, driven by pre-enabled flags). But the whole tool is
**parameter-oriented**: `OnPlaceParOp` takes its subject from `ui.rolloverPar`
and bails unless `owner.family == "COMP"`.

The issue asks for the **inverse direction** — a dropped *operator* as the
subject rather than a hovered *par*. That is a new entry point alongside the
existing one, not a tweak to it. Wants CHOP Execute DAT / DAT Execute DAT with
the channel prefilled (or `*`).

### Done 2026-09-01

**The open question dissolved rather than being decided.** It had been carried
as "channel inside or `*`, which default?" — but a drop payload NAMES its type,
so there is nothing to default: a dropped `Channel` knows which channel it is,
and a dropped CHOP names none, which means all of them. The owner pointed this
out with a live payload —
`{'dragItems': [type:Channel name:chan1 owner:/base5/lfo1 ...]}` — and a working
reference in `/base5`.

**And the "legacy callback system" suspicion was wrong, in a useful way.** The
drop icon (`button_ParOpPlace`) already runs TD's *modern* panel callbacks
(`drop = usecallbacks`, `onHoverStartGetAccept` / `onDropGetResults`), the same
API as the `/base5` example, and its `onDropGetResults` already discriminated
`Par` / `ParGroup` / `ParGroupUnit`. So this extended an existing branch instead
of porting anything. What IS parameter-oriented and modifier-driven is
`OnPlaceParOp` itself, which reads `ui.rolloverPar` — that is not drag-and-drop
at all, which is the thing that made the tool look legacy from outside.

`OnDropOperator` + `_createExec` are the new operator-oriented entry point,
beside the parameter-oriented one:

| Dropped | Created | Target | Channel |
|---|---|---|---|
| `Channel` | CHOP Execute DAT | its `owner` | the channel's name |
| CHOP | CHOP Execute DAT | the CHOP | `*` |
| DAT | DAT Execute DAT | the DAT | — |

Two details that are easy to get wrong and were measured, not assumed: the par
names are **singular** (`chop`, `channel`, `dat`) — `chops`/`chans` belong to
NoNode's exec DATs — and an Execute DAT ships with **every event toggle off**,
so one is turned on (Value Change / Table Change) or the drop creates a DAT that
can never fire and reads as having silently done nothing.

No modifier is required, deliberately: modifiers on a *par* drop select among
three outcomes, while an operator drop has exactly one.

**Verified** by calling `onDropGetResults` directly with a synthetic `info`, the
same technique the NoNode harness uses — all three cases produced the right DAT,
correctly targeted and armed. The op reference goes through
`TDF.getShortcutPath` as the existing code does, which yields a bare sibling
name (`op('zz_src')`) in the realistic same-network case; it only degrades to an
absolute path when source and target sit in unrelated branches, which is
pre-existing behaviour of that helper rather than something introduced here.

---

## 8. Registry group structure does not roam between projects  `[BUG]` — WITHDRAWN

**Symptom.** Group definitions and the order of injected UI elements should
persist across projects when the toolkit is set to roam, and do not.

**Measured.** Two different stores, and only one of them roams:

- **Per-tool order and display** ride the tool's own `Registry` page bind
  masters. [`ScopeAndPersistence.md`](ScopeAndPersistence.md) records that this
  page is persisted *on purpose* — "those pars are the bind masters holding
  surface order and display". These **do** roam via the ConfigRegistry `pars`
  rail.
- **Group structure** — which groups exist, their ids, and their bracket
  positions — lives as virtual `GroupStart_G*` / `GroupEnd_G*` sequence entries
  **on the registry COMP itself** (`_RegistryGroupsMixin`,
  [`RegistryBase.py`](../scripts/shared/RegistryBase.py) around line 1476). And
  every registry is in that same document's list of **twelve tools with no
  config host at all**: `FNS_ToolbarRegistry`, `FNS_NavbarRegistry`,
  `FNS_MainMenuRegistry`, `FNS_OpMenuRegistry`, `FNS_PaneTypeRegistry`,
  `FNS_TimelineRegistry`, `FNS_PaletteRegistry`, `FNS_HubRegistry`, and the
  rest. So group structure has no roaming rail whatsoever.

### WITHDRAWN 2026-09-01 — group structure already roams

**The conclusion above is wrong, and no work should be done against it.** The
owner had chosen "move the brackets onto a roaming rail"; building that would
have added a SECOND, competing persistence path for state that already has
one.

The reasoning error is worth naming, because it is the same shape as §2b: a
list in another document was read as settling a question it does not answer.
It is true that the registries have no config host and that their own storage
does not roam. What does not follow is that the group structure has no rail —
that only holds if nothing *else* persists it. Something does.

**`FNS_Hub` owns the rail, and its `config_callbacks` says so in as many
words**: *"Persists every configurator tab's `state` table — dividers,
**hideable-group brackets**, adopted built-ins' order/display/width … without
them a bar layout dies with the component and never follows the user to another
project."* The hub has a config host, and each configurator implements
`SnapshotState()` / `RestoreState()`.

Measured live, then confirmed on disk rather than in memory:

    SnapshotState kinds: ['builtin', 'group', 'groupend', 'groupstart']
      ToolbarConfigurator  18 rows
      NavbarConfigurator   13 rows

    C:/Users/Dan/Documents/Derivative/Palette/FNStools_ext/config/FNStools_config.json
      FNS_Hub.state.configurators
        ToolbarConfigurator  18 rows, group rows present
        NavbarConfigurator   13 rows, group rows present

So the brackets are in the machine-global roaming file today. The registry's
own storage is the live working copy; the configurator's snapshot is the
durable, roaming record, and `RestoreState` re-applies it.

**What stays open.** The owner raised this as "*need to check where the group
definitions are saved … they should retain between projects*" — a question,
not a bug report. The mechanism is verified present and correct. If group
structure has actually been observed failing to survive a new project, that is
a **different** defect — restore not firing, scope set to project rather than
global, or a configurator absent — and it needs a repro before anything is
built.

---

## 9. `rolloverParGroup` support in QuickParCustom and ParOPDrop  `[FEATURE]`

**Measured.** `ui.rolloverParGroup` **exists** in 2025.33070 and returns a real
ParGroup. Probed live while hovering a par, both were populated:

    ui.rolloverPar:      type:Par      name:parentshortcut  value:FNS_MediaBrowser
    ui.rolloverParGroup: type:ParGroup name:parentshortcut  value:(FNS_MediaBrowser)

**State of play.** `ParRandomizer` already guards for it. **QuickParCustom**
(its `rolloverPar` property) and **ParOPDrop**
([`ExtParOPPlace.py`](../modules/suspects/FNSTools/ParOPDrop/ExtParOPPlace.py),
around line 60) do not.

**Caveat — do not copy ParRandomizer's guard blindly.** It reads
`ui.rolloverPar if not hasattr(ui, 'rolloverParGroup') else ui.rolloverParGroup`,
which *always* prefers the ParGroup when the attribute exists. That changes the
object type handed to downstream code expecting a `Par`.

**Decision (owner, 2026-09-01): decide from what is hovered, not by a fixed
preference.** TD exposes both attributes, so a genuinely multi-component group
under the cursor means the group and a single-value parameter means that
parameter. No modifier key, which also keeps this independent of item 4.

**The hazard that shaped the implementation.** `ParGroup.mode` returns a
**TUPLE** of modes — measured `(<ParMode.CONSTANT>, <ParMode.CONSTANT>, ...)`,
and `.expr` / `.bindExpr` likewise return tuples. So handing a ParGroup to
QuickParCustom's `_par.mode in [ParMode.BIND, ParMode.EXPRESSION]` checks would
compare a tuple against an enum, silently take the wrong branch and promote the
wrong thing. ParRandomizer gets away with its blanket preference only because
it uses `.val` and `.reset()`, which a ParGroup does support.

**LANDED 2026-09-01, with one half unverified:**

- **ParOPDrop — verified.** `_rolloverTarget()` picks group or single from what
  is hovered, and `_parNames()` expands a group to its MEMBER names
  (`Tintr Tintg Tintb`), because the Parameter CHOP/DAT's `parameters` par is a
  name list and the group name alone matches nothing. Re-drop now merges only
  the names not already present. Tested directly: group → `['Tintr','Tintg','Tintb']`,
  single → `['Solo']`, and a one-member group correctly treated as single.
- **QuickParCustom — implemented, hover path NOT verified.** `_rolloverMembers()`
  returns the group's members as **Pars, never the ParGroup**, so every
  `ParMode` check downstream stays valid, and promote loops over them inside a
  single undo block. The guard refuses to widen when the live
  `ui.rolloverParGroup` does not match the parameter in hand — verified, since
  that is the case that would otherwise promote a whole group by accident.
  What could not be tested here is the actual mouse-hover path, which needs a
  human at the keyboard: **hover a component of a vector or colour par and
  press the promote shortcut, and confirm all members are promoted in one undo
  step.**

`ParRandomizer` was deliberately left alone — its blanket preference is not
broken for what it does, and changing it was not asked for.

---

## Suggested order

**Revised 2026-09-02.** Every numbered item is done (see the table); the
order below is kept as the record of how the pass was sequenced. What remains
is not in the numbering: the hand tests only the owner can run (item 9's
QuickParCustom hover, item 4 on macOS, the palette's click-outside dismiss),
the release rail for the two
packages that exist only in the dev tree (FNS_CommandPalette, the built-ins
inside FNS_CommandRegistry), and the ExtUtils fleet rollout the distributor
survey kept reporting (58 slim copies without FNSCommand, PreviewPanel25's
unlinked full copy) -- run 2026-09-02, see §19.

**Revised 2026-08-31 after §2c.** The first draft of this list put NoNode first,
on the reasoning that it was "the foundation every ExtUtils tool sits on". The
usage scan disproved that: no shipped tool calls it. The order below reflects
the measurements, not the first impression.

1. **SwapOps (item 1)** — live, shipped code the owner hits directly. The
   connector API is proven and the rewrite should *shrink* the code. Gated on
   the `/SwapTest` harness, which is the real work and is worth building
   regardless of when the rewrite happens.
2. **NoNode (item 2)** — genuinely broken and genuinely published (QuickExt
   users build on it), but with no internal caller there is no internal urgency
   and no internal regression risk. The fix is now well understood and confined
   to one file: dispatch keys plus tag recovery. §2b is withdrawn; there is no
   second layer.
3. **Modifier keys (item 4)** — small and shared once an approach is chosen, but
   blocked on a decision and on a macOS verification the Windows box cannot
   provide.

Items 5–9 are independent and can be taken in any order. Item 5's command-path
bug is small, live and user-visible, so it is a reasonable thing to pick up
alongside anything else. Item 3 needs a reading pass before it can be ordered
at all.

---

## 10. Version registered commands, and dedupe by package  `[FEATURE]` — OPEN

Owner's idea, 2026-09-01: a registered command should carry a version, taken
from its registrator's `Pkgversion`, so that when two registrators offer the
same command the newest package wins.

**Measured first, because it changes the shape of the work.** A command's
identity today is `path#id`:

    /FNSTools/AltSelect#toggleactive
    /FNSTools/AutoCombine#toggleactive
    /FNSTools/AutoRes#toggleactive

`toggleactive` appears **12 times** across the 99 live commands and nothing
collides, because the owner path namespaces it. Labels are already distinct
too ("Toggle AltSelect", "Toggle AutoCombine") — zero duplicate labels in the
whole set. So **there is no collision to resolve today**, and the version field
alone would resolve nothing.

The real proposal underneath is therefore: **introduce a name-level identity
above the path**, and use package version to arbitrate it. The version is the
easy half; the identity is the design.

### What has to be decided

- **What counts as "the same command"?** `id` alone is far too broad — it
  would collapse all twelve `toggleactive`s into one. Candidates: an explicit
  declared canonical id (`fns.swapops.swap-selected`), or `capability` +
  `id`, which already exists as a blessed-namespace field and is the closest
  thing to a cross-package name.
- **Which real situations produce a genuine duplicate?** A stale copy of a
  tool left in a project; a tool present both in `/FNSTools` and in a user's
  own copy; two packages both implementing one blessed capability. **Measured
  2026-09-01: none of them occurs here yet.** No tool registers from more than
  one path, and the only registrant outside `/FNSTools` is `/PreviewPanel25`,
  which is a genuinely separate component rather than a duplicate. So this
  arbitration currently has no case to resolve — build it when a real
  duplicate appears, or deliberately as groundwork for third-party packages,
  but not on the belief that something is broken today.
- **Winner replaces, or specs merge?** The owner's example — one registrant
  declaring one `surface`, another declaring two — reads as *replace
  wholesale*, the newest package's spec winning entire. Merging would be the
  other option and is strictly more surprising. Replace is probably right, but
  it should be a stated choice.
- **What happens to the loser?** Dropped silently, or listed as shadowed so a
  consumer can explain why a command vanished. Silent loss of a command is the
  kind of thing that is very hard to debug from the palette.
- **Tools with no `Pkgversion`.** Reachable and populated on real tools
  (`SwapOps`, `QuickMarks` both `3.0.1`), read off the tool COMP or its
  `FNS_About`. But **the just-adopted `FNS_CommandRegistry` has none at all** —
  no `FNS_About`, no bare `Pkgversion` par — so an arbitration keyed on it
  needs a defined answer for absent (treat as lowest? refuse to arbitrate?).
  **Closed 2026-09-01** (see 6c): the registry now carries a bare `Pkgversion`
  of `0.1.0`. The design question it raised is still live, though — arbitration
  must still define what an ABSENT version means for a third-party registrator
  that ships without one.

### Precedent to reuse

The registry family already arbitrates exactly this way one level up: **newest
wins, ties keep the incumbent, and it NEVER prompts** — that is how a shipped
registry replaces an older promoted global (`/fns-registry`). Reusing that
comparator, including the tie rule and the no-prompt rule, keeps commands
consistent with the globals rather than inventing a second policy. Note it
compares whole versions, and normalizes `1.0` to `1.0.0` so the two are equal
rather than the shorter sorting lower.

---

## 11. Sweep the command set for the fields we just built  `[FEATURE]` — OPEN

Now that `context` exists alongside `surface`, `capability` and `state`, the
99 live commands should be swept and annotated deliberately rather than
opportunistically. Measured adoption, 2026-09-01, across 43 registering tools:

| Field | Declared | Of 99 |
|---|---|---|
| `help` | 94 | 5 commands ship with no subtitle at all |
| `hidden` | 28 | |
| `capability` | 19 | `fns.media-browser` 8, `fns.autosave` 4, `fns.mobile-control` 4, `fns.collect` 3 |
| `state` | 18 | toggles/setters that chip their live value |
| `params` | 7 | |
| `surface` | 4 | and those same 4 declare both `session` and `context-menu` |
| **`context`** | **2** | the two annotated as proof of shape |

Re-measured 2026-09-01 after every `FNSCommand` copy was put on the file rail
(103 commands, 45 owners): `help` 98, `hidden` 29, `capability` 19, `state` 18,
`params` 7, `surface` 4, `context` 2. Eight copies had been frozen before
`resolve_context` existed and would have ignored the field entirely — fixed in
`566fce9`, so the sweep now has a set that can actually carry the annotation.

### What the sweep is actually for

- **`context` on the other 97.** The mechanical bulk, but not mindless: the
  right token is a judgement per command, and a wrong one is worse than none
  (a consumer would grey out a command that actually works). `ToggleActive`
  on a tool needs nothing; `SwapSelected` needs `selected`; the ParOPDrop and
  QuickParCustom commands want `rollover-par`.
- **`surface` is at 4 of 99, and that is worth questioning rather than
  fixing.** Absent means quick-launch only, which is a sane default — so the
  question is not "why so few" but "which commands genuinely belong on the
  session bar or a context menu". Answering that is a product call, and it is
  the sort of thing the in-TD palette will make obvious once it exists.
- **`capability` groups exist but are thin.** Four blessed ids covering 19
  commands. If a consumer is going to render capability groups natively, the
  sweep should confirm each group is complete — a half-declared capability
  renders worse than none.
- **Identities.** `toggleactive` appears 12 times. The sweep is where a
  name-level identity would be assigned if item 10 is built, so the two want
  doing together rather than twice over the same 99 commands.
- **The 5 commands with no `help`.** Harvest derives help from the docstring's
  first line, so these are methods with no docstring. Cheapest possible win
  and it improves every consumer at once.

### Do it after the palette, not before

The strong argument for waiting: the in-TD palette is the first consumer that
will actually *use* `context` and `surface`, and building it will show which
annotations matter and which are ceremony. Annotating 97 commands first risks
doing it twice. The counter-argument is that the palette is easier to build
against a fully annotated set — so at minimum, annotate as each tool is
touched for other reasons, which is the policy already in force.

**Cost note:** `FNSCommand` lives in the master ExtUtils, but the annotations
live in each tool's own extension, so a full sweep means editing and re-saving
~43 suspects. That is the same 43-suspect sweep this session ran several
times; batching it once is much cheaper than trickling it.

---

## Operational notes from this pass

**Do not walk the whole project on the main thread.** A single probe doing
`op('/').findChildren(type=textDAT, maxDepth=6)` and reading `.text` on each
(~12,000 DATs) wedged TouchDesigner. Diagnosed rather than assumed: the process
reported **byte-identical CPU across six seconds** with `Responding: False`,
and both Envoy ports timed out rather than refusing — zero CPU means blocked,
not busy, so it was not still grinding through the query. Scope such sweeps to
a subtree, or read the project-wide `.tdn` snapshot from disk instead.

**Confirmed reproducible 2026-09-01, and it cost a second wedge.** Item 3
recorded that the multi-extension probe "hung TD and was not retried". It was
retried -- walking every COMP and then reading `.text` on the extension DATs of
the ones with more than one -- and TD deadlocked again with the identical
signature: **CPU flat at 10,346.56 s across a six-second sample, `Responding:
False`, and no modal dialog on the process** (checked via EnumWindows, since a
modal is the other thing that blocks the main thread at zero CPU). It does not
self-heal: the Envoy liveness watchdog cannot help when the block is *in* the
main thread it would have to run on.

**That explanation was WRONG, and a second wedge disproved it within the hour.**
A follow-up probe reading `.text` on exactly SIX explicit paths -- no
`findChildren`, no walk -- deadlocked TD with the same zero-CPU signature. Six
reads are not a volume problem, so "reading `.text` is expensive" cannot be the
cause. It is left here rather than deleted because acting on it is what produced
the second hang.

**The likelier common factor, not yet confirmed:** both probes read
`/FNSTools/logger/LoggerExt` and `/FNSTools/logger/CallbacksExt`. `fnsLog()`
routes through `op.FNS.op('logger')` and Envoy logs every call, so reading the
logger's own extension DATs from inside a logged call is a plausible re-entrant
block. **Unconfirmed on purpose** -- confirming it means deliberately wedging TD
a third time, which is not worth the answer. Treat the logger's extension DATs
as untouchable from a probe until someone has a safe way to test it.

The surviving practical rule: The parameter-only form of the same question --
`c.par['extension1'..'extension6']` across every COMP -- completed fine and
answered most of it (652 COMPs carry extensions, 21 carry more than one). Only
the follow-up that opened DAT text hung. Ask these questions from parameters,
from tags, or from the on-disk `.tdn`. **Best of all, ask them from disk**: the
question that started this -- which extensions call `CustomParHelper.Init` --
was finally answered with `grep` over `modules/suspects/`, with TD not involved
at all. Now that every extension source is externalized (item 13), that is the
default way to ask a question about code.

Two related traps, both hit the same session:

- A benchmark loop sized for a microsecond operation (`N=3000`) against one
  that turned out to take ~10 ms exceeded the 30 s MCP timeout twice; the
  orphaned calls kept running on the main thread and backed TD up behind them.
  Size loops from a measured single call, not an assumed one.
- **`.ext` / `.extensions` must never be used to inspect extension state** —
  reading them *performs* the initialisation being measured. See §2f, where
  this produced two wrong answers in a row.

**Reading state can change it, and reading `Par.val` is not reading the
expression.** Both of this session's withdrawn findings (§2b, §2f) came from a
probe that mutated or misread what it measured. When a conclusion rests on a
probe, prefer an observable the probe cannot influence — for extension state,
the exec DAT's target parameter; for parameters, `Par.expr`.

---

## Appendix — measurements

All run 2026-08-31 against the live session, TD **2025.33070**, via Envoy
`execute_python`. Probe COMPs were created and destroyed in the same call.

**Connector families** (`isMultiInputs` / `maxInputs` / connector counts)

| Op | isMultiInputs | maxInputs | in | out | inCOMP | outCOMP |
|---|---|---|---|---|---|---|
| `nullCHOP` | True | 1 | 1 | 1 | — | — |
| `overTOP` | True | 2 | 2 | 1 | — | — |
| `textDAT` | True | 1 | 1 | 1 | — | — |
| `mergeCHOP` | False | 9999 | 1 | 1 | — | — |
| `compositeTOP` | False | 9999 | 1 | 1 | — | — |
| `switchTOP` | False | 9999 | 1 | 1 | — | — |
| `mergeSOP` | False | 9999 | 1 | 1 | — | — |
| `baseCOMP` | True | 0 | 0 | 0 | 0 | 1 |
| `containerCOMP` | True | 0 | 0 | 0 | 1 | 1 |
| `geometryCOMP` | True | 0 | 0 | 0 | 1 | 1 |
| `windowCOMP` | True | 0 | 0 | 0 | 0 | 1 |

`maxInputs` stays 0 for COMPs even when they have horizontal connectors, so it
is **not** a valid discriminator for the COMP family.

**COMP connectors are created by inner In/Out ops**

    empty base : in 0  out 0  inCOMP 0  outCOMP 1
    + inCHOP   : in 1  out 0
    + inTOP    : in 2  out 0
    + outCHOP  : in 2  out 1
    inConn  -> [(0, 'in1', True), (1, 'in2', True)]
    outConn -> [(0, 'out1', False)]

**Connector API**

    attrs: connect, connections, description, disconnect,
           inOP, index, isInput, isOutput, outOP, owner
    a.outputConnectors[0].connections -> [('b', 0, True)]   # far-side connector
    mergeCHOP after 2 connects: len(inputConnectors) == 3    # grows by one spare

**OP identity across edits**

    rename: id 350308 -> 350308   hash CHANGED   stored_ref_still_key False
                                                 fresh_is_stored     True
    move  : id 350308 -> 350309   old id dead    tags survive
    copy  : id 350327 -> 350328   old id ALIVE   tags survive
    ancestor move: child id 350329 -> 350331
    op(<int id>) resolves; a destroyed op returns a stale .path without raising,
    so .valid is the only safe liveness check. tags is a DependSet.

**NoNode exec DAT targeting — registry-driven, and a trap**

    Par.val  -> 'constant1 constant2'          # STALE CACHED DISPLAY STRING
    Par.expr -> list(mod(me.dock.name).NoNode.CHOPEXEC_CALLBACKS.getRaw()
                     .get(...ChopExecType.ValueChange, {}).keys())

Read `Par.expr`, never `Par.val`, on an EXPRESSION-mode parameter. Reading
`.val` here produced a wrong finding (withdrawn 2b) and, when "restored" as an
expression, a live `SyntaxError` on `/FNSTools/MISC/ExtUtils/extChopValueChangeExec`.
Also: on the **master** ExtUtils these expressions evaluate to `None` because
the master is not docked — probe a docked clone.

**ExtUtils clone topology**

    56 full ExtUtils, all 56 cloning from
      /FNSTools/CustomParTools/QuickExt/ExtUtils
    master NoNode DAT: syncfile=True ->
      modules/suspects/FNSTools/QuickExt/ExtUtils/NoNode.py
    clone child par write: sticks through normal use AND a master edit,
                           REVERTED by `comp.par.clone = master`

**NoNode usage across 12,088 live DATs**

    RegisterChopExec / RegisterDatExec / RegisterParExec /
    RegisterKeyboardShortcut / NoNode.Init
      -> 235 hits, ALL of them ExtUtils/description docs or NoNode itself
      -> 0 shipped-tool call sites

**`ui` surface** — no modifier state exists

    ... rollover, rolloverOp, rolloverPage, rolloverPanel,
        rolloverPar, rolloverParGroup, status, undo ...

**Windows OS key state works inside TD**

    ctypes.windll.user32.GetAsyncKeyState -> {'shift': False, 'ctrl': False,
                                              'alt': False, ...}

---

## 12. ExtUtils — the minimal variant could not receive fixes  `[BUG]` — DONE

**Symptom.** Removing Stubser from the registry hosts' ExtUtils (the tail of
item 3's cleanup) turned out to be unsafe: a safety probe found their
`CustomParHelper` had **no `_stubber()` guard**, so deleting `extStubser` would
have left `STUBSER` pointing at a destroyed operator behind the old
`is not None` check — the dead-wrapper bug, recreated 96 times.

**Root cause — two ExtUtils, one name, one propagation rail.**

    full ExtUtils     48   47 clone from CustomParTools/QuickExt/ExtUtils
    minimal ExtUtils 171   clone = None, every single one

The full variant propagates fixes by cloning. The minimal one has no master of
its own, so its only rail is per-DAT file binding — and in the 96 registry
hosts that rail was broken in a way that reads as live:

    CustomParHelper, extParExec, extSeqParExec, extParGroupExec,
    extParPropDatExec   ->   syncfile = True,  file = ''

`syncfile=True` with an empty `file` is a **no-op binding**. The 55 minimal
copies under `FNS_About` were bound correctly and are byte-identical to disk,
which is what specified the target state. The 96 had been frozen since they
were stamped: no `_stubber()` guard, and exec callbacks still resolving the
helper by hard-coded name (`mod('CustomParHelper')`) instead of through the
dock (`mod(me.dock.name)`).

The split is exact — 100% of the stale ones are registry hosts, 100% of the
clean ones are `FNS_About`. `UpdaterHardening` bound and slimmed the latter and
left the former alone; every host stamped since inherited the unbound master.

**Fix, in the only safe order.** Bind first (which delivers the guard), then
delete. Reversing it reintroduces the dead wrapper. Each file's disk content is
pushed into the DAT *before* the `file` par is set, so the two already agree and
`syncfile` cannot write stale text back over the shared source — verified: the
five source files are unchanged.

    ops                18,624 -> 16,800   (-1,824, -9.8% of the project)
    bound and guarded  55/151 -> 151/151

**Naming.** Both COMPs were called `ExtUtils`, which is why a stale minimal one
could sit unnoticed inside 96 hosts. The minimal variant is now
`ExtUtilsMinimal` (57 full / 167 minimal, invariant verified both ways).

The rename could not land as-is. Extensions reach their ExtUtils two ways:

    next((d for d in me.docked if 'ExtUtils' in d.tags), None)   # 911 DATs
    or me.parent().op('ExtUtils')                                # 220 DATs

Tag-primary survives a rename; the name-based fallback does not — and **95 of
the minimal copies are not docked to anything**, so the fallback is their only
path. Renaming first would have broken all 95 at once. The fallback is now
tag-based, matching the primary (21 source files + 12 unbound/vendored DATs no
file edit reaches). Three name lookups deliberately remain: `ExtQuickExt` and
the NoNode test rig target the FULL master, which keeps its name.

**Two things worth keeping.**

- The tag is the contract, the name is a label. Every one of the 219 COMPs
  carries the `ExtUtils` tag and it was never touched; that is what made a
  171-COMP rename survivable at all.
- A longer name widens a node's tile (180 -> 288 units), which is a real layout
  consequence of any rename: it exposed 23 pre-existing `vc_data` overlaps and
  created 2 new ones. All 25 repositioned.

**Left open.** `/PreviewPanel25/.../FNS_About/ExtUtils` holds a nested
`extStubser/extStubser` inside a *full* ExtUtils — an artifact, not covered by
either sweep. `VSCodeTools` and `QuickExt` keep their own Stubser by design;
`CustomParHelper.EnableStubs` points users there.

---

## 13. The `.py` split sorted by mechanism, not by role  `[REFACTOR]` — DONE

**Symptom.** Source files lived in three places with no rule a reader could
apply: 91 under `FNSTools/`, 67 under `modules/suspects/`, 29 under `scripts/`.
[ExternalizationOwnership.md](ExternalizationOwnership.md) said this was
deliberate — PI's tree answers *"what ships"*, Embody's answers *"which files
reload live"*.

**Measured, that boundary was not there.** Counting live DATs whose `file` par
points at a `.py` with `syncfile` on:

    scripts/           1,782 bindings    20 files
    modules/suspects/    474 bindings    56 files
    FNSTools/            464 bindings    70 files

All three hot-sync, PI's tree included —
`modules/suspects/FNSTools/QuickExt/ExtUtils/CustomParHelper.py` is both a PI
export *and* the hot-sync source for 151 hosts, which is exactly how item 12
delivered its fix. Two more cracks: 31 of the 91 files under `FNSTools/` had no
`externalizations.tsv` row yet hot-synced fine, so the table is a partial
working set rather than the working set; and the "legal exception" of a
component split across both trees had become the pattern, at 7 components.

**The axis that does work is shared vs per-component.** `scripts/` holds
sources many components share — the QuickExt templates at 230 and 63 bindings
each, `RegistryBase.py` at 104. A file belonging to no single component needs a
home outside every component's folder. That is a category of twenty, not the
single "load-bearing exception" the rule named.

**Done.** `FNSTools/*.py` retired into `modules/suspects/FNSTools/…`; the
`FNSTools/` source tree no longer exists.

    modules/suspects/<component>/…   everything one component owns
    scripts/shared/ + templates/     sources many components share

94 files moved (91 `.py` + 3 component-owned `.html`), 470 live `file` pars
repointed, 0 left pointing at the old tree. Git records all 94 as pure renames
with 0 modified-after-rename.

**The ordering that made it safe.** `syncfile` was disarmed on every affected
DAT *before* the files moved, so no DAT ever pointed `syncfile=True` at a
missing file — the state that would have let TD write an empty DAT over a real
source. Re-armed only after repointing. Verified after: 933 DATs checked, live
text equals disk on every one.

**A false alarm worth recording.** Five DATs compared unequal to their files
until the check was made BOM-aware — `ColorUI/ExtColorUI.py`,
`FNS_Collect/FNSCollectExt.py`, `FNS_CommandRegistry/FNSCommandRegistryExt.py`,
`FNS_MediaBrowser/FNSMediaExt.py`, `FNS_PaletteRegistry/PaletteRegistryExt.py`
carry a UTF-8 BOM on disk that TD's DAT text does not. Content was identical.
Any future disk-vs-DAT comparison in this repo must strip `chr(0xFEFF)`.

**Checked before moving, so it need not be rechecked.** `publish_public.py`
gates public-vs-private by path, and `_gatedPrefixes` already emits *both*
layouts (`FNSTools/<pkg>/` and `modules/suspects/FNSTools/<pkg>/`), as does
`_packageish` — so the move cannot change any package's gated status.

**Deliberately left.** `scripts/UpdaterExt.py` belongs to `/Embody/updater`,
not to a FNSTools component. `PreviewPanel25/`, `FNS_CMS/`, `NoNodeTest/` and
`SwapTest/` are root-resident packages and test rigs, out of scope for a rule
about `FNSTools` components.

---

## 14. Three frozen RegistryBase copies, and a hole in how we verify  `[BUG]` — DONE

**Symptom.** After item 13's reinits, the textport showed:

    AttributeError: 'HubRegistryExt' object has no attribute '_packageHelpUrl'
      RegistryBase, line 377, in postInit
      HubRegistryExt, line 316, in _applyHostRegistration
      Context:(Extension 1) (/FNSTools/FNS_Hub/OpMenuConfigurator/FNS_HubRegistry)

**Cause.** Of 106 `RegistryBase` copies, 103 were current at 2000 lines and
**3 were frozen at 1908**, predating `_packageHelpUrl` (added in `a94dfc1`):

    /FNSTools/MISC/input_mouse/FNS_ToolbarRegistry/RegistryBase
    /FNSTools/FNS_Hub/OpMenuConfigurator/FNS_HubRegistry/RegistryBase
    /FNSTools/FNS_TimelineTools/FNS_TimelineRegistry/RegistryBase

This is the hazard `/fns-registry` names, in its worst form: **neither rail
reached them.** All three had `syncfile=False` (two with no `file` at all), so
the file rail was dead; and while their parents *do* clone from a master, clone
propagation is pull-based and lands only when the clone cooks — which for a host
in an undemanded panel may not happen until project load. Cloning-on is not the
same as fix-delivered.

The staleness predates this work. What this session contributed was the reinit
that ran `postInit` and turned a latent break into a visible one — it would have
fired at the next project open regardless.

**Fix.** All three set from `scripts/shared/RegistryBase.py` and bound to it
(text first, while sync was off, so sync could not write 1908 stale lines back
over the shared source). Now **106/106 bound and synced — 0 unsynced, 0
unbound** — so a base fix reaches every copy by file, without depending on
whether a panel happens to cook.

**The verification hole — this is the part worth keeping.**
`get_op_errors` reported **0 errors for `/FNSTools` while this was actively
throwing**. It surfaces operator errors; an exception raised inside an
extension's `__init__`/`postInit` is a *script* error and does not appear there.
Every "0 errors" claim in items 12 and 13 was made with that blind spot.

    op('/FNSTools').scriptErrors(recurse=True)     # extension/init exceptions
    get_op_errors(op_path, recurse=True)           # operator errors

**Both are needed; neither implies the other.** A sweep after this fix found
`/FNSTools` and `/sys` clean of script errors, and two unrelated ones outside
the toolkit (`/project1` scratch, third-party `/tox_updater1`) that were already
there.

Project rule 9 ("always check for errors after creating operators") names only
`get_op_errors` and should name both.


---

## 10 + 11 — done 2026-09-01

### 11. The sweep

`context` **2 → 25 of 103**: selected 9, network 8, current 7, rollover-par 1.
Every command that shipped without `help` now has one (5 → 0). The other 78
need no context — tool toggles, UI openers and global actions act on nothing
external, and the rule that a wrong token is worse than none is real: a
consumer greys out a command whose subject is absent, so a bad annotation
breaks a command that works.

**Tokens were taken from the subject each method RESOLVES, never from its
label**, and that mattered. `CustomParTools`' *Customize current COMP* and
*Open current COMP parameters* both say "current" and both read
`selectedChildren` — two of four would have been mislabelled from help text
alone.

Three declaration shapes had to be edited, which is why the first count did not
reconcile: **57 decorated methods, 27 `FnsCommands()` spec entries** across four
capability tools, and a few using the bare `@fns_command` form. **19 declaring
extensions are not externalized at all** and had to be edited live rather than
on disk.

Found on the way: five sources — `HubExt`, `FNSRemoteExt`, `FNSCollectExt`,
`FNSAutosaveExt`, `FNSMediaExt` — each had a `.py` on disk matching the live DAT
exactly while the DAT was bound to nothing. Editing the file would not have
reached TD; editing the DAT would have stranded the file. They agreed only by
coincidence. Verified identical, then bound.

`surface` stays at 4 and `capability` at 19 deliberately: which commands belong
on a session bar or in a context menu is a product call the in-TD palette will
make obvious, and annotating ahead of it risks doing it twice.

### 10. Arbitration

Built as groundwork, not a fix — the measurement in the section above still
holds, **there is no duplicate in the toolkit today**, and the feature is inert
until one appears.

**Identity is an opt-in `canonical` field, never derived from `id`.**
`toggleactive` appears twelve times across twelve different tools and `path#id`
already separates them; deriving identity from the id would collapse twelve
working commands into one.

**The rule is the registry family's own** — newest `Pkgversion` wins, a tie
keeps the incumbent, and it never prompts — reused deliberately so commands and
promoted globals do not need two policies in one head. The winner's spec
replaces the loser's *entire*: merging would let a surface declared only by the
loser survive into the winner. Losers are reported by `Shadowed()` rather than
dropped silently, because a command vanishing from a palette with no way to ask
why is very hard to debug.

An absent `Pkgversion` reads as `0.0.0` — lowest, not a refusal to arbitrate,
since refusing would mean serving both copies, the exact outcome this prevents.

`_verKey` pads to four components so **`1.0` equals `1.0.0`**; a bare tuple
sorts `(1, 0)` below `(1, 0, 0)` and would silently demote a package that wrote
its version with two components.

Verified against real packages: newest wins (3.0.2 over 3.0.1, loser shadowed
with `lost_to` + `winner_version`); tie keeps the incumbent; a versioned package
beats an unversioned one (0.1.0 over 0.0.0); `1.0 == 1.0.0`, `1.10 > 1.9`,
`2.0 > 1.999`; and with no canonical ids declared the whole path is inert —
103 served, 0 shadowed.

### A real bug the testing turned up

`RescanTools()` could not rediscover the registry-family tools, and the tag is
supposed to be exactly that durable mechanism. Measured:

    op('/').findChildren(tags=['fnscommands'])   -> 44, missing both /sys ones
    op('/sys').findChildren(same)                ->  2

**`/sys` is not reachable from a `/` sweep**, and the registry-family tools live
there by design (only the promoted global may register). So unregister → rescan
left them gone: 103 → 102 → 102, recovered only by an explicit `Register()`.
After scanning `/sys` explicitly: 103 → 102 → **103**, and the ConfigRegistry
case likewise 100 → 103. Also swapped `root` for `op('/')` per the project rule
that `root` is not reliably bound in every exec context.


---

## 3 + 4 — 2026-09-01

### 4. Stuck modifier keys — DONE on Windows

The doc said option 4 (does TD 2025 expose anything newer?) had to be settled
first. It is now settled: **no.** `ui` carries no modifier state at all, and
TD's panel values DO have `ctrl` / `alt` / `shift` / `cmd` but are documented as
"1 if the key is down WHEN THE PANEL IS CLICKED ON" -- latched at click time.
All three callers read OUTSIDE a click (a hotkey handler, a drop handler, a
display refresh), so panel values are the right idea with the wrong lifetime.

That leaves option 1, and it is built as
[`scripts/shared/FNSModifiers.py`](../scripts/shared/FNSModifiers.py) -- **one
shared helper**, as the item required, not three copies. Callers use
`heldOr(name, fallback)`; everything else is strategy behind that seam, kept in
one file so a later change of approach does not touch three tools again.

**The fallback is the contract.** `held()` returns True, False, or **None
meaning "cannot tell"**, and `heldOr` then returns the caller's existing CHOP
read. So the tool is fixed where the OS can be asked and byte-identical to
before where it cannot. It never invents a held modifier and never denies a
real one. macOS is implemented from the ApplicationServices API but **could not
be tested from Windows**; if it is wrong it raises, `held()` returns None, and
the Mac keeps exactly today's behaviour.

Proven twice over: `heldOr('shift', True)` returns `False` with nothing held --
a latched CHOP is correctly overridden -- and after a restart, with the helper
DATs absent entirely, all three tools ran with **zero errors**, which is the
fallback path doing its job under real conditions.

**A mislabel found on the way.** ParOPDrop's `null_mod_dat`, `null_mod_chop`
and `null_mod_dat1` do not carry what their names say: verified from their
channels they are **shift, alt and ctrl**. ParentHierarchy's `null_hk1` is
**ctrl** (`hotkey1/keyboardin2` watches `keys='ctrl'`), and QuickParCustom's
`null_hk['shift']` is shift.

### 3. CustomParHelper — fix (2) landed, the layer still open

Finding (2) -- `OnValueChange` discarding the `comp` it is handed -- is fixed at
all **four** sites (`OnValueChange`, `OnPulse`, and both ParGroup/Sequence
loops) via a new `_extForComp(comp)`. The two loop sites now route by
`_par.owner`, which is precisely the source the original author reached for and
left commented out one line above.

The comment they carried, *"a bit hacky to be able to call non-exposed methods
too"*, described a real need -- callbacks may be non-promoted and so exist only
on the instance -- but `EXT_SELF` is a CLASS attribute, so it answers "the last
extension to call Init" rather than "the extension owning this COMP".
`_extForComp` keeps the instance-not-COMP behaviour and just resolves it from
the right comp, returning `EXT_SELF` unchanged in the single-owner case.

**Sized rather than assumed**, which is what the entry was waiting on: **652
COMPs carry extensions, 21 carry more than one**, and of those pairs none
declares two `CustomParHelper` users -- they are `<Tool>Ext` + `CallbacksExt` or
`PopMenuExt` + `CallbacksExt`. So this is hardening, not a live bug. Getting
that number cost two TD deadlocks before it was finally answered with `grep`
over `modules/suspects/` (see the operational note).

Applying the fix also surfaced two more frozen copies:
`/PreviewPanel25/FNS_PaneTypeRegistry/{ExtUtils,FNS_About/ExtUtils}/CustomParHelper`
were unbound at **487 lines** -- the pre-slimming version, the same "neither
rail" case as items 12 and 14. Bound and current; **232/232 copies now carry the
fix and 0 are unbound.**

**Still open:** the parfield-style declarative layer, findings (1) invariant,
(3) `co_argcount` arity, and (5) positional group naming. (1) is worth writing
down as a rule -- *an extension's module reference must be local* -- and was
measured safe today at 726/726.


---

## 3 — the parfield layer, built 2026-09-01

The half worth taking from tdp-TouchUtilCollection is now in
[`CustomParHelper.py`](../modules/suspects/FNSTools/QuickExt/ExtUtils/CustomParHelper.py):
a class may DECLARE its parameters and have them created, instead of only
having them reflected.

```python
class MyToolExt:
    Speed = CustomParHelper.ParFloat(default=1.0, min=0, max=10, page='Settings',
                                     help='Playback speed multiplier.')
    Mode  = CustomParHelper.ParMenu(['fast', 'slow'], page='Settings',
                                    help='Which way the thing runs.')
```

**No base class**, which was the owner's cut and the right one: a ParField is
an ordinary class attribute, so declaring costs nothing structural and
`EnsureExtension` is not adopted. Twenty field types (`ParFloat`, `ParInt`,
`ParStr`, `ParToggle`, `ParPulse`, `ParMenu`, `ParStrMenu`, `ParFile`,
`ParFolder`, `ParHeader`, `ParXYZ`, `ParRGB`, `ParRGBA`, and the OP-reference
family), reachable off `CustomParHelper` so the existing single import line is
still enough.

**Declarations run BEFORE reflection** in `Init`, so a declared parameter is
present when properties and callback routing are generated. That is also what
closes finding **(4)**: reflection generates properties once at Init, so a
parameter added later has none until someone calls
`UpdateCustomParsAsProperties()` by hand — a declared parameter cannot drift
from its property, because the declaration creates both.

Four properties, each verified live rather than asserted:

| | |
|---|---|
| **Additive** | a class declaring nothing gets `[]` back and its parameters are untouched — which is why this landed without changing a single existing tool |
| **Idempotent, values safe** | value 7.5 survived a re-run that refreshed label and help; no duplicate parameter |
| **Restyle is refused, not forced** | declaring `ParStr` over an existing Float leaves the Float and its value intact, and says so — applying it would mean destroying the parameter along with its expression, binding and export |
| **Help is mandatory** | omitting it raises at DECLARATION, at class-compile time in front of the author, per `.claude/rules/parameters.md` |

Regression check on the 232 synced copies: 232/232 carry it, 0 unbound, no
script or operator errors, 103 commands, 130 registry entries, 60 fps.

**Finding (1) is now written into the module** as an invariant rather than
left as a note: *an extension's module reference must be LOCAL*. Generated
properties are set on the CLASS, closed over one `owner_comp`, and that is safe
only because `.module` is per-DAT. Two COMPs pointed at one module share a
class, and the second `Init` rebinds the first's properties. Measured safe today
at 726/726. Callback ROUTING no longer has the problem at all — `_extForComp`
resolves it per-comp.

**Left as papercuts, deliberately:** (3) callback arity from
`__code__.co_argcount`, which mis-dispatches for defaults, `*args` or a real
wrapping decorator; and (5) `__isParGroup` as `len(pg) > 1` with positional
group naming. Both hold for TD's conventions; neither is principled.


## 15 — declarative callback decorators, built 2026-09-01

Asked for as "some decorator scheme to register methods for pars / operators
callbacks, without initing CustomParHelper or initing with a different
signature". Built in NoNode alone, which is what makes the second half true:
`NoNode.Init` + `NoNode.HarvestCallbacks(self)` is a complete tool with no
CustomParHelper involved.

Contract and reasoning: [NoNodeCallbackDecorators](NoNodeCallbackDecorators.md).
User-facing form: `packaging/docs/CustomParTools.md`, under NoNode.

The load-bearing decisions:

- **The decorator returns the function untouched**, recording a spec in a marker
  attribute — the FNSCommand pattern. Dispatch reads `co_argcount` to decide how
  many arguments a callback wants, so a wrapper would mis-call every decorated
  method. This is papercut (3) from item 3 turning into a real constraint rather
  than a note.
- **Targets are strings resolved at harvest.** The same class-body timing
  problem that forced the parfield layer to an init-time API; here it can simply
  be deferred, so the declarative form survives.
- **Harvest rebuilds the registry** instead of adding to it, so a deleted
  callback leaves nothing stale — the defect class behind 2d/2e, addressed by
  construction rather than by a better `Deregister*`.
- **A bad target is reported, not raised.** `RegisterParExec` currently returns
  silently when the parameter does not exist; a mistyped name yields a callback
  that never fires and never complains.

**Measured, and it corrected a wrong theory of mine.** Arming is not something
the caller does: each exec DAT's target parameter is an expression over the
registry, so registering arms the DAT as a side effect. `__markOperatorAsWatched`
is cosmetic (node colour + a move-survival token) and arms nothing — an earlier
guess that it was the arming step was wrong.

Coverage went 15 → 23 cases in `NoNodeTest/nonode_harness.py`. Two pre-existing
cases had to be **scoped** rather than weakened: they asserted over the whole
registry and so assumed the rig held exactly one registration. Adding a second
legitimate one broke them, which is the harness working correctly.

## 16 — 63 ExtUtils clones were watching the master's parameters  `[BUG]` — DONE

Self-inflicted, found while verifying item 15. Every `extParExec`,
`extSeqParExec` and `extParGroupExec` in 63 ExtUtils copies had `ops` and `op`
set to the ABSOLUTE path `/FNSTools/CustomParTools/QuickExt` — so 55 tool COMPs
(plus 4 scratch COMPs in `/project1`) had their parameter callbacks pointed at
the master instead of at themselves.

The cause is an earlier repair in this session that restored the MASTER's value
using an absolute path. It is correct *for the master* and wrong everywhere it
propagates: those 63 are clones, so cloning carried it to all of them. The 169
copies that were fine are `ExtUtilsMinimal`, which has no master and therefore
received nothing.

**The general rule this is a case of:** the project's ban on absolute operator
references is not only about renames. An absolute path written into a CLONE
MASTER is a path that will be evaluated from 63 other places, where it silently
means something else. `../..` is right in all of them.

Repaired to `../..` across 696 `ops` + 696 `op` values (three exec DAT names ×
232 copies): 0 still absolute, 0 misresolving — each now evaluates to its own
owning COMP. `/FNSTools` reports no errors and no extension script errors, and
the harness stayed at 23/23. Persisted with a project save.


## 17 — CustomParHelper declarative callbacks, built 2026-09-01

Asked for straight after item 15: "can we have CustomParHelper decorator
too...? ... I'll be using customparhelper for the most part." So the set is
COMPLETE rather than a useful subset — one decorator per callback kind:
`onPar` (value change, or pulse on a Pulse par), `onParGroup`, `onSeq`,
`onSeqBlock`, `onAnyValueChange`, `onAnyPulse`.

Contract: [CustomParHelperContract](CustomParHelperContract.md). User-facing
form: `packaging/docs/CustomParTools.md`, "Naming the handler yourself".

**The design decision worth keeping.** Dispatch resolves a handler by NAME in
six places (`hasattr(comp, f'onPar{_par.name}')` and friends). Rather than
thread a resolver through all six in a file that syncs to 232 copies, harvest
binds the decorated method to its CONVENTIONAL name on the extension instance.
Every existing lookup then finds it unchanged, which buys the entire callback
surface — including sequences, ParGroups and both general callbacks, with all
their arity variants — for zero dispatch edits. `Init` harvests, so no
signature changed and a class that declares nothing is untouched.

Two reports the convention cannot produce, both logged rather than raised: a
declaration naming a parameter that does not exist, and a collision with an
existing conventionally-named method — where the REAL METHOD WINS and the
declaration is reported ignored, since silently shadowing working code is the
worse failure.

**Verification, and one honest correction.** The first end-to-end run showed
the pulse decorator firing but value-change and ParGroup not. That was a TEST
artifact, not a defect: those parameters were created in the same call that
changed them, before the exec DAT's `pars` expression had picked them up.
Direct dispatch proved routing was correct, and a rerun with the parameters
already present fired all of them. Final measurement, one real change each:
`Gain` (value), `Reset` (pulse) and `Translate` (ParGroup) each fired their
freely-named handler once, alongside a conventional `onParSpeed` and a NoNode
decorator on the same extension, no script errors, harness 25/25.

`onSeq` / `onSeqBlock` are verified at the name-resolution level (all six kinds
produce exactly the string dispatch looks for) but not exercised end-to-end —
the rig has no sequence parameter. Stated rather than glossed.

**This supersedes a claim in [NoNodeCallbackDecorators](NoNodeCallbackDecorators.md)**
made the same day: that a freely-named handler for your own custom parameter
had to go through NoNode. For a parameter on your own COMP, CustomParHelper's
decorators are better — they use the exec DATs already watching it instead of
adding a second watcher. NoNode's `onParExec` is for parameters on OTHER
operators.

## 18 — Follow-ups batch, 2026-09-02

Six non-urgent items the owner asked for in one go. Recorded first, corrected
in place as each lands.

| # | Item | State |
|---|---|---|
| 18a | Palette: presets — Alt+S bakes a command's arguments under a name; `PRESET` rows; Ctrl+H deletes | built, verified headless: alias + mid-walk preset persist in the `Presets` par, rank, run plumbing, delete |
| 18b | Palette: dismiss on blur — input `onFocusEnd`, decided 3 frames later so a row click does not close it | built; verified that the check keeps the palette open while the input has focus; the close-on-click-outside half needs a human |
| 18c | Palette: Ctrl+H hides the selected command from inside the palette (Commands tab shows it again) | built, verified |
| 18d | QuickMarks: the doubled `RetrieveQuickmark` in `HandleShortcut` — explain, then remove | removed; measured on a floating pane that x/y/zoom set in the same call as the owner switch survive two frames |
| 18e | QuickMarks: auto-name identical for nested `base1` networks — shortest unique path suffix | built; the owner's three marks would now auto-name `base1/base1/base1/base1/base1`, `base7/base1/base1/base1/base1`, `base7/base1/base1/base1` (stored labels untouched) |
| 18f | CustomParHelper: `co_argcount` arity (finding 3) and positional group naming (finding 5) | DONE — `_arity()` reads the signature (functools.wraps seen through, `*args` capped at the richest call, defaults still count) at all 8 dispatch sites; `_groupName()` / `Par.parGroup.name` replace every `Parname[:-1]`. Landed live: 237/239 root copies re-synced (the 2 stale are the known PreviewPanel25 pair), 227 owners reinitialised in 12 chunks, 201 bound, 32 never call Init; harness 25/25; HotkeyManager's mixed-arity callbacks clean; one AutoRes `kindergaertner_mymod` observer error during the burst (`Target` evaluated None), cleared and not recurring. TD re-inits dependents lazily on access -- measured, see CustomParHelperContract.md, Landing |

**Item 5's "naming feature still open" line is stale**: the sequence-par rework
it points at is the LANDED paragraph above it. What actually remained of item 5
is 18d and 18e.

**18f lands last on purpose.** `CustomParHelper.py` file-syncs into every
tool's ExtUtils, so it is edited in a scratch copy, parse-checked, and landed
when no peer session is mid-reinit — a peer was live in FNS_HotkeyManager while
this batch started.

## 19 — Fleet rollout, observer guard, doc hygiene, 2026-09-02

Leftovers the owner asked to be cleared without them.

- **ExtUtils rollout** (`extutils_distributor.rollout(apply=True)`): the 58
  slim copies without a `FNSCommand` DAT got one, file-synced to the master;
  `/PreviewPanel25/FNS_PaneTypeRegistry/FNS_About/ExtUtils`, the one full copy
  with no clone link, was linked, which also removed its stray nested
  `extStubser` (item 12's leftover) by clone conformance. Survey now
  `healthy=True`. Clone conformance rebuilt that copy's children with docks but
  no positions, so its NoNode docks were re-rowed by hand (two rows under the
  host); the sibling `FNS_PaneTypeRegistry/ExtUtils` copy's CustomParHelper
  docks likewise. 55 owning packages re-exported through PI. FNS_Updater's was held back
  at first on the belief that a peer session was mid-work in it; that was
  the wrong session (the HotkeyManager one, which pointed it out), and the
  foreign-packages session that did own it had committed (`8a280ae1`), so
  the tox was re-exported in a follow-up commit. A stale tox there would
  have silently dropped the four added module DATs at the next project open.
- **kindergaertner ChildObserver**: `Observe()` dereferenced `Target.eval()`
  unguarded and raised once during the CustomParHelper reinit burst (item 18f).
  Guarded in the QuickExt master and the AutoRes and AutoCombine copies; the
  OpTemplates copy already carried its own guard. The three copies are not
  clones of the master (`clone=None`), so each was patched and saved.
- **Docs**: the backlog's "Suggested order" now says what is actually left;
  item 6c's "still open" is marked resolved (the registry has its catalog entry
  and page, and ships built-ins); the palette design doc's five open decisions
  are recorded as closed; `CommandRegistration.md` names the live registry
  version (1.9.0, not 1.2.0).
- **Not done, and why**: the release rail (shipping decision); the hand tests.
  The TDXLPP mirror was done by that project's own agent the same day
  (registry 1.9.0 verbatim, canonical ids verified equal, Pkgversion on its
  built-in owners); see `CommandRegistration.md`.

## 20 — FNS_PreviewPanel: PreviewPanel25 becomes a package, 2026-09-02

Owner's direction: PreviewPanel25 is to be tracked privately as a package,
gated at the base tier, checked over and optimised. Decisions taken by the
owner: tier `8323905` (the tier the four gated packages use), name
`FNS_PreviewPanel`, category Network; the nested `UI/POPtoDAT_panel` stays
nested and PI-tracked but is not a package of its own; ExtUtils copies move to
the current shapes; FNS_About to the newest shape; catalog entry and doc page;
a `pre_release` hook; a code review of the extensions; the extensions
externalised; a cook pass with the panel open.

**Measured before touching (2026-09-02).** A container at the project root,
3,654 ops: `UI` 2,766 (of which `POPtoDAT_panel` 2,654, `popViewer` 1,122),
`default_render` 595 (a POP/SOP/T3D render chain), the pane-type host 213;
62 developer annotations hold 1,426 of those ops; 7 ExtUtils copies. Idle
cook 0.23 ms with 0.04 ms in children -- negligible, so "optimise" is size,
ship shape and the open-panel cost, not idle cook. Two pane types are
registered from inside it: `PreviewPanel` (root host) and `PopViewer` (the
nested panel's host). It rewrites its tox on every project save because an
Embody externalization row (`externalizations.tsv`) still points at
`modules/suspects/PreviewPanel25.tox` -- the cross-system binding
`ExternalizationOwnership.md` says to fold to one owner when next touched.
Two dangling references to `../../project1/box1` (the nested panel's `Pop`
par and `default_render/select_pop`). Both hosts' extension DATs file-sync
from the RETIRED `PreviewPanel25/FNS_PaneTypeRegistry/` tree, not from the
master. No `Pkgversion`, no `FNS_About` at the root; the nested panel carries
an FNS_About with an EMPTY `Pkgversion` and its own About pars.

| Step | State |
|---|---|
| 20a Code review of PreviewPanelExt / POPtoDATPanelExt / callbacks; fix what is wrong | done -- two real bugs: `PreviewPanelExt` scheduled a `_postInit` that never existed (a deferred AttributeError on every load) and `POPtoDATPanelExt.onParPop` re-entered itself while syncing; both fixed |
| 20b ExtUtils shapes: root full clone (it declares a command); nested panel -> ExtUtilsMinimal; hosts and FNS_About -> ExtUtilsMinimal; hosts' DATs bound to the master's files | done -- root: full ExtUtils clone (it declares `openpreviewpanel`); nested panel, both hosts and FNS_About: ExtUtilsMinimal; hosts' DATs bound under `modules/suspects/FNSTools/FNS_PaneTypeRegistry/`. Trap: `copy()` dropped a copied minimal's internal docks (extParExec / extSeqParExec / extParameter), so the nested host's register pulse died on `me.dock`; the distributor's `_repairDocks` put them back |
| 20c FNS_About at the root (current shape, `Pkgversion` 0.1.0, owner mirror by expression); the nested panel's FNS_About folded away | done -- root `FNS_About` (Pkgversion 0.1.0, page To Deploy), owner mirror by expression |
| 20d Dangling `project1/box1` references cleared; legacy `dropped_op` storage cleared | done |
| 20e `pre_release` hook: strip annotations and file bindings, blank project state (dropped op, POP refs), ship hosts inert | done -- `pre_release` (58 lines) blanks storage, POP refs and select ops, destroys every annotation (62 live) and severs clone links; PI's `CompReleaseManager.run_prerelease` runs it on the release candidate |
| 20f Move to `/FNSTools/FNS_PreviewPanel` (hosts' `Comp` relative first), PI-owned: Embody row removed, PI Add root + nested panel + extension DATs, git paths moved, retired tree removed | done -- hosts registered under the new path (root `PreviewPanel`, nested `PopViewer`), the command announced; Embody row gone; PI Add on root + nested panel + 6 DATs (13 tracking rows); retired tree removed from git |
| 20g Catalog entry (Network, access 8323905) + `packaging/docs/FNS_PreviewPanel.md` + site build | done -- catalog entry (Network, 8323905), `packaging/docs/FNS_PreviewPanel.md`, site build exit 0 |
| 20h Cook pass with the panel open: measure with a POP and a DAT dropped in; diet what shows | done -- see the cook pass below |
| 20i Release through PI, read the artifact back, save, commit | done -- `modules/release/FNS_PreviewPanel.tox` (799,578 bytes, 2,153 ops); read back in a non-cooking `/sys` container: 0 annotations, no `pi_suspect`, no file-bound DATs, no dev tox bindings (only TD's own disabled docsHelper references inside the stock popViewer), Pkgversion 0.1.0 with FNS_About, both hosts Autoregister on |

**Cook pass (2026-09-02, panel open, a 40k-point POP dropped in).** The tool
costs about 2 ms a frame -- 1.38 ms CPU + 0.58 ms GPU, 38.6 MB GPU -- and is the
project's top hotspot while the panel shows, with fps steady at 60. Nearly all
of it is TD's stock `popViewer` clone (`/sys/TDTox/popViewer`, 1,162 ops; its
`render1` alone 0.86 ms CPU + 1.44 ms GPU); the tool's own overhead is about
0.25 ms; the expensive ops in the first frames were one-time setup cooks; the
cook-dependency-loop warning sits inside TD's `numericalChooser`. Nothing of
ours to diet -- the panel's cost IS the viewer it embeds.

**Traps paid for in the move.** (1) Loading the renamed tox reloaded the root
host from its own legacy tox (stale bindings, the old full ExtUtils): disable
every nested `enableexternaltox` before saving or loading a parent tox.
(2) Hosts register with the path they have at init: rename BEFORE saving the
tox, or the entries carry the old path. (3) A COMP copy drops the internal
docks of a copied ExtUtilsMinimal (20b). (4) PI's `Add` appends its own rows
beside repointed ones -- dedupe the live `suspects` table by path.

## 21 — Shared command curation file + config hygiene, 2026-09-02

Owner's direction (2026-09-02, after the config survey): favourites, hidden
overrides and presets are to be SHARED between FNS_CommandPalette and the
TDXLPP launcher, and the survey's other findings stand as work.

**Survey (2026-09-02, live + the roaming file).** 38 tools carry a registered
config host; the roaming file held 51 sections. The four tools the docs listed
as "not registered at all" (QuickMarks, midiMapper, oscMapper, ResetPLS1) all
carry registered hosts with `Persistpars` on and no exclusions: what stayed
local was their STATE rail, not their parameters. QuickMarks had moved its
marks from StorageManager into the `Mark0..Mark9` pars, so operator paths from
this project sat in the roaming file and autoload applied them in every other
project on the machine. Recent tools without a host: FNS_Autosave (real
prefs), FNS_Remote (prefs beside project-specific Control/Perform pars);
FNS_MediaBrowser, FNS_Collect, FNS_PreviewPanel and FNS_CommandKit have
nothing to persist; the registries stay out by design.

| Step | State |
|---|---|
| 21a Contract `docs/CommandCuration.md`: beside the gate file under the machine-default palette, schema 1, `tool#id` keys, per-entry merge by `updated`, tombstones pruned after 30 days, seeding by union, the launcher's preset field names | done |
| 21b Palette: `CommandCuration` module DAT (PI-tracked) holds the file protocol; `CommandPaletteExt` routes Favourites / ToggleFavourite / _overrides / ToggleHidden / ListPresets / SavePreset / DeletePreset through it; the three legacy pars adopted once and emptied; `Cfexcludepars` += the three pars | done -- exercised live: first load stamps `seeded.fnstools`; a corrupt file is parked and rewritten from memory; a vanished file comes back; a peer write landing between read and write is merged, not lost |
| 21c Launcher side: contract handed to the tdxlpp agent; their `quick_*` prefs adopt by union and retire | pending their owner's scheduling -- their agent verified the mapping (QuickCommandPreset lossless, machine-default palette resolvable, tool#id = command_identity) and raised three objections, all adopted the same day as rules 3, 5 and 6: re-stat before the rename, rewrite from memory after parking, `seeded` recorded in the file; their second pass added the rename retry (Windows sharing violations) and a `revision` counter, both adopted and verified live |
| 21d QuickMarks `Cfexcludepages = Marks`; ResetPLS1 `Cfexcludepars = Limitdepth Root Except`; config saved once so the roaming sections drop the marks | done |
| 21e Hosts stamped on FNS_Autosave (excl. Status Lastsave Savenow) and FNS_Remote (excl. Active, status/url/port readouts, pairing pulses, Control*, Perform*) through `StampHost`; `Promotepars` on afterwards (the stamp leaves it off), registered, moved next to their tools | done |
| 21f Docs: ScopeAndPersistence §7 and the fns-config-scope skill corrected; CommandRegistration and CommandPaletteDesign point at the contract | done |
| 21g Save (PI per owner, root last), verify, commit | done -- 44 toxes (the 40 dock-repaired owners, the three tools with new hosts, the root), no operator errors, no script errors, config rewritten once, project saved |
| 21h Fleet: 46 of 201 slim ExtUtils copies -- every config host, the `/sys` global's included -- had lost their internal docks, so their par callbacks were dead and a changed exclusion never re-registered (found because QuickMarks' marks stayed in the roaming file after the exclusion); repaired with the distributor's dock repair, the 40 owning suspects saved, and `survey()` / `rollout()` now check and repair slim docks (they skipped every slim copy and reported healthy). Clone re-sync and promotion copies drop docks, so expect drift again after master changes: run the rollout after any ExtUtils surgery | done |

## 22 — FNS_CommandRegistry 0.1.1: annotations out, verified cooking-enabled, 2026-09-02

Owner's direction (relayed by the launcher's agent, confirmed here): the 0.1.0
artifact's five documentation annotations broke the launcher's import
(`'td.annotateCOMP' object has no attribute 'Editing'`, 5,800+ errors), and
the read-back that passed them was a cooking-disabled load, where extensions
never initialise. Same lesson as item 14, one layer down: op errors and script
errors are different things, and a container that cannot cook shows neither.

| Step | State |
|---|---|
| 22a The five annotations destroyed on the master (`ann_command_registry`, `ann_builtin_commands`, `FNS_BuiltinCommands/ann_builtin_owners`, `TD_Dialogs/ann_td_dialogs`, `TD_Session/ann_td_session`) | done |
| 22b `pre_release` hook on the master strips annotations from the staged copy at every release (PI-tracked) | done |
| 22c Pkgversion 0.1.0 -> 0.1.1 on FNS_About (a changed artifact needs a new version; the owner mirrors by expression) | done |
| 22d Released through PI: `modules/release/FNS_CommandRegistry.tox`, 88,022 bytes, sha256 `ebc48223849764cb865711ed3d3abe6ff0d85c702ed8b80e6ee38b08c122462c`; `packaging/launcher_mirror.json` updated | done |
| 22e Verified COOKING-ENABLED: loaded once into a base at the project root, 1,271 frames later `errors(recurse=True) == []`, no script errors, `op.FNS_COMMANDREGISTRY` still the `/sys` incumbent (REGISTRY_VERSION tie, no promotion), 141 commands before, during and after, 0 shadowed; the copy destroyed | done |
| 22f Launcher side: import verbatim, byte-identical copy at `utility/TDXLauncherUtility/FNS_CommandRegistry.tox`, checker exit 0 | done -- imported verbatim the same day; verified cooking-enabled on their side (2,130 frames, 0 errors, 40 commands, 38 built-ins, 38/38 canonical, Shadowed() empty); checker exit 0 from both repos |

Pre-existing, not touched: `/sys` and `/button1` overlap at the project root.

## 23 — FNS_BeatMod: beat-synced parameter modulation, 2026-09-02

Owner's direction (autonomous, "I'm going to a party"): adopt the idea behind
`/stoleTK`, which turned out to be a copy of RayTK 0.42 whose
`operators/utility/lfoGenerator` is the relevant piece, as a Base-gated
package named FNS_BeatMod; derive the beat sync from the Beat CHOP, add a tap
tempo that sets TD's global BPM, be smarter about placement, cover ParGroups,
and tween into the modulation instead of cutting. Design: `BeatModDesign.md`.

| Step | State |
|---|---|
| 23a Design doc written first; the source studied (phase ramp -> Pattern lookup, sync table, wave table) | done |
| 23b Tool shell under `/FNSTools` at a free slot in Global Extensions: full ExtUtils clone docked to the ext DAT, FNS_About (0.1.0, owner mirror by expression, owner About page in FNS_PreviewPanel's shape), `fnscommands` tag, PI-bound root + DATs | done |
| 23c `modulator` template of stock ops: Beat CHOP (locked, period = Beats, multiples = channels, shiftstep = Spread) -> select -> phase (Expression) -> Lookup into a Pattern with one channel per member -> shape (`centre + amp * wave * blend`) -> rename -> out1; Constant -> Lag for the blend | done |
| 23d Extension: parfields (Bpm, Tap, Modulate, Remove, Period, Wave, Depth, Tween, three Shortcut pars), Apply / Release / RestoreFromModulator / Modulators, four commands (ModulateRollover, RemoveRollover with context rollover-par; TapTempo; SetBpm with state), hotkeys via a keyboardin following the pars | done |
| 23e Config host stamped (hotkeys, Bpm and pulses excluded), `pre_release` (annotations out, clone links severed), catalog (Parameters, 8323905), `packaging/docs/FNS_BeatMod.md`, site build exit 0 | done |
| 23f Verified live: group of three (geo `t`) and a lone par (level `opacity`); first frame reads the old values, glide measured rising (lag 0.04 -> 0.70 -> 0.90) while the values swung; placement stepped past a filler at the first slot; refusals for a driven par and a non-numeric par; SetBpm 128 reached the timeline and the par, tap from a 0.5 s interval gave 120; release restored constants and destroyed both modulators; HotkeyManager discovers the three bindings, no clashes | done |
| 23h Owner's follow-ups (2026-09-03): random waves (`random` steps per cycle, `randomsmooth` smoothsteps between cycle values, both from the Beat CHOP's `count + ramp` and a per-modulator `Seed`); the hovered MEMBER alone as a second action (`Ctrl+Alt+B`, `Modulate hovered par only`) beside the toolkit's whole-group rule, with QuickParCustom's owner-and-name guard; then the rest that needs no mouse: a gaussian wave in the shaped branch, the hovered-par commands falling back to the palette's summon snapshot while it is open, the Bpm par mirroring the timeline live through `parexec_tempo`, and the hotkey callback chain exercised by name | done |
| 23i Owner's second pass (2026-09-03, back at the desk): `/stoleTK` read properly this time (RayTK's `editorActions` animate-param group with an LFO and a Speed generator per parameter tuplet); five actions on five hotkeys (LFO, Speed, menu, Remove, Tap) with a popMenu at the mouse ticking the beat division and beat sync; Speed as a real Speed CHOP from the current value, rate per division times tempo when synced; Tweener (shipped inside the tool at the owner's direction) fades Blend on a curve, the Lag CHOP stepping aside; the rollover rule becomes par-if-hovered-else-group; every outcome on `ui.status`; a slim ExtUtils clone master created at `QuickExt/ExtUtilsMinimal`, the tool's four slim copies linked to it, the distributor surveying the unlinked rest (181) and linking them only on `rollout(apply=True, link_slim=True)`, the owner's call | done |
| 23j Owner's hand test (2026-09-03): a tap made every LFO jump, because locked mode derives phase from timeline position times tempo; modulators now follow TD's own free-running global beat (`/local/master_beat`, `global` play mode, a `Playmode` opt-out on the modulator), so tempo changes change the rate and never the phase (a master of our own made TD warn about two Update Global sources, so it went); `Tapresets` (off) for a deliberate bar realign; the menu's ticks pre-select in place through a live `checkedItems` expression instead of closing and re-opening; the modulator's Target par widened from COMP to any OP after a test on a Noise TOP warned; Speed's default a tenth of the norm range per period | done |
| 23k Owner's second hand test (2026-09-03): the modulation now sweeps the parameter's norm range (`Min`/`Max` from normMin/normMax, `Multiplier`, `Offset`), unipolar patterns mapped to -1..1; the rest values moved from a string par into a `rest` Constant CHOP the glide starts from and Remove returns to; "tempo did not change the speed" measured true, TD's `/local/master_beat` keeps the tempo it last saw because nothing cooks it, so `chopexec_master` in the tool pulls it every frame (followers at 60 BPM ran at 120 until then) | done |
| 23l Measured properly (2026-09-03): a local-mode Beat CHOP cooked every frame follows the timeline tempo exactly (218.2 against 218.2) and integrates, so it never jumps; TD's global master does not follow the tempo, pulled or not. Each modulator now runs its own local beat with a `pull` CHOP Execute inside; the first-tap reset realigns all modulators together; `chopexec_master` removed; tap tempo writes nothing before the fourth tap; a fade that sat at 0.033 during the hand test was a Tweener stepping per frame while batch saves blocked the main thread, not a fault | done |
| 23m Owner's ask (2026-09-03): a modulator deleted by hand should glide its parameters back. Measured: OP Execute `onDestroy` fires after the frame without the operator (the DAT's own destruction), `onNumChildrenChange` after the fact; the driven par already raises by then. An extension `onDestroyTD` inside the modulator runs inside `destroy()` with everything readable, so `ModulatorExt` snapshots current and rest values and hands them to the tool (`op.FNS_BEATMOD`), which sets constants and tweens to rest. Follow-up 2026-09-14: undoing the delete brought the modulator back driving nothing, since undo does not restore the constants written from `onDestroyTD`; the tool now keeps the snapshot and the returning modulator's `__init__` reclaims its members a frame later, which also replaced the one-frame reinit confirm (BeatModDesign.md item 13) | done |
| 23n Owner's change of mind (2026-09-03): a new wave swings around the parameter's current value by default, to the nearer slider end (`edge`), or a fraction of the slider range each way (`fraction`, default 0.1); the whole-range sweep stays as the third strategy; `Rangemode` and `Fraction` on the tool, ticked in the menu; the modulator gained a `Around` toggle that makes Min..Max relative to each member's rest value. Tap tempo in the menu keeps it open | done |
| 23o Owner's idea and UI (2026-09-03): press and hold a kind in the menu and an XY pad (`window_xy` / `popXY`) opens under the cursor; u picks the beat division, v the swing around the value; release applies, the bottom edge and Escape apply nothing. Hold detection through the popMenu's callback DAT (`onMouseDown` / `onMouseUp` / `onRollover`) and a 350 ms `run`; release caught by the pad's Mouse In CHOP and by a watcher on `op.TDResources.MouseCHOP`; two Text TOPs show the numbers live | done |
| 23p Owner (2026-09-03): a parameter this tool already modulates is modified in place with a glide, never refused: `Modify` tweens Beats, Min, Max and Multiplier through Tweener and crossfades the wave through a second wave bank in the modulator (`Waveb`, `Wavemix`, a copied pattern/lookup/shaped/speed/switch chain off the same phase, `shape` mixing the banks), ping-ponging banks so nothing swaps back | done |
| 23q Owner's question (2026-09-03) exposed that the pad dropped its height for Speed and labelled it as a swing; the height is now the rate, that fraction of the slider range per the chosen division (top = half the range per division), labelled "0.25 per 1 beat" (per seconds with beat sync off), through Apply's depth so a running Speed glides to it | done |
| 23r Owner (2026-09-03): random waves drew a different sequence per member of a group, good sometimes and not others; `Randomlink` per wave bank on the modulator seeds every channel alike, a tool default and a menu tick beside beat sync, and a change on a running random modulation crossfades like a wave change | done |
| 23s Owner's UI (2026-09-03): a settings strip above the pad in `popXYmenu`, two horizontal rows of three minimal buttons (range strategy Edge/Frac/Full in one tint, polarity + / - / ± in another) lit from the tool's Default Range and the new Default Polarity, selected by a 400 ms dwell with the button down; polarity is a window question (`_window` takes polarity and a scale), so the pad's height now scales the window itself and unipolar windows stay anchored at the value | done |
| 23t Owner (2026-09-03): the beat divisions became a `Divisions` string parameter (beats, any order, fractions), parsed and sorted by the tool; the Default Period menu, the popMenu ticks and the pad's axis follow it; names encode the beats so a saved Default Period survives edits; docs vague about the count | done |
| 23u Owner (2026-09-03): the Tween Curve menu lists every easing curve in the tool's Tweener (31, rebuilt from its easing module at init), and the tool's parameters, which had accreted in creation order, carry explicit orders in sections: tempo, actions, new modulations, swing, Speed, glide, hotkeys | done |
| 23v Owner (2026-09-03): a CHOP reference whose channels are modulation sources: `modulator_chop` template (select, the owner's windowed normaliser, trigger envelope, range math, limit, smooth, fan, the shared output stage), a `CHOP Mod` page of defaults, a `From CHOP` popMenu sub-menu of the channels with hold-to-pad (x = smoothing), a third settings row (normalise, trigger, clamp), modify-in-place and cross-kind replacement through the rest value; both templates cook-disabled, copies switched on when placed | done |
| 23w Owner's reminder (2026-09-03): the config exception and the release hook for the CHOP source. `Sourcechop` is excluded from roaming on the host (verified on the host's own Excludepars) and cleared on the staged copy by `pre_release`, which also forces both modulator templates cold and drops any popMenu config copy TD spawns | done |
| 23x Owner (2026-09-03): a spawned CHOP modulator must read apart from a beat one, by colour since the name is long enough; amber and green node colours on the templates and stamped on each copy, existing modulators recoloured | done |
| 23y Owner (2026-09-03): the CHOP processing set by hovering, not on the modulator afterwards. Pages on the pad for a CHOP modulator: Norm and Trig switch their stage on and turn the axes to its numbers, Swing returns, each page keeps its values, all applied at release; the pad's position reported per frame and a corridor along the top so the strip is reachable without dragging the swing (fixed for the wave pad too); the third row only for CHOP pads | done |
| 23z Owner (2026-09-03): every parameter set from the pad before the modulator exists, with right-click as the lock. Right button on TD's mouse CHOP locks a page (values captured, crosshair and readout frozen through a switched-in Constant CHOP, pointer ignored until the page changes or a second right-click); pages for a channel Swing/Norm/Trig/Atk/Range/Lim (a Peak par on the modulator) and for a wave Swing/Phase/Glide, one kind row each; the wave pad starts from an existing beat modulator too | done |
| 23aa Owner (2026-09-03): no held button for the CHOP route, everything set up before applying, with a preview. `chopPanel` + `window_chop`: a staged copy of `modulator_chop` inside the panel (rest from the target, driving nothing), OP Viewers of Trail CHOPs of the source channel and the staged output, pages Swing/Norm/Thresh/Atk/Range/Lim with option rows (stages, range strategy, polarity, limit kind, envelope shape attack-release or attack-decay: `Trigmode` and `Decay` on the modulator), Apply through `ApplyChop`, Cancel/Escape drop the staging; the held pad waves-only behind `Holdpad` | done |
| 23ab Owner (2026-09-03): the third and final modulator, the record CHOP stuff from the root TODO annotation. `modulator_rec` (the take in a locked Select CHOP, Join CHOP insert bridge, Trim, Lookup on the beat ramp or a Speed CHOP clock; Seam blend/ping-pong/hard, Play Mode beat/time, Beats, Speed, Phase, Reverse) and the tool's recorder (Parameter CHOP into a Record CHOP: the first change starts, `alt.shift.r` or Stop After seconds of stillness ends with the still tail trimmed), Record page defaults, menu item, `RecordRollover` command | done |
| 23ac Owner (2026-09-03): allow marking multiple parameters for recording. The record command arms, marks and stops in that order; the take carries every marked operator through one Parameter CHOP (`op:par` channels), each modulator's Select names its own channels one by one and renames them back, members sorted into the take's channel order (Rename and rest are positional), one modulator per operator sharing Duration and Beats, all or none; same-name operators refused | done |
| 23ad Owner (2026-09-03): `TypeError: float() argument ... not 'NoneType'` on Harmonic Gain -- the expression was written before the modulator's Out CHOP had cooked, so the channel read None. `_bindPars` force-cooks it, binds what is there and re-tries the rest for up to eight frames, binding anyway on the last | done |
| 23ae Owner (2026-09-03): a settings popup for the optional recording parameters. Recording options sub-menu beside Record a gesture: play back, round to a division, seam and seam length, stop after; live ticks through `RecordChecks()`, autoClose 2 so it stays open | done |
| 23af Owner (2026-09-03): the CHOP modifier maps from a range TO a range like a Math CHOP. `Tolo`/`Tohi` on the modulator drive the `range` Math CHOP's torange (`Choptolo`/`Choptohi` defaults, a To page on the panel); 1..0 inverts, measured 0.25 -> 0.75 | done |
| 23ag Owner (2026-09-03): the hold-for-settings interaction reaches the recording, and a plain click's settings become a choice. `_holdable` covers the record item (hold opens Recording options, `_holdopened` swallows the release's select), `Holdpad` relabelled Hold Opens The Settings, and `Clicksettings` (A Plain Click Uses: last / shipped) routes every apply path through `_default`, with `_touched` letting a setting changed in this menu visit win | done |
| 23ah Owner (2026-09-03): the same click-or-hold UX for the channel route. A click on a Source CHOP channel applies through `ApplyChop` with the settings as they stand; a hold opens the staged panel (`_holdable` now an instance method, reading `_chopItems`); with Hold Opens The Settings off a click still opens the panel, the only way left to reach it | done |
| 23ai Measured while verifying 23ah: an extension reinit forgets `_panel` and orphans the staged copy plus the open window -- 33 cooking operators that had already shipped in one tox. `__init__` schedules `_sweepStaging` (drops the staging and closes the window when no session owns them) and `pre_release` strips a staging at ship time | done |
| 23aj Owner (2026-09-03) asked where the record hotkey is: it existed as `alt.shift.r`, but FNS_HotkeyManager's ComputeConflicts shows that combo belongs to ParRandomizer's `Shortcutop` -- both fire. Moved to `ctrl.alt.r` (free, and it matches `ctrl.alt.g` for the menu). The owner's own `Shortcuttap` = `alt.r` collides with ParRandomizer's `Shortcutpar` the same way; `alt.t`, its shipped default, is free | done |
| 23ak Owner (2026-09-03): a manager panel -- list the deployed modulators and their targets, tag them so they survive a restart, navigate to them, open the modulator's or the target's parameters, plus tempo/Tap and the division, and the source CHOP for channel modulators. `manager` (lister cloned from /sys/TDTox/lister + colDefine + per-column callbacks), `table_mods` rewritten by `ManagerRefresh`, tag `fns_beatmod` applied at spawn and back-filled by `Modulators()`, `Openmanager` par + command, Blend cell mutes | done |
| 23al Owner (2026-09-03) took all three offers: live auto-refresh while the manager is open (a 500 ms tick that only writes when the rows actually changed), a Status column plus Sweep for orphaned modulators (target gone, or no member still reads them -- 2 of the 20 live ones), and double-click to reopen the surface that made a modulator (CHOP panel, parameters, or the XY pad in a new sticky mode that applies on the next click) | done |
| 23am Owner (2026-09-03): document all of it, for the web docs. `packaging/docs/FNS_BeatMod.md` rewritten as nine `##` feature sections with matching anchors (the house convention: no underscores, no package prefix in the first heading), a Click or hold section that states the shared gesture model once instead of three times, and the sentence A Plain Click Uses had been spliced into repaired. catalog.json blurb now names all three modulator kinds and the manager. BeatModDesign decisions reordered 1..35 (10 and 12 had been stranded at the end by repeated insertion), Surface rewritten from the live tool, and Not-in-this-version no longer lists three things that shipped. Release trap recorded in DocsEvidenceDerivation: the manifest reads the LIVE hotkey, so this project's `alt.r` tap remap would ship as the documented key | done |
| 23an Owner (2026-09-03): the manager should register to FNS_Hub. `FNS_HubRegistry` host stamped (canonical `BeatMod`, content the `manager` panel, label without a space, order 60), `Promotepars` set True afterwards because `StampHost` leaves it False even when asked (the documented trap), panel `w`/`h` bound to the hub's tabs container with the standalone size as fallback, and `OnHubExposure` on the tool's extension driving the live tick, which had keyed off a window that is never open in the hub Read-back note: loading the released tox registers the SAME canonical from the copy, and destroying it takes the live tool's tab with it -- re-register the host and `SetTabDisplayed(name, True)` after a read-back, the way the opshortcut is re-asserted. | done |
| 23ao Owner (2026-09-04): FNS_Keyframer, a sub-tool of FNS_TimelineTools -- reference operators (a sequence block each) with include/exclude patterns, key their parameters into an Animation COMP at its own current frame, a Key Function menu, a Drive toggle that wires the parameters to the animation's out and releases them to constants, Exclude Pages with `Common About Info Version` shipped. Six Animation COMP facts measured and written into KeyframerContract (an uncooked channel takes no key; deleteKeyframe(0) wipes the channel; dots are dropped from channel names; the COMP is not subscriptable; a bound pulse does not propagate; out is stale within the frame) | done |
| 23ap Owner (2026-09-04): driving from an Animation COMP is normally a CHOP export, make it the default and keep the other optional. Drive Method menu (export / expression); export builds a tagged Null + DAT Table by Name beside the animation and sets the flag; off reads values before the flag drops because an ended export reverts to the PRE-export constant (measured), then destroys the rig. `export` is a CHOP flag, not a par: `n.par.export = True` does nothing silently | done |
| 23aq Owner (2026-09-04): the keyframer should get its own buttons in the Animation editor's graph heading, like the other TimelineTools blocks. `FNS_Keyframer/ui_row` (KF label, KEY, UNKEY, DRIVE; copies of the Animation block's widgets), published through `FNS_TimelineRegistry.RegisterWidget(zone='graphheading', order=10)` from the extension on the 90-frame delay, `ui_click` routing releases, DRIVE bound through the child's Drive to the host's, `Controls In Animation Editor` to withdraw it. Pressed on the mirror in /ui with interactMouse and read back. Paid for: the source label is display-off (the copy took no flow room, KEY landed on UNKEY); the film toggle's text is a constant icon codepoint; in-frame hit-testing is stale after a layout change; dark captures hide glyphs. TimelineToolsContract's in-UI section had drifted (it still said `options`); corrected | done |
| 23ar Owner (2026-09-04): the strip needs a drop target ("that's the most important"), for full operators, single parameters or pargroups, and a click to open the keyframer's settings. KF is a button: click opens the host's parameter dialog; the row takes drops through its own `drop_callbacks` (PI file-bound), which the registry copies onto the mirror. `AcceptsDrop`/`HandleDrop` on the extension: an operator becomes a block on `*`, a parameter or pargroup a block for its owner listing those names (merged into an existing block; `*` covers), an Animation COMP sets Animation, a curveless parameter is reported. Tested through the handlers, not a mouse | done |
| 23as Owner (2026-09-04): an Animation COMP has many operator targets; Drive must not stop at the referenced operator. `SetDrive` now walks the animation's channels table: every `operator:parameter` channel whose operator resolves (the map the tool stores ON the animation when it keys, then a sibling by name, then the one project-wide match) is wired; unresolved channels are counted and reported. Remove Keys At Frame stays with the references | done |
| 23at Owner (2026-09-04): a drop should already add the entry to the editor's channel list, without keyframes. `HandleDrop` gives every dropped parameter a channel in the animation at once (default = the parameter's value; an operator dropped whole gets one per parameter its block lets through), settles the animation and remembers the prefix map. Keyframe's fresh channels carry the keyed value as default too | done |
| 23au Owner (2026-09-04): the strip can land in different Animation COMP editors, so every interaction must update the animation reference. `EditorAnimation()` reads the dialog's `local/variables` KEYPATH (owner's correction the same day: the pane's owner is not guaranteed, measured `/` with `/animation3` open; the owner is the fallback), `SyncAnimation()` re-points Animation, run first by every strip action (drop, KEY, UNKEY, KF, and DRIVE when its value changes under the mouse). Found on the way and fixed: switching Animation while driving undid the rig on the NEW animation and left the old one exporting; Drive now remembers the animation it wired (`kf_driven_anim`) and off undoes that one | done |
| 23av PI listed copies as suspects (2026-09-04): `copy()` carries the `pi_suspect` tag and the file binding, so every deployed BeatMod modulator's `ModulatorExt`, the owner's scratch host copies and PI's own FNS_About ExtUtils were table rows, 38 of project state, churning `suspects.tsv`. PI's `Scan`/`ReinitSuspects` now skip a stray copy (no suspect COMP above it, another tagged DAT on the same file); sole holders and in-package clones unchanged; 518 -> 480 rows, verified stable across a PI save of the root with modulators deployed. BeatMod's spawns strip the tracking tags from copies (`_untrack`). PI's Save never wrote DAT files (syncfile does), so the "stale copy overwrites the master" fear was misplaced; the real one was `ReinitSuspects` re-binding copies to new files. Recorded in ExternalizationOwnership | done |
| 23aw Owner (2026-09-04): channels deleted from the editor's list came back on the next key, because Keyframe created a channel for every referenced parameter. The tool now remembers the channels it created on the animation (`kf_channels`); a referenced parameter whose channel it made once and is gone now is left out and counted in Status; a drop re-adds explicitly | done |
| 23ax Owner (2026-09-04): KEY should only consider the channels already in the list; the References may be obsolete as the main interface, the strip and the editor's own data are it; keep the extension's public interface. Done: `Keyframe`/`RemoveKeys` act on the channel list, on the picked channels when any are picked (the `picked` column is the editor's selection, measured in the dialog's DATs), else all, and create nothing; drops add channels only (no reference block); the References feed a new `Add Channels From References` pulse (`AddChannels()`), a bulk add without keys; the `kf_channels` memory from 23aw retired; UNKEY at frame 0 removes the row by hand (fact 3). API names kept, `Keyframe`/`RemoveKeys` gained `channels=None` | done |
| 23ay Owner (2026-09-04): "will want to do a random sample hold speed modulator too". Reading: the Speed kind (a Speed CHOP integrating one constant rate, decision 10) with the rate re-drawn at random every beat division and held, the parameter still running and ping-ponging in its range; a smooth variant glides between rates. Sketch: a `Speedshape` menu on the modulator (constant / random step / random smooth) feeding the rate stage from the same phase as the `random` waves, scaled by Speedrate, with a direction option (always forward / random sign); menu item under Speed, pad unchanged, manager Detail says `random rate`. Answered (owner): random sign by default; seed shared by default with the per-member option; the range question answered by decision 10 (Speed counts on from the current value, the range only sets how far a division travels). Built: `rate_shape` Expression CHOP in the template between `rate` and both Speed CHOPs, `Speedshape` + `Speedbipolar` on the modulator, *Random speed* menu item (`speedrandom` kind through Apply, Modify and the pad), tool defaults `Speedbipolar` and `Speedrandomlink`, manager Detail `random rate`; decision 37 | done |
| 23az Owner (2026-09-07): a random speed in discrete time, a random number added each beat; the Count CHOP's third input (increment value) is the answer. Built as the shape `randomstep` and the menu kind *Random jumps*: `step_draw` draws the amount, `count_step`/`count_step_b` Count CHOPs triggered by the ramp's wrap add it per division, the wave switches take them as a fourth input, crossfades reset the count. Same seeds as the pace, so a modulator switched between the two keeps its dice; decision 38 | done |
| 23ba Owner (2026-09-07): on macOS the held button does not track into the pad's window; make holding optional as a custom par, a normal click applies. `Padsticky` (Pad Stays Open, off by default): the hold opens the pad sticky, the release is ignored, a click applies, Escape applies nothing; the sticky mode already existed for the manager's double-click. Decision 39 | done |
| 23bb Owner (2026-09-08): `Configscope` on FNS_ConfigRegistry is not guarded against `op.FNS` missing, which breaks standalone tool releases. Every follower (master, /sys global, six stamped hosts) converted from a bind on `op.FNS.par.Configscope` to the guarded expression `... if hasattr(op, 'FNS') else 'project'`. Measured first: a dangling bind evaluates to '' silently (no exception, so the documented fallback never ran), a guarded BIND does the same because its else branch is not a parameter, the guarded EXPRESSION reads `project` without the root. ConfigScope.md, the skill and the docstring corrected. Follow-up the same day (owner: "I thought more tools would be affected since all of them carry the configregistry"): 46 hosts, 40 without the par at all (stamped before it existed; cloning forces children, never a COMP's own pars), reading GLOBAL standalone; all 40 given the guarded par, help text refreshed everywhere, 46 tool toxes and the root saved | done |
| 23bc Owner (2026-09-08): "can we make sure such mistakes don't happen in the future?" Two mistakes, two rails. Saves: `PrivateInvestigator.DirtySuspects()` / `SaveDirty()` save every dirty suspect COMP leaves-first and report what is still dirty; CLAUDE.md makes it the step before any commit carrying toxes. Hosts: `ConfigRegistryExt._ensureScopePar()` heals the Configscope invariant on every init (add when missing, rewrite a bind or an unguarded expression, never a constant) and `ScopeAudit()` reports drift over the root's tree and /sys; `tests/test_root_shortcut_guards.py` fails on any bare `op.FNS` in the sources (docstrings and try blocks excepted). CLAUDE.md: a fix meant for every host goes into the master plus an init heal, never a hand sweep. Observed, not yet explained: TD deadlocked (0 CPU, not responding, no dialog) in a call that pushed the master's new ext text into the /sys ConfigRegistry global and pulsed its reinit for the second time in a session, then went on to SaveDirty; the first push-and-reinit had returned fine. restart_td recovered it; the hosts healed themselves at boot and nothing was lost. Until understood, do not reinit the /sys global by hand: re-save the master tox and let the next boot promote it | done |
| 23g Save, commit, release through PI with a cooking-enabled read-back | done -- `modules/release/FNS_BeatMod.tox` (154,478 bytes) loaded once cooking-enabled at the project root: 86 ops, 0 annotations, no PI tags, no clone links, no file bindings, Pkgversion 0.1.0, 0 errors and no script errors after 912 frames, the live registry rows untouched; copy destroyed |

**Paid for.** (1) The Expression CHOP's formula pars take the code as an
EXPRESSION, not a value. (2) A Pattern CHOP's wave type is `wavetype`. (3) The
Lookup CHOP emits one channel per channel of its TABLE, so the pattern must
carry one channel per member for a group. (4) A base COMP is not
subscriptable: the parameter expression must reference the modulator's Out
CHOP. (5) `geo.parGroup.t`, not `geo.par.t`. (6) Creating a keyboardin DAT
from Python auto-creates its callbacks DAT. (7) A parfield method with the
same name as a par shadows it: the API is Apply/Release, the pulses Modulate/
Remove. (8) A target nothing cooks does not pull its modulator, so readings
between reads look frozen; a rendered or displayed target pulls every frame.

## 24. ConfigRegistry — the roaming file carries a schema beside each value  `[FEATURE]` — DONE

Asked from the launcher side (TDXLPP, 2026-09-10), with the owner's preference
stated: **the config JSON should carry each par's label and style, not only
its name.**

**What is true today.** Every `pars` entry in `FNStools_config.json` is exactly
`mode / val / expr / bindExpr / eval` — measured across all 60 sections on this
machine, the union of entry keys is those five. No `label`, `help`, `style`,
`page`, `menuNames`/`menuLabels`, `min`/`max`. So any consumer editing the file
with no session running can only render by guessing from the value's type
(bool → checkbox, number → number, else text) and can only search on the par's
NAME. The launcher's offline editor is exactly that today, and it says so in
its header.

**What the live surface already has.** `UiState()` → `_describePars` emits all
of it (label, page, style, order, help, menus, ranges) — the console page and
the launcher both render real controls and search label + name + help from it.
The gap is only the file.

**The ask.** Persist the schema fields beside the value in each `pars` entry
(`label`, `style`, `page`, `help`, `menuNames`, `menuLabels`, `min`, `max`;
`order` too). They are written by the same `_snapshotPars` walk that already
has the Par in hand, so the cost is bytes, not a second pass. The launcher's
offline editor would then render the same controls as live and search the same
fields — and every other file-side consumer (a diff, a hand edit, a future
config CMS) gets a readable document instead of a bare value map.

**Both questions are now decided (2026-09-10), and neither is open again
without a reason written here.**

1. **IN the file, not a sibling** — the owner's preference, and the measurement
   backs it. `_applyPars` reads exactly `mode`, `expr`, `bindExpr`, `val` and
   `eval` from a record and ignores every other key, and it is the ONLY reader
   of a file par record anywhere in the repo (the other `pars` hits are the
   live parGroup structure, not the file). So schema fields are inert for every
   existing reader. The decisive argument is not size but staleness: sections
   are REPLACED whole on save, so schema written by the same `_snapshotPars`
   walk can never drift out of step with the values beside it, whereas a
   sibling file is a second write with its own failure mode — exactly the drift
   rule 2 is meant to prevent. Cost, measured on this machine: the file is
   101,941 bytes over 60 sections and 825 pars, and a schema block averages 192
   bytes per par (max 333), so it grows to roughly 260 KB. That is a document a
   person can still open.
2. **A stale schema is cosmetic; a stale value is not.** Labels, help and menu
   labels drift when a tool updates, and that is harmless: every consumer reads
   values as the truth and schema as presentation. Nobody may "fix" a label
   mismatch by writing the roaming file — the tool's own parameter is the
   authority, and the next save corrects the file for free.

**One correction to the spec, for whoever builds it.** The fields cannot be
lifted from `_describePars` verbatim: that walk is per parGROUP (one entry per
group, components under `pars`) while `_snapshotPars` is per PAR, and it also
filters `UI_SKIP_PAGES`, which the snapshot does not. So the schema block must
be read off the Par in hand, taking `label`/`menuNames`/`menuLabels` from the
group's first par for a component, and `min`/`max` only where `clampMin`/
`clampMax` are set on an Int or Float, as `_describePars` already does. Expect
the file to describe some pars the live settings page hides.

**Not asked for:** per-tool scope (§6 of ScopeAndPersistence.md stands), or any
change to `_applyPars`. Values-in, values-out is unchanged.

**Built 2026-09-10** (owner: no official release yet, so the file shape is still
ours to change, and "a label name is a fair ask"). `_parSchema(p)` returns the
presentation block and `_snapshotPars` folds it into each record with
`setdefault`, never `update`, so a value key always wins if a schema field is
ever named like one. `_applyPars` is untouched.

| Verified live | Result |
|---|---|
| An Int par with `clampMin` on and `clampMax` off | `min: 0.0` emitted, `max` omitted — the unclamped `max` reads 1.0 beside a slider range of 10 and would have drawn a control that lies |
| A Menu par | `menuNames` + `menuLabels` + `help` emitted |
| A record carrying `label`, `style` and `min` fed to `_applyPars` | value applied (7), and label/style/min on the live par unchanged — the schema is inert on the way back in |
| Whole-file cost, 47 registered tools, 649 pars | pars blocks 44,834 -> 226,897 bytes, 281 bytes per par; the file goes from 101,941 bytes to about 284,000 |

That size is 5x the pars payload, not the 260 KB estimated before measuring;
`help` is most of it and the launcher searches on `help`, so it stays.

**`SCHEMA` stays 1, deliberately.** The gate is an exact match that RETIRES a
mismatched file to a `.bak` and refuses to load it, so a bump for an additive
change that breaks no reader would discard every settings file in the field.
The class comment already said "bump only on breaking shape changes".

**Found while testing: a readOnly par never roamed.** `FNS_BackupCleaner`'s
`Regex Pattern` was authored `readOnly`, and `_snapshotPars` skips readOnly
pars, so the setting silently stayed project-local while `Keep Last` beside it
roamed. Cleared, and it snapshots now. Worth a sweep: any tool with a
user-facing par marked readOnly is not persisting it.

**Two things about the rollout.** (1) The roaming file gains schema at the NEXT
BOOT, not now: `op.FNS_CONFIGREGISTRY` is the `/sys` global, which runs a COPY
of the ext DAT with no file sync, and the standing rule after the 2026-09-08
deadlock is to re-save the master and let the next boot promote it rather than
push text into the global by hand. (2) The edit dirtied 45 suspects, and they
were deliberately NOT mass-saved: every host's `ConfigRegistryExt` DAT is itself
`syncfile`-bound to the same `.py` this commit carries (verified on a host: same
file, `syncfile` on, new text already present), so the code reaches every host at
boot from the file, the tox text is re-derived, and writing 45 toxes while three
other sessions were live would have embedded their in-flight state for no gain.

**Launcher side, already landed (TDXLPP, 2026-09-10):** the settings tab now
reads `scope` from `UiState` and shows it as a badge with the right sentence
for each; flips it through `/api/scope` with your push/adopt choice presented
inline instead of a popup; searches live settings on tool name/label + par
label/name/help/page/menu labels (the console's fields, plus two the wire
carries); and, before an OFFLINE write, probes every live session's scope and
warns when a global-scope project is open, since its next save replaces the
sections wholesale. Only the offline editor waits on this item.


---

## 25 — FNS_BackupCleaner: TDBackupCleaner adopted, 2026-09-10

Owner's direction: "new tool: FNS_BackupCleaner --- from /FNSTools/TDBackupCleaner
--- this is a base-gated tool that should register to the hub. add it to private
investigator, CMS, all that." The tool already sat under the toolkit root as a
foreign shape: its own name, no PI row, an `externaltox` pointing at
`modules/suspects/project1/TDBackupCleaner.tox`, a file that does not exist.

| Step | State |
|---|---|
| 25a Renamed to `FNS_BackupCleaner`: parent shortcut `BackupCleaner`, ext DAT + class `BackupCleanerExt`, the 7 widget and About binds re-pointed, the treeLister callbacks re-pointed, header label. No reference to the old name survives anywhere in the subtree | done |
| 25b PI adoption per operator (`Add`, never `Scan`): the COMP, `BackupCleanerExt`, and `treeListerConfig/callbacks` -- three suspect rows, `externaltox` recomputed to `modules/suspects/FNSTools/FNS_BackupCleaner.tox` and normalized to forward slashes, the two DATs bound under `modules/suspects/FNSTools/FNS_BackupCleaner/` | done |
| 25c Version identity: `FNS_About` gains `Pkgversion` 0.1.0 (authoritative) and `Touchbuild` 2025.33070; its empty legacy `Version` par destroyed; the tool's About page mirrors by EXPRESSION, read-only, never a bind (a bind writes back through the mirror and rewrites the authority) | done |
| 25d Hub host stamped (canonical `BackupCleaner`, tab order 70, panel kind = the tool itself) and config host stamped (canonical `FNS_BackupCleaner`, `Excludepars = Root Scan Clean`). Tool sized by expression to the hub's tab area with an 800x600 fallback, since a mirrored root panel has no panel parent | done |
| 25e Catalog row (Workflow, tier 8323905 through `gate_package.py`, which wrote the Worker grant too -- a `wrangler deploy` is still owed), user-facing doc, release-notes line, site build 59 package pages exit 0 | done |

**Three defects the adoption would have amplified, fixed here.**

1. `__init__` ran a full `os.walk` of the project folder. An extension
   reinitializes on every source save and on project open, so the tool paid a
   whole-tree disk walk at every boot. Scanning is now demand-driven:
   `OnHubExposure(exposed)` (the hub contract's own hook) scans when the tab is
   shown, and the Scan pulse scans by hand.
2. `onParRoot` popped a `ui.messageBox` summary. That fires on a plain value
   change, and a config host applies stored values at load -- registering this
   tool for config would have put a blocking modal into the boot. The summary is
   now the Scan pulse's alone, `Root` is excluded from the roaming snapshot
   anyway (a path on one machine), and both scan callbacks no-op until a scan
   has actually happened.
3. A stock widget's `Slider0` pointed at a `./slider0` child deleted long ago,
   warning on every cook.

**Paid for.** (1) `StampHost` copies the master's own `Promotepars`, which is
False, so a fresh host promotes nothing; setting it True is not enough either --
the promotion runs on the value CHANGE and on registration, so a stamp made
before the host's extension is live needs `_ensureToolRegistryPage()` called
once afterwards. Verify on the TOOL (`Registry` page carries `Cf*` AND `Hb*`),
never on the host, which reports "Registered" for a half-applied stamp.
(2) **An OP-reference parameter value on a COMP resolves SIBLING-relative, not
child-relative.** A sweep that cleared "unresolvable" DAT references using
`o.op(value)` wiped 141 live wires -- the tree lister's input table, its
callbacks DAT, every widget look callback -- with no error, because a cleared
reference is silently valid. Recovered exactly by diffing every DAT-style
parameter against the tox PI had already written and copying the values back
(845 compared, 0 differences afterwards). The lesson is the tox: PI's `Add`
writes one before any of the risky work, and that file is the restore point.
(3) **A release read-back belongs under `/sys`, never at the network root.** The
artifact's registry hosts are live: loaded at `/`, this one registered itself
under canonical `BackupCleaner` and, when the probe was destroyed, took the real
tool's hub entry with it, leaving the hub's mirror pointing at a dead operator.
`RegistryBase` suppresses registration under `/sys` and `/ui` (`_isUnderSysOrUi`),
which is why the TimelineTools read-back used `/sys/quiet`. Recovered by pulsing
the tool's `Hbregister`; the check afterwards is the registry's own entry list,
not the host's `Regstatus`, which stayed "Registered" throughout.

---

## 26 — FNS_GlobalOutSelect: the Refresh path, 2026-09-10

Owner: "FNS_GlobalOutSelect needs some love and optimization especially in
treePanel/fastOpFind". Measured before touching anything, pulse-first, because
these finders are `activecook off` with the scan bound to the Refresh pulse and
a force-cook without a pulse only re-serves the cached table in 0.03 ms.

| Measured | Before | After |
|---|---|---|
| One Refresh (pulse, then cook the tree input and the lister) | ~130 ms, 225 operators cooked | ~33 ms, 13 operators cooked |
| Full-project scans per Refresh (28,306 ops) | 2, at ~33 ms each | 1 |
| Operators in the package | 707 | 445 |
| Rows the tree receives | 54 | 54, identical apart from `recursiveChildren` counts |

**What it was.** `fastOpFind/opfindComponent` scans `/` for every COMP with a
global shortcut. `fastOpFind/out_ops` held a second, identical finder whose only
job was to be a replicator template: one `yeaN` COMP per shortcut, each with its
own OP Find (52 finders, 208 operators) looking for `out*` children, to locate
in this project exactly one operator (`FNS_QuickTime/out_time`). Around them, a
shelf of dead DATs from an earlier design: `execute1` and `parexec1` pulsed a
`replicator_expanded` that no longer exists (so changing Limit Max Depth or Max
Depth raised on every change), `execute2` cleared a `table_outs` that no longer
exists, `datexec2`/`evalExpanded`/`eval_expandedPaths`/`table_expandedLen`/
`eval_expandedPathsxxx`/`depthTest`/`datexec3`/`opfindBrowser_callbacks` fed
nothing. The finder's `limitmaxdepth` was a constant False, so its `maxdepth`
expression (with a `mod.depthTest` branch for a digits case that never occurs)
was inert and the panel's depth pars did nothing.

**What it is.** One native finder, its `limitmaxdepth`/`maxdepth` now following
the panel's pars; `script_outs`, a Script DAT fed by `select_opfindComponent`,
walks the children of each listed COMP for `out*` types and emits rows in the
finder's own eight-column shape so `merge1` joins them by name (0.6 ms for 52
shortcuts). Everything else in the chain (`sort2`, `reorder1`, `substitute1`,
`select1`, `merge1`, `script1`, `sort1`, `out1`) is unchanged: it relabels rows
by shortcut name, deduplicates and sorts. The `Clickableheader` enable
expression referenced `me.par.Header`, which lives on the lister, and warned on
every cook; it now reads the lister's par.

**Ruled out by measurement, so nobody re-tries them.** The `recursiveChildren`
column and the wire-path columns cost nothing measurable. The finder's callback
DAT defines an `onFindOPGetInclude` that always returns True, a Python call per
operator visited: removing it changed nothing (34-37 ms with, 32-37 without).
A pure-Python `findChildren(type=COMP, parName='opshortcut',
onlyNonDefaults=True)` over the same tree is SLOWER (48-60 ms), and `dir(op)`
exposes no shortcut registry, so the 33 ms is the native traversal and is the
floor for a whole-project scan. The Namefilter on the panel reads `^tweener`
(case-sensitive, so it excludes nothing today); left as found.

**Left alone.** `treePanel/opfindAll`'s callbacks expression names an
`opfindBrowser_callbacks` sibling that does not exist in `treePanel` (the
Lambdafilterkey feature is dead either way); `Includeresultparents` and the
`Except` parameter chain (`parameter2`, `convert1`, `null1`, `script_except`)
reference a `parent.MAIN.par.Except` the tool no longer has. Both are inert.

**Follow-up the same day.** Owner: "let's add a proper refresh button". The
tool's top row is now `topbar` (horizlr, 25 px): the existing header widget
filling, and `btn_refresh`, a copy of FNS_BackupCleaner's `Scan` widget with
its value bound to `parent.MAIN.par.Refresh`, so the two tools look alike and
the button is one bind, no code. The header label no longer says "Refresh
Manually" and no longer carries a hand-typed version. Verified by a click
through the hub mirror (the tool itself has no active panel; the Select does):
the finder cooked once more.

**And a defect in FNS_BackupCleaner found from the same complaint** ("the UI
seems messed up, I needed to uncook and recook"): its extension wrote a
placeholder table on init whose header named different columns than a scan
writes (`Time Spent, Count` against `Count, Work Hrs`), and the tree lister
lays its columns out from those names. Before item 25 a scan always overwrote
the placeholder at once; after it, any extension reinit (a project save is
one) left an already-open tab on the mismatched placeholder with no exposure
event to rescan. Now the placeholder carries the scan's header, and the COMP
stores the FRAME of its last scan (storage survives a reinit): a marker at or
below the current frame is this session's and triggers a deferred rescan; a
project open restarts the frame count, so a marker from an earlier run is
larger than the clock and never fires, and a cold boot stays free. A new
`pre_release` hook unstores the marker and resets `table_list` to the
placeholder on the staged copy, so an artifact never ships the author's
backup listing (948 rows of it were in the tox) or scans on install. Verified:
a stale marker leaves the placeholder alone, a scan followed by a reinit
refills within a second, no errors.

---

## 27 — FNS_Remote: the toolbar button, 2026-09-10

Owner: "I'd like the FNS_Remote to install a button to the toolbar, and when
dragging an operator onto it to be the component. when holding alt and
dragging onto it to add to the component list. add a hover tooltip and update
documentation. icon should be material design icons mobile phone icon".

| Step | State |
|---|---|
| 27a `button_remote`: a copy of FNS_ParOPDrop's `button_ParOpPlace`, the toolkit's proven 30x19 drop-target button (Drag/Drop = callbacks, a `help` DAT the panel's `helpdat` points at for the rollover tooltip, `text` child in Material Design Icons). Glyph `chr(0xF011C)`, mdi-cellphone. Its dead `execute1` (connects to an `emptypanel` that does not exist) and the ParGroup-promote `dragdrop1` were not copied along | done |
| 27b `FNSRemoteExt.ExposeComponent(comp, append=False)`: block 0 replaced, or a block appended; an already-listed COMP is enabled instead of listed twice; an empty shipped first block is filled rather than skipped; non-COMPs refused with a result dict, never an exception | done |
| 27c `dragdrop` callbacks: accept when any drag item is a COMP or a parameter of one; the modifier is `comp.panel.alt` read off the panel under the cursor, which is the bar MIRROR (`_mirrorDragDrop` copies the callback settings onto it); several COMPs in one plain drop set the first and add the rest | done |
| 27d Click opens the pairing page (`OpenPairing`, which starts serving if needed); the button state follows the `Active` par through its parexec, so it lights while serving. FNS_Remote gained the `Remote` parent shortcut the callbacks resolve through | done |
| 27e `FNS_ToolbarRegistry` host stamped (canonical `Remote`, `Comp = button_remote`, `Promotepars` on afterwards); `tbmirror_Remote` in the bookmark bar with Drop = callbacks pointing at the button's DAT; the widget's `Url` par is the docs page, which the entry's `help_url` derives from | done |
| 27f Doc page section, release note, this row | done |

Verified live: through the callback DAT, a plain drop of `/project1` set block
0; `ExposeComponent(/Embody, append=True)` added block 1; the same call again
returned `already`; `ExposeComponent(/FNSTools)` replaced block 0; a parameter
drag exposed its owner; a DAT was refused; hover accepts a COMP and refuses a
DAT. The tool's Control sequence was restored to its shipped state afterwards.
The Alt path itself cannot be driven from a script (a real drag with a held
key); it reads the same panel value every TD panel exposes.

**Follow-up the same evening: "shouldn't the pair a phone screen show a QR
code?" and "we really just need a qr code shown".** Two facts settled it. The
browser pairing page draws a QR only when LAN access is on, and the owner's
remote served loopback only, so the page showed the "allow LAN" note and no
code (a 127.0.0.1 code is useless to a phone). And TD bundles OpenCV, whose
`QRCodeDetector` decodes an image, so a code rendered inside TD can be proven
without any new package. `OpenPairing` (the par pulse, the toolbar click, the
Phone Remote command) now opens `qr_window`, a popup over `qr_panel`: title,
a Script TOP fed by `FNSRemoteExt.QrImage()`, the URL, a LAN toggle bound to
the `Lan` par, and a note. The browser route survives as `OpenPairingPage`.
`_qrMatrix` is a port of the page's inline encoder (byte mode, level L, mask
0). **Paid for:** both encoders treated every version as one Reed-Solomon
block, which is true only up to version 5 at level L; a version-6 symbol
decoded as garbage. Both are now bounded at version 5 (104 bytes; a pairing
URL is about 60) and refuse beyond it. Verified: 20 of 20 realistic random-
token URLs decode with OpenCV; the live Script TOP read back and decoded to
the remote's own URL with LAN on for the test, then LAN restored.

**Same evening, four more from the owner** (a screenshot of the popup, then
"misaligned / website served: first tab control, second touch, third session /
make sure pargroups get collapsible individual par sliders too under the
combo / make sure sliders are draggable"). The popup's fixed-width children
sat at the left of a `verttb` container; `justifyh = center` on the panel is
the whole fix. The served page now opens on Control, then Touch, then
Session. `ControlSchema` marks a component of a multi-par group with
`group`/`groupLabel`/`groupSize` and marks the numeric styles (Float, Int, XY,
XYZ, XYZW, UV, UVW, WH, RGB, RGBA) with `numeric` plus the norm range, since
an XYZ component's style is `XYZW`, not `Float`, and was falling to a text
box; the page folds a group into one header row (label, combined readout,
chevron) with one slider per component underneath, labelled by what the
component adds to the group name (Posx -> X). Sliders get `touch-action:
none`, a 44 px hit height and a 28 px thumb, which is what stops a phone
treating the drag as a scroll. Verified in the browser pane under mobile
emulation against a scratch COMP with Float/Int/Toggle/Menu/XYZ/RGB/Pulse:
Control first and shown, a slider push reached TD (Amount 1.5), a component
slider reached TD and updated the group readout (Posx 0.7, "0.7 0 0"), kids
labelled X Y Z and R G B, computed touch-action none. A real finger drag is the
owner's to try; the pane cannot render a drag while hidden.

**"FNS_Remote missing extutils minimal and also commands."** True on both
counts. The tool had no ExtUtils at all, so the ExtUtils distributor's survey
could not even see it, and its four commands lived on a legacy `FnsCommands()`
spec list handed to `Register` from a deferred `_announce`; the registry held
148 commands and none from Remote. Now: `ExtUtils` is a copy of the slim
master (`FNS_CustomParTools/QuickExt/ExtUtilsMinimal`), clone-linked to it,
tagged `ExtUtils` + `tdn_exclude`, docked to `FNSRemoteExt`; the extension
imports `FNSCommand` through the dock (with the `parent().op('ExtUtils')`
first-compile fallback) and declares `OpenPairing` (id `remote`, state
`Active`, surfaces session + context-menu), `Info`, `Serve` and `Stop` (hidden)
with `@fns_command`, all under the `fns.mobile-control` capability, the ids
unchanged because the launcher keys on them; `AnnounceCommands()` calls
`FNSCommand.announce` fifty frames after init, the BeatMod pattern.

## 28 — A host loaded mid-session never autoregisters, 2026-09-11

Reported by the TDXLU launcher after re-importing two registry packages for
its companion release, and reproduced by them a second time on a second
package version: a freshly loaded host with `Autoregister` already ON does
not register until `Register` is pulsed. Their reimport guidance in
`packaging/launcher_mirror.json` already carries the pulse as a workaround,
observed 2026-09-08.

**Their diagnosis was half of it.** `onParAutoregister` firing on change only
is real: a host whose `Autoregister` is already on inside the tox never
changes that parameter, so nothing self-triggers. But the toolkit has a
compensating mechanism, and the actual defect is that the compensation is out
of reach by the time a mid-session load happens.

`RegistryBase._reapplyAutoregisterHosts()` finds live Autoregister hosts the
global has no entry for and asks them to republish. Reading it (line 1167):

- it runs only on the `/sys` global,
- it decrements `_boot_sweeps_left` from `BOOT_SWEEPS = 6` and returns once
  that reaches zero,
- the counter is an instance attribute, seeded once per extension init.

So the sweep is a BOOT window, by design, because it is a project-wide
`findChildren`. A host destroyed and re-loaded mid-session, which is exactly
what the launcher's reimport does, arrives long after those six healing ticks
are spent, and nothing asks it to publish. Nothing is broken at boot, which is
why this only ever shows up in a reimport.

It also explains why the failure looks intermittent and is not: any extension
reinit wave reseeds the counter, and `project.save()` triggers one. A load
followed by a save picks the host up. A load followed by a verification, which
is what the launcher does, does not.

**The fix, unbuilt:** a host should publish from its own init when
`Autoregister` is on, rather than depending on a global sweep that has a
deadline. Host-side covers the mid-session load that the boot window cannot,
and it removes the pulse from the launcher's reimport recipe.

**Recognising it, and the trap in testing the fix.** Both from the launcher's
second reproduction, confirmed here against `RegistryBase`.

The failure signature is `Regstatus` reading `Idle`, which
`_applyHostRegistration` writes when it declines (line 527), while the global's
entry still carries the DESTROYED host's `source_registry_id`. The stale id is
real and self-healing once something republishes: `_healRegistryEntries` rewrites
`source_registry` and `source_registry_id` whenever they disagree with the live
source (line 1142). So the pair is diagnostic, a host saying Idle beside a global
still pointing at a dead operator.

The trap is that `project.save()` MASKS this bug. The save triggers a reinit
wave, the wave reseeds `_boot_sweeps_left`, and the sweep then finds the host and
publishes it. So a fix verified with a save between the load and the check passes
whether or not the fix works. Item 28's acceptance test therefore has to be load,
then check, with no save in between, and it has to run at least seven healing
ticks after boot so the window is genuinely spent. Anything looser proves
nothing.

The same masking is a hazard for a recipe author, which is why the launcher's
runbook now pins its order. A sequence of load, save, verify registers with no
pulse, which invites the reader to conclude the pulse is decoration and drop it.
It is not decoration, it is the deterministic path, and the save side effect is
not something a release recipe should lean on.

**Blast radius is why it is a backlog item and not a patch.** `RegistryBase`
is the shared base under ten registries and every host stamped into a tool, so
this reaches roughly every package that carries one, and it wants the
`_ensure*`-on-init shape plus a real cold-boot test rather than a quick edit
landed the week of a release. Owner's call.

## 29 — ParentHierarchy draws a dead button beside iopBrowser's, 2026-09-11

Owner asked whether any work order mentions deduplicating the
ParentHierarchy and iopBrowser buttons. None did; this is that record.

**Measured live (2026-09-11).** Both `FNS_iopBrowser/nbwidget` and
`FNS_ParentHierarchy/nbwidget` are 21x21 registrants holding a displayed
`button` (19x19) inside a `buttonborder`, so a pane bar with both packages
installed shows two identical-looking buttons. iopBrowser's is real: its
`panelexec1` opens `FNS_IOPBROWSER/popMenu_bar` on press. ParentHierarchy's
has no press handler at all; its exec DATs are the hover chain
(`chopexec1`/`chopexec2` watching `panel2` over the path area), the hotkey
COMPs and the per-frame nugget updater. The button is a leftover of the
2026-09-09 split, when both widgets were cut from the same
`parent_hierarchy` shell. The package doc already states the intent:
"This tool adds no button to the pane bar. It reads the path that is
already there."

**Fix shape.** Make ParentHierarchy's widget buttonless: `button` and
`buttonborder` display off (or removed) and the widget's width 0, so the
hover chain keeps its per-pane copy without occupying a slot. The bars
hold copies, so unregister and re-register to re-copy, and verify on a
live `nbitem_ParentHierarchy` instance, never the master (brief
2026-09-09, item 28). Cold-boot check afterwards (NavbarColdBootCheck.md).
**Landed 2026-09-11 (owner: "go for it").** On the master `nbwidget`:
`button` and `buttonborder` display off, `w` from the bar-height
expression to a constant 0. Re-copied into the bars through the host's
own `Unregister` then `Autoregister = 1` (the `Nb*` names are the tool
page's promotions; the host carries them unprefixed, and the write-through
cleared the intent once before it stuck, exactly item 27 of the split
brief). Verified on the live copies in `pane1`, `pane2` and
`panebar_default`: width 0, no button, no border, the hover chain's
`panel2` carrying its 5 channels, no errors; `nbitem_iopBrowser` still 21
wide with its button. The master's own `panel2` path warning is the
permanent master-only warning the split brief recorded. Pkgversion
bumped and the suspect PI-saved. Owed: a hand test of the Alt-hover in a
bar (the chain was not touched, only the visuals) and the cold-boot check.

## 30 — IOP promotion to the root, and the path-bar drop that was dead, 2026-09-11

Owner: adding an IOP shortcut to `/` is possible in TouchDesigner but the
tool refused it when an operator was dropped with Ctrl+Alt on the path
bar. Measured live, two defects under one symptom:

1. **The root was never a drop target by design.** `GetDropPath` took
   ParentHierarchy's `ParentCompList`, whose `GetInfo` stops at
   `op('/')`, and halved the cell id over that root-less chain. TD's path
   bar lays its cells out as `0 "/"  1 name  2 "/"  3 name ... ">>"`, so
   the root cell mapped onto the first child, and in a pane at root the
   chain was empty and the index raised. That is the "not permitted".
2. **The whole route was dead since the 2026-09-09 split.**
   `ExtHijackDragdrop.delegate_comp` reached for `nbitem_ParentHierarchy`
   in the same bar, the breadcrumb COPY, which carries no extension since
   the singleton split, so `GetInfo()` raised `AttributeError` on every
   drop, at every target.

**Fix (landed).** `GetDropPath` builds the chain itself from this bar's
own `../panenav/out1` path, root included, and maps `(idx + 1) // 2`
onto the top-down chain, returning None for the `>>` overflow cell; the
drop callback returns early on a None target. No dependency on
ParentHierarchy remains (CustomParTools must not require an optional
package). The IOP promoter itself needed nothing: a headless write onto
`/` through `OnSelect` landed and was cleaned up. Re-copied into the bars
through the host's Unregister then Autoregister; verified on the live
copies in pane1 (root: cell 0 -> `/`), pane2 (`/FNSTools/FNS_PreviewPanel`:
0 -> `/`, 1 and 2 -> `/FNSTools`, 3 and 4 -> the panel, 5+ -> None) and
`panebar_default`, no errors. CustomParTools Pkgversion bumped, the
package PI-saved (hijack_dragdrop is carried by its parent's tox). The
doc now says the root cell counts as a parent. Owed: a hand test of the
actual Ctrl+Alt drop (the modifier state cannot be simulated), and a
cold-boot check.

**Addendum, same day: the iopBrowser icon.** The owner's actual gesture
was a drop on the iopBrowser BUTTON, which was never a promotion route:
its drop mode was `dropparent`, so the drop bubbled up the bar into TD's
legacy `/sys/drop` and did nothing. The widget master now carries a
`dragdrop` callbacks DAT (button and border on `usecallbacks`, sibling-
relative reference): an operator dropped on the icon becomes an IOP of
the network the pane is in, root included, through CustomParTools'
promoter (its name dialog) when that package and module are present, or
written straight into the parent's `iop` sequence under the operator's
own name without it. Parameters are refused at hover. Verified on the
live copies in all three bars (callbacks resolve per copy, accept OP /
reject Par, promoter found, headless write onto `/` landed and was
cleaned up), no errors. iopBrowser Pkgversion bumped, suspect PI-saved.

## 31 — Fuzzy search: one tiered matcher for the palette search, the command palette and the launcher, 2026-09-11

Owner asked how good the fuzzy search is in FNS_SearchPalette and
FNS_CommandPalette and whether it can improve without losing accuracy.
Measured first, over the 1406 live palette names and the 118 command rows:

- **SearchPalette** is accurate and has no typo tolerance at all: `nosie`
  lists DRAGON_COMPOSITE (a subsequence), `fedback` lists
  displaced_feedback, `kinnect` lists nothing; a multi-word query falls
  to subsequence as a whole, and there is no initials tier.
- **CommandPalette** ranks straight queries well but its one scorer is a
  subsequence, so abbreviations fill the list with junk (`tmln`: Toggle
  timeline, then threadManagerClient), a category subsequence outranks a
  title subsequence (`quik`: every QuickExt command above Store
  quickmark), and `opne ext`, `nosie`, `randomise` find nothing.

**The rule that keeps accuracy: new tiers only fill below the old ones.**
Both surfaces keep their strict matching (exact, prefix, word start,
substring) exactly as it was; the looser tiers rank under every strict
hit and only show when the strict ones run out.

**Built: `scripts/shared/FuzzyMatch.py`**, a pure-Python module bound
into both packages as a `FuzzyMatch` DAT (the RegistryBase pattern) and
mirrored into the TDXL launcher as `src/fuzzy.ts`. A token hits at one
of seven tiers: exact, prefix, word, substring, initials (`mfo` ->
movieFileOut), typo (bounded Damerau distance: 1 for 4..7 letters, 2 for
8+, against each word, its prefix cut to the token's length, and the
joined name), subsequence (the CommandPalette's original scorer, now the
floor). Typo sits above subsequence on purpose: for four or more
letters, one slip from a real word is a stronger signal than letters
scattered through a longer name. Both sides fold before comparing: lower
case, separators and camel humps dropped, and a few British spellings,
anchored per word (`randomise` -> `randomize`, `colour` -> `color`) and
narrow on purpose, because a fold changes typo distances: an unanchored
`ise` -> `ize` turned noise into noize and put `nosie` two edits from it.
A multi-token query's tier is its worst token's, and the tier of every
token is folded into the quality, so a row whose other tokens hit
tighter wins the tie.

- **CommandPalette** scores title, category and path through
  `score_fields`: a category hit carries a 0.4 tier penalty and a path
  0.7, so a title hit outranks the same hit elsewhere; the path stays
  substring-only. The total is `(10 - tier) * 1000 + quality * 100` plus
  the unchanged nudges (type, favourite, context relevance), which keep
  their old reach inside a tier. The untyped ordering and the prefix
  modes are untouched.
- **SearchPalette** keeps its own strict pass and wildcards; only the
  fallback that ran when nothing matched literally now goes through the
  module (`rank = 4 + tier`), so folder tokens, exclusions and Latestonly
  still apply to fuzzy rows. The installed copy under
  `/ui/dialogs/palette` carries the DAT because the install script copies
  the whole container.
- **Pinned** by `tests/test_fuzzy_match.py` over two fixtures dumped from
  the live session, `tests/fixtures/palette_names.txt` and
  `command_rows.json`: a query -> expected-first table, and the
  invariant that a literal substring hit never leaves the strict tiers.
- **Launcher port**: the TDXLPP session owns that checkout (one writer
  per checkout, a live TD on it) and the matcher change to a shipping
  product is the owner's call, so the port and its case table went to
  that session as a message. Owner said go; landed there as 1d03dfb the
  same day: `src/fuzzy.ts` byte for byte the mirror of the Python module,
  `fuzzyScore` a one-line delegation, the ten call sites untouched, the
  inline-args bonus rescaled from `90 * k` to `1000 * k` because it
  encoded "worth a whole word" against the old magnitudes, the tie-
  breaker nudges left alone because a tie-breaker is what they now are.
  That session's review caught the one defect: the spelling folds used
  regex lookbehind, a parse-time error on JavaScriptCore before Safari
  16.4 that would have taken the launcher bundle with it; both files now
  use capture groups (1b46abf6 here). Their gate is
  `scripts/fuzzy-selftest.mjs` (`npm run test:fuzzy`, 51 cases, hard
  fails on a reappearing lookbehind); a case added to
  `tests/test_fuzzy_match.py` here should be mirrored there.

## 32 — A pasted install with nothing picked went silent, and the Console tab raised, 2026-09-12

Owner did a clean install from the site's copied script with no tools
picked and saw nothing open, plus this in the Textport:

    File "/FNSTools/webBrowser/parexec1", line 32, in onPulse
    td.tdError: Cannot execute Javascript.

Three defects and one gap, all in shipped code, measured live:

1. **The traceback is the Hub's.** `HubExt._serveConsole` pulses the
   root browser's `Reload` when its address already points at the
   console server, and the stock palette browser's `parexec1` turns that
   pulse into `location.reload()` through `executeJavaScript`, a frame
   later and outside any try. On a fresh install the Web Render is still
   off at that point (exposure serves the console before it switches the
   render on), so the JavaScript cannot run. **Fix:** pulse only when
   `webrender1` is active; a render that switches on loads its address by
   itself. Verified: two consecutive opens of the console at Install &
   remove through the Hub, render off then on, no error either time.
2. **The paste rail opened nothing.** By design it stores `FNS_welcomed`
   = `paste` right after `loadTox` so the first-run welcome stays out of
   the way while the selection installs; nothing followed the install.
   With no tools picked that meant core landed and the flow ended
   silently. **Fix:** `InstallerExt.Install` ends in `_afterPasteInstall`:
   when the flag says `paste` it moves it to `shown` and, unless Plus
   picks are waiting (`tools` minus `install` in the selection; the script
   then pulses Configure itself for the sign-in picker), pulses the root's
   Pick Tools 60 frames later, which opens the console's Install & remove
   tab in the Hub. Verified on the dev installer with the flag armed: the
   Hub switched from Toolbar to Console with `#tools` and the flag moved
   on.
3. **Tab order.** Install & remove is now the first console tab
   (`BUILTIN_TABS` and the page's `FALLBACK_TABS`), so an open with no
   fragment lands there.
4. **"Set up like last time" never appeared on a pasted install** because
   the offer needs `FNS_FIRSTRUN`, and `_isFirstRun` counted core as
   installed packages; the paste rail installs core before anything can
   open. `_isFirstRun` now ignores the manifest's core names too, so a
   root with core and no tools is a first run: the welcome and the
   machine's last install (pre-checked, never applied) show on the
   console's Install & remove tab. `docs/LastInstallRecord.md` updated.

FNS_Hub and FNS_Console to 3.2.1, the installer rail to 3.2.2 (the
InstallerExt change ships inside the bootstrap, so users see all of this
after the next release). Not done: a cold clean install from the site's
script on a bare project to watch the landing end to end; the pieces were
verified in the dev project.

**Same day, after v3.2.2 shipped, three more from the owner's clean
installs.** (a) The landing *had* worked: the Hub window opened at the
bottom-left of display 0, another screen. Hub (and Remote's QR window,
BeatMod's manager) now open on the display the cursor is on. (b) The
picker's Close button died a minute after an install: the installer
stopped its server on a fixed timer and released the browser's hold with
it, so the render went dormant on its last frame; now idle-based with a
page heartbeat, and the hold is released only by the server that owns it
(the console's hold survived being cleared by the installer before). The
console page got the same heartbeat against its ten-minute idle. (c)
**"Set up like last time" had never fired since 2026-08-22**, on a drop
or a paste: `_isFirstRun` counted every COMP child but the three rails,
and the root's own `FNS_ConfigHost` has shipped inside the bootstrap since
then, so every root had one "package". Worse, `FNS_ConfigHost` is also a
catalogued package name. The test now asks the only real question: is
any manifest TOOL (packages minus core, minus the rails and the root
host) a child of the root or in its install record. Verified on the
shipped rail: bare root and core-only root are first runs, a tool child
or a pane-placed tool in the record is not, and the served page for a
core-only root carries the owner's last install. The record itself was
fine all along (written on project save; the owner's SPRIND_sketch.toe
had recorded seven tools). Installer rail to 3.2.3.

**2026-09-13, after v3.2.3.** The first pasted install with the offer
working reported `removed FNS_ConfigHost`: the root's own config host is
a COMP child named like the catalogued package, the served page listed
it as an installed tool, the user's selection did not include it, and
the apply pass removed it -- silently costing that project its roaming
root settings and its last-install record. `ResolvePlan` never puts
`ROOT_HOST` in `to_remove` now, and the served `installed` list leaves
out the rails and the host. Two UX asks from the same screenshot: "Set
up like last time" is the first card, lit as primary, and installs on
that one click (`installNow`: plan, then install, no review dialog; the
list is the user's own from a saved project); and the done dialog is a
report (tool count up front, chips by title, removals struck, failures
marked, core folded into the label) instead of a monospace dump.
Verified in the Browser pane against a scratch bootstrap served by its
own installer: one click, nineteen packages landed, no removal, the
report rendered. Installer rail to 3.2.4.

**Same day: docs links were dead inside TouchDesigner.** Owner asked
whether the report's chips should open the docs in a browser. Measured
first: the Web Render TOP ignores popups (`Redirect Popups` off; on
would navigate the picker away), so every `target=_blank` link the
served page had -- "Read the docs", the per-tool "docs ↗", "Become a
supporter" -- did nothing in TD; only the site flavor ever opened them.
Now the served page hands every external link to `POST /open` and the
installer opens the system browser (`ui.viewFile`, TD's own opener and
the convention in HubRegistry, MainMenuRegistry and the promoter's
dialog; owner's call over Python's `webbrowser`), the console proxies
`/open` for the Hub's tab, and each
tool chip in the report is a link to its `help_url`. Verified with a
recording override on `_openExternal` and a click executed inside the
live render: the docs URL arrived. Console 3.2.3, rail 3.2.5.

**Same day: the Hub "looked odd in terms of sizing".** Measured: the
root `webBrowser` is a fixed 1280 x 720 panel and the Hub's Console tab
mirrors it (a Select COMP, fit off) into 900 x 560, so the page rendered
at 1280 wide and was scaled to 900 (small text) with the 16:9 frame
letterboxed in the slot (black bands above and below the page). The
browser's `w`/`h` are expressions now: the Hub's tab area when a Hub is
installed, 1280 x 720 otherwise (the bare-root picker in its floating
viewer). Measured after: browser, mirror and render all 900 x 560. Ships
in the root, so rail 3.2.6. The plan modal is a report too (same shape as
the install report; verified on a bare scratch root).

## 33 — OpMenuMods took no effect on a fresh install, 2026-09-14

Owner installed FNS_OpMenuMods into a fresh project (SPRIND_sketch) and
the OP Create dialog showed none of it. Read through Convoy on that node:
every host reported `Registered`, the global's contributor table held
OpMenuMods, IOFilter and OpTemplates, and `/ui/dialogs/menu_op/nodetable`
held only the registry's own right-click menu: no `script_inject`, no
`script_IOFilter`. `Resync()` on the global injected both at once.

**Cause.** `RegisterContributor` rebuilt only the pop menu when the
dialog already existed and left the full surface sync (chain stages,
panels) to the deferred path, which only runs when the dialog is NOT
there yet, so only at boot. A contributor registering mid-session, which
is every fresh install, never got its stages; the healing tick that would
have caught it is switched off in code. The dev project never showed it
because its surface is built at boot. **Fix:** register and unregister
run the whole idempotent sync, plus one deferred pass ten frames later
for a contributor whose own ops were still being built when its host
registered. Registry Version 1.1.1 so fresh globals carry it; package
3.2.1. The owner's test project was healed live by the Resync.

## 34 — AutoRes rewrote operators the owner never dropped, 2026-09-14

Owner Alt-dropped one generator TOP and AutoRes changed other operators
with it. Both AutoRes and AutoCombine carry a vendored `kindergaertner`
child watcher pointed at `ui.panes.current.owner`. Its snapshot was the
network's whole subtree (a recursive `findChildren()`, 14,932 operators
under the toolkit root), keyed by the OP object, but `Observe()` only runs
on the target's DIRECT child count change. Anything that appeared deeper in
between (a package the updater replaced, a replicator, a tox loading inside
a child COMP, ops pasted into a sub-network through another pane) piled up
as "new", and the next Alt-drop handed the whole backlog to `SetRes` /
`SetCombine`: every inputless generator TOP (AutoRes) or every TOP with
inputs (AutoCombine) in it was rewritten. A dropped COMP also had its
insides rewritten, and OP hashes follow the name so a rename read as a
create plus a delete.

**Fix.** The OpTemplates copy had already been ported (NavbarCookDiet.md:
immediate children, keyed by `OP.id`, a `Refresh()`); the same observer
now lives in the AutoRes and AutoCombine copies, which are separate
nested suspects with their own toxes (saved explicitly, then the
packages, then the root). Each tool's callback also filters to direct
children of the watched network and refuses a batch over 16 as not a
drop. Verified live: a probe TOP created at the root is seen by both
watchers by id, an oversized batch and a nested op fed straight to the
callback are refused without a raise. Packages 3.2.2.

**Left as is.** Five watchers exist. OpTemplates' pane watcher has an
empty callback (OpMenuRegistry places alternatives now); its library
watcher (`kindergaertner_mymod1`, target the templates COMP) only
refreshes a cache and colours base COMPs directly under the library, so
its recursive snapshot is wasteful, never wrong; QuickExt's watches the
Component Editor's config COMP through a tag filter and its injector
refuses any DAT without QuickExt's own marker text. Port those two to the
immediate-children observer when either is next touched.
