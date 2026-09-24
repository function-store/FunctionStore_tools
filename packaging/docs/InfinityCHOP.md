---
package: InfinityCHOP
summary: 'A point or a whole curve on one shape that morphs from a circle to the infinity loop: frequency multipliers for Lissajous variations, a trail span, smooth speed with reset, and a size and centre for the output values.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Output
    anchor: output
---

## What it is

InfinityCHOP draws one curve, and Shape decides which: at 0 it is a circle, at 1 the infinity loop, and every value between morphs one into the other. Frequency multipliers bend it further into Lissajous figures, and whole numbers keep it closed.

With Samples at 1 you get a single point travelling along the curve, ready to drive a position, a camera or a light. Raise Samples and the whole curve comes out as that many points, ready to instance or to draw as a line. Span shortens the drawn part into a trail that follows the leading point.

Speed moves the curve by itself in loops per second, and changing it never makes the point jump. Phase places the point by hand, and Reset puts the travelled distance back to zero.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Output

- **out1** (CHOP): two channels, **tx** and **ty**, with one sample per point.
