---
package: ColorGenPro
summary: 'A cosine palette generator in GLSL: the full coefficient set per channel, an RGB and D mode, a blackout region with a soft edge, and a lookup ramp as a second output.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Parameters
    anchor: parameters
---

## What it is

ColorGenPro builds a palette from the cosine palette formula, `pow(a + b*cos(2PI*(c*t+d)), e)` per channel, with every coefficient open. Offset, amplitude, period, phase and exponent for red, green and blue give smooth gradients that loop cleanly and animate with a single phase; the RGB and D mode collapses them to one offset, amplitude and exponent when you want fewer knobs. Blackout reserves part of the palette for black, either by extending the length or by taking it from the colours, with a soft edge you shape. Length sets how many colours the lookup holds; the palette comes out as a colour strip and as a lookup ramp.

It is the Pro sibling of ColorGen, which shapes its palette with a phase step and exponents instead. It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the image to colour through the palette; with nothing wired, a built-in 0 to 1 ramp is used, so both outputs show the palette on a bare drop.
- **out_col** (TOP): the palette strip.
- **out_lookup** (TOP): the input coloured through the palette.

## Parameters

### Custom

- **Length** (Int): how many colours the palette holds.
- **Input Smoothness** (Menu): the sampling filter of the input.
- **Blackout** (Float, 0 to 1): what share of the length is black; enables the soften parameters.
- **Reductive** (Float, 0 to 1): at 0 the blackout extends the palette length, at 1 it keeps the length and takes from the colours.
- **Soften Black** (Float, 0 to 1, 0 is a hard edge), **Soften Exponent** (Float), **Soften Extend** (Menu: Mirror, Zero/Hold, Repeat): the soft edge around the blackout and how it extends.
- **a (Offset)**, **b (Amplitude)**, **c (Period)**, **d (Phase)**, **e (Exponent)** (Float, three values each): the per channel coefficients of the palette formula. The palette is clamped at zero before the exponent, so an offset below the amplitude cannot produce invalid pixels.
- **RGBD Mode** (Toggle), **Offset**, **Amplitude**, **Exponent** (Float): generate the three d (Phase) values from one offset, amplitude and exponent instead of typing them.
- **Default** (Pulse): restore the shipped coefficients and the RGBD values.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
