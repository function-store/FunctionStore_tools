---
title: "T3D, 3D textures in TouchDesigner"
summary: "A family of 48 operators for 3D textures: generate volumes, process them (filters, composites, transforms, optical flow, fluid simulation) and render them (ray-marched volumes, iso-surfaces, volume tracing), all on the GPU."
---

## What it does

T3D is a family of 48 TouchDesigner operators for 3D textures. It generates volumes (shapes, signed distance fields, noise, fractals, metaballs, geometry and point clouds), processes them (filters, composites, transforms, optical flow, fluid simulation), and renders them (ray-marched volumes, iso-surfaces, volume tracing).

Volumes are regular TOPs of texture type 3D Texture, connected with TOP wires. Every operator runs on the GPU as compute shaders, and cooks only when its inputs or parameters change.

## Getting it

T3D is available to Josef Pelz's supporters on [Patreon](https://www.patreon.com/JosefPelz/).
