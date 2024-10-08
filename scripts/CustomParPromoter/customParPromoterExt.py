import re

class customParPromoterExt:
	"""
	customParPromoterExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.ignorePages = ['About','Info','Common', 'Version Ctrl']
		self._reference = None
		self._target = None
		self.hk_mod = self.ownerComp.op('null_mod')

	@property
	def Reference(self):
		return self._reference
	
	@Reference.setter
	def Reference(self, _op):
		if type(_op) == str:
			_op = op(_op) 
		self._reference = _op
		
	@property
	def Target(self):
		return self._target

	@Target.setter
	def Target(self, comp):
		if type(comp) == str:
			comp = op(comp)
		if comp.family == 'COMP':
			self._target = comp
		else:
			self._target = None

	@property
	def refBind(self):
		return not self.ownerComp.par.Refbind.eval() if self.hk_mod[0].eval() else self.ownerComp.par.Refbind.eval()


#VVVVVVVVVVVVVVVVVVVVVVVVVVVV MAIN VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

	def DoPromoteAll(self, exceptions=None):
		for page in self.Reference.customPages:
			if page.name in self.ignorePages:
				continue

			page_name = f'{self.Reference.name}:{page.name}'

			# Set to keep track of processed parGroups
			processed_parGroups = set()

			for par in page.pars:
				# Handle exceptions
				if exceptions and par.name in exceptions:
					continue

				# Check if the parameter is a parGroup
				if self.IsParGroup(par):
					# Extract the group name without the last character
					pg_name = par.name[:-1]

					# Check if this parGroup has been processed already
					if pg_name in processed_parGroups:
						continue
					processed_parGroups.add(pg_name)

					self.PromoteParGroup(self.Reference.parGroup[pg_name], page_name)
				else:
					self.PromotePar(par, page_name)

	# unfortunately params that are for example XYZ, Float2/3 etc are not handled well by appendPar
	# as it creates duplicates (Par[xyz] becomes Par[xyz][xyz])... therefore the below
	def PromoteParGroup(self, pg, page_name, target = None):
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		
		name = pg.name.title()
  
		if self.parNameExists(name):
			if self.checkAlreadyBound(pg, name):
				return
			else:
				name = self.parNameCheck(name)
		
		page_name_q = f'{self.Reference.name}:{pg.page.name}'
		page_exists = any([_page.name == page_name_q for _page in target.customPages])
		if page_exists:
			new_page = target.customPages[page_name_q]
		else:
			new_page = target.appendCustomPage(page_name)

		try:
			if type(pg) == ParGroupPulse and len(pg.eval()) == 2:
				new_pars = [new_page.appendPar(name, par=pg[0]), new_page.appendPar(f'{name}pulse',par=pg[1])]
			else:
				new_par = new_page.appendPar(name, par=pg[0])
				new_pars = new_par.pars()
				for i, old_par in enumerate(pg):
					new_pars[i].val = old_par.val
					new_pars[i].default = old_par.default
		except:
			if type(pg) == ParGroupPulse:
				new_pars = [new_page.owner.parGroup[name], new_page.owner.parGroup[f'{name}pulse']]
			else:
				new_par = new_page.owner.parGroup[name]
				new_pars = new_par.pars()

		for p, new_p in zip(pg.pars('*'), new_pars):
			new_p.val = p.val
			new_p.startSection = p.startSection
			if not self.refBind:
				new_p.val = p.val
				p.expr = f"{self.Reference.shortcutPath(target)}.par.{new_p.name}"
				p.mode = ParMode.EXPRESSION
			else:
				new_p.val = p.val
				p.bindExpr = f"{self.Reference.shortcutPath(target)}.par.{new_p.name}"
				p.mode = ParMode.BIND	
		

	def PromotePar(self, _par, page_name, target = None):
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		
		name = _par.name.title()
		if self.parNameExists(name):
			if self.checkAlreadyBound(_par, name):
				return
			else:
				name = self.parNameCheck(name)

		page_name_q = f'{self.Reference.name}:{_par.page.name}'
		page_exists = any([_page.name == page_name_q for _page in target.customPages])
		if page_exists:
			new_page = target.customPages[page_name_q]
		else:
			new_page = target.appendCustomPage(page_name)

		try:
			new_par = new_page.appendPar(name, par=_par)
		except:
			new_par = new_page.owner.par[name]

		new_par.startSection = _par.startSection
		new_par.val = _par.val
		if new_par.isMenu:
			new_par.menuSource = target.shortcutPath(self.Reference, toParName = _par.name) 
		if not self.refBind:
			_par.expr = f"{self.Reference.shortcutPath(target)}.par.{new_par.name}"
			_par.mode = ParMode.EXPRESSION
		else:
			new_par.val = _par.val
			_par.bindExpr = f"{self.Reference.shortcutPath(target)}.par.{new_par.name}"
			_par.mode = ParMode.BIND	

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ MAIN ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
	

########################## EDGE CASES ##################################

	def parNameExists(self, name):
		name = name.title() # capitalize first letter
		par_names = list(map(lambda _par: _par.parGroup.name, self.Target.customPars))
		#par_names = [_par.parGroup.name for _par in self.Target.customPars]
		par_names.extend([_par.name for _par in self.Target.customPars])
		return name in par_names
	
	def checkAlreadyBound(self, _par, name):
		# handles pargroups also as one unit
		try:
			_pars = _par.pars()
		except:
			_pars = [_par]
		suspects = [_p for _p in self.Target.pars(f'{name}*')]
		for _par in _pars:
			for _p in suspects:
				if _par in _p.bindReferences:
					return True
		return False
	
	def parNameCheck(self, name):
		# if there is any with the same parameter name add a number
		# NOTE: gets messy with parGroups, but works
		if self.parNameExists(name):
			#tar_page_name = self.tar.par[name].page.name
			#if self.ref.name not in tar_page_name:
			## ^ why was this needed?
			end_digit = tdu.digits(name)
			if None == end_digit:
				end_digit = 0

			end_digit = str(end_digit+1)
			name = re.sub(r'\d+$', '', name)
			name += str(end_digit)
			# recurse
			name = self.parNameCheck(name) # and now check again... and again... ?

		return name

	def IsParGroup(self,par):
		par_name = par.name[:-1]
		try:
			pg = par.owner.parGroup[par_name]
			return len(pg.val) > 1
		except:
			return False
