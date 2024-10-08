# DO NOT REMOVE, used by QuickExt to inject extension
# Below is the import of CustomParHelper --- see `extUtils` for more info
CustomParHelper: CustomParHelper = mod(next(d.name for d in me.docked if 'extUtils' in d.tags)).CustomParHelper # import
###

class QuickExtTemplate:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)

	


