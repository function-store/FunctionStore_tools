---
package: FNS_Autosave
summary: Save the project on a timer, without touching the timeline or interrupting a show
features:
  - name: Saving on an interval
    anchor: saving-on-an-interval
  - name: Staying out of the way
    anchor: staying-out-of-the-way
---

## Saving on an interval

Set an interval and leave it on. The save is driven by a Timer CHOP
rather than the timeline, so it does not depend on the project playing
and does not move anything you are working with.

Two modes, because people mean different things by "save":

- **TD** uses TouchDesigner's own Save, honouring your *Increment
  Filename when Saving* and *Copy to Backup Folder* preferences — so if
  you like numbered saves, you keep getting them.
- **Overwrite** holds that increment preference off for the duration of
  the save, so every save lands back in the file you already have open,
  however the preference is set.

## Staying out of the way

**Only if modified** skips the save when nothing has changed, so an idle
project is not rewritten every few minutes. **Skip while performing**
suppresses saves in Perform Mode, because the middle of a show is the
worst possible moment for a disk write.

Nothing is saved until you turn it on: it arrives inactive, and the
status line tells you when the last save happened and when the next one
is due.
