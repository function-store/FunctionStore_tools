CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class ExtQuickCollapse:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)

	def undoCollapse(self, isUndo, _return):
		ui.panes.current.owner = _return
		pass
	
	def OnCollapse(self, advanced=False):
		selected = ui.panes.current.owner.selectedChildren
		if not selected:
			return
		
		ui.undo.startBlock('Collapsing')
		ui.undo.addCallback(self.undoCollapse, info = ui.panes.current.owner)

		selected[0].parent().collapseSelected()
		
		new_comp = ui.panes.current.owner.currentChild

		if not new_comp:
			return
		
		# if advanced:


		ui.panes.current.owner = new_comp

		ui.undo.endBlock()
		pass

	
