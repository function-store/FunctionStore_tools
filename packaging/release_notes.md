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

FNS_ConfigRegistry: the settings page is reachable at last -- the web
server that serves it is created on demand instead of being expected to
already exist, and a promoted copy missing the page pulls it from the
master rather than failing.
