---
status: in-force
summary: Release signing — a dedicated Ed25519 key signs the manifest and discovery document at Stage time; clients verify against a pinned public key, fail closed on tamper, and allow-but-log unsigned during the transition.
since: 2026-08-28 (owner decision on key custody: local file outside the repo)
skill: fns-packaging
---

# Release signing

Artifact hashes verify downloads *against the manifest*; until 2026-08-28
nothing verified the manifest itself, so whoever could serve
`manifest.json` or `fnstools.json` supplied both the malicious tox and
the hash that blessed it (audit F-03/#2). Both documents now ship a
sidecar `<name>.sig` — Ed25519 over the exact file bytes, base64, one
line — and every install verifies it against a pinned public key.

## The key

* **Dedicated keypair.** The Worker's JWT key was deliberately NOT
  reused: it is a Cloudflare secret the release machine cannot and
  should not hold, and one key doing two jobs couples their rotations.
* **The private key lives OUTSIDE the repo** (owner decision):
  `%USERPROFILE%/.fnstools-release/signing.key` — a 32-byte seed, hex.
  Override with `FNS_SIGNING_KEY=<path>`. It must never enter the repo,
  a staged artifact, or the bucket. **Back it up offline**: a lost key
  means shipping a new key generation.
* **The public key is PINNED** in `ExtUpdater.py`
  (`SIGNING_PUBKEY_HEX`), beside `DISCOVERY_PINS` and under the same
  contract — replacing it mints a new generation of the component; it
  never fixes installs already in the field.
* Generate once with `python packaging/sign_release.py --init` (refuses
  to overwrite an existing key).

## Signing (release side)

`publish.Stage()` signs every staged copy of both documents — the
release-pinned manifest, the rolling manifest, `.well-known/fnstools.json`,
the release-pinned discovery copy, and the `pin3-` file — and **refuses
to stage without the key** (`FNS_ALLOW_UNSIGNED=1` is the offline-test
hatch only; the guard tests use it, a release never does). `upload.py`
ships the two rolling `.sig`s `no-cache`, exactly like their documents —
a fresh manifest under yesterday's cached signature would fail every
install at once.

Implementation is pure python (`packaging/ed25519_ref.py`, RFC 8032
reference construction): no machine needs a crypto package to release,
and the client needs none to verify.

## Verification (client side)

`ExtUpdater` fetches `<url>.sig` beside each document and classifies:

| State | Meaning | Action |
|---|---|---|
| `verified` | signature checks against the pin | proceed (logged INFO) |
| `bad` | a WELL-FORMED signature that fails | **refuse** — a bad discovery sig refuses that pin; a bad manifest sig fails the pass. This is tamper evidence and never negotiable. |
| `unsigned` | sig absent, unparseable, or a CDN error page | allowed and logged loudly while `REQUIRE_SIGNED = False` |

The asymmetry mirrors the TD-build floor and the kill switch: a known
incompatibility refuses, an unknown one does not — documents published
before signing existed must not strand the fleet. A stalled or aborted
`.sig` fetch is an availability fact, not tamper evidence, and classifies
as unsigned; a stale sig can never judge fresh bytes (the sidecar is
deleted before each fetch).

**The transition ends by flipping `REQUIRE_SIGNED` to `True`** once every
fleet install has taken at least one signed release; unsigned then
refuses like `bad`. That flip ships as a normal component update.

## Verified by

`tests/test_release_signing.py` — RFC 8032 known-answer vectors against
both implementations, signer→client roundtrip, tamper/flipped-bit/garbage
classification, and a check that the local key actually derives the
pinned public key. The implementation was additionally cross-validated
against node:crypto (same deterministic signatures, both directions) when
it was written.

## Sources

* Audit finding A F-03 / B #2 (2026-08-27) — the authenticity gap
* [RailHardening.md](RailHardening.md) — availability (pins, cache); this
  document is the authenticity half it deliberately left open
* `packaging/sign_release.py`, `packaging/ed25519_ref.py`,
  `modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py`
