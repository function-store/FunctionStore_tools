
'''Info Header Start
Name : ExtOpenExt
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
Saveversion : 2025.33070
Info Header End'''
import re

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

class ExtOpenExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		fnsLog('OpenExt: init')

	def OnOpen(self):
		_op = ui.panes.current.owner.currentChild
		if not _op.isCOMP:
			return
		
		_object = None
		for _block in _op.seq.ext:
			if _block.par.promote:
				_object = _block.par.object
				break
		if _object:
			_op_relative_path = self._getExtOpPath(_object.eval())
			if not _op_relative_path:
				return
			
			_dat = _op.op(_op_relative_path)
			if _dat:
				fnsLog(f'OpenExt: opening extension DAT {_dat.path}')
				_dat.par.edit.pulse()

	def _getExtOpPath(self, _object):
		pattern = r"op\('(.*?)'\)\.module\..*\(me\)"
		match = re.search(pattern, _object)
		if not match:
			return None
		return match.group(1)
		
		

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Open extension of current')
	def OpenCurrentExt(self):
		"""Open the extension code of the current COMP."""
		self.OnOpen()
		return {'ok': True}

	def onInitTD(self):
		run('args[0]._announceCommands()', self, delayFrames=60)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def onDestroyTD(self):
		try:
			reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
			if reg is not None and hasattr(reg, 'Unregister'):
				reg.Unregister(self.ownerComp.path)
		except Exception:
			pass
