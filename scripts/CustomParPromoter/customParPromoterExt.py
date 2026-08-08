'''Info Header Start
Name : customParPromoterExt
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
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

		# GLSL Vectors page: promote only the vector value groups (vec<N>value),
		# each named/labelled from its uniform (vec<N>name) via PromoteParGroup.
		# The vec<N>name string parameters themselves are skipped.
		glsl_vectors = self.__isGlslOp(self.Reference) and _page.name == 'Vectors'

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
			elif not glsl_vectors:
				# On the GLSL Vectors page single pars are the uniform-name
				# strings -- skip them; elsewhere promote singles as usual.
				self.PromotePar(par, page_name)

	# unfortunately params that are for example XYZ, Float2/3 etc are not handled well by appendPar
	# as it creates duplicates (Par[xyz] becomes Par[xyz][xyz])... therefore the below
	def PromoteParGroup(self, _parGroup, page_name, target = None, refBind = None, parName = None, parLabel = None):
		ui.undo.startBlock('Promote param')
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		if refBind is None:
			refBind = self.refBind
			
		glsl_name = self.__glslUniformName(_parGroup)
		label = parLabel if parLabel is not None else (self.__glslLabel(glsl_name) if glsl_name else _parGroup.label.title())
		name = parName if parName is not None else (self.purgeParName(glsl_name) if glsl_name else _parGroup.name.title())

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
				name = name.capitalize()
				new_pars = [new_page.appendPar(name, par=_parGroup[0]), new_page.appendPar(f'{name}pulse', label=f'{label}', par=_parGroup[1])]

			else:
				new_par = new_page.appendPar(name, label=label, par=_parGroup[0])
				new_pars = new_par.pars()
				for i, old_par in enumerate(_parGroup):
					new_pars[i].val = old_par.val
					new_pars[i].default = old_par.default
		except Exception as e:
			if type(_parGroup) == ParGroupPulse:
				new_pars = [new_page.owner.parGroup[name], new_page.owner.parGroup[f'{name}pulse']]
			else:
				name = name.capitalize()
				new_par = new_page.owner.parGroup[name]
				new_pars = new_par.pars()

		for p, new_p in zip(_parGroup.pars('*'), new_pars):
			if p is None or new_p is None:
				continue
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
		ui.undo.endBlock()
		return new_par


	def PromotePar(self, _par, page_name, target = None, refBind = None, parName = None, parLabel = None, parMin = None, parMax = None, clamp = None, parDefault = None):
		ui.undo.startBlock('Promote param')
		if not target:
			target = self.Target
		if page_name in self.ignorePages:
			return
		if refBind is None:
			refBind = self.refBind

		glsl_name = self.__glslUniformName(_par)
		label = parLabel if parLabel is not None else (self.__glslLabel(glsl_name) if glsl_name else _par.label.title())
		name = parName if parName is not None else (self.purgeParName(glsl_name) if glsl_name else _par.name.title())

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
			if self.IsParGroup(_par):
				# single member of a multi-value group (XYZ, RGB, Float3, ...):
				# promote just this component as a standalone scalar, otherwise
				# appendPar(par=_par) would recreate the entire parGroup.
				new_par = self._appendSinglePar(new_page, name, label, _par)
			else:
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
		else:
			_max = _par.normMax
			if _par.name == 'index': # special case
				_owner = _par.owner
				if _owner.inputs:
					_max = len(_owner.inputs) - 1
				new_par.normMax = _max
				new_par.max = _max

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
		ui.undo.endBlock()
		return new_par

	def _appendSinglePar(self, new_page, name, label, _par):
		"""Append a single-value par mirroring one member of a multi-value group.

		appendPar(par=_par) copies the *group* style, so for a member of a
		multi-value parGroup it recreates the whole group. To promote only the
		dropped component we append a single par matching the member's own type.
		Dispatch is by the member's ``is*`` flags rather than a hardcoded numeric
		assumption, so menu/string/etc. group members -- possible in newer TD --
		are handled too; anything unrecognised falls back to appendPar. Returns
		the new ParGroup (size 1).
		"""
		if _par.style == 'StrMenu':
			return new_page.appendStrMenu(name, label=label)
		if _par.isMenu:
			return new_page.appendMenu(name, label=label)
		if _par.isPython:
			return new_page.appendPython(name, label=label)
		if _par.isString:
			return new_page.appendStr(name, label=label)
		if _par.isToggle:
			return new_page.appendToggle(name, label=label)
		if _par.isMomentary:
			return new_page.appendMomentary(name, label=label)
		if _par.isPulse:
			return new_page.appendPulse(name, label=label)
		if _par.isInt:
			return new_page.appendInt(name, label=label)
		if _par.isFloat:
			return new_page.appendFloat(name, label=label)
		# Unrecognised / future style: copy the member definition as a last resort.
		return new_page.appendPar(name, label=label, par=_par)

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
				# future-proofing: use isSamePar if available, otherwise use isPar
				if hasattr(_par, 'isSamePar'):
					if any(_par.isSamePar(__par) for __par in _p.bindReferences):
						return True
				elif hasattr(_par, 'isPar'):
					if any(_par.isPar(__par) for __par in _p.bindReferences):
						return True
				else:
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

	def __isGlslOp(self, _op):
		"""True if the operator is any GLSL type (glslTOP, glslmultiTOP, glslMAT)."""
		return _op is not None and _op.OPType.lower().startswith('glsl')

	def __glslUniformName(self, _par):
		"""Shader uniform name for a GLSL 'vec<N>value' vector-uniform parameter.

		On a GLSL operator's Vectors page each uniform is a 'vec' sequence block:
		the value parGroup is vec<N>value (components vec<N>valuex/y/z/w) and the
		shader name lives in vec<N>name. When such a value parameter is promoted
		we want the meaningful uniform name (e.g. 'uColor') rather than the
		generic 'Vec0value'. Returns the name string, or None if not applicable.
		"""
		try:
			owner = _par.owner
		except Exception:
			return None
		if not self.__isGlslOp(owner):
			return None
		match = re.match(r'^vec(\d+)value[xyzw]?$', _par.name)
		if not match:
			return None
		name_par = owner.par[f'vec{match.group(1)}name']
		if name_par is None:
			return None
		uniform = str(name_par.eval()).strip()
		return uniform or None

	def __glslLabel(self, name):
		"""Label for a GLSL uniform name.

		Keep shader-style prefixed camelCase (a lowercase letter immediately
		followed by a capital, e.g. 'uColor', 'iCounter') untouched; otherwise
		capitalize the first letter.
		"""
		return name if re.match(r'^[a-z][A-Z]', name) else name.capitalize()

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
			if isinstance(dropParam, ParGroupPulse) or isinstance(dropParam, ParGroupUnit):
				dropParam = dropParam[0]
			details['par'] = dropParam
			style = dropParam.style
			default = dropParam.default
			is_num = style in self.__parNumTypes
			details['isNum'] = is_num
			self.popDialog.par.Minmaxentryarea = is_num

		glsl_name = self.__glslUniformName(dropParam)
		textEntries = [self.purgeParName(glsl_name) if glsl_name else dropParam.name.capitalize(), self.__glslLabel(glsl_name) if glsl_name else '']
		if is_num:
			_max = dropParam.normMax
			if dropParam.name == 'index':
				_owner = dropParam.owner
				if _owner.inputs: # if it's a table
					_max = len(_owner.inputs) - 1
			
			textEntries.extend([dropParam.normMin, _max])
			textEntries.append(default)

		self.popDialog.Open(callback=self.OnCustomizeCallback, details=details, textEntries=textEntries)

	def OnCustomizeCallback(self, info):
		if info['buttonNum'] != 1:
			return
		
		details = info['details']
		parGroup = details.get('parGroup', None)
		par = details.get('par', None)
		if isinstance(par, ParGroupPulse) or isinstance(par, ParGroupUnit):
			par = par[0]
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


