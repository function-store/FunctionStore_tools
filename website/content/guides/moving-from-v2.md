---
title: Moving from v2
order: 15
summary: For projects that have the 2023 toolkit inside. Take it out, install v3, and see what carries over.
---

FNSTools v3 replaces the 2023 toolkit (`FunctionStore_tools_2023`, versions 2.x). The two cannot share a project: both claim the `FNS` shortcut and the same places in TouchDesigner's interface. Take the old toolkit out of a project before you put v3 in.

v3 needs TouchDesigner 2025 or newer. If you are staying on TouchDesigner 2023, keep using v2: version 2.11.2 is its last release, on [GitHub](https://github.com/function-store/FunctionStore_tools/releases/tag/v2.11.2) and on the [`dev2023` branch](https://github.com/function-store/FunctionStore_tools/tree/dev2023).

## Why v2 does not offer the update

The v2 updater (the yellow border on the toolbar's `?` icon) only watches the GitHub releases page. v3 is published through functionstore.tools, so v2 keeps reporting that you are up to date. Moving to v3 is a one-time step by hand. After that, v3's own updater keeps every tool current.

## Take v2 out of a project

1. Save a copy of the project first.
2. At the root of the network (`/`), delete the `FunctionStore_tools_2023` component. If you renamed it, type `op.FNS` in the Textport to see where it is.
3. Save the project, then close and reopen it, so TouchDesigner rebuilds its interface without the old toolbar and navbar.

Do this for each project that has v2 inside, before you install v3 in it.

## Install v3

1. Drag [`FNSTools.tox`](https://storage.functionstore.tools/fnstools/latest/FNSTools.tox) into the root of the project.
2. The picker opens on the first drop. Pick your tools and install them; [Getting started](/docs/guides/getting-started/) walks through it.

## Your startup file

If your startup file has v2 inside (`FNS_TDDefault_2023.toe`, or your own file with the toolkit in it), every new project starts with the old toolkit. Make a new one: open an empty project, drop in `FNSTools.tox`, pick your tools, save it, and set it in `Preferences > General > Startup File Mode`.

## What carries over

- **The palette folder.** v2 kept its files in `FNStools_ext` in your user palette. The first time v3 runs, it renames that folder to `FNSTools` and keeps everything in it.
- **Your OpTemplates library.** OpTemplates finds the library you already have, including the `_2023` copy, before it creates a new one. Whatever it replaces is kept as `OPTemplates1.before-adopt.tox`.
- **Tool settings start fresh.** v2 saved them in `FNS_tools_config.json`. v3 tools start from their own defaults and save to a new file, `FNSTools/config/FNStools_config.json`. The old file stays where it was, so you can still look up a value.
- **Hotkeys.** [HotkeyManager](/docs/fns-hotkeymanager/) lists every binding in your install and flags conflicts.

## Help

Ask in the Troubleshoot channel on [Discord](https://discord.gg/b4CaCP3g3K), or open an [issue on GitHub](https://github.com/function-store/FunctionStore_tools/issues).
