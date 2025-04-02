'''Info Header Start
Name : install
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.390.toe
Saveversion : 2023.11600
Info Header End'''

def inject(target_comp, target_op=None, inject_op=None, panelparent=None):
	if _op := target_comp.op(inject_op.name):
		if _op.outputConnectors:
			out_conns = _op.outputConnectors[0].connections
		else:
			out_conns = []
		_op.destroy()
	else:
		if target_op and target_op.outputConnectors:
			out_conns = target_op.outputConnectors[0].connections
		else:
			out_conns = []

	_op = target_comp.copy(inject_op)
	if target_op:
		_op.nodeX = target_op.nodeX + 150
		_op.nodeY = target_op.nodeY
	if _op.docked:
		_op.docked[0].nodeX = _op.nodeX
		_op.docked[0].nodeY = _op.nodeY - 100
	if _op.isPanel and panelparent and _op.inputCOMPConnectors:
		_op.inputCOMPConnectors[0].connect(panelparent.outputCOMPConnectors[0])

	if _op.outputConnectors and out_conns:
		for out_conn in out_conns:
			_op.outputConnectors[0].connect(out_conn.owner)
	if _op.inputConnectors and target_op:
		_op.inputConnectors[0].connect(target_op)
	_op.bypass = False
	return _op

# mark hack

clipboard_save = ui.clipboard

target_comp = op('/ui/dialogs/menu_op/nodetable')
target_op = target_comp.op('families')
inject_op = op('script_inject')
injected_op = inject(target_comp, target_op, inject_op)

# iofilter hack
target_op = injected_op
inject_op = op('IOFilter/script_IOFilter')
inject(target_comp, target_op, inject_op)

target_comp = op('/ui/dialogs/menu_op')
inject_op = op('IOFilter/radioExpose')
panelparent = target_comp.op('families')
radioExpose = inject(target_comp, target_op=None, inject_op=inject_op, panelparent=panelparent)
radioExpose.par.display = True


# right click menu hack
comp = op('/ui/dialogs/menu_op/nodetable/popMenu')

comp.par.h.expr = '18 * op("./itemsLayout").numRows'

items = comp.par.Items
items_list = eval(items.eval())
if len(items_list) <= 3:
	items_list.append('Edit Templates...')
items.val = str(items_list)

cb = 'popMenuCallbacks'

comp.parent().op(cb).text = op(cb).text

op('menu_op_compatible_mod').run()
ui.clipboard = clipboard_save