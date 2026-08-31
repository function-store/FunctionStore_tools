---
status: open
summary: 'Decision: how the TDXLU launcher and the FNSTools rail should share package installation -- two installers today, and what to do about it. Recommends the installer becoming a command provider over folding the companion into the toolkit.'
since: 2026-08-31 (raised by the owner after the four capabilities landed)
skill: fns-packaging
---

# The launcher / toolkit boundary — who installs what

> **Implementation status (2026-08-31).** Option A is BUILT and shipped
> in v3.0.13: `FNS_Installer` declares `fns.install` (dry-run by
> default), `ResolvePlan` takes `minimal=` and `sources=`, and `minimal`
> can also ride a `selection.json` key so an existing integration opts in
> without a new code path. The offline path is live on both sides.
> **Still open:** the companion's home (Option B — a release-ownership
> question for TDXLPP, not a task we schedule), the `external` row, and
> the consent-shape questions at the end.

**The decision:** the launcher can put toxes into a user's project, and so
can the FNSTools installer. Two systems place packages, and only one of
them keeps records. This document is for choosing which way that
collapses.

Raised by the owner 2026-08-31, after Collect, Media, Remote and Autosave
moved onto the toolkit rail ([PlusCapabilityPackaging](PlusCapabilityPackaging.md)).

## Correction (2026-08-31): the online path was already delegated

Written before TDXLPP confirmed how their FNS tab actually works. **It
already installs through our installer**: sync store → write
`selection.json` → `fns_install` verb → pulse `FNS_Installer`, with a
target picker and an adds/removals confirm. So for a user who HAS
FNSTools, placement was never split — the launcher was already asking.

That narrows this document's problem statement to where it is still
true: the **bootstrap** (placed by `load_tox` because there is no
installer yet), the shelf place action, and every path on a machine with
no toolkit root at all. It also reduces the command rail's online value
to "a lighter per-package plan/confirm reachable from the Current view",
which is a convenience, not a fix.

What survives as genuinely load-bearing:

- **`minimal`** — their existing flow forces core, so installing one
  capability lands ten packages. This is the bait-and-switch, and it is
  in the path they already ship. Delivered as a `selection.json` key so
  they get it WITHOUT adopting the command rail (below).
- **`source`** — the offline path, which nothing else provides, and
  which is blocked on whether their installer may bundle our bootstrap.

The rest of Option A remains correct but is smaller than it looked.

## The problem, stated once

There are **two installers**:

| | FNSTools | Launcher |
|---|---|---|
| Fetches | manifest + artifacts to the palette store | `fns_sync_store` to the same store |
| Places | `InstallPlan` → COMP in the target, honouring `placement` | `load_tox` / shelf place action |
| Records | `installed` table row: package, sha, release, when | nothing |
| Updates | `Compare()` on live `Pkgversion` vs the store manifest | nothing |

Anything the launcher places lands **behind the toolkit's back**. Two
consequences, both raised by the owner and both real:

1. **No updatability — but not for the reason it first appears.**
   `Compare()` walks the toolkit root's children and matches them against
   the manifest **by name**, reading the live `Pkgversion`; it needs no
   install record (the record drives the `missing` state and removal
   bookkeeping). So a launcher-placed tool that happens to sit in a
   toolkit root IS seen. The real failure is that for a launcher-only
   user **there may be no toolkit root to walk at all** — and a tool
   placed outside one is invisible, frozen, with nothing reporting it.
2. **Duplicates.** Nothing shared answers "is this already here", so a
   user who later installs FNSTools — or opens a project snapshot that
   already contains it — gets a second copy. For `FNS_Autosave` that is
   not cosmetic: two autosavers both writing saves is the collision the
   single-package decision existed to prevent.

Both symptoms have one cause: **nobody owns placement.**

## What is NOT the problem

Worth ruling out, because it changes which options are serious:

- **Not stocking.** Downloading a `.tox` into the palette store is
  harmless and shared; the store is a mirror by contract. The damage
  starts at placement.
- **Not the free/gated split.** Gated packages are acquired deliberately
  by a paying supporter, so an install step is expected and fine. This is
  overwhelmingly a question about **`FNS_Autosave`** — the one capability
  a user should not have to know to ask for.
