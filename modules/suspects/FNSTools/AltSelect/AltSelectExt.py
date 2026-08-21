
'''Info Header Start
Name : AltSelectExt
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

class AltSelectExt:
	"""
	AltSelectExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.lastSelectedPos = (0, 0)
		self.family_to_selectpar = {
			'SOP':'sop',
			'TOP':'top',
			'CHOP':'chops',
			'DAT':'dat',
			'COMP':'selectpanel',
			'POP': 'pop'
		}
		self._tag = 'FNS_AltSelect'
		self.selectColor = (0.71, 0.53, 0.16)
		self.lastSelectedPos = None
		fnsLog('AltSelect: init')


	def OnSelectOP(self, _op):
		if _op:
			self.lastSelectedPos = {'op_pos': (_op.nodeX, _op.nodeY), 'docked_pos': {_dock: (_dock.nodeX, _dock.nodeY) for _dock in _op.docked}}


	@property
	def hotkey(self) -> bool:
		return bool(self.ownerComp.op('null_hk')[0].eval())


	def OnUpdate(self, _op: OP):
		if not self.hotkey:
			return
		
		new_pos = (_op.nodeX, _op.nodeY)
		if self.lastSelectedPos and (new_pos != self.lastSelectedPos):
			self.onPosChange(_op, new_pos, self.lastSelectedPos)


	def onPosChange(self, _op, new_pos, last_pos):
		if _op.family not in self.family_to_selectpar.keys():
			self.lastSelectedPos = None
			return
		# selectCOMP only works with Panel types
		if isinstance(_op, COMP) and not _op.isPanel:
			self.lastSelectedPos = None
			return
		
		fnsLog(f'AltSelect: creating select for {_op.path}', level='DEBUG')
		ui.undo.startBlock('Selecting OP') #---------

		sel_par = self.family_to_selectpar[_op.family]
		sel_fam = _op.family

		new_select = _op.parent().create(f'select{sel_fam}', 
				   f"select_{_op.name.split('_')[-1]}")
		new_select.tags.add(self._tag)
		new_select.nodeX = new_pos[0]
		new_select.nodeY = new_pos[1]
		new_select.par[sel_par] = _op
		new_select.viewer = True
		new_select.color = self.selectColor
		_op.selected = False
		new_select.selected = True
		new_select.current = True

		# I usually have this enabled anyway
		if _op.isPanel:
			new_select.par.matchsize = True

		ui.undo.endBlock() # -------------------------

		# restore pos
		_op.nodeX = last_pos['op_pos'][0]
		_op.nodeY = last_pos['op_pos'][1]

		for _dock in _op.docked:
			if _dock in last_pos['docked_pos'].keys(): 
				_dock.nodeX = last_pos['docked_pos'][_dock][0]
				_dock.nodeY = last_pos['docked_pos'][_dock][1]

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle AltSelect')
	def ToggleActive(self):
		"""Enable or disable AltSelect."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
