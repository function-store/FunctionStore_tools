'''Info Header Start
Name : QuickParentExt
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
class QuickParentExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.popDialog = self.ownerComp.op('popDialog')
		self.paneParent = None

	

	def AddParentshortcut(self, _target):
		self.paneParent = _target
		defaultText = self.paneParent.name if self.paneParent.par.parentshortcut.eval() == '' else self.paneParent.par.parentshortcut.eval()
		self.popDialog.Open(text='Add Parent Shortcut', title='Add Parent Shortcut', buttons=['OK', 'Cancel'],
			escButton=2, enterButton=1, escOnClickAway=True, textEntry=defaultText, callback=self.OnAddParentshortcutCallback)
	

	def OnAddParentshortcutCallback(self, result):
		if result['button'] == 'OK':
			if self.paneParent is not None:
				parentshortcutpar = self.paneParent.par.parentshortcut
				if parentshortcutpar is not None:
					parentshortcutpar.val = result['enteredText']