- **Not companion updates.** The companion has `update_utility` and it
  works. Its update story is solved differently, not missing.

## Option A — the installer becomes a command provider  ← RECOMMENDED

`FNS_Installer` declares `FnsCommands()` like any other tool, so
installing a package is a registry command. The launcher stops placing
toxes and **asks** instead; the toolkit does the placing, recording and
updating it already knows how to do.

The one primitive the launcher keeps is **ensure-bootstrap**: if
`FNSTools.tox` is not in the project, stock and load it — that is the
only tox it ever places, and it is exactly the tox that contains the
installer. Everything after that is a request.

- Duplicates: solved. One code path owns placement and it already checks
  presence (and, for `placement: pane`, the install record).
- Updatability: solved. Installs go through `InstallPlan`, so they get
  the `installed` row and `Compare()` picks them up like anything else.
- "Ensured by proxy": achieved, without a dependency edge. The companion
  can ask on first run for what it needs — a runtime request the user can
  see and consent to, which is where an install decision belongs.
- Cost: small, and it is **our** code — a `FnsCommands()` spec on
  `FNS_Installer`, plus the launcher swapping `load_tox` for a command
  call. No product restructuring, no branding change, no release-cadence
  coupling.

### A's prerequisite: a minimal-install mode

**Core is 10 packages and `ResolvePlan` forces it into every install** —
`FNS_ConfigRegistry`, `FNS_Console`, `FNS_Hub`, `FNS_Updater` and six
registries. Several inject into TD's UI. So "install autosave" as the
installer works today means *a Hub, a Console and six registries the user
never asked for*. For someone who dragged a launcher tox to get one
safety feature, that is a bait-and-switch, and it would poison the whole
scheme on first contact.

The rule exists because "every tool plugs into the infrastructure" —
registry hosts need their masters. **These four plug into nothing**: they
carry no registry hosts, so their derived `requires` is empty, and core
is not infrastructure for them but baggage.

So A requires: **install exactly what was asked plus its derived
`requires`, skipping the core force when that is empty.** One conditional
in `ResolvePlan`. Without it, do not build A.

**But minimal must be a CAPABILITY, not a policy.** The counter-argument
is real: a user who meets FNSTools through autosave and gets no Hub and
no Console has a poorer path into the rest of the toolkit. Two facts
settle how much that matters:

- **They are not stranded.** The bootstrap root carries its own
  `Pick Tools` entry point, and its help text describes this exact state:
  *"before that — the bare bootstrap — the installer's own picker."* A
  bare-bootstrap-without-Console is an anticipated, supported
  configuration with a working full-catalogue picker one pulse away.
- **Core is less invasive than it sounds.** An empty registry owns no
  surface — it tears down its own ops and never touches TD's dialogs
  ([PaletteTabContract](PaletteTabContract.md)). Six registries with
  nothing contributing are dormant, not intrusive. What is genuinely
  visible is Hub and Console.

So neither absolute is right, and the choice belongs at the **offer**,
not in `ResolvePlan`:

- *"Install autosave"* → minimal; one package, nothing else changes.
- *"Install autosave and set up FNSTools"* → core too, opens the picker.

**Default to minimal**, because the asymmetry runs one way: expanding
later is one pulse on `Pick Tools`, while pruning back ten unwanted
packages means finding the Console's remove tab and unchecking things —
and unchecking an installed tool REMOVES it, which is a frightening
operation to hand a newcomer.

### The rule that protects the other persona

**No automatic install without PRIOR consent** — which is not the same as
"always ask".

"Set up like last time" reads `last_install` from the roaming config and
would cheerfully restore a user's entire toolkit into a project where
they wanted one feature. Triggering that **unasked** is the violation.
Doing it because the user previously said "always set my projects up like
this" is honouring an instruction, and is fine.

This matters because the same event has opposite correct answers
depending on who it is. An FNSTools regular opening a fresh project might
be delighted their tools arrived. A launcher-only user would be alarmed.
So the design must **offer rather than assume** — once.

