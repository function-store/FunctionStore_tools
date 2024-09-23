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