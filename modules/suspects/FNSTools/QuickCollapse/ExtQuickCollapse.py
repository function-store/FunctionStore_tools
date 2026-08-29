
'''Info Header Start
Name : ExtQuickCollapse
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

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

class ExtQuickCollapse:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.popDialog = ownerComp.op('popDialog')
		self.newCOMP = None
		self.selected = None
		fnsLog('QuickCollapse: init')

	def undoCollapse(self, isUndo, _return):
		ui.panes.current.owner = _return
		pass
	
	def OnCollapse(self, customize=False):
		self.selected = ui.panes.current.owner.selectedChildren
		if not self.selected:
			return

		if customize:
			self.popDialog.Open(callback=self.OnCustomizeCallback)
			return
		else:
			self.collapse()
		pass

	def collapse(self, _name=None, _shortcut=None, ok_by_enter=False):
		if not self.selected or ok_by_enter:
			return
		fnsLog(f'QuickCollapse: collapsing {len(self.selected)} ops'
			+ (f' into "{_name}"' if _name else ''))
		ui.undo.startBlock('Collapsing')
		ui.undo.addCallback(self.undoCollapse, info = ui.panes.current.owner)
		
		self.selected[0].parent().collapseSelected()
		self.newCOMP = ui.panes.current.owner.currentChild

		if not self.newCOMP:
			ui.undo.endBlock()
			return
		
		if _name:
			self.newCOMP.name = _name
		if _shortcut:
			self.newCOMP.par.parentshortcut = _shortcut

		ui.panes.current.owner = self.newCOMP
		ui.undo.endBlock()



	def OnCustomizeCallback(self, info):
		if info['buttonNum'] == 1:
			# we need to check if `OK` was pressed by enter key ### might be only for Mac???
			# TODO: check if this is the case for Windows
			key = self.ownerComp.op('keyboardin1')[1,'key'].val
			ok_by_enter = key == 'enter' 
			
			self.collapse(_name=info['enteredText'][0], _shortcut=info['enteredText'][1], ok_by_enter=ok_by_enter)
			

	


	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Collapse selected')
	def CollapseSelected(self):
		"""Collapse the selected operators into a container."""
		self.OnCollapse()
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

	@FNSCommand.fns_command(label='Toggle QuickCollapse', state='Active')
	def ToggleActive(self):
		"""Enable or disable QuickCollapse."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
