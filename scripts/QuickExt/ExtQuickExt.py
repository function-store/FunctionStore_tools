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

class ExtQuickExt:
	"""
	ExtExtensionCreate description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.dialog = self.ownerComp.op('popDialog')
		self.ConfigComp = None
		self.extTemplate = self.ownerComp.op('extTemplate')

	def CreateExtension(self, _target):
		if not _target:
			return
		self.ConfigComp = _target
		self.dialog.Open(textEntry='Ext')
		pass

	def getExtIndex(self):
		idx = self.ConfigComp.par.ext.sequence.numBlocks+1
		for _seqBlock in self.ConfigComp.par.ext.sequence:
				if not _seqBlock.par.object.eval():
					idx = _seqBlock.index+1
					break
		return idx

	def OnSelect(self, info):
		sel = True if info['buttonNum'] == 1 else False
		if sel and self.ConfigComp:
			extIndex = self.getExtIndex()
			extName = info['enteredText']
			extModuleName = extName
			extPar = getattr(self.ConfigComp.par, 'extension' + str(extIndex))
			extPromotePar = getattr(self.ConfigComp.par,
									'promoteextension' + str(extIndex))
			extNamePar = getattr(self.ConfigComp.par,
								'extname' + str(extIndex))
			edges = TDF.findNetworkEdges(self.ConfigComp)
			if edges:
				edgeX = edges['positions']['left']
				edgeY = edges['positions']['top']
			else:
				edgeX = 0
				edgeY = 0
			xPos = edgeX - 500 - (extIndex - 1) * 200
			yPos = edgeY

			masterExt = self.extTemplate
			masterUtils = self.ownerComp.op('extUtils')
			extDat = self.ConfigComp.copy(masterExt, name=extModuleName)
			extUtils = self.ConfigComp.copy(masterUtils, includeDocked=True)
			extUtils.dock = extDat

			extensionText = masterExt.text
			extensionText = extensionText.replace('DefaultExt',
												extModuleName)
			extDat.par.file.mode = ParMode.CONSTANT
			extDat.par.file.expr = ''
			extDat.par.file = ''
			extDat.text = extensionText
			extDat.par.language = 'python'
			extDat.nodeX = xPos
			extDat.nodeY = yPos
			extDat.viewer = True
			extDat.tags.add('TDExtension')
			extPar.val = "op('./" + extModuleName + "').module." \
						+ extModuleName + '(me)'
			extPromotePar.val = True
			extNamePar.val = ''
			extDat.docked[0].nodeX = extDat.nodeX + 150
			extDat.docked[0].nodeY = extDat.nodeY - 120
			extDat.docked[0].showDocked = True
			extDat.current = True

			self.__purgeTags(extDat)
			self.__purgeTags(extUtils)
			
			for idx, _dock in enumerate(extUtils.docked):
				_dock.nodeX = extUtils.nodeX
				_dock.nodeY = extUtils.nodeY - 120 * (idx + 1)
				_dock.showDocked = False
				self.__purgeTags(_dock)
				if hasattr(_dock.par, 'file'):
					_dock.par.file.mode = ParMode.CONSTANT
					_dock.par.file.expr = ''
					_dock.par.file = ''
			
			self.ConfigComp.par.reinitextensions.pulse()
			# fin

	def __purgeTags(self, _op):
		TAGS_TO_REMOVE = ['FNS_externalized', 'pi_suspect']
		for _tag in TAGS_TO_REMOVE:
			if _tag in _op.tags:
				_op.tags.remove(_tag)

	def OnOpen(self, info):
		pass

	def OnClose(self, info):
		pass
