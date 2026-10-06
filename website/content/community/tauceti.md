---
title: "TauCeti, presets and tweening for TouchDesigner"
summary: "Store, recall and fade between parameter states, with a dashboard, a cue list and a CHOP mapper."
---

## What it does

TauCeti is a preset system. The PresetManager stores the parameters of the components you point it at, and recalls them later, either instantly or as a tween over time.

Around it sit a few companions:

- **Tweener**: the engine that moves parameters from one value to another with a curve.
- **PresetDashboard**: a panel of your presets, to trigger them by hand.
- **PresetCuelist**: presets in order, for running a show.
- **PresetChopMapper**: drive presets from CHOP channels.
- **TweenCHOP**: a tween you can use on its own, as a CHOP.

## Why we like it

<!-- your words: this highlight stays a draft until you write them -->

## Getting it

It ships as a Python package, `tdp-TauCeti`. The FNSTools picker installs it into your project's Python environment and places the PresetManager.