### Consent must PERSIST, or the scheme rots

The failure mode that would kill this in practice: a user who drags the
companion into **every** project (no startup file) meets the same dialog
every time. One extra click per project is not a small cost — it is a
recurring tax on the exact person who uses the launcher most, and it
would teach them to resent the feature.

So the offer carries "remember this choice", stored machine-locally.
After the first yes, every later project is silent: drag companion →
launcher ensures bootstrap + the remembered packages → done. **One drag,
no dialog, and they now have autosave they did not have before** — which
is strictly better than today's flow for that user, not merely equal.

Two constraints on the silent path:

- It stays **visible**: a status line naming what landed, never a modal
  and never nothing. Silent-and-invisible is how a user ends up not
  understanding why their project contains things.
- It stays **revocable**: "stop doing this" must be findable, or the
  remembered yes becomes a trap.

### Better still: attack the repeat, not the click

A user dragging the same tox into every project is doing by hand what
TD's **startup file** already solves — and the companion's own
onboarding treats "drag it in" and "bake it into the startup file" as
equivalent paths, without ever promoting the second.

So the launcher should notice the pattern and offer, once: *"You have set
this up N times — add it to your TouchDesigner startup file?"* That
removes the drag AND the dialog permanently, for the companion and for
whatever toolkit packages the user always wants.

Worth stating plainly because it reframes the whole objection: making a
recurring cost cheaper is worse than removing the recurrence. The
consent-persistence above is the fallback for users who decline this.

### Two more things to get right when building it

- **Consent.** An install triggered from another app must not be silent.
  The command should surface the picker (or a confirm) rather than
  installing on demand — the launcher asking is not the same as the user
  agreeing.
- **Async.** Command handlers run synchronously on TD's main thread, so
  the handler kicks the existing download job and returns; it must not
  block on a fetch. The updater's job machinery already works this way.

### What A does to the drag-and-drop moment: nothing

The launcher's onboarding today is: hello → no companion → "drag
`TDXLauncherUtility.tox` onto your project" → one drag, done.

Under A that is **unchanged**. The companion stays the drag target, the
hello and the prompt are identical. What changes happens only *after*,
and only when a capability is missing: the launcher offers, and on accept
the bootstrap arrives with no drag (it is the one tox the launcher may
place, being the tox that contains the installer) and the requested
package installs. Cost to a launcher-only user: **one click, and only
when they want the feature.**

## Option B — the companion becomes an FNSTools package

The owner's original premise: `TDXLauncherUtility` ships as a package
that sits **beside** `/FNSTools` (`placement: "root"`, which landed
2026-08-31 and fits this exactly — presence is the live COMP, updates
apply in place, removal is real).

Genuinely attractive, and three things say the boundary is already
blurring: `placement: root` exists; the gate's `TIERS` map already lists
`TDXLU_Pro` beside `FNS_TimelineTools`, so **licensing stopped
respecting the product boundary a while ago**; and the companion's
`FNS_CommandRegistry` would become a core registry like the other ten.

What it costs, and why it is not the first move:

- **It changes what the user drags — and that is the real cost.** Today
  the launcher says "drag `TDXLauncherUtility.tox`": one drag of *their*
  thing, one outcome. Under B the companion cannot arrive without
  FNSTools, so the drag becomes `FNSTools.tox` — a drag of *ours*,
  followed by a picker, to get a launcher feature. For a launcher-only
  user that is an onboarding regression, and it is the one cost that
  lands on people rather than on us. (Under A the drag does not move at
  all — see above.)
- **Release-cadence coupling.** The companion currently ships on TDXLPP's
  schedule. As a package its version and release ride our rail, so
  shipping a companion fix means cutting an FNSTools release.
- **A decomposition, not a move.** `FNS_CommandRegistry` lives inside the
  companion. If the companion becomes an optional package, every tool's
  command registration would depend on an optional non-core package —
  wrong shape. Doing B properly means splitting the registry out into a
  core package first, which is its own piece of work with its own
  argument (today "the launcher ships the registry" is deliberate: a
  registry with no consumer is dead weight).
