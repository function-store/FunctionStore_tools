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
			# Store docked operators information before replacement
			oldComp = parent.FNS
			docked_ops = []
			for docked_op in oldComp.docked:
				docked_info = {
					'op': docked_op,
					'pos': (docked_op.nodeX, docked_op.nodeY),
				}
				docked_ops.append(docked_info)
				# Undock the operator before replacement
				docked_op.dock = None

			newComp.par.externaltox.mode = ParMode.EXPRESSION
			newComp.par.externaltox.expr = f"f'{{app.userPaletteFolder}}/FNStools_ext/{fp.baseName}'"
			newComp.par.Gittag = self.newTag
			newComp.par.savebackup = True
			newComp.store('post_update', True)

			TDF.replaceOp(parent.FNS, newComp)
			newComp.destroy()

			# Restore docked operators
			newComp = parent.FNS
			for dock_info in docked_ops:
				docked_op = dock_info['op']
				if docked_op:
					# Restore position first
					docked_op.nodeX, docked_op.nodeY = dock_info['pos']
					# Then re-dock
					docked_op.dock = newComp
		pass
