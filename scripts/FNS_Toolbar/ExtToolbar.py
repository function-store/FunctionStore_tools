class ExtToolbar:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		
	# def On<Insert Paramname>(self, _par, _val, _prev):
	# def On<Insert PulseParamName>(self, _par):

	def OnInstall(self):
		self.postInit()

	def postInit(self):
		ui.status = 'Installed Custom Toolbar'
		try:
			target = op('/ui/dialogs/bookmark_bar')
		
			containers = op('containers').ops('*')
			containers = sorted(containers, key=lambda x: x.nodeX)
		
			for i, cont in enumerate(containers):
				if _op := target.op(cont.name):
					_op.destroy()
				newOP = target.copy(cont)
				newOP.nodeX = 500 + i*200
				newOP.nodeY = -400
				try:
					if newOP.isPanel:
						newOP.inputCOMPConnectors[0].connect(target.op('emptypanel').outputCOMPConnectors[0])
				except:
					pass
				
			ui.status = 'Function Store - Toolbar installed'
		except:
			pass
