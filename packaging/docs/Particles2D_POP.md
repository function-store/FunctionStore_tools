---
package: Particles2D_POP
summary: 'A 2D particle simulation as a POP loop: a source image emits particles, curl noise and wind effectors steer them with lookup ranges, trails stretch them, and the loop rides out as points for your own render.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

Particles2D_POP is a particle simulation built on POPs, so it runs on the GPU and hands you points. A source image decides where particles are born; each one gets a life, a mass and a drag, and two effectors move it: a curl noise field with its own speed and a wind with variance, each read through an image lookup so a texture can steer the flow. Trails stretch the points along their motion. What comes out is the point cloud, ready for a Render TOP with your own material, or for any POP that takes points.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in_loopin** (POP): optional; points to carry into the loop.
- **in_source** (TOP): the image particles are born from.
- **in_effector_curl** (TOP), **in_effector_wind** (TOP): optional images that steer the curl and wind effectors through their lookups.
- **out_loopout** (POP): the simulated points.
