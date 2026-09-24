---
package: InfinityCHOP
summary: 'A point or a whole curve on one shape that morphs from a circle to the infinity loop: frequency multipliers for Lissajous variations, a trail span, smooth speed with reset, and a size and centre for the output values.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Output
    anchor: output
  - name: Parameters
    anchor: parameters
---

## What it is

InfinityCHOP draws one curve, and Shape decides which: at 0 it is a circle, at 1 the infinity loop, and every value between morphs one into the other. Frequency multipliers bend it further into Lissajous figures, and whole numbers keep it closed.

With Samples at 1 you get a single point travelling along the curve, ready to drive a position, a camera or a light. Raise Samples and the whole curve comes out as that many points, ready to instance or to draw as a line. Span shortens the drawn part into a trail that follows the leading point.

Speed moves the curve by itself in loops per second, and changing it never makes the point jump. Phase places the point by hand, and Reset puts the travelled distance back to zero.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Output

- **out1** (CHOP): two channels, **tx** and **ty**, with one sample per point.

## Parameters

### Curve

- **Samples** (Int): 1 is a travelling point, and more draw the curve as that many points.
- **Span** (Float): how much of the curve the samples cover, in loops. 1 is the whole closed curve, and less is a trail. Active with more than one sample.
- **Shape** (Float): 0 is a circle, 1 is the infinity loop, and values between morph.
- **Frequency** (Float, two values): how many times X and Y swing per loop. Equal whole numbers keep the plain shape, and other whole numbers make Lissajous figures.
- **Cross Frequency** (Float): the cosine that folds Y into the loop's crossing. Active when Shape is above 0.
- **Pinch Frequency** (Float, two values): the pinch that narrows X and Y toward the crossing. Active when Shape is above 0.
- **Phase** (Float): where on the curve the first point sits, in loops.
- **Speed** (Float): loops per second. 0 holds still, and negative runs backwards.
- **Reset** (Pulse): return the travelled distance to zero.
- **Size** (Float, two values): half the width and height of the curve in the output values.
- **Center** (Float, two values): the centre of the curve.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
