
'''Info Header Start
Name : ExtTDTypings
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
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

class ExtTDTypings:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		fnsLog('TDTypings: init')

	@property
	def repo(self):
		return self.ownerComp.op('repo')
	
	@property
	def path(self):
		return Path(self.ownerComp.par.Path.eval())
	

	def __fixFileName(self, name):
		# extract filename.ext from name_ext, keeping in mind that name can contain underscores

		# find the last underscore
		underscoreIndex = name.rfind('_')
		if underscoreIndex == -1:
			return name
		else:
			return name[:underscoreIndex] + '.' + name[underscoreIndex+1:]


	def OnInstall(self):
		self.DeployStubs(force=False)

	def OnForce(self):
		self.DeployStubs(force=True)


	def DeployStubs(self, force=False):
		fnsLog(f'TDTypings: deploying stubs to {self.path} (force={force})')
		#check if the path exists if not create it
		if not self.path.exists():
			self.path.mkdir(parents=True)
		for child in self.repo.findChildren(type=DAT):
			fileName = self.__fixFileName(child.name)
			fullPath = self.path / fileName
			# if the file already exists in self.path, skip unless force is True
			if (fullPath).exists() and not force:
				continue
			# write the file to disk, overwrite if exists
			with open(fullPath, 'w') as f:
				f.write(child.text)
			ui.status = 'Deployed stubs to ' + str(fullPath) + ' successfully.'

			
		
