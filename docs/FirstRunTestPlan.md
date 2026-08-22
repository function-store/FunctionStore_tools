---
status: open
summary: Manual end-to-end test plan for the first-run experience — drop welcome, guided picker, "Set up like last time", CMS Recommended, dev-folder guard. Run on a clean TD before the next release.
since: unreleased 2026-08-22 (covers work landed that day; automated checks passed, the cold user-path runs below are still pending)
---

# First-run experience — end-to-end test plan

What the agent verified on 2026-08-22 was **inside the dev project**
(drop tests in `/sys/quiet`, the page driven through the DOM, installs
into a cooking-disabled container). The runs below are the parts only a
real user path proves: a bare `.toe`, a real drop, a real bucket, a cold
restart. Tick them before the release that ships this.

**Conventions.** "Bare project" = a new, empty `.toe` in a folder that has
no `externalizations.tsv`. "Bootstrap" = the `FNSTools.tox` from
`packaging/dist/` (rebuild with `BuildBootstrap()` after any source
change — Preflight flags a stale one) or, for the release candidate, the
one in `packaging/publish/<release>/`. Between runs that need a *clean
machine*, move `<userPaletteFolder>/FNStools_ext/config/FNStools_config.json`
aside (the whole roaming config) and clear
`<userPaletteFolder>/FNStools_ext/store/` if you want to see the catalog
download.

---

## Run 0 — Preconditions (5 min)

1. In the dev project, Textport:
   `exec(open('packaging/build_installer.py').read()); EnsureDevRails(); EnsureRootEntryPoints(op.FNS)`
   then `BuildInstaller(); BuildBootstrap()`. Both report `exported: True`,
   `errors: 'clean'`.
2. `Preflight()` (see RELEASING.md) shows no stale-rail warning.
3. Open `packaging/dist/FNSTools.tox` size: ~260 KB (it now carries the
   root config host; the pre-2026-08-22 bootstrap was ~215 KB).

## Run 1 — First drop on a clean machine (the headline path)

*Setup:* bare project, roaming config moved aside, store emptied.

1. Drag `FNSTools.tox` into the network editor.
   - **Expect:** within ~2 s, without clicking anything, a floating viewer
     opens with the picker. Title reads **Welcome to FNSTools.**, eyebrow
     **FIRST RUN**, a 3-step strip under the hero (step 1 lit).
   - While the store is empty the list area says *"First run: fetching the
     package catalog from the bucket… this page refreshes itself."* and
     the page reloads itself every ~2.5 s until the catalog lands.
