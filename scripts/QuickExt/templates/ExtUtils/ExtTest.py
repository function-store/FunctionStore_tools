CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
NoNode: NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
####

class ExtTest:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		NoNode.Init(ownerComp, enable_chopexec=True, enable_datexec=True, enable_keyboard_shortcuts=True, enable_parexec=True)
		NoNode.SetMarkColor((0.5, 0.05, 0.5))
		
		# CHOP Exec tests
		NoNode.RegisterChopExec(NoNode.ChopExecType.ValueChange, self.ownerComp.op('null_test_chopexec'), 'v1', self.onTestChopValueChange)
		NoNode.RegisterChopExec(NoNode.ChopExecType.OffToOn, self.ownerComp.op('null_test_chopexec'), 'v*, v2', self.onTestChopOffToOn)
		NoNode.RegisterChopExec(NoNode.ChopExecType.OnToOff, self.ownerComp.op('null_test_chopexec'), ['v1', 'v2'], self.onTestChopOnToOff)
		#NoNode.RegisterChopExec(NoNode.ChopExecType.WhileOn, self.ownerComp.op('null_test_chopexec'), '*', self.onTestChopWhileOn)
		#NoNode.RegisterChopExec(NoNode.ChopExecType.WhileOff, self.ownerComp.op('null_test_chopexec'), '*', self.onTestChopWhileOff)
		
		# DAT Exec tests
		NoNode.RegisterDatExec(NoNode.DatExecType.TableChange, self.ownerComp.op('null_test_datexec'), self.onTestDatExecTableChange)
		NoNode.RegisterDatExec(NoNode.DatExecType.RowChange, self.ownerComp.op('null_test_datexec'), self.onTestDatExecRowChange)
		NoNode.RegisterDatExec(NoNode.DatExecType.ColChange, self.ownerComp.op('null_test_datexec'), self.onTestDatExecColChange)
		NoNode.RegisterDatExec(NoNode.DatExecType.CellChange, self.ownerComp.op('null_test_datexec'), self.onTestDatExecCellChange)
		NoNode.RegisterDatExec(NoNode.DatExecType.SizeChange, self.ownerComp.op('null_test_datexec'), self.onTestDatExecSizeChange)
		NoNode.DisableDatExec()

		# Keyboard shortcut test
		NoNode.RegisterKeyboardShortcut('ctrl.t', self.onTestKeyboardShortcut)

		# Parexec tests
		NoNode.RegisterParExec(NoNode.ParExecType.ValueChange, 'Float', self.onTestParValueChange)
		NoNode.RegisterParExec(NoNode.ParExecType.OnPulse, 'Pulse', self.onTestParOnPulse)
		NoNode.RegisterParExec(NoNode.ParExecType.ValueChange, self.ownerComp.par.Testseq0float, self.onTestParSeqValueChange)

	# CHOP Exec callbacks
	def onTestChopValueChange(self, _channel, _sampleIndex, _val, _prev):
		debug(f'onTestChopValueChange: {_channel.name} {_sampleIndex} {_val} {_prev}')

	def onTestChopValueChange2(self, _channel, _sampleIndex, _val, _prev):
		debug(f'onTestChopValueChange2: {_channel.name} {_sampleIndex} {_val} {_prev}')

	def onTestChopOffToOn(self, _channel, _sampleIndex, _val, _prev):
		debug(f'onTestChopOffToOn: {_channel.name} {_sampleIndex} {_val} {_prev}')

	def onTestChopOnToOff(self, _channel, _sampleIndex, _val, _prev):
		debug(f'onTestChopOnToOff: {_channel.name} {_sampleIndex} {_val} {_prev}')

	def onTestChopWhileOn(self, _channel, _sampleIndex, _val, _prev):
		debug(f'onTestChopWhileOn: {_channel.name} {_sampleIndex} {_val} {_prev}')

	def onTestChopWhileOff(self, _channel, _sampleIndex, _val, _prev):
		debug(f'onTestChopWhileOff: {_channel.name} {_sampleIndex} {_val} {_prev}')

	# DAT Exec callbacks
	def onTestDatExecTableChange(self, _dat):
		debug(f'onTestDatExecTableChange: {_dat}')

	def onTestDatExecRowChange(self, _dat, _row):
		debug(f'onTestDatExecRowChange: {_dat} {_row}')

	def onTestDatExecColChange(self, _dat, _col):
		debug(f'onTestDatExecColChange: {_dat} {_col}')

	def onTestDatExecCellChange(self, _dat, _cells, _prev):
		debug(f'onTestDatExecCellChange: {_dat} {_cells} {_prev}')

	def onTestDatExecSizeChange(self, _dat):
		debug(f'onTestDatExecSizeChange: {_dat}')

	# Keyboard shortcut callback
	def onTestKeyboardShortcut(self):
		debug('onTestKeyboardShortcut: ctrl+t pressed')

	# # Existing parameter callbacks
	# def onParFloat(self, _par, _val, _prev):
	# 	debug(f'onParFloat: {_par} {_val} {_prev}')

	# def onParPulse(self, _par):
	# 	debug(f'onParPulse: {_par}')
	# 	print('printing parameters as self.par<Parname> properties:', self.parFloat, self.parPulse, self.parGroupInt)
	# 	print('printing parameters as self.eval<Parname> properties:', self.evalFloat, self.evalPulse, self.evalGroupInt)

	# def onParGroupInt(self, _parGroup, _val):
	# 	debug(f'onParGroupInt: {_parGroup} {_val}')

	# def onSeqTestseqN(self, idx):
	# 	debug(f'onSeqTestN: {idx}')

	# def onSeqTestseqNfloat(self, _par, idx, _val, _prev):
	# 	debug(f'onSeqTestNFloat: {_par} {idx} {_val} {_prev}')

	# def onSeqTestseqNstr(self, _par, idx, _val, _prev):
	# 	debug(f'onSeqTestNStr: {_par} {idx} {_val} {_prev}')

	# Parexec callbacks
	def onTestParValueChange(self, _par, _val):
		debug(f'onTestParValueChange: {_par.name} {_val}')

	def onTestParOnPulse(self):
		debug(f'onTestParOnPulse')

	def onTestParSeqValueChange(self, _par, _val):
		debug(f'onTestParSeqValueChange: {_par.name} {_val}')

