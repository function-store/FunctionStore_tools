---
title: "Embody, TouchDesigner as files and as a conversation"
summary: "Externalizes your network to files you can diff and version, and runs an MCP server so AI assistants can build and debug in your live TouchDesigner session."
---

## What it does

Embody externalizes the operators you tag to files on disk that mirror your network, so a project can be diffed, branched and versioned with git, and reconstructs itself from those files when it opens. Its networks are written as TDXN, a readable YAML format.

It also runs Envoy, an MCP server inside TouchDesigner, so AI assistants such as Claude Code can create operators, wire them, set parameters and debug errors in your live session.

## Why we like it

<!-- your words: this highlight stays a draft until you write them -->

## Getting it

Place it from the FNSTools console's Community tab: it downloads exactly `Embody-v6.2.65.tox`, the build we checked. Newer versions are on its [releases page](https://github.com/dylanroscover/Embody/releases), and the [documentation](https://dylanroscover.github.io/Embody/) covers setup. FNSTools itself is developed with Embody.
