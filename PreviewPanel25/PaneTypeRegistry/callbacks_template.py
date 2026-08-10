"""PaneTypeRegistry callbacks -- what happens when your pane is recalled.

Spawned by the 'Create Callbacks' pulse on a PaneTypeRegistry host, which
also points that host's Callback parameter at this DAT. Nothing else is
needed: fill in the hook and the panebar picks it up.

HOW IT WORKS
    Your tool ships ONE registry host + ONE of these DATs. The host
    registers your COMP as a pane type, and the entry stores only a
    REFERENCE to this DAT -- the behaviour lives here, with your tool, and
    travels inside your tool's .tox.

WHERE IT LANDS
    The registry adds your entry to TD's panebar pane-type menu. Choosing
    it recalls your COMP into that pane:

    panebar menu  ->  entry selected
        1. built-in flags run first, in this order, from the host's
           Registration page:
              Set Owner ....... point the pane at the registered COMP
              Change Type ..... switch the pane to the registered Pane Type
              Maximize / Tear Away / Float / Open Parameters
        2. THEN onPaneRecall(ctx) runs -- this file

    So the hook is for what the flags cannot express: focusing a field,
    opening your panel, refreshing a lister, restoring last state.

THE CONTRACT
    The hook is OPTIONAL. As shipped this file does nothing -- uncomment
    the example, or write your own. `me` is this DAT, so `me.parent()` is
    your tool; resolve everything from there, never an absolute path.

    A hook that raises is contained: the registry reports it with debug()
    and the recall still completes.
"""


def onPaneRecall(ctx):
	"""Run after the built-in recall actions.

	ctx keys:
	    pane       -- ui.Pane (reassigned after changeType if that ran)
	    pane_comp  -- the panebar UI COMP that triggered the selection
	    owner      -- the registered COMP, or None
	    canonical  -- the panebar menu name this entry was registered under
	    info       -- the raw registry entry dict
	    registry   -- the PaneTypeRegistryExt instance
	"""
	# owner = ctx.get('owner')
	# pane = ctx.get('pane')
	# if owner is not None and hasattr(owner, 'Open'):
	# 	owner.Open()
	pass
