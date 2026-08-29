---
package: FNS_TimelineTools
summary: 'Drive TouchDesigner''s timeline from your media: pick a movie and an audio file, optionally resize the timeline to fit, and see them behind the ruler and the Animation editor as a filmstrip, a waveform and your editor''s markers.'
features:
  - name: Media on the timeline
    anchor: media-on-the-timeline
  - name: 'Scope: which timeline?'
    anchor: scope-which-timeline
  - name: The background
    anchor: the-background
  - name: The waveform
    anchor: the-waveform
  - name: Markers from your editor
    anchor: markers-from-your-editor
---

## Media on the timeline

Pick a **movie file**, an **audio file**, or both. The tool loads them, locks
their playback to the timeline rather than letting them run on their own clock,
and can either resize the timeline to the longest one or trim them to fit the
range you already have.

That last part is a window, not just a length. A timeline whose range starts at
frame 100 is already 99 frames into the song when the range opens, so trimming
from the beginning of the file would play the right *duration* of the wrong
*part*. The media window carries an offset as well as a length, and everything
downstream — playback and drawing alike — reads the same window.

*Sync Timeline to Media* resizes the range to fit; with it off, the media is
trimmed to the range instead. Either way playback stays locked to the timeline.

## Scope: which timeline?

TouchDesigner has more than one timeline. Any component can carry a **local**
timeline with its own range and transport, swapped into the UI with the `S`
button and back out with `/`.

*Scope* picks which one this tool drives: the root timeline, or a named
component's local one. *Ensure Local Timeline* creates a local timeline on that
component if it does not have one — a bare Time COMP is an empty shell, so it is
cloned from the root's rather than created blank.

## The background

The tool draws behind two of TD's surfaces, and it is the **single owner** of
both: the strip in the timeline's frame-ruler band, and the Animation editor's
background. The timeline strip gets its own row rather than stealing height from
the transport controls.

What it draws is a **composite of three layers**, not a choice between them:

- **Filmstrip** — thumbnails sampled evenly across the movie. It is baked once
  on *Build Strip* and then costs nothing; it does not rebuild itself when the
  media changes, which is exactly what keeps it free.
- **Waveform** — the audio, drawn live.
- **Markers** — vertical coloured lines, in front of both.

Each layer has its own *Show* toggle and opacity, per surface, and each has a
toggle and slider in the control row. Hiding one is not merely cosmetic: a
hidden layer stops rendering altogether.

## The waveform

The Animation editor view is **interactive**. The graph can be zoomed and panned, and
the waveform stays pinned between the range markers while that happens — it
scrolls and scales with the view instead of being stretched to whatever is on
screen.

The timeline strip is a different shape and a different job: it is 64:1 and
always holds the whole range, so it works as an overview while the graph view
works as an editing surface. Both are rendered from one set of audio, and
either can be switched off on its own.

*Resolution* is how many points the wave is drawn with across the whole file —
higher reads more detail when you zoom in, at the cost of GPU points. *Wave
Height*, *Wave Color* and *Wave Opacity* are the rest.

## Markers from your editor

Cut your edit somewhere else, then bring the structure back. Point *Marker File*
at a marker list exported from your editor and the tool draws each marker as a
vertical coloured line across both surfaces.

| Where it came from | How to export it |
|---|---|
| DaVinci Resolve | Timelines ▸ Export ▸ **Timeline Markers to EDL** — names and colours come across |
| Premiere Pro | File ▸ Export ▸ **Markers** (CSV) — names come across; Premiere does not put colours in that file |
| Final Cut / Resolve XML | any **FCPXML** with markers in it |
| Audacity | a label track (**Export Labels**) — handy for music you cued by ear |

The format is worked out from what is inside the file, not from its extension,
so a marker list saved under the wrong name still loads.

**Timecodes need to know their frame rate.** *Source Frame Rate* is the rate of
the timecodes **in the file**, not your timeline's — leave it at 0 to assume they
match. Nothing here ever changes your timeline's rate.

*Source Start Timecode* handles sequences that start at `01:00:00:00`, which is
most of them out of Resolve: left on `auto` the tool drops the leading hour so
the markers land where you expect.

*Time Base* decides what a marker time means. **Timeline** is seconds from the
start of your working range and works with no media loaded at all. **Media** ties
markers to the picture, so if the media sits at an offset inside the range the
markers move with it.

**Hover a line to see its name.** The label follows the marker, in both the
timeline strip and the Animation editor, and disappears when you move away.
Names are hover-only on purpose: seven of them across a 60-pixel strip would
overlap into noise, and the one you want is the one under the pointer. *Hover
Labels* turns it off; *Label Size* and *Label Color* are the rest.

The remaining look controls: *Marker Color* (used for markers whose file carried
none), *Marker Width* in screen pixels — held steady however far you zoom the
Animation editor — and *Marker Height* as a share of the surface.

Markers are a list, not a property of the media: the table is yours to edit by
hand, add to, or keep across a media change. *Merge On Load* adds a second file's
markers to what is already there instead of replacing them.

**Right-click the strip to author them.** On a line you get Rename, Set Colour and
Delete; on empty strip, Add Marker Here, Add Marker At Playhead and Clear All.
The menu names the marker and its frame, so you always know what you are about to
change.

**Save Markers** writes them back out. *FNS CSV* keeps everything — it is the
tool's own columns, and reading it back gives you exactly what you had.
*Resolve marker EDL* goes back into an edit, but an EDL only knows the sixteen
Resolve colour names and only stores whole frames, so a hand-picked colour is
snapped to the nearest and a marker dropped between frames moves by up to half a
frame. The status line tells you how many of each, rather than letting you find
out in the edit.

Requires [FNS_TimelineRegistry](/docs/fns-timelineregistry/) for the timeline
surface; the Animation editor background works without it.
