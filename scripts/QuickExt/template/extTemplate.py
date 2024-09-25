'''Info Header Start
Name : extTemplate
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.148.toe
Saveversion : 2023.11600
Info Header End'''
from extUtils import CustomParHelper

class DefaultExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)

	


