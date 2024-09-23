import TDFunctions as TDF

class ExtUpdater:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.update_button = op('/ui/dialogs/bookmark_bar/wiki/text')
		self.IsUpdatable = tdu.Dependency(False)
		self.newTag = None

	def Check(self, _):
		if self.ownerComp.par.Enabled.eval():
			iop.TDAsyncIO.Run([self._doDaCheck()])


	async def _doDaCheck(self):
		iop.GitHub.PollLatestTag()
	
	def OnPolledLatestTag(self, new_tag):
		self.newTag = new_tag
		_base = self.ownerComp.par.Target.eval()
		fetchedTag = _base.par.Gittag.eval()
		fetchedTag = fetchedTag.strip('v')
		new_tag = new_tag.strip('v')
		
		new_major = int(new_tag.split('.')[0])
		base_major = int(fetchedTag.split('.')[0])
		tag_flag = new_tag[-1]

		if new_major > base_major and not tag_flag != 'f':
			self.IsUpdatable.val = False
		else:
			self.IsUpdatable.val = (fetchedTag != new_tag)

	def PromptUpdate(self):
		ret = ui.messageBox('FNS_tools update available', 'Would you like to update FNS_tools to a newer version?',buttons=['No','Yes'])
		if ret:
			self.Update('dummy')
		else:
			self.update_button.parent().op('docsHelper').OpenDocs()

	def Update(self, _):
		op.FNS_CONFIG.SaveAllToJSON()
		iop.Downloader.par.Download.pulse()
		

	
	def OnFileDownloaded(self, callbackInfo):
		debug(callbackInfo)
		comp_path = callbackInfo['compPath']
		newComp = op(comp_path)
		fp = tdu.FileInfo(str(callbackInfo['path']))
		if newComp:
			newComp.par.externaltox.mode = ParMode.EXPRESSION
			newComp.par.externaltox.expr = f"f'{{app.userPaletteFolder}}/FNStools_ext/{fp.baseName}'"
			newComp.par.Gittag = self.newTag
			newComp.par.savebackup = True
			# response = ui.messageBox('FunctionStore_tools',
			# 	 f'Update successfully downloaded to {callbackInfo["path"]}, about to replace with {parent.FNS.path}.\nWould you like to enable as external tox?',
			# 	 buttons=['No','Yes'])
			# newComp.par.enableexternaltox = bool(response)
			newComp.store('post_update', True)

			TDF.replaceOp(parent.FNS, newComp)
			newComp.destroy()
			# after post_update this will happen
			# op.FNS_CONFIG.LoadAllFromJSON()
		pass
