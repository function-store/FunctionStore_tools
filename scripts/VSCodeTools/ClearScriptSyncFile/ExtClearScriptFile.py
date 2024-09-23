class ExtClearScriptFile:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
	
	@property
	def tags(self):
		return self.ownerComp.par.Tags.eval().split(" ")


	def OnClearselected(self):
		_ops = ui.panes.current.owner.selectedChildren
		self.__clear(_ops)


	def OnClearcomp(self):
		_ops = ui.panes.current.owner.findChildren(type=DAT,  tags=self.tags, allTags=True, maxDepth=1)
		self.__clear(_ops)
		pass


	def OnClearcompchildren(self):
		_ops = ui.panes.current.owner.findChildren(type=DAT, tags=self.tags, allTags=True)
		self.__clear(_ops)
		pass
	

	def OnClearall(self):
		_ops = root.findChildren(type=DAT, tags=self.tags, allTags=True)
		self.__clear(_ops)
		pass


	def __restoreTags(self, isUndo, _ops):
		if not isUndo:
			return
		for _op in _ops:
			if _op.isDAT and (_filepar := getattr(_op.par, 'file', None)):
				for _tag in self.tags:
					if _tag not in _op.tags:
						_op.tags.add(_tag)
						_op.color = (1, 0.5, 0.5)


	def __clear(self, _ops):
		ui.undo.startBlock('Clear Externalized Script Files')
		ui.undo.addCallback(self.__restoreTags, info = _ops)
		for _op in _ops:
			if _op and all(_tag in _op.tags for _tag in self.tags):
				if _op.isDAT and (_filepar := getattr(_op.par, 'file', None)):
					_filepar.val = ""
					_op.color = (0.55,0.55,0.55)
					for _tag in self.tags:
						if _tag in _op.tags:
							_op.tags.remove(_tag)
					
		ui.undo.endBlock()