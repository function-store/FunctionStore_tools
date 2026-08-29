---
status: in-force
summary: 'Where a tool''s settings actually live: the .toe versus the machine-global JSON, the pars and state rails, every per-tool hatch and what it really gates.'
since: 628c523 2026-08-25 (closes ProductAdoptionAudit P5)
verified: 2026-08-26 — code-anchored against ConfigRegistryExt.py; hatch usage and the hostless-package survey measured live across all 49 packages
skill: fns-config-scope
---

# Scope and Persistence: what roams, what stays

Closes **P5** of [ProductAdoptionAudit.md](ProductAdoptionAudit.md). The
scope *switch* is documented in [ConfigScope.md](ConfigScope.md) and the
how-to lives in the `fns-config-scope` skill; this document is the model
underneath both — the two stores, the two rails, and what each per-tool
parameter actually gates. Read it before deciding that a tool "should not
sync", because two of the four hatches do not mean what their names
suggest.

## 1. There are two stores

**The `.toe` is the local store, and it is the default.** A tool's custom
parameters, the configurators' `state` tables, `StorageManager` contents
and `ExternalTables` sidecar files all live in the project file and
survive every save without the ConfigRegistry being involved at all.
Local identity between saves is not a feature that has to be switched on;
it is what happens when nothing overwrites it.

**The JSON is a machine-global overlay.** One aggregated file at
`<app.userPaletteFolder>/FNStools_ext/config/FNStools_config.json`
(schema 1, atomic write, override via the master's `Configfile` par —
`ConfigPath`, `ConfigRegistryExt.py:236`), shared by every project on the
machine. It is applied **once per session, ~30 frames after each tool
registers** (`_queueApply`, `:981`) — after clone sync, the tool's own
extension init and Registry-page bind wiring.

So the only moment local state is at risk is that one deferred apply at
boot. Everything else — every save, every mid-session edit — leaves the
`.toe` authoritative.

```
   .toe  ──(always)──────────────────────────────► live tool
                                                     ▲
   JSON  ──(global scope, Autoload on, once/session, ~30 frames)──┘
```

**`Configscope` on `/FNSTools` decides whether the overlay exists at
all.** `global` (default) roams; `project` never reads and never writes
the file. There is **no per-tool scope** — see §6.

## 2. Two rails per tool

A tool's section in the file has exactly two payloads, and they are gated
differently.

| Rail | What it is | Written by | Applied by |
|---|---|---|---|
| `pars` | mode/val/expr/bindExpr of the tool COMP's **custom parameters** | `_snapshotPars` `:373` | `_applyPars` `:402` |
| `state` | any JSON-safe dict the tool returns from `onConfigSave()` in its `config_callbacks` DAT | `_snapshotTool` `:475` | `_applyToolConfig` → `onConfigLoad(data)` `:993` |

Plus a `meta` block (save timestamp, `tool_version`) that is recorded and
never applied.

**The `pars` rail is conservative by construction.** Meta pages
(`About`, `Version Ctrl`, `Info`, `Callbacks`, `Common`) are skipped,
pulse/momentary/header styles and read-only pars are skipped, and **a par
missing from the live tool is never created** — TDJSON's
`addParametersFromJSONOp` was rejected precisely because it resurrects
retired parameters from a stale file. A dangling BIND falls back to
CONSTANT carrying the recorded `eval`, so a broken bind cannot kill an
extension init. The tool's own `Registry` page **is** persisted on
purpose: those pars are the bind masters holding surface order and
display, and restoring them is how bar layout survives a tool
replacement.

**The `state` rail is whatever the tool says it is.** It is
`json.dumps`-probed before it lands, so a bad state drops that one tool's
section rather than poisoning the file — but nothing inspects or filters
its contents. See §4.

## 3. The hatches, and what they actually gate

Four parameters on the tool's Config page (`TOOL_PAGE_PARS`, `:88`). The
table is the whole truth; the prose after it is the part that surprises
people.

| Hatch | `pars` written | `pars` applied | `state` written | `state` applied |
|---|---|---|---|---|
| *(defaults)* | yes | yes | yes | yes |
| `Persistpars` **off** | **no** | **no** | yes | yes |
| `Excludepars` / `Excludepages` pattern | **no** (matched names) | *unfiltered* — see below | yes | yes |
| `Autoload` **off** | **yes** | **no** | **yes** | **no** |
| `Configscope = project` (toolkit-wide) | **no** | **no** | **no** | **no** |

