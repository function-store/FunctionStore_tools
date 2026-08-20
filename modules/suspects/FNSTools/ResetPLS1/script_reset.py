
'''Info Header Start
Name : script_reset
Author : root
Saveorigin : FunctionStore_tools_2025_DEV.38.toe
Saveversion : 2025.33070
Info Header End'''

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

customables = ['baseCOMP',
				'containerCOMP',
				'geometryCOMP',
				'scriptCHOP',
				'scriptDAT',
				'scriptSOP',
				'scriptTOP']

_root_path = parent().par.Root.eval()
root = op(_root_path if _root_path else '../')
if root is None:
	_err = f"ResetPLS: Root '{_root_path}' does not resolve -- nothing was reset"
	fnsLog(_err, level='ERROR')
	raise ValueError(_err)
fnsLog(f'ResetPLS: resetting ops under {root.path}')
optypes = [r[0].val for r in op('table_optypes').rows()]
exceptions = [p[1:] if p.startswith('^') else p for p in (r[0].val for r in op('merge1').rows())]

def isAllowed(o):
	return o.OPType in optypes and not any(tdu.match(p, [o.path]) for p in exceptions)

maxDepth = int(parent().par.Depth.eval()) if parent().par.Limitdepth.eval() else None
for o in root.findChildren(key=isAllowed, maxDepth=maxDepth):
	op_type = o.OPType
	
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
		if hasattr(o.par, 'resetpulse'):
			o.par.resetpulse.pulse()
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