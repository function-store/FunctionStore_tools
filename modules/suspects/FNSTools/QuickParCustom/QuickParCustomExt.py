
'''Info Header Start
Name : QuickParCustomExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
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

class QuickParCustomExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp : baseCOMP = ownerComp
		self.compEditor = op('/sys/TDDialogs/CompEditor')
		fnsLog('QuickParCustom: init')

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	@property
	def customParPromoter(self):
		"""CustomParTools, which carries customParPromoterExt -- we are its child.

		Was `getattr(op, 'FNS_CPP', None)`: a tool->tool edge the packaging audit
		believed this tool did not have (it reads as a guarded getattr, not a
		literal reference, so the text scan missed it). Folding this COMP into
		CustomParTools turns it into a plain parent reference.

		Resolved lazily: the parent's extensions are not guaranteed ready while
		this one is still constructing."""
		return self.ownerComp.parent()

	@property
	def rolloverPar(self):
		return ui.rolloverPar

	def _rolloverMembers(self, _par):
		"""The parameters one promote should cover.

		TD exposes both ui.rolloverPar and ui.rolloverParGroup, so hovering tx
		of t can mean the whole group while hovering a single-value parameter
		means just that one -- decided by what is under the cursor rather than
		by a fixed preference.

		Members come back as Pars, NEVER as the ParGroup itself. ParGroup.mode
		is a TUPLE of modes (and .expr / .bindExpr likewise), so handing a
		group to the ParMode checks in onShortcut would compare a tuple to an
		enum, quietly take the wrong branch, and promote the wrong thing.
		"""
		pg = getattr(ui, 'rolloverParGroup', None)
		try:
			if (pg is not None and len(pg) > 1
					and pg.owner is _par.owner
					and pg.name == _par.parGroup.name):
				return list(pg)
		except Exception:
			pass
		return [_par]


	@property
	def mod(self):
		"""Is shift held.

		The CHOP latches: TD loses focus with shift down, the keyup never
		arrives, and the channel stays at 1. FNSModifiers asks the OS
		instead where it can, and returns the CHOP value unchanged where
		it cannot -- so this is a fix on Windows and exactly today's
		behaviour anywhere the OS cannot be asked.
		"""
		chop = self.ownerComp.op('null_hk')['shift'].eval()
		mods = self.ownerComp.op('FNSModifiers')
		if mods is None:
			return chop
		return mods.module.heldOr('shift', chop)
	
	def onShortcut(self, shortcutName):
		_par = self.rolloverPar
		if _par is None:
			return
		fnsLog(f'QuickParCustom: shortcut "{shortcutName}" on par {_par.owner.path}.{_par.name}')
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
					_members = self._rolloverMembers(_par)
					# one undo block for the whole group, not one per member
					ui.undo.startBlock('Promote param' if len(_members) == 1
									   else f'Promote {len(_members)} params')
					_new_par = None
					for _member in _members:
						_promoted = self.customParPromoter.PromotePar(_member, None)
						if _promoted is not None and _new_par is None:
							_new_par = _promoted
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
	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle QuickParCustom', state='Active')
	def ToggleActive(self):
		"""Enable or disable QuickParCustom."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
