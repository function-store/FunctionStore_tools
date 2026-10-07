---
status: in-force
summary: 'The FNS_ prefix is an operator-name convention, not a product name. Every listing a user reads shows the public name (the package FNS_BeatMod displays as BeatMod); identity keys, file names, shortcuts and COMP names keep the prefix. The rule, the surfaces it reaches, and the one identity move it cost.'
since: 2026-09-03 (owner ask: the prefix is noise wherever names are sorted or listed)
verified: 2026-09-03 -- console Settings, Install and Updates tabs read live in the browser; command registry, hotkey list and docs site rebuilt and read back
---

# Public tool names: where the FNS_ prefix earns its place and where it does not

Inside TouchDesigner the `FNS_` prefix does real work. It groups the
toolkit in a network, keeps a dropped COMP from colliding with a user's
own `Console` or `Hub`, and says at a glance who owns an operator. That
argument holds for operator names and for nothing else.

Everywhere a name is put in a LIST, the prefix is noise, and worse than
noise when the list is sorted: twenty-seven packages collapse under "F"
and the letter that actually distinguishes them is the fifth character.
The launcher's command list, the console's settings sidebar, the hotkey
list, the docs site and the install picker all sorted that way.

## The rule

**Identity keeps the prefix. Display drops it.**

The public name of a package is its name with a leading `FNS_` removed.
`FNS_BeatMod` displays as `BeatMod`, `FNS_ToolbarRegistry` as
`ToolbarRegistry`. A package with no prefix displays as itself. The
derivation is mechanical, not curated, so nothing has to be maintained
in step:

```python
def public_name(name):
    return name[4:] if name.startswith('FNS_') else name
```

Verified 2026-09-03: stripping the prefix collides with no other
package name, so public names stay unique across all 58 packages.

**Sort on what is printed.** A list that prints public names and sorts
on canonical ones is the same wall of "F" with the prefix hidden. Every
listing below sorts on the public name.

**Never derive an identity from it.** These keep the prefixed name, and
changing any of them breaks something already on disk or in a project:

| Thing | Why it is frozen |
|---|---|
| COMP name in the network | the reason the prefix exists |
| `.tox` file name | the installer writes `<name>.tox` |
| package name in `catalog.json` / `manifest.json` | the Worker's entitlement map keys on it, as do install records |
| OP shortcut (`op.FNS_HOTKEYMANAGER`) | resolved by name at runtime, everywhere |
| tags (`fnscommands`, `FNS_hotkeys`), storage keys, registry canonical names | registry keys and roaming config keys |
| docs URL slugs (`/docs/fns-beatmod/`) | `help_url` values are baked into manifests that already shipped and into `FNS_About.Helpurl` on installed copies |
| command ids | `CommandRegistration.md`: ids are public API |

Where a surface has only one string doing both jobs, the fix is to add a
label beside the key, never to change the key. Three surfaces work that
way now: the config registry's `UiState()` gained `label` next to
`name`, the manifest gained `title` next to `name`, and the console page
reads `label || name`.

## What each surface does

| Surface | Shows | How |
|---|---|---|
| Launcher quick-launch list, in-TD Command Palette | `Autosave` | `FNSCommandRegistryExt.Register()` stores `_publicName(comp.name)` as `tool` (registry 1.10.0) |
| Console Settings page, sidebar and headings | `Autosave` | `ConfigRegistryExt.UiState()` adds `label`, sorts on it; `console_page.html` prints `toolLabel(t)` and matches a search against both spellings |
| Console Updates tab | `Autosave` | `console_page.html` prints and sorts on `publicName(r.package)` |
| Console Install tab, `/get/`, the picker in the installer | `Autosave` | `configurator/index.html` prints and sorts on `titleOf(p)` = `p.title` from the manifest, falling back to the derivation |
| Docs site: titles, sidebar, cards, landing catalogue, Plus page | `BeatMod` | `build-site.mjs` carries `p.title` on every page object and sorts on it |
| Hotkey manager list | `BeatMod` | `HotkeyManagerExt._toolName()` returns the public name; bindings are still keyed by owner path and par name |
| Hub tabs, Console tabs, Palette Browser tabs | already clean | canonical names were prefix-free from the start (`BeatMod`, `HotkeyManager`, `Console`) |
| `packaging/docs/*.md` prose | `Hub`, `ConfigRegistry` | stripped in prose and link text; kept inside backticks, where the string names a COMP, a shortcut, a tag or a path |
| `docs/*.md`, this repo's engineering notes | `FNS_Hub` | kept: they name real operators |

Two derivations of one rule have to agree, the same way `packageSlug`
and `_helpUrl` already do: `PublicName()` in `packaging/build_manifest.py`
writes the manifest's `title`, and `publicName()` in
`website/tools/build-site.mjs` and in the two HTML shells falls back to
it. Every consumer prefers the stored value, so the fallback only fires
against a manifest published before `title` existed.

## What it cost

The command registry's `tool` field is the curation identity
(`tool#id`) for favourites, hidden overrides and presets, shared with
the launcher through `CommandCuration.md`. Changing the field moved
every FNS key once: `FNS_Autosave#save-now` became `Autosave#save-now`,
and any entry curated under the old key orphans.

That was chosen over adding a second wire field, deliberately and with
the owner's decision, because the cost was near zero on 2026-09-03: the
`tool#id` identity was adopted on 2026-09-02 and the launcher side had
not shipped it. Measured rather than assumed, on the machine that has
had the identity longest: `command-curation.json` held zero entries and
zero presets, and the palette's legacy pars held no keys, so nothing
was orphaned at all. The bill only ever grows. **There is no second
free move** -- the public name is now as permanent as a command id.

The launcher needs no release for this: it prints the field the wire
gives it. The registry version says what happened, 1.9.0 to **1.10.0**.

Doing the sweep surfaced an unrelated defect worth naming here because
it was found by it: `console_page.html` and `ConfigRegistryExt.py` were
committed source bound to nothing, so a change committed to the file
never reached the running tool. Measured, fixed for all 50 files
across 18 package toxes, and written up in
[ExternalizationOwnership.md](ExternalizationOwnership.md#correction-2026-09-03--the-tox-is-the-carrier-and-50-files-are-bound-to-nothing).

## Left open

- **`manifest.json` carries no `title` until the next manifest build**
  (it is generated inside TD from the live components). Nothing is
  blocked meanwhile: the site and both pickers derive the same string
  when the field is absent.
- **A curated `title` in `catalog.json` overrides the derivation.**
  Nothing sets one today. Whether the CMS preserves an unknown key
  through a package edit has not been checked, so treat curated titles
  as unproven until it is.
- **Renaming the unprefixed tools** (`AltSelect`, `SwapOps`,
  `QuickPane` and the rest) so the whole fleet carries `FNS_` in the
  network. The same idea from the other end, and still open: it moves
  COMP names, `.tox` file names and package identity at once, so it is
  its own piece of work with its own migration.
