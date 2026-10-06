---
title: Getting started
order: 10
summary: Install FNSTools, choose packages, update them and manage settings.
---

For an overview of packages and registries, see [Architecture](/docs/guides/architecture/). For implementation details, see [How FNSTools is built](/docs/guides/how-fnstools-is-built/).

You need TouchDesigner 2025 or newer, on Windows or macOS.

## Install

1. Download [`FNSTools.tox`](https://storage.functionstore.tools/fnstools/latest/FNSTools.tox) and drag it into the root of a project. It arrives empty: the container you drop is where your tools will live. Dropped into a nested network, it moves itself to the root.
2. The picker opens by itself on the first drop. Choose **Recommended**, **Everything** or **Pick my own** (on a machine that has installed before, **Set up like last time** comes first), adjust the list, press **Review install** and then **Install**. Only the packages you ticked are downloaded, plus the core they need, and every file is verified before it is written.
3. Save the project and set it as your startup file in `Preferences > General > Startup File Mode`, so every new project opens with your tools in it.

You can also use [the online picker](/get/) and paste its install command into the Textport, or install into a running session from the FNSTools tab of TDX Launcher Ultra.

## Add or remove tools later

Select the toolkit container and pulse **Pick Tools** on its `FNSTools` page. The picker opens inside TouchDesigner with your installed tools pre-checked. Tick to add, untick to remove; removed tools retain their settings for reinstallation.

## Updating

Pulse **Open Settings** on the toolkit container and switch to the **Updates** tab. **Check for updates** compares every installed package against the published release and lists what is newer, with its release notes. Update one package or all of them. Updates preserve your settings.

Only the tools you installed are offered. An update never adds a package you did not choose.

## Your settings

Every tool keeps its settings in the project file. By default, a shared settings file in your user palette also applies them to other projects and preserves them across updates. To pin a project to its own settings instead, set **Config Scope** to `project` on the toolkit container. The **Settings** tab of the same window edits every installed tool's parameters in one place and can export or import them.

MIDI and OSC maps are the exception: they save into the project folder, so they travel with the show.

## Patreon tools

A few tools are marked Patreon. They appear in the picker like everything else and install once your membership covers them: each one names the lowest Patreon tier that unlocks it (Base, Pro or Coaching). Press **Sign in with Patreon** in the picker to connect your membership, and where a tool offers a Gumroad licence key, redeem it in the same place. [How unlocking works](/patreon/) has the details, and everything else stays free.

## Getting help

`Alt`-right-click (or `Alt`-middle-click) any toolbar icon to open that tool's page on this site; `Option` on macOS. Where a page says `Alt`, press `Cmd` on macOS unless it says otherwise.

Bugs go to the **Troubleshoot** channel on [Discord](https://discord.gg/b4CaCP3g3K) or to [GitHub issues](https://github.com/function-store/FunctionStore_tools/issues). If a download or install stalls, leave it as it is and send the Textport contents along with the report.
