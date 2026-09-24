---
package: ParticlesGpuUltimate
summary: 'A GPU particle system driven by images: a thresholded source emits particles, look, life, turbulence, wind and force fields shape them, a fluid simulation can carry them, with raw colour, position and optical-flow inputs and one rendered output.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

ParticlesGpuUltimate turns an image into a particle system and renders it. The source image is thresholded to decide where particles are born and what colour they carry; Look sets their material, size and fades; Life how long they last and how their life maps to size and alpha; Turbulence and Wind push them with fields that read the image's dark and bright sides differently; Forces adds point, radial or directional fields you place; and the Fluid page runs a fluid simulation the particles can ride, fed by the image, by a raw colour, position or optical-flow input, or by its own splats. The whole thing composites over the source or a background colour and comes out as one TOP.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in_main** (TOP): the source image.
- **in_fluid** (TOP): optional; an image that drives the fluid simulation.
- **in_col_raw**, **in_pos_raw**, **in_optflow_raw** (TOP): optional raw colour, position and optical-flow maps that replace the ones derived from the source.
- **bg** (TOP): the rendered particles over the background.

## Parameters

### Source

- **Source Res** (Int, two values): the resolution the source is sampled at.
- **Comparator** (Menu), **Source Threshold** (Float): which pixels emit particles.
- **OverUnderLay Source** (Menu), **Under Opac**, **Operation**, **Opac** (Float, Menu, Float): how the source composites with the particles.
- **Comp Over Background Color** (Toggle), **Bgcolor** (RGBA): the background.

### pGpu

- **Render Res** (Int, two values), **Create** (Menu), **Max Particles in Simulation** (Int), **Birth** (Int), **Random InitPos** (Toggle): the simulation's size and how particles are created.
- **Camera** (COMP), **Projection Blend** (Float), **Light** (COMP): the render's camera and light.
- **Hit Behaviour** (Menu), **Speed**, **Drag** (Float), **Pause** (Toggle), **Reset** (Pulse).

### Look

- **Material** (Menu), **Open MAT** (Pulse), **SOP** (Menu), **Particle Size Max** (Float), **Compositing** (Menu), **Alpha Threshold** (Float).
- **Fade In**, **Fade Out**, **Fade to Color**, **Fade to Alpha**, **Fade to Size** (Float): how particles appear and vanish.
- **Col to Size Map** (Menu), **Col to Size Cross**, **Exponent Value**, **Size Mod Invert** (Float): size from colour.

### Life

- **Life Type** (Menu), **Life**, **Life Max**, **Lifevariance**, **Exponent Value**, **To Range** (Float): the lifetime and how it maps.
- **Random InitPos**, **InitPos/CurrPos** (Toggle), **RGB** (Menu): where life is sampled from.

### Turb and Wind

- Each has a gain, an effector exponent and an RGB channel, then a **Dark Side** and a **Bright Side** set of vectors and magnitudes, so the field pushes the dark and the bright parts of the image differently, plus an **InitPos/CurrPos** toggle for where the effector is sampled.

### Forces

- **Forces** (Sequence): per force a **Force Type** (Menu), **Forcepos** (three values), **Force Radius**, **Force Amount** (Float) and **Forcedir** (three values).

### FLUID

- **Output Res**, **Sim Res** (Int, two values), **Optical Flow Magnitude** (Float), **Enable Fluid** (Toggle), **Fluid as Source** (Float).
- **Verticalstrength**, **Force Map Velocity Strength**, **Output Max Lum**, **Palette Flow**, **Splat Flow**, **Density Flow**, **Decay**, **Pressure Passes**, **Color Diffusion**, **Velocity Diffusion**, **Vorticity**, **Pressure** (Float, Int for passes): the fluid solver.
- **Pulse** (Pulse), **Time** (Float): a splat and the simulation clock.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
