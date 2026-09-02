---
package: SetSmoothness
summary: Set Input and Viewer Smoothness on TOPs from the toolbar, without opening the Common page.
features:
  - name: Set Input/Viewer Smoothness
    anchor: set-inputviewer-smoothness
    icon: Set Smoothness.png
---

## Set Input/Viewer Smoothness

Sets the **Input Smoothness** and **Viewer Smoothness** parameters that live on
every TOP's *Common* page, from a toolbar menu instead of a parameter dialog.

Click the toolbar button, pick a filtering mode, and it is written to the
**selected** TOPs. Hold `Alt` while you pick and it goes to **every TOP in the
current network** instead. The button's own tooltip says so: *"Press ALT to set
all in a Comp."*

The two settings are separate on purpose. Input Smoothness is how a texture is
sampled as it comes into an operator; Viewer Smoothness is how it is filtered
when drawn on screen. Setting either to **Use Input** leaves each TOP's existing
value alone, which is how you change one without disturbing the other.

This is a nearest-neighbour hunt more than anything else: pixel art, LED maps and
anything on a low-resolution grid needs `nearest`, and TouchDesigner defaults to
`linear`; switching a dozen TOPs by hand through the Common page is
the chore this replaces.

Both actions are also quick-launch commands, **Smoothness → selected** and
**Smoothness → all**, so they can be fired from
[FNS_CommandKit](/docs/fns-commandkit/) with no toolbar button at all.
