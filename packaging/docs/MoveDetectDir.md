---
package: MoveDetectDir
summary: 'Reads which way things move in a camera or any image with optical flow and turns it into left/right and down/up channels, with thresholds, inversion and filtering, for swipe and gesture triggers.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

MoveDetectDir watches an image and tells you which way it is moving. It runs optical flow on the input, measures how much of the flow points left, right, down and up, and when the movement passes a threshold it comes out as two channels: one for left and right, one for down and up. Wave a hand across a camera and the channel swings to the side you swiped to.

Use it to page through a slideshow with a gesture, to steer a scene from a crowd, or to trigger anything that should react to the direction of motion and not just its amount.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (TOP): the image to watch, usually a camera.
- **out1** (CHOP): two channels, **LR** for left and right movement and **DU** for down and up.
