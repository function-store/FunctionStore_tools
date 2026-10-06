---
status: in-force
summary: "Set up like last time" — the machine's last install roams as state on the toolkit root's own config host; a fresh bootstrap offers it, and applies it unasked only when the root's Always Set Up Like Last Time toggle says so.
since: unreleased 2026-08-22 (landed with the first-run welcome; root host now ships in the bootstrap)
---

# The last-install record

**What it is.** When a project saves, the toolkit root's config host
(canonical `FNS`) writes one extra `state` entry into the roaming config:

```json
"FNS": { "state": { "last_install": {
  "packages": ["AutoRes", "FNS_Toolbar", "..."],
  "project": "MyShow.toe",
  "when": "2026-08-22T21:10:03",
  "bind": "embedded"
}}}
```

Dropping the bootstrap into a *new* project then opens the first-run
welcome with a first card, **Set up like last time** — "12 tools, as in
MyShow.toe on 2026-08-22" — first and lit as the primary choice. Since
2026-09-13 that one click plans and installs: the list is the user's own,
from a project they saved, so the click is the confirmation and the
review dialog is not asked for (the other cards still land on
**Review install… → Install**). The settings half of "my setup" needs no
work at all: the moment those tools register, the roaming config
re-applies their sections, exactly as `docs/ConfiguratorDistribution.md`
promises ("install decides WHAT is in the project; the config layer always
re-applies on top").

## Why this shape

- **Derived, never hand-maintained.** The record is computed on every
  `SaveAll` from the rails' `installed` table (written per package as it
  lands — `InstallerExt.RecordInstalled`). There is no fourth record to
  keep honest beside `installed`, the store manifest and `Pkgversion`; the
  table is the truth and the record is a view of it. A root with no table
  (never installed through the rails: the dev master, a hand-built root)
  returns the *previous* value rather than `{}`, because `SaveAll`
  replaces a tool's section wholesale and a root with nothing to say must
  not erase what another project recorded.
- **State on the root host, not a sidecar file.** `docs/ConfigScope.md`
  refuses palette sidecars, and `docs/FirstRunNudgePlan.md` already fixed
  where machine-global first-run state lives: *"a state entry on the root
  `FNS` host … fires once per machine, not per project, and roams
  correctly."* Last-writer-wins across projects is the config's documented
  semantics — "last time" means the project you saved last, which is the
  mental model the card's label sets.
- **Scope comes for free.** Under `Configscope = project` the snapshot runs
  but the file is never written, the read-back is skipped, and the
  installer's reader refuses too — so no offer appears, and none would
  half-work (the settings would not re-apply there either). Same ruling as
  the nudge plan: acceptable, do not special-case it.
- **Offered, not applied unasked.** "An update pass is not an install pass"
  (`docs/PackagingScheme.md`); a download into someone's project because a
  *different* project once held those tools is exactly the surprise a
  live-show toolkit must not pull. The card pre-selects; the plan step still
  surfaces stale caches, missing artifacts and `SourceLock` refusals.
- **Only on a root with no tools.** The card lives inside the served
  picker's `FNS_FIRSTRUN` branch. "No tools" is measured against the
  manifest since 2026-09-12: no manifest tool (packages minus core) as a
  child of the root or in its install record. Before that the test
  counted every COMP but the three rails, and the root's own
  `FNS_ConfigHost` (shipped in the bootstrap since 2026-08-22, and also a
  catalogued package name) made every root look installed-into, so the
  card had never fired. Core does not count either: the paste rail
  installs core before anything can open, and a root with core and no
  tools is still the user's first look at the picker. Everywhere else served mode pre-checks
  *what this project has* (unchecking reads as removal), and a remembered
  list leaking in there would read as "install these" over a live project.

## Always, without asking (2026-09-16)

The owner asked for the opposite of the offer as an explicit opt-in: a
toggle on the toolkit root, **Always Set Up Like Last Time**
(`Setuplikelast`, on the `FNSTools` page beside the pulses, default off).
With it on, a fresh drop installs the last recorded setup with nothing
to click: no picker, no window, progress as Textport lines. The user
turned it on themselves, on this machine, so the surprise the bullet
above guards against is not one.

- **It roams as an ordinary root par.** The root's host snapshots the
  root's pars (only `Configscope` is excluded), so the toggle travels in
  the same file as the record it acts on, and every new project on the
  machine sets itself up the same way.
- **The welcome reads it from the file, not only the par.** The host that
  restores the root's pars may not have run when the welcome fires (90
  frames after the drop), so `InstallerExt.AutoSetupWanted` reads the
  live par first and then the root's `pars` section of the roaming file
  directly, the way `LastInstall` reads the record. Same scope rule:
  never under project scope, and never without a record.
- **The rail is the picker's card, without the page.**
  `InstallerExt.InstallLastSetup(confirm=True)` writes the selection the
  card would post (record names the release still has, over core, in the
  recorded bind mode; Patreon names held aside and named), then walks
  manifest → artifacts → install, each download waited for by a
  frame-scheduled tick, bounded at ten minutes. It never removes. Any
  stop prints why and points at Pick Tools; anything short of a started
  install makes the welcome fall through to the picker as before.
  Without `confirm` it is a dry run that reports what would land.
- **The flag still moves to `shown`** before the rail starts, so a
  project load never fires it, and the paste rail (flag `paste`) is
  untouched.

## What ships to make it work

The bootstrap now carries the root's config host (`FNS_ConfigHost` in
`BOOTSTRAP_KEEP`, severed from the dev checkout like every stamped host:
`externaltox` cut, `pi_suspect` stripped, `Regstatus` blank). Before this
the shipped root had **no** section in a user's config — `packaging/README`
claimed the root "keeps roaming its own settings" and it did not. The
callbacks DAT (`config_callbacks`) is generated by `EnsureRootEntryPoints`
alongside the pulse forwarder and the welcome DAT, and the host's
`Callback` par is pointed at it there.

## Limits, stated

- The reader (`InstallerExt.LastInstall`) opens the registry's default
  path directly — a bare root has no registry to ask and cannot know a
  master's `Configfile` override. Users who relocate the config get no
  offer; they still get Recommended / Everything / Pick my own.
- Names are filtered against the current manifest and dropped silently
  (every package name changed once already, with no migration path); the
  card says how many fell away.
- `bind` (the `Package Files` mode) rides along and is applied to the
  installer only when this card is chosen; an ordinary selection leaves
  the par alone.
- Core is never part of the record's *offer*: the list is tools only, and
  core is implied by the plan as always.
