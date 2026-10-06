'''Info Header Start
Name : extutils_distributor
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
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
	slim - no NoNode; lives inside the FNS_*Registry hosts and
	       FNS_ConfigHost.  NOT cloned (cloning would force the master's
	       whole child set onto a deliberately trimmed copy), but each
	       slim MUST carry a FNSCommand DAT file-synced to the master's
	       module - rollout() copies it in where missing, so the module
	       has ONE source of truth everywhere.

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
SLIM_MASTER_NAME = 'ExtUtilsMinimal'         # the slim master beside the full one (2026-09-03)
EXCLUDE_PREFIXES = ('/TDXLauncherUtility',)  # companion ships its own copy


def master():
	"""The master ExtUtils this package distributes (sibling of this DAT)."""
	return me.parent().op(MASTER_NAME)


def slim_master():
	"""The slim master (ExtUtilsMinimal) beside the full one, or None.

	Slim copies used to be independent copies with file-synced modules;
	since 2026-09-03 a clone master exists so new slims can link to it.
	Linking the existing fleet is an explicit rollout(link_slim=True): a
	clone re-sync rebuilds a copy's children from the master, and a slim
	that drifted from the master's shape would be reshaped silently.
	"""
	return me.parent().op(SLIM_MASTER_NAME)


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
	       'need_clone': [], 'need_docks': [], 'missing_modules': [],
	       'slim_missing_fnscommand': [], 'slim_need_docks': [],
	       'slim_master': None, 'slim_not_linked': 0}
	sm = slim_master()
	out['slim_master'] = sm.path if sm is not None else None
	for c in _instances():
		reason = _skipReason(c, m)
		if reason:
			out['skipped'][reason] = out['skipped'].get(reason, 0) + 1
			if reason == 'slim':
				if c.op('FNSCommand') is None:
					out['slim_missing_fnscommand'].append(c.path)
				# slims are not clone targets, but their internal docks drift
				# exactly like the fulls' (clone re-sync and promotion copies
				# drop them), and a slim whose extParExec is undocked has DEAD
				# par callbacks: 46 of 201 were found that way on 2026-09-02,
				# every config host in the fleet, with this survey saying healthy.
				drift = _dockDrift(c, dockmap)
				if drift:
					out['slim_need_docks'].append((c.path, drift))
				# informational, not a health failure: linking is the owner's call
				if sm is not None and c.path != sm.path and not _isCloneOf(c, sm):
					out['slim_not_linked'] += 1
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
	out['healthy'] = not (out['need_clone'] or out['need_docks']
	                      or out['missing_modules']
	                      or out['slim_missing_fnscommand']
	                      or out['slim_need_docks'])
	return out


def rollout(apply=False, link_slim=False):
	"""Clone every full ExtUtils from the master, then repair its docks.

	Dry run by default - pass apply=True to write. Returns a report of
	what was (or would be) touched; check 'healthy' from survey() after.
	link_slim=True also clone-links every slim copy to the slim master
	(see slim_master()); off by default, deliberately.
	"""
	m = master()
	if m is None:
		return {'ok': False, 'error': 'no master %r beside this DAT' % MASTER_NAME}
	dockmap = _dockMap(m)
	out = {'ok': True, 'apply': apply, 'master': m.path,
	       'cloned': [], 'docks_repaired': [], 'skipped': {},
	       'slim_module_added': [], 'slim_docks_repaired': [], 'slim_linked': []}
	sm = slim_master()
	for c in _instances():
		reason = _skipReason(c, m)
		if reason:
			out['skipped'][reason] = out['skipped'].get(reason, 0) + 1
			if reason == 'slim':
				if c.op('FNSCommand') is None:
					if apply:
						_addSlimModule(c, m)
					out['slim_module_added'].append(c.path)
				if link_slim and sm is not None and c.path != sm.path and not _isCloneOf(c, sm):
					if apply:
						c.par.enablecloning = True
						c.par.clone = sm
					out['slim_linked'].append(c.path)
				drift = _dockDrift(c, dockmap)      # see survey(): dead par callbacks otherwise
				if drift:
					if apply:
						drift = _repairDocks(c, dockmap)
					out['slim_docks_repaired'].append((c.path, drift))
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


def _addSlimModule(slim, m):
	"""Copy the master's FNSCommand DAT into a slim instance.

	The copy keeps the master's file/syncfile binding, so every copy
	syncs the ONE module file - single source of truth. Placed at the
	slim network's clear bottom-left corner.
	"""
	import math
	new = slim.copy(m.op('FNSCommand'))
	sibs = [x for x in slim.children if x is not new]
	if sibs:
		new.nodeX = int(math.floor(min(x.nodeX for x in sibs) / 200.0) * 200)
		new.nodeY = int(math.floor((min(x.nodeY for x in sibs)
		                            - new.nodeHeight - 200) / 200.0) * 200)
	return new


def _instances():
	"""Every ExtUtils in the project, by tag then by name.

	root.findChildren does NOT reach the promoted registry copies in
	/sys (found the hard way: their slim ExtUtils missed a module
	sweep), so /sys is scanned explicitly.
	"""
	found = {}
	for c in root.findChildren(tags=[MASTER_NAME]):
		found[c.path] = c
	for c in root.findChildren(name=MASTER_NAME):
		found.setdefault(c.path, c)
	sysop = op('/sys')
	if sysop:
		for c in sysop.findChildren(name=MASTER_NAME):
			found.setdefault(c.path, c)
	return list(found.values())


def _skipReason(comp, m):
	"""Why comp is not a rollout target, or None when it is one."""
	if comp.path == m.path:
		return 'master'
	sm = slim_master()
	if sm is not None and comp.path == sm.path:
		return 'slim-master'
	if comp.path.startswith(EXCLUDE_PREFIXES):
		return 'excluded'
	if comp.op(FULL_MARKER) is None:
		return 'slim'
	if comp.path.startswith('/sys/'):
		# Full instances inside promoted /sys registry copies are
		# process-transient - recreated from their (already covered)
		# shippers on every promotion. Slims above still get the
		# FNSCommand module check; fulls are not clone targets.
		return 'sys-transient'
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
