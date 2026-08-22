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
| **FNS_CommandRegistry** | Launcher companion (TDXLPP), promoted to `/sys`, reached as `op.FNS_COMMANDREGISTRY` | The registry itself. We NEVER ship it — tools ship registration, the launcher ships the registry |
| **FNSCommand module** | Master: `FNSTools/CustomParTools/QuickExt/ExtUtils/FNSCommand.py` | `fns_command` decorator + `announce()`. THE single source — every copy in the project file-syncs this one file |
| **FNSCommandAnnouncer** | Child of master ExtUtils → rides all full-ExtUtils clones + the kit | The ONE lifecycle implementation: announces its grandparent tool, guarded |
| **Full ExtUtils clones** (~97) | Tool roots + FNS_About boxes | Live-clone the QuickExt master; carry module + announcer |
| **Slim ExtUtils copies** (~90, incl `/sys`) | Registry hosts, FNS_ConfigHost | NOT clones (deliberately trimmed); carry a file-synced `FNSCommand` DAT only — **no announcer** |
| **FNS_CommandKit** | `/FNSTools/FNS_CommandKit`, released to `modules/release/` | Third-party drop-in: module copy + clone-linked announcer + thin `Announce()` delegate + README |
| **extutils_distributor** | `FNSTools/CustomParTools/QuickExt/extutils_distributor.py` | Fleet police: `survey()` / `rollout(apply=True)` — clone links, dock repair, slim module presence, `/sys` scan |
| **PI release scrub** | `CompReleaseManager.prepare()` | On release: clears `file`/`syncfile` on any syncfile-marked DAT, severs clones reaching outside the candidate |

### Who registers how

- **Tools**: decorators only; the announcer does the lifecycle.
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

## Versions (state as of 2026-08-21)

- Live in-session registry: **1.2.0** (decorator harvest + `params` work).
- `hidden=` (1.3.0) and `builtin=` (1.4.0) are stamped in our metadata
  already but ride the wire only once the **utility 0.16.0** companion is
  injected. Forward-compatible: nothing to change on our side.
- **Ids are permanent**: launcher curation, history, and user presets key
  on `tool#id`. Renaming a shipped id (or the tool COMP) orphans all
  three. Treat every shipped id as public API.
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
- Handlers run synchronously on the main thread — return fast, kick long
  work off with `run(..., delayFrames=1)`. A dict with `ok: False` marks
  the run failed in the palette footer.

---

## Traps, operations and debugging

Moved to `/fns-command-registration` (the skill) so they load exactly when
someone is about to trip over them. Ten traps, the `extutils_distributor`
health check, the saving regime, and the "my command doesn't show" checklist.
