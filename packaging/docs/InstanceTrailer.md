---
package: InstanceTrailer
summary: 'Turns one moving image into a trail of its recent frames: a cache of the last N frames laid out in a row or column, with the spacing shaped by an exponent, ready to drive instancing.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Parameters
    anchor: parameters
---

## What it is

InstanceTrailer caches the incoming frames and lays the most recent ones out side by side, oldest at one end and newest at the other. Depth says how many, Direction and Expval shape how the samples are spread through the cache, so the trail can bunch up near the present or fan out into the past. The layout is a texture and the sample positions ride out as a CHOP, which is what an instanced geometry needs to draw the trail in 3D.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the frames to trail. The cache records only while something is wired in.
- **out1** (TOP): the laid out trail.
- **out2** (CHOP): the trail as pixel data (one sample per pixel of a second, identical layout, r g b a channels), for instancing or CHOP-side use; the first block is the newest copy and the last block the oldest, matching out1 top to bottom.

## Parameters

### Custom

- **Depth** (Int): the number of delayed copies in the trail, the live frame included; default 10, at least 1.
- **Max Cache Size** (Int): the frames the cache holds (default 300); the trail cannot reach further back, and larger values use more GPU memory.
- **Cache Size** (Int): how many frames back the oldest copy reaches; clamped to Max Cache Size.
- **Direction** (Float, -1 to 1): the direction and strength of the time offset; positive delays the copies into the past, negative reverses the order.
- **Exponent Value** (Float): spaces the delays; 1 is even, higher values bunch the copies near the live frame.
- **Align** (Menu): Left to Right, Right to Left, Top to Bottom, Bottom to Top.
- **Recreate All Operators** (Pulse): rebuild every copy, for example after a large change of Depth.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
