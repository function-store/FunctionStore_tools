
class ExtParRandomizer:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.random = iop.Random # this is an extension

	def OnRandomizeOp(self, _op = None):
		ui.undo.startBlock('Randomize OP parameters')
		_op = _op or ui.panes.current.owner.currentChild
		if not _op:
			return
		_par_list = []

		_page = _op.currentPage
		for _par in _page.pars:
			if not (_par.readOnly and _par.enable):
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
		_par = ui.rolloverPar
		self.RandomizePar(_par)
		ui.undo.endBlock()


