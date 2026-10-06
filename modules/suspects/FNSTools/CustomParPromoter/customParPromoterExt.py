
'''Info Header Start
Name : customParPromoterExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
import re
import TDFunctions as TDF

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
		self._ensureModulePars()
		# The registry hosts are not usable during __init__, and a TDXN import
		# can still replace children after it, so the surface pass is deferred.
		# Resolved by shortcut at call time, never a cached self -- that goes
		# stale on the next source save.
		try:
			run('op.FNS_CPP.ext.customParPromoterExt.applyModuleGates()',
				delayFrames=30, delayRef=op.TDResources)
		except Exception:
			pass
		fnsLog('CustomParPromoter: init')

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

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
		fnsLog(f'CustomParPromoter: promoting all pars of page "{_page.name}" from {self.Reference.path}')

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
			# Carried AFTER the last .val write: assigning .val flips the mode
			# back to CONSTANT, which is what undid the carried expression.
			self._carryParMode(p, new_p, target)
			if not refBind:
				p.expr = f"{self.Reference.shortcutPath(target)}.par.{new_p.name}"
				p.mode = ParMode.EXPRESSION
			else:
				p.bindExpr = f"{self.Reference.shortcutPath(target)}.par.{new_p.name}"
				p.mode = ParMode.BIND
		ui.undo.endBlock()
		fnsLog(f'CustomParPromoter: promoted parGroup "{name}" to {target.path}')
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
		# Carried AFTER the last .val write: assigning .val flips the mode
		# back to CONSTANT, which is what undid the carried expression.
		self._carryParMode(_par, new_par[0] if hasattr(new_par, 'pars') else new_par, target)
		if not refBind:
			_par.expr = f"{self.Reference.shortcutPath(target)}.par.{new_par.name}"
			_par.mode = ParMode.EXPRESSION
		else:
			_par.bindExpr = f"{self.Reference.shortcutPath(target)}.par.{new_par.name}"
			_par.mode = ParMode.BIND
		ui.undo.endBlock()
		fnsLog(f'CustomParPromoter: promoted par "{name}" to {target.path}')
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

	# --- carrying an expression or bind across a promotion ------------------
	#
	# appendPar(par=...) copies the definition, never the mode: a promoted
	# parameter came out in CONSTANT mode holding the constant-mode value,
	# and whatever expression or bind the original had was overwritten a
	# line later when the original was rewired to the new parameter. The
	# expression now moves UP with the parameter. It was authored on the
	# reference, so every relative reference in it is rebased to resolve
	# the same operator from the target.

	# One match per relative reference an expression can carry. The
	# lookbehind keeps `.op(` (a method on some other operator) and `.me`
	# out; op('...') is tried first so a `me` inside its string is never
	# matched on its own.
	_REF_TOKEN = re.compile(r"""
		(?<![\w.])(?P<fn>op|mod)\(\s*(?P<q>['"])(?P<path>[^'"]*)(?P=q)\s*\)
		| (?<![\w.])parent\(\s*(?P<depth>\d*)\s*\)
		| (?<![\w.])(?P<sc>parent|iop|ipar)\.(?P<name>[A-Za-z_]\w*)
		| (?<![\w.])me\b
		""", re.VERBOSE)

	def _carryParMode(self, old_par, new_par, target):
		"""Move old_par's expression or bind onto new_par, rebased to target.

		Call it BEFORE old_par is rewired to point at new_par. Constant and
		export modes carry nothing. Returns True when the mode was carried;
		on any failure new_par keeps a constant value, set to the live value
		of the original, and the reason is logged.
		"""
		mode = old_par.mode
		if mode == ParMode.EXPRESSION:
			attr, text = 'expr', old_par.expr
		elif mode == ParMode.BIND:
			attr, text = 'bindExpr', old_par.bindExpr
		else:
			return False
		if not text:
			return False
		rebased = self._rebaseExpression(text, old_par.owner, target)
		if rebased is not None:
			try:
				setattr(new_par, attr, rebased)
				new_par.mode = mode
				fnsLog(f'CustomParPromoter: carried {attr} of {old_par.owner.path}.{old_par.name} '
					   f'to {target.path}.{new_par.name}: {text!r} -> {rebased!r}')
				return True
			except Exception as e:
				reason = f'{type(e).__name__}: {e}'
		else:
			reason = 'a reference in it could not be resolved from the target'
		try:
			new_par.mode = ParMode.CONSTANT
			new_par.val = old_par.eval()
		except Exception:
			pass
		msg = (f'CustomParPromoter: could not carry the {attr} of '
			   f'{old_par.owner.path}.{old_par.name} ({text!r}) to {target.path}: {reason}. '
			   f'The promoted parameter holds the value instead.')
		fnsLog(msg, level='WARNING')
		debug(msg)
		return False

	def _rebaseExpression(self, expr, source, target):
		"""Rewrite expr, authored on source, to resolve the same operators from target.

		Every relative reference (op('..'), mod('..'), me, parent(), parent.X,
		iop.X, ipar.X) is resolved by evaluating it in the SOURCE's context --
		TouchDesigner's own resolution, never a hand-parsed path -- and
		re-expressed with target.shortcutPath(found), which yields `me` for the
		target itself, a parent/global shortcut where one applies, and a
		relative path otherwise. The result is then checked by evaluating both
		expressions and comparing; returns None when a reference does not
		resolve or the two disagree.
		"""
		unresolved = []

		def found(sub):
			try:
				return source.evalExpression(sub)
			except Exception:
				return None

		def repl(m):
			text = m.group(0)
			fn = m.group('fn')
			if fn == 'mod':
				dat = found("op(%r)" % m.group('path'))
				if not isinstance(dat, OP):
					unresolved.append(text)
					return text
				return "mod(%r)" % target.relativePath(dat)
			if m.group('sc') == 'ipar':
				host = found('iop.' + m.group('name'))
				if not isinstance(host, OP):
					unresolved.append(text)
					return text
				return target.shortcutPath(host) + '.par'
			resolved = source if text == 'me' else found(text)
			if not isinstance(resolved, OP):
				unresolved.append(text)
				return text
			return target.shortcutPath(resolved)

		rebased = self._REF_TOKEN.sub(repl, expr)
		if unresolved:
			fnsLog(f'CustomParPromoter: unresolved in {expr!r}: {unresolved}', level='WARNING')
			return None
		# Verify: same value from both sides. An original that already fails
		# to evaluate is carried as-is -- the user keeps the error they had.
		try:
			expected = self._evalKey(source.evalExpression(expr))
		except Exception:
			return rebased
		try:
			actual = self._evalKey(target.evalExpression(rebased))
		except Exception as e:
			fnsLog(f'CustomParPromoter: rebased {rebased!r} does not evaluate from {target.path}: {e}', level='WARNING')
			return None
		if expected != actual:
			fnsLog(f'CustomParPromoter: rebased {rebased!r} evaluates to {actual!r}, original {expr!r} to {expected!r}', level='WARNING')
			return None
		return rebased

	@staticmethod
	def _evalKey(value):
		"""A comparable stand-in for an expression's value: operators by path,
		parameters by owner and name, everything else by value."""
		if isinstance(value, OP):
			return ('op', value.path)
		if isinstance(value, Par):
			return ('par', value.owner.path, value.name)
		try:
			return ('num', float(value))
		except Exception:
			return ('str', str(value))

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
		
	def _customizeFallbackLabel(self):
		"""What an empty Label field in the customize dialog stands for: the
		label of the parameter being promoted (its shader name on a GLSL
		vector), and only when that is blank the name typed in the dialog."""
		details = getattr(self, '_pendingCustomize', None) or {}
		return details.get('sourceLabel') or self.__saveParamNameBeforePurge

	def onFocus(self, field, comp):
		if field == 'label' and comp.editText == '':
			fallback = self._customizeFallbackLabel()
			if fallback:
				self.popDialog.op('entry2/inputText').par.text = fallback

	def onFocusEnd(self, field, comp):
		if field == 'paramname':
			text = comp.editText
			self.__saveParamNameBeforePurge = text
		elif field == 'label':
			if comp.editText == '':
				fallback = self._customizeFallbackLabel()
				if fallback:
					comp.par.text = fallback
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
		# The Label field opens showing the label the promoted parameter will
		# get -- the source parameter's own label -- so what is on screen is
		# what OK produces; clearing it falls back to the same label.
		source_label = self.__glslLabel(glsl_name) if glsl_name else str(dropParam.label)
		details['sourceLabel'] = source_label
		textEntries = [self.purgeParName(glsl_name) if glsl_name else dropParam.name.capitalize(), source_label]
		if is_num:
			_max = dropParam.normMax
			if dropParam.name == 'index':
				_owner = dropParam.owner
				if _owner.inputs: # if it's a table
					_max = len(_owner.inputs) - 1
			
			textEntries.extend([dropParam.normMin, _max])
			textEntries.append(default)

		# Keep the customize context HERE: this extension is stable, while
		# PopDialogExt re-initializes (losing its self.details) -- see the
		# fallback in OnCustomizeCallback. No callback arg: the dialog's
		# docked callbacks DAT routes onSelect back to us, and that DAT
		# lookup survives extension reinits where an assigned callback dies.
		self._pendingCustomize = details
		self.popDialog.Open(details=details, textEntries=textEntries)

	def OnCustomizeCallback(self, info):
		if info['buttonNum'] != 1:
			return

		# info['details'] is PopDialogExt instance state and reads None when
		# that extension re-initialized between Open and OK; fall back to the
		# context we kept on THIS (stable) extension.
		details = info.get('details') or getattr(self, '_pendingCustomize', None)
		if details is None:
			debug('CustomParTools: customize context lost -- drop the parameter again')
			return
		parGroup = details.get('parGroup', None)
		par = details.get('par', None)
		if isinstance(par, ParGroupPulse) or isinstance(par, ParGroupUnit):
			par = par[0]
		is_num = details.get('isNum', False)

		labelEntry = info['enteredText'][1]
		nameEntry = info['enteredText'][0]
		
		if not labelEntry:
			labelEntry = details.get('sourceLabel') or nameEntry
		nameEntry = self.purgeParName(nameEntry)
		def _num(v):
			# blank/invalid entry means "leave unset" -- float('') raised here
			# and the swallowed ValueError made OK silently do nothing
			try:
				return float(v)
			except (TypeError, ValueError):
				return None
		minEntry = _num(info['enteredText'][2]) if is_num else None
		maxEntry = _num(info['enteredText'][3]) if is_num else None
		chekcboxClamp = info['checkBoxes']
		default = info['enteredText'][4] if is_num and info['enteredText'][4] not in (None, '') else None
		
		if parGroup is not None:
			self.PromoteParGroup(parGroup, None, parName=nameEntry, parLabel=labelEntry)
		elif par is not None:
			self.PromotePar(par, None, parName=nameEntry, parLabel=labelEntry, parMin=minEntry, parMax=maxEntry, clamp=chekcboxClamp, parDefault=default)


	def SetTableMenu(self, _table, _target):
		fnsLog(f'CustomParPromoter: creating table menu par from {_table.path} on {_target.path}')
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



	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Promote pars of selected', context='selected')
	def PromoteSelected(self):
		"""Promote custom parameters of the selected operators."""
		self.ownerComp.par.Promote.pulse()
		return {'ok': True}


	### Modules page -- per-sub-module Active switches ###

	# name, label, default, startSection, help
	_MODULE_PARS = (
		('Activeparpromote', 'Parameter Promotion', True, True,
		 'Drop a parameter onto the CustomParTools button to promote it onto '
		 'the current network COMP. The core action of the tool.'),
		('Activequickext', 'QuickExt', True, False,
		 'Create an extension on the current COMP from the button.'),
		('Activequickparent', 'QuickParent', True, False,
		 'Set a parent shortcut on the current COMP from the button.'),
		('Activeclearpars', 'ClearPars', True, False,
		 'Alt-click (Cmd on macOS) the button to clear the custom parameters '
		 'of the current child.'),
		('Activeioppromoter', 'IOP Promoter', True, False,
		 'Hold the modifier while dropping an operator on the button to '
		 'promote it as an Internal OP instead of promoting parameters.'),
		('Activehijackdragdrop', 'Navbar Drag/Drop', True, True,
		 'Accept operator and parameter drops anywhere on the pane navigation '
		 'bar. Off UNREGISTERS the widget, removing it from every bar.'),
		('Activepathcellclickinject', 'Navbar Path Cell Click', True, False,
		 'Open parameters for the operator whose path cell you click in the '
		 'pane bar. Off UNREGISTERS the widget, removing it from every bar.'),
		('Activequickparcustom', 'QuickParCustom', True, True,
		 "Rollover hotkeys for promoting and customizing the parameter under "
		 "the mouse. Bound to QuickParCustom's own Active switch."),
		('Activetdshortcuts', 'Parameter/Editor Hotkeys', True, False,
		 'The four stock-TouchDesigner hotkeys on the Custom page (open '
		 'parameters, open component editor). Off deactivates the keyboardins; '
		 'the matching quick-launch commands stay available.'),
	)

	# Everything whose only front door is button_custompar_tools. With all of
	# these off the button has nothing left to do, so the package leaves the
	# navbar and the toolbar outright. FNS_ConfigRegistry is deliberately NOT
	# in this cascade: it carries no surface, and it is what persists these
	# very toggles -- unregistering it would discard the setting that asked
	# for the unregistration.
	_BUTTON_MODULE_PARS = ('Activeparpromote', 'Activequickext',
						   'Activequickparent', 'Activeclearpars',
						   'Activeioppromoter')

	def ModuleEnabled(self, module):
		"""True when `module` is switched on, on the Modules page.

		`module` is the sub-module's operator name -- ModuleEnabled('QuickExt'),
		ModuleEnabled('iopPromoter') -- lowercased onto its Enable* parameter.

		Fails OPEN: a missing parameter reports enabled. FNS_NavbarRegistry
		COPIES button_custompar_tools into every pane bar, so those copies call
		this from OUTSIDE the package (which is why it is promoted), and must
		not go dead against a CustomParTools with no Modules page.
		"""
		p = self.ownerComp.par['Active' + str(module).lower()]
		return True if p is None else bool(p.eval())

	def _ensureModulePars(self):
		"""Get-or-create the Modules page. Never destroys, never overwrites a value."""
		c = self.ownerComp
		page = None
		for pg in c.customPages:
			if pg.name == 'Modules':
				page = pg
				break
		if page is None:
			page = c.appendCustomPage('Modules')
		for name, label, default, section, help_ in self._MODULE_PARS:
			p = c.par[name]
			if p is None:
				p = page.appendToggle(name, label=label)[0]
				p.val = default
			p.default = default
			p.label = label
			p.help = help_
			p.startSection = section

	def _setSurfaceRegistration(self, comp, prefix, on):
		"""Register or unregister one surface host ('Nb' navbar, 'Tb' toolbar).

		Autoregister on its own is not an off switch -- it only decides what
		happens at init -- so the Register/Unregister pulse has to follow it for
		the change to reach the live bars. Writes nothing when the state already
		matches, so an extension reinit does not churn the surface.
		"""
		auto = comp.par[prefix + 'autoregister']
		act = comp.par[prefix + ('register' if on else 'unregister')]
		if auto is None or act is None:
			return False
		if bool(auto.eval()) == bool(on):
			return False
		auto.val = bool(on)
		act.pulse()
		fnsLog('CustomParPromoter: %s %s%s' % (
			comp.name, prefix, 'register' if on else 'unregister'))
		return True

	def applyModuleGates(self):
		"""Push the Modules toggles onto everything they gate but do not own.

		The click and drop paths ask ModuleEnabled() at call time, so they need
		nothing from here. What needs pushing is state owned by ANOTHER
		operator: a disabled module has to LEAVE its surface, not merely
		decline to act.
		"""
		c = self.ownerComp

		# QuickParCustom already ships its own Active toggle, and a quick-launch
		# command with state='Active' that writes to it. BIND rather than push,
		# so a write from either side lands on one value and the two cannot
		# drift apart.
		qpc = c.op('QuickParCustom')
		if qpc is not None and qpc.par['Active'] is not None:
			want = 'parent.PAR_PROMOTER.par.Activequickparcustom'
			if (qpc.par.Active.bindExpr != want
					or qpc.par.Active.mode != ParMode.BIND):
				qpc.par.Active.bindExpr = want
				qpc.par.Active.mode = ParMode.BIND

		# the four stock-TD hotkeys: an expression tracks the toggle forever,
		# where a pushed value goes stale the next time anything sets it.
		want = 'parent.PAR_PROMOTER.par.Activetdshortcuts'
		for k in c.children:
			if k.OPType != 'keyboardinDAT':
				continue
			if (k.par.active.expr != want
					or k.par.active.mode != ParMode.EXPRESSION):
				k.par.active.expr = want
				k.par.active.mode = ParMode.EXPRESSION

		# exclusive surfaces: each of these owns its own navbar host, so its
		# toggle is a straight register/unregister.
		for name, parname in (('hijack_dragdrop', 'Activehijackdragdrop'),
							  ('PathCellClickInject', 'Activepathcellclickinject')):
			sub = c.op(name)
			p = c.par[parname]
			if sub is not None and p is not None:
				self._setSurfaceRegistration(sub, 'Nb', bool(p.eval()))

		# the shared surface.
		live = [c.par[n] for n in self._BUTTON_MODULE_PARS]
		button_on = any(bool(p.eval()) for p in live if p is not None)
		for prefix in ('Nb', 'Tb'):
			self._setSurfaceRegistration(c, prefix, button_on)
