'''Info Header Start
Name : ExtClownUI
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.444.toe
Saveversion : 2023.11600
Info Header End'''


CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import

###

import json
import random
import os

class ExtColorUI:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		
		# before anything happens
		self.activeColorTable : tableDAT= self.ownerComp.op('null_active')
		self.default_fam_colors = {}
		self.default_all_colors = {}

		self.table_out : tableDAT = self.ownerComp.op('table_out')
		self.logger = self.ownerComp.op('Logger').ext.Logger


	@property
	def colors_sequence(self) -> Sequence:
		return self.ownerComp.seq.Colors

	def storeDefaultColors(self):
		# save the default colors
		for _row in self.activeColorTable.rows(val=True):
			self.default_fam_colors[_row[0]] = _row[1:]
		for _color in ui.colors:
			self.default_all_colors[_color] = ui.colors[_color]

	def OnStart(self):
		self.storeDefaultColors()

		# cache contents from file
		if self.evalAutoloadallcolors or self.evalAutoloadfamiliescolors:
			# check if the file exists
			if os.path.exists(self.evalFile):
				with open(self.evalFile, 'r') as f:
					contents = json.load(f)
					if any(color in ui.colors for color in contents):
						if self.evalAutoloadallcolors:
							self.ownerComp.store('colors', contents)
							# take all the active families from the dictionary and add them to the fam_colors dictionary
						_fam_colors = {}	
						if self.evalAutoloadfamiliescolors:
							for _fam in self._available_families:
								_fam_colors[_fam] = contents[_fam]
							self.ownerComp.store('fam_colors', _fam_colors)

		# load colors from stored values or from file
		if self.evalAutoloadallcolors:
			self.onParLoadallcolors()
		
		if self.evalAutoloadfamiliescolors:
			self.onParLoadfamiliescolors()


	def onParResetallcolors(self):
		ui.colors.resetToDefaults()
		self.ownerComp.store('colors', {})
		self.ownerComp.store('fam_colors', {})
		self.storeDefaultColors()

	def onParSetallfamiliescolors(self):
		for _block in self.famcolors_sequence:
			self.setColor(_block.par.Family.eval(), _block.parGroup.Rgb.eval())

	def onParSetallcolors(self):
		for _block in self.colors_sequence:
			self.setColor(_block.par.Uielement.eval(), _block.parGroup.Rgb.eval())
		# also do it for families
		self.onParSetallfamiliescolors()

	def onSeqColorsNUielement(self, idx):
		# when selecting ui element from dropdown or by typing in the text field
		val = self.colors_sequence[idx].par.Uielement.eval()
		if val in ui.colors:
			self.colors_sequence[idx].parGroup.Rgb = ui.colors[val]


	def onSeqColorsNRgbr(self, idx):
		self.setColorParGroup(idx)
	def onSeqColorsNRgbg(self, idx):
		self.setColorParGroup(idx)
	def onSeqColorsNRgbb(self, idx):
		self.setColorParGroup(idx)

	def onSeqMatchingNRgbr(self, idx):
		element = self.seq_matching[idx].par.Uielement.eval()
		color = self.seq_matching[idx].parGroup.Rgb.eval()
		self.setColor(element, color)
	def onSeqMatchingNRgbg(self, idx):
		element = self.seq_matching[idx].par.Uielement.eval()
		color = self.seq_matching[idx].parGroup.Rgb.eval()
		self.setColor(element, color)
	def onSeqMatchingNRgbb(self, idx):
		element = self.seq_matching[idx].par.Uielement.eval()
		color = self.seq_matching[idx].parGroup.Rgb.eval()
		self.setColor(element, color)
	
	def setColorParGroup(self, idx):
		element = self.colors_sequence[idx].par.Uielement.eval()
		color = self.colors_sequence[idx].parGroup.Rgb.eval()
		self.setColor(element, color)



	def onSeqColorsNResetcolor(self, idx):
		element = self.colors_sequence[idx].par.Uielement.eval()
		self.setColor(element, self.default_all_colors[element])


	def onParSaveallcolors(self):
		_colors = {}
		for block in self.colors_sequence:
			_ui_element = block.par.Uielement.eval()
			_color = block.parGroup.Rgb.eval()
			_colors[_ui_element] = _color

		for block in self.famcolors_sequence:
			_fam = block.par.Family.eval()
			_color = block.parGroup.Rgb.eval()
			_colors[_fam] = _color

		self.ownerComp.store('colors', _colors)



	def onParLoadallcolors(self):
		_colors = self.ownerComp.fetch('colors', {})
		self.colors_sequence.numBlocks = 1
		idx_cntr = 1
		valid = False
		for idx, (_ui_element, _color) in enumerate(_colors.items()):
			if _ui_element in self._available_families:
				# find out which row it belongs to
				idx = self._available_families.index(_ui_element)
				self.famcolors_sequence[idx].parGroup.Rgb.val = _color
				valid = True
			elif (_ui_element and _ui_element in ui.colors and _ui_element not in self._available_families): # check if it's a valid ui element and not a family
				if idx_cntr > 1:
					self.colors_sequence.numBlocks += 1
				block = self.colors_sequence[idx_cntr-1]
				block.par.Uielement.val = _ui_element
				block.parGroup.Rgb.val = _color
				self.setColor(_ui_element, _color)
				idx_cntr += 1
				valid = True
		return valid

	def onParClearsequence(self):
		self.colors_sequence.numBlocks = 1
		self.colors_sequence.blocks[0].par.Uielement.val = ''
		self.colors_sequence.blocks[0].parGroup.Rgb.val = [0,0,0]

