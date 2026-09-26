---
title: "EssentiaTD, audio analysis as native CHOPs"
summary: "Real-time and offline audio analysis as native CHOPs, powered by Essentia: spectrum, mel bands, MFCCs, pitch, key, onsets and BPM, and EBU R128 loudness. Windows and macOS."
---

## What it does

EssentiaTD brings [Essentia](https://essentia.upf.edu/), the audio analysis library from the Music Technology Group in Barcelona, into TouchDesigner as five C++ CHOP plugins. Between them they cover spectrum analysis, mel bands, MFCCs, pitch detection, key estimation, onset and BPM tracking, and EBU R128 loudness metering.

Every analyzer takes raw audio and runs its own FFT, and each can work in real time, frame by frame, or on a whole file at once.

## Why we like it

<!-- your words: this highlight stays a draft until you write them -->

## Getting it

EssentiaTD is a set of plugins, not a .tox, so it installs outside your project: an installer for Windows (`EssentiaTD-Setup.exe`) and macOS (`EssentiaTD.pkg`) puts them in your TouchDesigner plugins folder. Restart TouchDesigner afterwards and the operators appear in the OP Create dialog under CHOP. There is also an [interactive guide](https://darienbrito.github.io/EssentiaTD/) to every parameter.
