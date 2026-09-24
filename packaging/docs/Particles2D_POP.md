---
package: Particles2D_POP
summary: 'A 2D particle simulation as a POP loop: a source image emits particles, curl noise and wind effectors steer them with lookup ranges, trails stretch them, and the loop rides out as points for your own render.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

Particles2D_POP is a particle simulation built on POPs, so it runs on the GPU and hands you points. A source image decides where particles are born; each one gets a life, a mass and a drag, and two effectors move it: a curl noise field with its own speed and a wind with variance, each read through an image lookup so a texture can steer the flow. Trails stretch the points along their motion. What comes out is the point cloud, ready for a Render TOP with your own material, or for any POP that takes points.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in_loopin** (POP): optional; points to carry into the loop.
- **in_source** (TOP): the image particles are born from.
- **in_effector_curl** (TOP), **in_effector_wind** (TOP): optional images that steer the curl and wind effectors through their lookups.
- **out_loopout** (POP): the simulated points.

## Parameters

### Custom

- **Start Pulse** (Pulse): start the simulation.
- **Maximum Particles** (Int), **Birthrate** (Float): how many particles live at once and how fast new ones are born.
- **Life** (Float), **Life Variance** (Float): how long a particle lives, and how much that varies.
- **Initial Mass**, **Initial Drag**, **Velocity Damping**, **Speed** (Float): the physics of each particle.
- **Length** (Float): how far trails stretch the points along their motion.
- **Reset Pulse** (Pulse): clear the simulation.

### Curl

- **Curl** (Float, three values), **Speed** (Float, four values), **Open Curl Noise** (Pulse): the curl noise field and its animation.
- **Rgb** (Menu), **Normalize** (Toggle), **Fromrange**, **Torange** (Float, two values each), **Exponent Value** (Float), **Update** (Toggle): how the curl effector image is read.

### Wind

- **Wind** (Float, three values), **Variance** (Float, three values), **Wind Variance Speed** (Float, four values), **Open Variance** (Pulse): the wind and its variance noise.
- **RGB** (Menu), **Normalize** (Toggle), **From Range**, **To Range** (Float, two values each), **Exponent Value** (Float), **Update** (Toggle): how the wind effector image is read.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
