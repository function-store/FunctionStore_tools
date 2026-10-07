---
package: CookBar
summary: A bar above every operator in the network you are viewing, showing how long it takes to cook and how much GPU memory it holds, so the expensive parts of a network stand out at a glance.
features:
  - name: Turning it on
    anchor: turning-it-on
  - name: Reading the bars
    anchor: reading-the-bars
  - name: Global Hog CHOP
    anchor: global-hog-chop
    icon: HogCHOP.png
  - name: What it changes in your network
    anchor: what-it-changes-in-your-network
---

## Turning it on

Click its toolbar button, run **Toggle cook bar** from quick-launch, or switch
**Active** on. Cook Bar draws behind the network in the network editor you are
working in, and follows you as you move between networks and between panes.
The button lights up while the bars are on, whichever way you switched them.
Right-click it to open Cook Bar's parameters, like the other toolbar tools.

With two panes showing the same network, the bars fit the one you are working
in: the two share one background.

It needs the timeline playing. While the timeline is paused, **Active** is
greyed out and the bars stop; they come back when you press play.

**Max OPs** sets how many operators get bars at once, starting from the
middle of the view: 100 unless you change it, up to 250. Only operators in
view count. More bars cost GPU time, measured on a 1536x700 pane:

| Max OPs | GPU per frame |
|---|---|
| 50 | about 0.1 ms |
| 100 | about 0.25 ms |
| 250 | about 1.4 ms |

A bigger pane costs more in proportion to its size.

## Reading the bars

**The top bar is cook time**, CPU and GPU together.

- It fills across the operator as cook time rises to 1 ms, going from green
  through yellow to red.
- Past 1 ms it grows taller, up to ten times its height, fading as it goes.
- Moving stripes mean the operator cooked this frame or the last one. A dim,
  still bar means it is not cooking right now.

**The bottom bar is GPU memory.** It fills across the operator up to 100
million pixel channels (about three 4K RGBA textures) and grows taller past
that. Operators that hold no GPU memory have no bottom bar.

**On a COMP**, the top bar adds the COMP's own cook time to everything inside
it, and the bottom bar counts the GPU memory of everything inside it.

## Global Hog CHOP

Ctrl+right-click the toolbar button (Ctrl or Cmd on macOS), press **Open Global Hog CHOP** on the
CookBar page, or run **Open Global Hog CHOP** from quick-launch, to open the
parameters of a global **Hog CHOP**. Switch it on,
dial in how much of each frame it eats, and watch how the rest of your patch
copes when it is starved of cook time, with the bars showing where the time
goes. It ships switched off.

While the Hog is on, the toolbar button turns red, so a stress test is never
left running by accident.

## What it changes in your network

The bars are a background image. While Cook Bar is on, it changes three things
in the network you are viewing, so nothing covers the bars:

- it places a hidden Select TOP there to show them;
- it switches off the display flags of that network's TOPs;
- it lowers the back colour of every annotation to **Annotation Alpha** (0.2
  unless you change it on the CookBar page). An annotation that is already
  fainter stays as it is.

When you leave the network or turn Cook Bar off, it removes the hidden
operators and puts the display flags and annotation colours back the way they
were. It does the same just before you save the project, and draws again right
after, so a saved project never keeps them. Removing Cook Bar while it is on
puts the network back too.
