---
package: GlobalVolControl
summary: Set the overall volume of TouchDesigner.
features:
  - name: Mute and Volume
    anchor: mute-and-volume
    icon: GlobalVol.png
---

## Mute and Volume

A speaker button and a slider on the toolbar for TouchDesigner's **application-wide**
output level, the same thing the Audio Device Out settings control, without
opening a dialog.

This is the master level, not a per-operator one: it does not touch the Volume
parameter on any Audio Device Out or Audio Play CHOP, so turning it down leaves
your patch's own mix exactly as you built it. That is what makes it safe to grab
mid-set.

**Mute** silences output without disturbing the slider, so unmuting returns you to
the level you were at.
