---
status: open
summary: P3 — plan to exercise FNS_Updater's self-update end-to-end. The riskiest untested path in the product; never run.
since: 7842401 2026-08-21
---

# P3 — Updater Self-Update Live Verification Plan

`FNS_Updater` is `kind: core` and self-update is implemented, but it has
never been exercised end-to-end. It is the riskiest untested path in the
product: the updater replacing itself mid-run.

## Harness

A **disposable scratch `.toe`** with FNSTools installed from
`packaging/dist/` — never the dev project. (The `locked` guard should
refuse dev masters anyway; observing that refusal is a free side-test.)

## Steps

1. Serve the staged store locally: copy `packaging/publish/` to a scratch
   dir, `python -m http.server` over it, point the scratch install's
   `Baseurl` at `http://localhost:<port>/`.
2. In the **staged copy only**: bump `FNS_Updater`'s `Pkgversion` in the
   manifest and in the artifact tox (recompute its sha256 for the
   manifest — downloads are hash-verified).
3. `RefreshStore` → `CheckUpdates` → expect FNS_Updater in state `update`.
4. **Read the UPDATER ext BEFORE running the update** and answer the key
   design question: does it order self-update LAST in a batch? A mid-batch
   self-replacement kills the running ext and orphans the queue. If it
   doesn't defer itself to last, that is the bug this test exists to find —
   fix before proceeding.
5. Run `UpdateProject` with FNS_Updater + at least one ordinary tool
   queued.
6. Cold-boot the scratch project afterward; run `CheckUpdates` again.

## Success criteria

- The batch completes: the ordinary tool AND the updater both land.
- The new `Pkgversion` reads live off the installed FNS_Updater COMP.
- A second `CheckUpdates` works post-replacement (the new ext is alive and
  wired).
- No orphaned downloads / stale downloader state.
- Cold boot: updater functional from disk.

## Known traps (vendored TDFileDownloader — all previously paid for)

- A request issued from inside the Web Client DAT's own callback is
  silently dropped (so is its own `queueNext()`) — drive the queue
  yourself; defer every post-download stage a frame.
- A stale `stateDict` entry (keyed url+location, left in GET/WAIT) makes
  later requests for that file return stale state — call `AbortAll()` per
  job.
- A connection that never opens produces NO callback at all — needs a
  stall watchdog, not just an abort handler.

Also: install tests that stage live package copies must use a
cooking-disabled container (`allowCooking = False` BEFORE loading) — a
live registry-master copy otherwise promotes itself to `/sys` and destroys
the running one. In this plan the scratch `.toe` is a real install, so
this applies only if any staging/inspection step loads a tox beside the
running toolkit.

## Deliverable

Test transcript + verdict recorded (append a dated STATUS block to this
doc); any bug found gets fixed and re-verified before the doc is marked
done.
