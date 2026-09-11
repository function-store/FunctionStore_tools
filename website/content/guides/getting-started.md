---
title: Getting started
order: 10
summary: Install the toolkit, pick your tools, keep them current, and know where your settings live. The short version.
---

This is the short version. For the shape of the toolkit itself, read [Architecture](/docs/guides/architecture/); the full account of the machinery is [How FNSTools is built](/docs/guides/how-fnstools-is-built/) at the end of the docs.

You need TouchDesigner 2025 or newer, on Windows or macOS.

## Install

1. Download [`FNSTools.tox`](https://storage.functionstore.tools/fnstools/latest/FNSTools.tox) and drag it into the root of a project. It arrives empty: the container you drop is where your tools will live. Dropped into a nested network, it moves itself to the root.
2. The picker opens by itself on the first drop. Choose **Recommended**, **Everything** or **Pick my own** (on a machine that has installed before, **Set up like last time** comes first), adjust the list, press **Review install** and then **Install**. Only the packages you ticked are downloaded, plus the core they need, and every file is verified before it is written.
3. Save the project and set it as your startup file in `Preferences > General > Startup File Mode`, so every new project opens with your tools in it.

Other ways in: a project that already has a toolkit container takes the bare [`FNS_Installer.tox`](https://storage.functionstore.tools/fnstools/latest/FNS_Installer.tox); [the online picker](/get/) gives you one line to paste into the Textport with no download at all; and the FNSTools tab of TDX Launcher Ultra installs into a running session through the same installer.

## Add or remove tools later

Select the toolkit container and pulse **Pick Tools** on its `FNSTools` page. The picker opens inside TouchDesigner with your installed tools pre-checked. Tick to add, untick to remove; a removed tool keeps its settings for the day you reinstall it.

## Updating

Pulse **Open Settings** on the toolkit container and switch to the **Updates** tab. **Check for updates** compares every installed package against the published release and lists what is newer, with its release notes. Update one package or all of them. Your settings survive an update; a tool comes back where you left it.

Only the tools you installed are offered. An update never adds a package you did not choose.

## Your settings

Every tool keeps its settings in the project file. By default they also roam: one settings file in your user palette follows you into the next project and across updates, so the way you set a tool up is the way you find it. To pin a project to its own settings instead, set **Config Scope** to `project` on the toolkit container. The **Settings** tab of the same window edits every installed tool's parameters in one place and can export or import them.

MIDI and OSC maps are the exception: they save into the project folder, so they travel with the show.

## Plus tools

A few tools are marked Plus. They appear in the picker like everything else and install once your account covers them: press **Sign in** in the picker to connect a Patreon membership, and where a tool offers a licence key, redeem it in the same place. [How Plus works](/plus/) has the details, and everything else stays free.

## Getting help

`Alt`-right-click (or `Alt`-middle-click) any toolbar icon to open that tool's page on this site; `Option` on macOS. Where a page says `Alt`, press `Cmd` on macOS unless it says otherwise.

Bugs go to the **Troubleshoot** channel on [Discord](https://discord.gg/b4CaCP3g3K) or to [GitHub issues](https://github.com/function-store/FunctionStore_tools/issues). If a download or install stalls, leave it as it is and send the Textport contents along with the report.
