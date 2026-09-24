---
package: InstanceTrailer
summary: 'Turns one moving image into a trail of its recent frames: a cache of the last N frames laid out in a row or column, with the spacing shaped by an exponent, ready to drive instancing.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
---

## What it is

InstanceTrailer caches the incoming frames and lays the most recent ones out side by side, oldest at one end and newest at the other. Depth says how many, Direction and Expval shape how the samples are spread through the cache, so the trail can bunch up near the present or fan out into the past. The layout is a texture and the sample positions ride out as a CHOP, which is what an instanced geometry needs to draw the trail in 3D.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the frames to trail. The cache records only while something is wired in.
- **out1** (TOP): the laid out trail.
- **out2** (CHOP): the trail as pixel data (one sample per pixel of a second, identical layout, r g b a channels), for instancing or CHOP-side use; the first block is the newest copy and the last block the oldest, matching out1 top to bottom.
