---
package: ComplexOp
summary: 'A GLSL TOP that treats the image plane as the complex plane and applies a complex function to it: square, root, exp, log, inverse, the trigonometric and hyperbolic families and their inverses, with iteration, a pre and post transform and a choice of edge handling.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
---

## What it is

ComplexOp reads the UV of every pixel as a complex number, runs it through the complex function you pick, and samples the input image at the result. A square folds the plane once around the origin; a log turns rings into stripes; the trigonometric functions tile and warp the picture in ways a plain Transform TOP cannot reach. The function can be applied several times in a row, and a transform before and after it moves the point of interest to where the function does something worth seeing.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the image to warp.
- **out1** (TOP): the warped image.
- **out2** (TOP): the mapped UV field, for feeding another sampler.
- **borders** (TOP): the border mask, where the mapped UV left the image.
