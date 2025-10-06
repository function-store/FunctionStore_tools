

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class MidiMapperMultiExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.folderTabs = self.ownerComp.op('masterFolderTabs1')
		self.masterMidiMapper = self.ownerComp.op('midiMapper1')
		self._prev_mapper_learn_states = {}
		self._addingParameter = False
		self.parComp = self.ownerComp.op('parameter1')
		self.parWindow = self.ownerComp.op('window1')
	
	@property
	def midiMappers(self):
		return self.ownerComp.ops('midiMapper*')	
	
	def getMappingTable(self, _mapper):
		return _mapper.op("repo_maker").Repo

	def OnDelete(self, idx):
		namesList = self.folderTabs.par.Menunames.eval().split(' ')
		if len(namesList) == 1:
			return
		self.folderTabs.par.Menunames = self.folderTabs.par.Menunames.eval().replace(f' {namesList[idx]}','')
		if len(self.midiMappers) == 1:
			return
		self.midiMappers[idx].destroy()
		pass

	def OnAdd(self):
		new_mapper = self.ownerComp.copy(self.midiMappers[-1])
		new_mapper.nodeY = self.midiMappers[-1].nodeY - 200
		new_mapper.par.Clear.pulse()
		new_mapper.par.Id.val += 1

		self.folderTabs.par.Menunames += f' {new_mapper.name}'
		self.folderTabs.par.Value0 = new_mapper.name

	def LearnDone(self, idx):
		if not self._addingParameter:
			return
		idx -= 1
		for _idx, _mapper in enumerate(self.midiMappers):
			_mapper.par.Learn.val = self._prev_mapper_learn_states[_mapper.name]

			if _idx == idx:
				self.folderTabs.par.Value0 = _mapper.name
				continue


			mappingTable = self.getMappingTable(_mapper)
			idx_to_delete = []
			for _row in mappingTable.rows()[1:]:
				if _row[0] and _row[0].val == "Learn":
					idx_to_delete.append(_row[0].row)
			mappingTable.deleteRows(idx_to_delete)
		self._addingParameter = False


	def AddParameter(self, _par):
		self._addingParameter = True
		for _mapper in self.midiMappers:
			_mapper.AddParameter(_par)
			self._prev_mapper_learn_states[_mapper.name] = _mapper.par.Learn.eval()
			_mapper.par.Learn.val = True

	def Resetall(self):
		for _mapper in self.midiMappers:
			_mapper.par.Resetall.pulse()

	def OpenParWindow(self, _comp):
		self.parComp.par.op = _comp.path
		self.parWindow.par.winopen.pulse()