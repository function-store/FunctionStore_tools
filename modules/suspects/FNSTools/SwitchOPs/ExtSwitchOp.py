
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
		if _op.path not in [row[0] for row in self.fifo.rows(val=True)]:
			self.fifo.appendRow(_op.path)

	def OnSwitch(self):
		_current = ui.panes.current.owner.currentChild
		_cur_path = _current.path if _current else None
		_swop = next((row[0] for row in self.fifo.rows(val=True) if row[0] != _cur_path and op(row[0])), None)
		if not _swop:
			return
		fnsLog(f'SwitchOPs: switching current to {_swop}')
		op(_swop).current = True