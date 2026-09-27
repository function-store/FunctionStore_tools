---
title: "TDFam, your own operator family"
summary: "Custom operator families for TouchDesigner: your own tab in the OP Create dialog, manifests, placement, stubs and in-place updates, in one component."
---

## What it does

TDFam lets you make a custom operator family: a named group of your own operators with their own tab, colour and search words in TouchDesigner's OP Create dialog. Operators can live inside the component or as .tox files in a folder.

Each operator can carry a manifest (its label, group, version, colour, docs link and right-click menu). Placed operators can be turned into lightweight stubs and back, and updated in place with their parameters kept. A shared registry coordinates every installed family.

## Why we like it

<!-- your words: this highlight stays a draft until you write them -->

## Getting it

[Download TDFam_create.tox](https://github.com/dotsimulate/TDFam/releases/latest/download/TDFam_create.tox), always the latest release. It carries the registry inside it. The FNS operator family in FNSTools is built on TDFam.
