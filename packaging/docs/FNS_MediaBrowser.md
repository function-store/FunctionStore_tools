---
package: FNS_MediaBrowser
summary: See every media file your project uses, find the missing ones, and replace them in place
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

TouchDesigner's own shipped defaults are ignored, so the list is your
media, and leaves the installation's out.

## Replacing and repointing

Pick a file and choose another, and the parameter is rewritten in place,
no hunting through the network for the operator that holds it. A file
picked from inside the project folder is stored project-relative, so the
swap survives the project moving.

Sequence patterns are preserved as patterns, with no flattening to the first frame,
and the same relink rules apply that Collect uses, so the two tools never
disagree about what a path means.
