---
status: in-force
summary: 'The command curation file shared between FNS_CommandPalette and the TDXLPP launcher: one machine-wide store for favourites, hidden/shown overrides and presets, keyed by tool#id, merged per entry with tombstones, seeded once per machine.'
since: 2026-09-02
skill: fns-command-registration
---

# Command Curation — one favourites file for every consumer on the machine

Owner's direction, 2026-09-02: the palette's favourites, hidden/shown
overrides and presets are to be SHARED with the launcher (its tray overlay
and its palette tab inside TD). Until then curation was two stores by design
(`CommandRegistration.md`): the launcher's `config.json` prefs and the
palette's custom parameters, both keyed `tool#id` since the identity switch
the same day, so a merge was already mechanically possible. This document is
the contract both sides implement; the launcher's agent reviewed the first
draft the same day and three of its objections changed rules 3, 5 and 6 (see
"Reviewed" at the end). Query history stays per consumer: it is not
curation, and the launcher's history includes sessions the palette never
sees.

## Location

`<machine-default user palette>/FNSTools/config/command-curation.json`,
beside `FNStools_config.json` and the launcher's `gate-session.json`. The
rule the gate file already established applies unchanged: the location is
ALWAYS the machine-default user palette folder on both sides (the launcher
resolves it with `palette::default_user_palette_dir()`), never a relocated
store folder, so sharing cannot silently diverge. The file is machine-wide by
nature; the toolkit's `Config Scope` does not apply to it, because a
favourite keyed by `tool#id` is not project data. Under project scope the
palette still reads and writes it — that is the one deliberate exception to
"nothing leaves the `.toe`", stated here so it is a decision.

## Document

```json
{
  "schema": 1,
  "written_by": "fnstools",
  "written_at": 1788352000.0,
  "revision": 17,
  "seeded": {"fnstools": 1788352000.0, "tdxlu": 1788360000.0},
  "commands": {
    "FNS_Collect#collect": {"favorite": true, "updated": 1788352000.0},
    "TD_Session#toggle-realtime": {"hidden": false, "updated": 1788351000.0},
    "OpTemplates#insert": {"favorite": false, "updated": 1788350000.0}
  },
  "presets": {
    "3f9a1c2e": {"label": "Tempo 120", "target": "FNS_Toolbar#set-bpm",
                 "kwargs": {"bpm": "120"}, "updated": 1788352000.0},
    "b71e0d44": {"label": "old", "target": "X#y", "kwargs": {},
                 "deleted": true, "updated": 1788000000.0}
  }
}
```

- **`schema`** — bump only for a change a reader of the previous number
  cannot survive; adding a field is not one. A reader that meets a higher
  number than it knows leaves the file alone and works from memory.
- **`written_by` / `written_at`** — DIAGNOSTIC ONLY (`fnstools` or `tdxlu`,
  and when). Never merge on them, never resolve anything with them; the
  per-entry `updated` is the only clock that decides.
- **`revision`** — a monotonic integer every write increments (absent reads
  as 0). Compared alongside `(mtime, size)` before a write, it removes the
  one hole stat leaves: two same-size writes inside one timestamp tick.
- **`seeded`** — consumer name → epoch of the one time that consumer seeded
  the file from its private store (rule 6). It lives in the file so that
  "seed once" is a property of the machine, not of a config file that can be
  restored from a backup.
- **`commands[tool#id]`** — `favorite` (absent = false) and `hidden` (absent
  = no override; `true` hides, `false` shows a command the tool declared
  hidden), plus `updated`. An entry with `favorite` false and no `hidden` is a
  **tombstone**: it says "removed at this time" so a stale peer cannot put the
  favourite back.
- **`presets[id]`** — `label`, `target` (a `tool#id`, optionally pinned to
  one copy as `tool#id@instance`, see "Multi-instance tools"), `kwargs` (string
  values, the launcher's `QuickCommandPreset` shape, so their side maps one to
  one), `updated`, and `deleted` (a tombstone). Ids are opaque unique strings;
  both sides mint `uuid4().hex[:8]`. A preset stays in the file when its
  target is not live; consumers show it as unavailable.
