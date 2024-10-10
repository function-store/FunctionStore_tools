# DO NOT REMOVE THIS VERY IMPORTANT LINE!!! used by QuickExt to inject extension

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
NoNode: NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
###

class QuickExtTemplate:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)

	


