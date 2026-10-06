

'''Info Header Start
Name : AutoResExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
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

class AutoResExt:
	"""
	AutoResExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		fnsLog('AutoRes: init')

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def modifierHeld(self):
		"""Whether the tool's modifier (the Keys parameter, alt) is held right now.

		Asks the OS through FNSModifiers, immune to the missed keyup that
		leaves a Keyboard In latched after an alt-tab -- a latched Alt is
		what armed AutoRes for a drop nobody meant to resize. Where the OS
		cannot be asked it falls back to the keyboardin chain (null_hk).
		"""
		keys = str(self.ownerComp.par.Keys.eval()).split() if self.ownerComp.par['Keys'] is not None else []
		modifier = keys[0].lower().lstrip('lr') if keys else 'alt'
		hk = self.ownerComp.op('null_hk')
		raw = bool(hk['activate'].eval()) if hk is not None else False
		mods = self.ownerComp.op('FNSModifiers')
		if mods is None:
			return raw
		return mods.module.heldOr(modifier, raw)

	def SetRes(self, _op):
		if self.modifierHeld() and _op.pars('outputresolution'):
			if not _op.inputs:
				if _op.par.outputresolution.enable and not _op.isFilter:
					fnsLog(f'AutoRes: setting resolution on {_op.path}', level='DEBUG')

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
	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle AutoRes', state='Active')
	def ToggleActive(self):
		"""Enable or disable AutoRes."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
