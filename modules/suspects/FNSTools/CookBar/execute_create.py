def create():

	# check if timeline is not running
	if op('/local/time') and not op('/local/time').par.play:
	
		parent().par.Active.enable = False
		parent().comment = 'cook bar deactivated, no support for paused timeline'
	
	# FNSTools: only while Active. Unguarded, creating the tool (or installing
	# the toolkit) dropped its background ops into whatever network was open
	# and switched off the display flags there, with the bar off.
	elif parent().par.Active:
	
		mod.text_funcs.check()
