# Pre-release hook -- runs on the STAGED COPY before the portable tox is
# written (extensions NOT initialized there; direct par/storage edits only).
# args[0] = resolved save path.
#
# Everything FNS_UISkin holds is a REFERENCE into the user's own project, so
# the released tox must ship with every skin parameter blank: a shipped
# reference is either dangling or, worse, silently resolves to an unrelated
# operator in the next project. Blank pars make no claim, which leaves TD's
# UI exactly as the new user had it.

comp = me.parent()

for _page in comp.customPages:
	for _p in _page.pars:
		if _p.style in ('TOP', 'CHOP', 'SOP', 'DAT', 'MAT', 'OP', 'COMP'):
			try:
				_p.mode = ParMode.CONSTANT
				_p.val = ''
			except Exception:
				pass

# captured pre-claim values belong to THIS project's /ui, never to a release
if 'Originals' in comp.storage:
	comp.unstore('Originals')

# never ship bound to this repo's suspect tox
comp.par.enableexternaltox = False
comp.par.externaltox = ''
