---
package: RealRamp
summary: 'A GLSL ramp with a true phase and period: vertical, horizontal, radial or circular, repeating or mirroring, so an animated phase never drifts or snaps the way a keyed Ramp TOP can.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

The Ramp TOP is a keyframed gradient, which is the right tool for a designed palette and the wrong one for a driven gradient: a phase that runs past the last key snaps, and a period is a matter of stacking keys. RealRamp computes the gradient in a shader from a phase and a period, in four geometries, and extends it by repeating or mirroring. Drive Phase from a CHOP and the ramp cycles smoothly forever.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (TOP): optional; sets the output resolution when connected.
- **out1** (TOP): the ramp.

## Parameters

### Custom

- **Resolution** (Int, two values): the output size when nothing is wired into the input; with an input the ramp takes its resolution.
- **Type** (Menu): Vertical and Horizontal are linear, Radial sweeps around the centre, Circular grows outward from it.
- **Phase** (Float): offsets the ramp along its direction, in periods. Constant 0 by default; drive it with an expression or a CHOP to scroll the ramp.
- **Period** (Float): the length of one cycle in UV units; smaller values repeat the ramp more often, 0 outputs black.
- **Extend** (Menu): past one period, Repeat restarts at black and Mirror runs back down for a seamless ping-pong.
- **Viewer Smoothness**, **Pixel Format**: the display filter and the pixel format; the default 32-bit float keeps the ramp free of banding, 16-bit float is usually enough. Input Smoothness is present so the toolkit's smoothness tools can set it, but the ramp never samples its input, so it has no visible effect.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
