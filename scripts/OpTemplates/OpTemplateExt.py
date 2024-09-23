from functools import cached_property
from collections import defaultdict
import itertools
import os
import re
import TDFunctions

class OpTemplateExt:

	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.op_families = [fam.__name__ for fam in OP.__subclasses__()]
		self.pop_tab = self.ownerComp.op('table_pop_templates')
		self.pendingOrigOP = None
		self.pendingTemplates = []
		self.all_optypes = self.getAllOptypes()
		self.defaultTemplates = op('OPTemplates1')
		self.extFolder = app.userPaletteFolder + '/FNStools_ext/OpTemplates'
		self.inputOpTypes = ['inTOP','inCHOP','inSOP','inMAT','inDAT']
		self.outputOpTypes = ['outTOP','outCHOP','outSOP','outMAT','outDAT']
		self.opFamilyConvertTypes = ['choptoTOP','dattoCHOP','toptoCHOP','soptoCHOP',
			       					'choptoDAT','soptoDAT','chopexecDAT',
									'choptoSOP','trailSOP']
		self.logger = op('logger1')

	def getAllOptypes(self):
		all_optypes = []
		bigfams = [OP, COMP]
		for bigfam in bigfams:
			for sub in bigfam.__subclasses__():
				for _optype in sub.__subclasses__():
					all_optypes.append(_optype.__name__)
	
		return all_optypes
	
	@property
	def templatesCOMP(self):
		return templates if (templates := self.ownerComp.par.Templates.eval()) else self.defaultTemplates

	@property
	def hotkey(self):
		return bool(self.ownerComp.op('null_hk')[0])
	
	def find_keywords_in_input(self, keywords, input):
		for k in keywords:
			if k in input:
				return k
	

	@cached_property
	def Templates(self) -> dict[str, OP]:
		# Templates can be
		templates = self.templatesCOMP
		
		all_ops = list(itertools.chain.from_iterable(_comp.ops('*') for _comp in templates.ops('*')))

		_ops = list(filter(lambda _op: not _op.inputs and _op.family in self.op_families and not _op.dock, all_ops))
		# for COMPs need to have the OP type name in their name
		# we add the name to the list and use this rule later
		types_ops = defaultdict(list)
		for _op in _ops:
			types_ops[_op.parent().name].append(_op)

		return types_ops
	
	def log(self, smth):
		self.logger.Log(smth)
	

	def OnNewOp(self, _op: OP):
		if not self.hotkey:
			return
		if _op.family not in self.op_families:
			return
		
		#list Templates
		template_ops = self.Templates[_op.OPType]
		if not template_ops:
			return
		
		self.pop_tab.clear()
		self.pop_tab.appendRow([_op.OPType, 'path'])
		
		for template in template_ops:
			self.pop_tab.appendRow([template.name, template.path])
			
		if len(template_ops) > 1:
			self.pendingTemplates = template_ops
			self.pendingOrigOP = _op
			self.updateTitleColor(_op.family)
			self.ownerComp.op('popMenu').par.Open.pulse()
			# we pop the menu and place later
			return
				
		self.PlaceTemplate(_op, template_ops)


	def PlaceTemplate(self, orig_op = None, template_ops = None):
		if not orig_op:
			orig_op = self.pendingOrigOP
		if not template_ops:
			template_ops = self.pendingTemplates
		if orig_op and template_ops:
			self.placeOPchain(orig_op, template_ops)
			
		self.ownerComp.op('kindergaertner_mymod').Refresh()


