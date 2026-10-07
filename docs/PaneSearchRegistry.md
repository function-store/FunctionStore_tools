---
status: landed
summary: FNS_PaneSearchRegistry, the eleventh registry, opens each network editor pane's find bar to contributed widgets the way the navbar is open; SearchFix becomes its first contributor.
since: 2026-10-01
verified: 2026-10-01
skill: fns-registry
---

# PaneSearchRegistry: the find bar as an open surface

Owner, 2026-10-01: the find bar should take contributions from any tool or
developer, not only from SearchFix. That is what the registries are for: a
surface that does not know its contributors (docs/RegistryScheme.md).

**It adds containers to the bar, nothing else** (owner, 2026-10-01). The
search itself is not a registry concern: SearchFix replaces it on its own,
and nothing contributes results or filters through the registry.

## The surface

`/ui/panes/pane_find/<pane name>`: one container per network editor pane,
made by TouchDesigner the first time that pane's find bar opens, kept after
it closes (verified while building SearchFix, docs/SearchFix.md). Its own
controls hang off `emptypanel` by their COMP connectors and are ordered by
`alignorder`: search 0, back 1, forward 2, label 3, Home 3.5, filler 4,
close 5.

Closest existing surface: the navbar (`/ui/panes/panebar/<pane>`), which
COPIES each widget into every pane's bar. Copies, not mirrors, because a
contribution may keep per-pane state (SearchFix's Deep and depth are per
pane).

## v1

1. **The master**, `/FNSTools/FNS_PaneSearchRegistry`, a core package like
   the other ten, promoted to `/sys/FNS_Registries/FNS_PaneSearchRegistry`
   (newest version wins, never prompts). Built fresh rather than copied:
   the toolbar master's Registration page (minus Barwidth and Helpurl), its
   `ExtUtilsMinimal` and `FNS_About` copied in, a new
   `PaneSearchRegistryExt`. `FNS_About` stays dormant
   (`initextonstart` off) as in every registry master: switched on, its
   module's first line finds no docked ExtUtils and the class never
   defines.
2. **Hosts.** A contributor stamps a host with the master's `StampHost`
   (`Comp` = its panel, `Canonicalname`, `Menuorder`, `Autoregister`), like
   every other registry. Unregister removes its copies; a reinit is not a
   removal.
3. **Injection.** The global copies every registered widget into every find
   bar as `psr_<Canonicalname>`: hung off `emptypanel`, `alignorder`
   between Home and the filler in Menuorder, display on. A new find bar (a
   pane opening its bar for the first time) gets them a frame later, through
   an OP Execute on `pane_find` (the periodic heal watch is off in
   RegistryBase). A copy is made quiet the way the navbar makes its copies
   (hosts inside it off) and cut loose from the source's files. A copy is
   kept while its source is the same operator, so its per-pane state
   survives; `RefreshWidget()` replaces them all.
4. **SearchFix moves onto it.** Its checkboxes, Deep field and their DATs
   become a registered widget. The search patch itself (the results bridge,
   switching TD's tscript handlers off) stays SearchFix's: it is a
   replacement of TD's search, not a contribution to the bar.
5. **Shipping.** Core package, catalog entry, user doc, a `pre_release`
   hook running the common strip, `requires` derived for SearchFix, the
   fns-registry skill's list and RegistryScheme updated, cold test.

## Verified (2026-10-01, TD 2025.33070)

- The master promotes: `/sys/FNS_Registries/FNS_PaneSearchRegistry`,
  `op.FNS_PANESEARCHREGISTRY`, status "Idle (global)".
- SearchFix's host registers `bar_template`; both open find bars got
  `psr_SearchFix`, hung off `emptypanel` at alignorder 3.6, Deep off,
  depth 3, the results bridge pointing into it, TD's handlers off.
- A find bar opened afterwards (pane3) got the copy and SearchFix's patch
  within 10 frames.
- Searching through the copy: from `/` with Deep on, `SimpleScene` found 8
  results and fed the bar's own `results` (label "1 of 8").
- With a find bar open, the copy kept its operator id across 900 frames.

**A TouchDesigner crash during the build.** TD died between PI adopting the
master and the next call, which created an annotation inside it; the log
ends with the adoption complete and no record of the annotation request.
Neither suspect tested afterwards reproduced it: switching the master's
external tox on (no reload, same op id) and the heal tick (which turned out
to be off, so it never ran), and creating that same annotation again after
the restart, with the project saved first, went through cleanly. The cause
is not known. The master was
restored from its tox with `loadTox`, re-adopted, and the host re-stamped;
switching `enableexternaltox` on did not mark anything dirty, so the master
and the root were saved explicitly.

## Not in v1

- A Hub configurator tab (order and visibility per widget). The toolbar and
  navbar have one; Menuorder on the host is enough to start.

Name: `FNS_PaneSearchRegistry`, the owner's latest wording (the first was
`FNS_PaneFindRegistry`).
