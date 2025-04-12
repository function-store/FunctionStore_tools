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
		self.popDialog = self.ownerComp.op('popDialog')
		self.__parNumTypes = ['Float', 'Int', 'Xy', 'Xyz', 'Xyzw', 'Uv', 'Uvw', 'Wh','Rgb', 'Rgba']
		self.__saveParamNameBeforePurge = ''

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
	def PromoteParGroup(self, _parGroup, page_name, target = None, refBind = None, parName = None, parLabel = None):
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		if not refBind:
			refBind = self.refBind
		
		label = _parGroup.label.title() if parLabel is None else parLabel
		name = _parGroup.name.title() if parName is None else parName

		if self.parNameExists(name):
			if self.checkAlreadyBound(_parGroup, name):
				return
			else:
				name = self.parNameCheck(name)
		
		new_page = self._getTargetPage(page_name, target, _parGroup.page)
		if new_page.name in (set([p.name for p in target.customPages]) - set([p.name for p in target.pages])):
			target.currentPage = new_page

		try:
			if type(_parGroup) == ParGroupPulse and len(_parGroup.eval()) == 2:
				new_pars = [new_page.appendPar(name, par=_parGroup[0]), new_page.appendPar(name=f'{name}pulse', label=f'{label}', par=_parGroup[1])]
			else:
				new_par = new_page.appendPar(name, label=name, par=_parGroup[0])
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
			if not refBind:
				new_p.val = p.val
				p.expr = f"{self.Reference.shortcutPath(target)}.par.{new_p.name}"
				p.mode = ParMode.EXPRESSION
			else:
				new_p.val = p.val
				p.bindExpr = f"{self.Reference.shortcutPath(target)}.par.{new_p.name}"
				p.mode = ParMode.BIND	



	def PromotePar(self, _par, page_name, target = None, refBind = None, parName = None, parLabel = None, parMin = None, parMax = None, clamp = None, parDefault = None):
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		if refBind is None:
			refBind = self.refBind

		if self.IsParGroup(_par):
			self.PromoteParGroup(_par.parGroup, page_name, target, refBind)
			return
		
		label = _par.label.title() if parLabel is None else parLabel
		name = _par.name.title() if parName is None else parName

		if self.parNameExists(name):
			if self.checkAlreadyBound(_par, name):
				return
			else:
				name = self.parNameCheck(name)

		new_page = self._getTargetPage(page_name, target, _par.page)
		
		if new_page.name in (set([p.name for p in target.customPages]) - set([p.name for p in target.pages])):
			target.currentPage = new_page

		try:
			if type(_par) == ParGroupPulse: # why did it come to this???
				_par = _par[0]
			new_par = new_page.appendPar(name, label=label, par=_par)
		except Exception as e:
			new_par = new_page.owner.par[name]

		if parMin is not None:
			new_par.normMin = parMin
			new_par.min = parMin
			if clamp:
				new_par.clampMin = clamp[0] # true/false
		if parMax is not None:
			new_par.normMax = parMax
			new_par.max = parMax
			if clamp:
				new_par.clampMax = clamp[1] # true/false

		if parDefault is not None:
			new_par.default = parDefault
			
		new_par.startSection = _par.startSection
		new_par.val = _par.val
		if new_par.isMenu:
			new_par.menuSource = target.shortcutPath(self.Reference, toParName = _par.name) 
		if not refBind:
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
		
		custom_page_names = [p.name for p in target.customPages]
		all_page_names = [p.name for p in target.pages]
		
		new_page = None
		# we have a target or candidate page name
		if page_name:
			# Get list of existing page names
			
			# First try the exact page name
			if page_name in custom_page_names:
				new_page = target.customPages[page_name]
			else:
				# Try the constructed page_name_q
				page_name_q = f'{self.Reference.name}:{source_page.name}'
				if page_name_q in custom_page_names:
					new_page = target.customPages[page_name_q]
				else:
					# If neither exists, create the page with the given name
					new_page = target.appendCustomPage(page_name)

		# Only if no page_name was provided, use current custom page or first available
		if new_page is None:
			if target.customPages:
				try:
					new_page = target.currentPage if target.currentPage.name in custom_page_names else None
				except Exception as e:
					new_page = None
					
				if new_page is None:  # means not a custom page selected, take first available
					new_page = target.customPages[0]
				else:
					new_page = TDF.getCustomPage(target, new_page.name)
			else:
				new_page = target.appendCustomPage('Custom')
		
		return new_page

	def purgeParName(self, text, replace=False):
		
		prune_text = text.replace(' ', '')
		# also remove any non-alphanumeric characters
		prune_text = re.sub(r'[^a-zA-Z0-9]', '', prune_text)
		# remove leading and trailing underscores
		prune_text = prune_text.strip('_')
		# remove any leading numbers
		prune_text = re.sub(r'^[0-9]+', '', prune_text)
		text = prune_text.capitalize()
		if replace:
			paramname = self.popDialog.op('entry1/inputText').par.text
			paramname.val = text
		return text
			

	def OnEditText(self, field, text):
		if field == 'paramname':
			# we could purge here but that's not how custom par editor works either
			#self.purgeParName(text, replace=True)
			self.__saveParamNameBeforePurge = text
			#self.popDialog.op('entry2/inputText').par.text = text
			pass
		elif field in ['min', 'max']:
			return
		
	def onFocus(self, field, comp):
		if field == 'label' and self.__saveParamNameBeforePurge and comp.editText == '':
			self.popDialog.op('entry2/inputText').par.text = self.__saveParamNameBeforePurge

	def onFocusEnd(self, field, comp):
		if field == 'paramname':
			text = comp.editText
			self.__saveParamNameBeforePurge = text
		elif field == 'label':
			if comp.editText == '' and self.__saveParamNameBeforePurge:
				comp.par.text = self.__saveParamNameBeforePurge
			self.purgeParName(self.__saveParamNameBeforePurge, replace=True)

	def OnCustomizeParameterDropped(self, dropParam):
		details = {}
		details['refBind'] = self.refBind
		if type(dropParam) == ParGroup:
			# is pargroup
			details['parGroup'] = dropParam
			self.popDialog.par.Minmaxentryarea = False
			is_num = False
		else:
			# is par
			details['par'] = dropParam
			style = dropParam.style
			default = dropParam.default
			is_num = style in self.__parNumTypes
			details['isNum'] = is_num
			self.popDialog.par.Minmaxentryarea = is_num

		textEntries = [dropParam.name.capitalize(), '']
		if is_num:
			textEntries.extend([dropParam.normMin, dropParam.normMax])
			textEntries.append(default)

		self.popDialog.Open(callback=self.OnCustomizeCallback, details=details, textEntries=textEntries)

	def OnCustomizeCallback(self, info):
		if info['buttonNum'] != 1:
			return
		
		details = info['details']
		parGroup = details.get('parGroup', None)
		par = details.get('par', None)
		is_num = details.get('isNum', False)

		labelEntry = info['enteredText'][1]
		nameEntry = info['enteredText'][0]
		
		if not labelEntry:
			labelEntry = nameEntry
		nameEntry = self.purgeParName(nameEntry)
		minEntry = float(info['enteredText'][2]) if is_num and info['enteredText'][2] is not None else None
		maxEntry = float(info['enteredText'][3]) if is_num and info['enteredText'][3] is not None else None
		chekcboxClamp = info['checkBoxes']
		default = info['enteredText'][4] if is_num else None
		
		if parGroup is not None:
			self.PromoteParGroup(parGroup, None, parName=nameEntry, parLabel=labelEntry)
		elif par is not None:
			self.PromotePar(par, None, parName=nameEntry, parLabel=labelEntry, parMin=minEntry, parMax=maxEntry, clamp=chekcboxClamp, parDefault=default)


	def SetTableMenu(self, _table, _target):
		_page = self._getTargetPage(None, _target, None)
		_target.currentPage = _page
		table_name = _table.name.replace('_', '').title()
		par_name = self.parNameCheck(table_name)
		new_par = _page.appendMenu(par_name, replace=False)
		
		# Check first row for label and name columns
		label_col = -1
		name_col = -1
		if _table.numRows > 0 and _table.numCols > 0:
			for col in range(_table.numCols):
				header = str(_table[0, col]).lower()
				if 'label' in header:
					label_col = col
				elif 'name' in header:
					name_col = col
		
		if _table.numCols > 1 and (name_col != -1 or label_col != -1):
			# Use the found label column if available, otherwise default to 1
			name_col = name_col if name_col != -1 else 0
			label_col = label_col if label_col != -1 else 1
			expression = f'tdu.TableMenu({TDF.getShortcutPath(_target, _table)}, nameCol={name_col}, labelCol={label_col}, includeFirstRow=False)'
		else:
			if _table.numCols > 1:
				expression = f'tdu.TableMenu({TDF.getShortcutPath(_target, _table)}, nameCol=0, labelCol=1, includeFirstRow=True)'
			elif _table.numCols == 1:
				expression = f'tdu.TableMenu({TDF.getShortcutPath(_target, _table)}, includeFirstRow=True)'
		new_par.menuSource = expression


