

'''Info Header Start
Name : ExtParOPPlace
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
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

class ExtParOPPlace:
	def __init__(self, ownerComp):
		# Initialization of class variables
		self.ownerComp = ownerComp
		self.chopPreEnabled = False
		self.datPreEnabled = False
		self.datExecPreEnabled = False
		self.parameterChop = None
		self.parameterDat = None
		self.parameterExecDat = None
		fnsLog('ParOPDrop: init')

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def OnChopPre(self, value: bool):
		# Set CHOP pre-enabled state and reset parameter CHOP if disabled
		self.chopPreEnabled = value
		if not value:
			self.parameterChop = None

	def OnDatPre(self, value: bool):
		# Set DAT pre-enabled state and reset parameter DAT if disabled
		self.datPreEnabled = value
		if not value:
			self.parameterDat = None
			
	def OnDatExecPre(self, value: bool):
		# Set DAT pre-enabled state and reset parameter DAT if disabled
		self.datExecPreEnabled = value
		if not value:
			self.parameterExecDat = None

	@staticmethod
	def _rolloverTarget():
		"""The hovered parameter, as a ParGroup when it is genuinely multi-component.

		TD exposes BOTH ui.rolloverPar and ui.rolloverParGroup, so which one
		applies is decided by what is actually under the cursor rather than by
		a fixed preference: hovering tx of t yields the whole group, hovering a
		single-value parameter yields that parameter. ui.rolloverParGroup
		exists from 2025.33070; older builds fall back to the single par.
		"""
		pg = getattr(ui, 'rolloverParGroup', None)
		if pg is not None and len(pg) > 1:
			return pg
		return ui.rolloverPar

	@staticmethod
	def _parNames(target):
		"""Every parameter name the target contributes -- group or single.

		The Parameter CHOP/DAT's `parameters` par is a name list, so a group
		contributes all of its members (tx ty tz) rather than the group name,
		which would not match anything on its own.
		"""
		if hasattr(target, 'pars'):          # ParGroup
			return [p.name for p in target]
		return [target.name]

	# One row per modifier: the CHOP that latches it, the OS name, and the
	# operator that modifier places (cache attribute, type, name, the
	# parameter-list par, the operator-reference par). Ordered by
	# precedence -- the first held one wins (ctrl > shift > alt).
	# The null_mod_* names are historical and do NOT describe what they
	# carry -- verified from their channels: null_mod_dat is shift,
	# null_mod_chop is alt, null_mod_dat1 is ctrl.
	_MODES = (
		('null_mod_dat1', 'ctrl',  'parameterExecDat', 'parameterexecuteDAT', 'parexec1',   'pars',       'op'),
		('null_mod_dat',  'shift', 'parameterDat',     'parameterDAT',        'parameter1', 'parameters', 'ops'),
		('null_mod_chop', 'alt',   'parameterChop',    'parameterCHOP',       'parameter1', 'parameters', 'ops'),
	)

	def _modHeld(self, chop_name, modifier):
		"""One modifier, OS-authoritative where possible, CHOP otherwise.

		The CHOP latches on a missed keyup (alt-tab), which is what makes
		the drop fire when nothing is held. See FNSModifiers."""
		chop = self.ownerComp.op(chop_name)
		raw = bool(chop[0].eval()) if chop is not None else False
		mods = self.ownerComp.op('FNSModifiers')
		if mods is None:
			return raw
		return mods.module.heldOr(modifier, raw)

	def OnPlaceParOp(self, _par = None):
		mode = self._placeMode()
		if mode is None:
			return


		current_parameter = _par if _par is not None else self._rolloverTarget()
		if current_parameter is None or current_parameter.owner.family != "COMP":
			return

		current_selected = ui.panes.current.owner.currentChild
		self._update_generic_parameter(current_selected, current_parameter, mode)

	def _placeMode(self):
		"""The _MODES row for the modifier held RIGHT NOW, or None.

		Decided by _modHeld -- OS-authoritative, CHOP otherwise -- and used
		for BOTH the drop gate and the choice of operator, so the two can
		never disagree. The *PreEnabled flags are not consulted: they are
		the CHOP-latched copy of this state, reset to False on every
		extension reinit and moved only by a CHOP value change, so they
		were False while the OS said a modifier was held -- which is how a
		drop reached the placement code with no operator type chosen
		(UnboundLocalError on op_type).
		"""
		for row in self._MODES:
			if self._modHeld(row[0], row[1]):
				return row
		return None

	def _update_generic_parameter(self, selected_op, curr_parameter, mode):
			_chop, _mod, cache_attr, op_type, op_name, param_name, operators_param_name = mode
			parameter_instance = getattr(self, cache_attr)

			newly_created = False
			
			# Helper function to create a new parameter instance
			def create_new_instance():
				fnsLog(f'ParOPDrop: creating {op_type} for par {curr_parameter.owner.path}.{curr_parameter.name}')
				new_instance = ui.panes.current.owner.create(op_type, op_name)
				new_instance.viewer = True
				new_instance.current = True
				new_instance.nodeCenterX = ui.panes.current.x
				new_instance.nodeCenterY = ui.panes.current.y
				return new_instance
			
			if selected_op and selected_op.opType == op_type:
				# Check if the parameter_instance's operator reference matches curr_parameter.owner
				current_op_path = getattr(selected_op.par, operators_param_name).eval()
				if current_op_path == curr_parameter.owner:
					parameter_instance = selected_op
				else:
					# Create new instance if the referenced operator doesn't match
					parameter_instance = create_new_instance()
					newly_created = True
			elif not parameter_instance:
				parameter_instance = create_new_instance()
				newly_created = True

			par_names = self._parNames(curr_parameter)
			if newly_created:
				getattr(parameter_instance.par, param_name).val = ' '.join(par_names)
				getattr(parameter_instance.par, operators_param_name).expr = TDF.getShortcutPath(parameter_instance, curr_parameter.owner)
			else:
				existing = getattr(parameter_instance.par, param_name).val.split(' ')
				missing = [n for n in par_names if n not in existing]
				if missing:
					getattr(parameter_instance.par, param_name).val += ' ' + ' '.join(missing)

			self.parameterExecDat = False
			self.parameterChop = False
			self.parameterDat = False
	# --- dropped operators (issue #127) ------------------------------------
	#
	# The drop payload NAMES its own type, which is what answers "the Channel
	# inside or `*`" from the issue -- it is not a setting anyone has to
	# choose. A dropped Channel already knows which channel it is; a dropped
	# CHOP names no channel and so means all of them.
	#
	# Par / ParGroup drops still go to OnPlaceParOp: that is the
	# parameter-oriented entry point, and this is the operator-oriented one
	# beside it. Both are reached from the drop callbacks on
	# button_ParOpPlace.

	def OnDropOperator(self, item):
		"""A CHOP / Channel / DAT dropped on the icon -> its Execute DAT.

		Returns the created DAT, or None if the item is not one of those --
		so the caller can hand anything else to another handler.
		"""
		if isinstance(item, Channel):
			return self._createExec('chopexecuteDAT', 'chopexec1',
									{'chop': item.owner, 'channel': item.name},
									('valuechange',))
		if isinstance(item, OP):
			if item.family == 'CHOP':
				# no channel named, so watch every one
				return self._createExec('chopexecuteDAT', 'chopexec1',
										{'chop': item, 'channel': '*'},
										('valuechange',))
			if item.family == 'DAT':
				return self._createExec('datexecuteDAT', 'datexec1',
										{'dat': item}, ('tablechange',))
		return None

	def _createExec(self, op_type, op_name, pars, events):
		"""Create an Execute DAT in the current network, targeted AND armed.

		An Execute DAT ships with every event toggle OFF, so one has to be
		turned on here -- otherwise the drop creates a DAT that can never
		fire, which reads as the drop having silently done nothing.
		"""
		pane = ui.panes.current
		instance = pane.owner.create(op_type, op_name)
		instance.nodeCenterX = pane.x
		instance.nodeCenterY = pane.y
		instance.viewer = True
		instance.current = True
		for name, value in pars.items():
			par = getattr(instance.par, name)
			if isinstance(value, OP):
				# a shortcut-relative expression, never an absolute path
				par.expr = TDF.getShortcutPath(instance, value)
			else:
				par.val = value
		for event in events:
			setattr(instance.par, event, True)
		fnsLog('ParOPDrop: created %s at %s' % (op_type, instance.path))
		return instance

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle ParOPDrop', state='Active')
	def ToggleActive(self):
		"""Enable or disable ParOPDrop."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
