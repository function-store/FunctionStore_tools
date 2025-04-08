from pathlib import Path

class ExtScriptExternalize:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.__script = None
		self.popDialog = self.ownerComp.op('popDialog')
		self.tags = ['FNS_externalized', 'pi_suspect']
		
#############################################
# Properties
	@property
	def ScriptOp(self) -> OP:
		return self.__script

	@ScriptOp.setter
	def ScriptOp(self, _op):
		if self.__check_eligibility(_op):
			self.__script = _op
		else:
			self.__script = None

	@property
	def Folder(self):
		return self.ownerComp.par.Folder.eval()
	
#############################################
# Callbacks

	def OnExternalizeselected(self):
		self.ScriptOp = ui.panes.current.owner.currentChild
		self.Externalize()


	def Externalize(self, file_path=None, forceDialog=False, forceOverwrite=False):
		if self.ScriptOp is None:
			return

		if not file_path:
			file_path = self.__createFilePathFull()

		if not forceOverwrite:
			file_path = self._checkFilePath(file_path, forceDialog)
		if file_path is None:
			return
		
		self._setFilePath(file_path)


	def _checkFilePath(self, file_path, forceDialog=False):
		# Check if the file exists and open a dialog to choose a new name
		if file_path.exists() or forceDialog:
			self.popDialog.par.Text = f"{self.__ensureForwardSlashes(file_path)} already exists. Please choose a new name." if not forceDialog else f"Please choose a new name."
			self.popDialog.Open(textEntry=f"{self.__ensureForwardSlashes(file_path.with_suffix(''))}")
			return None
		return file_path


	def OnDialogFinish(self, info):
		if info['buttonNum'] == 1:
			file_path = Path(f"{info['enteredText']}.{self.__getFileExtensionForOp(self.ScriptOp)}") 
			self.Externalize(file_path=file_path)
		elif info['buttonNum'] == 2:
			self.Externalize(file_path=self.__createFilePathFull(), forceOverwrite=True)


	def _setFilePath(self, file_path):
		self.ScriptOp.par['file'] = self.__ensureForwardSlashes(file_path)
		self.ScriptOp.par.syncfile = True
		self.ScriptOp.color = (1, 0.5, 0.5)
		for tag in self.tags:
			if tag not in self.ScriptOp.tags:
				self.ScriptOp.tags.add(tag)
		self.ScriptOp.par.edit.pulse()


#############################################
# Helper Functions

	def __check_eligibility(self, _op):
		if isinstance(_op, OP) and _op.isDAT and hasattr(_op.par, 'file'):
			return True
		return False
	
	def __ensureForwardSlashes(self, path):
		return str(path).replace('\\', '/')

	def __getFileExtensionForOp(self, _op) -> str:
		# Check if the operation is a tableDAT, return 'tsv'
		if isinstance(_op, tableDAT):
			return 'tsv'
		
		# Attempt to get the docked operation
		if _op_dockedto := _op.dock:
			# Check if the docked operation type includes 'glsl'
			if 'glsl' in _op_dockedto.OPType:
				# Determine the file extension based on the operation name
				if '_vertex' in _op.name:
					return 'vert'
				elif '_pixel' in _op.name:
					return 'frag'
		
		# Default return 'py' if none of the above conditions are met
		return 'py'
	
	def __createFilePathFull(self, _op=None):
		if _op is None:
			_op = self.ScriptOp
		name = _op.name 
		# Construct the initial file path using pathlib
		extension = self.__getFileExtensionForOp(self.ScriptOp)

		if not name.endswith(f'.{extension}'):
			name = f"{name}.{extension}"
			
		if 'TDExtension' not in _op.tags:
			file_path = Path(self.Folder) / name
		else:
			file_path = Path(self.Folder) / _op.parent().name / name
		return file_path