---
status: landed
summary: The paid-tool path end to end, as it was fixed on 2026-08-29 — auth extension unwired, entitlement invisible, the "I just pledged" dead end, and the website paste rail aborting on a gated pick. Written to be independently re-checked, with the command for each claim.
since: 2026-08-29
skill: fns-packaging
---

# The entitlement path, and what was wrong with it

Written for a reviewer — human or agent — who should assume nothing here
is true and check it. Every claim below names the file and the command
that settles it. Where a fix rests on judgement rather than measurement,
it says so.

The work landed as `12d6545`, `3bfebde`, `a123fa6`, `08b690f`,
`a2ca2dc` on `dev25-updater-hardening`.

## What we were trying to solve

FNS_TimelineTools is the first paid package. The gate (Cloudflare
Worker), the tier map, signing and the bucket layout were all built and
tested. The question that started this was much smaller — *"do we, on
any surface, let the user know they are authenticated and have plus
access?"* — and pulling it exposed that **the paid path had never run
end to end**, because it cannot be run by the person who built it:
Patreon does not let a creator pledge to their own campaign.

Everything below follows from that single fact. Four separate pieces of
correct, well-commented code were wired to nothing, and each would have
been found by the first customer.

## The four defects

### 1. `ExtAuth` was never registered as an extension (`12d6545`)

`FNS_Updater` declared `extension1` (`ExtUpdater`) and left `extension2`
empty, while `ExtUpdater._auth()` reads `self.ownerComp.ext.ExtAuth`.
That resolved to `None`, and `_auth()` treats `None` as *"auth DAT
absent: behave as signed out"*.

Measured before the fix:

    _auth()                        -> None
    _entitled('FNS_TimelineTools') -> False
    _gatedToken()                  -> ''

So **every gated download behaved as signed out**. A supporter would
sign in, receive a session, and still be refused, with nothing naming
the cause.

*Check it*: in TD, `op.FNS.op('FNS_Updater').extensions` must contain
`ExtAuth`; `type(ext._auth()).__name__` must be `ExtAuth`. Promotion was
checked for collisions first — `ExtAuth` and `ExtUpdater` share no
public names (compare `dir()` of both classes, uppercase entries).

**Reviewer's angle**: promotion is the risk. If a later extension adds a
name that both classes define, the second promotion silently wins. The
collision check was done once, by hand, at wiring time.

### 2. Entitlement was invisible (`3bfebde`, and the swatch in `12d6545`)

`AuthStatus()` composed a good line and had zero callers. `MissingFor()`
composed the right refusal and had zero callers. The picker marked a
package `Plus` but could not say whether it was *yours*.

Fixed by giving the picker an account: `InstallerExt._accountGlobal()`
emits `window.FNS_ACCOUNT` alongside the five globals it already writes,
in three distinguishable states — absent (no updater rail), `null`
(signed out), object (`label`, `products`, `checked_at`).

**The constraint that matters**: the same file is published as `/get/`
on the public website. Entitlement must never reach it.

*Check it*: `python tests/test_picker_flavors.py`. It asserts the built
public page carries no `FNS_ACCOUNT` assignment, that exactly one place
in `InstallerExt.py` emits the global, that no token string appears in
that file, and — the part worth trusting — it lifts the chip's **real
decision lines** out of `index.html` and evaluates them in node across
all four states rather than restating the logic.

**Reviewer's angle**: the test reads source with regexes. If someone
reformats those lines, the test fails loudly (it asserts the match), but
if someone adds a *second* path that emits account data, only the
"exactly one place emits" check would catch it, and only for that exact
string form.

### 3. A skipped Plus package said nothing (`a123fa6`)

`_makeQueue` correctly skips a gated package the install is not entitled
to, and collects `job['gated']` — its comment says the user must be told
*"you do not have this"* rather than a download failure. That list was
written in two places and **read in none**. The package simply did not
appear.

`_report()` now names them using `MissingFor()`, and returns `gated` /
`gated_why`.

*Check it*: `grep -n "job.get('gated')" modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py`
must find the read in `_report`. Live, `MissingFor` returns *"Sign in to
download X."* when signed out and *"Your current tier does not include
X."* when signed in — both were exercised by temporarily stubbing
`IsSignedIn`.

**Reviewer's angle**: this is a status string, not a dialog. Whether it
is prominent enough for a first-run user is a judgement call, untested.

### 4. The website paste rail aborted the whole install (`08b690f`)

