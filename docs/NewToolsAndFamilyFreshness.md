---
status: landed
summary: Update never fetched family operators, the installer never re-fetched a recorded one whose file was missing, and nothing told a user that a release added tools. Backlog for fixing all three, with the first-install rules the new-tools notice must keep.
since: 2026-09-25
---

# New tools, and family operators that stay current

Field report, 2026-09-25 (owner, on a second project): after pressing
Update, the FNS tab showed nothing new, although every family operator was
ticked in the picker. Uninstalling and reinstalling the family did not bring
them all back. And the question behind it: how does anyone learn that a
release added tools?

## What was wrong

1. **Update never fetched a family operator.** An FNS family member is
   installed as a record only (placement `none`): nothing is placed, the
   tox waits in the store and the family folder mirrors it. `Compare()`
   reported every such member as `component` and never as an update, so an
   update pass never downloaded its new version. The family folder mirrors
   what the store holds, so members stayed at whatever version first
   landed, and ones that never reached the store never appeared.
2. **The installer never re-fetched a recorded member whose file was
   missing.** `ResolvePlan` treats a `none` package as present when the
   install record names it, and `to_fetch` only took steps that were
   neither on disk nor present. A member recorded on this machine but
   absent from the store (a store cleaned, another machine's record) was
   planned as present and never downloaded.
3. **Nothing announced new tools.** Update checks installed packages only.
   Release `notices` are hand-written and rare, and the picker's New filter
   shows only to someone who goes looking.

## The backlog

- [x] **A. The installer fetches a recorded family member with no file.**
      `to_fetch` includes a `none` step whose artifact is not in the store,
      present or not.
- [x] **B. Update keeps family members current in the store.** `Compare()`
      reports a recorded `none` member as an update when its store copy is
      missing or its bytes differ from the manifest. The update pass
      fetches it, the apply step records it (nothing to replace), and the
      family sync that already ends every pass mirrors it into the folder.
      Gated members follow the existing gated-skip rule.
- [x] **C. The picker announces tools this machine has not been shown.**
      - "Shown" is machine-wide, in `<palette>/FNSTools/config/seen_packages.json`
        (served picker; the installer reads and writes it), and in the
        browser's `localStorage` on the site and the standalone.
      - Opening the picker with unseen tools shows a dismissable "New
        since you last looked" dialog: the tools as small cards with their
        release note and a tick, "Add the ticked ones" and "Not now". Either
        button marks them shown.
      - Unseen tools keep a New badge on their card until the next release.
- [x] **D. The console's Install & remove tab carries the count,** the way
      the Updates tab already carries its count.

## First installs (owner: "watch out for first installs")

A new user must never be greeted with eighty "new" tools. The rules:

- **A bootstrap's first run** (`FNS_FIRSTRUN`) and **a first visit to the
  site** mark every current tool as shown and show no dialog. The guided
  setup is their introduction.
- **A first install that never opened this picker** (TDX Launcher Ultra,
  the paste rail, any headless `Install` with a selection file) counts as
  a first run too: whatever picked its tools was the introduction.
  `Install()` asks the picker's own question (`_isFirstRun`, no tool in the
  target yet) *before* installing, and afterwards `RecordFirstInstall`
  marks every current non-preview tool as shown, only while the machine
  has no seen file. Asking afterwards is too late: the root then holds
  tools and reads as an existing install with no record (field report
  2026-10-06, a fresh machine installing through TDXLU was greeted with
  the release line's new tools).
- **An existing install with no seen file yet** (everyone on the release
  that introduces it) starts from what they already know: every tool is
  shown except the ones the release line introduced (`whatsnew` starts
  "new package") that they have not installed. So an upgrading user sees
  the genuinely new tools once, and nobody sees the whole catalog.
- The dialog never opens during the guided setup, over another dialog, or
  inside a project that is locked as a source checkout.
- **A Patreon tool the viewer cannot get is never news** (owner,
  2026-09-25: "don't pester them"). Signed out, or without the tier, the
  dialog leaves it out and opens only if something free or owned remains;
  the console's count leaves it out too. It is not marked shown, so it is
  announced once the account holds it; its card keeps the New badge.
- **It is a preference** (owner, 2026-09-25). The window carries "Show
  this window when tools are added"; unticked, it never opens by itself
  (the record's `announce: false` when served, `fns.announce` in the
  browser elsewhere). The New filter still lists the tools, and with it
  on the results line shows the setting, so the way back is findable.

## Verified (2026-09-25)

- **B**: `Compare()` on a scratch root recording ComplexMix and
  FNS_RandomCHOP reported both as updates with the family note (the store
  held neither the one nor the current bytes of the other).
- **C and D**: `/newtools.json` and `/manifest.js` answered through the
  dev installer's request handler, and the machine record was written from
  what the project holds. Rendered headless: a first site visit opened the
  guided setup, not the dialog, and recorded all 82 tools as shown; a
  returning visitor with no record saw the 17 tools this release line
  introduced; the served dialog listed the installer's unseen tools.
- **A** is pinned in tests/test_new_tools.py; the live path needs a real
  install on a machine whose store lacks a recorded member.

## Verified (2026-10-06): a headless first install

The patched `InstallerExt` ran in TD against the live store manifest (68
pickable tools, 14 previews), with `InstallPlan` stubbed to create the
picked tool's COMP and the seen file redirected to a scratch folder:

- **Empty target, no seen file:** first run before the install, not after
  (the field bug's condition). The install wrote a record of all 68 tools,
  no previews, and `UnseenTools` then returned nothing.
- **Target already holding a tool, no seen file:** the install wrote no
  record, and `UnseenTools` returned the release line's 10 introduced
  tools, as before.
