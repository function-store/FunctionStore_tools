"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
import TDFunctions as TDF

class SmoothnessExt:
	"""
	SmoothnessExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	def OnSelected(self):
		selected = ui.panes.current.owner.selectedChildren
		self.setSmoothness(selected)

	def OnAll(self):
		selected = selected = ui.panes.current.owner.ops('*')
		self.setSmoothness(selected)
		
	def setSmoothness(self, _ops):
		insmooth = parent().par.Inputfiltertype.menuIndex
		viewsmooth = parent().par.Filtertype.menuIndex
		
		tops = list(filter(lambda _op: _op.family == 'TOP' and _op.pars('inputfiltertype', 'filtertype') ,_ops))
		
		for top in tops:
			top.par.inputfiltertype = insmooth
			top.par.filtertype = viewsmooth+1 #skipping same as input
				
		comps = list(filter(lambda _op: _op.family == 'COMP' and _op.pars('Inputfiltertype', 'Filtertype'), _ops))
		for comp in comps:
			comp.par.Inputfiltertype = insmooth
			comp.par.Filtertype = viewsmooth+1 #skipping same as input
