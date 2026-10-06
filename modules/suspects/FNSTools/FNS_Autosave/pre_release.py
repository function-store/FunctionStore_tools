# Embody pre_release hook for STANDALONE exports of FNS_Autosave
# (Releaseall / ExportPortableTox run it on the staged copy; when the whole
# utility is exported, the utility's own pre_release sanitizes this COMP
# instead -- Embody ignores nested hooks). Reset volatile state so a
# released tox never carries a save log from the dev project, and never
# ships with autosave already armed.

# Settings that BIND UP to the companion (op('..')) when nested. Shipped
# standalone that bind dangles in whatever COMP the user drops this into,
# so bake each one to a local constant at its default. Order matters: on
# the staged copy the bind master is ALREADY dangling, so assigning .val
# first would push through the broken bind and raise -- detach via mode,
# then set. The dangling bind also evaluates to nothing useful, which is
# why the default (not the staged "current value") is what ships.
BOUND_SETTINGS = ('Active', 'Interval', 'Mode', 'Onlymodified', 'Skipperform')
READOUTS = ('Status', 'Lastsave')


def _sanitize(comp):
	for name in READOUTS:
		p = getattr(comp.par, name, None)
		if p is not None and p.mode == ParMode.CONSTANT:
			p.val = ''
	for name in BOUND_SETTINGS:
		p = getattr(comp.par, name, None)
		if p is None:
			continue
		try:
			p.mode = ParMode.CONSTANT
			p.val = p.default
			# Drop the stored bind too: inert in constant mode, but it still
			# ships and names an op in whatever project this was exported
			# from. Same reasoning as the companion's _clearExternalOpRefs.
			p.bindExpr = ''
		except Exception:
			pass


_sanitize(parent())

# The generic FNS strip runs LAST, after this package's own scrub: root-panel
# binds frozen, web servers pinned to loopback, vc_data / Version Ctrl pages
# gone, stubser logs cleared, console exposure dormant, FNS_About.Owner an
# expression. Every package runs it; the 25 that did not shipped their PI
# bookkeeping and dev-project paths in v3.1.3 (packaging/pre_release_common.py).
exec(open('packaging/pre_release_common.py').read())
