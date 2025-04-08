'''Info Header Start
Name : ExtClownUI
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.451.toe
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

	def setColor(self, _type: str, _color: list[float]):
		if _type in ui.colors:
			if _type not in self.default_all_colors:
				# in case somehow the color was not saved on startup
				self.default_all_colors[_type] = _color
			ui.colors[_type] = _color
			return True
		return False

	def storeDefaultColors(self):
		# save the default colors
		for _row in self.activeColorTable.rows(val=True):
			self.default_fam_colors[_row[0]] = _row[1:]
		for _color in ui.colors:
			self.default_all_colors[_color] = ui.colors[_color]

	def OnStart(self):
		self.updateSearchStatus('')
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
		self.populateSequence()

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
		
		self.updateSearchStatus(f'Showing {len(elements)} of {self.evalMaxinlist if self.evalMaxinlist else "all"}')

		if not elements:
			elements = ['No match']
		else:
			# sort elements by distance to color
			elements.sort(key=lambda x: sum(abs(a - b) for a, b in zip(ui.colors[x], color)))
			# keep only the first N
			if self.evalMaxinlist:
				elements = elements[:self.evalMaxinlist]
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


#### THANKS CURSOR FOR THIS CODE

	def _calculate_word_similarity(self, word1: str, word2: str) -> float:
		"""Calculate similarity between two words, considering partial matches."""
		if word1 == word2:
			return 1.0
		if word1 in word2 or word2 in word1:
			return 0.8
		# Check for common prefixes/suffixes
		prefix_len = 0
		while prefix_len < min(len(word1), len(word2)) and word1[prefix_len] == word2[prefix_len]:
			prefix_len += 1
		suffix_len = 0
		while suffix_len < min(len(word1), len(word2)) and word1[-(suffix_len+1)] == word2[-(suffix_len+1)]:
			suffix_len += 1
		return (prefix_len + suffix_len) / (2 * max(len(word1), len(word2)))

	def _match_wildcard(self, pattern: str, text: str) -> bool:
		"""Check if text matches a wildcard pattern."""
		if '*' not in pattern:
			return pattern in text
		parts = pattern.split('*')
		if not parts[0] and not parts[-1]:  # *pattern*
			return all(part in text for part in parts[1:-1])
		elif not parts[0]:  # *pattern
			return text.endswith(parts[-1])
		elif not parts[-1]:  # pattern*
			return text.startswith(parts[0])
		else:  # pattern*pattern
			return text.startswith(parts[0]) and text.endswith(parts[-1])

	def _calculate_key_score(self, key: str, search_terms: list[str]) -> float:
		"""Calculate a sophisticated score for a key based on search terms."""
		key_lower = key.lower()
		key_parts = key_lower.split('.')
		total_score = 0.0
		
		# First check for exact match of the entire search string
		full_search = ' '.join(search_terms)
		if full_search == key_lower:
			return 2.0  # Highest possible score for exact match
		
		# Check for exact segment matches in order
		search_parts = full_search.split('.')
		if len(search_parts) > 1:
			# Check if all search parts match segments in order
			matches_in_order = True
			last_match_index = -1
			for part in search_parts:
				try:
					current_index = key_parts.index(part)
					if current_index <= last_match_index:
						matches_in_order = False
						break
					last_match_index = current_index
				except ValueError:
					matches_in_order = False
					break
			if matches_in_order:
				return 1.8  # Very high score for ordered segment matches
		
		# Check for hierarchical matches (terms appear in order, separated by dots)
		search_terms_dot = '.'.join(search_terms)
		if search_terms_dot in key_lower:
			return 1.6  # High score for hierarchical matches
		
		# Check if all terms appear in the key (not necessarily in order)
		all_terms_present = all(term in key_lower for term in search_terms)
		if all_terms_present:
			# Calculate position-based score
			positions = [key_lower.find(term) for term in search_terms]
			ordered = all(positions[i] <= positions[i+1] for i in range(len(positions)-1))
			if ordered:
				return 1.4  # Good score for ordered terms
			return 1.2  # Decent score for unordered terms
		
		# Handle single term matches with position-based scoring
		for i, term in enumerate(search_terms):
			term_lower = term.lower()
			term_score = 0.0
			
			# Check for exact segment match
			if term_lower in key_parts:
				# Higher score for earlier terms in the search
				position_weight = 1.0 - (i * 0.2)  # Each subsequent term gets 20% less weight
				term_score = 1.0 * position_weight
			else:
				# Check for wildcard matches
				if '*' in term:
					if self._match_wildcard(term_lower, key_lower):
						term_score = 0.7
				else:
					# Check for partial matches in each part
					best_part_score = 0.0
					for part in key_parts:
						similarity = self._calculate_word_similarity(term_lower, part)
						best_part_score = max(best_part_score, similarity)
					term_score = best_part_score * 0.5  # Reduce score for partial matches
			
			# Weight by position in the key (earlier matches are better)
			position_weight = 1.0
			if term_lower in key_lower:
				position = key_lower.find(term_lower)
				position_weight = 1.0 - (position / len(key_lower))
			
			total_score += term_score * position_weight
		
		# Normalize score
		final_score = total_score / len(search_terms)
		
		# Check if all terms appear in order (but not necessarily as exact segments)
		ordered_terms = ' '.join(search_terms)
		if ordered_terms in key_lower:
			final_score = max(final_score, 1.5)  # Boost score for ordered terms
		
		return final_score

	def searchColorKeys(self, search_term: str) -> list[tuple[str, float]]:
		"""Enhanced search for keys in ui.colors with partial matching and wildcards.
		
		Args:
			search_term: Can be multiple terms separated by spaces or dots.
						Supports wildcards (*) and partial word matching.
		
		Returns:
			list[tuple[str, float]]: List of matching keys with their colors
		"""
		results = []
		exact_match = None
		
		# First check for exact match with dots preserved
		if search_term in ui.colors:
			exact_match = (search_term, ui.colors[search_term], 2.0)  # Store exact match with highest score
		
		# Then try with spaces instead of dots
		search_terms = [term for term in search_term.replace('.', ' ').split() if term]
		
		for key in ui.colors:
			# Skip the exact match as we already have it
			if exact_match and key == exact_match[0]:
				continue
				
			score = self._calculate_key_score(key, search_terms)
			if score > 0.2:  # Lower threshold to include more matches
				results.append((key, ui.colors[key], score))
		
		# Sort by score (higher is better)
		results.sort(key=lambda x: x[2], reverse=True)
		
		# Combine results with exact match at the top
		final_results = []
		if exact_match:
			final_results.append((exact_match[0], exact_match[1]))
		final_results.extend([(key, color) for key, color, _ in results])
		
		return final_results

	def onParClearmatchsequence(self):
		self.seq_matching.numBlocks = 1

#### THANKS CURSOR FOR THIS CODE ABOVE

	def onParSearch(self):
		term = self.evalSearchelement
		results = self.searchColorKeys(term)
		self.updateSearchStatus(f'Showing {len(results)} of {self.evalMaxinlist if self.evalMaxinlist else "all"}')
		# trim results to max
		if self.evalMaxinlist:
			results = results[:self.evalMaxinlist]
		self.addSearchResults(results)
		
	def addSearchResults(self, results: list[tuple[str, float]]):
		self.seq_matching.numBlocks = len(results)
		for idx, result in enumerate(results):
			block = self.seq_matching[idx]
			block.par.Uielement.val = result[0]
			block.parGroup.Rgb.val = result[1]

	def updateSearchStatus(self, text: str):
		self.evalSearchstatus = text
