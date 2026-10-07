def valueChange(par, val, prev):
	
	if par.name == 'Active':
		active = val == 'on'
		if active:
			mod.text_funcs.check()
		mod.text_funcs.active(active)