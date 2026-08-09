"""PaneTypeRegistry recall callbacks.

Called when a registered panebar entry is selected.
"""


def onPaneRecall(ctx):
	"""Run custom logic after built-in recall actions.

	ctx keys:
		pane       - ui.Pane (reassigned after changeType if that ran)
		pane_comp  - panebar UI COMP that triggered the selection
		owner      - registered COMP, or None
		canonical  - panebar menu name
		info       - registry entry dict
		registry   - PaneTypeRegistryExt instance

	Built-in flags (Set Owner / Change Type / Maximize / Float) run first;
	use this for panel-specific behavior (Open, focus, etc.).
	"""
	# owner = ctx.get('owner')
	# pane = ctx.get('pane')
	# if owner is not None and hasattr(owner, 'Open'):
	#     owner.Open()
	pass
