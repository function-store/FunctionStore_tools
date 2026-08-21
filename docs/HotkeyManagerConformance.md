# Conforming to FNS_HotkeyManager

What a tool must do to have its hotkeys discovered, listed, rebindable, conflict-checked
and persisted by `FNS_HotkeyManager`. Source of truth:
[HotkeyManagerExt.py](modules/suspects/FNSTools/FNS_HotkeyManager/HotkeyManagerExt.py).

## 1. Put the binding somewhere discovery looks

Discovery (`Discover()`) is **project-wide**: every top-level COMP under `/` except the
names in the manager's `Excluderoots` par (default `ui sys local`). Inside each root it
finds exactly three shapes:

| Shape | Parameters read | Notes |
|---|---|---|
| **Keyboard In CHOP** | `keys`, `modifiers` | grouped as one row |
| **Keyboard In DAT** | `keys`, `shortcuts` | grouped as one row |
| **COMP custom par** | any par whose name matches | one row per par |

A custom par qualifies only if **all** of these hold:

- style is `Str`, `StrMenu` or `Menu` (toggles are never bindings);
- lowercased name **contains** `key`, `shortcut` or `hotkey`;
- lowercased name contains **none** of: `opshortcut`, `parentshortcut`, `arrowkeys`,
  `savehotkeys`, `loadhotkeys`, `shortcutactive`, `deletekey`.

So `Hotkey`, `Togglekey`, `Menushortcut` are found; `Enablekeyboardshortcuts` (toggle)
and `Opshortcut` are not.

## 2. Things that silently exclude you

- **Path contains** `popMenu`, `popDialog`, `KeyModifiers`, or `FNS_HotkeyManager`.
- **Panel-scoped keyboardins**: a non-empty `panels` par (value or expression) means a
  local control scheme, not a global hotkey — skipped.
- **Empty / falsy raw value**: a binding par that evaluates falsy is not a binding.
- **DAT `keys` holding only modifiers** (`ctrl alt shift cmd esc enter tab`) — that's a
  modifier-listen setup, not a hotkey.
- **Bind followers**: if your par binds to a master that is itself discovered, only the
  master is listed. A follower whose master is undiscovered still shows up.

## 3. Parameter mode contract

Only two modes are externalizable:

- **Constant or Bind** — the value is stored as-is.
- **Expression** — stored *only* if the expression contains `app.osName` (the OS-switch
  convention). Any other expression is invisible to the manager.

On rebind, an OS-switch expression keeps its structure (Windows half gets the combo, mac
half swaps `ctrl` → `cmd`); everything else is written back as a constant. Never point a
hotkey par at some other expression and expect persistence to survive.

## 4. Value format

Space-separated combos; within a combo, `.` or `+` joins parts. Modifiers are matched
against `ctrl/alt/shift/cmd` plus their `l`/`r` variants (`lctrl` normalizes to `ctrl`)
and always emitted in the order `ctrl alt shift cmd`. Character classes expand, so
`ctrl.[0-9]` correctly collides with a literal `ctrl.5`.

```
ctrl.k        alt.shift.r        ctrl.[0-9]        f5 f6
```

A CHOP's `modifiers` menu par is folded in as a prefix of that op's `keys` record — don't
double-declare the modifier in both places.

## 5. Naming, so the row reads well

- **Tool column** = the direct child of the FNS tools root that contains the op; outside
  the package it's the top-level COMP under `/`. Keep bindings inside your tool COMP so
  they group under your tool's name.
- **Path column** = shortcut-relative inside the tools package, full path outside it.
- Use relative references only — the manager resolves stored paths against the tools root,
  then as a root-level path, then as a global shortcut.

## 6. Persistence

- **Inside the FNS tools package**: always persisted. Not user-toggleable.
- **Outside it**: persists only when *declared* — add the tag `FNS_hotkeys` to the
  keyboardin op, or to any COMP containing it (the nearest tagged ancestor wins). The UI's
  Persist cell toggles the tag on the row's own op; a tag inherited from an ancestor must
  be removed at the carrier.
- Undeclared, project-local bindings never leave the project — the same path means
  something different in every `.toe`.

Declared rows go through `ConfigSaveRows`/`ConfigLoadRows` into the user palette via
FNS_ConfigRegistry. Rows that came from the config file but don't resolve in the current
project ride along untouched, so switching projects can't drop another project's bindings.

## 7. Defaults

`Load Default` restores from `table_gathered_hotkeys1` and right-clicking a Hotkey cell
resets that one row. Ship your tool with its intended bindings baked in as constants (or
OS-switch expressions) so a default capture is meaningful.

## Quick checklist

- [ ] Binding lives on a Keyboard In CHOP/DAT (`keys`/`modifiers`/`shortcuts`) or a
      `Str`/`StrMenu`/`Menu` custom par named `*key*`/`*shortcut*`/`*hotkey*`
- [ ] Par mode is Constant, Bind, or an `app.osName` expression
- [ ] `panels` par left empty for global hotkeys
- [ ] Value uses `mod.key` syntax with recognized modifier names
- [ ] Op does not sit under a `popMenu`/`popDialog`/`KeyModifiers` path
- [ ] Outside the tools package: `FNS_hotkeys` tag added if it should persist
- [ ] Verified by opening the manager UI (`Open UI`) and finding your row, with no
      unintended Status conflict
