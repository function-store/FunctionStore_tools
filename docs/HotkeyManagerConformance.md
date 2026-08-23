---
status: in-force
summary: Why FNS_HotkeyManager persists only declared sources and reads defaults off the parameter -- the reasoning behind the conformance rules.
since: 97bda12 2026-08-21
skill: fns-hotkey-conformance
---

# FNS_HotkeyManager — the reasoning

**The conformance rules moved to a skill.** Discovery shapes, silent exclusions,
the parameter-mode contract, value format, naming, persistence and defaults now
live in `.claude/skills/fns-hotkey-conformance/SKILL.md` — load
`/fns-hotkey-conformance` before touching a binding. This file keeps only *why*
those rules are what they are.

## Why persistence is declared, not automatic

Inside the tools package every binding persists; outside it, only a binding
carrying (or contained by) the `FNS_hotkeys` tag does. The asymmetry is
deliberate: **a stored path means something different in every `.toe`**. A
`/project1` keyboardin is a different operator in every project, so roaming it
through the user palette would push one project's bindings onto another's
unrelated operators. Declaration is the user saying "this one is mine, not this
project's".

The same reasoning drives the merge rule: rows that came from the config file
but do not resolve in the current project ride along untouched rather than being
dropped, so opening project B can never erase project A's bindings.

## Why defaults live on the parameter, not in a table

A default authored on the par (`default` / `defaultExpr` / `defaultBindExpr`,
selected by `defaultMode`) follows the operator through renames and reparenting;
`Par.reset()` restores value, expression, bind expression and mode as a unit. A
default table keyed by path goes stale the moment a tool moves — and tools moved
a lot during the v3 restructure.

**Keyboard In built-ins cannot participate.** `default*` members are settable on
custom parameters only, and the factory default of `keys`/`shortcuts` is the
empty string — so `reset()` on a keyboardin would *unbind* the hotkey rather
than restore it. That is why those rows still fall back to
`table_gathered_hotkeys1`, and why the recommended shape is a hotkey-named
custom par on the owning COMP with the keyboardin following it by expression.

## Why only `app.osName` expressions survive

Persisting an arbitrary expression would mean persisting whatever it references
— unresolvable in another project. The OS-switch convention is the one shape the
manager can rewrite safely on rebind (Windows half takes the combo, mac half
swaps `ctrl` → `cmd`), so it is the one shape allowed.

## Why the binding is promoted to the tool's parameter

A Keyboard In's `shortcuts` par can hold the combo directly, and for a while
many tools did exactly that. The manager still finds those -- discovery scans
keyboardins as well as COMP pars -- so this is a convention, not a
requirement. It is worth holding anyway for reasons that are not stylistic:

- **Defaults are a parameter feature.** `default`, `defaultExpr`,
  `defaultBindExpr` and `defaultMode` exist on custom parameters only. A
  keyboardin's factory default for `keys`/`shortcuts` is the empty string, so
  `Par.reset()` on a raw keyboardin does not restore the shipped combo -- it
  clears it. Raw rows therefore have to fall back to
  `table_gathered_hotkeys1`, a table keyed by path that goes stale the moment
  a tool is renamed or moved. Promoting the binding is what buys a default
  that travels with the operator.
- **Discoverability without spelunking.** A binding on the tool's Custom page
  is visible to anyone who opens the tool's parameters. One inside `tool/sub/keyboardin1`
  is not.
- **Exactly one editable row.** The follower expression is written *without*
  `app.osName` on purpose: the parameter-mode contract then makes it
  invisible to the manager, so the pair yields one row -- the par -- rather
  than two competing ones.

The cost is that par names become semi-public: ConfigRegistry persists by par
name and the manager stores by path + par, so a later rename silently drops a
user's saved binding. Name them once, carefully.

**State (2026-08-24): swept -- 43 of 44 promoted.**

Eight tools gained a hotkey par and their keyboardin now follows it:
OpToClipboard `Shortcut`, ParOPDrop `Keys`, QuickMarks `Shortcuts`, QuickPane
`Shortcuts` (its existing `Keys` is the held-modifier set, a different thing),
ResetPLS1 `Shortcut`, SetSmoothness `Keys`, SwitchOPs `Shortcut`,
VSCodeTools/ScriptSyncFile `Shortcut`. Values are byte-identical before and
after; only the location changed.

The two FNS_Navbar `parent_hierarchy` keyboardins were **not** what the earlier
note claimed. They already followed their parent's `Keys` -- but through
`parent().par.Keys.eval() if app.osName == 'Windows' else ...`, and because
that expression contains `app.osName` the parameter-mode contract stores it,
so BOTH the par and its follower were listed. The OS switch moved onto the par
(where it is editable) and the follower is now plain, collapsing two rows into
one. Discovery went 46 -> 44 for exactly that reason.

**This is a caveat on the recipe in the skill's 7:** the
`app.osName`-in-the-follower form does put a keyboardin on the `.default` path,
but it also makes the follower visible. Prefer the OS switch on the par and a
plain `parent().par.X` follower.

The single remaining raw row is `ParOPDrop/keyboardin1 [modifiers]`, a CHOP
menu par whose value is `ignore` -- it carries no binding, so there is nothing
to promote.

Side benefit: the long-standing `ctrl.0` conflict now reports as
`ResetPLS1.Shortcut` vs `QuickMarks.Shortcuts` instead of naming two
keyboardins, so it points at something the manager can actually rebind.
