
class ExtSwitchOp:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.fifo = self.ownerComp.op('fifo1')

	def OnSelectOP(self, _op):
		if _op not in self.fifo.rows(val=True):
			self.fifo.appendRow(_op)
		pass

	def OnSwitch(self):
		_current = ui.panes.current.owner.currentChild
		_swop = next((_op for _op in self.fifo.rows(val=True) if _op != _current.path), None)
		opex(_swop[0]).current = True
		pass