##################### BULKY GOODS #####################
	def placeOPchain(self, orig_op, template_ops):
		'''
		Handles single operators, operator chains, docked operators, as well as inserting between operators,
		and restoring relative positions --- all at the same time
		'''

		def index_connections(orig_op, op_attr, conn_attr):
			'''
			`index` attribute of OP.outputs[0].inputConnectors[0].connections seems incorrect?
			This method builds a structure of OP:[indices] as in input/output connections for all slots (indexed) of all original output/input ops.

			op_attr in [inputs, outputs]
			connn_attr in [outputConnectors, inputConnectors]
			'''
			conns_indexed = defaultdict(list)
			for inOp in set(getattr(orig_op, op_attr)):
				for idx, _connector in enumerate(getattr(inOp, conn_attr)):
					for _connection in _connector.connections:
						if _connection and _connection.owner is orig_op:
							conns_indexed[inOp].append(idx)
			return conns_indexed
		
		def restore_connections(conns_indexed, connector_attr, new_op):
			'''restore original connections before replacing the template with one or more ops/comps
			connector_attr == inputConnectors /// outputConnectors'''
			to_connect = new_op
			if conns_indexed:
				for op, indices in conns_indexed.items():
					for connector_idx in indices:
						# this is gonna look weird, but in case of COMPS we are not simply connecting to an OP but a connector
						if new_op.family == 'COMP':
							invert_conn_attr = 'outputConnectors' if connector_attr == 'inputConnectors' else 'inputConnectors'
							to_connect = getattr(new_op, invert_conn_attr)[0]
							if not to_connect:
								return
							
						getattr(op, connector_attr)[connector_idx].connect(to_connect)
							
		def bfs(op):
			'''breadth first search'''
			from collections import deque
			visited = set([op])
			queue = deque([op])
			result = []
			while queue:
				op = queue.popleft()
				if op:
					result.append(op)
					for output in op.outputs:
						if output not in visited:
							visited.add(output)
							queue.append(output)
			return result
		
		def get_new_root(_parent, orig_type):
			new_root_op = _parent.findChildren(tags=['TEMPLATE_ROOT'], depth=1) # TODO: adding `type=orig_type` to the search breaks 
																				#SystemError: <built-in method findChildren of td.baseCOMP object at 0x0000021F5322BF00> returned a result with an error set 
			new_root_op = sorted(new_root_op, key=lambda _op: _op.OPType == orig_type) # prioritize this attribute
			if new_root_op:
				new_root_op = new_root_op[0]
				return new_root_op

		def new_ops_bfs_sorted(_parent, orig_type):
			new_root_op = get_new_root(_parent, orig_type)
			new_ops = bfs(new_root_op)
			return new_ops

		def get_famconvert(orig_op):
			if orig_op.OPType not in self.opFamilyConvertTypes:
				return None
			from_type = next((sub.lower() for sub in self.op_families if sub.lower() in orig_op.OPType), None)

			if from_type:
				if hasattr(orig_op.par, from_type):
					return (from_type, getattr(orig_op.par, from_type).val)
			return 
			
		def set_famconvert(new_op, orig_famconvert):
			if hasattr(new_op.par, orig_famconvert[0]):
				setattr(new_op.par, orig_famconvert[0], orig_famconvert[1])

		# save all relevant info before destroying
		template_op = template_ops[0]
		_parent = orig_op.parent()
		op_pos = (orig_op.nodeX, orig_op.nodeY)
		orig_type = orig_op.OPType
		orig_famconvert = get_famconvert(orig_op)

		# Build a structure of OP:[indices] 
		# meaning input/output connections (OPs) for all in/out slots (indexed) of all original output/input ops.
		in_conns_indexed = index_connections(orig_op, 'inputs', 'outputConnectors')
		out_conns_indexed = index_connections(orig_op, 'outputs', 'inputConnectors')

		# bye-bye
		orig_op.destroy()
  
		ui.undo.startBlock(f'Replacing {orig_op.path} with template!')
		
		to_clean = []
		if template_op.OPType == 'baseCOMP':
			self.primeNewCOMPTemplate(template_op) # making sure
			ops_to_copy = template_ops[0].findChildren(depth=1)

			if template_op.inputConnectors and (_roots := template_op.inputConnectors[0].inOP.outputs):
				ops_to_copy.remove(template_op.inputConnectors[0].inOP)
				for _op in _roots:
					_op.tags.add('TEMPLATE_IN')
					_op.tags.add('TEMPLATE_ROOT')
					to_clean.append(_op)
			else:
				_root = template_op.findChildren(key=lambda _op: _op.OPType == orig_type and not _op.inputs)

				if _root:
					for _r in _root:
						to_clean.append(_r)
					_root = _root[0]
				else:
					_root = ops_to_copy[0]
					for _r in ops_to_copy:
						to_clean.append(_r)
				_root.tags.add('TEMPLATE_ROOT')
			
			if template_op.outputConnectors and (_outs := template_op.outputConnectors[0].outOP.inputs):
				_outs[0].tags.add('TEMPLATE_OUT')			
				for _out in _outs:
					to_clean.append(_out)
				ops_to_copy.remove(template_op.outputConnectors[0].outOP)
			else:
				to_clean.append(_root)
		else:
			# we have to tag something as TEMPLATE_ROOT from operators to copy
			# op-chain case
			template_op.tags.add('TEMPLATE_ROOT')
			to_clean.append(template_op)
			ops_to_copy = bfs(template_op)
			
			if orig_famconvert:
				set_famconvert(template_op, orig_famconvert)
		
		for _op in ops_to_copy:
			_op.tags.add('TEMPLATE_COPY')
			to_clean.append(_op)

		# wish I found these methods earlier
		ui.copyOPs(ops_to_copy)
		ui.pasteOPs(_parent, x=op_pos[0], y=op_pos[1]) # wish this returned the pasted OP references
		
		for new_op in _parent.findChildren(tags=['TEMPLATE_COPY'], depth=1):
			new_op.bypass = False
			new_op.allowCooking = True
			new_op.tags.remove('TEMPLATE_COPY')

		# now we need to reconnect the ins and outs if any... gonna be a bit messy :)

		# below is only relevant when chaining OPs
		# check if we had inOPs, easy case
		if new_in_ops := _parent.findChildren(tags=['TEMPLATE_IN'], depth=1):
			for _op in new_in_ops:
				restore_connections(in_conns_indexed, 'outputConnectors', _op)
				_op.tags.remove('TEMPLATE_IN')
		else:
			# if we didn't have any inOPs we use our guess tagged as TEMPLATE_ROOT for the input, and finding the output
			# first in list should be the reference op
			_inOP = get_new_root(_parent, orig_type)
			
			to_clean.append(_inOP)
			restore_connections(in_conns_indexed, 'outputConnectors', _inOP)
		
		if new_out_ops := _parent.findChildren(tags=['TEMPLATE_OUT'], depth=1):
			_outOP = new_out_ops[0]
			for _op in new_out_ops:
				_op.tags.remove('TEMPLATE_OUT')
		else:
			# this is our best bet what the last op in the chain is
			new_ops = new_ops_bfs_sorted(_parent, orig_type)
			if new_ops:
				_outOP = new_ops[-1]
			else:
				_outOP = None

		if _outOP:
			if 'TEMPLATE_ROOT' in _outOP.tags:
				_outOP.tags.remove('TEMPLATE_ROOT')
			restore_connections(out_conns_indexed, 'inputConnectors', _outOP)

		self.clean_all_tags(_parent)		
		# for _op_clean in to_clean:
		# 	self.clean_tags(_op_clean, _parent)

		ui.undo.endBlock()
		self.pendingOrigOP = None

	def clean_all_tags(self, _parent):
		_tags = ['TEMPLATE_OUT', 'TEMPLATE_IN', 'TEMPLATE_COPY', 'TEMPLATE_ROOT']
		for _op in _parent.findChildren(tags=_tags, depth=1):
			for tag in _tags:
				if tag in _op.tags:
					_op.tags.remove(tag)

	def clean_tags(self, _op, _parent):
		_tags = ['TEMPLATE_OUT', 'TEMPLATE_IN', 'TEMPLATE_COPY', 'TEMPLATE_ROOT']
		for tag in _tags:
			if tag in _op.tags:
				_op.tags.remove(tag)



