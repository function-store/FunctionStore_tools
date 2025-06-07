customables = ['baseCOMP',
				'containerCOMP',
				'geometryCOMP',
				'scriptCHOP',
				'scriptDAT',
				'scriptSOP',
				'scriptTOP']

toreset = op('null_toreset')
custompars = op('null_custom_resetpars')

for r in toreset.rows()[1:]:
	op_type = r[0].val
	o = op(r[1].val)
	
	# there are some exceptions
	if 'DAT' in op_type and op_type != 'scriptDAT':
		o.par.clear.pulse()
	elif op_type in ['replicatorCOMP']:
		o.par.recreateall.pulse()
	elif op_type in ['audiofileinCHOP','moviefileinTOP']:
		o.par.cuepulse.pulse()
	elif op_type == 'actorCOMP':
		o.par.updatecspulse.pulse()
	elif op_type in ['timerCHOP','flexsolverCOMP','bulletsolverCOMP','flowTOP']:
		o.par.start.pulse()
	elif op_type.endswith('POP'):
		if hasattr(o.par, 'startpulse'):
			o.par.startpulse.pulse()
	elif op_type not in customables:
		# default case
		if op_type in ['speedCHOP']:
			if o.parent().OPType == 'timeCOMP' and not parent().par.Timeline.eval():
				continue
		try:
			o.par.resetpulse.pulse()
		except:
			continue
			
	if op_type in customables:
		for resetpar in op('table_custom_resetpars').rows():
			if hasattr(o.par, resetpar[0].val):
				try:
					o.par[resetpar[0].val].pulse()
				except:
					continue

# misc		
if parent().par.Timeline.eval():
	op('/').time.frame = parent().par.Frame.eval()
	try:
		ui.panes.current.owner.time.frame = parent().par.Frame.eval()
	except:
		pass
	
if parent().par.Customscript.eval():
	op('callbackManager').Execute('onReset')()