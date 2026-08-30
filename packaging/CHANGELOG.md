# FNS tools changelog

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

