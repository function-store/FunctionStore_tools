---
package: SlideShow
summary: 'A slideshow of a folder of images: timed or stepped with next and previous, in order or random, with a crossfade between slides and a fitted output resolution.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Output
    anchor: output
  - name: Parameters
    anchor: parameters
---

## What it is

Point SlideShow at a folder and it plays the images in it. Give it a Period and it moves on by itself; set the Period to zero and step through with Next and Prev. Random shuffles the order and draws a new shuffle each time the folder has been played through. Every change crossfades from the old slide to the new one, and each image is fitted to the output resolution.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Output

- **out1** (TOP): the current slide, crossfading into the next.

## Parameters

### Custom

- **Res** (Float, two values): the output resolution, 1920 by 1080 unless you set it.
- **Folder** (Folder): the folder of images to play.
- **Select** (Int): the slide shown now. Next, Prev and the timer set it, and you can set it yourself too.
- **Period** (Float): seconds per slide. Zero stops the timer so the slides change only on Next and Prev.
- **Crossfade Opacity** (Float): how strongly the previous slide lingers through the crossfade.
- **Random** (Toggle): shuffle the order.
- **Next**, **Prev** (Pulse): step forward or back one slide.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
