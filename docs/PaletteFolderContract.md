---
status: in-force
summary: The toolkit's machine-wide folder in the TouchDesigner user palette is `FNSTools`, replacing `FNStools_ext`. One folder, one migration, one flat family folder (`FNSTools/FNS`) that both TDFam and TD's own palette read. The launcher (TDXLU) derives the same folder independently and follows the same contract.
since: 2026-09-18
---

# The palette folder: `<user palette>/FNSTools`

Owner, 2026-09-18: "currently FNSTools externalizes many things to
FNStools_ext folder in the palette. We want to retire that folder and just
use FNSTools. Comparatively, the family operators should end up in
FNSTools/FNS, no subfolder for categories, they are decided by their own
manifest."

## The contract

`<user palette>` is `app.userPaletteFolder` (TouchDesigner) or the
launcher's `default_user_palette_dir()`. Both products derive the folder
below on their own; neither asks the other.

| Path | What it is | Owner |
|---|---|---|
| `FNSTools/` | the toolkit's machine-wide folder | shared |
| `FNSTools/store/` | flat mirror of the bucket, one tox per package plus `manifest.json` | FNS_Updater, FNS_Installer, launcher stocking |
| `FNSTools/config/FNStools_config.json` | roaming settings | FNS_ConfigRegistry |
| `FNSTools/config/gate-session.json` | the shared sign-in (docs/TDXLUGateIntegration.md G7) | FNS_Updater auth, launcher |
| `FNSTools/config/command-curation.json`, `fns_remote.json` | per-tool machine config | FNS_CommandPalette, FNS_Remote |
| `FNSTools/tables/` | the ExternalTables of ResetPLS, OpMenuMods, ExprHotStrings, HotkeyManager | those tools |
| `FNSTools/OpTemplates/` | the global template library | FNS_OpTemplates |
| `FNSTools/selection.json` | the installer's last selection | FNS_Installer, launcher |
| `FNSTools/FNS/` | the FNS operator family: `<Name>.tox` + `<Name>.json` sidecar, flat | FNS_Updater |

Everything under the root keeps the relative layout it had under
`FNStools_ext`, with one exception: the family.

### The family folder is flat, and it is the palette copy

Before: TDFam read `FNStools_ext/family/FNS/<op_group>/<pkg>_<version>.tox`
(a machine contract) and a second, human copy was mirrored into
`FNStools_ext/FNS/<Name>.tox` for TD's palette. Now there is ONE folder,
`FNSTools/FNS/`, and both read it:

- the file is the tool's PUBLIC name (`RandomCHOP.tox`, not
  `FNS_RandomCHOP_1.0.0.tox`), with `RandomCHOP.json` beside it;
- the sidecar is TDFam's own shape (`OpInfo`, `ParRetain`, `StateRetain`,
  `Shortcuts`); `OpInfo.op_group` is the category and `OpInfo.op_version`
  the version. There are no category subfolders.
- TDFam takes a loose file at the folder root as "no category" and reads
  the group from the sidecar (`OpFamRegistryExt` line 833:
  `op_info.get('op_group') or group_index.get(normalized)`); a file its
  naming regex does not match parses as `(stem, None)` and the version
  comes from the sidecar (`OpFamRegistryExt` line 857). Measured on the
  vendored TDFam in FNS_OpFamily, 2026-09-18.
- the folder is derived from the store and pruned: anything else in it is
  removed. Never hand-place a tox there.
- after every sync `paletteData.json` is rebuilt and TD's palette DAT is
  pulsed, so the folder shows in TD's Palette as `FNSTools > FNS`.

## Migration

Whoever runs first renames the legacy folder into place:

1. if `<palette>/FNSTools` does not exist and a folder whose name is
   `fnstools_ext` in any casing does, `os.rename` it to `FNSTools`;
