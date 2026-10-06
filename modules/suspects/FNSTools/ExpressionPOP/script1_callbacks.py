# me - this DAT
# scriptOp - the OP which is cooking
#
# press 'Setup Parameters' in the OP to call this function to re-create the parameters.


import re

def onSetupParameters(scriptOp):
	page = scriptOp.appendCustomPage('Custom')
	p = page.appendFloat('Valuea', label='Value A')
	p = page.appendFloat('Valueb', label='Value B')
	return

# called whenever custom pulse parameter is pushed
def onPulse(par):
	return




def make_glsl_define(idx, leftSide, rightSide, leftMode=0):
	define_name = f'POP_EXPRESSION_{idx}'
	define_text = f'#define {define_name}'
	if leftMode == 0:
		define_expression = f'{leftSide}[id] = ({rightSide})'
	else: 
		define_expression = f'{leftSide} = {rightSide}'
	return (define_name, define_text, define_expression)


def onCook(scriptOp):
	code = """
<INSERT DEFINES HERE>
void main() {
	const uint id = TDIndex();
	if(id >= TDNumElements())
		return;
		
	<SUBSTITUTE_EXPRESSIONS_HERE>
}
		"""
	scriptOp.clear()

	inPOP = op('in1')
	inDAT : tableDAT = scriptOp.inputs[0]
	pointAttribNames = [attr.name for attr in inPOP.pointAttributes]

	inExpressions = inDAT.row('Expr_expression', val=True)[1:]
	inLeftmodes = inDAT.row('Expr_leftmode', val=True)[1:]

	# join the inExpressions and inLeftmodes into a single 2d list
	inData = [[inLeftmodes[i], inExpressions[i]] for i in range(len(inExpressions))]


	glsl_expressions = {}
	for idx, data in enumerate(inData):
		inExpression = data[1]
		if not inExpression:
			continue
		inExpression = inExpression.split('=')
		
		leftSide = inExpression[0].strip()
		rightSide = inExpression[1].strip()

		# look for the point attributes in the expression, and replace them with TD_In_*() in the expression
		# using regex word boundaries to ensure we only match complete attribute names
		for attr in pointAttribNames:
			# Use word boundaries (\b) to match complete words only
			pattern = r'\b' + re.escape(attr) + r'\b'
			replacement = f'TDIn_{attr}()'
			rightSide = re.sub(pattern, replacement, rightSide)
		define_name, define_text, define_expression = make_glsl_define(idx, leftSide, rightSide, leftMode = int(data[0]))
		glsl_expressions[define_name] = (define_text, define_expression)
	
	# V1 - using defines
	# # Insert defines with proper indentation
	# defines_text = '\n\t\t'.join(glsl_expressions.values())
	# code = code.replace('<INSERT DEFINES HERE>', defines_text)
	
	# # Insert expression calls with proper indentation and semicolons
	# expressions_text = ';\n\t\t\t'.join(glsl_expressions.keys()) + ';'
	# code = code.replace('<SUBSTITUTE_EXPRESSIONS_HERE>', expressions_text)

	# V2 - not using defines
	code = code.replace('<INSERT DEFINES HERE>', '')
	expressions_text = '\n\t'.join([f'{define_expression};' for define_text, define_expression in glsl_expressions.values()])
	code = code.replace('<SUBSTITUTE_EXPRESSIONS_HERE>', expressions_text)

	scriptOp.text = code

	return

def onGetCookLevel(scriptOp):
	"""
	sets the scriptOp's cook level, the conditions necessary to cause a cook.

	Return one of the following:
		CookLevel.AUTOMATIC - inputs changed and output being used. TD default behavior.
		CookLevel.ON_CHANGE - inputs changed, output used or not.
		CookLevel.WHEN_USED - every frame when output is being used
		CookLevel.ALWAYS - every frame
	"""

	return CookLevel.AUTOMATIC