2. The welcome dialog appears over the list with exactly three cards:
   **Recommended** / **Everything** / **Pick my own** (no "Set up like
   last time" — this machine has no record). The Recommended card names
   the count and the first four tools; **nothing on the welcome mentions
   core**.
3. Press **Esc**. Dialog closes, step strip moves to step 2, list is empty
   (0 selected). Reload the panel (root → **Pick Tools**): the welcome
   does **not** reappear in this panel session.
4. Click **Recommended** (reopen via a fresh panel if needed — close the
   viewer, root → Pick Tools). Count shows the recommended number; the
   checked cards match `catalog.json`'s `recommended: true` set.
5. **Review install…** — step strip to 3; plan lists core + the tools;
   core rows say `install (download)` on an empty store. **Install**:
   progress dialog ("Downloading… N done, M to go"), then
   **Installed ✓** with the package list and the hint text; an
   **Open Settings** button is present.
6. Click **Open Settings**: the same panel navigates to the FNS console on
   its Settings tab. (Textport: the installer's `webserver` DAT goes
   `active = False` within ~2 s.)
7. Look at the network: the dropped root holds core + tools, `installed`
   table, `README`, `exec_root_welcome`, `config_callbacks`,
   `FNS_ConfigHost`, `parexec_root_pulses`. `root.fetch('FNS_welcomed')`
   = `'shown'`. No errors on the root (`root.errors(recurse=True)` empty).
8. The toolbar (if FNS_Toolbar was picked) appears at the top of the
   network editor after a frame.
9. **Save** the project (Ctrl+S). Open the roaming config JSON:
   `tools.FNS.state.last_install` exists, `packages` lists every
   installed package, `project` is this `.toe`, `bind` = `embedded`.
10. **Reopen** the project. **Expect:** no picker opens (flag set), no
    errors, tools come back.

**Fail signals:** picker never opens (check the root's `exec_root_welcome`
→ *Create* toggle on; `op.TDResources` exists); welcome opens a second
time after reload; core mentioned on the welcome; `Open Settings` errors
("no FNS console installed yet" means FNS_Console did not land or did
not expose — see `ExposeConsoleHosts`).

## Run 2 — "Set up like last time" (same machine, second project)

*Setup:* right after Run 1 (the roaming config now holds the record).
New bare project in another folder.

1. Drop the bootstrap. Picker opens; welcome shows **four** cards with
   **Set up like last time** first: *"N tools, as in <Run-1 toe> on
   <date>."* (N = tools only; core is not counted.)
2. Before clicking anything: the list behind the dialog already has those
   N tools checked (Esc would land on them).
3. Click **Set up like last time** → **Review install…** → plan shows the
   same tools. **Install**. Settings from Run 1 (e.g. a toolbar layout
   change you made there) re-apply once the tools register.
4. Save this project. Reopen **Run 1's** project, change one tool's
   selection there (Pick Tools → uncheck one → Apply), save. Drop a
   bootstrap into a third bare project: the card now reflects **Run 1's**
   newer state — last writer wins, as documented.

**Variant 2a — bind mode rides along.** In Run 1 set the installer's
**Package Files** to *Shared* before installing; after the save the record
carries `bind: shared`; in Run 2 choosing the card sets the new
installer's Package Files to *Shared* (check the par before Install).
Choosing **Recommended** instead leaves it at *Embedded*.

**Variant 2b — catalog drift.** Edit the roaming JSON by hand: add a fake
name to `packages`. The card says *"(1 no longer in the catalog)"* and the
plan never mentions it.

**Variant 2c — project scope.** In Run 1's project set the root's
**Config Scope** to *project* (confirm dialog → Stay/Push as offered),
save. Check the roaming JSON: `last_install` is **unchanged** (not
rewritten). Drop a bootstrap into a new project whose root you flip to
*project* scope before the picker loads (Pick Tools again after the
flip): **no** "Set up like last time" card.

## Run 3 — Paste rail does not double-trigger

1. On `tools.functionstore.xyz/get/` pick two tools → **Copy install
   script**. Paste into the Textport of a bare project.
2. **Expect:** the bootstrap lands and installs the selection; **no picker
   opens** over it (`root.fetch('FNS_welcomed')` = `'paste'`).
3. Root → **Pick Tools** afterwards opens the console's Install & remove
   tab normally.

## Run 4 — Existing installs are untouched

1. Open a project installed **before** this change (or Run 1's project).
   Root → **Pick Tools**: the console / picker opens with the project's
   tools pre-checked; **no** welcome, **no** step strip, no "last time"
   card (not a first run).
2. Copy the whole root to another project via Ctrl+C / Ctrl+V: no picker
   opens (storage travels with the copy).

## Run 5 — Dev-project guard

*In the dev checkout (this repo).*

1. On `/FNSTools/FNS_Installer` set **Install Into** to a fresh
   cooking-disabled container (`t = op('/sys/quiet').create(baseCOMP,
   'trial'); t.allowCooking = False`), **Selection** to
   `packaging/example-selection.json`, **Package Files** to *This
   project's own folder*, pulse **Plan**.
   - **Expect** (Private Investigator's **DEV** toggle on): Status
     `LOCKED -- Package Files 'project' would write into …/FNStools,
     inside the toolkit's development project (Private Investigator: DEV
     on) …`. **Install** refuses with the same text. Nothing is written
     under `FNStools/`.
2. Set **Package Folder** to a folder outside the project → Plan resolves.
3. Toggle PI's **DEV** off, Plan with the default folder → resolves (the
   guard is the toggle, nothing else). Toggle it back **on**.
4. Reset: Package Files *Embedded*, Package Folder blank, Install Into
   blank, destroy the trial.

## Run 6 — CMS Recommended

1. `cd website && node tools/cms.mjs` → open the URL. Pick a tool, tick
   **Recommended**, ⌘S. `git diff packaging/catalog.json` shows exactly
   one added line (`"recommended": true`) on that package; the list shows
   a `REC` badge. Untick, save: the line is gone.
2. `npm run pages` in `website/` builds clean.
3. In the dev project: `exec(open('packaging/build_manifest.py').read());
   Build()` → `manifest.json` gains/loses the name in `starter`, tools
   only, in manifest order. (Reverting the generated manifest afterwards
   is fine if you are not releasing.)
4. Release → the next bare-project drop's **Recommended** card reflects
   the change. A project served an **older** manifest (no `starter`)
   shows no Recommended card at all, and the welcome still works.

## Run 7 — Cold restart of the dev project

1. Restart TD on the dev project. `/FNSTools` still has
   `exec_root_welcome` (Create on), `config_callbacks`, and
   `FNS_ConfigHost.par.Callback` → `config_callbacks`. No picker opened on
   the dev root (it never welcomes: `externaltox` set).
2. Save the dev project: the dev machine's roaming JSON keeps whatever
   `last_install` it had (the dev root has no `installed` table and
   returns the previous value, never `{}`).

---

## Sign-off

| Run | Result | Date / who |
|---|---|---|
| 0 Preconditions | | |
| 1 First drop, clean machine | | |
| 2 Set up like last time (+2a, 2b, 2c) | | |
| 3 Paste rail | | |
| 4 Existing installs untouched | | |
| 5 Dev-project guard | | |
| 6 CMS Recommended | | |
| 7 Cold restart | | |

When every row is ticked, flip this file's `status` to `landed` and fold
anything learned into `docs/LastInstallRecord.md` / `packaging/README.md`.