- **`updated`** — epoch seconds as written by `time.time()` or its equivalent.
  Both consumers run on one machine, so the clocks agree.

## Rules, identical for both sides

1. **Key on the curation identity `tool#id`**, never on the wire key `path#id`.
   Since 2026-09-03 (registry 1.10.0) the `tool` part is the package's PUBLIC
   name, its COMP name with a leading `FNS_` removed, so the identity for
   `FNS_Autosave` is `Autosave#save-now`. Consumers need no change: they read
   the field the wire gives them. The one-time cost was paid deliberately while
   the installed base of curated entries was a day old
   (see [PublicToolNames.md](PublicToolNames.md)).
2. **Read**: re-read the file whenever its `(mtime, size)` differs from the
   last read or write (both, because two writes can land inside one mtime
   tick), and merge it into memory **per entry**: the entry with the greater
   `updated` wins; a tie keeps the file's. The `seeded` map merges as a union
   keeping the later stamp per consumer.
3. **Write, with a lost-update check**: read-and-merge as in 2, apply the
   change with `updated = now`, prune tombstones older than 30 days, then
   **re-check immediately before the rename**: if `(mtime, size)` moved since
   the read, or the file's `revision` is not the one you merged from, another
   consumer wrote in between — read, merge and apply again, up to three
   times, then write anyway and report. Write the document with `revision`
   incremented, **atomically** (temp file in the same folder, named per
   process as `<file>.<pid>.tmp` so two writers never share one, then rename
   over) — and **retry the rename itself** a few times, tens of milliseconds
   apart: on Windows a replace fails with a sharing violation while any other
   process holds the destination open (the other consumer mid-read, an
   antivirus scanner, the indexer, a sync client), and it surfaces as a plain
   IO error, so without the retry a favourite silently fails to save with
   every other rule followed. Never write a document built from memory
   alone. Atomic rename alone only prevents a torn file; it is the re-check
   that stops two open panels from dropping each other's changes. The
   mutation must therefore be idempotent, which every one in this contract
   is.
4. **Remove by tombstone, never by deleting the key**: a favourite comes off
   as `favorite: false`; an override comes off by dropping `hidden` (the
   entry stays with its `updated`); a preset by `deleted: true`.
5. **A file that will not parse is parked** (`<file>.corrupt-<epoch>`,
   recoverable by hand) **and immediately replaced from the parker's merged
   memory** when that consumer holds loaded state with entries in it, so a
   torn write costs at most what changed since that consumer's last read.
   The same rewrite-from-memory applies when the file vanishes under a
   running consumer. A consumer that has never loaded anything (fresh
   process, empty memory) parks and leaves the file absent; it must NOT write
   an empty document, because the parked file is then the only copy and the
   other consumer's memory will restore it. Without this rule, 5 and 6
   together turned one corrupt write into the silent loss of every favourite
   on the machine.
   **Only a parse failure is corruption.** A read the OS refuses (on Windows,
   a sharing violation while another writer, a scanner or the indexer holds
   the file open) parks nothing and writes nothing: the consumer keeps
   working from memory and reads again next time. A change made meanwhile
   stays in memory with its `updated` stamp and goes out with the next
   write. Parking a healthy file held open would lose the other consumer's
   latest entries, and in a fresh process with empty memory would leave the
   file absent. (Added 2026-09-24, after the same rule was agreed for
   `command-usage.json`.)
6. **First contact seeds by union, once per machine**: a consumer seeds only
   while its name is absent from `seeded`. It adopts the entries of its
   previous private store wherever the file has no entry for that key,
   writes its stamp into `seeded` (always, even when nothing was adopted),
   and then retires the private store. The stamp in the file — not the
   retired store — is what makes it once: a launcher config restored from a
   settings export, or a project saved before this change, arrives with the
   old lists repopulated and no memory of having seeded, and would otherwise
   re-add favourites whose tombstones were pruned. The palette empties its
   `Favouritekeys`, `Visibilityoverrides` and `Presets` parameters after
   adopting them; the launcher retires `quick_favorite_commands`,
   `quick_hidden_commands`, `quick_shown_commands` and
   `quick_command_presets`.
