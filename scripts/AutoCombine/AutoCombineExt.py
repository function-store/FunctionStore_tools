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

class AutoCombineExt:
	"""
	AutoCombineExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	def SetCombine(self, _op):
		if not _op.inputs:
			return
		if self.ownerComp.op('null_hk')['activate'].eval():
			if _op.pars('combineinput'):
				try:
					_op.par.combineinput.val = parent.AutoCombine.par.Combineinput.eval()
					_op.par.operand.val = parent.AutoCombine.par.Operand.eval()
				except:
					pass
			if _op.pars('rgb'):
				try:
					_op.par.rgb.val = parent.AutoCombine.par.Rgb.eval()
				except:
					pass
			if _op.pars('format'):
				_op.par.format.val = parent.AutoCombine.par.Format.eval()
		pass