- **Product boundary.** TDXLU would appear in the FNSTools catalogue with
  an FNSTools docs page and tier row. Mechanically fine; a branding call.

## The reverse persona, and what it revealed

Traced 2026-08-31: an **FNSTools user who already has `FNS_Autosave`**
and then discovers the launcher.

They install the app, it launches a project, finds no companion, tells
them to drag `TDXLauncherUtility.tox`. They drag it once. The companion
promotes `FNS_CommandRegistry`, which rescans for `fnscommands`-tagged
COMPs — and their autosave is already tagged, already carries its
`FnsCommands()` spec, already declares `fns.autosave`. **It lights up in
the launcher's Current bar, retroactively, with no reinstall and no
configuration.** Same for Collect, Media and Remote if they have them.
That is the durable-announcement design paying off: the tag is TD-native
and needs no registry, so a registry arriving later rediscovers them.

Two properties worth naming because they are not obvious:

- **No entitlement dance.** A supporter who owns Collect does not
  re-authenticate to use it in the launcher. Under possession-at-stocking,
  possession IS the proof; licensing was settled once, at install. The
  launcher only renders commands.
- **No duplicate — because TDXLPP deleted their copies.** This is the
  user most likely to have both, so had the companion kept its own
  autosave, this is exactly where two autosavers would have collided.
  That deletion was not cleanup; it was the precondition for this
  direction working at all.

**What it revealed:** for this user the companion is the *only unmanaged
thing in their project*. Everything else arrived through the rail with a
record, a version and an update path. That is the itch Option B
scratches — so the reverse persona argues FOR B while the launcher-only
persona argues AGAINST it. The two options serve opposite users, which is
why the choice resisted resolution.

### Rejected: "the companion as both a drag and a package"

The tempting synthesis was that the companion could be acquired either
way — dragged for launcher-only users (onboarding unchanged), or ticked
in the catalogue by FNSTools users who want it managed — with the
installer's `placement: root` presence check (`op(home_path + '/' + name)`,
exactly where a dragged companion lands) preventing duplicates.

**It does not survive contact.** Three reasons, the first fatal:

1. **They are not the same artifact.** A dragged companion is TDXLPP's
   release build on their cadence. A catalogue package is OUR artifact,
   exported by our pipeline from a live COMP in our project, carrying
   `FNS_About`/`Pkgversion` and `pi_suspect`, sha-pinned in our manifest.
   Two builds of one component, two pipelines, two version schemes. Our
   updater reads `Pkgversion` off the live COMP, so a dragged companion
   reads `unversioned`. And "fix" that by having TDXLPP adopt our version
   shape and their release cadence is now coupled to our numbering —
   **the exact cost B was supposed to carry and A was supposed to avoid,
   arriving through the side door.**
2. **Someone must build the package.** A package is a depth-1 COMP in our
   root that PI tracks, so a permanent copy of their companion would live
   in our project, re-imported on every companion change — forever. The
   alternative is new machinery for third-party artifacts, since
   `Packages()` derives from live COMPs and has no concept of an external
   one. This applies to the "additive door" idea just as much as to B.
3. **The overlap handling is "silently does nothing."** Presence detected
   → install skipped → the user ticks the box and their companion stays
   unmanaged. With `Replace` on it is worse: destroys theirs, installs
   ours, possibly a downgrade, while `update_utility` and our updater both
   believe they own it.

### The better question: who owns the companion's release?

Not "which persona wins" but **who ships and updates the companion**:

- TDXLPP wants independent cadence → it stays dragged, and **A is the
  whole answer**.
- TDXLPP would rather retire `update_utility` and ride our rail → that is
  **B**, with its onboarding cost accepted deliberately.

That is TDXLPP's call, not ours, and it is a cleaner question than the
one this document started with.

### The cheap partial: an `external` row

The reverse persona's real discomfort is that the companion is *invisible*
to their toolkit — not that it is unmanaged. That is fixable without
owning anything.

`Compare()` already emits states it never acts on (`unversioned`,
`incompatible`, and `component`). Add one more:

```
package              state     installed  available  note
TDXLauncherUtility   external  0.23.0     —          maintained by the launcher's own updater
```