###
	@property
	def _available_families(self):
		return self.activeColorTable.col(0, val=True)


	@property
	def famcolors_sequence(self) -> Sequence:
		return self.ownerComp.seq.Families


	def populateSequence(self):
		families = self._available_families
		
		self.famcolors_sequence.numBlocks = 1
		self.famcolors_sequence.numBlocks = len(families)
		for block in self.famcolors_sequence.blocks:
			fam = families[block.index]
			# for some reason setting the MenuSource with TableMenu kept evaluating correctly but throwing an error
			block.par.Family.menuNames = families
			block.par.Family.menuLabels = families
			
			block.par.Family = fam
			block.parGroup.Rgb.val = self.activeColorTable.row(fam)[1:]


	def onParSavefamiliescolors(self):
		_just_fams_colors : dict[str, list[float]] = self.ownerComp.fetch('fam_colors', {})
		_colors : dict[str, list[float]] = self.ownerComp.fetch('colors', {})
		
		for _row in self.activeColorTable.rows(val=True):
			_just_fams_colors[_row[0]] = tuple(float(r) for r in _row[1:])
			_colors[_row[0]] = tuple(float(r) for r in _row[1:])

		self.ownerComp.store('fam_colors', _just_fams_colors)
		self.ownerComp.store('colors', _colors)


	def onParLoadfamiliescolors(self):
		_just_fams_colors : dict[str, list[float]] = self.ownerComp.fetch('fam_colors', self.default_fam_colors)
		if _just_fams_colors:
			for _fam, _color in _just_fams_colors.items():
				if _fam in ui.colors:
					ui.colors[_fam] = _color
				else:
					# TODO: handle custom OP families##
					pass
		self.populateSequence()
		

	def onSeqFamiliesNRgbr(self, idx):
		self.setColor(self.famcolors_sequence[idx].par.Family.eval(), self.famcolors_sequence[idx].parGroup.Rgb.eval())
	def onSeqFamiliesNRgbg(self, idx):
		self.setColor(self.famcolors_sequence[idx].par.Family.eval(), self.famcolors_sequence[idx].parGroup.Rgb.eval())
	def onSeqFamiliesNRgbb(self, idx):
		self.setColor(self.famcolors_sequence[idx].par.Family.eval(), self.famcolors_sequence[idx].parGroup.Rgb.eval())


	def onParResetfamiliescolors(self):
		self.logger.log(f'Resetting families colors to defaults: {self.default_fam_colors}')
		for _fam in self.default_fam_colors:
			self.setColor(_fam, self.default_fam_colors[_fam])
			self.famcolors_sequence[self._available_families.index(_fam)].parGroup.Rgb.val = self.default_fam_colors[_fam]
		self.ownerComp.store('fam_colors', {})
		self.populateSequence()

	def onSeqFamiliesNResetcolor(self, idx):
		fam = self.famcolors_sequence[idx].par.Family.eval()
		if fam in self.default_all_colors:
			rgb = self.default_all_colors[fam]
			self.setColor(fam, rgb)
			self.famcolors_sequence[idx].parGroup.Rgb.val = rgb
		else:
			self.logger.log(f'No default color found for {fam}')

	def onSeqMatchingNResetcolor(self, idx):
		element = self.seq_matching[idx].par.Uielement.eval()
		self.setColor(element, self.default_all_colors[element])
		self.seq_matching[idx].parGroup.Rgb.val = self.default_all_colors[element]

	def _addElementToColorsSequence(self, element, color, existing_elements=None):
		"""Helper method to add an element to the colors sequence.
		
		Args:
			element: The UI element to add
			color: The RGB color for the element
			existing_elements: Optional list of already existing elements to check against
		
		Returns:
			bool: True if element was added or updated, False otherwise
		"""
		if element == 'No match':
			return False
			
		if element in ui.colors and element not in self._available_families:
			# Check if element already exists in sequence
			current_elements = [_par.val for _par in self.colors_sequence.blockPars.Uielement]
			if element in current_elements:
				# Update existing element's color
				idx = current_elements.index(element)
				self.colors_sequence[idx].parGroup.Rgb.val = color
				return True
				
			# If this is the first element and there's an empty block at the beginning, use it
			if self.colors_sequence.numBlocks == 1 and not self.colors_sequence[0].par.Uielement.eval():
				current_idx = 0
			else:
				# Otherwise add a new block
				self.colors_sequence.numBlocks += 1
				current_idx = self.colors_sequence.numBlocks - 1
			
			block = self.colors_sequence[current_idx]
			block.par.Uielement.val = element
			block.parGroup.Rgb.val = color
			return True
		return False

	def onSeqMatchingNAddtosequence(self, idx):
		element = self.seq_matching[idx].par.Uielement.eval()
		color = self.seq_matching[idx].parGroup.Rgb.eval()
		self._addElementToColorsSequence(element, color)

	def onParAddtocolorssequence(self):
		# takes found elements from seq_matching and adds them to the colors sequence
		element_count = 0
		
		for idx in range(self.seq_matching.numBlocks):
			element = self.seq_matching[idx].par.Uielement.eval()
			color = ui.colors[element]
			if self._addElementToColorsSequence(element, color):
				element_count += 1

