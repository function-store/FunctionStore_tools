"""
PopMenu callbacks for TD's node-table right-click menu.

Installed into /ui/dialogs/menu_op/nodetable/popMenuCallbacks by
OpMenuRegistry. The first three items are TD's own (Help / Python Help /
Operator Snippets); everything after them was published by a registered
tool, and is dispatched back through the registry -- so no tool is named
here, and each tool's handler lives inside that tool.

Callbacks always take a single argument, which is a dictionary
of values relevant to the callback. Print this dictionary to see what is
being passed. The keys explain what each item is.

PopMenu info keys:
	'cell': either cell id or -1 for no cell
	'item': the item label in the menu list
	'row': the row from the wired dat input, if applicable
	'details': details provided by object that caused menu to open
"""

# TD's own leading items; registered items are appended after these.
BUILTIN_ITEMS = 3


def onSelect(info):
	"""
	User selects a menu option
	"""

def onRollover(info):
	"""
	Mouse rolled over an item
	"""

def onOpen(info):
	"""
	Menu opened
	"""

def onClose(info):
	"""
	Menu closed
	"""

def onMouseDown(info):
	"""
	Item pressed
	"""

def onMouseUp(info):
	"""
	Item released
	"""


def onClick(info):
	"""
	Item pressed and released
	"""
	selectedOp = op('selectedOp')

	if info['index'] == 0:
		helpName = selectedOp['help',1].val
		ui.viewFile('https://docs.derivative.ca/{0}'.format(helpName))
	elif info['index'] == 1:
		pyHelpName = selectedOp['pythonHelp',1].val
		ui.viewFile('https://docs.derivative.ca/{0}'.format(pyHelpName))
	elif info['index'] == 2:
		myOp = eval(selectedOp['snippet',1].val)
		if myOp:
			myFamily = myOp.family
			myType = myOp.OPType
			run(f"ui.openOperatorSnippets(optype='{myType}', example=1)",
								delayFrames=1, delayRef=op.TDResources)
	else:
		registry = getattr(op, 'FNS_OPMENUREGISTRY', None)
		if registry is None:
			return
		optype = selectedOp['pythonHelp',1].val
		optype = optype.split(' ')[0]
		registry.InvokeMenuItem(info['index'] - BUILTIN_ITEMS, optype)

def onLostFocus(info):
	"""
	Menu lost focus
	"""
