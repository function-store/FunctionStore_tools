---
title: Architecture
section: guides
order: 20
summary: The toolkit in one page. Independent packages, a small core of registries they plug into, one place they install and update from, and settings that follow you between projects.
---

This is the shape of it in a couple of minutes. The long version, with the reasoning and the measurements behind every choice, is [How FNSTools is built](/docs/guides/how-fnstools-is-built/) at the end of the docs.

## One tool, one package

Every tool in the catalog is a single `.tox` with its own version, its own docs page and its own line in the picker. You install the ones you want and leave the rest alone. Ticking SwapOps brings nothing else along with it.

The exception is a small **core** that arrives with your first pick and that every tool leans on. Core is mostly registries.

## Registries are the backbone

A registry owns one place in TouchDesigner's interface and decides what appears there. There are nine.

| Registry | The surface it owns |
|---|---|
| [ToolbarRegistry](/docs/fns-toolbarregistry/) | TouchDesigner's bookmark bar |
| [NavbarRegistry](/docs/fns-navbarregistry/) | every pane bar |
| [MainMenuRegistry](/docs/fns-mainmenuregistry/) | the main menu strip |
| [OpMenuRegistry](/docs/fns-opmenuregistry/) | the OP Create dialog |
| [PaneTypeRegistry](/docs/fns-panetyperegistry/) | the pane-type menu |
| [PaletteRegistry](/docs/fns-paletteregistry/) | tabs in the Palette Browser |
| [TimelineRegistry](/docs/fns-timelineregistry/) | panels in the timeline |
| [HubRegistry](/docs/fns-hubregistry/) | the tabs of the Hub window |
| [ConfigRegistry](/docs/fns-configregistry/) | the settings file |

A tool that wants a toolbar button carries a small host, and the host publishes one entry into the toolbar registry. The registry decides the order, the visibility and the placement from there, which is why you can reorder or hide anything from [Hub](/docs/fns-hub/) and have it stay that way.

Two things follow. A registry collects whatever is present, so a partial install is simply a shorter list and any single tool works on its own. And the registries ship raw and cloneable, so a component you built yourself can carry a host and sit on the toolbar beside everything else.

## No tool depends on another tool

What a package requires is worked out from the registries it hosts. A tool with a toolbar button requires the toolbar registry, and that is the whole graph. Nothing is written by hand, so nothing goes stale, and every requirement points at core.

Tools reach for each other only through a guarded lookup. ExprHotStrings uses CustomParTools when it is installed and carries on quietly when it is absent, with the extra behaviour missing and no error raised.

## Installing and updating

One bucket holds every release, and each release has a manifest saying what exists, where the bytes are and what version every package is. The picker reads that manifest, downloads only what you ticked, and checks each file against it before writing anything.

Every package carries its version on itself, so the updater compares the version of the component sitting in your project against the published one. The checksum's only job is proving that a download arrived intact. You update the tools you use, and an update never installs something you did not pick.

## Settings follow you

A tool's settings live in your project file. By default they also roam through one file in your user palette, so the way you set a tool up is the way you find it in your next project and after the next update. A project can opt out and keep everything to itself.

## It reaches past the toolkit

Tools announce the actions they can perform, so anything able to run them can also list them: the [command palette](/docs/fns-commandpalette/) inside TouchDesigner, and TDX Launcher Ultra, which asks this installer to place packages instead of dropping files of its own.

A few tools are Plus. The lock sits on the bytes, so the server declines to send them without a membership, and every page and every listing stays complete whether or not you have one. [How Plus works](/plus/) covers the details.

## Next

- [Getting started](/docs/guides/getting-started/) walks the install itself.
- [How FNSTools is built](/docs/guides/how-fnstools-is-built/) is this page again with the reasoning, the measurements and the traps that shaped each decision.
