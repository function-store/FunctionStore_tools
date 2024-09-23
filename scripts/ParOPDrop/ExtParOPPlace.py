
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
		if not (self.chopPreEnabled or self.datPreEnabled or self.datExecPreEnabled):
			return

		current_parameter = _par if _par is not None else ui.rolloverPar

		if current_parameter is None or current_parameter.owner.family != "COMP":
			return

		current_selected = ui.panes.current.owner.currentChild
		self._update_generic_parameter(current_selected, current_parameter)

	def _update_generic_parameter(self, selected_op, curr_parameter):
			# Determine the appropriate parameters based on enabled flags
			param_name = 'parameters'  # Default parameter attribute name
			if self.datExecPreEnabled:
				parameter_instance = self.parameterExecDat
				op_type = 'parameterexecuteDAT'
				op_name = 'parexec1'
				param_name = 'pars'  # Parameter attribute name for parameterexecuteDAT
			elif self.chopPreEnabled:
				parameter_instance = self.parameterChop
				op_type = 'parameterCHOP'
				op_name = 'parameter1'
			elif self.datPreEnabled:
				parameter_instance = self.parameterDat
				op_type = 'parameterDAT'
				op_name = 'parameter1'

			newly_created = False
			if selected_op and selected_op.opType == op_type:
				parameter_instance = selected_op
			elif not parameter_instance:
				parameter_instance = curr_parameter.owner.create(op_type, op_name)
				parameter_instance.viewer = True
				parameter_instance.current = True
				newly_created = True

			if newly_created:
				getattr(parameter_instance.par, param_name).val = curr_parameter.name
				if op_type == 'parameterexecuteDAT':
					parameter_instance.par.op.val = '..'
			elif curr_parameter.name not in getattr(parameter_instance.par, param_name).val.split(' '):
				getattr(parameter_instance.par, param_name).val += ' ' + curr_parameter.name

			# Update the instance back to the class variable
			if self.datExecPreEnabled:
				self.parameterExecDat = False
			elif self.chopPreEnabled:
				self.parameterChop = False
			elif self.datPreEnabled:
				self.parameterDat = False