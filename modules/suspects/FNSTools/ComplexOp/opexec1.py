# me - this DAT.
# changeOp - the operator that has changed
# 
# Make sure the corresponding toggle is enabled in the OP Execute DAT.

def onPreCook(changeOp):
	return

def onPostCook(changeOp):
	return

def onDestroy():
	return

def onFlagChange(changeOp, flag):
	return

def onWireChange(changeOp):
	# Show the wired input's resolution; enable state is the parameters'
	# enableExpr (editable only while nothing is wired in).
	if parent().inputs:
		_temp = parent().inputs[0]
		parent().parGroup.Resolution = (_temp.width, _temp.height)
	return

def onNameChange(changeOp):
	return

def onPathChange(changeOp):
	return

def onUIChange(changeOp):
	return

def onNumChildrenChange(changeOp):
	return

def onChildRename(changeOp):
	return

def onCurrentChildChange(changeOp):
	return

def onExtensionChange(changeOp, extension):
	return
	