Cheap because **the companion already carries an `FNS_About`**, so its
version reads with the same child-first logic every other reader uses —
no new convention and nothing needed from TDXLPP. Detection is the
`op.TDXLU` shortcut resolving (the same signal the packages already use),
or a one-entry known-externals table.

Hard rules, or it becomes a nag for something we cannot fix: never in
`updates`, never counted `missing` or `stale`, never touched by Refresh
or Update, and the note must read as information rather than a chore.

Cost is roughly twenty lines plus checking that row-rendering surfaces do
not assume every state is actionable. It does **not** make the companion
updatable, unify the pipelines, or answer the ownership question — it
converts "my toolkit pretends this does not exist" into "my toolkit knows
about it and says who maintains it", and forecloses nothing. The shape is
general: any known-but-foreign component could use it later.

## Offline — the regression the move actually introduced

The launcher ships `TDXLauncherUtility.tox` **inside its own bundle**, so
dragging it has never needed a network. Autosave used to be in that
bundle. It is now on the rail, which needs the bucket for both the
bootstrap and the artifact.

**So there is a real regression, and it is not about clicks.** D7's
zero-friction argument had an offline dimension that this document
dismissed too quickly: a user with no network could previously drag one
file and have autosave. Under the rail they cannot.

**The palette store already softens it.** The store is machine-wide and
by contract a mirror of the bucket, so once a machine has synced even
once, the installer plans from the cached manifest with `have=True` and
installs with **no network**. Offline therefore only fails on a machine
that has **never** synced.

### What the bundler gathers: the manifest's `launcher` block

A bundler needs to know WHICH packages are worth carrying, and "has
commands" is the wrong test — nearly every FNS tool has quick-launch
commands, so that predicate gathers the entire fleet.

`build_manifest.LauncherSurface()` derives the right set by reflection
(landed 2026-08-31): a package qualifies if any of its commands declares
a `surface` token other than `quick`, or a `capability`. It reads both
registration shapes — a `FnsCommands()` spec list and
`@fns_command`-decorated promoted methods — and emits, presence-style:

```json
"launcher": { "surfaces": ["context-menu", "session"],
              "capabilities": ["fns.collect"],
              "seedable": false }
```

**`seedable` is NESTED inside the block — `p.launcher.seedable`, never
`p.seedable`.** Stated emphatically because getting it wrong is silent:
a consumer reading the top level gets `undefined`, and if its bundling
predicate ORs that with a free check (as any careful one will), the
result stays correct while the guard never actually runs. That happened
— a live consumer's cross-check was inert for every package and still
agreed with itself, which is the worst failure shape a redundant guard
has. Verified against the published v3.0.13 manifest: there is no
top-level `seedable`, only the nested one.

Nested is canonical, and deliberately: `seedable` answers "may a bundler
carry THIS launcher-capable package", which is meaningless for a package
with no launcher block at all. A top-level key would invite bundling
things that reach no consumer surface.

Absent means "commands only", which is the normal answer. Measured on
the live fleet the day it landed: **4 of 53 packages qualify** — exactly
the four ported capabilities, and none of the other 49. That is the
discrimination the field exists for, and it gives a bundler a one-key
predicate.

Derived, never declared, same rule as `surfaces` and `hotkeys`
([CREATING.md](../packaging/CREATING.md)).

### The fix: the launcher seeds the STORE, it does not place toxes

Bundle a snapshot of the free rail — `manifest.json` plus the free
artifacts — and on ensure-bootstrap populate
`<userPalette>/FNStools_ext/store/` from it. The **normal install path
then runs offline**: full records, correct placement, correct binding, no
duplicates, no version skew, because nothing is hand-dropped.

This is in contract rather than a workaround: the store is defined as a
mirror where "a file that disagrees with the manifest is stale cache,
never a modification to preserve", so a pre-populated mirror is exactly
what it is for, and the existing sha-mismatch staleness detection heals
it the moment the machine is online.

It is also strictly better than the obvious alternative — bundling toxes
for the launcher to drop — which would reintroduce every duplicate and
version-skew problem this document exists to remove.

**Costs, stated plainly:**

