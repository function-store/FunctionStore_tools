---
package: PrismTOP
summary: 'A kaleidoscopic prism: the input rendered through instanced, rotating polygon facets in up to three ring patterns, with softness, a chromatic distortion pass, fit and transform, and a dry/wet mix. An alternative for the Tile TOP and the Mirror TOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

A Tile TOP repeats, a Mirror TOP flips; a prism does both through glass. PrismTOP maps the input onto polygon facets, instances them in rings around the centre and renders the result, so the picture is repeated, mirrored and rotated at once, with soft edges between facets, a rotation that can swing on a sine, and a chromatic distortion pass that splits the colours the way a real prism does. Up to three ring patterns stack, each with its own instance count, radius, scale, phase and alpha, and the original sits underneath at its own opacity and scale. Dry / Wet mixes the whole thing against the input.

It is the alternative for the Tile TOP and the Mirror TOP: create either with the alternatives shortcut held and PrismTOP is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (TOP): the image to refract.
- **out1** (TOP): the prism, mixed with the input by Dry/Wet.

## Parameters

### Custom

- **Res** (Int, two values): the render resolution.
- **Operation** (Menu): the composite operation that lays the facets over the original.
- **Orig Opac** (Float) and **Orig Scale** (Float): the opacity and scale of the original image underneath the facets.
- **Fit** (Menu): how the input fits the facets: Fill, Fit Horizontal, Fit Vertical, Fit Best, Fit Outside, Native Resolution.
- **Translate** (Float, two values), **Scale** (Float), **Rotate** (Float): the transform of the facet layer.
- **Sides** (Int): the polygon's number of sides.
- **Softness** (Float): the soft edge of each facet.
- **Rot Sin Amp**, **Rot Sin Phase** (Float): a sine swing added to the rotation.
- **Dry/Wet** (Float): 0 is the input, 1 is the prism.

### Patterns

- **Pattern** (Sequence): up to three rings of facets, each with **Instances** (Int), **Radius**, **Instance Scale**, **Phase** and **Alpha** (Float).

### Chroma

- **Layers** (Int), **Chromatic** (Float), **Distortion** (Float): the chromatic distortion pass, how many colour layers it splits into and how far they spread.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
