---
package: CircularDistortionTOP
summary: 'A circular distortion for images: rings of displacement around a centre you place, with phase, frequency, amplitude and a mode blend, and a choice of how the input extends past its edge.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

CircularDistortionTOP pushes the image in rings around a point. Frequency sets how many rings, Amplitude how far the pixels move, Phase spins the rings outward or inward when animated, and Mode blends between the distortion's two characters. Put the centre on a face, a logo or the middle of the frame and drive Phase from a CHOP for a ripple; crank Amplitude for a lens that breathes.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (TOP): the image to distort.
- **out1** (TOP): the distorted image.

## Parameters

### Custom

- **Center** (Float, two values): the point the rings are centred on.
- **Phase** (Float): the position of the rings; animate it to make them travel.
- **Frequency** (Float): how many rings across the image.
- **Amplitude** (Float): how far the pixels are displaced.
- **Mode** (Float): a blend between the distortion's two characters.
- **Input Extend Mode Uv** (Menu): what a displaced sample returns past the image edge.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