### `Autoload` off is not "do not sync"

`SaveAll` (`:499`) iterates every registered entry with **no `autoload`
check**, and assigns `tools[canonical] = section` — a wholesale replace of
that tool's section. `autoload` is consulted only at registration, to
decide whether to queue the apply (`:1062`).

So `Autoload` off means **publish but never adopt**: the tool ignores the
shared file, while still overwriting it for every other project on the
machine at each save. For a tool holding project-specific values that is
the worst of both — it exports exactly the values that should not travel.

**The hatch that actually stops the sync is `Persistpars` off**, which is
symmetric: it gates the snapshot (`:481`) and the apply (`:1013`) through
the same `info` flag. `Excludepars = '*'` is the equivalent for a tool
that must keep its `state` roaming while no parameter does.

### Exclusions are snapshot-side only

`Excludepars`/`Excludepages` are `tdu.match` patterns tested in
`_snapshotPars`. `_applyPars` iterates whatever the section contains with
**no pattern filter**. Adding a name to `Excludepars` therefore stops
future writes, but a value written before the exclusion keeps being
applied until that project saves again and replaces the section. It is
self-correcting after one save on the machine that made the change — not
immediately, and not at all on a machine that never saves.

### `Autoload` off does not stop the file being read for that tool

It stops the deferred apply being *queued*. `LoadTool(name, force=True)`
and `LoadAll()` still apply it if something calls them.

## 4. The `state` rail has no exclusion hatch

`Persistpars`, `Excludepars` and `Excludepages` all cover custom
parameters only. Anything returned from `onConfigSave()` roams
unconditionally under global scope; `Autoload` off suppresses only the
load side. There is no per-key filter and no "state stays local" flag.

**The only rail is the callback itself.** If part of a tool's state is
project-specific — operator paths, file paths on this machine, per-show
bookmarks — do not put it in the returned dict. Keep it in the `.toe` (a
table DAT, `StorageManager`, an `ExternalTables` sidecar) and return only
the portable half.

## 5. REPLACE semantics — last writer wins per surface

`RestoreState` on the three configurators is a **wholesale replace**, not
a merge, and the JSON is machine-global. So the last project to save a
surface owns that surface's layout for every project on the machine. This
is by design and was explicitly decided rather than fixed — see
[ConfiguratorPersistenceFixes.md](ConfiguratorPersistenceFixes.md) §0.D.

Two consequences worth stating plainly:

- A project opened, nudged and saved will re-shape the toolbar for the
  next project you open. Setting that project to `Configscope = project`
  removes it from the contest entirely — it stops adopting *and* stops
  clobbering.
- The file itself is read-merge-write at the *tool* level: sections of
  tools that are not currently installed are preserved, so a partial
  install never loses another install's data. The replace is inside one
  tool's section, not across the file.

Schema handling is deliberately unforgiving in the read direction: a file
whose `schema` is not `SCHEMA` is **refused for reading** — `ConfigData`
hands callers an empty document (`:306`) — and on the next write it is
moved aside as `.schemaN.bak` and started fresh. Nothing is silently
destroyed, but nothing mismatched is silently half-applied either.

## 6. There is no per-tool scope

`Configscope` is one menu on `/FNSTools`. A tool cannot declare "my
settings are project-local" while the rest of the toolkit roams; the
nearest approximations are `Persistpars` off (kills the `pars` rail both
ways) plus a `state` callback that returns nothing local, or flipping the
whole toolkit to project scope.

This is the real gap the hatch table exposes, and it is why the de-facto
answer today is §7 — non-registration.

## 7. The exceptions list — tools that stay project-local

These were deliberately never given a `config_callbacks` DAT. Their state
lives in the `.toe` plus sidecar files and never enters the roaming layer.
Triage record: `briefs/2026-08-12-config-roaming-handover.md` §2.

