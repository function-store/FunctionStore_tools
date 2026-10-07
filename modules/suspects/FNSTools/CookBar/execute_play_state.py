def playState(state):
	
	if parent().par.Active:
		mod.text_funcs.active(state)
	
	parent().par.Active.enable = state
	parent().comment = '' if state else 'cook bar deactivated, no support for paused timeline'