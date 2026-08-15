
'''Info Header Start
Name : ExtSwitchOp
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

class ExtSwitchOp:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.fifo = self.ownerComp.op('fifo1')
		fnsLog('SwitchOPs: init')

	def OnSelectOP(self, _op):
		if _op not in self.fifo.rows(val=True):
			self.fifo.appendRow(_op)
		pass

	def OnSwitch(self):
		_current = ui.panes.current.owner.currentChild
		_swop = next((_op for _op in self.fifo.rows(val=True) if _op != _current.path), None)
		fnsLog(f'SwitchOPs: switching current to {_swop[0] if _swop else None}')
		opex(_swop[0]).current = True
		pass