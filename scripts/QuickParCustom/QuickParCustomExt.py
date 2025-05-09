

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class QuickParCustomExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.compEditor = op('/sys/TDDialogs/CompEditor')
		self.customParPromoter : customParPromoterExt = getattr(op, 'FNS_CPP', None)

	@property
	def rolloverPar(self):
		return ui.rolloverPar
	
	@property
	def mod(self):
		return self.ownerComp.op('null_hk')['shift'].eval()
	
	def onShortcut(self, shortcutName):
		_par = self.rolloverPar
		if _par is None:
			return
		_owner = _par.owner
		_target = None
		do_promote = True
		do_open = False

		if _par.mode == ParMode.EXPORT:
			return
		
		if shortcutName in [self.evalShortcutrolloverpromote, self.evalShortcutrolloverpromotemod]:
			if _owner is not None and _par is not None:
				if _par.mode in [ParMode.BIND, ParMode.EXPRESSION]:
					_target, _par = self._getExpressionTarget(_par)
					do_open = True
					do_promote = False
				if do_promote:
					self.customParPromoter.Target = _owner.parent() if _target is None else _target
					self.customParPromoter.Reference = _owner
					ui.undo.startBlock('Promote param')
					_new_par = self.customParPromoter.PromotePar(_par, None)
					ui.undo.endBlock()
					if _new_par is not None:
						_par = _new_par[0]
					_owner = _par.owner
				if do_open:
					self.compEditorOpenPar(_owner if _target is None else _target, _par)
		elif shortcutName in [self.evalShortcutrollovercustomize]:
			if _owner.isCOMP:
				self.compEditorOpenPar(_owner, _par)
			else:
				if _par.mode in [ParMode.BIND, ParMode.EXPRESSION]:
					_owner, _par = self._getExpressionTarget(_par)
					self.compEditorOpenPar(_owner, _par)
		elif shortcutName in [self.evalShortcutrolloverswitchparmode]:			
			if _par.mode not in [ParMode.BIND, ParMode.EXPRESSION]:
				return

			_expr_target = _par.expr if _par.mode == ParMode.EXPRESSION else _par.bindExpr
			_par.mode = ParMode.EXPRESSION if _par.mode == ParMode.BIND else ParMode.BIND
			if _par.mode == ParMode.EXPRESSION:
				_par.expr = _expr_target
			else:
				_par.bindExpr = _expr_target


	def _getExpressionTarget(self, _par):
		if _par.mode == ParMode.EXPRESSION:
			_exprEval = _par.evalExpression()
			if isinstance(_exprEval, Par):
				return (_exprEval.owner, _exprEval)
		elif _par.mode == ParMode.BIND:
			_master = _par.bindMaster
			if isinstance((_master_par:=_master), Par) and isinstance( (_master_comp:=_master.owner) , COMP):
				return (_master_comp, _master_par)

	def compEditorOpenPar(self, comp, _par):
		par_name = _par.name
		if not self.compEditor.op('window').isOpen:
			self.compEditor.Open(comp)
		else:
			self.compEditor.Connect(comp)
		self.compEditor.CurrentPage = _par.page.name
		self.compEditor.CurrentPar = _par
		self.compEditor.RefreshListers()
		_comp_editor_pages = self.compEditor.op('pagesAndParameters/listerPages')
		_comp_editor_pars = self.compEditor.op('pagesAndParameters/listerPars')
		_page = _par.page.name
		
		# get page index from comp editor pages
		_page_list = list(filter(lambda x: x['pageName'] == _page, _comp_editor_pages.Data))
		_page_idx = _page_list[0]['sourceIndex']
		if _page_idx != 'Auto-Header':
			_comp_editor_pages.SelectRow(_page_idx+1)
			_comp_editor_pages.scroll(_page_idx, 0)

		if not isinstance(_par, Par):
			return
		if len(_par.parGroup) > 1:
			par_name = _par.parGroup.name
		_par_list = list(filter(lambda x: x['ParName'] == par_name, _comp_editor_pars.Data))
		_par_idx = _par_list[0]['sourceIndex']
		if _par_idx != 'Auto-Header':
			_comp_editor_pars.SelectRow(_par_idx+1)
			_comp_editor_pars.scroll(_par_idx, 0)