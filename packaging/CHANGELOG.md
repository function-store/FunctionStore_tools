# FNS tools changelog

## v3.2.65 -- 2026-10-06

- FNS_PaneSearchRegistry 0.1.1 -- a registry host stamped from it no longer carries a copy of the package's About component, which raised an "ExtFnsAbout" script error once the tool shipped.
- FNS_SearchFix 0.2.3 -- no longer shows an "ExtFnsAbout" script error inside its find-bar registry host, and that host's About values are filled in.

## v3.2.64 -- 2026-10-06

- FNSTools.tox and FNS_Installer.tox 3.2.44 -> 3.2.45 -- an install made without the picker (TDX Launcher Ultra, a pasted script) counts as the first run, so its first picker shows no "New since you last looked"; the bootstrap carries updater 3.2.24

A new machine that installs FNSTools through TDX Launcher Ultra, a pasted script or any other rail that skips the picker no longer sees "New since you last looked" the first time it opens the picker. That install now counts as the first run it is, so every current tool starts out as already shown.

## v3.2.63 -- 2026-10-05

- FNSTools.tox and FNS_Installer.tox 3.2.43 -> 3.2.44 -- the install picker's ranked, docs-aware search and Compact view, and FNS_PaneSearchRegistry in core; the bootstrap carries updater 3.2.24
- FNS_PaneSearchRegistry 0.1.0 -- new. Publishes controls into the find bar of every network editor pane, beside its Home toggle, one copy per pane; a pane that opens its find bar later gets them too.
- FNS_ProSceneChanger 1.0.5 -> 1.0.6 -- the same page layout as SimpleSceneChanger: Scenes and Transition, with the Pro pages after them.
- FNS_SearchFix 0.2.2 -- new. The network editor's find bar finds any part of a name, any case, with wildcards, optionally fuzzy and inside child networks, keeping its arrows and Home toggle. Legacy brings TouchDesigner's own search back, and Ctrl+F (Cmd+F) closes the bar while you are typing in it.
- FNS_SimpleSceneChanger 1.0.6 -> 1.0.7 -- parameters regrouped so the first page stays simple. Scenes holds what you pick and see (Select, Loop Type, Crossfade Length, Easing, Res, Callbacks, the Inputs); the other switch modes, fades, the A/B Fader, Finish Transition and Auto Advance share one Transition page, and the Callbacks page is gone. Every value carries over.

From this release on, a tool's About page is its last parameter page when it ships: a page added after About while the tool was being built no longer sits behind it. Each tool picks this up the next time it is released.
The install picker's search now reads each tool's documentation, its tags and the operators it stands in for, survives a typo, and lists the best match first in one ranked list (Enter ticks the top one); a hit found only in the docs says which words found it. A Compact toggle beside the filters shows title-only tiles, with the description on hover.

## v3.2.62 -- 2026-09-30

- FNSTools.tox and FNS_Installer.tox 3.2.42 -> 3.2.43 -- the bootstrap carries updater 3.2.24, so a dismissed Patreon sign-in no longer locks Sign in on a fresh install
- FNS_TimelineTools 3.2.7 -> 3.2.8 -- dropping a movie or audio file now asks whether to load it as media or just sync the timeline to its length. Syncing only measures the file and resizes the timeline; the loaded media, filmstrip and waveform are left alone. The new On Media Drop setting picks the answer once and skips the question.
- FNS_Updater 3.2.23 -> 3.2.24 -- closing or cancelling the Patreon sign-in page no longer locks Sign in for five minutes. Clicking Sign in again starts a fresh sign-in straight away.

## v3.2.61 -- 2026-09-30

- FNSTools.tox and FNS_Installer.tox 3.2.41 -> 3.2.42 -- offers "Install <tool>" commands for tools this project does not have; the bootstrap never ships a config-file override; the bootstrap carries updater 3.2.23
- FNS_BorderlessTD 3.2.6 -> 3.2.7 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_CamSequencer 3.0.9 -> 3.0.10 -- with a Source CHOP set (a GeoPilot head bus, MIDI, OSC), its button channels are heard again: Capture, Next, Prev and the other mapped buttons did nothing, because setting a Source switched off the only reader of that source.
- FNS_CommandPalette 3.2.11 -> 3.2.12 -- "Install <tool>" commands show with their own INSTALL badge.
- FNS_CommandRegistry 3.2.4 -> 3.2.5 -- a tool that is bypassed or has cooking off no longer offers its commands in the command palette or the launcher, and running one of them says why instead of failing. Tools can also switch single commands off with a new `enabled` setting.
- FNS_CustomParTools 3.2.7 -> 3.2.8 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_GlobalVolControl 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_HydroHomie 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_Misc 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_OpTemplates 3.2.7 -> 3.2.8 -- a Library Folder parameter chooses which folder in your palette holds the global template library, so a second setup can keep its own set apart. Leave it empty to keep the usual folder. Downloaded on its own, it also loads without a clone warning from its toolbar button.
- FNS_Output 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_ParOPDrop 3.2.6 -> 3.2.7 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_ParRandomizer 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_QuickTime 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_Remote 3.2.10 -> 3.2.11 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_ResetPLS 3.2.6 -> 3.2.7 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_SetSmoothness 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_SwapOps 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- FNS_ToolbarRegistry 3.2.3 -> 3.2.4 -- toolbar hosts that still pointed at the registry by a fixed relative path are switched to the location-independent link on start, so a tool used outside the toolkit no longer shows a clone warning.
- FNS_Updater 3.2.22 -> 3.2.23 -- keeps the "Install <tool>" commands current after every store download or update and when your sign-in or entitlements change.
- FNS_VSCodeTools 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.
- RealRamp 1.0.0 -> 1.0.1 -- now an alternative for the Ramp TOP (create a Ramp TOP with the alternatives shortcut held) and no longer an FNS family operator. Colour keys are a sequence of parameters on the Keys page, with Step, Linear, Ease In Ease Out and Hermite blending like the Ramp TOP. It starts horizontal, Extend adds Hold and Zero beside Repeat and Mirror, and Radial and Circular now match the Ramp TOP: Radial starts at 3 o'clock and period and phase behave the same way.
- ThresholdColor 1.0.1 -> 1.0.2 -- installs as an alternative for the Threshold TOP only. Create a Threshold TOP with the alternatives shortcut held to use it; an install no longer puts a copy inside the toolkit.
- midiMapper 3.2.5 -> 3.2.6 -- its toolbar button links to the toolbar registry by a location-independent path, so the tool downloaded on its own loads without a clone warning.

FNS_Installer: offers "Install <tool>" as a command in the command palette and the launcher for every tool this project does not have and your account can install. Running it installs the tool, downloading it first when needed.


The tools with a toolbar button (BorderlessTD, CustomParTools, GlobalVolControl, HydroHomie, Misc, OpTemplates, Output, ParOPDrop, ParRandomizer, QuickTime, Remote, ResetPLS, SetSmoothness, SwapOps, VSCodeTools, midiMapper) ship with that link, so each one downloaded on its own loads without a warning.

## v3.2.60 -- 2026-09-27

- FNSTools.tox and FNS_Installer.tox 3.2.40 -> 3.2.41 -- rebuilt: the Community card's Install says it installs the latest release; the bootstrap carries updater 3.2.22
- FNS_Console 3.2.13 -> 3.2.14 -- the Community card's Install says it installs the latest release.
- FNS_Updater 3.2.21 -> 3.2.22 -- a community tool shipped as a Python package installs its latest release by name; a dry run goes first and the install is refused if it would add a package TouchDesigner ships.

## v3.2.59 -- 2026-09-27

