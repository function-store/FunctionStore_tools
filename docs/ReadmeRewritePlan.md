# P1 — README Rewrite Plan

Rewrite the root `README.md` (untouched since 2025-05, still describes the
2023 monolith) around the v3 product. Adoption-critical: it is the first
thing every prospective user sees and it currently contradicts the actual
product.

## Decisions (2026-08-21, owner)

- **README defers to the website + bucket** for installation. It is a
  landing page, not a manual.
- **GitHub Releases will probably still host the bootstrapper**
  (`FNSTools.tox`) — so ONE download badge pointing at the latest-release
  `FNSTools.tox` artifact is fine. No other release-artifact links.
- **The wiki will probably be retired** — the README must NOT deep-link
  wiki pages. Link the website for docs instead.
- Native installers are deferred (`docs/NativeInstallerDecision.md`) — do
  not promise `.exe`/`.dmg`.

## Structure

1. **Hero**: what FNSTools is — v3, 46 modular packages (7 core + 39
   tools), pick-and-choose via the in-TD configurator. New `FNSLogo` art
   (already in `icons/`). One configurator screenshot.
2. **Install** (short): drag `FNSTools.tox` into any project → it
   bootstraps from the store. Badge → latest release `FNSTools.tox`.
   "Full instructions and alternatives" → website link. State the real
   minimum TD version (2025 build — confirm exact number against what the
   toolkit actually requires before writing it).
3. **Updates** (2–3 lines): the updater checks the store; per-package
   updates; settings survive via config roaming.
4. **Config scope** (2–3 lines): settings roam machine-globally by
   default; `Configscope` can pin a project to `.toe`-only.
5. **Mac notes**: carry over the existing section, verify it is still
   accurate (hotkey `Alt`→`Cmd` mapping, any tools that don't work).
6. **Community/credits**: keep the existing contributors, Patreon,
   Discord, InSession stream copy — it is good and current-ish; verify
   links.

## Kill list

- Both 2023 badges (`FunctionStore_tools_2023.tox`, `FNS_TDDefault_2023.toe`)
  and the downloads counter (points at old artifacts).
- "TouchDesigner.2023.11880" requirement.
- The 2023 install steps (startup-file dance, clear-script-errors note —
  re-verify whether any of it still applies to v3 before deleting the
  advice outright; if the startup-file suggestion still holds, keep it as
  one line).
- All wiki deep-links (installation, per-tool pages, Alt-RightClick wiki
  shortcuts note — check whether that hotkey now opens something else).
- The legacy "Self-Update Feature" and "Syncing/Externalizing" sections —
  superseded by the updater + config-roaming reality; replace with the
  short sections above.

## Sources for correct copy

- `website/` — the current, correct product copy.
- `docs/ConfiguratorDistribution.md` — install/update contracts.
- `docs/ProductAdoptionAudit.md` §1 — verified product facts (package
  counts, rails, bucket).

## Verification

- Every link resolves (website, release badge, Discord, Patreon, credits).
- Zero occurrences of "2023" (except deliberate history, if any).
- No wiki links.
- Rendered preview checked (GitHub-flavored markdown).
