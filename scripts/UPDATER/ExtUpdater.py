
'''Info Header Start
Name : ExtUpdater
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
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
		# Snapshot every registered tool's settings before the toolkit COMP is
		# replaced. Guarded: a config problem must never block the update.
		cfg = getattr(op, 'CONFIGREGISTRY', None)
		if cfg and cfg.valid and cfg.extensionsReady:
			try:
				cfg.SaveAll()
			except Exception as e:
				debug(f'UPDATER: config save before update failed: {e}')
		else:
			debug('UPDATER: no ConfigRegistry global -- updating without a config snapshot')
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
			# UPDATER-private flag: the fresh toolkit's UPDATER shows the
			# changelog prompt once on its first start. Settings restore is
			# NOT tied to this any more -- every tool's ConfigRegistry host
			# auto-loads its own section when it registers.
			newComp.store('updater_show_changelog', True)

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

	def ShowChangelogAfterUpdate(self):
		"""Offer the changelog once after an update (moved here from the
		legacy FNS_Config OnStart). The flag is stored on the toolkit root by
		OnFileDownloaded and cleared the first time this runs."""
		root = parent.FNS
		if not root.fetch('updater_show_changelog', False, search=False):
			return
		root.unstore('updater_show_changelog')
		run(
			"args[0]._openChangelog() if args[0] else None",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)

	def _openChangelog(self):
		try:
			ret = ui.messageBox('FNS_tools updated', 'Would you like to see the changelog?', buttons=['No', 'Yes'])
			if ret == 1:
				ui.viewFile('https://github.com/function-store/FunctionStore_tools/releases/latest')
		except Exception as e:
			debug(f'UPDATER: changelog prompt failed: {e}')