- The launcher's bundle grows by whatever free artifacts it seeds.
- Seeded artifacts age: a user who never goes online gets whatever
  shipped with their launcher build — the same deal that already applies
  to the companion itself.
- **Free packages only.** A gated artifact cannot be seeded, because its
  bytes are the thing being sold. An offline supporter still cannot stock
  Collect — correctly, and unavoidably.

### RESOLVED 2026-08-31: the offline path is going ahead

TDXLPP's owner approved bundling our bootstrap, so the offline path is
real rather than pending. What they built matches the precedence above:
`effective_bootstrap()` resolves **store-first** and falls back to a
bundled copy; the bundle is an **artifact source only**, never copied
into the store, so it cannot make a store artifact look present-but-stale
and our sha checks remain the only truth about store contents. With
neither available it returns nothing and says "refresh the store once
while online" rather than pretending.

**A practice worth copying, and the mistake that produced it.** They do
not hand-copy or commit our tox. A build-time script pulls
`rails['FNSTools.tox']` from the **rolling manifest**, verifies the
sha256 the manifest pins, and records release + digest + URL in a tracked
JSON. The reason: they had our DEV build sitting in `release/` ready to
ship. Fetching makes a *released* artifact the only thing that can reach
a bundle, and the digest makes a wrong one loud. (Note our repo's
`packaging/manifest.json` carries an EMPTY rails block — rails are hashed
in by `Stage()`, so only the staged/published manifest has them. That is
correct, not a bug, but it will confuse anyone who checks the repo copy.)

**Consequence for release ordering:** their installer pins whatever
release was current at ITS build time. A launcher built before our
catalogue release bundles a bootstrap that predates the four packages.
Harmless for the bootstrap itself — it only has to provide the installer
and updater, and a store refresh brings the rest — but it means "which
toolkit can this user's machine reach offline?" is answered by the
launcher's build date, not ours.

**The gap that remains:** the bootstrap alone does not make autosave
work offline. It supplies the installer and updater; the CAPABILITY still
needs its artifact, which is what `source` consumes. So the offline
autosave story needs `FNS_Autosave.tox` bundled too, by the same
fetch-and-verify route — and that cannot happen until the package is
released and catalogued as free, since `seedable` is false for an
uncatalogued package and a released artifact is the only kind their
script will fetch.

### The seeding rule: cold start only

The dangerous case is the reverse arrival order — **an FNSTools user with
a populated store who installs the launcher afterwards.** Seeding
naively would overwrite their current store with the launcher's vintage,
and the damage would not stop at files: the store manifest is what the
updater treats as *what the world publishes*. Roll it back and
`Compare()` sees older versions than the user has installed, so every row
reads `current` and **real updates go silently invisible**. Not
hypothetical — this exact confusion was hit on 2026-08-31, when the CMS
Published column read a v3.0.9 store cache against a v3.0.11 release.

Seeding a single artifact into a populated store is worse than doing
nothing, too: artifacts are sha-checked against the manifest, so a
bundled `.tox` from another release lands `stale`, and the installer
REFUSES stale copies ("Refresh Store in FNS_Updater, then re-Plan").
Offline, absent and stale both block — but stale blocks with a misleading
message and a file that looks present. Seeding would manufacture a trap.

So:

- Store has **no manifest** → seed it. This is the never-synced machine
  the whole mechanism exists for.
- Store has a manifest → **seed nothing.** The user is already on the
  rail; anything the bundle adds is redundant or stale.

The same precedence applies to ensure-bootstrap: **prefer the store's
rails over the bundle's**, since a populated store already carries a
fresher `FNSTools.tox` than the launcher shipped with.

One sentence covers both: **the store is authoritative, the bundle is
only the cold-start fallback.** That makes arrival order a non-event —
an FNSTools user who installs the launcher later has nothing touched,
and gets the freshest bootstrap rather than the launcher's vintage.

#### …even when the bundle is NEWER than the store

The obvious objection: a user with a months-old store installs a fresh
launcher carrying newer artifacts. Should the bundle win then?

