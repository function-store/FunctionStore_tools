---
title: "Swaggy Bokeh, depth of field with real bokeh"
summary: "Physically based depth of field in GLSL, with bokeh, autofocus and a focus overlay. Drop in your scene camera, or composite a render with a depth pass."
---

## What it does

Swaggy Bokeh is a physically based depth of field in GLSL, a port of Martin Upitis's bokeh shader. Point it at your scene camera and it matches the camera for you, or feed it a render and a depth pass to composite.

It has autofocus on a point of the frame, bokeh highlights with rings, edge bias and chromatic aberration, and a Show Focus overlay that draws the focus plane in red and the sharp zone in white.

## Why we like it

<!-- your words: this highlight stays a draft until you write them -->

## Getting it

Place it from the FNSTools console's Community tab: it downloads exactly `Swaggy_Bokeh_v1_0.tox` from the repository. It dates from 2017; we loaded it in TouchDesigner 2025 and its shaders compile.
