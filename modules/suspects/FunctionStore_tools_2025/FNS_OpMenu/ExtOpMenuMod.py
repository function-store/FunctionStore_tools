
'''Info Header Start
Name : ExtOpMenuMod
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
import TDFunctions as TDF

class ExtOpMenuMod:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.searchWordsTable = self.ownerComp.op('OpSearchWords')
		TDF.createProperty(self, 'SearchWordDict', value={}, dependable=True)
		self.UpdateSearchWords()

	def UpdateSearchWords(self):
		words = {}
		for row in self.searchWordsTable.rows()[1:]:
			words[row[0].val] = [_word.strip() for _word in row[1].val.split(',')]
		self.SearchWordDict = words