**No, and the reason is structural.** Online the question is moot — a
refresh fetches the real bucket, which beats any bundle. Offline,
seeding forward is a trap: the store holds ONE release (`manifest.json`
plus that release's artifacts beside it) and artifacts are sha-checked
against that manifest, while a bundle can only ever carry a **subset**
(free packages, likely only launcher-capable ones). Advancing the
manifest therefore makes every artifact the bundle does not carry
sha-mismatch → `stale` → and the installer **refuses stale copies**.

So the "helpful" forward seed would take a user who could install
anything in their store offline, and leave them able to install only the
few the bundle shipped — strictly worse, in the one situation where they
cannot recover. **The manifest is a fleet-wide, all-or-nothing document;
a partial bundle can never safely advance it.**

What to do instead:

- **Say so.** The launcher can compare both release labels, so a newer
  bundle becomes a visible message — "your package store is older than
  this launcher's bundle; refresh when you are next online" — rather than
  silence. Costs nothing, and turns invisible staleness into something
  the user can act on.
- **If an offline path is ever wanted**, the only coherent form is an
  explicit **whole-store replace**: wipe and seed the bundle atomically.
  Never automatic, because it trades version freshness for COVERAGE —
  the user loses every package the bundle does not carry, including any
  gated artifacts they had already fetched. A real trade, but only ever a
  knowing one.

## Option C — leave it, special-case autosave

Keep two systems and accept that launcher-placed tools are unmanaged;
solve only autosave, by whatever one-click "add to this session" the
launcher wants to build.

Rejected as an end state, but honest about why it is tempting: it is the
least work and the population at risk is currently empty. It fails
because it leaves the duplicate hazard live on the one package where
duplication actually corrupts (two autosavers), and it pays that price
without buying anything reusable.

## Recommendation

**Do A, with store seeding. Add the `external` row. Leave the companion's
home to TDXLPP.**

Store seeding is not optional garnish: without it, A trades a
bundled-and-offline autosave for one that needs a network, which is a
regression for exactly the users least able to complain about it.

A solves both stated problems at the root — one owner of placement — for
a fraction of B's cost, and it touches mostly our own code rather than
another product's onboarding. It also makes the "ensured by proxy" idea
work *without* breaking the packaging rule that tools depend only on
core: the companion asks at runtime instead of declaring a dependency.

B is not wrong, and A does not foreclose it — in fact A makes B easier,
because once the launcher installs through the toolkit, moving the
companion onto the rail is a packaging change rather than a behavioural
one. But B is no longer OURS to schedule: it turns on who owns the
companion's release, which is TDXLPP's decision (above). Until they want
to retire `update_utility`, B is not a pending task — it is an option
they hold.

The `external` row is the piece that makes waiting comfortable. It gives
the FNSTools user what they actually wanted — a toolkit that acknowledges
the companion — at ~20 lines, with no coupling, no second pipeline, and
nothing foreclosed. Build it when A lands, not before: it is only
meaningful once the launcher and the toolkit are already cooperating.

C only if this whole track is being deprioritised, in which case say so
explicitly rather than drifting into it.

## What is still the owner's to answer

0. **Is the minimal-install mode acceptable?** It relaxes "core is not
   optional" for packages that require nothing. That rule has protected
   the toolkit from broken partial installs, and this is the first
   deliberate hole in it. The alternative is landing 10 core packages on
   a launcher user who asked for one feature, which is worse — but the
   rule change is the owner's to bless, not mine.
1. **Consent shape** for the FIRST offer: a two-option prompt (autosave
   only / autosave + set up FNSTools), and whether "remember this" is
   checked by default. Everything after the first yes should be silent
   but visible — that part I would not make optional.
2. Whether the launcher may **ensure-bootstrap** unprompted — that is the
   one placement it keeps, and it is a real "this app modified my project"
   moment.
3. **B's branding question**, whenever B is taken up: is TDXLU a product
   beside FNSTools or within it? The gate already behaves as though it is
   within.

## What this does not block

Nothing here gates the current release. The four packages ship the same
way under any option; the catalogue work
([PlusCapabilityPackaging](PlusCapabilityPackaging.md)) is independent
and should not wait on this decision.
