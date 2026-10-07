---
package: FNS_Collect
summary: 'Gather every external file your project references into the project folder, then save'
features:
  - name: Collect All & Save
    anchor: collect-all-save
  - name: The plan comes first
    anchor: the-plan-comes-first
---

## Collect All & Save

A project that points at files scattered across your drive is a project
that breaks the moment you move it, hand it over, or take it to a venue.
Collect finds every File-style parameter whose value is a real file
**outside** your project folder, copies each one into
`{project}/collected/<category>/`, rewrites those parameters to
project-relative paths, and saves the `.toe`.

FNSTools' own files are left out, so the toolkit's tools keep pointing where
they do. Your media inside it is collected: TimelineTools' movie and audio file
are copied like any other, and its players and waveform follow the new path. A
tool you placed in your own network (a scene changer, a sequencer) is collected
like the rest of the project.

Collect is the **Collect** tab of [Hub](/docs/fns-hub/) (the **FNS** button in the
main-menu bar), and **Open UI** on the tool opens it in a window of its own.

Copying is chunked, so a folder of large movies does not freeze the UI.

## The plan comes first

Nothing is copied until you have seen what would happen. The first run is
always a **dry run**: it reports the files it found, grouped by category,
and only then do you confirm. You can include or exclude individual files
before applying.

Expressions are left alone by default: freezing an expression that
happens to evaluate to a path would detach live wiring, with nothing gained over a
value. Turn **Collect Expressions** on if you want them resolved too.
