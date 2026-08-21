"""extutils_distributor - roll this package's master ExtUtils out to every tool copy.

Points every full ExtUtils in the project at QuickExt/ExtUtils as its
clone master, so a module added to the master - FNSCommand for
FNS_CommandRegistry, say - ships with every tool from then on.

	m = mod('extutils_distributor')     # from inside QuickExt
	m.survey()                          # what would change; no writes
	m.rollout(apply=True)               # do it
	m.survey()                          # healthy=True when clean

Idempotent: instances already cloned and correctly docked are skipped,
so re-running after adding a module to the master is free.

Two shapes of ExtUtils live in the project and only one is a target:

	full - carries NoNode; what a tool's extension docks to.  CLONED.
	slim - 9 children, no NoNode; lives inside the FNS_*Registry hosts
	       and FNS_ConfigHost.  LEFT ALONE - cloning would force the
	       master's whole child set onto a deliberately trimmed copy.

Cloning does NOT carry dock relationships: TD forces a clone's children,
wiring, layout, parameter values and flags to match the master, but not
their docks (see https://docs.derivative.ca/Clone). An instance whose
children get rebuilt therefore comes out undocked, and that breaks
extParameter's Pages expression, which calls mod(me.dock.name). So
rollout() re-docks every child to the master's map and re-arms that
expression afterwards.

Side effects worth knowing, all inherited from the master as-is: the
master's children carry file/syncfile bindings to the QuickExt sources,
its text DATs may carry release info headers, and extKeyboardIn.active
follows the master. Normalize the master first if you do not want those.
"""

MASTER_NAME = 'ExtUtils'
FULL_MARKER = 'NoNode'                       # in full ExtUtils, absent in slim
EXCLUDE_PREFIXES = ('/TDXLauncherUtility',)  # companion ships its own copy


def master():
	"""The master ExtUtils this package distributes (sibling of this DAT)."""
	return me.parent().op(MASTER_NAME)


def targets():
	"""Every full ExtUtils instance a rollout would touch."""
	m = master()
	if m is None:
		return []
	return [c for c in _instances() if _skipReason(c, m) is None]


def survey():
	"""Report what rollout() would change, without writing anything."""
	m = master()
	if m is None:
		return {'ok': False, 'error': 'no master %r beside this DAT' % MASTER_NAME}
	dockmap = _dockMap(m)
	modules = set(x.name for x in m.children)
	out = {'ok': True, 'master': m.path, 'targets': 0, 'skipped': {},
	       'need_clone': [], 'need_docks': [], 'missing_modules': []}
	for c in _instances():
		reason = _skipReason(c, m)
		if reason:
			out['skipped'][reason] = out['skipped'].get(reason, 0) + 1
			continue
		out['targets'] += 1
		if not _isCloneOf(c, m):
			out['need_clone'].append(c.path)
		missing = sorted(modules - set(x.name for x in c.children))
		if missing:
			out['missing_modules'].append((c.path, missing))
		drift = _dockDrift(c, dockmap)
		if drift:
			out['need_docks'].append((c.path, drift))
	out['healthy'] = not (out['need_clone'] or out['need_docks'] or out['missing_modules'])
	return out


def rollout(apply=False):
	"""Clone every full ExtUtils from the master, then repair its docks.

	Dry run by default - pass apply=True to write. Returns a report of
	what was (or would be) touched; check 'healthy' from survey() after.
	"""
	m = master()
	if m is None:
		return {'ok': False, 'error': 'no master %r beside this DAT' % MASTER_NAME}
	dockmap = _dockMap(m)
	out = {'ok': True, 'apply': apply, 'master': m.path,
	       'cloned': [], 'docks_repaired': [], 'skipped': {}}
	for c in _instances():
		reason = _skipReason(c, m)
		if reason:
			out['skipped'][reason] = out['skipped'].get(reason, 0) + 1
			continue
		if not _isCloneOf(c, m):
			if apply:
				c.par.enablecloning = True
				c.par.clone = m
			out['cloned'].append(c.path)
		# after cloning: children may have been rebuilt, dropping their docks
		drift = _dockDrift(c, dockmap)
		if drift:
			if apply:
				drift = _repairDocks(c, dockmap)
				_rearmParameterPages(c)
			out['docks_repaired'].append((c.path, drift))
	return out


def _instances():
	"""Every ExtUtils in the project, by tag then by name."""
	found = {}
	for c in root.findChildren(tags=[MASTER_NAME]):
		found[c.path] = c
	for c in root.findChildren(name=MASTER_NAME):
		found.setdefault(c.path, c)
	return list(found.values())


def _skipReason(comp, m):
	"""Why comp is not a rollout target, or None when it is one."""
	if comp.path == m.path:
		return 'master'
	if comp.path.startswith(EXCLUDE_PREFIXES):
		return 'excluded'
	if comp.op(FULL_MARKER) is None:
		return 'slim'
	return None


def _isCloneOf(comp, m):
	if not comp.par.enablecloning.eval():
		return False
	clone = comp.par.clone.eval()
	return clone is not None and clone.path == m.path


def _dockMap(m):
	"""child name -> name of the child it docks to (None when undocked)."""
	return {x.name: (x.dock.name if x.dock else None) for x in m.children}


def _dockDrift(comp, dockmap):
	"""Children of comp whose dock does not match the master's."""
	out = []
	for x in comp.children:
		if x.name not in dockmap:
			continue
		if (x.dock.name if x.dock else None) != dockmap[x.name]:
			out.append(x.name)
	return out


def _repairDocks(comp, dockmap):
	"""Re-dock comp's children to the master's map. Returns names fixed."""
	fixed = []
	for x in comp.children:
		if x.name not in dockmap:
			continue
		want = dockmap[x.name]
		if (x.dock.name if x.dock else None) == want:
			continue
		x.dock = comp.op(want) if want else None
		fixed.append(x.name)
	return fixed


def _rearmParameterPages(comp):
	"""Re-evaluate extParameter.pages - its expression needs me.dock back."""
	par_dat = comp.op('extParameter')
	if par_dat is None or par_dat.par.pages.mode.name != 'EXPRESSION':
		return False
	par_dat.par.pages.expr = par_dat.par.pages.expr
	par_dat.cook(force=True)
	return True
