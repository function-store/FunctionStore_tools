---
package: FNS_TimelineRegistry
summary: 'Publish a widget into TouchDesigner''s timeline bar: transport controls beside the stock ones, an entry on the time-properties block, or a full-width strip in the frame-ruler band that gets its own row.'
features:
  - name: Timeline Registry
    anchor: timeline-registry
  - name: The three zones
    anchor: the-three-zones
  - name: For tool authors
    anchor: for-tool-authors
---

## Timeline Registry

TouchDesigner's timeline bar is a fixed piece of chrome. This registry makes it
extensible: a tool publishes a panel COMP and it appears in the bar, in a zone it
picks, without that tool knowing anything about the dialog's layout.

Nothing stock is moved or re-expressed. Contributions are shown through Select
COMP mirrors anchored to TD's own blocks, and `/ui` is never saved with a
project, so the whole surface is rebuilt on every load; the registry
re-registers each time.

It ships as its own core package, promoted to `/sys` (global shortcut
`op.FNS_TIMELINEREGISTRY`), alongside the other surface registries.

**With nothing contributed it claims nothing at all.** The surface appears with
the first registration and disappears with the last, and the bar returns to its
stock height.

## The three zones

- **transport**: beside TD's own play controls, in the existing row.
- **properties**: with the time-properties block at the left.
- **background**: a full-width strip in the frame-ruler band, drawn underneath
  the ruler numbers (TD's own ruler background is transparent, so it shows
  through).

`background` is a **grow** zone: it takes no height out of the
transport row and clipping the controls, it makes the bar taller by its own
height and the bar's fixed-height blocks follow. The dialog height is always
recomputed as base plus growth and never incremented; the bar's height is saved in
the `.toe` while `/sys` is not, so an increment-and-restore scheme would creep
taller every session.

## For tool authors

A tool that wants a timeline widget ships a small **host** copy of this registry,
the same shape as a toolbar or navbar entry. The host's Registration page names
the contribution: the tool COMP, a canonical name, the zone, order, and whether
it is displayed.

From Python, `op.FNS_TIMELINEREGISTRY.RegisterWidget(comp, 'mytool',
zone='transport', order=20)` does the same, with `UnregisterWidget()` and
`SetWidgetZone()` as the rest of the API.

Registration is **not** instantaneous: the entry is stored first and its zone
arrives with the host's parameter a frame later, so anything that depends on the
final zone settles a frame later.

[FNS_TimelineTools](/docs/fns-timelinetools/) is the reference consumer; it uses
`transport` for its own controls and `background` for the media strip.
