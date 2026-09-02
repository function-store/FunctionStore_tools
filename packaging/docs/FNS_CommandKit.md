---
package: FNS_CommandKit
summary: 'Drop-in kit that lets any component publish commands to every palette that serves them: the FNS_CommandPalette inside TouchDesigner and the TDXL launcher''s.'
features:
  - name: Command Kit
    anchor: command-kit
  - name: Adopting it
    anchor: adopting-it
---

## Command Kit

Your component's commands appear in every palette that serves the command
registry, the [FNS_CommandPalette](/docs/fns-commandpalette/) inside
TouchDesigner and the TDXL launcher's (`>` / `?` in both), without it having
to know anything about the registry. Drop this COMP inside your component,
mark the methods you want exposed, and they show up.

It is **guarded throughout**: when no registry is in the session, nothing
happens and nothing errors. A component carrying the kit works exactly the
same for someone who never installs the palette or the launcher.

## Adopting it

1. Drag the COMP in as a **direct child** of your component's root.
2. Mark your commands (either way below).
3. Done. The kit announces your component on load, once you actually declare
   something. After changing your command set at runtime:
   `op('FNS_CommandKit').Announce()`.

### Decorator: derives everything from your code

```python
FNSCommand = op('FNS_CommandKit').mod('FNSCommand')  # import

class MyToolExt:
    @FNSCommand.fns_command(help='Set the project tempo')
    def SetBpm(self, bpm: float = 120, sync: bool = False):
        ...
```

The label comes from the CamelCase name, the help from the docstring's first
line, and the prompted parameters from the signature: type hints become
styles, `typing.Literal[...]` becomes a menu, and a parameter with no default
is required. Extras: `fns_command(label=…, help=…, hidden=True, params=[…])`,
plus `context=` (what the command acts on, so a palette can grey it out when
that subject is absent), `state=` (a live value to show as a chip),
`surface=` and `capability=` (where and how a consumer may present it), and
`canonical=` (a cross-package identity for a command another package might
ship too; the newest package wins). The
[registry page](/docs/fns-commandregistry/#what-a-command-carries) explains
each.

### Explicit spec: no imports at all

Promote a `FnsCommand` spec instead, for components that would rather not
import anything. See the kit's own **README** DAT for that form.

### Rules worth knowing

- **Command ids are permanent.** Favourites, hidden flags and presets in
  both palettes key on `tool#id`, and the id derives from the method name, so
  renaming a shipped method, or the component, orphans all of them. Treat
  every shipped id as public API.
- Handlers run **synchronously on the main thread**. Return quickly and kick
  long work off with `run(..., delayFrames=1)`.
- Caps: 24 commands per component, 6 parameters per command.

Components inside the FNS toolkit do not need this kit; they already carry an
ExtUtils with the announcer in it. This is for everything else.
