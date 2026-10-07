---
status: in-force
summary: A package flagged `preview` ships in the release but only the creator's signed-in account can see or install it. It is gated to a pseudo tier the Worker grants the creator alone; the site, picker, questionnaire, bundles and new-tools notice leave it out. Clearing the flag releases it at its catalog access.
since: 2026-09-25
---

# Preview packages

**The problem.** Work-in-progress tools were published in releases so the
owner could test them in production. Everyone else saw and could install
them too. Removing them from the catalog would stop the testing; revoking
them after the fact is the wrong tool. What is wanted is an unreleased
state: shipped, testable by the owner, invisible to everyone else, and
released later with one switch.

**The answer.** Catalog `preview: true`.

## What a preview is

| | A preview | After release |
|---|---|---|
| In the release, updated like any package | yes | yes |
| Who can download it | the creator account only | its `access` |
| Shown on the site (docs, cards, counts, search) | no | yes |
| Shown in the picker | to the creator, marked "preview" | to everyone |
| Offered by the questionnaire, bundles, Recommended | no (a Recommended flag waits) | yes |
| Announced by "New since you last looked" | no | yes, to everyone, once |

## How it works

- **The gate.** A preview's manifest `access` is `preview`, so its artifact
  is published under the private `plus/` prefix like any gated package.
  The Worker's TIERS map grants it under the key `preview`. Patreon tier
  ids are numeric, so no membership can carry that key; the Worker adds it
  to the creator account's tiers (`patreonTiers`, beside the existing
  creator grant of the top tier). A top-tier patron does not get it: the
  creator's usual top-tier grant is a real tier ("Coaching") that paying
  patrons also hold, which is why previews needed a tier of their own.
- **The catalog keeps the real access.** `access` stays the tier the tool
  will ship at. `gate_package.py` keeps the two files in step: `--preview`
  sets the flag and makes `preview` the package's only Patreon grant
  (variants included); `--release` clears it and re-derives the real grants
  from `access`. Re-gating a preview records the new access but grants
  nothing public. Gumroad rows are left alone, so a key set up before
  launch survives.
- **Hiding.** The picker removes previews from the manifest at boot unless
  the account is entitled, before any list is built. The installer's
  new-tools record never includes them, so they are announced when they go
  public. The site build keeps their docs and catalog checks but builds no
  page or card for them, and strips them from the manifest it bakes into
  /get/. The public mirror withholds their sources like a gated tool's.

## Limits

- **The published manifest names them.** It is the machine-readable file
  every install reads, so a preview's name and description are in it with
  `preview: true`. Nothing presents them to a person, and nothing can
  download them, but the names are not secret.
- **A tool that already shipped publicly keeps its old public files.** Its
  earlier free artifacts stay at their versioned bucket paths until they
  are deleted with `wrangler r2 object delete`, one call per file.
- **Someone who installed it while it was public** keeps their copy. The
  updater cannot fetch a preview for them, so it reports the update as not
  available to their account.

## Releasing a preview

Untick "Preview" in the CMS (or `gate_package.py <Name> --release`), cut
the release, and `wrangler deploy` so the Worker grants it at its access.
