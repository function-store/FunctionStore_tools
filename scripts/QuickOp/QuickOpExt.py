from enum import Enum, auto

class FamilyOrder(Enum):
	COMP = auto()
	TOP = auto()
	CHOP = auto()
	SOP = auto()
	MAT = auto()
	DAT = auto()
	CUSTOM = auto()

class QuickOpExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

		self.lastSelectedPos = {}
		self.newPos = (0,0)

		self.MenuOp = op('/ui/dialogs/menu_op')
		self.familyPanel = op('/ui/dialogs/menu_op/families/family').panel
		self.nodeScript = op('/ui/dialogs/menu_op/node_script')
		self.NodeTable = op('/ui/dialogs/menu_op/nodetable')
		self.opTable = op('/ui/dialogs/menu_op/op_table')
		self.connecttoTable = op('/ui/dialogs/menu_op/connectto')
		self.menuLocal = op('/ui/dialogs/menu_op/local/set_variables')

		self.newOpPending = False
		self.menuClicked = False
		self.origOp = None
		self.isInsert = False

	@property
	def hk_add(self) -> bool:
		return bool(self.ownerComp.op('null_hk')['add'].eval())
	
	@property
	def hk_insert(self) -> bool:
		return bool(self.ownerComp.op('null_hk')['insert'].eval())

	def OnUIChange(self, _op: OP) -> None:
		if not (self.hk_add or self.hk_insert):
			return
		self.isInsert = self.hk_insert

		new_pos = (_op.nodeX, _op.nodeY)
		if new_pos != self.lastSelectedPos:
			self.onPosChange(_op, new_pos, self.lastSelectedPos)


	def onPosChange(self, _op, new_pos, last_pos) -> None:
		self.origOp = _op
		self.newPos = new_pos
		self.newOpPending = True

		self.OverrideNodeScriptActive(False)
		# VERY DANGEROUS, THIS CAN BREAK OP CREATE IF NOT RE-ENABLED!
		# So we add a broad try-except block to ensure it gets re-enabled
		try:
			self.MenuOp.par.winopen.pulse()
			self.setFamily(self.origOp.family)
			
			self.MenuOp.op('search/textfield').panel.field = ''
			self.MenuOp.op('search/textfield').setKeyboardFocus()

			# restore pos
			self.origOp.nodeX = last_pos['op_pos'][0]
			self.origOp.nodeY = last_pos['op_pos'][1]

			for _dock in self.origOp.docked:
				if _dock in last_pos['docked_pos'].keys(): 
					_dock.nodeX = last_pos['docked_pos'][_dock][0]
					_dock.nodeY = last_pos['docked_pos'][_dock][1]
		except:
			self.OverrideNodeScriptActive(True)
			self.OnCancel()


	def OnOpCreate(self, sel_id):
		if not (self.menuClicked and self.newOpPending):
			return
		
		self.OverrideNodeScriptActive(False)
		# VERY DANGEROUS, THIS CAN BREAK OP CREATE IF NOT RE-ENABLED!
		# So we add a broad try-except block to ensure it gets re-enabled
		try:
			self.MenuOp.par.winclose.pulse()

			owner = self.origOp.parent()
			if not owner:
				return
			opType = self.id_to_opType(sel_id)
			name = self.id_to_name(sel_id)

			ui.undo.startBlock('Creating OP (QuickOp)')

			new_op = owner.create(opType, name)

			ui.undo.endBlock()

			new_op.nodeX = self.newPos[0]
			new_op.nodeY = self.newPos[1]

			if self.isInsert and len(self.origOp.outputConnectors):
				if len(new_op.outputConnectors) and len(self.origOp.outputConnectors):
					if output_conn := new_op.outputConnectors[0]:
						if conns := self.origOp.outputConnectors[0].connections:
							for conn in conns:
								output_conn.connect(conn)
			if len(new_op.inputConnectors) and len(self.origOp.outputConnectors):
				if input_conn := new_op.inputConnectors[0]:
					input_conn.connect(self.origOp)


			new_op.cook(force=True)
			self.origOp.selected = False
			new_op.current = True
			new_op.selected = True
			new_op.viewer = True

			self.OverrideNodeScriptActive(True)
			self.OnCancel()
		except:
			self.OverrideNodeScriptActive(True)
			self.OnCancel()

	
	def id_to_opType(self, id):
		return self.opTable[id+1,'opType']
	

	def id_to_name(self, id):
		return self.opTable[id+1,'name']


	def OnSelectOP(self, _op):
		self.lastSelectedPos = {'op_pos': (_op.nodeX, _op.nodeY), 'docked_pos': {_dock: (_dock.nodeX, _dock.nodeY) for _dock in _op.docked}}

	def OnFocusLoss(self) -> None:
		if not self.menuClicked:
			self.newOpPending = False
		self.menuClicked = False
		self.isInsert = False
		self.OverrideNodeScriptActive(True)
		return
	
	def OnMenuClick(self) -> None:
		self.menuClicked = True
		self.OverrideNodeScriptActive(True)
		return
	
	def OnCancel(self) -> None:
		self.newOpPending = False
		self.menuClicked = False
		self.isInsert = False
		self.OverrideNodeScriptActive(True)


	def OverrideNodeScriptActive(self, _bool):
		# VERY DANGEROUS, THIS CAN BREAK OP CREATE IF NOT RE-ENABLED!
		self.nodeScript.par.active = _bool


	def setFamily(self, sel_fam):
		self.connecttoTable[0,0] = sel_fam
		self.connecttoTable[0,1] = 'output'
		self.menuLocal['menu_type', 1] = sel_fam
		self.menuLocal['menu_pane', 1] = ui.panes.current

		self.familyPanel.cellradioid = FamilyOrder[sel_fam].value-1
