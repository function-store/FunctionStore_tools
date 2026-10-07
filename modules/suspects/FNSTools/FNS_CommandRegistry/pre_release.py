# Embody/PI pre_release hook -- runs on the STAGED COPY in /sys/quiet before the
# portable tox is written (extensions NOT initialized there; direct par/storage
# edits only). args[0] = resolved save path.
#
# PI's own scrub already strips pi tags, file bindings and externaltox from the
# copy. This hook removes the one thing only this package knows about:
#
#   developer annotations. TDAnnotate internals do not survive a different
#   TDAnnotate version: the five documentation annotations shipped in the
#   0.1.0 artifact raised "'td.annotateCOMP' object has no attribute
#   'Editing'" on the launcher's import and cascaded past 5,800 errors
#   (2026-09-02). The master carries none since the 0.1.1 re-release, and this
#   hook keeps any future ones out of the artifact regardless.
#
# Nothing here evaluates a parameter: evaluating a dangling reference on the
# staged copy aborts the whole hook run at a level no `except` here can catch.

_t = me.parent()

for _a in _t.findChildren(type=annotateCOMP, maxDepth=99, includeUtility=True):
	try:
		_a.destroy()
	except Exception:
		pass

# The generic FNS strip runs LAST, after this package's own scrub: root-panel
# binds frozen, web servers pinned to loopback, vc_data / Version Ctrl pages
# gone, stubser logs cleared, console exposure dormant, FNS_About.Owner an
# expression. Every package runs it; the 25 that did not shipped their PI
# bookkeeping and dev-project paths in v3.1.3 (packaging/pre_release_common.py).
exec(open('packaging/pre_release_common.py').read())
