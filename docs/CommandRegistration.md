# Command Registration — how FunctionStore tools ship quick-launch commands

The definitive map of the FNS_CommandRegistry integration in this project:
what the pieces are, how to author commands, why it is shaped this way,
and every trap we paid for while building it (2026-08-21). Read this
before touching anything command-related.

The wire contract itself lives in the TDXLPP repo:
`docs/fns-command-registry.md`. This document is the FunctionStore-side
implementation guide.

---

## TL;DR — authoring a command

**Internal tool (has a root ExtUtils):** two lines, no lifecycle code.

```python
FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand')  # import

class MyToolExt:
	@FNSCommand.fns_command(help='Set the project tempo')
	def SetBpm(self, bpm: float = 120, sync: bool = False):
		...
```

That's it. Registration is **automatic** — the `FNSCommandAnnouncer`
inside your tool's ExtUtils announces the tool ~60 frames after load.
Label derives from the CamelCase name, help from the docstring's first
line, user-prompted params from the signature (type hints → styles,
`typing.Literal[...]` → menu, no default → required). Extras:
`fns_command(label=..., help=..., hidden=True, params=[...])`.
Never set `builtin=` — that flag is for TD/system commands
(TDXLPP-side `TD_UI` / `TD_Project`).

**After changing your command set at runtime:**
`op('ExtUtils/FNSCommandAnnouncer').Announce()` (from inside the tool).

**Third-party tool:** drop `modules/release/FNS_CommandKit.tox` inside
the tool, then the same two lines with
`FNSCommand = op('FNS_CommandKit').mod('FNSCommand')`. The kit's README
covers the rest, including the zero-import explicit-`FnsCommands()` path.

---

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
- **Proposed, not yet live**: `state=` chips for toggle commands (live
  ON/OFF in the palette, evaluated at query time) — see
  `docs/CommandStateProposal.md`. Do NOT stamp `state` kwargs until the
  registry side lands the schema.
- Handlers run synchronously on the main thread — return fast, kick long
  work off with `run(..., delayFrames=1)`. A dict with `ok: False` marks
  the run failed in the palette footer.

---

## Traps (all paid for — do not rediscover)

1. **Cloning does not carry dock relationships.** A clone whose children
   get rebuilt comes out undocked, which breaks `extParameter`'s Pages
   expression (`mod(me.dock.name)`). The distributor repairs docks and
   re-arms that expression — run it after any clone surgery.
2. **Cloning forces CHILDREN, never the clone COMP's own pars.** An
   extension wired on a master COMP does not propagate to clones of that
   COMP — wire `extension1` on each clone once (the kit's announcer
   needed this). Conversely this is why the announcer works at all: it is
   a *child* of ExtUtils, so its own `extension1` IS forced.
3. **`root.findChildren` does not see `/sys`.** Sweeps and the registry's
   own `RescanTools` miss `/sys` — worse, RescanTools PRUNES owners it
   cannot rediscover. After any rescan, re-announce the `/sys` globals
   via their `op.FNS_*` shortcuts. (Upstream fix belongs in TDXLPP.)
4. **Address `/sys` globals by shortcut, never path.** A peer session
   relocated them to `/sys/FNS_Registries/` mid-work; only
   shortcut-identity code survived.
5. **A DAT's cached module recompiles only on DAT change.** Making a
   missing module resolvable is not enough — touch the importing DAT
   (no-op text write) or its class keeps stub bindings.
6. **Batch text surgery: never cut to a searched terminator.** Cutting
   "to the second `return None`" truncated 6 exts (5 silently valid);
   excising "def → next def" ate the DECORATOR line of the following
   method (3 commands vanished with zero errors — the count diff caught
   it). Verify any batch edit with an AST parse AND a
   `def`-name diff against git HEAD of the synced mirrors.
7. **syncfile DATs write through to disk immediately** — the on-disk
   `.py` is NOT a pre-edit backup. Git HEAD is.
8. **PI's dirty flag does not trip on clone-driven child changes.** After
   clone surgery, build the save list from every suspect that OWNS an
   affected instance, never from the Dirty column — 47 tools would have
   silently reverted on boot otherwise (externaltox-revert hazard).
9. **PI's release scrub is tag-gated by history.** The generic rules
   (clear syncfile-marked file refs; sever out-of-candidate clones) were
   added 2026-08-21 in `CompReleaseManager.prepare()` — keep them when
   touching PI. `prerelease_all` is also guarded against candidates with
   no custom pages.
10. **`mod()` is path-relative, not search-up** — `mod('FNSCommand')`
    from inside a sibling COMP fails; use `mod('../FNSCommand')`.

---

## Operations

**Health check** (run after anything ExtUtils/command related):

```python
m = op('/FNSTools/CustomParTools/QuickExt/extutils_distributor').module
m.survey()            # healthy=True or a precise list of what is wrong
m.rollout(apply=True) # fixes: clone links, dock drift, slim modules
```

**Command inventory:** `op.FNS_COMMANDREGISTRY.Commands()` /
`.Run(key)` / status par on `/sys/FNS_CommandRegistry`.
Baseline: **81 commands from 42 owners** (see
`docs/CommandRegistryCandidates.md` for what maps to what and what was
deliberately skipped).

**Saving:** the suspect regime (PI `Save()` per owner, leaves first,
`/FNSTools` root last). PreviewPanel25 and private_investigator1 persist
via their OWN externaltox pars, not PI's table. mapTables rides the root
tox.

**Debugging "my command doesn't show":**
1. `op.FNS_COMMANDREGISTRY` resolves? (No launcher companion → nothing
   surfaces, by design.)
2. Method decorated AND promoted (uppercase)? Tool ext compiles?
3. `'fnscommands' in tool.tags`? If not, the announcer's guard didn't
   see your commands at +60 frames — call
   `op('ExtUtils/FNSCommandAnnouncer').Announce()` and check its return.
4. Row present but stale after an edit → `Announce()` again (ext reinit
   does NOT re-register since the legs were removed).
5. `/sys`-owned rows missing after a rescan → trap #3.