####################################################################	

	def DropOp(self, _op):
		comp = self.createOrReturnTypeBase(_op.OPType, allowCooking=False)
		self.colorNewBase([comp])
		new_op = comp.copy(_op, includeDocked=True)
		TDFunctions.arrangeNode(new_op)
		self.RefreshCachedTemplates()
		return
	
	def createOrReturnTypeBase(self, optype, allowCooking=True):
		temps = self.templatesCOMP
		if comps := temps.findChildren(name=optype):
			comp = comps[0]
		else:
			comp = temps.create(baseCOMP, optype)
			TDFunctions.arrangeNode(comp)
			comp.allowCooking = allowCooking
		return comp

	def OpenTemplateBase(self, optype):
		comp = self.createOrReturnTypeBase(optype)
		self.colorNewBase([comp])
		self.RefreshCachedTemplates()
		p = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name=optype)
		p.owner = comp

	def colorNewBase(self, new_ops):
		for _op in new_ops:
			if _op.parent() == self.templatesCOMP and _op.OPType == 'baseCOMP':
				self.ColorBaseCOMPbyName(_op)

	def OnTemplatesUpdate(self, new_ops):
		self.RefreshCachedTemplates()
		self.colorNewBase(new_ops)
		pass


	def RefreshCachedTemplates(self):
		if hasattr(self, 'Templates'):  # This will check if 'my_property' is cached
			del self.__dict__['Templates']


	def ColorBaseCOMPbyName(self, _op):
		def find_first_match(input_str, criteria):
			for c in criteria:
				if c in input_str:
					return c
			return None
		op_family = find_first_match(_op.name, self.op_families)
		if op_family:
			_op.color = ui.colors[op_family]
		

	def updateTitleColor(self, op_family):
		self.ownerComp.op('popMenuConfig').parGroup.Titlecolor = ui.colors[op_family]


	def primeNewCOMPTemplate(self, comp):
		comp.allowCooking = False
		pass


	def OpenTemplatesFloating(self):
		p = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name="Templates")
		p.owner = self.ownerComp.par.Templates.eval()
	
	

	
