import re

class ExtOpToClipboard:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self._op_ref = None
		# Define the regular expression pattern with a capturing group, we choose @ as the delimiter
		self.patternize = lambda _opname: f"op('{_opname}')@"
		self.regex = lambda _op_ref: rf".*(op\('({re.escape(_op_ref)})'\)\@).*" 
		self.mod = self.ownerComp.op('null_mod')

	def OnCopy(self):
		if _op := ui.panes.current.owner.currentChild:
			ui.clipboard = self.patternize(_op.name)
			self._op_ref = _op

	def OnRolloverPar(self, _op_str, _par_str, _expr):
		_op = op(_op_str)
		if not _op:
			return
		_par = op(_op_str).par[_par_str]
		if _par.mode in [ParMode.EXPRESSION, ParMode.CONSTANT] and _expr != 'None':
			if self._op_ref and (_to_replace := self.__checkExprReplace(_expr)):
				if not self.mod['shift'].eval():
					shortcut = f"op('{_op.relativePath(self._op_ref)}')"
				else:
					# RFE: this is a workaround to get the shortcut path of the op
					# so this kinda sucks since keyboardin DAT/CHOP is not working during text input,
					# so if you want to use this feature, you need to move your cursor out of the text input field before pasting
					# then paste the expression,
					# and then press enter or click away to stop text ipnut, 
					# and then press shift and hover over the parameter
					shortcut = _op.shortcutPath(self._op_ref)
				if shortcut:
					_par.expr = _par.expr.replace(_to_replace, shortcut)
				pass

	
	def __checkExprReplace(self, _expr):

		pattern = self.regex(self._op_ref.name)
		
		# Use re.match to check if _expr matches the pattern
		match = re.match(pattern, _expr)
		# If there's a match
		if match:
			return match.group(1)
		
		# If no match, return None
		return False

