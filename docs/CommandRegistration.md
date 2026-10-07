---
status: in-force
summary: 'How FunctionStore tools ship quick-launch commands: the FNSCommand authoring module, the registry integration, and every trap paid for while building it.'
since: e45e207 2026-08-21
skill: fns-command-registration
---

# Command Registration — how FunctionStore tools ship quick-launch commands

The definitive map of the FNS_CommandRegistry integration in this project:
what the pieces are, how to author commands, why it is shaped this way,
and every trap we paid for while building it (2026-08-21). Read this
before touching anything command-related.

The wire contract itself lives in the TDXLPP repo:
`docs/fns-command-registry.md`. This document is the FunctionStore-side
implementation guide.

---

## Authoring — see the skill

The authoring recipe, the hard rules (permanent ids, caps, main-thread
handlers), the ten traps and the health check live in
`.claude/skills/fns-command-registration/SKILL.md` — load `/fns-command-registration`
before writing or debugging a command. This document keeps the map and the
reasoning: what the pieces are, why the scheme is shaped this way, and what
the shape costs.

## The pieces

| Piece | Where | Responsibility |
|---|---|---|
| **FNS_CommandRegistry** | Master `/FNSTools/FNS_CommandRegistry` (a store package since v3.1.1), promoted to `/sys`, reached as `op.FNS_COMMANDREGISTRY`; the launcher companion carries the same released artifact (`packaging/launcher_mirror.json`) | The registry itself. Row corrected 2026-09-08: it read "we NEVER ship it", which held until v3.1.1 |
| **FNSCommand module** | Master: `FNSTools/CustomParTools/QuickExt/ExtUtils/FNSCommand.py` | `fns_command` decorator + `announce()`. THE single source — every copy in the project file-syncs this one file |
| **FNSCommandAnnouncer** | Child of master ExtUtils → rides all full-ExtUtils clones + the kit | The ONE lifecycle implementation: announces its grandparent tool, guarded |
| **Full ExtUtils clones** | QuickExt users' own components (and `/project1` tests) | Live-clone the QuickExt master; carry module + announcer + NoNode. Toolkit tools left this shape on 2026-09-14 (docs/ExtUtilsSlimMigration.md) |
| **Slim ExtUtils clones** | Toolkit tool roots, nested tools, their FNS_About boxes | Live-clone `QuickExt/ExtUtilsMinimal`: module, CustomParHelper, the par-exec DATs and `extAutoInit`; **no announcer**, so each command owner announces itself from `onInitTD` |
| **Slim ExtUtils copies** (incl `/sys`) | Registry hosts, FNS_ConfigHost | Mostly unlinked copies (deliberately trimmed); carry a file-synced `FNSCommand` DAT — **no announcer** |
| **FNS_CommandKit** | `/FNSTools/FNS_CommandKit`, released to `modules/release/` | Third-party drop-in: module copy + clone-linked announcer + thin `Announce()` delegate + README |
| **extutils_distributor** | `FNSTools/CustomParTools/QuickExt/extutils_distributor.py` | Fleet police: `survey()` / `rollout(apply=True)` — clone links, dock repair, slim module presence, `/sys` scan |
| **PI release scrub** | `CompReleaseManager.prepare()` | On release: clears `file`/`syncfile` on any syncfile-marked DAT, severs clones reaching outside the candidate |

### Who registers how

- **Tools**: decorators plus a deferred `FNSCommand.announce(self.ownerComp)` from `onInitTD` (slim ExtUtils, no announcer). Components on the full ExtUtils still get the announcer's automatic lifecycle.
- **Registry-family exts** (`ConfigRegistryExt`, `PaneTypeRegistryExt`):
  the deliberate exception. Their hosts carry slim ExtUtils (no
  announcer), and only the `/sys` GLOBAL may register — they keep their
  own legs with an `_isCommandOwner()` guard comparing
  `self.ownerComp is op.FNS_<NAME>REGISTRY` (identity via shortcut, NOT
  path — this survived the registries being relocated to
  `/sys/FNS_Registries/` mid-session).
- **FNS_CommandKit**: contains the SAME announcer (clone-linked to the
  master; severed + baked on release). `FNSCommandKitExt` is a one-line
  delegate so `op('FNS_CommandKit').Announce()` works.

### The announcer's guards (each earned)

1. Announces `ownerComp.parent().parent()` — announcer → container
   (ExtUtils or kit) → tool. Identical geometry in both homes.
2. **Declares-commands check**: only announces a parent that actually has
   decorated promoted methods or a promoted `FnsCommands()`. FNS_About
   boxes and passive hosts are silently skipped and never tagged
   (an empty `Register()` acts as an unregister; tagging everything is
   rescan noise).