7. **Nothing else rides along.** Query history, seen-command catalogues,
   session state and the like stay in each consumer's own store.

## Multi-instance tools

Added 2026-09-15 with registry 1.11.0, additive (no `schema` bump): readers
that predate it treat a pinned target as an unknown identity and show the
preset as unavailable, which is safe.

A tool that lives as several copies registers the same `tool#id` once per
copy, and each item carries the copy's label as `instance` (the owner's
`FnsInstance()`). The file keeps two different answers for the two kinds of
entry:

- **`commands[tool#id]` never splits per copy.** A favourite or a
  hidden/shown override is a machine-wide preference about a capability. An
  instance label is project data: another project may give the same label to
  a copy doing something else, so a per-copy favourite would star the wrong
  thing there. Starring `Scope#freeze` stars every copy, in every project.
- **`presets[id].target` may pin one copy**: `tool#id@instance`, split at the
  FIRST `@` (ids never contain one; a label may). An unpinned target lists
  once per live copy, each row titled with its label. A pinned target matches
  only the copy whose current `instance` equals the label exactly, so it is
  project-level in meaning: where no copy carries the label, the preset is
  dormant and stays in the file.
- **Label collisions are shared on purpose.** Two projects that both label a
  copy `Main out` both light up a preset pinned to it, since the file is
  machine-wide. That matches the common case (the same role in a similar
  rig). A user who wants them apart gives the copies project-specific labels.
- A favourite star on a spread preset row belongs to the preset, not to the
  copy the row shows.

## Field mapping

| Launcher pref | File |
|---|---|
| `quick_favorite_commands` (list of `tool#id`) | `commands[id].favorite = true` |
| `quick_hidden_commands` | `commands[id].hidden = true` |
| `quick_shown_commands` | `commands[id].hidden = false` |
| `quick_command_presets` (`{label, target, kwargs}`) | `presets[<minted id>]` with the same three fields |

## The palette's side

`FNS_CommandPalette/CommandCuration` (a module DAT, externalized) holds the
whole file protocol in `CurationFile`; `CommandPaletteExt` routes
`Favourites`, `ToggleFavourite`, `_overrides`, `ToggleHidden`, `ListPresets`,
`SavePreset` and `DeletePreset` through one instance created on first use.
The three legacy parameters remain declared so an older project's values can
be adopted once (rule 6), and they are excluded from the roaming config
(`Cfexcludepars` on the palette's config host), because the shared file is
what roams now. A palette that cannot read the file works from memory and
logs why; it never blocks.

## Why this shape

- **Per-entry merge, not last-file-wins**: two consumers write at different
  moments about different commands; whole-file replacement would drop one
  side's change every time they interleave.
- **Tombstones**: without them the union rule of first contact, and any
  consumer holding a stale in-memory copy, would resurrect removals.
- **The launcher's preset field names**: their side already has the shape;
  the palette adapts on read and write, so neither side carries a translation
  table in the file.
- **No file owner**: the gate file proved the pattern; the alternative (one
  side authoritative, the other polling it) puts one product's uptime in the
  other's critical path.

## Reviewed

The launcher's agent reviewed the first draft on 2026-09-02 before writing a
line against it. Verified on their side: `QuickCommandPreset` maps
losslessly, the machine-default palette folder is what they already resolve,
`tool#id` matches `command_identity`. Three objections were adopted in full
and are now rules 5 (rewrite from memory after parking, never an empty
document), 3 (re-stat before rename, retry) and 6 (`seeded` in the file),
plus `written_by`/`written_at` marked diagnostic-only. Their second pass
added the rename retry and the `revision` field (both in rule 3). Their
implementation
is scheduled by their owner; the palette side landed the same day and the
file appears on a machine the first time either consumer writes.
