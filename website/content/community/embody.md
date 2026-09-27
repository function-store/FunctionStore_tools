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

Download the `.tox` from its [latest release](https://github.com/dylanroscover/Embody/releases/latest); the [documentation](https://dylanroscover.github.io/Embody/) covers setup. FNSTools itself is developed with Embody.
