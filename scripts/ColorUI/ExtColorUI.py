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
		self.table_out : tableDAT = self.ownerComp.op('table_out')
		self.colors_saved = {}

	def __randomizeColors(self):
		for ui_element in ui.colors:
			self._randomizeColor(ui_element)
		pass

	def _randomizeColor(self, ui_element):
		ui.colors[ui_element] = [random.uniform(0, 1) for _ in range(3)] 

	def onParResetcolors(self):
		ui.colors.resetToDefaults()
		self.parRandomize.val = False

	def onParRandomize(self):
		self.__randomizeColors()


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


	def onParUielement(self, val):
		if val in ui.colors:
			self.ownerComp.parGroup.Color = ui.colors[val]
#
	def onParSetcolor(self):
		# store current color
		try:
			if self.evalUielement not in self.colors_saved:
				self.colors_saved[self.evalUielement] = ui.colors[self.evalUielement]
			# set new color
			ui.colors[self.evalUielement] = self.ownerComp.parGroup.Color.eval()
		except:
			pass

	def onParResetcolor(self):
		try:
			ui.colors[self.evalUielement] = self.colors_saved[self.evalUielement]
			self.ownerComp.parGroup.Color = self.colors_saved[self.evalUielement]
		except:
			pass

