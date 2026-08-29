
'''Info Header Start
Name : AutoCombineExt
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




FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class AutoCombineExt:
	"""
	AutoCombineExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		fnsLog('AutoCombine: init')

	def SetCombine(self, _op):
		if not _op.inputs:
			return
		if self.ownerComp.op('null_hk')['activate'].eval():
			fnsLog(f'AutoCombine: applying combine settings to {_op.path}', level='DEBUG')
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
	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle AutoCombine', state='Active')
	def ToggleActive(self):
		"""Enable or disable AutoCombine."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