#### EXTERNAL STUFF #####	

	def CreateTemplateContainer(self):
		newOP = self.ownerComp.parent(2).copy(op('OPTemplates1'))
		newOP.nodeX = self.ownerComp.nodeX
		newOP.nodeY = self.ownerComp.nodeY - 200
		newOP.dock = self.ownerComp
		self.ownerComp.par.Templates = newOP
		self.ExternalChange()
	def ExternalPathExpr(self, name=None):
		if name == None:
			name = self.templatesCOMP.name + ('_2023' if app.build.startswith('2023') else '')
		return f"app.userPaletteFolder + '/FNStools_ext/OpTemplates/{name}.tox'"
	
	@property
	def ExternalPath(self):
		return eval(self.ExternalPathExpr())

	
	def get_new_name(self, directory, filename):
		# Extract name and extension
		name, ext = os.path.splitext(filename)
		
		# Extract the base name (without trailing digits)
		match = re.search(r'(\d+)$', name)
		if match:
			base_name = name[:match.start()]
			current_num = int(match.group())
		else:
			base_name = name
			current_num = 0
		
		# Find the highest digit of matching filenames in the directory
		max_num = current_num
		for f in os.listdir(directory):
			if f.startswith(base_name) and f.endswith(ext):
				f_name, _ = os.path.splitext(f)
				f_match = re.search(r'(\d+)$', f_name)
				if f_match:
					max_num = max(max_num, int(f_match.group()))
		
		# If the filename exists or the current number is already the highest, increment the number
		num = max_num + 1
		while os.path.exists(os.path.join(directory, f"{base_name}{num}{ext}")):
			num += 1
			
		return f"{base_name}{num}{ext}"

	def externalExprUpdate(self, extpar, enable, path_expr = None):
			extpar.expr = path_expr if enable else ''
			extpar.mode = ParMode.EXPRESSION if enable else ParMode.CONSTANT


	def TemplateSave(self):
		confirm = not ui.messageBox("Confirm","You are about to overwrite your templates.", buttons=['OK','Cancel'])
		if confirm:
			if self.ownerComp.par.External:
				self.ExternalChange(onSave=True)
			else:
				project.save()

	def ExternalChange(self, onSave=False, startup=False, enable=None):
		if enable is None:
			enable = self.ownerComp.par.External.eval()

		ext_tox_par = self.templatesCOMP.par.externaltox
		if enable:
			if not ext_tox_par.eval():
				# give a default expression for external tox if it was empty
				self.externalExprUpdate(ext_tox_par, True, self.ExternalPathExpr())
			if os.path.exists(ext_tox_par.eval()):
				if startup:
					# ignore most of below, could probably a separate method even
					load = 2
				else:
					# if external tox already exists we need to make a choice:
					choices = ['Overwrite','Create New', 
								'Load Existing' if not onSave else 'Cancel']
					load = ui.messageBox("WARNING",
						f"External Template '{os.path.basename(ext_tox_par.eval())}' already exists. What would you like to do?", 
						buttons=choices)
				
				if load == 0: # overwrite
					self.templatesCOMP.save(ext_tox_par.eval(), createFolders=True)
				elif load == 1: # new
					new_name = self.get_new_name(self.extFolder, self.templatesCOMP.name)
					orig_op = self.templatesCOMP
					orig_op.name = new_name

					self.ownerComp.par.Templates = orig_op # update reference
					self.externalExprUpdate(ext_tox_par, True, self.ExternalPathExpr(new_name))
					self.templatesCOMP.save(ext_tox_par.eval(), createFolders=True)
				elif load == 2 and not onSave: # load, if onSave -> return instead
					self.templatesCOMP.par.reinitnet.pulse()
				else:
					return
			else:
				# there was no external tox already with this name, we're happy
				self.templatesCOMP.save(self.ExternalPath, createFolders=True)
		else:
			# clear reference to external tox
			self.externalExprUpdate(ext_tox_par, False)

		run("parent.OpTemplate.RefreshCachedTemplates()", fromOP=me, endFrame=True)

	
	def RefreshTemplates(self):
		self.templatesCOMP.par.reinitnet.pulse()