3. **No unregister on destroy** — the COMP dies on every clone resync and
   project-save strip; registrations must survive both. Dead owners are
   pruned lazily by the registry.
4. Everything guarded: no registry in the session = silent no-op.

---

## Design decisions and their trade-offs

**Why clone-distributed instead of vendored?** The contract blesses
vendoring ("the `_fns_command` attribute is the contract, any copy is
compatible forever"), and we started there. We migrated to distribution
for one source of truth: a contract addition (like `builtin` in 1.4.0)
lands in one file and reaches every copy by file-sync. The honest cost:
the distribution machinery has real failure modes (see Traps) that
vendored copies never had. The trade was accepted deliberately.

**Why an auto-announcer instead of explicit lifecycle code?** It removed
a ~15-line triplet from 39 exts and makes internal authoring one-touch.
The honest cost: registration is invisible in the tool's own code —
debugging requires knowing about the announcer. A middle option exists
and remains open: a `FNSCommand.install(self)` one-liner in each ext's
`onInitTD` (explicit, greppable, no announcer needed internally). We
chose the announcer; **if its invisibility ever costs a real debugging
session, switch then** — `install()` can be added, double-announce is
idempotent, and the announcer degrades to a no-op during migration. The
kit should KEEP the announcer regardless (zero-touch is its whole pitch).

**Why doesn't the kit have its own lifecycle class?** It briefly did —
that was divergence, and it was unified onto the shared announcer the
same day. One lifecycle implementation, everywhere.

---

## Versions (state as of 2026-09-15)

- Live in-session registry: **1.11.0**, FNS_CommandRegistry 3.2.1 in v3.2.15
  (multi-instance labels, below). 1.10.0 made the `tool` field the package's
  PUBLIC name, its COMP name with a leading `FNS_` removed, so a consumer's
  sorted list reads `Autosave` rather than burying every FNS tool under "F";
  see [PublicToolNames.md](PublicToolNames.md). 1.9.0 added canonical-id
  arbitration; the decorator harvest carries `canonical` since 2026-09-02.
- `hidden=` (1.3.0) and `builtin=` (1.4.0) are stamped in our metadata
  already but ride the wire only once the **utility 0.16.0** companion is
  injected. Forward-compatible: nothing to change on our side.
- **Ids are permanent**: launcher curation, history, and user presets key
  on `tool#id`. Renaming a shipped id (or the tool COMP) orphans all
  three. Treat every shipped id as public API. The `tool` half is the
  public name, which is as permanent as an id for the same reason: 1.10.0
  moved every FNS key once, on purpose, while the installed base was a day
  old. There is no second free move.
- **Multi-instance tools (registry 1.11.0, 2026-09-15)**: two optional
  promoted hooks on an owner COMP. `FnsInstance()` labels one copy of a tool
  that lives as several (evaluated per `Commands()` build, sent as
  `instance`, at most 32 chars); `FnsToolName()` pins the public tool name
  when copies have different COMP names, so curation keyed on `tool#id`
  reaches every copy. Canonical arbitration now keeps every copy of the
  winning tool. Preset targets accept `tool#id@instance` to pin one copy
  (see [CommandCuration.md](CommandCuration.md)); favourites and overrides
  deliberately stay per capability. FNS_CommandPalette titles such rows
  `label · instance`. The launcher's side is the same contract.
- Caps: 24 commands/tool, 6 params/command, menus ≤ 16 entries.
- **Live state chips (registry ≥ 1.6.0, adopted 2026-08-22)**: declare
  `state='Parname'` (custom par on the owner) or
  `state={'method': 'GetX'}` (promoted no-arg method — for inverse
  pars, child-widget values, computed state). Evaluated at QUERY time
  inside `Commands()` — always fresh, no re-announce needed. Values:
  bool → ON/OFF chip, number/str → value chip. Params may declare
  `current` for prompt prefill; a single-param command with `state`
  reuses it implicitly (SetVolume, SetInterval work this way). ~24 of
  our commands carry state. Design rationale:
  `docs/CommandStateProposal.md`.
- **Surfaces and capabilities (registry ≥ 1.7.0, master ported
  2026-08-31)** — two optional decorator fields, both pure metadata, both
  ignored by any older registry (the port is backward-safe in either
  direction, which is why it could land here before the launcher ships):

  - `surface=` names the consumer surfaces a command wants to appear on:
    a token or list of tokens (lowercase alnum/underscore/dash, ≤24
    chars, max 8). **Absent = exactly today's behaviour** (quick-launch
    only). Known tokens: `quick`, `session` (the launcher's Current-view
    companion bar), `context-menu` (its session right-click menu). The
    registry validates SHAPE only, never the value — consumers ignore
    tokens they do not serve, so new surfaces are additive and cost
    nothing to declare early.
  - `capability=` marks the command as part of a blessed capability: a
    namespaced id (`fns.collect`, `fns.media-browser`,
    `fns.mobile-control`; lowercase alnum/dot/underscore/dash, ≤64
    chars). A consumer that recognises the id may render rich native UI
    for the capability's command group; one that does not falls back to
    generic rendering. Progressive enhancement — **never a gate, never a
    secret**.

  Adoption is free for any tool: declaring `surface=['session']` today
  costs nothing and surfaces the command in the launcher's Current bar
  the moment its companion ships. Candidates:
  [CommandRegistryCandidates.md](CommandRegistryCandidates.md).

