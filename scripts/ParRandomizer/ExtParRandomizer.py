
class ExtParRandomizer:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.random = iop.Random # this is an extension
		self.ignorePages = ['About','Info','Common', 'Version Ctrl']
		self.checkShortcutRayTK()#
	
	@property
	def shortcutopEval(self):
		return self.ownerComp.par.Shortcutop.eval()
	
	@property#
	def shortcutparEval(self):
		return self.ownerComp.par.Shortcutpar.eval()
	
	# par callbacks
	def Shortcutop(self, _par, _val, _prev):
		self.checkShortcutRayTK()

	# par callbacks#
	def Shortcutpar(self, _par, _val, _prev):
		self.checkShortcutRayTK()
	
	def checkShortcutRayTK(self):
		conflict = False
		if raytk := getattr(op, 'raytk', None):
			if keyboardshortcut := getattr(raytk.par, 'Keyboardshortcut', None):
				if keyboardshortcut.eval() in [self.shortcutopEval, self.shortcutparEval]:
					conflict = True
			if tools_keyboardshortcut := getattr(raytk.par, 'Toolskeyboardshortcut', None):
				if tools_keyboardshortcut.eval() in [self.shortcutopEval, self.shortcutparEval]:
					conflict = True
		if conflict:
			result = ui.messageBox('Conflict with RayTK shortcut','The shortcut for FNS_tools:ParRandomzier is already in use by RayTK.', buttons = ['Ignore', 'Change it'])
			if result == 1:
				raytk.openParameters()
				self.ownerComp.openParameters()
		return conflict

	def OnRayTKChange(self, info):
		if info != '<error>':
			self.checkShortcutRayTK()

	def OnRandomizeOp(self, _op = None):
		ui.undo.startBlock('Randomize OP parameters')
		_op = _op or ui.panes.current.owner.currentChild
		if not _op:
			return
		_par_list = []

		_page = _op.currentPage
		for _par in _page.pars:
			if not (_par.readOnly and _par.enable and _par.page.name not in self.ignorePages):
				_par_list.append(_par)

		for _par in _par_list:
			self.RandomizePar(_par)
		ui.undo.endBlock()
		return

	def RandomizePar(self, _par):
		
		if isinstance(_par, ParGroup):
			for _subpar in _par:
				self.RandomizePar(_subpar)
			return
		
		if _par.page.name in self.ignorePages:
			return
		
		if _par.mode not in [ParMode.CONSTANT, ParMode.BIND]:
			return
		
		if _par.isNumber:
			_min = _par.min if _par.clampMin else _par.normMin
			_max = _par.max if _par.clampMax else _par.normMax
			if _par.isFloat:
				new_val = self.random.Uniform(_min, _max)
			elif _par.isInt:
				new_val = self.random.RandInt(_min, _max)
		elif _par.isToggle:
			new_val = self.random.RandInt(0, 1)
		elif _par.isMenu:
			new_val = self.random.RandInt(0, len(_par.menuNames) - 1)
		else:
			return
		
		_par.val = new_val


	def OnRandomizeRolloverPar(self):
		ui.undo.startBlock('Randomize parameter')
		_par = ui.rolloverPar if not hasattr(ui, 'rolloverParGroup') else ui.rolloverParGroup
		if _par is None or _par.page.name in self.ignorePages:
			return
		
		self.RandomizePar(_par)
		ui.undo.endBlock()

	def onResetPar(self):
		ui.undo.startBlock('Reset parameter')
		_par = ui.rolloverPar if not hasattr(ui, 'rolloverParGroup') else ui.rolloverParGroup
		if _par is None or _par.page.name in self.ignorePages:
			return
		_par.reset()
		ui.undo.endBlock()

	def OnResetAllCustom(self, all = False):
		self.onResetAllCustom(all)

	def onResetAllCustom(self, all = False):
		ui.undo.startBlock('Reset all custom parameters on current page')
		_owner = ui.panes.current.owner.currentChild
			
		par_names = [_par.name for _par in (_owner.currentPage.pars if not all else _owner.customPars)if not _par.readOnly and _par.enable and _par.page.name not in self.ignorePages]
		_owner.resetPars(parNames=' '.join(par_names))
		ui.undo.endBlock()

	def SaveAllCustomDefaults(self, _op = None):
		if _op is None:
			_op = ui.panes.current.owner.currentChild
			if not _op:
				return
		for _par in _op.customPars:
			_par.defaultMode = _par.mode
			_par.default = _par.eval()
			if _par.mode == ParMode.BIND:
				_par.defaultBindExpr = _par.bindExpr
			elif _par.mode == ParMode.EXPRESSION:
				_par.defaultExpr = _par.expr
		

	def OnShortcut(self, shortcutName):
		if shortcutName == self.ownerComp.par.Shortcutop.eval():
			self.OnRandomizeOp()
		if shortcutName == self.ownerComp.par.Shortcutpar.eval():
			self.OnRandomizeRolloverPar()
		if shortcutName == self.ownerComp.par.Shortcutreset.eval():
			self.onResetPar()
		if shortcutName == self.ownerComp.par.Shortcutresetallcustom.eval():
			self.onResetAllCustom()

