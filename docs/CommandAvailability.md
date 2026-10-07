---
status: in-force
summary: 'Command surfaces offer only what the project can run: FNS_CommandRegistry hides commands whose owner is bypassed, has cooking off or declares itself disabled, and FNS_Installer registers one Installer#install-<Package> command per installable package that is not in the project.'
since: 2026-09-27
skill: fns-command-registration
---

# Command availability and install commands

Owner's rule, 2026-09-27, relayed from the TDXLPP launcher session: **a command
surface offers only what the project can actually run.** For a tool that is not
in the project, offer "Install <tool>" instead of nothing. It applies to every
consumer of FNS_CommandRegistry: the native palette, the launcher's quick launch
and its palette sidebar.

Decided by the owner the same day:

1. Unusable commands are **hidden, not greyed**.
2. Install commands are served by FNS_Installer through the registry, one per
   package, so every surface gets identical rows.
3. Packages this account is not entitled to are **omitted**, not shown locked.
4. FNSTools_PRIV owns both halves; the launcher consumes them as served.

## Part 1: the registry hides what cannot run

`Commands()` leaves out every command of an owner that cannot run right now,
evaluated fresh on each call like `state` already is:

| Condition | Reason text |
|---|---|
| the owner COMP is bypassed (`comp.bypass`) | `<tool> is bypassed` |
| the owner or any ancestor has cooking off (`allowCooking` false) | `<tool> has cooking off` |
| the command declares `enabled` and it evaluates false | `<tool> is disabled` |

- **`enabled`** is a new optional spec field, a reference evaluated exactly
  like `state` (same resolver, same owner scope). Truthy or absent means
  enabled. A reference that fails to evaluate counts as enabled and is logged
  once per owner: a broken reference must not make a working tool vanish
  without a trace.
- **Hidden means absent from `Commands()`**, not a flag on the wire. The
  registration is kept, so the command returns the moment the owner is
  un-bypassed; nothing re-registers.
- **`Run(key)` refuses** a hidden command with `{'ok': False, 'unavailable':
  True, 'error': <reason text>}`, so a stale key held by a consumer gets the
  reason instead of a traceback from a tool that is off.
- **An owner that no longer resolves is still pruned**, as today. Only that
  case deletes the registration.
- `hidden: True` (the tool's own "not in the default list") is unchanged and
  independent: consumers that ask for all commands still see hidden-by-tool
  commands of a runnable owner, and never see an unrunnable owner's.

**Consequence every consumer must respect:** absence from `Commands()` no
longer means "not installed". A tool that is present but off is absent too.
"Is package X in this project" is answered by the installer (Part 2), never by
looking for its commands. The launcher's capability lookups (`fns.collect`,
`fns.autosave`) that decide "not installed" move to the installer's
`installed` command; a tool that is present with its commands absent is
reported as "<tool> is off", never as "install it". **`installed` itself
stays free of availability rules**: it reports presence even when the tool
is bypassed or has cooking off.

Registry version: **1.12.0**. The launcher carries a byte-identical mirror of
`FNS_CommandRegistry.tox`; it re-imports the released artifact as with every
registry release.

## Part 2: the installer serves install commands

FNS_Installer registers, beside its existing `install`, `installed` and
`available`, one command per package that is **installable and not present**:

```
id:         install-<Package>          e.g. install-Collect
tool:       Installer                  (the owner's public name)
identity:   Installer#install-Collect  (curation and usage key)
label:      Install <Title>            e.g. Install Collect
help:       the manifest description
method:     CommandInstall, kwargs {package: 'FNS_Collect', confirm: True}
capability: fns.install
surface:    none declared (listed everywhere)
```

`<Package>` is the package's public name (a leading `FNS_` removed), matching
curation identities since registry 1.10.0. Registry ids allow
`[A-Za-z0-9_-]`, at most 48 characters; every current package name fits.

### Which packages get a row

A package gets a row when ALL hold:

- the store manifest lists it with `kind: tool` (core packages install as a
  unit and are never offered singly);
- it is not `nopick` (foreign packages with their own install route);
- it is not an FNS operator family member (`family` in the manifest). Those
  are reached through the FNS tab of the OP Create dialog, and 34 rows would
  swamp a bare `?` list (owner, 2026-09-27);
- it is **not present**: no row for it in the project's `installed` record
  AND no live COMP of that name under the install target. The second check
  covers a copy placed by hand or the dev tree, which has no record;
- this account may install it: `access` is `free`, or the updater's
  `IsEntitled(package)` is true. Anything else is omitted. No updater or no
  auth beside the installer reads as not entitled, the same rule
  `_patreonLocked` already applies.

A present package never gets a row, whatever its state: bypassed and
cooking-off tools are present (Part 1 hides their commands; it must not
invite a reinstall).

### When the list is rebuilt

The installer re-registers its whole command list (the three fixed commands
plus the install rows) at:

- its own init (the existing deferred `_registerLauncherCommands`);
- the end of every install or removal it performs;
- the end of every FNS_Updater store job (`_report`: a refresh, a scoped
  fetch or an update), which asks the sibling installer to re-announce;
- every entitlement change the updater's auth sees: a licence claim or
  renewal, a trial starting or ending, a Patreon link or unlink. Otherwise a
  new supporter would not see their rows until the next store refresh.

