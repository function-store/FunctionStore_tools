CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class ExtQuickCollapse:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.popDialog = ownerComp.op('popDialog')
		self.newCOMP = None

	def undoCollapse(self, isUndo, _return):
		ui.panes.current.owner = _return
		pass
	
	def OnCollapse(self, customize=False):
		selected = ui.panes.current.owner.selectedChildren
		if not selected:
			return
		
		ui.undo.startBlock('Collapsing')
		ui.undo.addCallback(self.undoCollapse, info = ui.panes.current.owner)

		selected[0].parent().collapseSelected()
		
		self.newCOMP = ui.panes.current.owner.currentChild

		if not self.newCOMP:
			return
		
		if customize:
			self.popDialog.Open(callback=self.OnCustomizeCallback)
			ui.undo.endBlock()
			return

		ui.panes.current.owner = self.newCOMP
		ui.undo.endBlock()
		pass

	def OnCustomizeCallback(self, info):
		_name = info['enteredText'][0]
		_shortcut = info['enteredText'][1]

		if _name:
			self.newCOMP.name = _name
		if _shortcut:
			self.newCOMP.par.parentshortcut = _shortcut

		ui.panes.current.owner = self.newCOMP

	

