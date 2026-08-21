# P6 — Native Installer Decision (+ pip-rail cleanup)

**DECIDED 2026-08-21: Option B — defer.** No `.exe`/`.dmg` installers for
now. The one-drop `FNSTools.tox` bootstrapper is the official install rail.
Strike the native-installer promise from docs and website until it is real.

## Rationale

- The audience already runs TouchDesigner; dragging a `.tox` into a network
  is a gesture they know. A native installer adds little friction removal.
- Code-signing burden is real: Windows cert ≈ $100–400/yr; macOS
  notarization requires the $99/yr Apple developer account. **Unsigned**
  installers throw OS warnings that hurt adoption more than having no
  installer at all.
- A second release artifact per version = permanent maintenance overhead.

## Revisit triggers

- Audience extends meaningfully beyond TD-savvy users.
- Derivative ships a native packaging system (in which case adopt *that*
  rail, not a custom installer — the manifest/package contracts are
  packaging-system-agnostic by design; see `ConfiguratorDistribution.md`).

## Doc edits to execute

All in one pass; no code changes.

1. **`docs/ConfiguratorDistribution.md`**
   - Intro (~lines 9–10): "native `.exe`/`.dmg` installers are the
     bootstrap" → the one-drop `FNSTools.tox` is the bootstrap; native
     installers deferred (link this doc).
   - §4.2 revision note (~lines 309–310): same correction — delivery is
     bucket + one-drop tox; ".exe/.dmg" removed or marked deferred.
   - Owner quote block (~lines 561–572): keep the quote as history, add a
     dated note that the decision landed as "deferred" (this doc).
2. **Pip-rail cleanup** (stale spots that still present pip as live):
   - ~line 339: remove/strike "a `pip install fns-tool-a fns-tool-b` line
     (§3 route)".
   - ~line 426: remove/strike "Optional: pip marker-package rail on top
     (§3)".
   - §3 header already says SUPERSEDED — leave the section as the decision
     record.
3. **`docs/UvPackagingResearch.md`**: add a tombstone header — research
   only, the pip/uv rail was rejected 2026-08-13
   (`ConfiguratorDistribution.md` §3/§4.2); revisit only if TD ships a
   native pip/uv-based packaging system.
4. **Website**: audit copy for any `.exe`/`.dmg` promise; align with the
   one-drop rail. (Separate repo/folder: `website/`.)

## Success criteria

- Zero remaining promises of native installers in docs or website.
- Zero remaining text presenting pip as a live delivery option.
- The decision + revisit triggers findable from `ConfiguratorDistribution.md`.