Registration is one `Register(owner, specs)` call, so a rebuild replaces the
list atomically and bumps the registry revision once.

### Running one

`CommandInstall(package, confirm=True)` behaves as today, with one change for
the download case. When artifacts must be fetched first, the command no
longer returns and waits to be run again. It queues itself: once the store
job ends it re-runs the same install (the pattern `familyWhenFetched` already
uses for the FNS tab, with its three-minute cap), and it returns:

```
{'ok': True, 'fetching': True, 'package': 'FNS_Collect',
 'text': 'Downloading Collect; it installs when the download finishes'}
```

If the resumed install fails, the result goes to the installer's status line
and log. A click on an install row therefore always either installs, starts
a download that ends in an install, or returns `ok: False` with the reason
(not entitled, source-locked, not in the manifest). It never silently does
nothing.

**One install per package at a time.** While a package's install is queued or
downloading, its row is dropped from the list (a rebuild runs when the queue
starts), and a repeat call with a stale key returns `{'ok': True, 'fetching':
True, 'text': 'Already downloading Collect'}` without queueing a second
install.

### What consumers do

- List the rows like any command. The native palette gives them an `INSTALL`
  badge in their own hue and ranks them with general tool commands, so a
  typed name finds "Install Collect" the way it finds Collect's commands once
  installed.
- **Rows merge across open projects.** The wire key is `<owner path>#id`
  and the installer sits at the same path in every project, so the same
  install row from several open TDs is one command with several targets in the
  launcher's quick launch, which asks for the project. That is intended.
- Favourites, hidden overrides and usage key on `Installer#install-<Package>`
  as on any command. A row disappears once its package is installed; its
  curation and usage entries stay in the files and are simply unmatched.

## Reviewed

The launcher's agent reviewed this on 2026-09-27 and approved both parts. Its
notes are folded in above: rebuild on entitlement changes, one install per
package at a time, `installed` free of availability rules, and rows merging
across projects.

## Open

- Whether "Install <tool>" should also offer core setup ("Install Collect and
  set up FNSTools"). Out of scope here; the rows install minimally, as
  `CommandInstall` already does ([LauncherToolkitBoundary.md](LauncherToolkitBoundary.md)).

## Decided after review

- **Family members are left out** (owner, 2026-09-27, relayed by the
  launcher's agent).
- **The per-tool cap.** The registry keeps `MAX_COMMANDS_PER_TOOL = 24`, and
  an owner tagged `fnscatalog` gets `MAX_CATALOG_COMMANDS = 128`; the
  installer is the only one. The launcher has no per-tool cap of its own
  (only a 40-row limit per typed query), so it needs no exemption. At the
  launcher's request, an owner that offers more than its cap is logged once
  and the `Register()` result carries `dropped` and `cap`, instead of the
  silent drop that hid this in the first place.

## Built

- **Part 1, 2026-09-27.** Registry 1.12.0: `_ownerUnavailable` (bypass, or
  cooking off on the owner or any ancestor) hides every command of the owner
  in `Commands()` and makes `Run` refuse with `unavailable: True` and the
  reason; the optional `enabled` spec field (also accepted from the
  `fns_command` decorator's metadata) hides one command. Verified live on
  `/FNSTools/FNS_OpenExt`: bypassed and cooking-off both hid its commands and
  refused `Run` with "OpenExt is bypassed" / "OpenExt has cooking off", and
  both came back when restored; `enabled` read on, off, a false method, and a
  broken reference as enabled; a non-reference value is refused at
  registration. The master's reinit promoted 1.12.0 into `/sys` with all
  197 commands from 51 owners carried over.
- **Part 2, 2026-09-27.** `InstallerExt._installRows()` builds the rows from
  the store manifest, the install record, the live target and
  `_patreonLocked`; the installer tags itself `fnscatalog`.
  `rebuildInstallCommands()` re-announces, called after `CommandInstall` and
  the picker's `Install()`, by `ExtUpdater.askInstallerToRebuild()` a frame
  after every store job's `_report`, and by
  `ExtAuth._noticeEntitlementChange()`, which runs from `_setStatus` (every
  auth state change passes through it) and acts only when sign-in or the
  entitlement list actually changed. A download queues the package in
  `_installQueue` (its row drops at once) and `installWhenFetched` finishes
  the install when the store job ends, reporting to the status line.
  Verified live:
  - in this dev project every tool is present, so no rows (correct);
  - with the target pointed at `/sys` for one read, 40 rows: all 40 free
    non-family tools, the 7 `preview` ones omitted for an account with no
    entitlements; registering them kept all 43 commands under the
    catalogue cap, and the normal 3 were restored;
  - a plain owner offering 30 commands kept 24 and reported `dropped: 6`;
  - a repeat call for a queued package answered "Already downloading
    Autosave" and its row was dropped;
  - the updater and auth hooks ran without errors.

  - the native palette shows the rows with a coral `INSTALL` badge
    (captured: "install auto" listed Install AutoRes, AutoCombine,
    Autosave and CustomParTools).

  Not verified: a real download followed by the resumed install, which
  needs a project that is not the toolkit source root.