- FNSTools.tox and FNS_Installer.tox 3.2.39 -> 3.2.40 -- rebuilt: the picker opens with the Patreon or Free filter on from a link (/get/#patreon, #free, #all); the bootstrap carries updater 3.2.21
- FNS_RandomCHOP 1.0.5 -> 1.0.6 -- a Base COMP now, not a Container, with no Noise TOP inside; its viewer shows its own output in every copy (it pointed at the master's by absolute path).

## v3.2.58 -- 2026-09-26

- FNSTools.tox and FNS_Installer.tox 3.2.38 -> 3.2.39 -- rebuilt: the picker drops the 'All N tools' caption when nothing is filtered (a search or filter still says what it kept); the bootstrap carries updater 3.2.21

## v3.2.57 -- 2026-09-26

- FNSTools.tox and FNS_Installer.tox 3.2.37 -> 3.2.38 -- rebuilt: the picker points to the console's Community tab instead of listing other creators' tools, the installer places and installs those tools (a pinned tox, or a locked Python package), a community tool may be placed in the project root, the category rail sits at the side from 1000px, category groups have no headings, and the Place button sits in the card's corner; the bootstrap carries updater 3.2.21
- FNS_Console 3.2.12 -> 3.2.13 -- a new Community tab lists tools by other creators, with their write-up, the author's page, and Place or Install. The list reaches the console now (it was never forwarded). Reopening the console from the hub returns to the view you were last on, instead of Settings.
- FNS_Updater 3.2.20 -> 3.2.21 -- places a pinned tool from "From other creators" into your working network when the picker asks, and deletes a download that fails its size or hash check instead of leaving it in the store. It also installs a community tool shipped as a Python package: exactly the versions we checked, into your project's Python environment, then places its tox. A project without an environment is offered TouchDesigner's own manager to create one.

The picker no longer lists tools by other creators among ours: one line points to the console's Community tab (or to functionstore.tools/community/ outside the console).
The picker inside the console is quieter: the Patreon line appears only when something needs doing (signed out, link lost, nothing unlocked) with its one fix and a link to how unlocking works, Expand and Collapse sit on the filter row, and the count says how many picks need Patreon.

## v3.2.56 -- 2026-09-25

- FNSTools.tox and FNS_Installer.tox 3.2.36 -> 3.2.37 -- rebuilt: the picker hides tools that are not released yet from everyone but the owner, never announces a Patreon tool the viewer cannot get, and lets the new-tools window be turned off; the bootstrap carries updater 3.2.20
- ChopBank 1.0.0 -> 1.0.1 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- ChopProcess 1.0.0 -> 1.0.1 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- ConstantCHOP 1.0.0 -> 1.0.1 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- ExpressionPOP 1.0.1 -> 1.0.2 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- FNS_RandomCHOP 1.0.4 -> 1.0.5 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- FeedbackDisplace 1.0.2 -> 1.0.3 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- PrismTOP 1.0.1 -> 1.0.2 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.
- ThresholdColor 1.0.0 -> 1.0.1 -- the operator types it stands in for live in its alternatives table, which the content CMS can now read and edit.

## v3.2.55 -- 2026-09-25

- FNSTools.tox and FNS_Installer.tox 3.2.35 -> 3.2.36 -- rebuilt: the installer announces new tools once and downloads a family operator it has on record but no longer has the file for; the picker shows the two category groups; the bootstrap carries updater 3.2.20, which keeps family operators current
- FNS_AltSelect 3.2.4 -> 3.2.5
- FNS_AutoCombine 3.2.5 -> 3.2.6
- FNS_AutoRes 3.2.5 -> 3.2.6
- FNS_Autosave 3.2.4 -> 3.2.5
- FNS_BackupCleaner 3.2.5 -> 3.2.6
- FNS_BeatMod 3.2.7 -> 3.2.8
- FNS_BorderlessTD 3.2.5 -> 3.2.6
- FNS_ColorUI 3.2.5 -> 3.2.6
- FNS_CommandPalette 3.2.10 -> 3.2.11 -- the palette folder migration keeps the old copy of a file both folders hold under `FNSTools/legacy_FNStools_ext/` instead of deleting it.
- FNS_ConfigHost 3.2.4 -> 3.2.5
- FNS_ConfigRegistry 3.2.5 -> 3.2.6 -- the palette folder migration keeps the old copy of a file both folders hold under `FNSTools/legacy_FNStools_ext/` instead of deleting it.
- FNS_Console 3.2.11 -> 3.2.12 -- the Install & remove tab shows how many tools are new since you last looked.
- FNS_CustomParTools 3.2.6 -> 3.2.7
- FNS_ExprHotStrings 3.2.5 -> 3.2.6
- FNS_GlobalOutSelect 3.2.3 -> 3.2.4
- FNS_GlobalVolControl 3.2.4 -> 3.2.5
- FNS_HotkeyManager 3.2.5 -> 3.2.6
- FNS_Hub 3.2.9 -> 3.2.10
- FNS_HydroHomie 3.2.4 -> 3.2.5
- FNS_Misc 3.2.4 -> 3.2.5
- FNS_MixSequencer 1.0.6 -> 1.0.7 -- sits under COMP in the FNS tab of the OP Create dialog.
- FNS_OpFamily 0.1.6 -> 0.1.7 -- the FNS operator family has a new colour, a brick red (0.569 0.265 0.188), in the OP Create dialog and on its operators.
- FNS_OpMenuMods 3.2.6 -> 3.2.7
- FNS_OpTemplates 3.2.6 -> 3.2.7 -- finds the template library you already have before creating one from the shipped templates. That covers the `_2023` copy TouchDesigner 2023 saved to, an `OPTemplates2.tox` or higher from the old Create New choice, and a copy the palette folder migration set aside. The most recently saved one wins, and whatever it replaces is kept as `OPTemplates1.before-adopt.tox`.
- FNS_OpToClipboard 3.2.5 -> 3.2.6
- FNS_OpenExt 3.2.4 -> 3.2.5 -- the palette folder migration keeps the old copy of a file both folders hold under `FNSTools/legacy_FNStools_ext/` instead of deleting it.
- FNS_Output 3.2.4 -> 3.2.5
- FNS_ParOPDrop 3.2.5 -> 3.2.6
- FNS_ParRandomizer 3.2.4 -> 3.2.5
- FNS_ProSceneChanger 1.0.4 -> 1.0.5 -- sits under COMP in the FNS tab of the OP Create dialog.
- FNS_QuickCollapse 3.2.4 -> 3.2.5
- FNS_QuickPane 3.2.4 -> 3.2.5
- FNS_QuickTime 3.2.4 -> 3.2.5
- FNS_Remote 3.2.9 -> 3.2.10 -- the palette folder migration keeps the old copy of a file both folders hold under `FNSTools/legacy_FNStools_ext/` instead of deleting it.
- FNS_ResetPLS 3.2.5 -> 3.2.6
- FNS_SearchPalette 3.2.5 -> 3.2.6
- FNS_SetSmoothness 3.2.4 -> 3.2.5
- FNS_SimpleSceneChanger 1.0.5 -> 1.0.6 -- sits under COMP in the FNS tab of the OP Create dialog.
- FNS_SwapOps 3.2.4 -> 3.2.5
- FNS_SwitchOPs 3.2.4 -> 3.2.5
- FNS_SwitchTools 1.1.4 -> 1.1.5 -- sits under COMP in the FNS tab of the OP Create dialog.
- FNS_TimelineTools 3.2.6 -> 3.2.7
- FNS_Updater 3.2.19 -> 3.2.20 -- the palette folder migration keeps the old copy of a file both folders hold under `FNSTools/legacy_FNStools_ext/` instead of deleting it. Update keeps FNS family operators current. A family operator whose store copy is missing or older than the release is now an update like any other, and the family folder follows. Before this, family operators never updated.
- FNS_VSCodeTools 3.2.4 -> 3.2.5
- PasteFromClipboard 3.2.5 -> 3.2.6
- QuickMarks 3.2.4 -> 3.2.5
- SlideShow 1.0.1 -> 1.0.2 -- sits under COMP in the FNS tab of the OP Create dialog.
- TopToMidi 1.0.0 -> 1.0.1 -- sits under COMP in the FNS tab of the OP Create dialog.
- midiMapper 3.2.4 -> 3.2.5
- oscMapper 3.2.3 -> 3.2.4

When a release adds tools, the picker says so once: a "New since you last looked" window lists them with a tick each, and they keep a New badge. A first install is never shown the whole catalog. The installer also downloads a family operator it has on record but no longer has the file for.

The tool categories are reorganised into two groups: Working in TouchDesigner (Interface, Network, Parameters, Project, Developer, Miscellaneous) and Making the piece (Time & sequencing, Control & mapping, CHOPs & sensing, Visual, 3D and Particles, Show & output). The picker shows the two groups as headings. Operators moved out of Control and Media & Output into categories of their own, and links to the old docs sections still land on their successors.

The guided setup's questionnaire separates two meanings that shared one tag: its point-and-click answer now recommends tools with a window, tab or pane to work in, and the image effects, particles and scene changers are recommended to people who make live visuals or generative art.

The guided setup asks a new question, what you build with: CHOPs, image effects, particles and 3D, sequencing, cameras and sensors, MIDI controllers, OSC or phone control, or scenes and show playback. Each answer leads to its own tools, and "just the editor tools" leaves the operators out.

## v3.2.54 -- 2026-09-24

- FNSTools.tox and FNS_Installer.tox 3.2.34 -> 3.2.35 -- rebuilt: the installer carries the redesigned picker and Place once (a placed tool lands in this project without joining the setup); the bootstrap carries updater 3.2.19

The tool picker is redesigned. Patreon tools now sit last in every section, behind a "With Patreon" divider. Beside the search, All / Free / Patreon narrows the list, with a count on each choice. Selected shows only what you picked, and New shows the packages new in this release line. A results line names what is shown, with a removable chip per filter, and Select all / Clear act on exactly that list. Each section has its own Select section. Inside TouchDesigner each card says whether Apply will install it, keep it or remove it. The count in the footer opens a tray of everything you picked, grouped by what Apply does with it. Section headers work from the keyboard, and "/" jumps to the search.

Some tools can now be placed in one project without becoming part of your setup: their cards carry "place in this project only", and "Set up like last time" leaves them out of the next project. Every FNS family operator has it, and so do TDXMap and ParHoverMIDI_VSN1. The picker's new Placeable filter lists the tools you drop into a network as nodes.

## v3.2.53 -- 2026-09-24

- CircularDistortionTOP 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- EaseInterpolator 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- ExpressionPOP 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_BackupCleaner 3.2.4 -> 3.2.5 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_CamSequencer 3.0.8 -> 3.0.9 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_CommandPalette 3.2.9 -> 3.2.10 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_OpFamily 0.1.5 -> 0.1.6 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_OpSequencer 1.16.6 -> 1.16.7 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_PreviewPanel 3.2.4 -> 3.2.5 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_ProSceneChanger 1.0.3 -> 1.0.4 -- runs the shared parameter helper (same two fixes); its helper was bound to FNS_SimpleSceneChanger's files, so an edit in one tool could overwrite the other.
- FNS_RandomCHOP 1.0.3 -> 1.0.4 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_Remote 3.2.8 -> 3.2.9 -- every parameter has a tooltip, and the docs page describes each control from it.
- FNS_SimpleSceneChanger 1.0.4 -> 1.0.5 -- runs the shared parameter helper, so the first parameter change on a freshly placed copy is no longer lost and shrinking a parameter sequence no longer raises an error.
- FNS_SwitchTools 1.1.3 -> 1.1.4 -- runs the shared parameter helper, so the first parameter change on a freshly placed copy is no longer lost and shrinking a parameter sequence no longer raises an error.
- FNS_TimelineTools 3.2.5 -> 3.2.6 -- every parameter has a tooltip, and the docs page describes each control from it.
- FeedbackDisplace 1.0.1 -> 1.0.2 -- every parameter has a tooltip, and the docs page describes each control from it.
- FloatDataRecorder 1.0.0 -> 1.0.1 -- no missing-file error when a project opens before anything has been recorded; the CHOP player stays bypassed until its clip exists.
- MaskDraw 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- MoveDetectDir 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- Particles2D_POP 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- ParticlesGpuUltimate 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- PrismTOP 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.
- SlideShow 1.0.0 -> 1.0.1 -- every parameter has a tooltip, and the docs page describes each control from it.

Every parameter of every tool now has a tooltip, and the tool pages on functionstore.tools document each control from it.

## v3.2.52 -- 2026-09-24

- ChopBank 1.0.0 -- new package (Base, FNS operator family). One processor per channel with its own range, curve, zero-below, lag and speed, built from the input with Snap Input; an alternative for the Math CHOP and the Constant CHOP.
- ChopProcess 1.0.0 -- new package (Base, FNS operator family). Limit, remap with an exponent curve, zero-below, lag and a speed mode in one node; an alternative for the Math CHOP.
- CircularDistortionTOP 1.0.0 -- new package (Base, FNS operator family). Rings of displacement around a centre you place, with phase, frequency, amplitude and a mode blend.
- ColorGen 1.0.0 -- new package (Base, FNS operator family). A colour palette generator shaped by a phase step per channel and per channel exponents, with a lookup ramp output.
- ColorGenPro 1.0.0 -- new package (Pro, FNS operator family). A cosine palette generator in GLSL with the full coefficient set, an RGB and D mode and a blackout region with a soft edge.
- ComplexMix 1.0.0 -- new package. Combines two UV fields as complex numbers and samples an image through the result. FNS operator family member.
- ComplexOp 1.0.0 -- new package. A GLSL TOP that treats the image plane as the complex plane and applies a complex function to it. FNS operator family member.
- ConstantCHOP 1.0.0 -- new package (Base, FNS operator family). Typed constants promoted as properties you can read and set, with a snap from the input; an alternative for the Constant CHOP. Snap Input keeps the names it snaps (new blocks are only auto-named when empty), and blocks it adds get their properties at once.
- EaseInterpolator 1.0.0 -- new package (Base, FNS operator family). Crossfades two CHOPs through an easing curve: thirty classic easings or a custom curve from a third input, driven by one Select value.
- ExpressionPOP 1.0.0 -- new package (free, FNS operator family). Per-point attribute expressions compiled to a GLSL compute shader; an alternative for the Math Combine POP.
- FNS_AltSelect 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_AutoCombine 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_AutoRes 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Autosave 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_BackupCleaner 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_BeatMod 3.2.6 -> 3.2.7 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_BorderlessTD 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Collect 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ColorUI 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_CommandKit 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_CommandPalette 3.2.8 -> 3.2.9 -- commands you run often now rank higher (Rank By Usage, on by default). The bonus fades with a 14-day half-life, never outranks a better match or a favourite, and is shared with the TDXLU launcher. Clear usage on the Commands tab forgets the palette's history.
- FNS_CommandRegistry 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ConfigHost 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ConfigRegistry 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Console 3.2.10 -> 3.2.11 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_CustomParTools 3.2.5 -> 3.2.6 -- CustomParHelper skips parameters destroyed in the same frame they changed, so shrinking a sequence no longer raises "Invalid Par object" in every tool that uses it. CustomParHelper builds a freshly placed tool's extension before routing its first parameter callback, so the first pulse on a new node is no longer lost.
- FNS_ExprHotStrings 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_GlobalOutSelect 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_GlobalVolControl 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_HotkeyManager 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Hub 3.2.8 -> 3.2.9 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_HubRegistry 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_HydroHomie 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_MainMenuRegistry 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_MediaBrowser 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Misc 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_NavbarRegistry 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_OpMenuMods 3.2.5 -> 3.2.6 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_OpMenuRegistry 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_OpTemplates 3.2.5 -> 3.2.6 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_OpToClipboard 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_OpenExt 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Output 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_PaletteRegistry 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_PaneTypeRegistry 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ParOPDrop 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ParRandomizer 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ParentHierarchy 3.2.2 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_PreviewPanel 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_QuickCollapse 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_QuickPane 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_QuickTime 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_RandomCHOP 1.0.1 -> 1.0.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Remote 3.2.7 -> 3.2.8 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ResetPLS 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_SearchPalette 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_SetSmoothness 3.2.4 -- no longer raises on a COMP that carries only one of the two smoothness parameters; each is assigned only where it exists.
- FNS_SwapOps 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_SwitchOPs 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_TimelineRegistry 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_TimelineTools 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_ToolbarRegistry 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_Updater 3.2.18 -> 3.2.19 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_VSCodeTools 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FNS_iopBrowser 3.2.2 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- FeedbackDisplace 1.0.1 -- new package (Base, FNS operator family). A feedback loop with a displace stage inside it, driven by a built-in noise or a second input, with a per-pass transform and a dry/wet mix; the alternative for the Feedback TOP.
- FloatDataRecorder 1.0.0 -- new package (Base, FNS operator family). Records a float texture, a colour texture and a CHOP in sync and plays the three back against the timeline.
- InfinityCHOP 1.0.0 -- new package (Base, FNS operator family). One curve that morphs from a circle to the infinity loop, as a travelling point or the whole drawn shape; replaces the separate infinity and circle CHOP tools.
- InstanceTrailer 1.0.0 -- new package (Base, FNS operator family). Turns one moving image into a trail of its recent frames, with the offsets as a CHOP for instancing.
- KinectSinglePlayer 1.0.0 -- new package (Base, FNS operator family). Picks one player out of a Kinect skeleton stream by a bounding box.
- LayerSep3D 1.0.0 -- new package (Base, FNS operator family). Slices an image into depth layers by threshold and instances them as a stack in 3D.
- LinkOPs 1.0.0 -- new package (Base, FNS operator family). Links the parameters of several operators with exceptions, an automatic mode and a one-shot sync.
- MaskDraw 1.0.0 -- new package (Pro, FNS operator family). Draw a mask with the mouse straight onto the image; Save Mask With Project bakes the mask into the component so it survives a reopen.
- MoveDetectDir 1.0.0 -- new package (Base, FNS operator family). Optical flow turned into left/right and down/up channels, with thresholds, inversion and filtering, for swipe and gesture triggers.
- OpenOp 1.0.0 -- new package (Base, FNS operator family). A one-button shortcut that opens a deeply nested operator's parameter or viewer window.
- ParHoverMIDI_VSN1 1.9.0
- Particles2D_POP 1.0.0 -- new package (Base, FNS operator family). A 2D particle simulation as a POP loop: a source image emits, curl noise and wind steer, trails stretch, points ride out for your own render.
- ParticlesGpuUltimate 1.0.0 -- new package (Pro, FNS operator family). A GPU particle system driven by images, with look, life, turbulence, wind and force fields and a fluid simulation.
- PasteFromClipboard 3.2.4 -> 3.2.5 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- PrismTOP 1.0.0 -- new package (Base, FNS operator family). A kaleidoscopic prism that renders the input through instanced rotating facets in up to three ring patterns, with a chromatic distortion pass and a dry/wet mix; an alternative for the Tile TOP and the Mirror TOP.
- QuickMarks 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- RealRamp 1.0.0 -- new package (Base, FNS operator family). A GLSL ramp with a true phase and period in four geometries.
- SeqMod 1.0.0 -- new package (Base, FNS operator family). Watches a sequence of parameters on any COMP, publishes the block parameters as one list and fires a callback per added or removed block.
- SlideShow 1.0.0 -- new package (Base, FNS operator family). A folder of images played timed or stepped, in order or random, with a crossfade between slides.
- ThresholdColor 1.0.0 -- new package. A Threshold TOP that keeps the colour, offered as the alternative for the Threshold TOP.
- TopToMidi 1.0.0 -- new package (Base, FNS operator family). Samples an image at points you define and turns the values into MIDI notes in a musical scale.
- midiMapper 3.2.3 -> 3.2.4 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).
- oscMapper 3.2.2 -> 3.2.3 -- the first parameter change on a freshly placed copy is no longer lost, and shrinking a parameter sequence no longer raises an error (shared parameter helper).

Fourteen tools ported into the toolkit from the root PORT TOOLS bench, adopted as packages with unprefixed names. Thirteen are FNS operator family members (the FNS tab of the OP Create dialog); ThresholdColor is the Threshold TOP alternative.
ParHoverMIDI_VSN1: new foreign package. Parameter control by hovering with endless MIDI encoders, built for the Intech Studio VSN1; mirrored from its own GitHub releases, lands at the network root, explicit pick only, updates itself.
- FNSTools.tox and FNS_Installer.tox 3.2.33 -> 3.2.34 -- rebuilt: the installer carries the updated configurator page, and the bootstrap carries updater 3.2.19 with the shared parameter helper fixes

## v3.2.51 -- 2026-09-23

- FNSTools.tox and FNS_Installer.tox 3.2.32 -> 3.2.33 -- rebuilt: every registry host they carry runs the shared base that lets a stamped host's canonical name follow its owner; the bootstrap carries updater 3.2.18
- FNS_AltSelect 3.2.2 -> 3.2.3
- FNS_AutoCombine 3.2.3 -> 3.2.4 -- same watcher fix as AutoRes; a drop into a freshly entered network no longer combines every TOP there.
- FNS_AutoRes 3.2.3 -> 3.2.4 -- a drop no longer resizes every generator TOP on the level. The new-operator watcher compared the network you dropped into against a snapshot of the network you came from, so everything read as new; it now re-baselines when the watched network changes. AutoRes also asks the OS whether Alt is held, so an Alt that stuck after an alt-tab cannot arm it.
- FNS_Autosave 3.2.2 -> 3.2.3
- FNS_BackupCleaner 3.2.2 -> 3.2.3
- FNS_BeatMod 3.2.5 -> 3.2.6
- FNS_BorderlessTD 3.2.3 -> 3.2.4
- FNS_CamSequencer 3.0.7 -> 3.0.8
- FNS_Collect 3.2.1 -> 3.2.2
- FNS_ColorUI 3.2.3 -> 3.2.4
- FNS_CommandKit 3.2.1 -> 3.2.2
- FNS_CommandPalette 3.2.7 -> 3.2.8
- FNS_CommandRegistry 3.2.2 -> 3.2.3
- FNS_ConfigHost 3.2.2 -> 3.2.3
- FNS_ConfigRegistry 3.2.3 -> 3.2.4
- FNS_Console 3.2.9 -> 3.2.10
- FNS_CustomParTools 3.2.4 -> 3.2.5 -- promoting a parameter that has an expression or a bind now carries it onto the promoted parameter, with every relative reference in it (op paths, me, parent(), parent and internal shortcuts) rebased so it resolves the same operators from the target; the original still follows the promoted one as before. A reference that cannot be resolved leaves the value on the promoted parameter and logs why. The customize dialog opens with the Label field showing the parameter's own label, and an empty Label field now means that label, not the name typed in the dialog. the QuickExt new-operator watcher re-baselines when the watched network changes and tolerates a missing Target.
- FNS_ExprHotStrings 3.2.3 -> 3.2.4
- FNS_GlobalOutSelect 3.2.1 -> 3.2.2
- FNS_GlobalVolControl 3.2.2 -> 3.2.3
- FNS_HotkeyManager 3.2.3 -> 3.2.4
- FNS_Hub 3.2.7 -> 3.2.8
- FNS_HubRegistry 3.2.1 -> 3.2.2
- FNS_HydroHomie 3.2.2 -> 3.2.3
- FNS_MainMenuRegistry 3.2.1 -> 3.2.2
- FNS_MediaBrowser 3.2.1 -> 3.2.2
- FNS_Misc 3.2.2 -> 3.2.3
- FNS_MixSequencer 1.0.5 -> 1.0.6
- FNS_NavbarRegistry 3.2.1 -> 3.2.2
- FNS_OpFamily 0.1.4 -> 0.1.5
- FNS_OpMenuMods 3.2.4 -> 3.2.5
- FNS_OpMenuRegistry 3.2.2 -> 3.2.3
- FNS_OpSequencer 1.16.5 -> 1.16.6
- FNS_OpTemplates 3.2.4 -> 3.2.5 -- both new-operator watchers re-baseline when the watched network changes.
- FNS_OpToClipboard 3.2.3 -> 3.2.4
- FNS_OpenExt 3.2.2 -> 3.2.3
- FNS_Output 3.2.2 -> 3.2.3
- FNS_PaletteRegistry 3.2.1 -> 3.2.2
- FNS_PaneTypeRegistry 3.2.2 -> 3.2.3 -- a registered pane type can be picked again from the pane dropdown right after closing a pane that showed it and splitting a new one. TouchDesigner reuses the closed pane's dropdown state for the next pane in that slot; the registry now corrects that state as the dropdown opens, and equips pane slots that appear later in a session.
- FNS_ParOPDrop 3.2.3 -> 3.2.4
- FNS_ParRandomizer 3.2.2 -> 3.2.3
- FNS_ParentHierarchy 3.2.2 -> 3.2.3
- FNS_PreviewPanel 3.2.2 -> 3.2.3
- FNS_ProSceneChanger 1.0.2 -> 1.0.3
- FNS_QuickCollapse 3.2.2 -> 3.2.3
- FNS_QuickPane 3.2.2 -> 3.2.3
- FNS_QuickTime 3.2.2 -> 3.2.3
- FNS_RandomCHOP 1.0.1 -> 1.0.2
- FNS_Remote 3.2.6 -> 3.2.7
- FNS_ResetPLS 3.2.3 -> 3.2.4
- FNS_SearchPalette 3.2.3 -> 3.2.4 -- new Hide Palette When Idle option on the TD-SearchPalette page, off by default. When on, the palette browser closes after the chosen number of minutes without the mouse in it or typing in the search field; opening the palette, moving into it or typing restarts the countdown.
- FNS_SetSmoothness 3.2.2 -> 3.2.3 -- holding Alt while picking a smoothness now sets every TOP in the network on macOS as well. The modifier is Alt on both platforms, as the button help says; the tool asks the OS whether it is held, so an Alt that stuck after an alt-tab no longer forces the set-all path.
- FNS_SimpleSceneChanger 1.0.3 -> 1.0.4
- FNS_SwapOps 3.2.2 -> 3.2.3
- FNS_SwitchOPs 3.2.2 -> 3.2.3
- FNS_SwitchTools 1.1.2 -> 1.1.3
- FNS_TimelineRegistry 3.2.1 -> 3.2.2
- FNS_TimelineTools 3.2.3 -> 3.2.4
- FNS_ToolbarRegistry 3.2.1 -> 3.2.2
- FNS_Updater 3.2.17 -> 3.2.18
- FNS_VSCodeTools 3.2.2 -> 3.2.3
- FNS_iopBrowser 3.2.2 -> 3.2.3
- PasteFromClipboard 3.2.3 -> 3.2.4
- QuickMarks 3.2.2 -> 3.2.3
- TDXMap 1.2.0
- midiMapper 3.2.2 -> 3.2.3
- oscMapper 3.2.1 -> 3.2.2

A registry host stamped by drop-to-register takes its canonical name from the component it lands in by expression, so a pasted copy of that component registers under its own name instead of taking over the original entry. Existing hosts whose name simply repeated their owner are switched to the expression on init; hand-authored names are left alone.

## v3.2.50 -- 2026-09-22

- FNS_CamSequencer 3.0.6 -> 3.0.7 -- the last two Surface Collision tooltips read in plain punctuation. v3.2.49 fixed the other eighteen and missed these, because their text lives in the extension and is re-applied whenever it reloads.
- FNS_MixSequencer 1.0.4 -> 1.0.5 -- the parameter tooltips read in plain punctuation. v3.2.49 announced this and did not deliver it: the text lives in the extension and came back on the next reload.

## v3.2.49 -- 2026-09-22

- FNS_CamSequencer 3.0.5 -> 3.0.6 -- the parameter tooltips read in plain punctuation, and the Source CHOP help now says what the internal joystick actually does, which is stay off until you map a control or start a Learn.
- FNS_MixSequencer 1.0.3 -> 1.0.4 -- the parameter tooltips read in plain punctuation.
- FNS_OpSequencer 1.16.4 -> 1.16.5 -- the parameter tooltips read in plain punctuation.

## v3.2.48 -- 2026-09-21

- FNSTools.tox and FNS_Installer.tox 3.2.31 -> 3.2.32 -- the bootstrap carries updater 3.2.17, which no longer pops a window on project start
- FNS_Updater 3.2.16 -> 3.2.17 -- the popup that appeared on the first project open after an update is gone. The updater now says what landed in the Textport as the update finishes, which is where you already are, and nothing about an update happens on project start.

## v3.2.47 -- 2026-09-21

- FNS_ParOPDrop 3.2.2 -> 3.2.3 -- a drop no longer fails with UnboundLocalError when the held modifier and the latched CHOP flags disagree (after an extension reinit, for one); the placed operator is now decided by the same OS-level modifier check as the drop gate.

## v3.2.46 -- 2026-09-21

- FNSTools.tox and FNS_Installer.tox 3.2.30 -> 3.2.31 -- the install command the website hands you writes into the toolkit's current palette folder; it named the pre-v3.2.42 one, which the toolkit renamed out from under it mid-install; the bootstrap carries updater 3.2.16
- FNS_Autosave 3.2.1 -> 3.2.2 -- carries the current config registry code, which had been frozen several versions back on this tool.
- FNS_BeatMod 3.2.4 -> 3.2.5 -- carries the current config registry code, which had been frozen several versions back on this tool.
- FNS_CommandPalette 3.2.6 -> 3.2.7 -- carries the current config registry code, which had been frozen several versions back on this tool.
- FNS_ConfigRegistry 3.2.2 -> 3.2.3 -- a tool whose config tooltip still named the old palette folder corrects itself when it loads.
- FNS_Remote 3.2.5 -> 3.2.6 -- carries the current config registry code, which had been frozen several versions back on this tool.

The install command on the website works again. It wrote your picks into the toolkit's old palette folder, which the toolkit then renamed out from under it, so the install either lost the file naming your picks or fell back to an older catalog that happened to be on the machine. It now writes to the current folder.

## v3.2.45 -- 2026-09-19

- FNS_OpFamily 0.1.3 -> 0.1.4 -- the FNS operator family has a new color, 0.5 0.5 0.

## v3.2.44 -- 2026-09-19

- FNSTools.tox and FNS_Installer.tox 3.2.29 -> 3.2.30 -- rebuilt, with no change of their own: the toolkit root they carry was re-saved, and shipping different bytes under one rail version is what this bump avoids
- FNS_CamSequencer 3.0.4 -> 3.0.5 -- the game controller is only switched on while you are mapping one or already have one mapped, so a project that never uses a joystick stops polling for one every frame.

## v3.2.43 -- 2026-09-19

- FNSTools.tox and FNS_Installer.tox 3.2.28 -> 3.2.29 -- a clean start refreshes the package catalog before it installs, so a machine whose store predates the release no longer installs that older release into a new project; a tool that is installed without being placed anywhere is recorded as installed; the bootstrap carries updater 3.2.16
- FNS_CamSequencer 3.0.3 -> 3.0.4 -- the preset list opens again, the camera arrives at 0, 0, 5 with fog off, and the tool no longer takes your camera over the moment it lands.
- FNS_OpSequencer 1.16.3 -> 1.16.4 -- a column that lost its header is given its name back, so the preset list keeps working.
- FNS_Updater 3.2.15 -> 3.2.16 -- a tool that is installed without being placed in a project is reported as available on disk, no longer as missing.

A clean start no longer installs an old release. The package store is
machine-wide and outlives every project, so a store left behind by an
earlier install kept being used as the catalog: a fresh project could
install a release several versions old, correct in every byte and wrong
in every version, and the FNS operator family could still drop copies
into your network because that is what the old catalog asked for. The
silent "set up like last time" install now refreshes the catalog before
it plans, which is what the Pick Tools picker has always done.

A tool that installs without being placed anywhere, like the FNS
operator family, is now recorded as installed, so Pick Tools stops
offering it every time.

## v3.2.42 -- 2026-09-18

- FNS_CommandPalette 3.2.5 -> 3.2.6 -- the curation file moved to `FNSTools/config/command-curation.json`.
- FNS_ConfigHost 3.2.1 -> 3.2.2 -- the settings file is `FNSTools/config/FNStools_config.json`.
- FNS_ConfigRegistry 3.2.1 -> 3.2.2 -- the settings file is `FNSTools/config/FNStools_config.json`.
- FNS_CustomParTools 3.2.3 -> 3.2.4 -- the extension template file is looked up under `FNSTools/scripts`.
- FNS_ExprHotStrings 3.2.2 -> 3.2.3 -- its table lives in `FNSTools/tables`.
- FNS_HotkeyManager 3.2.2 -> 3.2.3 -- its gathered hotkeys table lives in `FNSTools/tables`.
- FNS_OpFamily 0.1.2 -> 0.1.3 -- reads its operators from the flat `FNSTools/FNS` folder; the category comes from each operator's manifest.
- FNS_OpMenuMods 3.2.3 -> 3.2.4 -- its tables live in `FNSTools/tables`.
- FNS_OpTemplates 3.2.3 -> 3.2.4 -- the global template library lives in `FNSTools/OpTemplates`.
- FNS_Remote 3.2.4 -> 3.2.5 -- its config file moved to `FNSTools/config/fns_remote.json`.
- FNS_ResetPLS 3.2.2 -> 3.2.3 -- its tables live in `FNSTools/tables`.
- FNS_Updater 3.2.14 -> 3.2.15 -- the package store is `FNSTools/store`, and the family folder and the palette copy are one flat `FNSTools/FNS` folder; a legacy `FNStools_ext` folder is migrated on first sight.

Installing an FNS family tool no longer drops a copy into the network you are working in. The tools are released as family members precisely so you can create them from the FNS tab of the OP Create dialog when you want one, and they are now in the TouchDesigner palette too; installing makes them available rather than placing one.

The toolkit's machine-wide folder in the TouchDesigner user palette is now `FNSTools`; the old `FNStools_ext` folder is renamed into place the first time any tool looks, so the store, your settings, tables and template library all move without a download or a re-save. The FNS operator family lives flat in `FNSTools/FNS`, one tox per tool under its plain name with its manifest beside it, and that same folder is what TouchDesigner's Palette shows.

## v3.2.41 -- 2026-09-18

- FNSTools.tox and FNS_Installer.tox 3.2.27 -> 3.2.28 -- installing an FNS family tool records it and places nothing, instead of spawning a copy into the network you are working in; the bootstrap carries updater 3.2.14
- FNS_CamSequencer 3.0.2 -> 3.0.3 -- the preset list opens again. A nameless column had crept into the presets table, and the list refuses to build on one.
- FNS_MixSequencer 1.0.2 -> 1.0.3 -- a nameless column can no longer break the preset list.
- FNS_OpSequencer 1.16.2 -> 1.16.3 -- a nameless column can no longer break the preset list.
- FNS_Updater 3.2.13 -> 3.2.14 -- the FNS operator tools now appear in TouchDesigner's own palette. They are mirrored into a flat FNStools_ext/FNS folder under their plain names, and TD's palette index is rebuilt and reloaded so they show up without a restart. The versioned family folder the OP Create tab reads is unchanged.

Installing an FNS family tool no longer drops a copy into the network you are working in. The tools are released as family members precisely so you can create them from the FNS tab of the OP Create dialog when you want one, and they are now in the TouchDesigner palette too; installing makes them available rather than placing one.

## v3.2.40 -- 2026-09-18

- FNS_OpFamily 0.1.1 -> 0.1.2
- FNS_ParentHierarchy 3.2.1 -> 3.2.2
- FNS_RandomCHOP 1.0.0 -> 1.0.1
- FNS_iopBrowser 3.2.1 -> 3.2.2

Four more tools stop shipping our version-history apparatus: FNS_OpFamily, FNS_RandomCHOP, FNS_iopBrowser and FNS_ParentHierarchy had no pre-release step at all, so they kept the Version Ctrl page and its tables. They are now cleaned up like every other tool, and open on their first parameter page.

## v3.2.39 -- 2026-09-18

- FNS_AltSelect 3.2.1 -> 3.2.2
- FNS_AutoCombine 3.2.2 -> 3.2.3
- FNS_AutoRes 3.2.2 -> 3.2.3
- FNS_Autosave 3.2.0 -> 3.2.1
- FNS_BackupCleaner 3.2.1 -> 3.2.2
- FNS_BeatMod 3.2.3 -> 3.2.4
- FNS_BorderlessTD 3.2.2 -> 3.2.3
- FNS_Collect 3.2.0 -> 3.2.1
- FNS_ColorUI 3.2.2 -> 3.2.3
- FNS_CommandKit 3.2.0 -> 3.2.1
- FNS_CommandPalette 3.2.4 -> 3.2.5
- FNS_CommandRegistry 3.2.1 -> 3.2.2
- FNS_ConfigHost 3.2.0 -> 3.2.1
- FNS_ConfigRegistry 3.2.0 -> 3.2.1
- FNS_Console 3.2.8 -> 3.2.9
- FNS_CustomParTools 3.2.2 -> 3.2.3
- FNS_ExprHotStrings 3.2.1 -> 3.2.2
- FNS_GlobalOutSelect 3.2.0 -> 3.2.1
- FNS_GlobalVolControl 3.2.1 -> 3.2.2
- FNS_HotkeyManager 3.2.1 -> 3.2.2
- FNS_Hub 3.2.6 -> 3.2.7
- FNS_HubRegistry 3.2.0 -> 3.2.1
- FNS_HydroHomie 3.2.1 -> 3.2.2
- FNS_MainMenuRegistry 3.2.0 -> 3.2.1
- FNS_MediaBrowser 3.2.0 -> 3.2.1
- FNS_Misc 3.2.1 -> 3.2.2
- FNS_NavbarRegistry 3.2.0 -> 3.2.1
- FNS_OpMenuMods 3.2.2 -> 3.2.3
- FNS_OpMenuRegistry 3.2.1 -> 3.2.2
- FNS_OpTemplates 3.2.2 -> 3.2.3
- FNS_OpToClipboard 3.2.2 -> 3.2.3
- FNS_OpenExt 3.2.1 -> 3.2.2
- FNS_Output 3.2.1 -> 3.2.2
- FNS_PaletteRegistry 3.2.0 -> 3.2.1
- FNS_PaneTypeRegistry 3.2.1 -> 3.2.2
- FNS_ParOPDrop 3.2.1 -> 3.2.2
- FNS_ParRandomizer 3.2.1 -> 3.2.2
- FNS_PreviewPanel 3.2.1 -> 3.2.2
- FNS_QuickCollapse 3.2.1 -> 3.2.2
- FNS_QuickPane 3.2.1 -> 3.2.2
- FNS_QuickTime 3.2.1 -> 3.2.2
- FNS_ResetPLS 3.2.1 -> 3.2.2
- FNS_SearchPalette 3.2.2 -> 3.2.3
- FNS_SetSmoothness 3.2.1 -> 3.2.2
- FNS_SwapOps 3.2.1 -> 3.2.2
- FNS_SwitchOPs 3.2.1 -> 3.2.2
- FNS_TimelineRegistry 3.2.0 -> 3.2.1
- FNS_TimelineTools 3.2.2 -> 3.2.3
- FNS_ToolbarRegistry 3.2.0 -> 3.2.1
- FNS_Updater 3.2.12 -> 3.2.13
- FNS_VSCodeTools 3.2.1 -> 3.2.2
- PasteFromClipboard 3.2.2 -> 3.2.3
- QuickMarks 3.2.1 -> 3.2.2
- midiMapper 3.2.1 -> 3.2.2
- oscMapper 3.2.0 -> 3.2.1

Every tool now opens on its first parameter page instead of whichever page happened to be selected when it was built, and none of them carry the version-history apparatus from our own checkout any more. This is the same clean-up the scene changers and sequencers got last release, applied across the whole toolkit.

## v3.2.38 -- 2026-09-18

- FNS_CamSequencer 3.0.1 -> 3.0.2 -- ships without the authoring apparatus it had been carrying: no Version Ctrl page, no version-history tables, and it opens on its first parameter page. Two camera-joystick setup steps that silently failed on every init now run.
- FNS_MixSequencer 1.0.1 -> 1.0.2 -- ships without the authoring apparatus it had been carrying: no Version Ctrl page, no version-history tables, and it opens on its first parameter page.
- FNS_OpSequencer 1.16.1 -> 1.16.2 -- ships without the authoring apparatus it had been carrying: no Version Ctrl page, no version-history tables, and it opens on its first parameter page.
- FNS_ProSceneChanger 1.0.1 -> 1.0.2 -- ships without the authoring apparatus it had been carrying: no Version Ctrl page, no version-history tables, and it opens on its first parameter page.
- FNS_Remote 3.2.3 -> 3.2.4 -- phone pairing ships off. Installing the tool no longer starts a pairing server on your machine; turn Active on when you want to pair.
- FNS_SimpleSceneChanger 1.0.2 -> 1.0.3 -- ships without the authoring apparatus it had been carrying: no Version Ctrl page, no version-history tables, and it opens on its first parameter page.
- FNS_SwitchTools 1.1.1 -> 1.1.2 -- ships without the authoring apparatus it had been carrying: no Version Ctrl page, no version-history tables, and it opens on its first parameter page.

## v3.2.37 -- 2026-09-18

- FNSTools.tox and FNS_Installer.tox 3.2.26 -> 3.2.27 -- the picker reports a catalog it could not fetch instead of promising a refresh, keeps an install plan's buttons in reach however long the list, and the bootstrap carries updater 3.2.12
- FNS_ColorUI 3.2.1 -> 3.2.2 -- the buttons at the bottom of a dialog stay put while its contents scroll.
- FNS_Console 3.2.7 -> 3.2.8 -- the buttons at the bottom of a dialog stay put while its contents scroll, so a long list cannot push them out of reach.
- FNS_Updater 3.2.11 -> 3.2.12 -- a first install on a clean machine can find the package catalog again. The updater looks for the bucket in three places: a mirror you set, the discovery document it has cached, and the endpoint built into it. The built-in one had gone missing, and a machine that had never run FNSTools has no cached document either, so there was nowhere left to look: the picker sat on "First run: fetching the package catalog" forever, because the fetch was refused before it began rather than failing. The endpoint is built in again, derived from the same pinned address discovery uses so the two cannot drift.

The tool picker says so when the catalog cannot be fetched, instead of promising that the page refreshes itself. The reason used to be written where only a developer reading the page source would find it. Its install plan also keeps Install and Close visible however many tools you pick.

## v3.2.36 -- 2026-09-17

- FNS_Console 3.2.6 -> 3.2.7 -- Open Settings opens Settings. It used to hand the panel over with no tab in the address, and the page falls back to its first tab, so you landed on Install & remove. The handover also forces the page to load now: the panel could keep showing whatever it had, which is why the Hub's Console tab sometimes drew the tool picker with no tabs on it until you closed and reopened the hub.

## v3.2.35 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.25 -> 3.2.26 -- the browser that draws the tool picker keeps rendering while its own window is open, so the picker cannot go dead under the reader

The tool picker no longer goes dead under an open window. The browser that draws it now treats its own open window as reason enough to keep rendering, so the page keeps taking clicks whatever else lets go, and the picker identifies its window by the address it served rather than by a port number that can move underneath it.

## v3.2.34 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.24 -> 3.2.25 -- the tool picker stays alive while its window is open, so a dialog left on screen keeps taking clicks

The picker stays alive while its window is open. Reading the Installed dialog without touching the mouse used to count as an abandoned page: the picker server stopped, the browser render went dormant, and the dialog sat on screen taking no clicks with no way back. An open picker window now outranks silence, and the server stops when the window is closed.

## v3.2.33 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.23 -> 3.2.24 -- the bootstrap carries updater 3.2.11

- FNS_Updater 3.2.10 -> 3.2.11 -- a gate call that never answers no longer wedges a download or a membership check. Every call to the licence gate carries a timeout, and a pending answer is watched: when it does not come the pass says so and carries on with the free packages, instead of sitting on "authorising..." or "checking your membership..." until TouchDesigner restarts.

## v3.2.32 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.22 -> 3.2.23 -- the picker waits for a Patreon sign-in for as long as the browser takes, refreshes itself when the sign-in lands (including one that unlocks nothing), and carries a Reload picker button in every auth dialog

The picker waits for a Patreon sign-in properly. The browser round trip can take as long as it takes, the page notices when the sign-in lands and refreshes itself, and every wait carries a Reload picker button, since the panel inside TouchDesigner has no reload of its own. It also notices a sign-in that unlocks nothing, which used to look like nothing happening at all.

## v3.2.31 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.21 -> 3.2.22 -- the picker offers Sign in with Patreon whenever the signed-in session includes no packages, says so in the account line, keeps I just pledged beside it, and lets an entitled account switch to a different one; the bootstrap carries updater 3.2.10
- FNS_Updater 3.2.9 -> 3.2.10 -- a Patreon session that includes no packages now offers the way in. A fresh install can adopt the machine session another Function Store product signed in with, and where that session has no Patreon link the picker showed only Join and I just pledged. It now offers Sign in with Patreon in the welcome, the header and the Patreon dialog, says plainly that the session holds no packages, and lets a signed-in account switch to a different one without signing out first.

## v3.2.30 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.20 -> 3.2.21 -- the picker offers "Add FNS tab to OP Create" while an FNS family operator is ticked, and the toolkit root's FNSTools page carries the same choice as a per-project toggle; the bootstrap carries updater 3.2.9
- FNS_OpFamily 0.1.0 -> 0.1.1 -- no longer offered on its own in the picker. It installs together with the first FNS family operator and is removed with the last, so projects without family operators get no FNS tab and no family registry. The tab is also optional: Pick Tools shows "Add FNS tab to OP Create" while a family operator is ticked, and the new Remove Operator Family command turns it off later while your tools stay installed. The toolkit root's FNSTools page has an FNS Tab in OP Create toggle for the same choice, per project.
- FNS_Updater 3.2.8 -> 3.2.9 -- keeps no FNS family folder in a project where the family is not installed.

## v3.2.29 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.19 -> 3.2.20 -- the picker's header and Patreon dialog offer Sign in again when the Patreon link is gone, and the toolkit root's page no longer carries Installer Parameters; the bootstrap carries updater 3.2.8
- FNS_Updater 3.2.7 -> 3.2.8 -- when Patreon reports that this install's link is no longer active, the picker offers Sign in again with Patreon, in the header and in the Patreon dialog, instead of a Check again that could never succeed. Tools the account still holds stay unlocked.

## v3.2.28 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.18 -> 3.2.19 -- the picker reads the recommendations list through the installer instead of fetching it from the bucket, which TouchDesigner's browser blocked

The picker inside FNSTools.tox can show recommended tools by other creators again. It used to ask the download server for that list directly, which the browser inside TouchDesigner blocks; it now gets the list through the toolkit, which keeps a copy up to date in the background and drops a removed recommendation within minutes.

## v3.2.27 -- 2026-09-17

- FNSTools.tox and FNS_Installer.tox 3.2.17 -> 3.2.18 -- the picker checks for a newer release when it opens and updates its list, and Install waits for a running store job instead of failing

The picker inside FNSTools.tox checks for a newer release every time it opens. A machine that already had a store from an earlier release used to keep showing that release's package list; now the list updates itself, or offers a reload if you had already started picking. Clicking Install while that check or a background download is still running now waits for it instead of failing.

## v3.2.26 -- 2026-09-17

- FNS_CamSequencer 3.0.0 -> 3.0.1 -- joins the FNS operator family: listed on the FNS tab of the OP Create dialog once the store holds it.
- FNS_MixSequencer 1.0.0 -> 1.0.1 -- joins the FNS operator family: listed on the FNS tab of the OP Create dialog once the store holds it.
- FNS_OpFamily 0.1.0 -- new. The FNS operator family, a tab in the OP Create dialog whose members are FNS tools mirrored from the store; built with TDFam. Stub, Replace Stubs, Update and Sync commands work without dialogs, and TDFam never stubs or replaces the toolkit's own copies.
- FNS_OpSequencer 1.16.0 -> 1.16.1 -- joins the FNS operator family: listed on the FNS tab of the OP Create dialog once the store holds it.
- FNS_ProSceneChanger 1.0.0 -> 1.0.1 -- joins the FNS operator family: listed on the FNS tab of the OP Create dialog once the store holds it.
- FNS_RandomCHOP 1.0.0 -- new, at the Base tier. The random-value CHOP is the family's first member and stays the alternative for the Noise CHOP.
- FNS_SimpleSceneChanger 1.0.1 -> 1.0.2 -- joins the FNS operator family: listed on the FNS tab of the OP Create dialog once the store holds it.
- FNS_SwitchTools 1.1.0 -> 1.1.1 -- joins the FNS operator family: listed on the FNS tab of the OP Create dialog once the store holds it.
- FNS_Updater 3.2.6 -> 3.2.7 -- keeps the FNS operator family's folder in step with the store after every refresh and update, so the FNS tab lists exactly the members this machine holds.
- FNSTools.tox and FNS_Installer.tox rebuilt at 3.2.17 -- the one-drop bootstrap carries updater 3.2.7 and the toolkit root with the FNS operator family

Released tools no longer carry Private Investigator markers. Every exported tox is scrubbed of the pi_suspect and FNS_externalized tags and of Vcoriginal, so a tool placed from the store or updated in place is never mistaken for a tracked development original by Private Investigator. Nothing else in the tools changes.

## v3.2.25 -- 2026-09-17

- FNS_ProSceneChanger 1.0.0 -- new: the Pro scene changer is its own package at the Pro tier, installed under its own name beside SimpleSceneChanger, so a Pro member can keep the simple one or run both in one fleet.
- FNS_SimpleSceneChanger 1.0.0 -> 1.0.1 -- no longer carries a Pro build inside its own row; ProSceneChanger is a separate package.

## v3.2.24 -- 2026-09-17

- FNS_SimpleSceneChanger 1.0.0 -- new, from the SceneChanger family: a scene changer for TOP outputs that cuts, fades or eases between wired scenes by select, timer, A/B fader or CHOP, cooking only the scenes on screen. The Pro build, the first tier variant, adds per-scene modes and timing, a cue table, CHOP output blending and fleet follow; the picker lands whichever build your account holds. Spawns into the network you are working in.
- FNS_SwitchTools 1.1.0 -- new, from the SceneChanger family: a companion for any Switch, Cross or multi-input operator that drives the index, colours the live input, cooks only the inputs in use and unloads the rest, and reorders, reverses, randomizes or aligns the inputs. Spawns into the network you are working in.
- FNS_Updater 3.2.5 -> 3.2.6 -- understands a package with tier variants (a Pro build beside the Base build): it fetches and installs the highest build your account holds, offers the swap upward when your tier grows, keeps an installed Pro build as it is if your tier drops, and counts every build in the store.
- FNSTools.tox and FNS_Installer.tox 3.2.16 -> 3.2.17 -- the picker shows a package's Pro build on its own row and the installer lands the build your account holds

## v3.2.23 -- 2026-09-17

- FNS_CamSequencer 3.0.0 -- new, from the OpSeqDev family: a camera with two preset sequencers inside, for its own transform and lens and for the Look At target, driven by hand, by a CHOP or by a joystick. Spawns into the network you are working in.
- FNS_MixSequencer 1.0.0 -- new, from the OpSeqDev family: a step sequencer of mixes over an OpSequencer's presets, each step a weight vector, crossfaded with easing. Spawns into the network you are working in.
- FNS_OpSequencer 1.16.0 -- new, from the OpSeqDev family: a preset sequencer for one operator, storing its parameter states in a table and scrubbing, jumping or mixing between them with easing. Spawns into the network you are working in.

## v3.2.22 -- 2026-09-17

- FNS_Updater 3.2.4 -> 3.2.5 -- a new toggle, Keep the Whole Release in the Store (on by default): after an install or an update pass the rest of the release is downloaded into the store, about 12 MB, so Pick Tools works offline afterwards and everything the store can offer is already on the machine. Off: only what you install is fetched.
- FNSTools.tox and FNS_Installer.tox 3.2.15 -> 3.2.16 -- the picker shows TDXMap's trial and never ticks a family product for you; an install ends by filling the store

TDXMap is no longer counted among the free tools. The picker, the website and its page now say what it is: a 14-day trial, then a Base or Pro licence; it still installs for everyone from the picker.

## v3.2.21 -- 2026-09-16

- FNS_Console 3.2.5 -> 3.2.6 -- hover text in the console and the tool picker now shows in TouchDesigner. The browser inside TouchDesigner never drew the standard tooltips, so a card whose description was cut short had no way to show the rest; every hover text is now drawn by the page itself, with the full description on a card.
- FNSTools.tox and FNS_Installer.tox 3.2.14 -> 3.2.15 -- the tool picker inside the installer draws its own hover text too

## v3.2.20 -- 2026-09-16

- FNSTools.tox and FNS_Installer.tox 3.2.13 -> 3.2.14

A new toggle on the toolkit root, Always Set Up Like Last Time: with it on, dropping FNSTools.tox into a new project installs the tools of the project you saved last with nothing to click, no picker and no window, progress in the Textport. It roams with your settings, so it applies to every new project on the machine.

## v3.2.19 -- 2026-09-16

- FNSTools.tox and FNS_Installer.tox 3.2.12 -> 3.2.13

A toolkit that lands somewhere you were not looking is now shown to you. After a drop into a network inside a component, and after an install pasted into the Textport, it is placed above the topmost operator at the top of the project, the network editor goes there, and the toolkit is selected.

## v3.2.18 -- 2026-09-16

- FNSTools.tox and FNS_Installer.tox 3.2.11 -> 3.2.12

Dropping FNSTools.tox into a network inside a component moves the toolkit to the top of the project as before, and now takes the network editor there with it and selects the toolkit, so it is easy to find. The questionnaire's result names its Patreon tools once, and its count matches what it ticks.

## v3.2.17 -- 2026-09-16

- FNS_Updater 3.2.3 -> 3.2.4 -- a download that gets no response ends with an error you can retry. On a slow or stalled connection the store refresh could wait forever, which is how a fresh install on a Mac never finished.

The tool picker now leads with what is free, and names the Patreon tools with the tier they unlock at. Recommended, Everything and the other starting points leave out a Patreon tool the account cannot install yet, ticking one by hand explains how it unlocks and offers sign-in, and an install never waits on a Patreon tool the account does not include. Closing the install dialog now closes it.

## v3.2.16 -- 2026-09-16

- FNS_Updater 3.2.2 -> 3.2.3 -- the update check when a project opens and the what's-new prompt after an update now run. Both were scheduled in a way that never reached the updater, so neither had been running.

A fresh install from the website opens the tool picker again. Dropping FNSTools.tox into a new project had shown an empty browser and installed nothing, so the toolkit arrived without its Hub or anything else.

## v3.2.15 -- 2026-09-15

- FNS_CommandPalette 3.2.3 -> 3.2.4 -- commands from a tool with several copies read "label · copy", so identical commands are no longer indistinguishable. A preset over such a tool lists once per copy, or can be pinned to one copy; favourites still apply to the command on every copy.
- FNS_CommandRegistry 3.2.0 -> 3.2.1 -- tools that live as several copies can label each copy. An owner that promotes FnsInstance() sends that label with every command, and FnsToolName() keeps one public tool name when the copies have different COMP names, so favourites, overrides and presets reach every copy. When several packages declare the same canonical id, every copy of the winning tool now stays listed.

## v3.2.14 -- 2026-09-14

- FNS_AutoCombine 3.2.2 -- the same fix as AutoRes; an Alt-drop no longer rewrites Combine Input and Operand on a backlog of operators that appeared elsewhere in the network.
- FNS_AutoRes 3.2.2 -- an Alt-drop touches only the operator you dropped. The watcher used to snapshot the whole subtree of the open network but only re-checked on direct child changes, so anything that appeared deeper in between (a reloaded package, a replicator) was reported as new at the next drop and had its resolution rewritten too.

## v3.2.13 -- 2026-09-14

- FNS_Updater 3.2.2 -- the popup with release notes after an update can be switched off with the new Show Notes After Update toggle; the choice roams with your settings.

## v3.2.12 -- 2026-09-14

- FNS_AltSelect 3.2.0 -> 3.2.1
- FNS_AutoCombine 3.2.0 -> 3.2.1
- FNS_AutoRes 3.2.0 -> 3.2.1
- FNS_BackupCleaner 3.2.0 -> 3.2.1
- FNS_BeatMod 3.2.2 -> 3.2.3
- FNS_BorderlessTD 3.2.1 -> 3.2.2
- FNS_ColorUI 3.2.0 -> 3.2.1
- FNS_CommandPalette 3.2.2 -> 3.2.3
- FNS_CustomParTools 3.2.1 -> 3.2.2
- FNS_ExprHotStrings 3.2.0 -> 3.2.1
- FNS_GlobalVolControl 3.2.0 -> 3.2.1
- FNS_HotkeyManager 3.2.0 -> 3.2.1
- FNS_Hub 3.2.5 -> 3.2.6
- FNS_HydroHomie 3.2.0 -> 3.2.1
- FNS_Misc 3.2.0 -> 3.2.1
- FNS_OpMenuMods 3.2.1 -> 3.2.2
- FNS_OpTemplates 3.2.1 -> 3.2.2
- FNS_OpToClipboard 3.2.1 -> 3.2.2
- FNS_OpenExt 3.2.0 -> 3.2.1
- FNS_Output 3.2.0 -> 3.2.1
- FNS_ParOPDrop 3.2.0 -> 3.2.1
- FNS_ParRandomizer 3.2.0 -> 3.2.1
- FNS_PreviewPanel 3.2.0 -> 3.2.1
- FNS_QuickCollapse 3.2.0 -> 3.2.1
- FNS_QuickPane 3.2.0 -> 3.2.1
- FNS_QuickTime 3.2.0 -> 3.2.1
- FNS_Remote 3.2.2 -> 3.2.3
- FNS_ResetPLS 3.2.0 -> 3.2.1
- FNS_SetSmoothness 3.2.0 -> 3.2.1
- FNS_SwapOps 3.2.0 -> 3.2.1
- FNS_SwitchOPs 3.2.0 -> 3.2.1
- FNS_Updater 3.2.0 -> 3.2.1
- FNS_VSCodeTools 3.2.0 -> 3.2.1
- PasteFromClipboard 3.2.1 -> 3.2.2
- QuickMarks 3.2.0 -> 3.2.1
- midiMapper 3.2.0 -> 3.2.1

Most tools are lighter inside: they drop a set of unused internal helpers (NoNode and its callback operators) and register their quick-launch commands themselves. Nothing changes in how any tool works or which commands it offers.

## v3.2.11 -- 2026-09-14

- FNS_BeatMod 3.2.1 -> 3.2.2 -- Undoing the deletion of a modulator reconnects the parameters it drove, also when the undo lands while they are still gliding back to rest. Pasting a cut modulator reconnects them as well.
- FNS_BorderlessTD 3.2.0 -> 3.2.1 -- The project name in the menu bar now shows the unsaved-changes asterisk in a normal window too, and reads it from this project's own window when several TouchDesigner instances are open.
- FNS_CommandPalette 3.2.1 -> 3.2.2 -- Typing is much faster: each keystroke ranks the whole catalogue in tens of milliseconds, where it used to take up to half a second. Results and their order are unchanged.
- FNS_OpMenuMods 3.2.0 -> 3.2.1
- FNS_OpTemplates 3.2.0 -> 3.2.1
- FNS_OpToClipboard 3.2.0 -> 3.2.1 -- With the mouse over a parameter, the copy shortcut copies a reference to that parameter (`.par.tx`), or to the whole group when the mouse is over a row's name (`.parGroup.t`). The pasted `@` resolves to the operator path as before.
- FNS_PaneTypeRegistry 3.2.0 -> 3.2.1
- FNS_SearchPalette 3.2.1 -> 3.2.2 -- With Latest Only on, numbered variants of a component (tool, tool1, tool2) now collapse only when they sit in the same folder. A numbered component in another folder, such as thdColor1 next to a thdColor saved elsewhere, is listed again. The same name saved in two folders still shows once. The search field is now a Text COMP, so Ctrl+Left and Ctrl+Right jump by word as in any other text field, and Ctrl+Shift+F clears the field before focusing it.
- FNS_TimelineTools 3.2.1 -> 3.2.2
- PasteFromClipboard 3.2.0 -> 3.2.1 -- Image files copied in Explorer now paste too, one operator per file. File In copies each file into the Save Folder by default; turn off the new Copy Pasted Files toggle to read the originals where they are. Script TOP and Annotate decode the file directly.

## v3.2.10 -- 2026-09-14

- FNS_OpMenuRegistry 3.2.1 -- a tool installed into a running session gets its OP Create dialog contributions at once. Registering only rebuilt the right-click menu when the dialog already existed, so OpMenuMods' search words and IO filter, and OpTemplates' markers, only appeared after a restart.

## v3.2.9 -- 2026-09-14

- FNS_Hub 3.2.5 -- the window is wider, 1040 by 800, so the picker's toolbar with its action, and the category chips with Expand and Collapse, each stay on one line.

Inside the Hub the picker keeps its chip row at every width instead of switching to the site's side rail, which spent a column on seven chips and left it empty below them.

## v3.2.8 -- 2026-09-13

- FNS_Console 3.2.5

Inside the Hub the install action sits at the top: the selection count and the Review install button take the spot the docs link had, the supporter status and Check again fold into the Plus line, and the sticky footer is gone.

## v3.2.7 -- 2026-09-13

- FNS_Hub 3.2.4 -- no black band above the tabs on a fresh install (the tab bar's height change left the layout half updated), and the Console tab is sized by the Hub itself when it shows, so the page renders at the tab's size on every install, not only where the Hub was already there.

The word "Plus" is gone. Tools that need a membership are marked with the lowest Patreon tier that unlocks them, Patreon:Base, Patreon:Pro or Patreon:Coaching, in the picker and on the website, and licence keys are called Gumroad licence keys. The sign-in button reads Sign in with Patreon. The explainer page moved to functionstore.tools/patreon/, and the old /plus/ address redirects there.

## v3.2.6 -- 2026-09-13

- FNS_Console 3.2.4 -- the Install & remove tab's explanatory paragraph is one sentence, and a tab is always loaded fresh, never from the browser's cache, so an updated picker shows up at once.
- FNS_Hub 3.2.3 -- the window is taller, 900 by 800, so the console and the configurators get the room they need.

The install plan reads as what will happen: how many tools install and with how much core, each as a chip by its title, removals and problems called out, what is already in the project folded into one line.

The Hub's Console tab renders at its own size. The toolkit's browser panel was a fixed 1280 by 720 page scaled down into the tab, which made the text small and left black bands above and below; it now takes the size of the area that shows it.

The picker is calmer inside TouchDesigner: a selected tool shows as a filled checkbox on a lifted card instead of a yellow border on every card, the Plus strip is one quiet line with the explanation as a tooltip, the category pitches step back, the category rail steps aside (the section headers carry the counts), the footer is one short line with one action, unlocked Plus chips are outlined instead of filled, the duplicate Show only Plus link is gone (the toolbar button does that), and Copy list is gone everywhere (the paste script and Download selection.json cover it).

## v3.2.5 -- 2026-09-13

- FNS_Console 3.2.3 -- the Install & remove tab passes the picker's "open in browser" requests through, so docs links open your browser from inside the Hub.

Docs links in the picker work inside TouchDesigner: every external link, including each tool in the install report (click a tool to read its docs), opens your system browser instead of vanishing into a blocked popup.

## v3.2.4 -- 2026-09-13

An install never removes the toolkit root's own settings host again. It shares its name with the standalone FNS_ConfigHost package, and the picker's apply pass read it as an unchecked tool: a fresh install reported "removed FNS_ConfigHost" and that project lost its roaming root settings and its last-install record.

"Set up like last time" is the first card on a first run and installs on that one click; there is no review step for a list you already chose in a project you saved. The install report is a report now: the number of tools installed up front, each tool as a chip by its title, removals struck through and failures marked, core folded into the label.

## v3.2.3 -- 2026-09-12

- FNS_BeatMod 3.2.1 -- the modulator manager window opens on the display the cursor is on.
- FNS_Console 3.2.2 -- the console page tells its server it is still in use while you are at it, so the Hub's Console tab no longer goes dead after ten quiet minutes.
- FNS_Hub 3.2.2 -- the Hub window opens centred on the display the cursor is on, instead of the bottom-left corner of display 0 (which on a multi-monitor desk was a different screen from the one you were working on).
- FNS_Remote 3.2.2 -- the QR pairing window opens on the display the cursor is on.

A pasted install now says in the Textport what it did and what it is opening, waits for the FNS console to come up before handing over, and says so when it opens the picker instead.

The picker's Close button no longer dies a minute after an install: the installer's server now stops only after the page has gone quiet (the page reports itself in use while you are at it), and it releases the browser's render only when the browser still shows the picker, never a hold the console owns.

"Set up like last time" works: a fresh bootstrap, dropped or pasted, offers the tools your last saved project installed, pre-checked and never applied on its own. It had not fired since the toolkit root started shipping its own settings host, which the first-run test mistook for an installed tool.

## v3.2.2 -- 2026-09-12

- FNS_Console 3.2.1 -- Install & remove is the first tab, and the tab a console opened without a named tab shows.
- FNS_Hub 3.2.1 -- showing the Console tab no longer raises "Cannot execute Javascript" on a fresh install: the tab reloads the page only when the browser's render is already live, and a render that switches on loads the page by itself.
- FNS_TimelineTools 3.2.1 -- The Keyframer makes an Animation COMP when none is selected. A drop on the strip, or Add Channels, with no animation creates one beside the operator being keyed and opens it in the Animation editor; the editor's own scratch animation under /ui never counts as the target.

A pasted install script now lands in the FNS console's Install & remove tab (in the Hub when the Hub is installed) once the install has finished, also when nothing but the bootstrapper was picked; a paste with Plus picks waiting still opens the sign-in picker instead. The "Set up like last time" offer appears on a root that holds core and no tools, so a pasted install sees it too.

## v3.2.1 -- 2026-09-11

- FNS_CommandPalette 3.2.1 -- typed queries now match in tiers (exact, prefix, word start, substring, initials, typo, subsequence), so a typo like "opne ext" or "nosie" still finds its command, abbreviations no longer fill the list with subsequence noise, a title hit outranks the same hit in a category, and "randomise" finds Randomize. Nothing that matched before ranks differently: the looser tiers only fill below the strict ones.
- FNS_CustomParTools 3.2.1 -- dropping an operator on the path bar with Ctrl+Alt promotes it as an internal operator again (the route had been broken since 3.2.0), and the root cell is a target now, so a shortcut can be added to / as well.
- FNS_ParentHierarchy 3.2.1 -- no longer draws a button in the pane bar. The doc always said it adds none; the button was a leftover of the split from iopBrowser and did nothing when pressed. The Alt-hover on the path is unchanged.
- FNS_Remote 3.2.1 -- The tool reports its own package version to anything that asks it what it is. That number had been frozen at an internal 0.1.0 since the tool was first built, so a launcher showing it saw the wrong version.
- FNS_SearchPalette 3.2.1 -- the fuzzy fallback that ran when nothing matched literally now tolerates typos ("nosie", "fedback", "kinnect"), spellings either side of the Atlantic ("randomise", "colour") and initials ("mfo"), ranked above the old subsequence reading; the strict search, wildcards, exclusions and folder tokens are unchanged.
- FNS_iopBrowser 3.2.1 -- drop an operator on its pane-bar button to add it as an internal operator shortcut of the network you are in, the root included.

The picker gains a Plus-only filter, and says what a Plus pick means where
it would otherwise surprise: on the Plus line, on the questionnaire's
result (with a Leave Plus out button), and in the paste-script dialog.


The picker's categories and the questionnaire's fits were re-read from each
tool's documentation and parameters: five tools moved category (CommandKit
to Developer, HydroHomie to Workflow, OpToClipboard and SetSmoothness to
Parameters, PreviewPanel to Surfaces), six
descriptions were corrected, and the Command, Palette and Timeline
registries are core packages now, as the catalog always said.

## v3.2.0 -- 2026-09-11

- FNS_AltSelect 3.2.0
- FNS_AutoCombine 3.2.0
- FNS_AutoRes 3.2.0
- FNS_Autosave 3.2.0
- FNS_BackupCleaner 3.2.0 -- New package. Every .toe backup TouchDesigner has written under
- FNS_BeatMod 3.2.0
- FNS_BorderlessTD 3.2.0 -- Enable and Enabletimeline are now Active and Activetimeline.
- FNS_Collect 3.2.0
- FNS_ColorUI 3.2.0
- FNS_CommandKit 3.2.0
- FNS_CommandPalette 3.2.0 -- The ~ prefix now completes instead of firing. Enter, a click Placing one of TouchDesigner's built-in palette components
- FNS_CommandRegistry 3.2.0
- FNS_ConfigHost 3.2.0
- FNS_ConfigRegistry 3.2.0 -- The roaming settings file now records each parameter's
- FNS_Console 3.2.0
- FNS_CustomParTools 3.2.0 -- Renamed from CustomParTools, and it now carries the pane-bar The nine Modules toggles are named Active... rather than
- FNS_ExprHotStrings 3.2.0
- FNS_GlobalOutSelect 3.2.0 -- Refreshing the tab is about four times faster and no
- FNS_GlobalVolControl 3.2.0
- FNS_HotkeyManager 3.2.0 -- Copies of one component that all carry the same binding
- FNS_Hub 3.2.0
- FNS_HubRegistry 3.2.0
- FNS_HydroHomie 3.2.0 -- The Enable parameter is now called Active. It comes back at its
- FNS_MainMenuRegistry 3.2.0
- FNS_MediaBrowser 3.2.0
- FNS_Misc 3.2.0 -- Renamed from MISC, and it now carries what was left of FNS_Toolbar --
- FNS_NavbarRegistry 3.2.0
- FNS_OpMenuMods 3.2.0 -- The node-table stage now applies the registry's alternatives
- FNS_OpMenuRegistry 3.2.0 -- Tools can now register themselves as alternatives for a
- FNS_OpTemplates 3.2.0 -- A Library Scope setting says where your templates live:
- FNS_OpToClipboard 3.2.0
- FNS_OpenExt 3.2.0
- FNS_Output 3.2.0
- FNS_PaletteRegistry 3.2.0
- FNS_PaneTypeRegistry 3.2.0
- FNS_ParOPDrop 3.2.0
- FNS_ParRandomizer 3.2.0
- FNS_ParentHierarchy 3.2.0 -- New package. Hover a parent in the pane-bar path with Alt to
- FNS_PreviewPanel 3.2.0
- FNS_QuickCollapse 3.2.0
- FNS_QuickPane 3.2.0
- FNS_QuickTime 3.2.0
- FNS_Remote 3.2.0 -- Pairing shows the QR code in a small window inside TouchDesigner,
- FNS_ResetPLS 3.2.0 -- Renamed from ResetPLS1, and its Enableall parameter is now
- FNS_SearchPalette 3.2.0
- FNS_SetSmoothness 3.2.0
- FNS_SwapOps 3.2.0
- FNS_SwitchOPs 3.2.0 -- No longer raises when a selected operator is destroyed in the
- FNS_TimelineRegistry 3.2.0
- FNS_TimelineTools 3.2.0
- FNS_ToolbarRegistry 3.2.0
- FNS_Updater 3.2.0 -- The Enabled parameter is now called Active. It comes back at its
- FNS_VSCodeTools 3.2.0
- FNS_iopBrowser 3.2.0 -- New package. Browse the internal operators and the OP tree of the
- PasteFromClipboard 3.2.0
- QuickMarks 3.2.0
- TDXMap 1.2.0
- midiMapper 3.2.0
- oscMapper 3.2.0

Every tool in the toolkit now reports the same version, 3.2.0. Up to now each
package carried its own number, so a catalogue where one tool read 3.0.4 and its
neighbour read 0.1.3 told you nothing about which release they came from. From
here the version is the release: if two tools disagree, one of them is behind.
Tools that gained nothing new in this release still move to 3.2.0, and that is
the point of the change, so nothing you install is left on a number that has to
be looked up.

FNS_Navbar has been dissolved into the tools it carried, so each one installs on
its own. Nothing is lost: everything that was on the pane bar is still there,
published by a smaller package.

network you are in, from a popup opened off the pane bar. The browser exists once
and every pane's button calls into it, so the bar carries 52 operators per pane
instead of the 959 the old combined widget copied into each one.

see its shortcuts, internal operators and now its extensions too; hover an
extension to expand the API TouchDesigner promotes from it, and click any row to
copy a reference you can paste, down to ext.MyExt.MyMethod(args). Adds no button
of its own. One popup serves every pane, so the bar carries 112 operators per
pane rather than the 959 the old combined widget copied into each one.

path-cell injection and drag-drop hijack that used to live in FNS_Navbar. Install
it under the new name to keep getting updates; the old package stays where it is
and stops being offered. A new Modules page switches each of the nine
sub-modules on or off on its own, so you can keep the parts you use and drop the
rest. Turning one off withdraws the surface it owns rather than leaving a dead
control behind: the two pane-bar widgets unregister and disappear from every bar,
and the button itself leaves the navbar and the toolbar once every action it
fronts is off.

or Right on a method fills the box so you can type arguments, and Enter again
runs it; Tab only ever completes. ~ext. lists the extensions on the COMP you are
on and ~ext.MyExt. narrows to one of them, listing everything reachable through
ext.MyExt rather than only what is promoted, so the lowercase half of an
extension is callable too. The accessors CustomParHelper generates for each
parameter are left out of that list, which on a big tool is the difference
between fifty rows and a thousand.

Every tool now installs under an FNS_ name. The prefix was already on about half
the toolkit and missing from the rest, which made the install list read like two
different products. Nothing about a tool changed in the renaming, but a rename is
a new package: your installed copies keep working and stop being offered updates,
so reinstall the ones you use under their new names. Four keep their old names on
purpose: PasteFromClipboard, QuickMarks, midiMapper and oscMapper.

Renamed with a new base name, so they read differently in the list: MISC is now
FNS_Misc, OUTPUT is FNS_Output, ResetPLS1 is FNS_ResetPLS, TDX_SearchPalette is
FNS_SearchPalette, FNS_OpMenu is FNS_OpMenuMods, and paste_from_clipboard is
PasteFromClipboard. Everything else simply gained the prefix.

The on/off parameter is called Active everywhere now. Most of the toolkit already
used it, which is also TouchDesigner's own name for that switch, so the five
tools that said Enable have been brought in line: FNS_HydroHomie,
FNS_BorderlessTD, FNS_Updater, FNS_ResetPLS and FNS_CustomParTools. A renamed
parameter loses its stored setting once, so those five come back at their
defaults, which is on.

default, on, once.

They come back at their defaults, on, once.

default, on, once.

Activeall. Install it under the new name to keep getting updates.

Enable..., matching the rest of the toolkit.

the toolbar background widget and the command that opens the toolbar
configurator. Install it under the new name to keep getting updates.

FNS_Toolbar: retired. The toolbar surface itself has been built by
FNS_ToolbarRegistry for a while, so the package had shrunk to a background
widget and one command; both moved to FNS_Misc rather than staying behind a
package of their own.

The install picker now ranks minor tools last. A handful of packages are small
conveniences rather than things you go looking for, and they were taking the
same space and the same weight as everything else. Those now sort to the end of
their own category and draw in a denser, lighter card, so a category reads as
the tools you came for plus a short footnote. Nothing is hidden and nothing
moves out of its category; they are still there and still tickable.

stock operator type. Create an operator with the alternatives shortcut held
(alt ctrl by default, on the registry's new Alternatives page) and every
alternative any installed tool has declared for that type is offered: one is
placed straight away, several open a picker. What used to be OpTemplates' own
engine, watching for new operators and swapping in a template with its wiring
restored, is now the registry's, and OpTemplates is its first contributor. A
tool that is only in your store, downloaded but not in the project, is offered
too, below a divider, and placed from disk as one node; nothing is installed by
that. In the operator list, ' >>>' marks a type with an alternative in the
project and ' >>' one whose only alternatives are in the store. A tool that
stands in for several types declares its alternative once, under one key that
lists the types separated by spaces. The registry hosts inside tools no longer
carry their own copy of the shortcut, so the hotkey manager lists it once. Fixed before release: the ' >>>' mark
was computed but never applied by the dialog's node table, a pane switch was
read as a batch of new operators, an alternative could be offered inside
its own source, and a placed copy of a tool registered itself as one more
alternative. A placed chain lands with its first operator exactly where you
clicked and the rest to the right, wired as in the library even when the
paste had to rename an operator.

mark per row, so ' >>>' and ' >>' show again for every contributor.

global (one .tox in your user palette, as before), project (a component at
the network root that saves with the .toe and survives toolkit updates), or
follow the toolkit's Config Scope, the default. A missing library is created
from the set loaded at that moment; switching from project to global asks
whether to push the project set, adopt the global one or stay; Push To
Global writes the active set to the palette file behind a prompt. The
External Templates Sync toggle and the Advanced mode are retired, and a
component Advanced pointed at is adopted as the project library. The
library is also published through the op-menu registry now, which owns the
watcher, the shortcut and the placement; nothing about the templates
themselves changed. Also fixed a long-standing leak: placing a
template that is a COMP left TEMPLATE_ROOT/IN/OUT tags on the library's own
children, and a stale TEMPLATE_OUT is what the next placement wires the
outputs to. Forty-six library operators carried them; the library was cleaned
and the engine now cleans every operator it tags. The shortcut now lives on
FNS_OpMenuRegistry's Alternatives page; a Keys value you had customised is
carried over there on first start, and Keys then mirrors it.

Registries keep every registration across a global takeover. When a newer
registry replaces the live one, the live entry table wins for every name it
holds, and a master or host that is not the global no longer keeps a parallel
table of its own. Before this, an update to the Hub or Palette registry could
bring back a tool's stale tab order or visibility from the master's copy.
(Ship this release with the [All] scope: the shared RegistryBase changed, and
every registry master and every host carries an embedded copy, so a [Bumped]
release would mix the new base with the old one on installed machines.)

same frame the selection changes.

(the T3D package's bypass shortcut inside every T3D operator, 25 of them)
list as one row with a count, rebind and reset together, and no longer show
as conflicts with each other. A status readout or a stored list whose name
happens to contain "key" (TimelineTools' Keyframer status, CommandPalette's
favourites) is no longer listed as a binding. A modifier-only binding that
another tool also holds (alt, held by four tools for four different gestures)
is marked shared in a quiet yellow instead of red or nothing.

The content CMS can now declare which operator types a package is an
alternative for, on a foreign package or on a live package that carries no
op-menu host; a package with a host keeps deriving the list from its own
callbacks, and a curated list beside a host is reported at preflight.

now lands the component itself, not the bundle Derivative ships it in (a
wrapper holding the component, its icon and its help text), and hands it to
your mouse to place, exactly like a new operator from the OP Create dialog. A
row can also be pressed and dragged into a network, the Palette browser's own
gesture.

The picker on /get and in the installer folds into category sections:
the first screen is the eight categories with their pitch and counts, a
section opens on click, on a filter match or when a guided-setup preset
selects into it, and a side rail on wide screens jumps and opens. Cards
lost their surface chips (the surfaces stay searchable and ride the
tooltip) and clamp their description to two lines. The installer keeps
the raw view with every section open.

a folder you choose, grouped by the project that made them, with the disk space
they take and an estimate of the hours of work they hold; send the ones you are
finished with to the recycle bin, or delete them outright. Keep Last protects
the newest saves in every folder, and nothing is scanned until you open the tab.

label, style, page, help, menu labels and clamped range beside its value, so a
tool that edits the file with no TouchDesigner session running can show the
same controls the settings page shows and search on more than a parameter name.
The values themselves are unchanged and are still the only thing read back in;
the description beside them is presentation, and a stale one is harmless.

longer stalls the frame: the project is scanned once instead of twice, and the
out operators inside each shortcut are collected by a few lines of Python
instead of a finder stamped per shortcut, which also makes the package 262
operators smaller. The Limit Max Depth and Max Depth settings now actually
limit the scan, and changing them no longer raises an error. The header row
has a Refresh button; refreshing by clicking the corner of the list still works.

Guided setup gains "Find my set": a few questions about how you work,
then a recommended selection with the reason beside each tool, editable
before it is applied. The questions and each tool's fit are catalog
content.

drawn by the tool itself, instead of opening a browser page. That code area is
also a button: click it and the page opens in a browser on this machine,
whether or not a code is showing. With LAN access off there is no code to
scan, so the square reads "Click to open here" and the address sits beside it,
which is the way into a remote that is serving only to this machine; the
switch to allow LAN access is in the same window. The toolbar button now says
which state it is in: struck through when it is not serving, a monitor when it
serves this machine only, and a phone with waves once a phone can reach it. It
still lights while serving. Drag that button into a network and it drops a
Select CHOP of the touch channels, already pointed at the tool. On the phone,
Control is the first tab; a parameter group such as a position or a colour is
one row of editable number fields, and opens into one slider per component,
each following the other; sliders have a thumb you can actually grab and no
longer fight the page's scrolling. Drop a component on the button to make it
the one the phone controls, or hold Alt while dropping to add it to the
component list instead. Dropping a parameter exposes the component it belongs
to. Two fixes: toggling Active could re-open the pairing window by itself, and
so could dragging off the button. The phone page now has a component browser:
an author walks the project one level at a time, exposes a component with one
tap, and removes one with the cross beside its name. And there are two links.
The full link reaches everything; the client link, a second code minted beside
it, opens only the exposed controls, with no session actions and no browsing,
and the server refuses those routes on it, where the page only hides them.
Pair the Client Link switches the pairing window and its QR code between the
two, Touch on Client Link decides whether that link gets the touch pad,
Regenerate Token now renews both codes, and the WebSocket asks for the token
on its first frame, so a neighbour on the network cannot push touches into a
rig by guessing the port.

## v3.1.4 -- 2026-09-08

- AltSelect 3.0.3 -> 3.0.4
- AutoCombine 3.0.3 -> 3.0.4
- AutoRes 3.0.3 -> 3.0.4
- BorderlessTD 3.0.4 -> 3.0.5
- ColorUI 3.0.5 -> 3.0.6
- CustomParTools 3.0.3 -> 3.0.4
- ExprHotStrings 3.0.3 -> 3.0.4
- FNS_Autosave 1.0.2 -> 1.0.3
- FNS_BeatMod 0.1.2 -> 0.1.3
- FNS_Collect 1.0.3 -> 1.0.4
- FNS_CommandKit 3.0.3 -> 3.0.4
- FNS_CommandPalette 0.1.2 -> 0.1.3
- FNS_CommandRegistry 0.1.3 -> 0.1.4
- FNS_ConfigHost 3.0.4 -> 3.0.5
- FNS_ConfigRegistry 3.0.4 -> 3.0.5
- FNS_Console 3.0.6 -> 3.0.7
- FNS_HotkeyManager 3.0.3 -> 3.0.4
- FNS_Hub 3.0.5 -> 3.0.6
- FNS_HubRegistry 3.0.4 -> 3.0.5
- FNS_MainMenuRegistry 3.0.4 -> 3.0.5
- FNS_MediaBrowser 1.0.2 -> 1.0.3
- FNS_Navbar 3.0.3 -> 3.0.4
- FNS_NavbarRegistry 3.0.4 -> 3.0.5
- FNS_OpMenu 3.0.3 -> 3.0.4
- FNS_OpMenuRegistry 3.0.4 -> 3.0.5
- FNS_PaletteRegistry 3.0.4 -> 3.0.5
- FNS_PaneTypeRegistry 3.0.3 -> 3.0.4
- FNS_PreviewPanel 0.1.2 -> 0.1.3
- FNS_Remote 1.0.2 -> 1.0.3
- FNS_TimelineRegistry 3.0.4 -> 3.0.5
- FNS_TimelineTools 3.0.6 -> 3.0.7
- FNS_Toolbar 3.0.6 -> 3.0.7
- FNS_ToolbarRegistry 3.0.4 -> 3.0.5
- FNS_Updater 3.0.12
- GlobalOutSelect 3.0.3 -> 3.0.4
- GlobalVolControl 3.0.3 -> 3.0.4
- HydroHomie 3.0.3 -> 3.0.4
- MISC 3.0.3 -> 3.0.4
- OUTPUT 3.0.3 -> 3.0.4
- OpTemplates 3.0.3 -> 3.0.4
- OpToClipboard 3.0.3 -> 3.0.4
- OpenExt 3.0.3 -> 3.0.4
- ParOPDrop 3.0.3 -> 3.0.4
- ParRandomizer 3.0.3 -> 3.0.4
- QuickCollapse 3.0.3 -> 3.0.4
- QuickMarks 3.0.3 -> 3.0.4
- QuickPane 3.0.3 -> 3.0.4
- QuickTime 3.0.3 -> 3.0.4
- ResetPLS1 3.0.3 -> 3.0.4
- SetSmoothness 3.0.3 -> 3.0.4
- SwapOps 3.0.3 -> 3.0.4
- SwitchOPs 3.0.3 -> 3.0.4
- TDXMap 1.2.0
- TDX_SearchPalette 3.0.3 -> 3.0.4
- VSCodeTools 3.0.3 -> 3.0.4
- midiMapper 3.0.3 -> 3.0.4
- oscMapper 3.0.3 -> 3.0.4
- paste_from_clipboard 3.0.2 -> 3.0.3

Every tool: every package now runs the shared export strip. Twenty-five
packages, every registry among them, had no hook for it and shipped their
authoring bookkeeping (Version Ctrl pages and tables) and the dev
project's paths in their FNS_About. The strip also writes the About
page's Owner as an expression that resolves wherever the tool lands.

## v3.1.3 -- 2026-09-08

- BorderlessTD 3.0.3 -> 3.0.4
- FNS_Toolbar 3.0.5 -> 3.0.6

## v3.1.2 -- 2026-09-08

- AltSelect 3.0.2 -> 3.0.3
- AutoCombine 3.0.2 -> 3.0.3
- AutoRes 3.0.2 -> 3.0.3
- BorderlessTD 3.0.2 -> 3.0.3
- ColorUI 3.0.4 -> 3.0.5
- CustomParTools 3.0.2 -> 3.0.3 -- The ExtUtils master's parameter watcher resolves its owner structurally, and CustomParHelper no longer overwrites that expression with a constant at init.
- ExprHotStrings 3.0.2 -> 3.0.3
- FNS_Autosave 1.0.1 -> 1.0.2
- FNS_BeatMod 0.1.1 -> 0.1.2
- FNS_Collect 1.0.2 -> 1.0.3
- FNS_CommandKit 3.0.2 -> 3.0.3
- FNS_CommandPalette 0.1.1 -> 0.1.2
- FNS_CommandRegistry 0.1.2 -> 0.1.3
- FNS_ConfigHost 3.0.3 -> 3.0.4
- FNS_ConfigRegistry 3.0.3 -> 3.0.4
- FNS_Console 3.0.5 -> 3.0.6
- FNS_HotkeyManager 3.0.2 -> 3.0.3
- FNS_Hub 3.0.4 -> 3.0.5
- FNS_HubRegistry 3.0.3 -> 3.0.4
- FNS_MainMenuRegistry 3.0.3 -> 3.0.4
- FNS_MediaBrowser 1.0.1 -> 1.0.2
- FNS_Navbar 3.0.2 -> 3.0.3
- FNS_NavbarRegistry 3.0.3 -> 3.0.4
- FNS_OpMenu 3.0.2 -> 3.0.3
- FNS_OpMenuRegistry 3.0.3 -> 3.0.4
- FNS_PaletteRegistry 3.0.3 -> 3.0.4
- FNS_PaneTypeRegistry 3.0.2 -> 3.0.3
- FNS_PreviewPanel 0.1.1 -> 0.1.2
- FNS_Remote 1.0.1 -> 1.0.2
- FNS_TimelineRegistry 3.0.3 -> 3.0.4
- FNS_TimelineTools 3.0.5 -> 3.0.6
- FNS_Toolbar 3.0.4 -> 3.0.5
- FNS_ToolbarRegistry 3.0.3 -> 3.0.4
- FNS_Updater 3.0.11
- GlobalOutSelect 3.0.2 -> 3.0.3
- GlobalVolControl 3.0.2 -> 3.0.3
- HydroHomie 3.0.2 -> 3.0.3
- MISC 3.0.2 -> 3.0.3
- OUTPUT 3.0.2 -> 3.0.3
- OpTemplates 3.0.2 -> 3.0.3
- OpToClipboard 3.0.2 -> 3.0.3
- OpenExt 3.0.2 -> 3.0.3
- ParOPDrop 3.0.2 -> 3.0.3
- ParRandomizer 3.0.2 -> 3.0.3
- QuickCollapse 3.0.2 -> 3.0.3
- QuickMarks 3.0.2 -> 3.0.3
- QuickPane 3.0.2 -> 3.0.3
- QuickTime 3.0.2 -> 3.0.3
- ResetPLS1 3.0.2 -> 3.0.3
- SetSmoothness 3.0.2 -> 3.0.3
- SwapOps 3.0.2 -> 3.0.3
- SwitchOPs 3.0.2 -> 3.0.3
- TDXMap 1.2.0
- TDX_SearchPalette 3.0.2 -> 3.0.3
- VSCodeTools 3.0.2 -> 3.0.3
- midiMapper 3.0.2 -> 3.0.3
- oscMapper 3.0.2 -> 3.0.3
- paste_from_clipboard 3.0.1 -> 3.0.2

Every tool: the shared ExtUtils base pointed its parameter watcher at an
absolute path into the dev project, so an install without CustomParTools
raised an error on every tool carrying one and could miss parameter
changes. It now resolves to the tool it sits in. Found on the first fresh
install of the beta.

## v3.1.1 -- 2026-09-08

- AltSelect 3.0.1 -> 3.0.2
- AutoCombine 3.0.1 -> 3.0.2
- AutoRes 3.0.1 -> 3.0.2
- BorderlessTD 3.0.1 -> 3.0.2
- ColorUI 3.0.3 -> 3.0.4
- CustomParTools 3.0.1 -> 3.0.2 -- Promoting while hovering a component of a vector or colour parameter promotes the whole group in one undo step. For extension authors, parameters can be declared as fields on the class and callbacks as decorators, with no base class required.
- ExprHotStrings 3.0.1 -> 3.0.2
- FNS_Autosave 1.0.0 -> 1.0.1
- FNS_BeatMod 0.1.0 -> 0.1.1 -- New. Beat-synced modulation of any parameter from the timeline tempo. Three kinds of modulator, a wave on the beat, a channel of any CHOP, or a recorded gesture, each built beside its target and gliding in through Tweener. Hold a kind in the menu for an XY pad, and manage every modulator in the project from the Hub tab.
- FNS_Collect 1.0.1 -> 1.0.2
- FNS_CommandKit 3.0.1 -> 3.0.2
- FNS_CommandPalette 0.1.0 -> 0.1.1 -- New. A command palette inside TouchDesigner over the command registry. Type to run any tool's commands, navigate the network with / . and .., walk parameters, keep favourites and history, and curate what shows from the Hub's Commands tab. Favourites and hidden commands are shared with the TDX launcher.
- FNS_CommandRegistry 0.1.1 -> 0.1.2 -- New as a store package. The registry the palette and the TDX launcher both read, shipped here for installs without the launcher, with TouchDesigner's own built-in commands inside it. The launcher carries the same artifact, so both loaded together resolve to one set.
- FNS_ConfigHost 3.0.2 -> 3.0.3
- FNS_ConfigRegistry 3.0.2 -> 3.0.3 -- The Config Scope setting on every host guards against a project with no toolkit root, and a host missing the setting gets it back on init.
- FNS_Console 3.0.4 -> 3.0.5
- FNS_HotkeyManager 3.0.1 -> 3.0.2 -- Conflict checks fold Cmd onto Ctrl so a Mac binding is compared against the same key, and a rebind the manager refuses now says so.
- FNS_Hub 3.0.3 -> 3.0.4
- FNS_HubRegistry 3.0.2 -> 3.0.3
- FNS_MainMenuRegistry 3.0.2 -> 3.0.3
- FNS_MediaBrowser 1.0.0 -> 1.0.1
- FNS_Navbar 3.0.1 -> 3.0.2
- FNS_NavbarRegistry 3.0.2 -> 3.0.3
- FNS_OpMenu 3.0.1 -> 3.0.2
- FNS_OpMenuRegistry 3.0.2 -> 3.0.3
- FNS_PaletteRegistry 3.0.2 -> 3.0.3
- FNS_PaneTypeRegistry 3.0.1 -> 3.0.2
- FNS_PreviewPanel 0.1.0 -> 0.1.1 -- New. A pane type that shows whatever you drop on it: TOPs as images, geometry through an orbitable camera, panels as themselves, POPs as points with their attributes one click away, and a POP as a live table or in its own viewer window.
- FNS_Remote 1.0.0 -> 1.0.1
- FNS_TimelineRegistry 3.0.2 -> 3.0.3
- FNS_TimelineTools 3.0.4 -> 3.0.5 -- Keyframer. Key any operators' parameters into an Animation COMP at the current frame from a KF / KEY / UNKEY / DRIVE strip in the Animation editor's graph heading. Drop operators, parameters or groups on the strip to add channels; the editor's channel list is what gets keyed and driven.
- FNS_Toolbar 3.0.3 -> 3.0.4
- FNS_ToolbarRegistry 3.0.2 -> 3.0.3
- FNS_Updater 3.0.9 -> 3.0.10
- GlobalOutSelect 3.0.1 -> 3.0.2
- GlobalVolControl 3.0.1 -> 3.0.2
- HydroHomie 3.0.1 -> 3.0.2
- MISC 3.0.1 -> 3.0.2
- OUTPUT 3.0.1 -> 3.0.2
- OpTemplates 3.0.1 -> 3.0.2
- OpToClipboard 3.0.1 -> 3.0.2
- OpenExt 3.0.1 -> 3.0.2
- ParOPDrop 3.0.1 -> 3.0.2 -- Dropping a CHOP, a channel or a DAT onto a parameter creates its Execute DAT, watching that channel or all of them. Dropping a vector or colour group expands to its members.
- ParRandomizer 3.0.1 -> 3.0.2
- QuickCollapse 3.0.1 -> 3.0.2
- QuickMarks 3.0.1 -> 3.0.2 -- Marks live on a parameter sequence and can be named. Retrieve is a single action, auto-names are unique, and the palette commands reach the same marks the hotkeys set.
- QuickPane 3.0.1 -> 3.0.2
- QuickTime 3.0.1 -> 3.0.2
- ResetPLS1 3.0.1 -> 3.0.2
- SetSmoothness 3.0.1 -> 3.0.2
- SwapOps 3.0.1 -> 3.0.2 -- Swapping preserves connector indices, including COMP connectors, so a growing multi-input keeps its slot order and wired COMPs keep their vertical wiring. Inputs that do not fit the other operator stay where they were instead of being dropped.
- SwitchOPs 3.0.1 -> 3.0.2
- TDXMap 1.2.0
- TDX_SearchPalette 3.0.1 -> 3.0.2
- VSCodeTools 3.0.1 -> 3.0.2
- midiMapper 3.0.1 -> 3.0.2
- oscMapper 3.0.1 -> 3.0.2
- paste_from_clipboard 3.0.0 -> 3.0.1

This is a beta. Every tool has been used in the dev project daily, and
this is the first release where strangers install it. Four packages are
new, one is mirrored from its own site, and every tool carries a fleet
change to the shared ExtUtils base. If something wedges, especially a
download that sits at "0 done, 1 to go", leave it as it is and report
it with the Textport contents.

Listings show the public name now: the package FNS_BeatMod appears as
BeatMod in the picker, the console and the site. Shortcuts, file names
and COMP names keep the prefix.

Every tool: the shared ExtUtils base heals its watchers when a watched
operator is renamed or moved, and a pasted or copied tool initialises
its extension on its own instead of waiting for something to cook it.
Stub generation left ExtUtils, which is about 1150 fewer operators in a
full install. Every quick-launch command carries help text and says
what it acts on.

TDXMap: Mirrored from its own release at version 1.2.0. MIDI controller mapping with a live web UI. It updates itself; the toolkit updater reports it as self-managed and leaves it alone.

## v3.0.14 -- 2026-08-31

- FNS_Collect 1.0.0 -> 1.0.1
- FNS_MediaBrowser 1.0.0

## v3.0.13 -- 2026-08-31

- FNS_Autosave 1.0.0
- FNS_Collect 1.0.0
- FNS_Media 1.0.0
- FNS_Remote 1.0.0
- FNS_Updater 3.0.7 -> 3.0.8

## v3.0.12 -- 2026-08-30

- FNS_TimelineTools 3.0.3 -> 3.0.4
- FNS_ToolbarRegistry 3.0.1 -> 3.0.2
- paste_from_clipboard 3.0.0

## v3.0.11 -- 2026-08-30

- ColorUI 3.0.2 -> 3.0.3
- FNS_ConfigHost 3.0.1 -> 3.0.2
- FNS_ConfigRegistry 3.0.1 -> 3.0.2
- FNS_Console 3.0.3 -> 3.0.4
- FNS_Hub 3.0.2 -> 3.0.3
- FNS_HubRegistry 3.0.1 -> 3.0.2
- FNS_MainMenuRegistry 3.0.1 -> 3.0.2
- FNS_NavbarRegistry 3.0.1 -> 3.0.2
- FNS_OpMenuRegistry 3.0.1 -> 3.0.2
- FNS_PaletteRegistry 3.0.1 -> 3.0.2
- FNS_TimelineRegistry 3.0.1 -> 3.0.2
- FNS_Toolbar 3.0.2 -> 3.0.3
- FNS_Updater 3.0.6 -> 3.0.7
- paste_from_clipboard 1.0.6 -> 1.0.7

## v3.0.10 -- 2026-08-30

- FNS_Console 3.0.2 -> 3.0.3
- FNS_Hub 3.0.2
- FNS_Toolbar 3.0.1 -> 3.0.2
- FNS_Updater 3.0.5 -> 3.0.6
- paste_from_clipboard 1.0.6

## v3.0.9 -- 2026-08-30

## v3.0.8 -- 2026-08-30

- FNS_Updater 3.0.4 -> 3.0.5

Downloads can no longer damage the store: artifacts land in a staging
file and only replace the store copy after their checksum passes, so a
failed or refused fetch leaves the previous good bytes untouched. A
gated download refused by the gate now says so honestly (instead of
reading as a checksum failure) and drops the stale download token, so
the next attempt asks for a fresh one.

The picker now finishes what the /get page started: if you copied an
install with a Plus tool checked, the pick completes on its own the
moment your account covers it -- whether you were already signed in on
this machine or sign in when prompted. A short countdown lets you
cancel; anything your tier does not cover stays visible with its
honest label instead of installing.

Signing in anywhere on the machine now counts everywhere: a session
that existed before shared sign-in shipped is published for other
Function Store products to adopt the first time it is read.

## v3.0.7 -- 2026-08-30

- FNS_Updater 3.0.3 -> 3.0.4 -- one sign-in now serves the whole machine. Signing in to

any FNS product (the toolkit, the TDX launcher) shares the session --
clicking Sign in when the machine is already signed in adopts it
instantly with no browser trip, and signing out anywhere signs the
machine out everywhere. Entitlement refusals, downloads and rechecks
are unchanged.

## v3.0.6 -- 2026-08-29

- FNS_Console 3.0.1 -> 3.0.2 -- the console panel renders reliably -- opening it now holds

the shared browser's render on while its server lives, instead of the
render optimizations switching it off one frame later.

The install rails ride along fixed: the one-line installer lands the
toolkit at the project root, opens the picker by itself when a Plus
tool was picked, Pick Tools keeps its panel rendered, and Open
Settings reports what it actually did.

## v3.0.5 -- 2026-08-29

- FNS_Updater 3.0.2 -> 3.0.3 -- sign-in now completes end to end -- the loopback listener

reads its parameters, gate responses route to their handlers, and
requests actually carry their bearer token. Refusals name the tier a
package unlocks at (and the lifetime key where one exists), a dead
session clears itself and re-offers the way back in, a Patreon outage
keeps a supporter entitled, and the picker narrates sign-in and
recheck outcomes and refreshes itself.

## v3.0.4 -- 2026-08-29

- AltSelect 3.0.0 -> 3.0.1
- AutoCombine 3.0.0 -> 3.0.1
- AutoRes 3.0.0 -> 3.0.1
- BorderlessTD 3.0.0 -> 3.0.1
- ColorUI 3.0.0 -> 3.0.1
- CustomParTools 3.0.0 -> 3.0.1
- ExprHotStrings 3.0.0 -> 3.0.1
- FNS_CommandKit 3.0.0 -> 3.0.1
- FNS_ConfigHost 3.0.0 -> 3.0.1
- FNS_ConfigRegistry 3.0.0 -> 3.0.1 -- the settings page is reachable at last -- the web
- FNS_Console 3.0.0 -> 3.0.1
- FNS_HotkeyManager 3.0.0 -> 3.0.1
- FNS_Hub 3.0.0 -> 3.0.1
- FNS_HubRegistry 3.0.0 -> 3.0.1
- FNS_MainMenuRegistry 3.0.0 -> 3.0.1
- FNS_Navbar 3.0.0 -> 3.0.1
- FNS_NavbarRegistry 3.0.0 -> 3.0.1
- FNS_OpMenu 3.0.0 -> 3.0.1
- FNS_OpMenuRegistry 3.0.0 -> 3.0.1
- FNS_PaletteRegistry 3.0.0 -> 3.0.1
- FNS_PaneTypeRegistry 3.0.0 -> 3.0.1
- FNS_TimelineRegistry 3.0.0 -> 3.0.1
- FNS_TimelineTools 3.0.2 -> 3.0.3
- FNS_Toolbar 3.0.0 -> 3.0.1
- FNS_ToolbarRegistry 3.0.0 -> 3.0.1
- FNS_Updater 3.0.1 -> 3.0.2
- GlobalOutSelect 3.0.0 -> 3.0.1
- GlobalVolControl 3.0.0 -> 3.0.1
- HydroHomie 3.0.0 -> 3.0.1
- MISC 3.0.0 -> 3.0.1
- OUTPUT 3.0.0 -> 3.0.1
- OpTemplates 3.0.0 -> 3.0.1
- OpToClipboard 3.0.0 -> 3.0.1
- OpenExt 3.0.0 -> 3.0.1
- ParOPDrop 3.0.0 -> 3.0.1
- ParRandomizer 3.0.0 -> 3.0.1
- QuickCollapse 3.0.0 -> 3.0.1
- QuickMarks 3.0.0 -> 3.0.1
- QuickPane 3.0.0 -> 3.0.1
- QuickTime 3.0.0 -> 3.0.1
- ResetPLS1 3.0.0 -> 3.0.1
- SetSmoothness 3.0.0 -> 3.0.1
- SwapOps 3.0.0 -> 3.0.1
- SwitchOPs 3.0.0 -> 3.0.1
- TDX_SearchPalette 3.0.0 -> 3.0.1
- VSCodeTools 3.0.0 -> 3.0.1
- midiMapper 3.0.0 -> 3.0.1
- oscMapper 3.0.0 -> 3.0.1
- paste_from_clipboard 1.0.0 -> 1.0.6

Documentation, and the settings page you could not reach.

Every package's docs were checked against what its code actually does
rather than what the old wiki said. Twenty-six were wrong: hotkeys that
had drifted to different modifiers, features nobody had written down,
paths still naming the pre-3.0 layout, and a few descriptions that
described the wrong behaviour entirely. ClearPars turned out to have
merged into CustomParTools during the redesign and is gone as a separate
package; its docs live there now.

FNS_ConfigRegistry ships a settings page -- every installed tool's
parameters on one page in your browser, served from inside TouchDesigner
on 127.0.0.1 and shut down again when you stop looking at it. It has been
in the code for a while, unreachable: the web server op it looks for was
never created. It builds itself on demand now, and the toolkit root grew
an **Open Settings** parameter to reach it, alongside Pick Tools and Open
Installer.

The one-drop bundle is now built as a copy of the development root with
the developer-only parts removed, rather than assembled separately, so the
two cannot drift apart in what they offer at the top level.

server that serves it is created on demand instead of being expected to
already exist, and a promoted copy missing the page pulls it from the
master rather than failing.

## Unreleased

- QuickParCustom -- **folded into CustomParTools** as a child, joining ClearPars, QuickExt, QuickParent and iopPromoter. It always depended on CustomParTools (it promoted through the `FNS_CPP` global), so on its own its hotkeys could not promote. Your settings carry over -- the config section keeps its name -- and the **Active** toggle still turns it off. Two notes: a custom rebinding of its hotkeys resets to default once, and the `QuickParCustom#toggleactive` command is now `CustomParTools/QuickParCustom#toggleactive`.
- QuickParCustom -- `shift+alt+x` (promote with an Expression) is now a real, listed hotkey. It was a derived expression FNS_HotkeyManager could not see, so it was never rebindable and never checked for conflicts.
- MY_HOTKEYS -- **retired.** Its four stock-TouchDesigner shortcuts (open parameters / open the COMP editor, for the selected operator or the current network's COMP) and their four quick-launch commands moved into CustomParTools; `ctrl+shift+f` moved into TDX_SearchPalette, and `ctrl+0` had already moved into ResetPLS1. Nothing was lost, but the four command ids are now owned by CustomParTools, so launcher history and presets keyed on `MY_HOTKEYS#<id>` need re-pointing once.
- CustomParTools -- gains those four shortcuts, as hotkeys and as palette commands sharing one implementation.
- FNS_Hub 0.2.0 -- New core package: the FNS button in the main-menu bar is now the one stop shop. Left-click opens a window with the Toolbar, Navbar, MainMenu and OpMenu configurators as tabs plus the console and the larger tool UIs; right-click jumps to any of them; drop a panel COMP on the button to register it into a surface. Two tab-bar styles (wrapping rows, or the classic single strip), drag to reorder, no close buttons (hidden tabs come back from the right-click menu). Tab order and the last tab roam with your settings. The OpMenu tab is new: reorder what tools contribute to the OP Create dialog, or switch a contribution off without uninstalling its tool.
- FNS_HubRegistry 0.1.0 -- New core registry behind the hub's tab bar: any tool can contribute a native panel, a viewer or a parameter page as a tab by carrying a host, and it appears the moment the tool exists.
- FNS_Toolbar 1.1.0 -- The Configurator moved into the hub; the gear button is gone from the bar. Drop-to-register, which had silently stopped working after the v3 rename, works again from the FNS button.
- FNS_Navbar 1.1.0 -- Same: the Configurator is the hub's Navbar tab, no gear on the pane bars.
- FNS_MainMenu -- Removed. It carried nothing but the Main Menu configurator, which is the hub's MainMenu tab now; its quick-launch command moved to FNS_Hub.
- FNS_Console 0.2.0 -- Opens inside the hub's Console tab when the hub is installed (the root's web browser viewer is the fallback); its browser only renders while that tab is shown.
- tools_ui -- Removed. The `Fx` toolbar panel's tabs live in FNS_Hub now, with the same right-click-for-parameters gesture and drag-to-reorder; the hub's tab order and last tab roam with your settings as before.
- oscMapper 1.1.0, ExprHotStrings 1.2.0, GlobalOutSelect 1.1.0, FNS_OpMenu 1.1.0, midiMapper 1.1.0, ColorUI 1.2.0 -- Each carries an FNS_Hub tab host instead of the old UI Tab parameters; the tab appears the moment the tool is installed, and *Shown in Hub* on the tool's Registry page is the new way to hide it. ColorUI's palette editor renders while its hub tab is shown and goes dark the moment you leave it, so the browser never runs for nobody.

## v3.0.1 -- 2026-08-16

- ColorUI 1.0.2 -- Its tab in the tools panel is now the palette editor itself, with families, colours and search inline, instead of a button that opened a parameter window.
- ExprHotStrings 1.1.1 -- Contributes its tools panel tab through the new UI Tab parameters, so the tab travels with the package and can be reordered or hidden.
- FNS_OpMenu 1.0.3 -- Carries the search-keywords tab in the tools panel now. It used to be loose glue sitting in the toolkit root that no package owned, which meant it simply went missing unless you had installed everything.
- FNS_Updater 1.0.10 -- Fixed a dead reference to a component that left the toolkit long ago, which made one node inside the updater throw an error on every cook.
- GlobalOutSelect 1.0.1 -- Contributes its tools panel tab through the new UI Tab parameters, and still refreshes itself whenever the tab is shown.
- MY_HOTKEYS 1.0.1 -- The palette search hotkey now checks that TDX_SearchPalette is actually installed rather than doing nothing when it is not.
- TDX_SearchPalette 1.1.0 -- New package, vendored from Yea Chen's TD-SearchPalette: a search field inside TouchDesigner's palette browser. Matching is case-insensitive and looks anywhere in the name rather than only at the start, several words narrow the result together, a word containing a slash matches the palette folder instead (`gen/ noise`), and numbered copies of one component collapse to the most recently modified. The last two are toggles on the package, and `ctrl+shift+f` jumps straight to the field when MY_HOTKEYS is installed.
- midiMapper 1.0.1 -- Contributes its tools panel tab through the new UI Tab parameters, so the tab travels with the package and can be reordered or hidden.
- oscMapper 1.0.1 -- Contributes its tools panel tab through the new UI Tab parameters, so the tab travels with the package and can be reordered or hidden.
- tools_ui 1.1.0 -- The tabbed panel builds itself from the tools you actually have installed instead of a fixed list, so a partial install no longer shows tabs that lead nowhere, and the panel refreshes itself on start and every time it opens. Drag the tabs to reorder them, close one with its X to hide it (turn it back on from that tool's own UI Tab parameters), and both the order and the tab you were last on come back with your settings.

Installing from the website is now one line. Pick the tools you want on
the site, press Copy install script, and paste the single line into the
Textport: it fetches the bootstrap and your selection straight from this
release, checks every hash before writing anything to disk, and installs.

Partial installs are the theme of this drop. Tools that reach for each
other now look first and stay quiet when the other side is absent, so a
subset behaves like a deliberate configuration rather than a broken one.
Packages have also stopped assuming the toolkit root is there at all --
each one resolves through its own global shortcut, so a single dropped
tox works standalone.

Every package page was re-read against the components themselves.
Twenty-six of forty-six had something stale -- paths left over from the
rename, wrong key combinations, descriptions of how things worked before
the redesign -- and the worst of them were rewritten outright. ClearPars
lost its own page, because it lives inside CustomParTools now.

Downloads are a little leaner too: artifacts had been carrying log data
baked in from an old project, and that no longer rides along.

## v3.0.0 -- 2026-08-16

- AltSelect 1.0.1
- AutoCombine 1.0.1
- AutoRes 1.0.4
- BorderlessTD 1.0.1
- ColorUI 1.0.1
- CustomParTools 1.0.1
- ExprHotStrings 1.1.0
- FNS_ConfigRegistry 1.0.0
- FNS_HotkeyManager 1.0.1
- FNS_MainMenu 1.0.1
- FNS_MainMenuRegistry 1.0.0
- FNS_Navbar 1.0.3
- FNS_NavbarRegistry 1.0.0
- FNS_OpMenu 1.0.2
- FNS_OpMenuRegistry 1.0.0
- FNS_PaneTypeRegistry 1.0.0
- FNS_Toolbar 1.0.5
- FNS_ToolbarRegistry 1.0.0
- FNS_Updater 1.0.9
- GlobalOutSelect 1.0.0
- GlobalVolControl 1.0.0
- HydroHomie 1.0.1
- MISC 1.0.0
- MY_HOTKEYS 1.0.0
- OUTPUT 1.0.0
- OpTemplates 1.0.0
- OpToClipboard 1.0.4
- OpenExt 1.0.1
- ParOPDrop 1.0.1
- ParRandomizer 1.0.1
- QuickCollapse 1.0.1
- QuickMarks 1.0.0
- QuickPane 1.0.5
- QuickParCustom 1.0.0
- QuickTime 1.0.0
- ResetPLS1 1.0.1
- SetSmoothness 1.0.0
- SwapOps 1.0.1
- SwitchOPs 1.0.1
- VSCodeTools 1.0.0
- midiMapper 1.0.0
- oscMapper 1.0.0
- paste_from_clipboard 1.0.5
- tools_ui 1.0.0

FNSTools 3.0 -- the toolkit takes its name, and core becomes the raw
registries. The whole toolkit is renamed FNSTools; the six registry
masters (FNS_ConfigRegistry, FNS_ToolbarRegistry, FNS_NavbarRegistry,
FNS_MainMenuRegistry, FNS_OpMenuRegistry, FNS_PaneTypeRegistry) ship as
their own core packages, promoted to /sys under those names -- raw,
standalone and cloneable, so the toolkit can be extended with the same
machinery it is built on. FNS_Updater (renamed from UPDATER) is the one
non-registry core. The former surface packages -- toolbar, navbar,
main-menu and OP-menu extras -- are ordinary optional tools now, and a
tool's requirements are exactly the registries it hosts. Full design
record: docs/FNSToolsRedesign.md. No migration from pre-3.0 installs;
this is the first public shape of the toolkit.

## v2.12.19 -- 2026-08-15

- UPDATER 1.0.8 -> 1.0.9 -- RefreshStore(names) scopes the artifact fetch -- a list fetches just those packages, an empty list is manifest-only, None still mirrors the whole release.

The picker downloads only what you pick. A lightweight bootstrap no
longer mirrors the whole release before showing the catalog: the page
appears after a manifest-only fetch (seconds), the plan says how many MB
your selection needs, and install fetches exactly those packages with
live progress. The full-mirror Refresh Store pulse remains for offline
installs and shared bindings.

## v2.12.18 -- 2026-08-15

- UPDATER 1.0.7 -> 1.0.8 -- dropped the dangling internal-op shortcuts to TDAsyncIO and github_remote (legacy of the pre-bucket update flow) that flagged every fresh drop with invalid-path warnings.

The bootstrap installer now targets whatever container it ships in --
TD numbers a second drop into an occupied project, and matching the
parent by literal name sent that installer at the other copy's root.
The plan status also names an existing toolkit root when installing
somewhere else.

## v2.12.17 -- 2026-08-15

- FNS_Config 1.1.2
- FNS_MainMenu 1.0.1
- FNS_Navbar 1.0.0 -> 1.0.3 -- the drag-drop hijack guards against panenav not existing yet on first load into a bare project, retrying briefly instead of erroring the install.
- FNS_OpMenu 1.0.0 -> 1.0.2
- FNS_Toolbar 1.0.3 -> 1.0.5
- UPDATER 1.0.3 -> 1.0.7 -- restored ShowChangelogAfterUpdate (execute1 still called it; it was dropped in the bucket rework) -- the flag is set by a successful update pass and the notes come from the store manifest, shown once on the next open.

Registry cores: the /sys global no longer inherits the master's clone
binding at promotion -- the global owns itself, so an update destroying
and reloading the in-project master cannot dangle it.

## v2.12.16 -- 2026-08-14

- PaneTypeRegistry 1.0.0 -- now ships as a core package -- the panebar pane-type registry master, previously only distributed with PreviewPanel, joins the toolkit so tools can host into it and `requires` can point at it. The package IS the master (no FNS_ wrapper), keeping the standalone identity it already has.

## v2.12.15 -- 2026-08-14

- UPDATER 1.0.5 -> 1.0.6 -- after an update pass, packages still flagging errors get one recook against the settled network. Clears the stale "operator has been deleted" flags left on early-updated packages whose registry master was replaced later in the same pass.

## v2.12.14 -- 2026-08-14

- UPDATER 1.0.4 -> 1.0.5 -- embedded packages now update on the installer's own rail -- destroy the old COMP and loadTox the store artifact live -- instead of grafting a staged copy in with replaceOp. The graft copy/destroys extension-bearing COMPs, which wedged or crashed TD during multi-package passes; destroy+loadTox is the path every install has always taken. Self-update follows the same pattern. Settings are unaffected (they live in the palette config JSON and re-apply on re-register).

## v2.12.13 -- 2026-08-14

- UPDATER 1.0.3 -> 1.0.4 -- the first package replacement of an update pass now runs on the main thread like the rest, instead of inline on the downloader's callback thread. Off-main replacement wedged TD inside registry surface injection (navbar widget copy) with unbounded memory growth when updates were driven headlessly.

## v2.12.12 -- 2026-08-14

- AltSelect 1.0.1 -> 1.0.2
- AutoCombine 1.0.1 -> 1.0.2
- AutoRes 1.0.4 -> 1.0.5
- BorderlessTD 1.0.1 -> 1.0.2
- ColorUI 1.0.1 -> 1.0.2
- CustomParTools 1.0.1 -> 1.0.2
- ExprHotStrings 1.1.0 -> 1.1.1
- FNS_HotkeyManager 1.0.1 -> 1.0.2 -- extension init no longer requires the FNS shortcut; searchRoot is the containing toolkit root.
- FNS_OpMenu 1.0.0 -> 1.0.1 -- IOFilter's switch is the new Iofilteractive toggle on the package, not a root parameter.
- FNS_Toolbar 1.0.3 -> 1.0.4
- HydroHomie 1.0.1 -> 1.0.2
- OpToClipboard 1.0.3 -> 1.0.4
- ParOPDrop 1.0.1 -> 1.0.2
- ParRandomizer 1.0.1 -> 1.0.2
- QuickCollapse 1.0.1 -> 1.0.2
- QuickMarks 1.0.2 -> 1.0.3
- QuickPane 1.0.4 -> 1.0.5
- QuickParCustom 1.0.1 -> 1.0.2
- ResetPLS1 1.0.1 -> 1.0.2
- SwapOps 1.0.1 -> 1.0.2
- SwitchOPs 1.0.1 -> 1.0.2
- paste_from_clipboard 1.0.4 -> 1.0.5

Tools own their parameters now. Every parent.FNS.par reference across the
toolkit -- 31 pars in 20 packages, plus the hotkey scan root and the
IOFilter gate -- is gone: each par is a plain tool-level value, the hotkey
manager anchors to whatever container it is installed in, and IOFilter
grew its own toggle.

## v2.12.11 -- 2026-08-14

- OpToClipboard 1.0.3 -- Active no longer hard-requires the dev root's par surface -- guarded parent.FNS lookup with a sane default, so a bare install works.
- QuickPane 1.0.4 -- Active no longer hard-requires the dev root's par surface -- guarded parent.FNS lookup with a sane default, so a bare install works.
- paste_from_clipboard 1.0.4 -- Folderpath falls back to Assets/clipboard_images when no root par exists, instead of erroring.

First release with the reworked bootstrap rail: the one-drop root now
ships the FNS global/parent shortcuts, the installer recooks a package
once before counting an install-time error, and the served configurator
shuts its web server down after a successful install.

## v2.12.10 -- 2026-08-14

- FNS_Navbar 1.0.1 -> 1.0.2

## v2.12.9 -- 2026-08-14

- FNS_Navbar 1.0.0 -> 1.0.1

