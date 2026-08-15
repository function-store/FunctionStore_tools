
'''Info Header Start
Name : ExtToolbar
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

class ExtToolbar:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		if (_table := self.ownerComp.op('ToolbarDef')) and _table.text.strip() == '':
			_table.text = self.ownerComp.op('ToolbarDef_default').text
		if _table and _table.text.strip() != '':
			_table.save(_table.par.file.eval(), createFolders=True)
		fnsLog('FNS_Toolbar: init')

	# def On<Insert Paramname>(self, _par, _val, _prev):
	# def On<Insert PulseParamName>(self, _par):

	def OnInstall(self):
		self.postInit()

	def postInit(self):
		ui.status = 'Installed Custom Toolbar'
		fnsLog('FNS_Toolbar: installing toolbar into /ui/dialogs/bookmark_bar')
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

	def CreatePars(self):
		owner = self.ownerComp
		seq = owner.seq.Def
		containers: COMP = op('containers')
		children = containers.findChildren(tags=['FNS'])

		# order children by _child.par.alignorder.eval()
		children = sorted(children, key=lambda _child: _child.par.alignorder.eval())
		numChildren = len(children)
		seq.numBlocks = numChildren-1

		for _block, _child in zip(seq.blocks, children):
			_block.par.Comp = _child.name
			_block.par.Order = _child.par.alignorder.eval()-self.ownerComp.par.Layoutstart.eval()

	def OnResetdefs(self):
		fnsLog('FNS_Toolbar: resetting toolbar definition to defaults')
		mainTable = self.ownerComp.op('ToolbarDef')
		defaultTable = self.ownerComp.op('ToolbarDef_default')

		mainTable.clear()
		mainTable.text = defaultTable.text