####

	def onParRandomize(self):
		for ui_element in ui.colors:
			self.setColor(ui_element, [random.uniform(0, 1) for _ in range(3)])
		pass

	def onParUndorandom(self):
		ui.colors.resetToDefaults()
		self.onParLoadallcolors()

	@property
	def seq_matching(self):
		return self.ownerComp.seq.Matching

	def _whichUIElement(self, color):
		elements = []
		tolerance = self.evalGroupTolerance # gives rgb tuple (r,g,b)
		# check if the color is close to the ui element color per channel
		for ui_element in ui.colors:
			ui_color = ui.colors[ui_element]
			if (abs(ui_color[0] - color[0]) <= tolerance[0] and 
				abs(ui_color[1] - color[1]) <= tolerance[1] and
				abs(ui_color[2] - color[2]) <= tolerance[2]):
				elements.append(ui_element)
		
		if not elements:
			elements = ['No match']
		else:
			# sort elements by distance to color
			elements.sort(key=lambda x: sum(abs(a - b) for a, b in zip(ui.colors[x], color)))
			# keep only the first N
			max_elements = self.evalMaxinlist
			elements = elements[:max_elements]
		self.seq_matching.numBlocks = len(elements)
		for idx, element in enumerate(elements):
			self.seq_matching[idx].par.Uielement.val = element
			self.seq_matching[idx].parGroup.Rgb.val = ui.colors[element]

	def onParCheck(self):
		colortocheck = self.evalGroupColortocheck
		self._whichUIElement(colortocheck)

	def onParGroupSetallrgb(self, _val):
		for _block in self.seq_matching:
			_block.parGroup.Rgb.val = _val

	def onParSetallrgbset(self):
		rgb = self.evalGroupSetallrgb
		self.onParGroupSetallrgb(rgb)

####
	def onParImport(self):
		_file = self.evalFile
		if _file:
			colors = {}
			with open(_file, 'r') as f:
				colors = json.load(f)
			if colors:
				self.colors_sequence.numBlocks = 1
				idx_cntr = 0
				for element, color in colors.items():
					if self.setColor(element, color) and element not in self._available_families:
						if idx_cntr > 0:
							self.colors_sequence.numBlocks += 1
						block = self.colors_sequence[idx_cntr]
						block.par.Uielement.val = element
						block.parGroup.Rgb.val = color
						idx_cntr += 1
					elif element in self._available_families:
						block = self.famcolors_sequence[self._available_families.index(element)]
						block.parGroup.Rgb.val = color
				
		pass

	def onParExport(self):
		_file = self.evalFile
		if _file:
			# take all colors from stored colors and save them to the file as json dictionary
			colors = self.ownerComp.fetch('colors', {})
			if colors:
				with open(_file, 'w') as f:
					json.dump(colors, f)
		pass

	######################################
	def setColor(self, _type: str, _color: list[float]):
		if _type in ui.colors:
			if _type not in self.default_all_colors:
				# in case somehow the color was not saved on startup
				self.default_all_colors[_type] = _color
			ui.colors[_type] = _color
			return True
		return False