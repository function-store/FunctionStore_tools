CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class ExtQuickCollapse:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.popDialog = ownerComp.op('popDialog')
		self.newCOMP = None
		self.selected = None

	def undoCollapse(self, isUndo, _return):
		ui.panes.current.owner = _return
		pass
	
	def OnCollapse(self, customize=False):
		self.selected = ui.panes.current.owner.selectedChildren
		if not self.selected:
			return

		if customize:
			self.popDialog.Open(callback=self.OnCustomizeCallback)
			return
		else:
			self.collapse()
		pass

	def collapse(self, _name=None, _shortcut=None):
		ui.undo.startBlock('Collapsing')
		ui.undo.addCallback(self.undoCollapse, info = ui.panes.current.owner)
		self.selected[0].parent().collapseSelected()
		self.newCOMP = ui.panes.current.owner.currentChild

		if not self.newCOMP:
			ui.undo.endBlock()
			return
		
		if _name:
			self.newCOMP.name = _name
		if _shortcut:
			self.newCOMP.par.parentshortcut = _shortcut

		ui.panes.current.owner = self.newCOMP
		ui.undo.endBlock()



	def OnCustomizeCallback(self, info):
		if info['buttonNum'] == 1:
			self.collapse(_name=info['enteredText'][0], _shortcut=info['enteredText'][1])
			

	

