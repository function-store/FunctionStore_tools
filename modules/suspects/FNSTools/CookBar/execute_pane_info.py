def frameStart(frame):

	# check if timeline is running
	if op('/local/time') and op('/local/time').par.play:
		
		active = me.fetch('active')
		if active:
			mod.text_funcs.check()