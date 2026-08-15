
'''Info Header Start
Name : install
Author : root
Saveorigin : FunctionStore_tools_2025_DEV.16.toe
Saveversion : 2025.33070
Info Header End'''
targets = [op('/ui/dialogs/mainmenu')]
#
# projname is published through the MainMenuRegistry host now (side left);
# the legacy direct-copy injection ships nothing.
containers = []
containers = sorted(containers, key=lambda x: x.nodeX)
for target in targets:
	for i, cont in enumerate(containers):
		if _op := target.op(cont.name):
			_op.destroy()
		newOP = target.copy(cont)
		newOP.nodeX = 500 + i*200
		newOP.nodeY = -400
		try:
			newOP.inputCOMPConnectors[0].connect(target.op('emptypanel').outputCOMPConnectors[0])
		except:
			pass
		newOP.allowCooking = True
		
ui.status = 'Function Store - Navbar installed'