---
status: open
summary: Improvement backlog for CookBar (Anton Heestand's Cook Bar, adopted 2026-10-07) - a thin extension with commands, keeping the user's project clean on save and uninstall, and making the bars readable at any scale.
since: 2026-10-07
verified: 2026-10-07
---

# CookBar backlog

CookBar was adopted on 2026-10-07 (`0bcbd3b3`), got its toolbar button and the
Global Hog CHOP on 2026-10-07 (`eba1b793`), and dims annotation backs while it
is on (`bc86ced0`). This is the list of what could come next, in the order I
would do it. Each item says what was measured and what is only expected.

## A. A thin extension, and commands on it (asked for)

CookBar has no extension today: its logic is the original's module DAT
(`text_funcs`) and callback DATs. Commands need one.

- **A1. `CookBarExt`, slim.** A small extension DAT with the slim ExtUtils
  clone (`FNS_CustomParTools/QuickExt/ExtUtilsMinimal`) docked to it,
  announcing its commands from `onInitTD` after 60 frames, the way FNS_Misc
  and the other slim tools do. It calls into `text_funcs` and holds no
  state of its own, so the tool keeps working the way it does now.
- **A2. Commands.**
  - *Toggle cook bar*, with a state chip from `Active`.
  - *Open Global Hog CHOP* (the right-click action).
  - *Toggle Global Hog CHOP*, hidden, with a state chip. FNS_Misc had this
    command as "Toggle hog" and lost it when the Hog moved here, so this puts
    it back where the Hog now lives.
- **A3. The extension buys a teardown hook** that B2 needs.

**Done 2026-10-07.** `CookBarExt` with the slim ExtUtils docked (copied from
FNS_Misc's clone, cloning paused for the copy). Registered:
`CookBar#togglecookbar` (chip from `BarActive`), `CookBar#openhog`,
`CookBar#togglehog` (hidden, chip from `HogActive`). The extension holds no
state; `putBack` and `reapply` call into `text_funcs`.

## B. Leave the user's project the way it was

While it is on, CookBar changes the network you are viewing: a hidden Select
TOP and a self-destructing DAT, the display flags of that network's TOPs, and
its annotations' back alpha. Leaving the network or switching off puts all of
it back (verified 2026-10-07). Two paths do not.

- **B1. Saving the project while the bar is on.** Nothing in CookBar reacts to
  a save (measured: no Execute DAT has `projectpresave` or `projectpostsave`
  on). The .toe is written with the display flags off and the annotations
  dimmed. The Select TOP and its DAT remove themselves when the project opens
  without CookBar, but the flags and the alpha stay changed. Fix: an Execute
  DAT that restores on pre-save and re-applies on post-save.
- **B2. Removing CookBar while it is on** (uninstall, or an update reloading
  it). Nothing restores either. An extension's `onDestroyTD` runs inside
  `destroy()` with the network still readable (measured on TD 2025.33070, see
  `.claude/rules/td-python.md`), so A1 can restore there. It also runs on a
  plain reinit, which nothing inside the call tells apart; re-applying a
  frame later covers that case.
- **B3. A Hog left on.** The Global Hog CHOP exists to eat frame time, and
  nothing on screen says it is on once its parameter window is closed. Tint
  the toolbar button, or show it in the button's state, while the Hog is
  active. Not measured yet: whether the Hog cooks at all while nothing pulls
  it, which decides how loudly this needs saying.

**B1, B2, B3 done 2026-10-07.**

- B1: `execute_save` (pre/post-save) calls `beforeSave` and `afterSave`.
  Measured on /project1 with the bar on: pre-save put the annotations back
  to 1.0 / 0.747 / 1.0 and removed the Select TOP while Active stayed on;
  post-save dimmed them to 0.2 again and put the Select TOP back.
- B2: `onDestroyTD` calls `putBack`. Measured: immediately after
  `initializeExtensions()` the annotations were back at their originals and
  the Select TOP gone; a frame later the new instance had re-applied. A real
  uninstall was not exercised.
- B3: the button's background turns red (0.75, 0.15, 0.15) while
  `hog_global` is active, by expression on the icon Text COMP. Measured
  without letting the Hog cook.
- Found after B2 landed: every extension reinit left a "Cook dependency
  loop" warning on CookBar until something forced a recook. `onDestroyTD`
  runs inside the owner's own cook, and its restore path wrote the owner's
  storage (`store()` of the cleared records, even when they were already
  empty). Fixed: the restore helpers write only when there is something to
  clear, `onDestroyTD` restores with `clear=False` and `forgetRestored`
  clears the records a frame later, and the new instance re-applies at +2
  frames. Measured: the warning now shows for an instant during the reinit
  and clears by itself; with the bar on, the network was put back and
  re-applied across a reinit.
- Right-click on the toolbar button opens CookBar's own parameters, the
  convention most toolbar tools follow (QuickTime, Remote, ResetPLS,
  VSCode, MIDILearn, HydroHomie, OpTemplates). The Hog moved to
  Ctrl+right-click and to an Open Global Hog CHOP pulse on the CookBar page.
  Ctrl is read from the OS through the shared FNSModifiers module: the
  panel's own ctrl value is latched when that panel is clicked, and the
  button is clicked through the toolbar's mirror, so the first
  Ctrl+right-click opened the parameters and only the second the Hog
  (reported by the owner, 2026-10-07).
  That was not the cause: it still took two clicks. The right-click
  watcher fired on `rstate` off-to-on, and on this toggle button `rstate`
  flips on every right-click like a switch (measured: sitting at 1 between
  clicks), so every second click fired. It now watches `rselect`, 1 while
  the right button is down. The OS Ctrl check stays: it is correct either way.
  Confirmed by the owner with real clicks: one Ctrl+right-click opens the Hog.

## C. Make the bars say more

- **C1. Adjustable scale.** A full bar is 1 ms of cook time and 100 million
  pixel channels of GPU memory, both fixed in the shader. In a heavy network
  most bars sit full; in a light one, most are empty. Two parameters
  (full-scale ms, full-scale GPU memory) passed to the shader as uniforms.
- **C2. Smoothing or a slower update.** Cook times jump from frame to frame,
  and the scan costs 1.5 to 2 ms a frame over a network the size of
  `/FNSTools` (measured, Max OPs 50). Averaging over a few frames, or
  scanning every Nth frame, makes the bars steadier and divides that cost.
- **C3. Follow the network you are working in.** The original reads
  `ui.panes[0]`, the first pane. With one pane that is the same thing (one
  pane open, measured); with split panes the bars can draw in a network you
  are not looking at. Follow the current network editor pane.

  **Done 2026-10-07.** `text_funcs.currentPane()`: the current pane when it is
  an open network editor, else the pane already followed (by id), else the
  first open network editor; a pane change recomputes the view size. Measured
  on the way: `ui.panes.current` named a CLOSED pane (`pane2`, `open` False,
  absent from `ui.panes`), and a closed floating pane stays in `ui.panes`
  with `open` False, so the open check is required. Not exercised: the bar
  moving to a second pane when focus moves there (focus cannot be set from a
  script; a floating pane created by script did not become current).
- **C3b. Bars in every pane at once: considered, declined 2026-10-07.** One
  drawing unit (scan, table, shader, output) per open network editor, with
  the toolbar button as the master switch and an optional per-pane navbar
  toggle. Declined by the owner: following the active pane covers the usual
  case. The reasoning, kept so it is not redone: the bars are a backdrop,
  and a network's backdrop comes from that network's displayed TOPs, so it
  belongs to the network, not the pane (the pane API has show/hide toggles
  such as `showBackdropTOPs`, no per-pane image). Two panes on the same
  network can never show different bars, and every extra unit adds its own
  scan (1.5 to 2 ms in a network the size of /FNSTools) and shader render.
  If it comes back, do C2 first.
- **C4. A paused timeline.** The original greys Active out while the
  timeline is paused. Showing the last measured bars while paused is
  possible; low value, since nothing cooks.
- **C5. CPU and GPU apart.** One bar adds CPU and GPU time. A two-tone bar
  would show which side is expensive. A shader change; maybe.

## D. Housekeeping

- **D1. Callback names.** The DATs use the pre-2018 names (`frameStart`,
  `create`, `playState`, `valueChange(par, val, prev)`). They still fire on
  2025.33070 (verified today). Port them to the `on...` names whenever those
  DATs are touched for something else.
- **D2. Remember preferences.** A ConfigRegistry host could carry Max OPs,
  Annotation Alpha and the C1 scales across projects. Never `Active`: an
  overlay that switches itself on in every project is a surprise. Load
  `/fns-config-scope` first.
- **D3. A hotkey to toggle**, through the hotkey conformance flow, with no
  default binding.

## Order

A1 and A2 first (asked for). B1 and B2 next: they keep CookBar from changing
a user's project behind their back, and B2 needs A1's extension anyway.
Then B3 with A2's hidden Hog command, then C1 and C2 together (both touch
the scan and the shader), then C3. C4, C5 and D are optional.

## Measured 2026-10-07

| What | Result |
|---|---|
| Cooks while off | 0 for the tool's DATs (the per-frame Execute DATs are gated by Active) |
| Scan cost while on, /FNSTools (125 children, Max OPs 50) | 1.5 to 2 ms a frame, after the `childrenGPUMemory()` change (was 9.3 ms) |
| Panes open | 1 network editor (`pane1`, `/project1`) |
| Save hooks on CookBar's Execute DATs | none |
| Legacy callback names | fire on 2025.33070 |
| Max OPs cost, 1536x700 bar image, synthetic op table | shader GPU 0.10 ms at 50, 0.25 ms at 100, 1.40 ms at 250; table-to-CHOP about 0.1 ms CPU at every count. The scan's own Python walks every operator in the network whatever Max OPs is. |
| Max OPs above 250 | was allowed (slider to 100, no upper clamp) while the shader arrays hold 250; clamped at 250 since |