2. if BOTH exist (a race, or an old launcher recreated the legacy folder),
   move every entry of the legacy folder that has no namesake in the new
   one; a FOLDER both sides hold is merged the same way one level down
   and removed once empty; a FILE both sides hold stays as the new side
   has it, and the legacy copy is kept aside at the same relative path
   under `FNSTools/legacy_FNStools_ext/` (since 2026-09-25; it used to be
   deleted, but the new side's file can be a seed while the legacy one is
   the user's work, and OpTemplates adopts from there); the legacy folder
   is deleted when it is empty;
3. every entry is tried on its own: one that refuses to move is left for
   the next run and never stops the others. A rename of the whole folder
   that fails leaves the legacy folder in use for that session;
4. the updater additionally removes the old `family/` tree (derived, so
   nothing is lost) and lets the next sync fill `FNS/`.

Both refinements in 2 and 3 were paid for on the first live run
(2026-09-18): TDFam's Folder DAT holds the old `family/FNS` tree open, so
the whole-folder rename failed, and a merge that stopped at that entry left
the store behind; and OpTemplates seeds its library when its file is
missing, so it had created `FNSTools/OpTemplates/OPTemplates1.tox` before
the merge reached the legacy one, and an entry-level rule then kept the
user's real library out. (That machine's library was restored by hand.)

Verified live after the fix, 2026-09-18: the legacy folder is gone, TDFam's
folder cache lists the seven members keyed by `op_type` with group and
version from the sidecars, and `GetMasterOps('FNS')` (the FNS tab's rows)
carries them all.

The toolkit runs 1 to 3 from every reader of the folder (`_fnsPaletteRoot()`
in each extension: they cannot share a module and the file the reader
wants may already be needed before the updater has initialised); 4 runs in
`FNS_Updater`. The launcher runs 1 to 3 in `fns_store.rs`.

Transitional: a launcher older than this contract keeps deriving
`FNStools_ext`; its writes (a stocked store, a selection) are pulled into
`FNSTools` by step 2 on the toolkit's next start.

## Backlog (2026-09-18)

Toolkit, this repo:

- [x] `FNS_Updater/ExtUpdater.py`: root resolver + migration, `StoreFolder`
      default, family folder = `FNSTools/FNS`, one sync (public names, TDFam
      sidecar), palette index rebuild kept
- [x] `FNS_Updater/ExtAuth.py`: storage dir, shared session path
- [x] `packaging/InstallerExt.py`: store, config subpath, selection.json
- [x] `FNS_ConfigRegistry/ConfigRegistryExt.py` (+ the OpenExt copy,
      `callbacks_template.py`)
- [x] `FNS_Remote/FNSRemoteExt.py`, `FNS_CommandPalette/CommandCuration.py`,
      `OpTemplates/OpTemplateExt.py`, `packaging/release_one.py`
- [x] live parameter expressions (14, swept 2026-09-18): FNS_Updater
      fileDownloader, FNS_OpFamily `Opfolder`, ResetPLS / OpMenuMods /
      ExprHotStrings `ExternalTables.Foldername` + table file exprs,
      HotkeyManager table exprs, OpTemplates `OPTemplates1.externaltox`,
      CustomParTools `extTemplate.file`, root `parexec1`
- [x] tests: `tests/test_palette_mirror.py` rewritten for the one folder,
      `tests/test_palette_root.py` for the resolver
- [x] docs, skills (`fns-config-scope`, `fns-packaging`), `packaging/README.md`,
      `packaging/docs/*.md`, `parameters.json` help strings, release notes
- [ ] release: the touched packages plus the rails (Guided Release)

Launcher, `C:/VJ/TD/Projects/TDXLPP` (landed by the tdxlpp session on
2026-09-18 in its working tree, uncommitted; `fns_ext_dir()` became
`fns_palette_dir()`, three unit tests cover fresh / rename / merge, and
`selection.json` moved to the root; the launcher release is sequenced after
the toolkit rail):

- [x] `src-tauri/src/fns_store.rs`: `fns_ext_dir()` becomes the resolver
      above (prefer `FNSTools`, migrate legacy, case-insensitive)
- [x] `src-tauri/src/licensing.rs` comment, `src/FnsPanel.tsx` paste
      snippet, `demo/mock/fns.ts`, docs (`fns-integration.md`, `fns-gate.md`,
      `fns-remote.md`, `fns-plus-capabilities.md`, README)
