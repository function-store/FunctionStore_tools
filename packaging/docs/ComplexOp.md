---
package: ComplexOp
summary: 'A GLSL TOP that treats the image plane as the complex plane and applies a complex function to it: square, root, exp, log, inverse, the trigonometric and hyperbolic families and their inverses, with iteration, a pre and post transform and a choice of edge handling.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Parameters
    anchor: parameters
---

## What it is

ComplexOp reads the UV of every pixel as a complex number, runs it through the complex function you pick, and samples the input image at the result. A square folds the plane once around the origin; a log turns rings into stripes; the trigonometric functions tile and warp the picture in ways a plain Transform TOP cannot reach. The function can be applied several times in a row, and a transform before and after it moves the point of interest to where the function does something worth seeing.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the image to warp.
- **out1** (TOP): the warped image.
- **out2** (TOP): the mapped UV field, for feeding another sampler.
- **borders** (TOP): the border mask, where the mapped UV left the image.

## Parameters

### Custom

- **Operand/Map** (Toggle): on, the input is an image warped through the function over a screen-space complex plane; off, the input is itself a complex map (a UV image, for chaining).
- **Op** (Menu): the complex function: none, csqr, csqrt, cexp, clog, cinv, cabs2, cconj, csin, ccos, ctan, ccot, csinh, ccosh, ctanh, ccoth, casin, cacos, catan, cacot, casinh, cacosh, catanh, cacoth, cpolar, cpow, cconst.
- **Power** (Float): the base for Logarithm or the exponent for Power; enabled only for those two.
- **Const** (Float, two values): the real and imaginary parts returned by the Constant function.
- **Op Iter** (Int): how many times the function is applied in a row, 1 to 64.
- **Center UV** (Toggle): put the origin of the plane at the image centre (z runs from -1 to 1) instead of the bottom-left corner.
- **Aspect** (Toggle): scale the plane by the image aspect so circles stay round.
- **Transform Order**, **Trans**, **Rot**, **Scale**, **Pivot**: the transform applied to z before the function, with its order of operations.
- **Post Transform Order**, **Post Trans**, **Post Rot**, **Post Scale**, **Post Pivot**: the transform applied to the result.
- **Boundary** (Float): the escape radius; iteration stops once the magnitude exceeds it, 0 disables the test.
- **Borders** (Float, two values): the soft edge of the borders output.
- **Extend** (Menu): what a sample outside the image returns: Hold, Zero, Repeat or Mirror.
- **Blend** (Float): mix between the unwarped coordinates (0) and the warped ones (1); defaults to 1.

### Common

- **Resolution**: the size of the built-in UV map when nothing is wired into the input.
- **Input Smoothness**, **Viewer Smoothness**, **Pixel Format**: the sampling filters and the pixel format; keep a float format when the UV output feeds another Complex tool or a Remap.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
