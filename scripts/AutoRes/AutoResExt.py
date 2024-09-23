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

class AutoResExt:
	"""
	AutoResExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	def SetRes(self, _op):
		if self.ownerComp.op('null_hk')['activate'].eval() and _op.pars('outputresolution'):
			if not _op.inputs:
				if _op.par.outputresolution.enable and not _op.isFilter:
					
					parentPanel = False
					i = 1
					try:
						while not parentPanel:
							parentPanel = _op.parent(i).isPanel
							i += 1						
					except:
						pass
					if parentPanel:
							_op.par.outputresolution.val = 10
					else:
						_op.par.outputresolution.val = 9
						_op.par.resolutionw.expr = "tdu.tryExcept(lambda: parent.Project.width, op.AUTO_RES.par.Resolutionw)"
						_op.par.resolutionh.expr = "tdu.tryExcept(lambda: parent.Project.height, op.AUTO_RES.par.Resolutionh)"						
					
					if _op.pars('rgb'):
						try:
							_op.par.rgb.val = parent.AutoRes.par.Rgb.eval()
						except:
							pass
					if _op.pars('format'):
						_op.par.format.val = parent.AutoRes.par.Format.eval()
					
		pass