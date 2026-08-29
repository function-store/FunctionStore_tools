
'''Info Header Start
Name : ExtScriptExternalize
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
import re
from pathlib import Path

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

class ExtScriptExternalize:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.__script = None
		self.popDialog = self.ownerComp.op('popDialog')
		self.tags = ['FNS_externalized', 'pi_suspect']
		fnsLog('ScriptSyncFile: init')

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
		fnsLog(f'ScriptSyncFile: externalizing {self.ScriptOp.path} -> {self.__ensureForwardSlashes(file_path)}')
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

	# Language values that don't name a concrete language -> sniff the content.
	__nonLanguageValues = ('input', 'parameter', 'text')
	# Explicit language -> file extension (glsl handled separately for stage).
	__languageExtMap = {
		'python': 'py',
		'json': 'json',
		'yaml': 'yaml',
		'yml': 'yaml',
		'xml': 'xml',
		'html': 'html',
	}

	def __getFileExtensionForOp(self, _op) -> str:
		# Check if the operation is a tableDAT, return 'tsv'
		if isinstance(_op, tableDAT):
			return 'tsv'

		# 1) Believe the DAT's declared language, unless it is a non-specific
		#    value ('input'/'parameter'/'text'), in which case sniff instead.
		lang = self.__declaredLanguage(_op)
		if lang and lang not in self.__nonLanguageValues:
			if lang == 'glsl':
				return self.__shaderStage(_op) or self.__detectShaderExtension(_op) or 'glsl'
			if lang in self.__languageExtMap:
				return self.__languageExtMap[lang]
			# Some other specific language TD reports -> believe it as the ext.
			return lang

		# 2) Reliable structural signal: a DAT docked to a glsl TOP/MAT.
		if _op_dockedto := _op.dock:
			# Check if the docked operation type includes 'glsl'
			if 'glsl' in _op_dockedto.OPType:
				return self.__shaderStage(_op) or 'glsl'

		# 3) Non-specific language: detect by content (glsl/json/yaml/xml/html).
		if ext := self.__detectContentExtension(_op):
			return ext

		# 4) Default return 'py' if none of the above conditions are met
		return 'py'

	def __declaredLanguage(self, _op) -> str:
		"""The DAT's declared script language, lowercased, or None if absent."""
		if hasattr(_op.par, 'language'):
			try:
				return str(_op.par.language.eval()).strip().lower()
			except Exception:
				return None
		return None

	def __shaderStage(self, _op) -> str:
		"""Return 'vert'/'frag' from the op name convention, else None."""
		name = _op.name.lower()
		if '_vertex' in name or '_vert' in name:
			return 'vert'
		if '_pixel' in name or '_frag' in name:
			return 'frag'
		return None

	def __detectContentExtension(self, _op) -> str:
		"""Best-effort extension sniffed from a textual DAT's content.

		Runs only when the DAT declares no specific language. Detects, in order
		of decreasing reliability: GLSL/TD shaders, XML/HTML markup, JSON, YAML.
		Returns None (caller defaults to .py) when nothing matches.
		"""
		if not _op.isText:
			return None
		text = _op.text
		if not text or not text.strip():
			return None

		if ext := self.__detectShaderExtension(_op):
			return ext
		if ext := self.__detectMarkupExtension(text):
			return ext
		if self.__looksLikeJson(text):
			return 'json'
		if self.__looksLikeYaml(text):
			return 'yaml'
		return None

	def __detectShaderExtension(self, _op) -> str:
		"""'vert'/'frag'/'glsl' when the text is a GLSL shader, else None.

		The one signature guaranteed in a TD GLSL shader is the entry point
		``void main() {`` -- the #version pragma is injected by TD, and TD
		builtins / gl_* variables are all optional -- so that is the gate. It
		also never appears in Python, keeping false positives out.
		"""
		if not _op.isText:
			return None
		text = _op.text or ''
		if not re.search(r'void\s+main\s*\(', text):
			return None

		# Disambiguate stage: explicit name convention first, then content.
		stage = self.__shaderStage(_op)
		if stage:
			return stage
		lowered = text.lower()
		if 'gl_position' in lowered or 'tddeform' in lowered:
			return 'vert'
		if ('gl_fragcolor' in lowered or 'tdoutputswizzle' in lowered
				or 'gl_fragcoord' in lowered):
			return 'frag'
		return 'glsl'

	def __detectMarkupExtension(self, text) -> str:
		"""'html'/'xml' when the text looks like angle-bracket markup, else None."""
		stripped = text.lstrip()
		if not stripped.startswith('<'):
			return None
		head = stripped[:1024].lower()
		if head.startswith('<?xml'):
			return 'xml'
		if '<!doctype html' in head or '<html' in head:
			return 'html'
		if any(tag in head for tag in ('<head', '<body', '<div', '<span', '<p>', '<a ')):
			return 'html'
		return 'xml'

	def __looksLikeJson(self, text) -> bool:
		s = text.strip()
		if not s or s[0] not in '{[':
			return False
		try:
			import json
			json.loads(s)
			return True
		except Exception:
			return False

	def __looksLikeYaml(self, text) -> bool:
		s = text.strip()
		if not s:
			return False
		# A document marker is a strong YAML signal; otherwise require a few
		# 'key: value' lines so plain prose isn't misread as YAML.
		if not (s.startswith('---') or s.startswith('%YAML')):
			if len(re.findall(r'(?m)^[ \t]*[\w.\-]+:(?:\s|$)', s)) < 2:
				return False
		try:
			import yaml
			return isinstance(yaml.safe_load(s), (dict, list))
		except Exception:
			return False
	
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