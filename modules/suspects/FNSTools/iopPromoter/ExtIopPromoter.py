
'''Info Header Start
Name : ExtIopPromoter
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
import TDFunctions as TDF

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

class ExtIopPromoter:
	"""
	ExtIopPromoter description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.dialog = self.ownerComp.op('popDialog')
		self.target = None
		self._op = None
		fnsLog('iopPromoter: init')

	def PromoteIop(self, _op, target):
		self.target = target
		self._op = _op
		fnsLog(f'iopPromoter: promoting {_op.path} as IOP on {target.path if target else None}')
		self.dialog.Open(textEntry=_op.name)

	def OnSelect(self, info):
		sel = True if info['buttonNum'] == 1 else False

		if sel and self.target and self._op:
			seq = self.target.par.iop.sequence
			seqBlock = None

			for _seqBlock in seq:
				if (not _seqBlock.par.op.eval()) and (not _seqBlock.par.shortcut.eval()):
					seqBlock = _seqBlock
					break
			if not seqBlock:
				seq.numBlocks += 1
				seqBlock = seq[-1]

			seqBlock.par.shortcut = info['enteredText']
			seqBlock.par.op = self.target.relativePath(self._op)

	def OnOpen(self, info):
		#debug(info)
		pass

	def OnClose(self, info):
		#debug(info)
		pass
