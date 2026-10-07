---
package: FNS_MediaBrowser
summary: 'See every media file your project uses, find the missing ones, and replace them in place'
features:
  - name: The media list
    anchor: the-media-list
  - name: Replacing and repointing
    anchor: replacing-and-repointing
---

## The media list

Every movie, image, audio file and geometry file your project references,
in one list, with the operator that uses it. Filter to **missing only** to
see what would break on another machine before it breaks there.

The browser is the **Media** tab of [Hub](/docs/fns-hub/) (the **FNS** button in
the main-menu bar), and **Open Browser** on the tool opens it in a window of its own.

TouchDesigner's own shipped defaults are ignored, so the list is your
media, and leaves the installation's out. FNSTools' own files are left out
too, except your media inside it: TimelineTools' movie and audio file are
listed, once each, without its internal players. A tool you placed in your own
network (a scene changer, a sequencer) is listed like the rest of the project.

## Replacing and repointing

Pick a file and choose another, and the parameter is rewritten in place
from the list, wherever its operator sits in the network. A file
picked from inside the project folder is stored project-relative, so the
swap survives the project moving.

Sequence patterns are preserved as patterns, and the same relink rules apply that Collect uses, so the two tools never
disagree about what a path means.
