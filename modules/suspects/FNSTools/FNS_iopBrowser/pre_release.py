# Embody/PI pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/table edits only). args[0] = resolved save path.
#
# This package shipped WITHOUT a hook until 2026-09-18, so its artifact
# carried the authoring apparatus: the Version Ctrl page and the vc_data
# tables that describe this checkout's save history rather than the tool. It
# also missed the loopback web-server rule, the console-ships-dormant rule,
# the FNS_About.Owner expression and the first-page rule. packaging/CREATING.md
# never mentioned the hook, which is why a package made by the book had none.
#
# Nothing tool-specific here yet: the generic strip is the whole job. Add
# package-specific work BELOW this line, never above it.
exec(open('packaging/pre_release_common.py').read())
