
'''Info Header Start
Name : ExtParOPPlace
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
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

	def OnPlaceParOp(self, _par = None):
		if not any(_op[0].eval() for _op in self.ownerComp.ops('null_mod_*')):
			return
		
		
		current_parameter = _par if _par is not None else ui.rolloverPar
		if current_parameter is None or current_parameter.owner.family != "COMP":
			return

		current_selected = ui.panes.current.owner.currentChild
		self._update_generic_parameter(current_selected, current_parameter)

	def _update_generic_parameter(self, selected_op, curr_parameter):
			# Determine the appropriate parameters based on enabled flags
			param_name = 'parameters'  # Default parameter attribute name
			operators_param_name = 'ops'
			if self.datExecPreEnabled:
				parameter_instance = self.parameterExecDat
				op_type = 'parameterexecuteDAT'
				op_name = 'parexec1'
				param_name = 'pars'  # Parameter attribute name for parameterexecuteDAT
				operators_param_name = 'op'
			elif self.datPreEnabled:
				parameter_instance = self.parameterDat
				op_type = 'parameterDAT'
				op_name = 'parameter1'
			elif self.chopPreEnabled: # self.chopPreEnabled
				parameter_instance = self.parameterChop
				op_type = 'parameterCHOP'
				op_name = 'parameter1'

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

			if newly_created:
				getattr(parameter_instance.par, param_name).val = curr_parameter.name
				getattr(parameter_instance.par, operators_param_name).expr = TDF.getShortcutPath(parameter_instance, curr_parameter.owner)
			elif curr_parameter.name not in getattr(parameter_instance.par, param_name).val.split(' '):
				getattr(parameter_instance.par, param_name).val += ' ' + curr_parameter.name

			self.parameterExecDat = False
			self.parameterChop = False
			self.parameterDat = False
	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle ParOPDrop', state='Active')
	def ToggleActive(self):
		"""Enable or disable ParOPDrop."""
		self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
		return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
