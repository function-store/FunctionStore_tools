---
package: FNS_CommandPalette
summary: 'A command palette inside TouchDesigner: every command your FNS tools declare, plus TouchDesigner''s own palette components, ranked by what you are looking at.'
hotkeys:
  - keys: Ctrl+Shift+P
    does: Open the palette over the network you are in
local_keys: [Ctrl+D, Ctrl+H, Alt+S, Alt+Up, Alt+Down]
features:
  - name: CommandPalette
    anchor: commandpalette
  - name: Prefixes
    anchor: prefixes
  - name: Commands tab
    anchor: commands-tab
  - name: Hotkey and persistence
    anchor: hotkey-and-persistence
---

## CommandPalette

Press the hotkey (`ctrl.shift.p` by default) and a small window opens over the
network you are in: one input, a ranked list, and a footer that always says
what Enter will do to the row you are on. Type to filter, Up and Down to move,
Enter or a click to act, Esc to close. Clicking anywhere else closes it too.

The list is fed by [FNS_CommandRegistry](/docs/fns-commandregistry/): every
command any installed FNS tool declares, without the tools knowing this
palette exists. TouchDesigner's own palette components are in the same list,
read from the Palette Browser's model, so your own palette folders are
included; Enter on one places it into the network you came from, right of
everything and selected.

Ranking cares about **where you were when you opened it**. The palette takes a
snapshot of your context before its window can take focus, and a command
whose context that snapshot satisfies ranks first, most specific first: a
command about the parameter under your mouse, then one about the current or
selected operator, then one about the network, then general commands, then
components. A command whose context is missing is dimmed and refused rather
than run into nothing. Badges are coloured by kind, and context commands carry
a small `par` / `op` / `net` tag so the reason for a row's rank is visible.

A command that declares parameters does not run on Enter; it walks them one
at a time. A menu parameter becomes pick rows filtered as you type, the rest a
text field whose placeholder names the parameter, its type and its default.
Enter accepts (empty keeps the default), Left steps back a parameter, Esc
backs out to the list.

## Prefixes

A leading character scopes the query. With nothing typed the footer shows
them.

| Prefix | Scope |
|---|---|
| `>` | Commands only: your tools' commands first, then TouchDesigner's own built-in commands, badged `TD` |
| `?` | Tool commands only, built-ins left out |
| `=` | Components only |
| `/`, `./`, `../` | Navigate the network: `/` is the root, `.` or `./` is where you came from, each `..` goes up a level |
| `~` | Public methods of the promoted extensions on the selected COMP, else the current one, else the network you came from |
| `#` | One tool's commands: `#` lists the tools, `#QuickMarks ` lists that tool's commands |

Navigation and tool rows drill in with Right and back out with Left, keeping
whichever convention you are typing in. A method runs through the COMP, so
the palette can only call what the COMP itself exposes; arguments typed after
the name (`~SetLevel 0.5`) are passed along, and a method whose required
arguments are missing is refused with the footer saying how many it needs.

Ctrl+D stars the selected command or component; starred rows lead within
their tier. Ctrl+H hides the selected command from the palette; the Commands
tab shows it again. Alt+Up and Alt+Down cycle the queries you have run
before.

**Presets.** Alt+S saves the selected command under a name of your own. Press
it in the middle of a parameter walk and the values entered so far are baked
in, the rest taking their defaults, so `Set volume` with `level=0.5` becomes a
one-keystroke row. Presets show a `PRESET` badge, rank just above the command
they wrap, run on Enter without prompting, and can be starred. A preset over a
hidden command still runs, since saving it was the opt-in. Ctrl+H on a preset
deletes it.

## Commands tab

The palette contributes a **Commands** tab to [FNS_Hub](/docs/fns-hub/):
every registered command, hidden ones included, with its tool and context.
Click **Star** to star it and **Hidden** to hide or show it; your choice
beats the tool's own default in both directions. A filter field narrows the
list, Refresh rebuilds it, and Open palette does what the hotkey does.
TouchDesigner's built-in commands show `built-in` in their Context cell.

## Hotkey and persistence

The hotkey lives on the tool's `Hotkey` parameter, so
[FNS_HotkeyManager](/docs/fns-hotkeymanager/) lists it, checks it for
conflicts and rebinds it. Which display the window opens on is set by the
window placement parameters on the same page.

Favourites, presets and hidden commands are keyed by tool and command id,
the same identity the launcher's tray app uses, so they survive a tool moving
in the network. They and the query history persist through
[FNS_ConfigRegistry](/docs/fns-configregistry/), so under global scope they
follow you between projects and under project scope they stay in the `.toe`.
