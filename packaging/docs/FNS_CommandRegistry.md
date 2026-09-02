---
package: FNS_CommandRegistry
summary: 'Collects the commands your tools declare, and TouchDesigner''s own, and serves them to whatever can run them: the FNS_CommandPalette inside TouchDesigner and the TDXL launcher''s tray palette. Tools never depend on it being installed.'
features:
  - name: Command Registry
    anchor: command-registry
  - name: What a command carries
    anchor: what-a-command-carries
  - name: Built-in commands
    anchor: built-in-commands
  - name: For consumers
    anchor: for-consumers
---

## Command Registry

A tool marks a promoted method as a command and forgets about it. This registry
is the other half: it finds those tools, reads their commands out of the live
class by reflection, validates them, and serves one flat list to whatever is
present to run them.

Discovery is by tag, not by scanning. A tool that declares commands is tagged
`fnscommands`, so a registry that arrives, or is replaced by a newer version,
later rediscovers every tool by rescanning tags and re-harvesting. That is why a
tool can be installed before any consumer exists and still show up the moment
one does.

It ships as its own core package, promoted to `/sys` with the global shortcut
`op.FNS_COMMANDREGISTRY`. **It stands apart from the surface registries**: it
carries no `RegistryBase`, injects no chrome, and claims no part of the
TouchDesigner UI. It shares the `/sys/FNS_Registries` home with them and nothing
else.

The authoring side is a separate package, [FNS_CommandKit](/docs/fns-commandkit/),
and the split is deliberate: a tool needs the kit and *no* registry. Every call a
tool makes is guarded, so with no registry in the session nothing happens and
nothing errors.

## What a command carries

Most of a command is derived from the method, with little left to declare: the label
from its CamelCase name, the help from its docstring's first line, and prompted
parameters from the signature, with type hints becoming input styles and a
missing default marking a parameter required.

What a tool declares on top of that is the part a consumer cannot guess:

- **`context`**: what the command acts on, so a consumer can resolve that
  subject before invoking and grey the command out when it is absent:
  `network`, `selected`, `current`, `rollover-op`, `rollover-par`.
- **`surface`**: where it should be offered. A different axis from `context`:
  one says what it needs, the other where it appears.
- **`state`**: where the command's live value lives, so a toggle can render as
  ON/OFF and a setter can show its number. Read at query time, so it is never
  stale.
- **`capability`**: a shared group id that lets a consumer render a family of
  commands together instead of as loose entries.
- **`builtin`**: TouchDesigner's own functionality, so a
  consumer can list it apart. FNS tools do not set it; the registry's own
  built-ins do.
- **`canonical`**: a cross-package identity for a command two packages might
  both offer. Opt-in and never derived from the id, because the same id
  (`toggleactive`, say) legitimately exists on many tools.

Every command has two names. The wire key, `path#id`, is what a consumer
hands back to run it. Curation keys on `tool#id`, the tool's name and the
command id, so favourites, hidden flags and presets survive a tool being
moved in the network; both palettes use that identity. Ids and tool names
are therefore permanent: renaming either orphans a user's curation, so a
shipped id is public API.

Limits are enforced at harvest: 24 commands per tool, 6
parameters per command, 5 contexts and 8 surfaces per command. A malformed
declaration is rejected with a reason instead of being served broken.

## Built-in commands

The registry ships with TouchDesigner's own actions as commands, so a palette
has something to run in a project with no other tool installed: opening the
Textport, the Errors and Performance Monitor dialogs, the Palette Browser,
Preferences and Window Placement, tearing a pane away or changing its type,
saving the project with or without its external toxes, loading a recent file,
toggling realtime, perform mode and always-on-top, setting the cook rate and
master volume, opening the project or TouchDesigner folder, and copying,
viewing or editing the current operator. They are flagged `builtin`, so a
consumer can keep them apart from your tools' commands: the FNS palette badges
them `TD`, lists them after tool commands and leaves them out of `?`.

Every built-in also declares a canonical id. When two packages offer the same
command, the one with the newest package version is served and the other is
set aside and listed by `Shadowed()`, so installing
a newer registry beside an older one never doubles the list. The TDXL
launcher's companion carries this same package, so a project with both
installed sees one registry and one set of built-ins, never two.

## For consumers

`op.FNS_COMMANDREGISTRY.Commands()` returns the full list; `Run(key, args)`
invokes one. `RescanTools()` re-harvests after a tool's command set changes at
runtime, `Shadowed()` lists what canonical-id arbitration withheld and what
beat it, and `Version()` reports the contract version (1.9.0 as of this
writing) so a consumer can tell which fields it can rely on.

Unknown fields are ignored, in both directions. A consumer
that predates `context` simply does not see it, and a tool that declares a
surface no consumer serves loses nothing, which is what makes it safe to
declare new fields early.

Handlers run synchronously on TouchDesigner's main thread, so a command returns
quickly and defers long work; a returned dict with `ok: False` marks the run
failed, and nothing raises into the consumer.
