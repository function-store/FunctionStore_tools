
'''Info Header Start
Name : SmoothnessExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
import TDFunctions as TDF

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass




FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class SmoothnessExt:
	"""
	SmoothnessExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		fnsLog('SetSmoothness: init')

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def OnSelected(self):
		selected = ui.panes.current.owner.selectedChildren
		self.setSmoothness(selected)

	def OnAll(self):
		selected = ui.panes.current.owner.ops('*')
		self.setSmoothness(selected)

	def modifierHeld(self):
		"""Whether the tool's modifier (the Keys parameter, `alt` on every
		platform) is held right now -- the "set all in the network" case.

		Asks the OS through FNSModifiers, which is immune to the missed keyup
		that leaves a Keyboard In latched after an alt-tab; where the OS
		cannot be asked it falls back to the button's key-state chain
		(null_hk), fed by the Keyboard In DAT's `state` column so it follows
		whatever key Keys names. It used to read the DAT's `alt` column, which
		only ever answered for the Alt key itself.
		"""
		keys = str(self.ownerComp.par.Keys.eval()).split()
		modifier = keys[0].lower().lstrip('lr') if keys else 'alt'
		hk = self.ownerComp.op('inputsmoothness1/null_hk')
		raw = bool(hk[0].eval()) if hk is not None else False
		mods = self.ownerComp.op('FNSModifiers')
		if mods is None:
			return raw
		return mods.module.heldOr(modifier, raw)

	def applyPicked(self, index):
		"""The popup menu's selection: set both filter menus to `index`, then
		apply to every TOP in the network when the modifier is held, to the
		selected ones otherwise. Wiring for popMenuConfig/callbacks."""
		self.ownerComp.par.Inputfiltertype.menuIndex = index
		self.ownerComp.par.Filtertype.menuIndex = index
		if self.modifierHeld():
			self.OnAll()
		else:
			self.OnSelected()
		
	def setSmoothness(self, _ops):
		fnsLog(f'SetSmoothness: setting smoothness on {len(_ops)} ops')
		insmooth = parent().par.Inputfiltertype.menuIndex
		viewsmooth = parent().par.Filtertype.menuIndex

		ui.undo.startBlock('Set smoothness')
		tops = list(filter(lambda _op: _op.family == 'TOP' and _op.pars('inputfiltertype', 'filtertype') ,_ops))
		
		for top in tops:
			top.par.inputfiltertype = insmooth
			top.par.filtertype = viewsmooth+1 #skipping same as input
				
		comps = list(filter(lambda _op: _op.family == 'COMP' and _op.pars('Inputfiltertype', 'Filtertype'), _ops))
		for comp in comps:
			# a COMP qualifies with EITHER parameter; assign only the ones it
			# has (RealRamp carries both, a generator may carry just Filtertype)
			if comp.pars('Inputfiltertype'):
				comp.par.Inputfiltertype = insmooth
			if comp.pars('Filtertype'):
				comp.par.Filtertype = viewsmooth+1 #skipping same as input
		ui.undo.endBlock()

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Smoothness -> selected', context='selected')
	def SmoothnessSelected(self):
		"""Apply the smoothness setting to the selected operators."""
		self.OnSelected()
		return {'ok': True}

	@FNSCommand.fns_command(label='Smoothness -> all', context='network')
	def SmoothnessAll(self):
		"""Apply the smoothness setting to all operators in the network."""
		self.OnAll()
		return {'ok': True}
