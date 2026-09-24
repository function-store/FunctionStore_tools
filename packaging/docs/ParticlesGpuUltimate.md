---
package: ParticlesGpuUltimate
summary: 'A GPU particle system driven by images: a thresholded source emits particles, look, life, turbulence, wind and force fields shape them, a fluid simulation can carry them, with raw colour, position and optical-flow inputs and one rendered output.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

ParticlesGpuUltimate turns an image into a particle system and renders it. The source image is thresholded to decide where particles are born and what colour they carry; Look sets their material, size and fades; Life how long they last and how their life maps to size and alpha; Turbulence and Wind push them with fields that read the image's dark and bright sides differently; Forces adds point, radial or directional fields you place; and the Fluid page runs a fluid simulation the particles can ride, fed by the image, by a raw colour, position or optical-flow input, or by its own splats. The whole thing composites over the source or a background colour and comes out as one TOP.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in_main** (TOP): the source image.
- **in_fluid** (TOP): optional; an image that drives the fluid simulation.
- **in_col_raw**, **in_pos_raw**, **in_optflow_raw** (TOP): optional raw colour, position and optical-flow maps that replace the ones derived from the source.
- **bg** (TOP): the rendered particles over the background.