| Tool | State | Why it stays local |
|---|---|---|
| QuickMarks | network bookmarks (`StorageManager`) | bookmarks are operator paths — meaningless in another project |
| midiMapper / oscMapper | mapping repo tables (`repo_maker.Repo` via `mapTables`/`ExternalTables`) | documented as "saved into your project folder for easy migration" — project-local by design. `midiMapper` is additionally `allowCooking=False` and cannot host anything |
| ResetPLS1 | exception list (table + `ExternalTables`) | left local pending a check of whether entries are op-path-based or pattern-based |

Migrated the other way, for contrast: `ExprHotStrings` (hot-string table)
and `NoUI`/`HideTimeline` (`timeline_height`) are genuinely user-level and
do roam.

The only recorded partial exclusion in the tree is
`{'Excludepars': 'Spoutactive'}` passed at `StampHost` time
(`scripts/shared/RegistryBase.py:1306`), plus the system's own
`Excludepars = 'Configscope'` on both hosts that snapshot the root — that
one is load-bearing: it is what stops a roamed section overwriting a
project's own scope declaration.

## 7b. Tools with no config host at all — and why that used to lose data

Distinct from §7: those tools opted OUT deliberately. These twelve simply never
had a host, so nothing about them roamed in either direction. Surveyed live
2026-08-26:

`FNS_ConfigRegistry`, `FNS_NavbarRegistry`, `FNS_OpMenuRegistry`,
`FNS_ToolbarRegistry`, `FNS_MainMenuRegistry`, `FNS_PaneTypeRegistry`,
`FNS_TimelineRegistry`, `FNS_PaletteRegistry`, `FNS_HubRegistry`,
`FNS_Console`, `FNS_ConfigHost`, `FNS_TimelineTools`.

Not roaming is fine on its own — the `.toe` is the store (§1). **It was not
fine in combination with `reloadcustom = True`**, which every package update
used to run under: the reload reset every custom par, and the standard answer
("ConfigRegistry re-applies them when the host re-registers") does not exist
for a tool that has no host. So an update wiped their settings with **no
restore path in EITHER scope** — not just under project scope, which is how the
exposure was originally framed.

Six of them were in the `reloadcustom = True` group: every registry's
`Menuorder`, `Callback`, `Autoregister` and the rest were reset on each update
with nothing to bring them back.

**Closed 2026-08-26** by the fleet flip to `reloadcustom = off`
([UpdaterHardening.md](UpdaterHardening.md) §4): custom par values now survive
an update in place, so a tool needs no host and no config file to keep its
settings across a version change. Hostless is now a complete position rather
than a silent liability.

### Eleven of them stay hostless on purpose

Two independent reasons, and they agree:

- **A registry's configuration IS its package's exposed Registration
  parameters**, and the surface layout it manages is already persisted by the
  configurators' `state` tables. A config host would add nothing.
- **Most of them are clone MASTERS**, so a host stamped into one replicates
  into every clone — the `/fns-registry` hazard. Measured 2026-08-26:
  `FNS_ConfigRegistry` 42 clones, `FNS_ToolbarRegistry` 20, `FNS_HubRegistry`
  12, `FNS_NavbarRegistry` 5, `FNS_MainMenuRegistry` 4, `FNS_OpMenuRegistry`
  and `FNS_TimelineRegistry` 3 each, `FNS_Console` 1. Seeding them would have
  put 42 ConfigRegistry hosts inside every config host.

`FNS_CommandKit` has no settable pars; `FNS_ConfigHost` and
`FNS_ConfigRegistry` are the config system itself.

