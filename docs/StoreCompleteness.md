---
status: in-force
summary: The machine's store holds the whole release, not only what was installed -- Keepstore on the updater (default on) mirrors the rest after every install and update pass, so Pick Tools works offline and a full mirror's completion is the one hook the FNS operator family will feed from.
since: 2026-09-17
---

# A complete store

**What it is.** `FNS_Updater` gains a toggle, **Keep the Whole Release in
the Store** (`Keepstore`, default on). With it on, every install (picker,
pasted script, the silent "Always Set Up Like Last Time" rail) and every
update pass finishes by mirroring the rest of the release into the
machine's store, `<userPaletteFolder>/FNSTools/store`: the free
artifacts (52 packages, 11.5 MB on 2026-09-17), plus the gated ones the
account is entitled to. Off, only what is installed is ever fetched, which
is what the picker did on its own.

## Why

- **Offline afterwards.** The picker downloads exactly the selection it
  installs, so a machine that never pulsed Refresh Store held only that.
  Adding or re-adding a tool later needed the network again. A complete
  store makes Pick Tools work with none.
- **What the store can offer is on disk.** Store-backed op alternatives
  (`docs/OpAlternatives.md`, layer 2) are offered only from artifacts
  already in the store; nothing is fetched on demand, by design. A complete
  store is what makes every alternative the manifest knows appear on every
  machine, and the same will hold for the FNS operator family (below).
- **Cheap.** 11.5 MB for everything free is less than one movie file, and a
  refresh fetches only artifacts whose bytes differ, so after the first
  mirror it is a manifest fetch and a hash walk.

## Where it runs, and where it never does

- The installer calls `FNS_Updater.KeepStore()` five frames after `Install()`
  returned, on every rail. The picker's done text says so ("the rest of the
  release downloads in the background, for offline use").
- The updater calls it itself after an **update** pass has reported.
- `KeepStore()` refuses while a job runs (the updater accepts one job at a
  time) and when the toggle is off, and **nothing chains after a refresh**,
  so a mirror can never re-trigger itself.
- The Refresh Store pulse is unchanged: a full mirror by hand.

## The one hook, and the operator family

A full mirror's completion (`names is None`, nothing failed) calls exactly
one method, `ExtUpdater._afterStoreComplete(status)`. Today it logs. It is
the seam the FNS operator family plan needs
(`docs/OperatorFamilyFromStore.md`, success criterion 4: the updater mirrors
every member whose tox is in the store into the TDFam family folder with
sidecars, after download, update and remove). With Keepstore on, "every
member whose tox is in the store" is every member, so the FNS tab in the
OP Create dialog is complete offline for the same reason Pick Tools is,
and the family sync has one place to run from instead of three.

## Limits

- The slow-CDN case (a Mac measured at 5 to 8 s per request, 2026-09-16)
  makes the first mirror several minutes of background traffic right after
  a fresh install; it competes with nothing, and the updater's Status shows
  it. A Cloudflare cache rule for the artifacts is the fix at the source.
- The toggle lives on the updater COMP, so an existing install gets it when
  its updater is replaced by an update pass (the updater compares its own
  `Pkgversion`); until then `_parBool('Keepstore', True)` reads a missing
  par as on.

## The picker checks the catalog (2026-09-17)

A store that already held a manifest was served to the embedded picker
as-is: the installer fetched a catalog only when the store had none, so a
machine whose store predated a release kept offering the old package list
(field report on v3.2.26, whose new packages did not appear). Serving a
store manifest now starts a manifest-only refresh, at most once a minute
(`InstallerExt._checkManifest`), and the page asks `/manifest/release`
whether the release moved. It reloads itself when the reader has not
picked or opened anything since the page loaded, and otherwise shows a
note with a Reload button.

The updater runs one store job at a time and refuses a second, so an
Install clicked during that check (or during the Keepstore mirror) used to
end in "Download failed: unknown". An install's download is now queued
behind a running job (`_fetchSelection`, `fetchWhenIdle`) and `/status`
reports it as fetching until it starts.
