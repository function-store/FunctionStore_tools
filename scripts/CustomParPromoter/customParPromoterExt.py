import re
import TDFunctions as TDF

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
		#for _page in self.Reference.customPages:
		if self.Reference:
			_page = self.Reference.currentPage

		if _page.name in self.ignorePages:
			# continue
			return

		page_name = f'{self.Reference.name}:{_page.name}'

		# Set to keep track of processed parGroups
		processed_parGroups = set()

		for par in _page.pars:
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
	def PromoteParGroup(self, _parGroup, page_name, target = None):
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		
		name = _parGroup.name.title()

		if self.parNameExists(name):
			if self.checkAlreadyBound(_parGroup, name):
				return
			else:
				name = self.parNameCheck(name)
		
		new_page = self._getTargetPage(page_name, target, _parGroup.page)

		target.currentPage = new_page.name

		try:
			if type(_parGroup) == ParGroupPulse and len(_parGroup.eval()) == 2:
				new_pars = [new_page.appendPar(name, par=_parGroup[0]), new_page.appendPar(f'{name}pulse',par=_parGroup[1])]
			else:
				new_par = new_page.appendPar(name, par=_parGroup[0])
				new_pars = new_par.pars()
				for i, old_par in enumerate(_parGroup):
					new_pars[i].val = old_par.val
					new_pars[i].default = old_par.default
		except:
			if type(_parGroup) == ParGroupPulse:
				new_pars = [new_page.owner.parGroup[name], new_page.owner.parGroup[f'{name}pulse']]
			else:
				new_par = new_page.owner.parGroup[name]
				new_pars = new_par.pars()

		for p, new_p in zip(_parGroup.pars('*'), new_pars):
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
		if self.IsParGroup(_par):
			self.PromoteParGroup(_par.parGroup, page_name, target)
			return
		
		name = _par.name.title()
		if self.parNameExists(name):
			if self.checkAlreadyBound(_par, name):
				return
			else:
				name = self.parNameCheck(name)

		new_page = self._getTargetPage(page_name, target, _par.page)

		try:
			new_par = new_page.appendPar(name, par=_par)
		except:
			new_par = new_page.owner.par[name]

		target.currentPage = new_par.page.name

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

	def _getTargetPage(self, page_name, target, source_page=None):
		"""Helper method to handle page selection logic
		Args:
			page_name: Requested page name
			target: Target component
			source_page: Original page from reference component
		Returns:
			Page object to use for parameter promotion
		"""
		new_page = None
		if page_name:
			# Get list of existing page names
			existing_pages = [p.name for p in target.customPages]
			
			# First try the exact page name
			if page_name in existing_pages:
				new_page = target.customPages[page_name]
			else:
				# Try the constructed page_name_q
				page_name_q = f'{self.Reference.name}:{source_page.name}'
				if page_name_q in existing_pages:
					new_page = target.customPages[page_name_q]
				else:
					# If neither exists, create the page with the given name
					new_page = target.appendCustomPage(page_name)
		
		# Only if no page_name was provided, use current custom page or first available
		if new_page is None:
			if target.customPages:
				try:
					new_page = target.currentPage
				except:
					new_page = None
			
				if new_page is None:  # means not a custom page selected, take first available
					new_page = target.customPages[0]
				else:
					new_page = TDF.getCustomPage(target, new_page.name)
			else:
				new_page = target.appendCustomPage('Custom')
		
		return new_page
