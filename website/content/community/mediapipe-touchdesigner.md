---
title: "MediaPipe in TouchDesigner"
summary: "GPU-accelerated MediaPipe in TouchDesigner, on Mac and PC with no installation: face, hand, pose, object and gesture tracking, segmentation and classification."
---

## What it does

A GPU-accelerated, self-contained [MediaPipe](https://developers.google.com/mediapipe) plugin for TouchDesigner that runs on Mac and PC with no installation. It covers face detection and landmarks, hand tracking and gestures, pose, object detection, image segmentation and classification.

The main MediaPipe component runs the models in a built-in browser and outputs a DAT per task plus a TOP with the video and overlays. Companion components show how to use each model's data.

## Why we like it

<!-- your words: this highlight stays a draft until you write them -->

## Getting it

Download `release.zip` from the [releases page](https://github.com/torinmb/mediapipe-touchdesigner/releases) and open the example .toe; the components are in its `toxes` folder. When you drag `MediaPipe.tox` into your own project, turn on Enable External .tox, or your .toe grows by the size of the models.
