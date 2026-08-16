# FNS tools changelog

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

