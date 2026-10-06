---
package: ComplexMix
summary: 'A GLSL TOP that combines two UV fields as complex numbers: add, subtract, multiply, divide or raise one to the other, optionally weighted by a third input, then samples an image through the result.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
---

## What it is

ComplexMix is the companion of ComplexOp. Where ComplexOp applies one complex function to the plane, ComplexMix takes two UV fields, treats each pixel pair as two complex numbers, and combines them with a complex operation. Feed it the UV outputs of two ComplexOps and the picture becomes the sum, product or quotient of two warps. A third input weights the combination per pixel, so the mix can follow a mask or an animated gradient.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node. The complex arithmetic is taken from Ricky Reusser's Shadertoy implementation, credited in the shader source.

## Inputs and outputs

- **in1** (TOP): the image that is sampled through the combined coordinates.
- **in2** (TOP): the first complex operand (Op1), a UV map such as ComplexOp's second output.
- **in3** (TOP): the second complex operand (Op2).
- **out1** (TOP): the combined image.
- **out2** (TOP): the combined UV field, for chaining into another sampler.
