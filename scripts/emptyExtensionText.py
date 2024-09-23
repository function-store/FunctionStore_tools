from extUtils import CustomParHelper

class DefaultExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)

	


