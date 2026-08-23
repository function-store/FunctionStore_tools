
'''Info Header Start
Name : ExtStubserWrapper
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
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

class ExtStubserWrapper:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.stubser : extStubser = self.ownerComp.op('stubser')
		fnsLog('StubserWrapper: init')

	def OnDeploystubs(self):
		fnsLog('StubserWrapper: deploying stubs for selected ops')
		includePrivate = self.ownerComp.par.Private.eval()
		includeUnpromoted = self.ownerComp.par.Unpromoted.eval()
		tags = self.ownerComp.par.Tags.eval()
		tags = tags.split(' ') if tags else []
		for _op in ui.panes.current.owner.selectedChildren:
			if _op.family == 'COMP':
				ui.status = f'Stubifying COMP {_op.name}'
				# we need to iterate cause we can have multiple tags, but tag parameter only accepts one
				for tag in tags:
					self.stubser.StubifyComp(_op, tag=tag, includePrivate=includePrivate, includeUnpromoted=includeUnpromoted)
			elif _op.family == 'DAT' and _op.isEditable:
				ui.status = f'Stubifying DAT {_op.name}'
				self.stubser.StubifyDat(_op)