from pathlib import Path

class ExtTDTypings:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

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

			
		
