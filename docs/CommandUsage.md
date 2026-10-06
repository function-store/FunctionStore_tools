---
status: in-force
summary: 'Optional rank-by-usage for FNS_CommandPalette and the TDXLU quick-launch overlay: a shared command-usage.json of per-consumer decayed scores keyed by tool#id, the pinned bonus formula with test vectors, and the write rule that tolerates several TDs.'
since: 2026-09-23
skill: fns-command-registration
---

# Command Usage: rank frequently used commands higher, optionally

Owner's request, 2026-09-23: frequently used commands should rank higher in
the command palettes, as an option. Two consumers run the same registry
commands (FNS_CommandPalette inside TD, the TDXLU quick-launch overlay), so
usage is shared between them the same way curation is
([CommandCuration.md](CommandCuration.md)). Drafted by the palette side and
reviewed by the launcher's agent the same day; their three requested changes
(decay model, several TD writers, pinned formula) are folded in below.

## Location and why it is a separate file

`<machine-default user palette>/FNSTools/config/command-usage.json`, beside
`command-curation.json`, resolved exactly as that file is (always the
machine-default user palette folder, never a relocated store).

It is NOT a section of the curation file. Curation rule 7 ("nothing else
rides along") stays in force, and a counter written on every run would churn
the favourites file and fight its lost-update loop for data that is only a
heuristic.

## Document

```json
{
  "schema": 1,
  "consumers": {
    "fnstools": {
      "Autosave#save-now": {"score": 3.0, "last": 1788352000.0, "count": 5},
      "TD_Session#toggle-realtime": {"score": 1.0, "last": 1788351000.0, "count": 1}
    },
    "tdxlu": {
      "Autosave#save-now": {"score": 2.0, "last": 1788350000.0, "count": 2}
    }
  }
}
```

- **`schema`**: same rule as curation. A reader that meets a higher number
  than it knows reads nothing from the file and gives no usage bonus. A
  writer that meets one records nothing and leaves the file untouched;
  otherwise its next run would write a schema-1 document over the newer
  file and wipe it.
- **`consumers.<name>`**: `fnstools` or `tdxlu`. A consumer writes only its
  own block and reads every block.
- **Key**: the curation identity `tool#id`. A preset counts against its
  target's `tool#id`, with any `@instance` pin dropped. Built-in TD commands
  are ordinary registry tools (`TD_Session`, `TD_Dialogs`, ...), so their
  identities are namespaced like any other package and cannot collide with
  another `tool#id` without the registry itself colliding.
- **`score`**: the decayed usage value as of `last` (float).
- **`last`**: epoch seconds of the latest recorded run (`time.time()`).
- **`count`**: raw run total. Display only; never used for ranking.

## What records

Only registry commands and presets write. A successful run records; nothing
else does:

- FNSTools: after `Run()` returns without refusing. Not on arming a
  destructive command, not on a refused or cancelled parameter walk, not on
  placing a palette component, navigating (`/`), or calling a promoted
  method (`~`).
- TDXLU: in `runToolCommand` after a reply with `ok !== false`. Session
  verbs, app actions, projects and `.tox` placement never touch the file.

Recording always runs, whatever the rank toggle says, so turning ranking on
later finds history already there.

## The math (identical on both sides)

Constants:

| Name | Value |
|---|---|
| `HALF_LIFE` | `1209600` seconds (14 days) |
| `V_SAT` | `20.0` |
| `BONUS_MAX` | `8.0` |
| `PRUNE_BELOW` | `0.01` |

All arithmetic is IEEE double. Nothing is rounded except where stated.

**On a run** (at time `now`, for key `k` in the writer's own block):

```
decay(dt) = 0.5 ** (max(0, dt) / HALF_LIFE)
score     = score * decay(now - last) + 1     # absent entry: score = 1
last      = now
count     = count + 1                         # absent entry: count = 1
```

Storing the decayed score, not the count, is what makes old heavy use fade:
100 runs a year ago contribute about 1.4e-06 today, not 100.

**At read** (for ranking):

```
v(k)  = sum over every consumer block c holding k of
        c[k].score * decay(now - c[k].last)
bonus = min(BONUS_MAX, BONUS_MAX * ln(1 + v) / ln(1 + V_SAT))
```

`bonus` is a float in `[0, 8]`. It is used unrounded.

**Pruning, on every write**: drop from the writer's own block any entry whose
`score * decay(now - last)` is below `PRUNE_BELOW`. A single run falls under
it after about 93 days of no use.

### Test vectors

| Case | Input | Expected |
|---|---|---|
| Never used | `v = 0` | `bonus = 0.0` |
| One run, just now | `v = 1` | `bonus = 1.8214` (4 dp) |
| One run, 14 days ago | `score 1, dt = 1209600` so `v = 0.5` | `bonus = 1.0654` |
| Update after one half-life | `score 4, dt = 1209600`, then a run | `score = 3.0` |
| Summed across consumers | fnstools `v = 3`, tdxlu `v = 2`, so `v = 5` | `bonus = 4.7082` |
| Saturated | `v = 20` or `v = 100` | `bonus = 8.0` |
| Old heavy use | `score 101, dt = 365 days` | `v ~ 1.43e-06`, `bonus = 0.0000` |

Compare to 4 decimal places; both sides mirror these as unit tests.

## Where the bonus goes in ranking

- **Typed**: add `bonus` to the row's score the same way `FAVOURITE_BONUS`
  (12) is added. Match tiers are 1000 apart on both sides, so usage cannot
  cross a tier, cannot beat a favourite on its own (12 > 8), and cannot
  reorder entry types (the launcher's `TYPE_WEIGHT` gaps and ours are wider
  than a tie).
- **Untyped** (the palette's empty query; the launcher's bare `>` / `?`
  browse): sort by context tier, then favourite, then `bonus` descending,
  then title. On the launcher side session verbs still lead that list.

## Write rule: several TDs share the fnstools block

Every open TD runs FNSTools, so several processes write `consumers.fnstools`.
A block written from memory would clobber the other TDs' increments. So:

1. Re-read the file at write time.
2. Apply the run update above to that one key in the value just read, prune
   the writer's own block, and leave every other block exactly as read.
3. Write atomically (temp file in the same folder, rename over), retrying
   the rename a few times tens of milliseconds apart for Windows sharing
   violations, as curation rule 3 does.

Two TDs recording at the same instant can still lose one increment. That is
accepted: usage is a tie-breaker, and a lost run costs at most one run's
worth of rank. The launcher is one process with one Rust writer for both of
its windows, so `tdxlu` really is single-writer.

A file that will not parse is parked (`<file>.corrupt-<epoch>`) and the
consumer carries on with no bonus. The next recorded run writes a fresh
document holding only that key. Usage is not worth rebuilding from memory.
Two consumers can each park the same corrupt file, leaving two
`.corrupt-<epoch>` copies; that is harmless, since nothing in either was
readable. Only a parse failure parks. A read refused at the OS level (on
Windows, a sharing violation while another writer holds the file open) is
not corruption: that write is skipped and the file left alone. Raised by the
launcher's agent from their implementation; the palette side had parked on
any read error until the same day.

## The toggle and clearing

- **FNSTools**: a `Rankbyusage` toggle on FNS_CommandPalette, roaming with
  the tool's config host (global scope follows the user between projects).
- **TDXLU**: Settings > Quick Launch > "Rank by usage", in launcher config
  (per machine).
- Off means no bonus; recording continues.
- **Clear usage** removes only the clearing consumer's own block. Ranking
  sums all blocks, so the UI copy says so, for example "Clears FNSTools'
  usage history; the launcher's still counts."
- Default: ON on both sides (owner, 2026-09-23). The bound keeps it a
  tie-breaker.

## Status

Contract approved by the launcher's agent on 2026-09-23, which recomputed
all seven test vectors independently and asked for the writer half of the
schema rule (folded in above). The owner set the default to ON the same day.

**Palette side built 2026-09-23.** `CommandCuration.UsageFile` holds the file
protocol beside `CurationFile`; `CommandPaletteExt` records in `_runCommand`
after a reply that is not `ok: False` (command rows by their `ident`, presets
by their target command's `tool#id`), adds the bonus in `Rank`, and offers
`UsageBonus(key)` and `ClearUsage()`, the latter behind a Clear usage button
on the Commands tab. The temp file is named per process (`.<pid>.tmp`) so two
TDs writing at once never share one. `tests/test_command_usage.py` runs the
seven test vectors and the file rules against a scratch palette. Verified
live: five recorded runs lifted a general command from row 74 to row 15 (the
top of its tier) with a bonus of 4.7082, the toggle off restored row 74, a
refused run recorded nothing, and Clear usage left an empty `consumers`.

**Implemented on both sides.** Palette `d0075aad` (FNSTools_PRIV), launcher
`be817c2` (TDXLPP `dev`, pushed), both 2026-09-23.

**Launcher side built 2026-09-23.** `src-tauri/src/command_usage.rs`
in TDXLPP, writer `tdxlu`: the same re-read-and-update-one-key write, a
per-process temp file, the rename retried 5 times at 40 ms, and a
process-wide mutex over both launcher windows. It records in `runToolCommand`
after a reply that is not `ok: false`, and presets record under their target
with the `@instance` pin dropped. Its 18 tests cover the seven vectors and
the file rules. Settings > Quick Launch > "Rank by usage" is on by default,
and its two-click Clear usage says FNSTools' history still counts.
