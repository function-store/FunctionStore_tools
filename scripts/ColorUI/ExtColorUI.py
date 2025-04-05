'''Info Header Start
Name : ExtClownUI
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.427.toe
Saveversion : 2023.11600
Info Header End'''


CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import

###

import random

class ExtColorUI:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		
		# before anything happens
		self.activeColorTable : tableDAT= self.ownerComp.op('null_active')
		self.default_fam_colors = {}

		self.table_out : tableDAT = self.ownerComp.op('table_out')
		self.colors_saved = {}
		self.colors_changed = {}
		self.logger = self.ownerComp.op('Logger').ext.Logger


	def OnStart(self):
		for _row in self.activeColorTable.rows(val=True):
			self.default_fam_colors[_row[0]] = _row[1:]
		self.logger.log(f'Default families colors: {self.default_fam_colors}')
		if self.evalAutoloadfamiliescolors:
			self.onParLoadfamiliescolors()

	def onParResetallcolors(self):
		ui.colors.resetToDefaults()
		self.colors_changed = {}
		self.ownerComp.store('colors', {})


	def onParUielement(self, val):
		# when selecting ui element from dropdown or by typing in the text field
		if val in ui.colors:
			self.ownerComp.parGroup.Color = ui.colors[val]
#
	def onParSetcolor(self):
		# set ui element to a color
		try:
			if self.evalUielement not in self.colors_saved:
				self.colors_saved[self.evalUielement] = ui.colors[self.evalUielement]
			if self.setColor(self.evalUielement, self.ownerComp.parGroup.Color.eval()):
				pass
		except:
			pass

	def onParResetcolor(self):
		try:
			if self.setColor(self.evalUielement, self.colors_saved[self.evalUielement]):
				self.ownerComp.parGroup.Color = self.colors_saved[self.evalUielement]
				self.colors_changed.pop(self.evalUielement)
		except:
			pass

	def onParSaveallcolors(self):
		_colors : dict[str, list[float]] = self.ownerComp.fetch('colors', {})
		self.logger.log(f'Saving colors: {self.colors_changed}')
		for _ui_element in self.colors_changed:
			_colors[_ui_element] = self.colors_changed[_ui_element]

		self.ownerComp.store('colors', _colors)

	def onParLoadallcolors(self):
		_colors : dict[str, list[float]] = self.ownerComp.fetch('colors', {})
		self.colors_changed = {}
		for _ui_element in _colors:
			self.setColor(_ui_element, _colors[_ui_element])

###
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
			self.colors_changed[_type] = _color
			return True
		return False


	def onParSavefamiliescolors(self):
		_just_fams_colors : dict[str, list[float]] = self.ownerComp.fetch('fam_colors', {})
		_colors : dict[str, list[float]] = self.ownerComp.fetch('colors', {})
		
		for _row in self.activeColorTable.rows(val=True):
			_just_fams_colors[_row[0]] = _row[1:]
			_colors[_row[0]] = _row[1:]

		self.ownerComp.store('fam_colors', _just_fams_colors)
		self.ownerComp.store('colors', _colors)


	def onParLoadfamiliescolors(self):
		_just_fams_colors : dict[str, list[float]] = self.ownerComp.fetch('fam_colors', self.default_fam_colors)
		if _just_fams_colors:
			for _fam, _color in _just_fams_colors.items():
				if _fam in ui.colors:
					ui.colors[_fam] = _color
				else:
					# TODO: handle custom OP families
					pass
		self.populateSequence()

	def onParSetfamiliescolors(self):
		for block in self.sequence.blocks:
			block : SequenceBlock = block
			self.setColor(block.par.Type.eval(), block.parGroup.Rgb.eval())

	def onParResetfamiliescolors(self):
		self.logger.log(f'Resetting families colors to defaults: {self.default_fam_colors}')
		for _fam in self.default_fam_colors:
			self.setColor(_fam, self.default_fam_colors[_fam])
		self.ownerComp.store('fam_colors', {})
		self.populateSequence()

####

	def onParRandomize(self):
		for ui_element in ui.colors:
			self.setColor(ui_element, [random.uniform(0, 1) for _ in range(3)])
		pass


	def _whichUIElement(self, color):
		elements = []
		for ui_element in ui.colors:
			if all(abs(a - b) < 0.01 for a, b in zip(ui.colors[ui_element], color)):
				elements.append(ui_element)
		
		self.table_out.clear()
		for element in elements:
			self.table_out.appendRow([element])
		print(f'Found matching color elements for {color}: {elements}')

	def onParGroupColortocheck(self, vals):
		self._whichUIElement(vals)

	def onParCheck(self):
		colortocheck = self.evalGroupColortocheck
		self._whichUIElement(colortocheck)