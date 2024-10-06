from extUtils import CustomParHelper

class QuickParentExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.popDialog = self.ownerComp.op('popDialog')


	@property
	def paneParent(self):
		return ui.panes.current.owner
	

	def AddParentshortcut(self):
		defaultText = self.paneParent.name if self.paneParent.par.parentshortcut.eval() is None else self.paneParent.par.parentshortcut.eval()
		self.popDialog.Open(text='Add Parent Shortcut', title='Add Parent Shortcut', buttons=['OK', 'Cancel'],
			escButton=2, enterButton=1, escOnClickAway=True, textEntry=defaultText, callback=self.OnAddParentshortcutCallback)
	

	def OnAddParentshortcutCallback(self, result):
		if result['button'] == 'OK':
			parentshortcutpar = self.paneParent.par.parentshortcut
			if parentshortcutpar is not None:
				parentshortcutpar.val = result['enteredText']


