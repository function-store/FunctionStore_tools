"""ConfigRegistry callbacks -- persist tool state beyond parameters.

Spawned by the 'Create Callbacks' pulse on a ConfigRegistry host, which
also points that host's Callback parameter at this DAT.

HOW IT WORKS
    Your tool ships ONE ConfigRegistry host (+ optionally one of these
    DATs). The host publishes your tool into the /sys global config
    registry; the global aggregates every tool's section into ONE json
    file in the user palette (FNStools_ext/config/FNStools_config.json).

    Custom PARAMETER state is persisted automatically for every hosted
    tool (Persist Pars toggle on the host) -- you do NOT need this DAT
    for that. This DAT is for state that lives OUTSIDE parameters: table
    rows, storage dicts, anything JSON-serializable.

THE CONTRACT
    Both hooks are optional; the registry probes this module and uses
    what it finds. `me` is this DAT, so `me.parent()` is your tool.
    Resolve everything from there -- never an absolute path, never a
    global shortcut.

    A hook that raises is contained: the registry reports it with
    debug(), skips this tool's state, and the config file stays intact.

WHEN THEY RUN
    onConfigSave -- on every SaveAll: TD's project pre-save, the Saveall
        pulse, and right before the UPDATER replaces the toolkit.
    onConfigLoad -- once per session after your tool registers (Autoload
        on the host, default on), AFTER parameter state was applied; also
        on an explicit Loadall / LoadTool.
"""


def onConfigSave():
	"""State to persist for this tool.

	-> dict, JSON-serializable (str/int/float/bool/None/list/dict only).
	   Stored under this tool's "state" key in the config file.
	   Return {} (or delete this function) to persist nothing extra.
	"""
	# return {'rows': [[c.val for c in r] for r in me.parent().op('my_table').rows()]}
	return {}


def onConfigLoad(data):
	"""Re-apply previously saved state.

	data -- exactly what onConfigSave returned when the file was written.
	Parameter state has already been applied when this runs.
	"""
	# t = me.parent().op('my_table')
	# t.clear()
	# for r in data.get('rows', []):
	# 	t.appendRow(r)
	return
