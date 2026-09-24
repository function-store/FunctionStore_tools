---
package: ComplexMix
summary: 'A GLSL TOP that combines two UV fields as complex numbers: add, subtract, multiply, divide or raise one to the other, optionally weighted by a third input, then samples an image through the result.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Parameters
    anchor: parameters
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

## Parameters

### Custom

- **Operation** (Menu): how the two operands combine (input 2 is Op1, input 3 is Op2, read from their red and green channels): Op1, Op2, Add, Subtract, Multiply, Divide, Power1**2 (Op1 to the power Op2), Power2**1 (Op2 to the power Op1).
- **Weighting** (Toggle) and **Fn Weight** (Float): scale Op1 by one minus the weight and Op2 by the weight before they combine; 0 is all Op1, 1 is all Op2, default 0.5.
- **Aspect** (Toggle): apply the transform in aspect-corrected space so rotation and scale stay round.
- **Transform Order**, **Trans**, **Rot**, **Scale**, **Pivot**: a transform applied to the combined coordinates, with its order of operations.
- **Extend** (Menu): what a sample of input 1 outside the image returns: Hold, Zero, Repeat or Mirror.
- **Blend** (Float): mix between plain screen coordinates (0, input 1 unchanged) and the combined, transformed coordinates (1).

### Common

- **Resolution**: the size of the built-in UV map when nothing is wired into input 1 (1280 by default); with input 1 wired, the outputs follow it.
- **Input Smoothness**, **Viewer Smoothness**, **Pixel Format**: the sampling filters and the pixel format; keep a float format when the UV output feeds another Complex tool or a Remap.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
