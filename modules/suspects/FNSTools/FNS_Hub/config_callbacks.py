"""ConfigRegistry callbacks for FNS_Hub.

Persists every configurator tab's `state` table -- dividers, hideable-group
brackets, adopted built-ins' order/display/width (plus their original
`td_order`, so Restore still works after roaming). A configurator is any
direct child of the hub whose extension promotes SnapshotState/RestoreState;
the payload is keyed by that child's name (ToolbarConfigurator,
NavbarConfigurator, MainMenuConfigurator, ...).

Everything else on a bar is persisted by the publishing tool's own host
parameters. These tables are the one piece of layout the configurators own
outright: without them a bar layout dies with the component and never
follows the user to another project.

Restore REPLACES rather than merges -- each table is one coherent per-user
layout -- and re-applies it to the live registry immediately (the payload
lands long after the configurator's boot republish).

The hub's own Hub-page pars (Activetab, Tabuserorder) roam as plain
persisted parameters; they are not part of this payload.
"""

STATE_SCHEMA = 1


def _configurators():
	out = {}
	for c in me.parent().children:
		if not c.isCOMP:
			continue
		try:
			ready = c.extensionsReady
		except Exception:
			ready = False
		if ready and hasattr(c, 'SnapshotState') and hasattr(c, 'RestoreState'):
			out[c.name] = c
	return out


def onConfigSave():
	states = {}
	for name, c in _configurators().items():
		# SnapshotState refreshes live groups' collapsed state from the
		# registry (the bar-side eye writes only there) before dumping
		rows = c.SnapshotState()
		if rows:
			states[name] = rows
	if not states:
		return {}
	return {'schema': STATE_SCHEMA, 'configurators': states}


def onConfigLoad(data):
	states = data.get('configurators') or {}
	cfgs = _configurators()
	for name, rows in states.items():
		c = cfgs.get(name)
		# row 0 is the header, and it travels with the payload so a table
		# written by an older/newer column set still migrates on restore
		if c is None or not rows or 'kind' not in rows[0] or 'name' not in rows[0]:
			continue
		c.RestoreState(rows)
	return
