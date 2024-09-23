class ExtStubserWrapper:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.stubser : extStubser = self.ownerComp.op('stubser')

	def OnDeploystubs(self):
		includePrivate = self.ownerComp.par.Private.eval()
		includeUnpromoted = self.ownerComp.par.Unpromoted.eval()
		tags = self.ownerComp.par.Tags.eval()
		tags = tags.split(' ') if tags else []
		for _op in ui.panes.current.owner.selectedChildren:
			if _op.family == 'COMP':
				ui.status = f'Stubifying COMP {_op.name}'
				# we need to iterate cause we can have multiple tags, but tag parameter only accepts one
				for tag in tags:
					self.stubser.StubifyComp(_op, tag=tag, includePrivate=includePrivate, includeUnpromoted=includeUnpromoted)
			elif _op.family == 'DAT':
				ui.status = f'Stubifying DAT {_op.name}'
				self.stubser.StubifyDat(_op)