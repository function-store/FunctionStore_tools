import re
import TDFunctions as TDF

class extExprHotString:
	"""
	extExprHotString description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.opShortStr = '#@'
		self.parentShortStr = '#!'
		self.parentPromoteShortStrBind = '#@!'
		self.parentPromoteShortStrExpr = '#@~'
		self.hotstrings = self.ownerComp.op('ExprHotStrings_tab')
		self.customParPromoter = op.FNS_CPP
	
	def opWrap(self, text):
		# Handling the #@something@ case
		# Examples:
		# #@something@ -> op('something')
		# #@.something@ -> op('something')
		text = re.sub(r'#@\.?([a-zA-Z0-9_/]+)@', r"op('\1')", text)
		
		# # Handling the case where dot appears immediately after #@
		# text = re.sub(r'#@(\./[a-zA-Z0-9_]+)', r"op('\1')", text)
		
		# Handling the .something case
		# Examples:
		# #@something.else -> op('something').else
		# #@.something.else -> op('something').else
		dot_match = re.search(r'#@\.?([a-zA-Z0-9_/]+)\.([a-zA-Z0-9_]+)', text)
		if dot_match:
			main_text, dot_text = dot_match.groups()
			text = text.replace(dot_match.group(0), f"op('{main_text}').{dot_text}")
		
		# Default handling
		# Examples:
		# #@something -> op('something')
		# #@.something -> op('something')
		text = re.sub(r'#@\.?([a-zA-Z0-9_/]+)', r"op('\1')", text)
		
		return text
	
	def parentWrap(self, _op, text):
		_parent = self.closestParent(_op)
		# Handle parameter reference case first (#!!)
		# Examples:
		# #!!something -> parent.par.something
		# #!!.something -> parent.par.something
		# #!! -> parent.par
		text = re.sub(r'#!!(\.?)(.*)', lambda m: f"{_parent}.par{m.group(1) or ('.' if m.group(2).strip() else '')}{m.group(2)}", text)
		
		# Then handle normal case
		# Examples:
		# #!something -> parent.something
		# #!.something -> parent.something
		# #! -> parent
		text = re.sub(r'#!(\.?)(.*)', lambda m: f"{_parent}{m.group(1) or ('.' if m.group(2).strip() else '')}{m.group(2)}", text)
		return text

	def parentPromoteWrap(self, _par, text):
		"""
		Handle parameter promotion with different binding modes:
		- #@! -> promotes parameter with refBind=True (bind mode)
		- #!@ -> promotes parameter with refBind=False (expression mode)
		"""
		current_op = _par.owner
		_parent = current_op.parent()

		# Determine binding mode based on which pattern is present
		if self.parentPromoteShortStrBind in text:
			refBind = True
			pattern = re.escape(self.parentPromoteShortStrBind) + r'(\.?)(.*)'
		elif self.parentPromoteShortStrExpr in text:
			refBind = False
			pattern = re.escape(self.parentPromoteShortStrExpr) + r'(\.?)(.*)'
		else:
			return text

		# Find the pattern in the text
		match = re.search(pattern, text)
		if not match:
			return text
			
		dot_prefix = match.group(1)  # Optional leading dot
		param_name = match.group(2)  # Parameter name after #@! or #!@
		
		# If no parameter name provided, use current parameter
		if not param_name.strip():
			param_name = _par.name
		else:
			# Remove leading dot if present
			param_name = param_name.lstrip('.')
		
		_pg = _par.parGroup

		if _pg is not None:
			# Set reference for the custom parameter promoter
			self.customParPromoter.Reference = current_op.path
			self.customParPromoter.Target = _parent.path
			# if _par.mode in [ParMode.EXPRESSION, ParMode.CONSTANT]:
			# 	_par.expr = ''
			# elif _par.mode in [ParMode.BIND]:
			# 	_par.bindExpr = ''
			# Do the actual promotion
			if len(_pg) > 1:
				created_par = self.customParPromoter.PromoteParGroup(_pg, None, target=_parent, parName=param_name, refBind=refBind)
			else:
				# had to do this otherwise we got weird bugs
				created_par = self.customParPromoter.PromotePar(_pg[0], None, target=_parent, parName=param_name, refBind=refBind)
			
			# Generate shortcut path to the created parameter
			shortcut_path = TDF.getShortcutPath(current_op, _parent, toParName=created_par.name)
			
			# Replace the specific pattern with the shortcut path
			text = re.sub(pattern, shortcut_path, text)
		
		return ''

	
	def can_transform_pattern(self, text, check = '#@'):
		# Check if text is inside single or double quotes
		single_quote_match = re.search(r"'[^']*" + check + r"[^']*'", text)
		double_quote_match = re.search(r'"[^"]*' + check + r'[^"]*"', text)
		
		# If inside f-string, allow transformation inside curly braces
		if text.startswith("f'") or text.startswith('f"'):
			f_string_match = re.search(r'f[\'"][^\'"]*{[^}]*' + check + r'[^}]*}[^\'"]*[\'"]', text)
			return f_string_match is not None
		elif single_quote_match is not None or double_quote_match is not None:
			return True
		else:
			# Return True if #@ pattern is present and not inside any string
			return check in text


	def HotstringCheck(self, OP, PAR, EXPR, BINDEXPR):
		if OP == 'None':
			return
		op_par = op(OP).par[PAR]
		_mode = op_par.mode
		if op_par.mode == ParMode.BIND:
			EXPR = BINDEXPR
		if op_par is None:
			return
		if op_par.mode in [ParMode.EXPRESSION, ParMode.CONSTANT, ParMode.BIND] and EXPR != 'None':
			expands = None

			if self.ownerComp.par.Openable.eval() and self.opShortStr in EXPR and self.can_transform_pattern(EXPR, self.opShortStr):
				expands = EXPR = self.opWrap(EXPR)
			if self.ownerComp.par.Parentshortcutenable.eval() and self.parentShortStr in EXPR and self.can_transform_pattern(EXPR, self.parentShortStr):
				expands = EXPR = self.parentWrap(OP, EXPR)
			if self.ownerComp.par.Customparpromoteenable.eval() and (self.parentPromoteShortStrBind in EXPR or self.parentPromoteShortStrExpr in EXPR) and (self.can_transform_pattern(EXPR, self.parentPromoteShortStrBind) or self.can_transform_pattern(EXPR, self.parentPromoteShortStrExpr)):
				expands = EXPR = self.parentPromoteWrap(op_par, EXPR)

			if self.ownerComp.par.Replaceinline:
				# match longest abbreviation first
				abvs = [(cell.row, cell.val) for cell in self.hotstrings.col('Abbreviation')[1:]]
				if not abvs:
					return
				abvs.sort(key=lambda x: len(x[1]),reverse=True)
				abbreviation = [s for s in abvs if s[1] in EXPR]
				
				if abbreviation:
					abbreviation = abbreviation[0]
					expands = self.hotstrings.cell(abbreviation[0], 'Expands', val=True)
					if expands is None or expands == '':
						return
					expands = re.sub(abbreviation[1], expands, EXPR)

			else:
				hotstring = self.hotstrings.findCell(EXPR, cols = ['Abbreviation'], valuePattern=False, caseSensitive=True)
				if hotstring:
					expands = self.hotstrings.cell(hotstring.row, 'Expands', val=True)
					
			if expands:
				# replace 
				if op_par.mode == ParMode.BIND:
					op_par.bindExpr = expands
				else:
					op_par.expr = expands
				# recurse in case multiple abbreviations were used
				self.HotstringCheck(OP,PAR,expands, expands)
	

	def closestParent(self, _op):
		# Start with the given operator
		current_op = op(_op)
		visited = set()  # Keep track of visited operators to prevent loops
		
		while current_op:
			# Add current operator to visited set
			visited.add(current_op.path)
			
			# Get parent
			parent = current_op.parent()
			if not parent:
				return 'parent()'
				
			# Check if we've already visited this parent
			if parent.path in visited:
				return 'parent()'
				
			# Check for parent shortcut
			if _shortcut := parent.par.parentshortcut.eval():
				return f'parent.{_shortcut}'
				
			# Move up to next parent
			current_op = parent
			
		return 'parent()'
