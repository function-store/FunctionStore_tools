
from TDStoreTools import StorageManager
import TDFunctions as TDF
import copy

class ExtQuickExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.dialog = self.ownerComp.op('popDialog')
		self.ConfigComp = None
		self.extTemplate = self.ownerComp.op('extTemplate')
		self.stubser = self.ownerComp.op('stubser')
		self.my_ext_type = 'QuickExt'
		self.MY_FORCED_TAG = f'# DO NOT REMOVE, used by {self.my_ext_type} to inject extension'
		self.__modifyCompEditor()

	def __modifyCompEditor(self):
		compEditor = op.TDDialogs.op('CompEditor')

		# copy self.extTemplate to compEditor as lower case self.my_ext_type+ExtensionText
		if not compEditor.op(self.my_ext_type.lower()+"ExtensionText"):
			new_ext = compEditor.copy(self.extTemplate, name=self.my_ext_type.lower()+"ExtensionText")
			new_ext.nodeY = compEditor.op('emptyExtensionText').nodeY - new_ext.nodeHeight - 20
			new_ext.nodeX = compEditor.op('emptyExtensionText').nodeX
			# erase file par value
			if hasattr(new_ext.par, 'file'):
				new_ext.par.file.mode = ParMode.CONSTANT
				new_ext.par.file.expr = ''
				new_ext.par.file = ''

		compEditor_ext = compEditor.op('CompEditorExt')
		# Look for the line that contains "if extType in ['Standard', 'Empty']:" and modify it
		lines = compEditor_ext.text.split('\n')
		modified = False
		for i, line in enumerate(lines):
			if "if extType in ['Standard', 'Empty']:" in line:
				lines[i] = line.replace("['Standard', 'Empty']", f"['Standard', 'Empty', '{self.my_ext_type}']")
				modified = True
				break
		if modified:
			compEditor_ext.text = '\n'.join(lines)

		addMenuExec = compEditor.op('extensions/ext1/addMenuExec')
		# Look for line that contains "menu.Open(['Standard', 'Empty'" and modify it
		lines = addMenuExec.text.split('\n')
		modified = False
		for i, line in enumerate(lines):
			if "menu.Open(['Standard', 'Empty']" in line:
				lines[i] = line.replace("['Standard', 'Empty']", f"['Standard', 'Empty', '{self.my_ext_type}']")
				modified = True
				break
		if modified:
			addMenuExec.text = '\n'.join(lines)

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

	def OnSelect(self, info, inject_ext = None):
		if inject_ext is not None and self.MY_FORCED_TAG not in inject_ext.text:
			# so: in kindergaertner we can only react to the tag `TDExtension`
			# and for some reason when injecting an extTemplate through the comp editor, the tags are removed
			# so when not injecting we also have the tag `TDExtension` and we've already done the work
			return
		sel = True if inject_ext is not None or info['buttonNum'] == 1 else False
		if sel and self.ConfigComp:
			masterUtils = self.ownerComp.op('extUtils')
			masterExt = self.extTemplate

			extIndex = self.getExtIndex()
			extIndex = extIndex if inject_ext is None else extIndex-1
			extModuleName = info['enteredText'] if info is not None else op.TDDialogs.op('CompEditor').ExtClassNames.get(extIndex)	
			edges = TDF.findNetworkEdges(self.ConfigComp)
			
			if edges:
				edgeX = edges['positions']['left']
				edgeY = edges['positions']['top'] - 220
			else:
				edgeX = 0
				edgeY = 0
			xPos = edgeX - 400
			yPos = edgeY


			extPar = getattr(self.ConfigComp.par, 'extension' + str(extIndex))
			extPromotePar = getattr(self.ConfigComp.par,
									'promoteextension' + str(extIndex))
			extNamePar = getattr(self.ConfigComp.par,
								'extname' + str(extIndex))
			
			if inject_ext is None:
				extDat = self.ConfigComp.copy(masterExt, name=extModuleName)
			else:
				extDat = inject_ext
				extDat.color = masterExt.color
				extDat.tags = masterExt.tags
				extDat.nodeWidth = masterExt.nodeWidth
				extDat.nodeHeight = masterExt.nodeHeight

			extDat.par.file.mode = ParMode.CONSTANT
			extDat.par.file.expr = ''
			extDat.par.file = ''
			extDat.par.language = 'python'

			extUtils = self.ConfigComp.copy(masterUtils, includeDocked=True)
			extUtils.dock = extDat
			#extUtils.par.file = ''
			
			extensionText = copy.deepcopy(masterExt.text)
			
			if self.MY_FORCED_TAG in extensionText:
				# remove the manual tag from the text
				new_text = extensionText.replace(self.MY_FORCED_TAG, '')
				extensionText = new_text

			extensionText = extensionText.replace('QuickExtTemplate',
												extModuleName)
			extDat.nodeX = xPos
			extDat.nodeY = yPos
			extDat.viewer = True
			extDat.tags.add('TDExtension')
			extPromotePar.val = True
			extNamePar.val = ''
			extDat.docked[0].nodeX = extDat.nodeX 
			extDat.docked[0].nodeY = extDat.nodeY - 200
			extDat.docked[0].showDocked = True
			extDat.current = True

			self.__purgeTags(extDat)
			self.__purgeTags(extUtils)

			for _dock in extUtils.ops('*'):
				#_dock.showDocked = False
				self.__purgeTags(_dock)
				if hasattr(_dock.par, 'file'):
					_dock.par.file.mode = ParMode.CONSTANT
					_dock.par.file.expr = ''
					_dock.par.file = ''
			
			extPar.val = "op('./" + extModuleName + "').module." \
						+ extModuleName + '(me)'
			extDat.text = extensionText

			self.ConfigComp.initializeExtensions(extIndex-1)
			self.__updateCompEditor(extIndex)

			# TODO: stubify packages
			#if self.ownerComp.par.Deploystubs.eval():
				#self.stubser.StubifyDat(masterUtils)

	def __updateCompEditor(self, index):
		compEditor = op.TDDialogs.op('CompEditor')
		entry = compEditor.op('extensions/ext'+str(int(index)))
		if entry is None:
			return
		bg = entry.op('extClassStatus1/bg')
		bg.cook(force=True)

	def __purgeTags(self, _op):
		TAGS_TO_REMOVE = ['FNS_externalized', 'pi_suspect']
		for _tag in TAGS_TO_REMOVE:
			if _tag in _op.tags:
				_op.tags.remove(_tag)

	
	def OnCompEditor(self, new_ops):
		# get the ops (probably only one) from new ops with the tags 'CompEditor' and 'extTemplate' 
		self.ConfigComp = op.TDDialogs.op('CompEditor').ConfigComp
		for _op in new_ops:
			self.OnSelect(None, inject_ext=_op)
		pass

	def OnClose(self, info):
		pass

	def OnOpen(self, info):
		pass
