
'''Info Header Start
Name : ClearParsExt
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

class ClearParsExt:
	"""
	ClearParsExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.Op = None
		fnsLog('ClearPars: init')

	def ClearPars(self):

		_ops = [self.Op]
		fnsLog(f'ClearPars: clearing par errors on {self.Op.path if self.Op else None} '
			f'(recursive={self.ownerComp.par.Recursive.eval()})')

		if self.ownerComp.par.Recursive.eval():
			if _op := _ops[0]:
				if _op.isCOMP:
					_ops.extend(_op.findChildren(depth=1, includeUtility=False, key=lambda _o: _o.opType != 'annotateCOMP' and 'annotate' not in _o.name))
			
		ui.undo.startBlock('Clear Par Errors')
		for _op in _ops:
			if _op is None:
				continue
			for _par in _op.pars():
				if _par.name == 'autoexportroot' or 'expr' in _par.name:
					continue
				if _par.valid:
					if _par.mode == ParMode.BIND:
						if _par.bindMaster == None:
							_par.bindExpr = None
							_par.expr = None
							_par.mode = ParMode.CONSTANT
							pass
					if _par.mode == ParMode.EXPRESSION:
						try:
							_par.eval()
						except:
							_par.expr = None
							_par.bindExpr = None
							_par.mode = ParMode.CONSTANT
			
			if _op.isCOMP and _op.opType != annotateCOMP:
				_op.clearScriptErrors(recurse=True)
		ui.undo.endBlock()