- Handlers run synchronously on the main thread — return fast, kick long
  work off with `run(..., delayFrames=1)`. A dict with `ok: False` marks
  the run failed in the palette footer.

---

- **Built-in commands ship inside the registry master (2026-09-02)**:
  `FNS_CommandRegistry/FNS_BuiltinCommands` holds two ordinary command owners,
  `TD_Dialogs` (22) and `TD_Session` (16), brought over from TDXLPP's
  `TDX_BuiltinCommands`. Each carries a docked `ExtUtilsMinimal` (the slim
  shape: FNSCommand and CustomParHelper file-synced to the masters, no
  NoNode, no announcer -- the owners announce from their own deferred
  init), imports `FNSCommand` the FNSTools way, and wraps the decorator
  locally to brand
  `builtin=True` and derive a **canonical id** `td.<group>.<kebab-method>`
  (`td.session.save-project`). Three things make the version gate real for
  them: (1) the wrapper declares the canonical id; (2) `_packageVersion` reads
  the OWNER's `Pkgversion`, so the container and both owners carry an
  expression-bound `Pkgversion` (`parent().par.Pkgversion`) that resolves to
  the registry package's version; (3) the harvest path now copies `canonical`
  from the decorator metadata -- it never had since 1.9.0, so no decorated
  command could be arbitrated (`Commands()` inserts the field only when the
  spec carries it). The runtime `/sys` copy is a full copy of the master, so
  `_sanitizeSysCopy` strips `FNS_BuiltinCommands` from it: a second owner set
  under `/sys` would announce the same commands from a path `RescanTools` can
  never rediscover and, with canonical ids, shadow the master's set on a
  boot-order coin toss. Consumer side (FNS_CommandPalette): `builtin` rows
  carry a `TD` badge in their own hue, rank after tool commands in `>` and the
  untyped list, and are excluded from `?` -- the wire contract's consumer
  rules. **TDXLPP must mirror two of these** for cross-project arbitration to
  work: the canonical derivation rule in its `TDX_BuiltinCommands` wrapper and
  the harvest fix in its registry copy; until then its built-ins carry no
  canonical id and simply coexist with ours (`path#id` keeps them apart).
  **Launcher state verified 2026-09-02** (TDXLPP checkout, read-only): its
  registry copy is 1.7.0 with no `canonical`, `_arbitrate` or `Shadowed`; its
  `FNSCommand.fns_command` has no `canonical=`; its built-ins are still
  `partial(fns_command, builtin=True)`. So with both companions in one
  project our 1.9.0 wins promotion and their built-ins register unarbitrated:
  38 duplicate rows in both palettes until they mirror (a) registry 1.9.0 +
  the `canonical` kw, (b) the wrapper, (c) a `Pkgversion` on their owners.
  Briefed to the TDXLPP agent session the same day. **Curation is two stores
  by design**: the launcher keeps favourites, hidden/shown overrides and
  presets in its `config.json` keyed `tool#id` (shared with its own
  TDXLUPalette tab in TD's Palette Browser, `palette_tabs.rs set_favorite`),
  our palette kept its own on pars (keyed `tool#id` since the identity
  switch that day). Their contract permits it ("consumers can curate
  differently"). SUPERSEDED 2026-09-02: the owner directed one shared file;
  the contract is `CommandCuration.md`. Their agent's reply the same day:
  registry 1.9.0 taken verbatim, the 38 canonical ids verified equal as sets,
  and later the same day the owners' `Pkgversion` landed and was verified in
  their live session (40 commands, 38 builtin, 38 canonical, Shadowed() empty
  there). **FNS_About caveat**: `_packageVersion` falls back to an FNS_About
  child's `Pkgversion`; their utility's FNS_About carries an empty `Version`
  par and no `Pkgversion`, so that path would have yielded ''. They bound the
  owners to the utility's extension constant instead, guarded by
  `extensionsReady` with a `'0.0.0'` fallback so a half-initialised project
  loses arbitration rather than winning on a garbage value. Consequence:
  where both companions load, the launcher's built-in set (0.23.0) wins and
  ours (0.1.0) is shadowed -- deterministic, and by version arithmetic, not by
  intent. **Mirror rule, revised the same day on the owner's direction: the
  launcher carries our RELEASED FNS_CommandRegistry package verbatim** --
  registry, `FNS_BuiltinCommands` and `FNS_About` in one artifact -- and
  drops its own `TDX_BuiltinCommands` fork, so there is one registry and one
  built-in set to keep identical rather than two files and a fork. The
  package was brought to the preferred shape first (an `FNS_About` child,
  `Pkgversion` 0.1.0 authoritative, the owner mirroring by expression; the
  palette got the same), then released through PI to `modules/release/`,
  read back into a cooking-disabled container and walked: no PI tags, no
  file bindings into this repo, the nested external-tox reference severed,
  every source compiling. `modules/release/` is ignored by git, so
  `packaging/launcher_mirror.json` records the artifact's version, size and
  sha256 at release, and `scripts/check_launcher_mirror.py` compares the
  launcher's copy (`utility/TDXLauncherUtility/FNS_CommandRegistry.tox`) to
  that record, keeps `FNSCommand.py` byte-identical for the launcher's own
  tools, and flags the old two-file shape while it still exists; exit 1 on
  any of it, to be run from either repo before a release. In a project
  where both companions load, the two registries are the same version and
  the two built-in sets the same package version, so promotion and
  arbitration both fall to the incumbent rule: identical content, no race. **The FNS_About caveat is fixed on their side**
  (same day): their utility's FNS_About is at the master shape with
  `Pkgversion` `0.23.0` authoritative and the legacy empty `Version` par
  destroyed; the chain is parameter-to-parameter (utility par bound to the
  child, read-only -- the registry-family shape -- then `parent().par.
  Pkgversion` down to both owners), the extension-constant guard is gone,
  and their release script now asserts the code constant equals the
  authority (fatal on a parse miss, because their prior check skipped
  silently when its regex stopped matching) and runs our mirror checker
  whenever this repo sits beside theirs, failing the release on drift.
  Left open by them as a decision, not a drive-by: giving their built-in
  owners a docked ExtUtilsMinimal so the owner sets are the same shape;
  arbitration does not depend on it. And a fair objection that
  comparing a companion version (0.23.0) with our package version (0.1.0) is
  a category error -- arbitration by version is a deterministic tie-break,
  not a quality signal; an explicit precedence field would make the outcome
  intentional (a 1.10.0 proposal, owner's call). On curation: standardise
  identity on `tool#id` (done on our side the same day), then optionally a
  shared no-owner file under the user palette folder with per-entry merge,
  tombstones for deletes, mtime reload and a schema version -- pending the
  owner. Decided the same day: built; the contract is `CommandCuration.md`.

- **Re-release 0.1.1 (2026-09-02).** The 0.1.0 artifact carried five
  documentation annotations; on the launcher's import their TDAnnotate
  internals raised `'td.annotateCOMP' object has no attribute 'Editing'` and
  cascaded past 5,800 errors. The cooking-disabled read-back above could not
  see that: extensions never initialise there, so it proves the tox parses,
  not that it works. The annotations are destroyed on the master, a
  `pre_release` hook strips any future ones from the staged copy, and the
  artifact is now verified by loading it ONCE into a cooking-enabled
  container in the project, waiting a few frames, and requiring
  `errors(recurse=True) == []`, no script errors, and `op.FNS_COMMANDREGISTRY`
  still resolving to the incumbent (same `REGISTRY_VERSION`, so no promotion;
  measured: 0 errors after 1,271 frames, 141 commands before, during and
  after). `packaging/launcher_mirror.json` records 0.1.1 (88,022 bytes).
  **The launcher's re-import recipe, as it is actually done there** (their
  agent, 2026-09-02, one step paid for with a TD crash): (1) destroy the old
  master, (2) let frames pass, (3) `loadTox` the new artifact -- destroying
  the promoted registry's master and loading its replacement in the SAME
  call crashed TD mid-teardown while the `/sys` incumbent still pointed at
  it; the same two operations a few frames apart work every time. Then keep
  it opaque: their Embody honours `tdn_exclude` only on a DIRECT child of
  the TDN boundary (the registry is one), strategy tags such as `py` that
  ride in on the owner DATs must be stripped on arrival or their Embody
  externalises them (that is how 0.1.0 forked), and `externaltox` points at
  the byte-identical repo copy with the toggle OFF so nothing ever reloads
  or re-saves the file the checker hashes.

## Traps, operations and debugging

Moved to `/fns-command-registration` (the skill) so they load exactly when
someone is about to trip over them. Ten traps, the `extutils_distributor`
health check, the saving regime, and the "my command doesn't show" checklist.
