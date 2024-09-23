
class ClearParsExt:
	"""
	ClearParsExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.Op = None 

	def ClearPars(self):
		
		_ops = [self.Op]
		
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