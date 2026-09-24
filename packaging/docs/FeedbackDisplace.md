---
package: FeedbackDisplace
summary: 'A feedback loop with a displace stage inside it: opacity, crossfade, filter size, displacement driven by a built-in noise or a second input, a per-pass transform, reset and a dry/wet mix. The alternative for the Feedback TOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

A Feedback TOP on its own gives you the loop and nothing else; the rest is always the same handful of operators around it. FeedbackDisplace is that handful in one node: the loop, a composite with an opacity, a blur, a displace stage that warps every pass by an animated noise or by whatever you wire into the second input, a transform applied per pass for drift, zoom and spin, a reset, and a dry/wet mix against the input. Trails, smears, liquid echoes and infinite zooms come from the parameters instead of from rebuilding the chain.

It is the alternative for the Feedback TOP: create a Feedback TOP with the alternatives shortcut held and FeedbackDisplace is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (TOP): the image fed into the loop.
- **in_displace** (TOP): optional; a displacement map that replaces the built-in noise.
- **out1** (TOP): the loop's output, mixed with the input by Dry / Wet Mix.

## Parameters

### Feedback

- **Operation** (Menu): the composite operation that lays the new frame over the loop.
- **Opacity** (Float): how much of the previous pass survives; close to 1 for long trails.
- **Cross** (Float): crossfade between the input and the loop before compositing.
- **Filter Size** (Int): the blur applied inside the loop each pass.
- **Aspect Correct** (Toggle): keep the displacement isotropic on non-square images.
- **Displace Weight** (Float, two values): the strength of the displacement in x and y.
- **Source Midpoint** (Float, two values): the displace map value that means no displacement.
- **UV Weight** (Float): how much the displacement follows the map's own UV.
- **Displace Period**, **Displace Amplitude**, **Displace Speed** (Float): the built-in noise that drives the displacement when nothing is wired into the second input.
- **T** (Float, two values), **Rotate** (Float), **Scale** (Float, two values): the transform applied to the loop every pass, for drift, spin and zoom.
- **Reset** (Momentary): clear the loop while held.
- **Dry / Wet Mix** (Float): 0 is the input, 1 is the loop.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
