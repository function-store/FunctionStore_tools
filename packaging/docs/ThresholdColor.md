---
package: ThresholdColor
summary: 'A Threshold TOP that keeps the colour: the pixels that pass the test come through in their original colour, with a soft edge, instead of as white.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

TouchDesigner's Threshold TOP answers a yes or no question per pixel and paints the answer white on black. ThresholdColor asks the same question and keeps the pixel's own colour instead: the Comparator names the pixels that are removed (with Less, every pixel below the threshold goes black), every other pixel keeps its exact RGB, and Soften feathers the boundary. It is the usual first step for isolating the bright or dark part of a picture without losing its colour.

It is the alternative for the Threshold TOP: create a Threshold TOP with the alternatives shortcut held and ThresholdColor is offered in its place, wired into the same spot.

## Inputs and output

- **in1** (TOP): the image to threshold.
- **out1** (TOP): the image with only the passing pixels, in colour.
