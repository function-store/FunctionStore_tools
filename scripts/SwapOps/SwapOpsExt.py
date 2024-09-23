class SwapOpsExt:
	"""
	SwapOpsExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	def OnSwap(self):
		selected = ui.panes.current.owner.selectedChildren
		selected = sorted(selected, key=lambda x: x.nodeCenterX)
		num_selected = len(selected)
		
		ui.undo.startBlock("Swap selected OPs")
		# reversed effect: middle-out order
		for i in reversed(range(int(num_selected/2))):
			op_a = selected[i]
			op_b = selected[num_selected-i-1]
			self.swapPosition(op_a, op_b)
			self.swapConnectorsMult(op_a, op_b)
		ui.undo.endBlock()
		
	def swapPosition(self, op1: OP, op2: OP):
		# Save the current positions of the operators
		x1, y1 = op1.nodeCenterX , op1.nodeCenterY 
		x2, y2 = op2.nodeCenterX , op2.nodeCenterY
		op1.nodeCenterX, op1.nodeCenterY = x2, y2
		op2.nodeCenterX, op2.nodeCenterY = x1, y1

	def swapConnectorsMult(self, op1: OP, op2: OP):
		# "leftmost" is always the male
		orig_male_op = op1 
		orig_male_inputs = orig_male_op.inputs.copy()
		orig_male_outputs = orig_male_op.outputs.copy()
		orig_female_op = op2 
		orig_female_inputs = orig_female_op.inputs.copy()
		orig_female_outputs = orig_female_op.outputs.copy()

		# prepare for annoying edge case
		middle_op_inputs = None
		if middle_op := list(set(orig_male_outputs).intersection(set(orig_female_inputs))):
			# if there was an OP in between the two swapping ones 
			# and that OP had multi-ins
			# then we do this to keep the order after connecting new male outs
			# see annoying edge case comments
			middle_op = middle_op[0]
			middle_op_inputs = middle_op.inputs.copy()

		for _, _ in enumerate(orig_male_op.inputConnectors):
			orig_male_op.inputConnectors[0].disconnect()
		for _, _ in enumerate(orig_male_op.outputConnectors):
			orig_male_op.outputConnectors[0].disconnect()
		for _, _ in enumerate(orig_female_op.inputConnectors):
			orig_female_op.inputConnectors[0].disconnect()
		for _, _ in enumerate(orig_female_op.outputConnectors):
			orig_female_op.outputConnectors[0].disconnect()

		new_male_op, new_female_op = orig_female_op, orig_male_op # "switch" 
		

		## easy ones ##
		 	
		# new female outs to original female outs
		for idx, ofo in enumerate(orig_female_outputs):
			new_female_op.outputConnectors[0].connect(ofo)

		# if they were connected (next to eachother) connect them again (swapped)
		if orig_female_op in orig_male_outputs:
			new_male_op.outputConnectors[0].connect(new_female_op.inputConnectors[0])
			
		## edge casing ##

		if (not new_female_op.isMultiInputs) and (not new_male_op.isMultiInputs):
			# if both have multi-inputs (not sure why this attribute is the opposite...)
			# then we swap everything
			for idx, omi in enumerate(orig_male_inputs):
				new_male_op.inputConnectors[idx].connect(omi)
			
			for idx, ofi in enumerate(orig_female_inputs):
				if ofi != new_female_op:
					new_female_op.inputConnectors[idx].connect(ofi)
		elif new_male_op.isMultiInputs and (not new_female_op.isMultiInputs):
			# if orig male had multi ins but new male does not (again this bool is inverted...)	
			# then we keep the multi-ins in the new female
			new_male_op.inputConnectors[0].connect(orig_male_inputs[0])	

			# skip first connector as it's now connected to new male
			for idx, omi in enumerate(orig_male_inputs[1:]):
				if omi != orig_male_op:
					new_female_op.inputConnectors[1+idx].connect(omi)
		elif new_female_op.isMultiInputs and (not new_male_op.isMultiInputs):
			# if orig female had multi ins but new female does not (again this bool is inverted...)	
			# then we keep the multi-ins in the new male
			new_male_op.inputConnectors[0].connect(orig_male_inputs[0])	

			# skip first connector as it's now connected to new male
			for idx, ofi in enumerate(orig_female_inputs[1:]):
				if ofi != orig_female_op:
					new_male_op.inputConnectors[1+idx].connect(ofi)
			pass
		else:
			# both are "single input"
			limit_len = min(len(orig_male_inputs),len(new_male_op.inputConnectors))
			for omi in orig_male_inputs[:limit_len]:
				if omi != new_male_op:
					new_male_op.inputConnectors[0].connect(omi)


			#dirty...
			if middle_op:
				# this was the original case
				for ofi in orig_female_inputs:
					if ofi != orig_male_op:
						new_female_op.inputConnectors[0].connect(ofi)
			else:
				new_female_op.inputConnectors[0].connect(orig_female_op.outputConnectors[0])
			
		# annoying edge case
		if middle_op_inputs:
			for _, _ in enumerate(middle_op.inputConnectors):
				middle_op.inputConnectors[0].disconnect()

		# normal case
		for omo in orig_male_outputs:
			if omo not in new_male_op.outputs and omo != new_male_op:
				new_male_op.outputConnectors[0].connect(omo)
				pass

		# annoying edge case
		if middle_op_inputs:
			for idx, moi in enumerate(middle_op_inputs[1:]):
				if orig_male_op != moi:
					middle_op.inputConnectors[1+idx].connect(moi)

	