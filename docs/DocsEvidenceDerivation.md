---
status: in-force
summary: 'What the docs site reads off the live project: shortcuts, surface placement and the bar icon a tool actually draws, plus the audit that catches a doc claiming a key nothing binds.'
since: 2026-08-31 (docs deep pass)
---

# Deriving the docs from the project, not from memory

The docs site has always had two kinds of content on a package page: **prose**,
written by a human in `packaging/docs/<Name>.md`, and **generated blocks**, read
off the live component at build time. The generated half cannot go stale by
construction. The prose half can, and it does so *silently*: a sentence naming a
shortcut that nothing binds is indistinguishable from one that works.

This document records what moved from the first column to the second, and the
one rule that keeps the remainder honest.

## The principle

> If the project knows the answer, the docs must ask the project.
> If only a human knows it, the docs must say so out loud when it is missing.

Everything below is an application of that. Nothing here is a new subsystem: the
evidence was already in the network, it just was not being read.

## 1. Shortcuts: read the evaluated value, not the constant

`build_manifest.Hotkeys()` asks `FNS_HotkeyManager.Discover()` for a package's
bindings, which is right: the manager owns discovery, and reimplementing it
would create a second rule to keep in step. It then read `HotkeyRecord.val`.

`val` is documented on the record as *"constant/bind value (`""` when
expression-driven)"*. The conformance contract
([HotkeyManagerConformance](HotkeyManagerConformance.md) §3) explicitly blesses
an OS-switch **expression** as the way to bind per-platform:

```python
'ctrl.e' if app.osName == 'Windows' else 'cmd.e'
```

Every tool that followed that advice therefore reported an empty string and was
dropped by the `if not keys: continue` guard below it. **Five packages shipped
with no Shortcuts section at all** while their prose correctly described a key
you could press: `OpenExt` (Ctrl+E), `SwitchOPs` (Ctrl+Tab), `OpToClipboard`
(Shift+Ctrl+C), `TDX_SearchPalette` (Ctrl+Shift+F) and `VSCodeTools`
(Ctrl+Shift+E / Ctrl+Shift+Alt+E).

The record already carried the right field: `HotkeyRecord.current`, *"evaluated
runtime value (what the binding IS right now)"*. That is what `Hotkeys()` reads
now, and it is what makes the function's own docstring promise, "the keys as
bound RIGHT NOW, never as someone remembered them", true.

### The modifier-listen exception