The one-line install script fetches with bare `requests` and no token,
because the website has no account and cannot have one. A gated artifact
answers 401; the JSON error body fails the sha256 check; the assert
aborts everything:

    checksum mismatch: FNS_TimelineTools

So picking one Plus tool on the website gave **no toolkit at all**, with
a checksum message for what is really "you have not signed in".

The page knows which picks are gated (`access` is in the manifest it
reads), so the split happens there: free packages download and install;
Plus picks are recorded as wanted (`selection.json` `tools`) but kept
out of `install`, which is what `ResolvePlan` acts on
(`InstallerExt.py`: `wanted = sel.get('install') or (core + tools)`).

*Check it*: generate the script from the page's own function with a
mixed selection and parse it as Python — the method used here was a node
one-liner that lifts `installScript()` out of `index.html`, then
`ast.parse`. `SEL` must hold only free picks, `names = m['core'] + SEL`,
`PLUS` carries the rest to the closing message.

**Reviewer's angle**: `tools` now contains names that were never
downloaded. Anything that reads `tools` expecting local files present
would be wrong. Only `ResolvePlan` was checked, and it prefers
`install`.

## The commercial dead end (`a2ca2dc`)

Separate from the four defects, and the most expensive:

**Nobody is rejected at sign-in.** A non-supporter completes the OAuth
and receives a valid session with `products: []` — correct, since
entitlement is a list. But then:

1. There was no path to *become* a supporter from the refusal.
2. **After pledging, nothing could notice.** Entitlement refreshes only
   from a `/token/download` response (`_rememberProducts`); a token is
   requested only when a gated item is in the queue; gated items enter
   the queue only when `_entitled()` is already true. The local record
   said "not entitled", so the gate was never asked again. Signing out
   and in was the only escape, and nothing said so.

The gate caches the Patreon call for `ENTITLEMENT_TTL` = **6 hours**, so
a naive "check again" would have returned a cached *no* for the rest of
the day after the money moved.

`POST /session/recheck` clears `checked_at` — the only thing
`refreshEntitlement` caches on — and reuses the existing refresh, so
there is no second copy of the entitlement logic. Throttled with the
same counter as redeem. Client: `ExtAuth.Recheck()` /
`OnRecheckResponse`, a `Check again` button, and a `Become a supporter`
link.

*Check it*: `node worker/test/gate.test.mjs`, section 13 — a session six
seconds old holding nothing, a pledge landing at Patreon, the re-check
seeing it despite the cache window, a download token following, 401
without a session, and the throttle tripping.

**Reviewer's angles**, in order of how much they matter:

- The throttle shares `REDEEM_LIMIT` (10/hour). A supporter who pledges,
  presses Check again, and gets Patreon's own propagation delay could
  plausibly burn several. Not tuned against real Patreon latency.
- `Recheck()` writes status but the picker does not refresh itself — the
  user must reload the page. The button's dialog says so; nothing
  enforces it.
- `support_url` is read from the manifest's `toolkit` block, which **does
  not define it yet**, so the button currently falls back to `/plus/`.
  Adding it to `build_manifest` is unfinished work, not a bug.

## What was NOT verified

Stated plainly, because these are the gaps a reviewer should attack
first:

- **No end-to-end run with a real entitled account.** Every check above
  is a unit, a stub, or a live call with a hand-stubbed `Account()`. The
  first true test is signing in with a Patreon account that holds tier
  `8323905`, `8291595` or `9796651` and watching a gated `.tox` arrive.
- **The creator short-circuit is untested against real Patreon.** It is
  covered by worker tests with a stubbed identity response (`gate.test.mjs`
  section 12), never by an actual sign-in.
- **The gate is not deployed with the tier map.** `wrangler deploy` had
  not been run at the time of writing, so `TIERS` in the live Worker may
  still be the placeholder.
- **`FNS_TimelineTools` has no artifact.** It, and seven other packages,
  are catalogued and in the manifest with no `dist/` export — see the
  release track, not this document.

## The pattern worth naming

`AuthStatus()`, `MissingFor()`, `job['gated']`, and `ExtAuth` itself:
four pieces of code written thoughtfully, for exactly the right moment,
and connected to nothing. That is what an untestable feature looks like
from the inside — each author did their part correctly and no one could
run the whole.

The creator short-circuit (`5917c0e`) is the structural fix: it lets the
owner hold the top tier without pledging, so the path can be walked
before a customer walks it.
