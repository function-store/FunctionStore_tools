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