Reading the evaluated value also surfaces pars that are **not** shortcuts. Five
tools carry a `Keys` par holding bare modifiers (`alt`, `alt ctrl`) because
they listen for a held modifier during a gesture ("hold Alt while you drop a
generator TOP"). Those are real, rebindable rows in the manager's UI and must
stay there; they are simply not a key anyone can be told to press, so
`_isModifierOnly()` drops them on the way to the manifest.

The trap in that filter, paid for once: the manager's `ignored_keys` list
includes `esc`, `enter` and `tab`, but those are **keys, not modifiers**. Folding
them in with `ctrl`/`alt`/`shift`/`cmd` deletes `ctrl.tab`, SwitchOPs' entire
binding. Hence two sets, `MODIFIERS` and `BARE_LISTEN_KEYS`, and a per-combo
test: bare `tab` in a listen list is noise, `tab` inside a combo is the key.

### The other side of reading the live value

Reading `.current` makes the docs honest about what a binding IS, which is what
we wanted. It also means the docs publish whatever the **authoring project**
happens to have bound, and that is not always what ships. FNS_BeatMod's tap
tempo is authored as `alt.t`, its parameter's default; this machine's project
has it remapped to `alt.r`, so a release built from here would document `alt.r`
for everyone (found 2026-09-03, before that package's first publish).

Nothing in the build can tell a deliberate binding from a personal one, so the
rule is a release-time one: **before publishing a package, reset its hotkey
parameters to their shipped defaults in the authoring project**, or check the
manifest's `hotkeys` block against the doc's frontmatter and the parameter's
`default`. A par whose evaluated value differs from its own default is the
signal, and it is cheap to look for: `p.eval() != p.default` across a package's
`Shortcut*` pars.

## 2. Surface placement and the icon a tool actually draws

`surfaces` (in the manifest) answers *"does this package put anything on
screen?"*, a list of surface ids, derived from the registry hosts a package
carries. It is what the index filter and the page badges run on, and it stays.

`surface_entries` (in `parameters.json`) answers the next question: *what,
exactly, and where.* One entry per registry host, carrying:

| Field | Read from |
|---|---|
| `surface` | the host's name, via `SURFACE_OF` |
| `widget` | the host's `Comp` par, relative to the package |
| `label` | the host's `Tablabel` when set, else `Canonicalname`: the name the **bar** shows |
| `order` | `Menuorder` / `Taborder` (`-1`, "no preference", is omitted) |
| `side` | `Align`, on the surfaces that have sides |
| `icon` | the glyph on the widget; see below |

Both derive from the same hosts, so the two can never disagree.

### The icon

An FNS bar button draws its icon as a **Text COMP** whose `font` is
`Material Design Icons` and whose `text` is a single private-use codepoint.
`_iconEvidence()` takes the *shallowest* such child of the registered widget:
a bar button keeps its glyph at `<widget>/text`, and anything deeper is
furniture. `ICON_CHROME` excludes that furniture explicitly: TD's own pop-menu
tick and submenu caret are set in the same face, and without the filter four
packages "had" an identical checkbox glyph.

Before this, the site showed a hand-typed `icon: <Name>.png` in the doc's
frontmatter, pointing at a wiki-era bitmap in `icons/`. For SwapOps that was
`SwapOPs.png`, **a different picture from the button it claimed to describe**.
That field still exists and still rides the table of contents; it is no longer
what the surface badge shows.

### Rendering

`RenderSurfaceIcons()` rasterizes each gathered codepoint to
`packaging/docs/surface-icons/<Name>-<surface>.png`, white on transparent, and
the site build copies them into `website/docs/assets/icons/surface/`.

It draws with a **throwaway Text TOP**, not with PIL, for two reasons: PIL is
not in TouchDesigner's Python (`numpy` and `requests` are, measured on
2025.33070), and a Text TOP set to the same face at the same codepoint is not a
lookalike of the button, it is the same renderer drawing the same glyph. It also
means nothing has to know where the font file lives: `font` takes the family
name the button already names.

Two failure modes are reported out loud: a codepoint that renders
an **empty** frame (the face has no glyph there, so the live button is showing
tofu), and a **stale** PNG left behind by a renamed package or a re-pointed
host, which is deleted; a wrong icon on a docs page is worse than none.

## 3. The audit: prose that claims a key nothing binds

Deriving more does not make the remaining prose correct. `build-site.mjs` now
scans every doc body for key combos and reports any whose key nothing in the
toolkit binds.

It **reports, never fails**. Each line is a claim to *check*, not a proven
error, and the filters matter more than the scan: the first version printed
nine findings of which seven were correct prose, and a report that cries wolf
gets ignored, which is the exact failure it exists to prevent. So:

- **mouse chords are skipped**: `Ctrl+RightClick` is a real instruction and is
  never a hotkey-manager binding;
- **modifier-only phrases are skipped**, for the same reason as §1;
- **parenthesised combos are skipped**: `Ctrl+Tab or (Option+Tab)` is one
  binding written for two platforms, and the manifest carries whichever half the
  build machine binds, so the other half can never match;
- **`[0-9]` and `{number}` are the same shortcut**;
- **the whole toolkit's bindings are the haystack**, the page's own included:
  `FNS_PaletteRegistry` documenting `TDX_SearchPalette`'s Ctrl+Shift+F is a
  cross-reference, not a stale claim;
- **a bound key with different modifiers passes**: ParOPDrop binds `p` and its
  doc describes four modifier variants of pressing it; the doc and the manifest
  are both right and merely differ in granularity.

A page with **no prose at all** is reported too, and now renders a visible
"not written yet" note. Rendered silently, an undocumented page is a title, a
badge row and generated tables, indistinguishable from a tool with little to
say, which is how `AltSelect` shipped a blank page nobody noticed.

## Second pass: what a day of changes taught the derivation

Re-run against the project a day later (three new packages, HotkeyManager and
QuickMarks reworked, `credit:` moved to catalog `author`), the same principle
caught three more things, two in the derivation itself.

- **A Str par named like a binding is not always a binding.** Discovery is by
  name, so `FNS_CommandPalette.Favouritekeys`, a JSON list of starred command
  ids, reached the manifest as the shortcut `[]` and the docs set it in a
  `<kbd>`. `_looksLikeKeys()` now refuses a value with no letter or digit, or
  one that starts like JSON. The manager still lists it as a rebindable row,
  which is a naming problem in the tool: the conformance
  contract says a Str par matching `*key*` **is** a hotkey.
- **The label a tab bar shows comes from `Tablabel` first.** ColorUI's
  hub tab reads *OpColor*, the palette's reads *Commands*, FNS_OpMenu's reads
  *SearchWords*; the first pass read only the canonical name and would have
  "corrected" three docs that were right. `SurfaceEntries()` prefers the
  override, as the host's own tooltip says to ("Empty = the canonical name").
- **`fixed_keys:` joins `local_keys:` in a doc's frontmatter.** BorderlessTD's
  `Shift+Esc` is a real, global key the manager cannot discover (a list
  expression on the keyboardin). Declaring it panel-scoped would be a lie;
  declaring it fixed says exactly what it is, and the audit stops reporting a
  gap that is already on record above.

Things the sweep found that live in the **tools** themselves, recorded here
so they are not rediscovered from scratch:

- **36 `Url` / `Helpcommand` parameters inside shipped widgets still open the
  retired GitHub wiki** (`.../FunctionStore_tools/wiki/02.-FNS_Toolbar#...`),
  every toolbar button's "docs" affordance. They are constant strings on the
  button and its `docsHelper`, so the fix is mechanical: each package already
  publishes its `help_url` in the manifest.
- **OUTPUT's package-level `Performwindow` is read by nothing.** The drop
  callback writes through `button_perform/Perform` (parent shortcut `Main`);
  the root parameter, whose tooltip says "the Window COMP these tools drive",
  is unwired. The doc now names the button's parameter.
- **Seven shipped values have no authored default.** BorderlessTD's `Enable`,
  `Fixfullscreenonstart`, `Fullscreen`, `Shiftesc` and `Enabletimeline` ship
  on, HydroHomie's `Intervalminutes` ships at 45 and QuickTime's `Multiplier`
  at 1, all with `par.default` unset, so the generated table says *off* / `0`
  while the tooltip says "on by default". The tables are right about what
  *Reset to default* does; the prose now says "ships on" and stops there.

## What this does not do

- It does not check whether a sentence is *true*, only whether a key it names
  exists. Prose remains prose.
- It does not gather an icon for a surface that has none. Panels, sliders and
  whole-COMP tabs legitimately have no glyph; 11 packages are in that state and
  the build says so, and renders no blank square.
- `BorderlessTD`'s `shift.esc` is still invisible to the manager: its keyboardin
  builds `shortcuts` from a **list expression** combining a par with a
  conditional, which is neither a constant nor the OS-switch shape §3 of the
  conformance contract recognises. That is a conformance gap in the tool, not in
  the harvest; it belongs on a `Shortcut*` par of its own.

## See also

- [HotkeyManagerConformance](HotkeyManagerConformance.md): the discovery and
  persistence contract this reads through
- [RegistryScheme](RegistryScheme.md): the hosts every surface entry is read
  from
- [PackagingScheme](PackagingScheme.md): where `manifest.json` and
  `parameters.json` sit in the release
