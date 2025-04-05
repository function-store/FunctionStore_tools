CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
#NoNode: NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
###

class ExtOpColorChange:
	def __init__(self, ownerComp):
		self.ownerComp : COMP = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		#NoNode.Init(ownerComp, enable_chopexec=True, enable_datexec=True, enable_parexec=True, enable_keyboard_shortcuts=True)

		self.activeColorTable : tableDAT= self.ownerComp.op('null_active')
		self.resetToDefaults()
		self.populateSequence() # with defaults

		if self.evalAutoload:
			self.loadSavedColors()

	@property
	def __available_families(self):
		return self.activeColorTable.col(0, val=True)

	@property
	def sequence(self) -> Sequence:
		return self.ownerComp.seq.Family

	def populateSequence(self):
		families = self.__available_families
		
		self.sequence.numBlocks = 1
		self.sequence.numBlocks = len(families)
		for block in self.sequence.blocks:
			fam = families[block.index]
			# for some reason setting the MenuSource with TableMenu kept evaluating correctly but throwing an error
			block.par.Type.menuNames = families
			block.par.Type.menuLabels = families
			
			block.par.Type = fam
			block.parGroup.Rgb.val = self.activeColorTable.row(fam)[1:]
		


	def setColor(self, _type: str, _color: list[float]):
		if _type in ui.colors:
			ui.colors[_type] = _color
		self.saveColors()

	def saveColors(self):
		_colors : dict[str, list[float]] = self.ownerComp.fetch('colors', {})
	
		for _row in self.activeColorTable.rows(val=True):
			_colors[_row[0]] = _row[1:]
		self.ownerComp.store('colors', _colors)

	def loadSavedColors(self):
		colors : dict[str, list[float]] = self.ownerComp.fetch('colors', None)
		if colors:
			for _type, _color in colors.items():
				if _type in ui.colors:
					ui.colors[_type] = _color
				else:
					# TODO: handle custom OP families
					pass
		self.populateSequence()
#
	def resetToDefaults(self):
		ui.colors.resetToDefaults()

	def onParSet(self):
		for block in self.sequence.blocks:
			block : SequenceBlock = block
			self.setColor(block.par.Type.eval(), block.parGroup.Rgb.eval())
			
	def onParLoad(self):
		self.loadSavedColors()

	def onParReset(self):
		self.resetToDefaults()
		self.populateSequence() # with defaults
