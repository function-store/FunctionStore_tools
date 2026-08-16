<!--
Release notes for the NEXT publish. Write prose about what changed and
why -- do NOT write version numbers or the release label here: the
bumped packages and their version transitions are stamped automatically
at publish time (you see the exact numbers in the confirm dialog).

This file is CLEARED after each successful publish; your text becomes
that release's entry in packaging/CHANGELOG.md and ships inside the
release's manifest. An empty file is fine -- the entry then carries just
the auto-generated package list.
-->

tools_ui: The tabbed panel builds itself from the tools you actually have installed instead of a fixed list, so a partial install no longer shows tabs that lead nowhere, and the panel refreshes itself on start and every time it opens. Drag the tabs to reorder them, close one with its X to hide it (turn it back on from that tool's own UI Tab parameters), and both the order and the tab you were last on come back with your settings.
TDX_SearchPalette: New package, vendored from Yea Chen's TD-SearchPalette: a search field inside TouchDesigner's palette browser. Matching is case-insensitive and looks anywhere in the name rather than only at the start, several words narrow the result together, a word containing a slash matches the palette folder instead (`gen/ noise`), and numbered copies of one component collapse to the most recently modified. The last two are toggles on the package, and `ctrl+shift+f` jumps straight to the field when MY_HOTKEYS is installed.
ColorUI: Its tab in the tools panel is now the palette editor itself, with families, colours and search inline, instead of a button that opened a parameter window.
FNS_OpMenu: Carries the search-keywords tab in the tools panel now. It used to be loose glue sitting in the toolkit root that no package owned, which meant it simply went missing unless you had installed everything.
oscMapper: Contributes its tools panel tab through the new UI Tab parameters, so the tab travels with the package and can be reordered or hidden.
midiMapper: Contributes its tools panel tab through the new UI Tab parameters, so the tab travels with the package and can be reordered or hidden.
ExprHotStrings: Contributes its tools panel tab through the new UI Tab parameters, so the tab travels with the package and can be reordered or hidden.
GlobalOutSelect: Contributes its tools panel tab through the new UI Tab parameters, and still refreshes itself whenever the tab is shown.
MY_HOTKEYS: The palette search hotkey now checks that TDX_SearchPalette is actually installed rather than doing nothing when it is not.
FNS_Updater: Fixed a dead reference to a component that left the toolkit long ago, which made one node inside the updater throw an error on every cook.

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
