
'''Info Header Start
Name : QuickParentExt
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




FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class QuickParentExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.popDialog = self.ownerComp.op('popDialog')
		self.paneParent = None
		fnsLog('QuickParent: init')

	

	def AddParentshortcut(self, _target):
		self.paneParent = _target
		defaultText = self.paneParent.name if self.paneParent.par.parentshortcut.eval() == '' else self.paneParent.par.parentshortcut.eval()
		self.popDialog.Open(text='Add Parent Shortcut', title='Add Parent Shortcut', buttons=['OK', 'Cancel'],
			escButton=2, enterButton=1, escOnClickAway=True, textEntry=defaultText, callback=self.OnAddParentshortcutCallback)
	

	def OnAddParentshortcutCallback(self, result):
		if result['button'] == 'OK':
			if self.paneParent is not None:
				parentshortcutpar = self.paneParent.par.parentshortcut
				if parentshortcutpar is not None:
					parentshortcutpar.val = result['enteredText']
					fnsLog(f'QuickParent: set parent shortcut "{result["enteredText"]}" on {self.paneParent.path}')



	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Add parent shortcut')
	def AddShortcutToCurrent(self):
		"""Add a parent shortcut to the current COMP (prompts for the name)."""
		target = ui.panes.current.owner.currentChild
		if target is None or not target.isCOMP:
			return {'ok': False, 'error': 'current operator is not a COMP'}
		self.AddParentshortcut(target)
		return {'ok': True, 'target': target.path}

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
