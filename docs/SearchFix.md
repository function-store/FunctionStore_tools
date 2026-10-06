---
status: landed
summary: FNS_SearchFix replaces the network editor find bar's literal prefix search with a Python search (contains, case-insensitive, wildcards, inside child networks), keeping its arrows and Home toggle; a Legacy toggle brings the old behaviour back.
since: 2026-10-01
verified: 2026-10-01
---

# SearchFix: a find bar that finds things

Owner's ask, 2026-10-01. The find bar of a network editor pane
(`/ui/panes/pane_find/<pane name>`) only finds what you type exactly as the
start of a name, in the network you are looking at. Searching `SimpleScene`
does not find `FNS_SimpleSceneChanger`, and there are no wildcards.

## What is there today (read live, TD 2025.33070)

| Part | How it works |
|---|---|
| Search field `search/text1` | Text COMP, `editablecontinuous`; `parameter1` reads its text |
| The search | `merge1..3` build the tscript `lc -d -s <path>/<text>*`; `eval2` runs it; `convert1` -> `select1` -> `results` |
| `path` | the pane's network, from `../../panebar/$pane/panenav/eval6` |
| Picking a result | `datexec1` on `results`: `opset -C on <path>/<result>`, then `desk -e 4 $pane` when Home is on |
| Back / forward | tscript panel scripts step the `current` row and select + home the same way |
| Home toggle | `home/out1` channel `v1` |
| Close | `neteditor -f 0 -p $pane`, then clears the text |

So the old search is a case-sensitive prefix glob over the current network's
children, run through tscript.

## The list

1. **The package.** `FNS_SearchFix`, depth-1 under `/FNSTools`, adopted into
   PrivateInvestigator, extension `SearchFixExt` in Python. `Active` turns the
   patch on and off; off restores TD's find bar exactly as it was.
2. **Patch every find bar, now and later.** One per pane, named after the
   pane. `/ui` is rebuilt on every project open, so the patch is applied on
   init and to every copy that appears later (a watcher on `pane_find`).
   To verify while building: a second pane's find bar arrives as
   `pane_find/pane2`.
3. **Search in Python.** A Script DAT in each find bar feeds `results`;
   TD's tscript chain is left in place, unwired, so Active off reconnects it.
   - Default: case-insensitive, matches anywhere in the name.
   - Wildcards when the text has `*`, `?` or `[...]`, matched the way
     `tdu.match` / `fnmatch` match.
   - Several words: every word must match.
   - Ranking: exact name, then prefix, then contains; shallower first.
   - Scope and caps: see open questions.
4. **Pick, step and home in Python.** Back, forward and the result pick go
   through `ui.panes`: enter the result's network if it is deeper, make it
   current and selected, and home on it when Home is on. TD's tscript
   handlers are switched off while the patch is active and back on when it is
   not.
5. **Legacy toggle**, off by default: the old prefix, case-sensitive,
   current-network search, in Python. A parameter on the tool and a toggle
   in each find bar.
6. **Shipping.** Catalog entry, `packaging/docs/FNS_SearchFix.md`, a
   `pre_release` hook that runs the common strip, a release-notes line.

## Decided (owner, 2026-10-01)

- **The controls go through a registry** (owner, 2026-10-01, superseding
  "no registry yet"): `bar_template` is published into every find bar by
  FNS_PaneSearchRegistry (docs/PaneSearchRegistry.md), so any tool or
  developer can add controls there too. SearchFix itself only patches the
  search: the results feed and TD's tscript handlers.
- **Scope is a depth limit per pane**, default 1: this network only, like
  today. Each find bar has its own **Deep** toggle; switching it on shows a
  number field (a copy of TD's Numeric Field basic widget, `Value0` bound to
  the widget's own `Depth`) and searches that many levels down. The tool's
  Depth is where the field starts. /ui is rebuilt on open, so a pane's
  values last the session.
  Higher values search inside child networks with
  `findChildren(maxDepth=N)` (`depth=` matches one exact level and finds
  nothing). From `/`, `/ui`, `/sys` and `/local` are skipped.
- **Matching** uses the shared tiered matcher `scripts/shared/FuzzyMatch.py`
  (CommandPalette and SearchPalette run on it): by default its strict tiers
  (exact, prefix, word start, substring); a **Fuzzy** toggle, off by
  default, adds initials, typos and subsequences. A word with `*`, `?` or
  `[` is a wildcard against the lower-cased name.
- **Python only.** Nothing new is written in tscript; TD's tscript handlers
  are switched off while the patch is active.
- **The depth field counts like `findChildren(maxDepth=N)`** (owner,
  2026-10-01): 1 is this network, the same as Deep off, and it can be typed
  with Deep on. 0 finds nothing there (measured: `maxDepth=0` returns no
  operators), so the field stops at 1.

## The shortcut

TD toggles a pane's find bar on Ctrl+F while the network editor has the
keyboard. The bar takes the keyboard as it opens, and from its search field
the shortcut does nothing, which is what read as "never closes" (owner,
2026-10-01). Nothing in TD says whether a bar is open: the container, the
pane bar and the pane's geometry read the same either way.

The first version kept its own open/closed flag per pane and fell out of
phase as soon as TD closed a bar on its own. What works is the search
field's `focus` panel value, read in the Keyboard In DAT's `onShortcut`
before TD handles the key (measured by logging every press): it is 0 on the
press that opens a bar (the field takes focus the same frame) and 1 on every
press made while typing in it. So the tool closes a bar only when its field
has focus, with the bar's own close button pressed and released on separate
frames, and leaves every other press to TD.

## Verified while planning

- A pane's find bar is created the first time it opens: opening pane2's with
  `neteditor -f 1 -p pane2` made `pane_find/pane2`, a full copy whose
  `path` names that pane's network. It stays after the bar is closed.
- The network editor pane API covers picking: `owner` is settable,
  `home(zoom, op)` and `homeSelected(zoom)` exist.
- The label's "nothing found" text reads the same tables as `results`, so
  feeding `results` from Python keeps the label honest.

## Still open

- **Cost.** The field edits continuously, so the search runs per keystroke:
  cap the number of results as well as the depth.