**`FNS_TimelineTools` was the exception and now has a host** (stamped via the
master's `StampHost`), with
`Excludepars = 'Scope Scopecomp Moviefile Audiofile Movieop Audioop'`. Its
appearance and behaviour roam — the Background and Waveform pages,
`Movieaudio`, `Synclength`, `Synctarget`, `Onmediachange`, `Followtimeline`;
29 pars in all — while the media pointers stay in the `.toe`, because they are
machine- and project-bound (absolute file paths and absolute op paths).
`Scope` is excluded **with** `Scopecomp` deliberately: a roamed scope of
`comp` with no `Scopecomp` to go with it is a broken state, so the pair travels
together or not at all. Verified by reading the written section back — none of
the six present.

## 8. `FNS_persist` — opt-in roaming without a host

The opposite lever. Tag any COMP `FNS_persist` and the `/sys` global
registers it (canonical = the COMP name, defaults throughout: autoload on,
persist pars, no callback, no `source_registry`) — the zero-configuration
path for micro-tools too small to carry a ConfigRegistry host. Precedent:
`FNS_hotkeys` in `HotkeyManagerExt`.

Because it registers with defaults and exposes no `Excludepars` par, the
tag is **all-or-nothing**: every custom par on the COMP roams. A tagged
COMP that also holds something project-specific needs a real host instead.

Timing rules that are easy to get wrong (`_sweepPersistTags`, `:161`):

- **Never on a timer.** Finding a tag means walking the whole project, and
  this toolkit runs inside live shows. It fires at the boot window
  (bounded by `BOOT_SWEEPS`) and at every `SaveAll` — nothing else.
- **The sweep runs BEFORE the snapshot in `SaveAll`.** Registering queues
  a deferred apply, so a COMP tagged mid-session whose canonical name
  already carries *another project's* section must have its live values
  written out first, or that foreign section lands on it a few frames
  later.
- Tagging mid-session is otherwise inert: it takes effect at the next
  save, and its settings apply on the next open.
- Untagging unregisters but never deletes the saved section — it is just
  an uninstalled tool.
- A hosted tool always wins its canonical name; clashes between two tagged
  COMPs keep the first and `debug()` the rest.

## 9. Decision guide

| You want | Do this |
|---|---|
| Settings shared across all projects on the machine | nothing — this is the default |
| This whole project's settings pinned to its `.toe` | `Configscope = project` on `/FNSTools` |
| One tool's parameters never to roam, in either direction | `Persistpars` off on its host |
| A few named parameters never to roam | `Excludepars` pattern (and save once from a project that has them, to purge stale entries) |
| A whole page never to roam (e.g. keep bar position local) | `Excludepages` pattern |
| A tool's *state* to stay local | do not return it from `onConfigSave()` — there is no hatch (§4) |
| A tool to ignore the shared file but keep feeding it | `Autoload` off — and understand you are still overwriting other projects (§3) |
| A micro-tool's pars to roam with no host | tag the COMP `FNS_persist` |
| Genuinely project-specific tools | do not register them at all (§7) |

## 10. Known gaps

Recorded, not fixed. Each is a defect in the *mechanism*, not the
documentation.

1. **`Autoload` off writes anyway.** Either `SaveAll` should skip
   autoload-off tools, or the concept should be renamed so it reads as
   load-only. Today it silently exports project-specific values into the
   shared file (§3).
2. **No `state` exclusion.** An `Excludestate` par, or a documented filter
   convention, would make the `state` rail as controllable as `pars` (§4).
3. **`_applyPars` ignores exclusion patterns.** Filtering on apply as well
   as snapshot would make an exclusion take effect immediately and on
   every machine, rather than after one save (§3).
4. **No per-tool scope.** A `Cfscope` par (`inherit`/`global`/`local`) on
   the Registration page, consulted by `_snapshotTool` and
   `_applyToolConfig`, is the honest fix — both choke points already take
   `info`, so it is roughly ten lines at each (§6).

## 10b. Considered and closed: values-only import for external configs

The 2026-08-27 audit rated "an imported config can restore parameter
*expressions*, which are arbitrary Python" as critical, and proposed a
trust split: configs saved by this install restore expressions, imported
ones restore values only.

**Rejected by the owner, 2026-08-28 — do not re-raise without new
facts.** The reasoning: with the web servers pinned to loopback (the
actual amplifier the audit found, fixed the same day), the remaining
vector is a config the user *chose* to import — the same trust act as
installing that person's `.tox`, which is this platform's entire
distribution model. TouchDesigner components ARE code; a config file is
not a lower trust tier here, and pretending it is would buy a degraded
import feature without a real boundary. Expression restore stays.

## 11. The updater gate

The updater uses this file as its save-before-replace /
restore-after-replace handoff. **Under project scope both directions are
gated**, so a tool-replacement flow must carry sections itself — its own
snapshot/apply around the swap, or temporarily forcing global scope with a
temp `Configfile` for the duration. Replacement logic that silently relies
on the file loses user state in every project-scoped install. Flagged in
the `ConfigRegistryExt` class docstring and in
[ConfigScope.md](ConfigScope.md).
