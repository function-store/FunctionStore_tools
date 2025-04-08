
import re

class extExprHotString:
	"""
	extExprHotString description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.opShortStr = '#@'
		self.hotstrings = op('ExprHotStrings_tab')
	
	def opWrap(self, text):
		# Handling the #@something@ case
		text = re.sub(r'#@([a-zA-Z0-9_/]+)@', r"op('\1')", text)
		
		# Handling the case where dot appears immediately after #@
		text = re.sub(r'#@(\./[a-zA-Z0-9_]+)', r"op('\1')", text)
		
		# Handling the .something case
		dot_match = re.search(r'#@([a-zA-Z0-9_/]+)\.([a-zA-Z0-9_]+)', text)
		if dot_match:
			main_text, dot_text = dot_match.groups()
			text = text.replace(dot_match.group(0), f"op('{main_text}').{dot_text}")
		
		# Default handling
		text = re.sub(r'#@([a-zA-Z0-9_/]+)', r"op('\1')", text)
		
		return text
	
	def can_transform_pattern(self, text):
		# Check if text is inside single or double quotes
		single_quote_match = re.search(r"'[^']*#@[^']*'", text)
		double_quote_match = re.search(r'"[^"]*#@[^"]*"', text)
		
		# If inside f-string, allow transformation inside curly braces
		if text.startswith("f'") or text.startswith('f"'):
			f_string_match = re.search(r'f[\'"][^\'"]*{[^}]*#@[^}]*}[^\'"]*[\'"]', text)
			return f_string_match is not None
		elif single_quote_match is not None or double_quote_match is not None:
			return True
		else:
			# Return True if #@ pattern is present and not inside any string
			return '#@' in text


	def HotstringCheck(self, OP, PAR, EXPR, BINDEXPR):
		op_par = op(OP).par[PAR]
		if op_par.mode == ParMode.BIND:
			EXPR = BINDEXPR
		if op_par is None:
			return
		if op_par.mode in [ParMode.EXPRESSION, ParMode.CONSTANT, ParMode.BIND] and EXPR != 'None':
			expands = None

			if self.ownerComp.par.Openable.eval():
				if self.opShortStr in EXPR:
					if self.can_transform_pattern(EXPR):
						expands = EXPR = self.opWrap(EXPR)

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
	