---
package: ColorGenPro
summary: 'A cosine palette generator in GLSL: the full coefficient set per channel, an RGB and D mode, a blackout region with a soft edge, and a lookup ramp as a second output.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Palette behavior
    anchor: palette-behavior
---

## What it is

ColorGenPro builds a palette from the cosine palette formula, `pow(a + b*cos(2PI*(c*t+d)), e)` per channel, with every coefficient open. Offset, amplitude, period, phase and exponent for red, green and blue give smooth gradients that loop cleanly and animate with a single phase; the RGB and D mode collapses them to one offset, amplitude and exponent when you want fewer knobs. Blackout reserves part of the palette for black, either by extending the length or by taking it from the colours, with a soft edge you shape. Length sets how many colours the lookup holds; the palette comes out as a colour strip and as a lookup ramp.

It is the Pro sibling of ColorGen, which shapes its palette with a phase step and exponents instead. It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the image to colour through the palette; with nothing wired, a built-in 0 to 1 ramp is used, so both outputs show the palette on a bare drop.
- **out_col** (TOP): the palette strip.
- **out_lookup** (TOP): the input coloured through the palette.

## Palette behavior

The palette is clamped at zero before the exponent is applied. An offset below the amplitude therefore clips the troughs to black rather than producing invalid pixels.
