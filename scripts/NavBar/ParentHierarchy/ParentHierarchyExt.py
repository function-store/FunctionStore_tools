
'''Info Header Start
Name : ParentHierarchyExt
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.519.toe
Saveversion : 2023.11880
Info Header End'''

import TDFunctions as TDF
import TDStoreTools as TDS
import re
from copy import copy

class ParentHierarchyExt:
	"""
	ParentHierarchyExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached#
		self.ownerComp = ownerComp
				# properties
		self.ParentShortcutList = []
		self.ParentCompList = []
		self.SelectedParentStr = ''
		self.ParentNuggetContainer = self.ownerComp.op('popMenu_nugget')
		self.ParentBarcontainer = self.ownerComp.op('popMenu_bar')
		self.current_comp_save = None
		self.NuggetList = TDS.DependList([''])
		self.divider = ['(hold ctrl for pars)', '(hit ctrl to poll pars, click to copy ref)']
		self.hasPars = False
		self.keepOpen = tdu.Dependency(False)
		self.showPars = False
		self.showVals = False
		self.idx = None
		self.compEditor = op('/sys/TDDialogs/CompEditor')
		run(
			"args[0].postInit() if args[0] "
					"and hasattr(args[0], 'postInit') else None",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)

	def postInit(self):
		TDF.createProperty(self, 'ParentShortcuts', value=self.ParentHierarchyContent(), dependable=True,
						   readOnly=False)

	@property
	def NavbarContent(self):
		if self.ownerComp.op('../panenav/out1'):
			return self.ownerComp.op('../panenav/out1').text.strip()
		return None
		
	# def updateNuggetList(self, state):
	# 	# check if we have parameters in the nugget list by checking if there is an item after (!!!) the divider
	# 	if self.parsFromIndex == -1 and self.showVals:
	# 		return
	# 	nugget_list = self.NuggetList.getRaw()
	# 	pars_list = nugget_list[self.parsFromIndex:]
	# 	curr_comp = self.curr_comp_save
	# 	# evaluate the parameters and append to the element
	# 	for idx, _par in enumerate(pars_list):
	# 		par_name = _par.split(':')[0].strip()
	# 		# check if item already has a value, but keep in mind label can have = sign in it, so not a good check
	# 		if '=' in _par:
	# 			# update the value
	# 			# parse the value from the string
	# 			par_vals = _par.split('=')
	# 			if len(par_vals) == 2:
	# 				par_label = par_vals[0].strip()
	# 				if state:
	# 					eval_val = curr_comp.par[par_name].eval()
	# 					# truncate length to 75 characters if it's a string and add dots if it's longer
	# 					if isinstance(eval_val, str):
	# 						if len(eval_val) > 75:
	# 							eval_val = eval_val[:75] + '...'
	# 					self.NuggetList[self.parsFromIndex + idx] = f'{par_label} = {eval_val}'
	# 				else:
	# 					self.NuggetList[self.parsFromIndex + idx] = f'{par_label}'
	# 		else:
	# 			if state:
	# 				eval_val = curr_comp.par[par_name].eval()
	# 				# truncate length to 75 characters if it's a string and add dots if it's longer
	# 				if isinstance(eval_val, str):
	# 					if len(eval_val) > 75:
	# 						eval_val = eval_val[:75] + '...'
	# 				self.NuggetList[self.parsFromIndex + idx] = f'{_par} = {eval_val}'
	# 			else:
	# 				self.NuggetList[self.parsFromIndex + idx] = f'{_par}'



	def SelectParentContent(self, idx = None, extraInfo = False, extraTrigger = False, showPars = False, showVals = False):
		def get_replaced_list(input_string, index):
			pattern = r'(\/|[^/]+)'
			elements = re.findall(pattern, input_string)
			replaced_list = []
			for i, element in enumerate(elements):
				if i == index:
					replaced_list.append(element)
				else:
					replaced_list.append(' ' * len(element))
			
			return replaced_list
		if idx is not None:
			self.idx = idx
		else:
			idx = self.idx
		if idx is None:
			return

		if self.ownerComp.op('null_hk1')[0][0]:
			showVals = True
			showPars = True
			extraInfo = True
		
		self.showPars = showPars
		self.showVals = showVals
		# if self.ownerComp.op('null_hk2')[0][0]:
		# 	showPars = True

		parent_shortcut = get_replaced_list(self.ParentHierarchyContent(), idx)
		parent_shortcut = ''.join(parent_shortcut).strip()
		#self.NuggetList = self.NuggetList.strip()
		### Initially I wanted this to overlay the other window, but positioning is messed up, so let's strip the whitespaces and make just a nugget
		self.NuggetList = TDS.DependList([])

		comp_list = copy(self.ParentCompList)
		comp_list.reverse()
		if len(comp_list) <= int(idx/2):
			return
		
		curr_comp = comp_list[int(idx/2)]
		self.curr_comp_save = curr_comp
		
		globalshort = tdu.tryExcept(lambda: curr_comp.par.opshortcut.eval(), None)
		ting = globalshort or '___'
		if ting and ting != '___':
			self.NuggetList += [f"G: {ting}"]

		if parent_shortcut and parent_shortcut != '___':
			self.NuggetList += [f'P: {parent_shortcut}']

		for idx, (intopname, intop) in enumerate(list(curr_comp.internalOPs.items())):
			self.NuggetList += [f"iop{idx+1}: {intopname or '___'}"]
			if extraInfo:
				self.NuggetList[-1] += f" = {curr_comp.relativePath(intop)}"
		
		self.NuggetList += [self.divider[0]]
		if showPars:
			self.NuggetList[-1] = self.divider[1]
			self.parsFromIndex = -1
			for par in self.curr_comp_save.customPars:
				if self.parsFromIndex == -1:
					self.parsFromIndex = len(self.NuggetList)
				par_label= f"{par.name}:{par.label}"
				
				if showVals:
					_par = self.curr_comp_save.par[par.name]
					if _par.isPulse:
						eval_val = "{pulse}"
					elif _par.isSequence and not _par.sequenceBlock:
						eval_val = "{seq}"
					else:
						eval_val = _par.eval()
					par_label += f' = {eval_val}'
					
					if len(par_label) > 75:
						par_label = par_label[:75] + '...'
				
				self.NuggetList += [par_label]

		if self.NuggetList:
			#self.ParentNuggetContainer.par.Items.val = self.NuggetList
			if not self.ownerComp.op('popMenu_bar/window').isOpen and not extraTrigger:
				self.ShowHideNugget(True)
		if (showPars or showVals) and extraTrigger:
			self.ParentNuggetContainer.ext.PopMenuExt.refresh()
			self.ParentNuggetContainer.ext.PopMenuExt.CalculateOptimalDimensions()
			self.ParentNuggetContainer.ext.PopMenuExt.RecalculateOffsets()
			self.keepOpen.val = True
		else:
			self.keepOpen.val = False
		
		
	def onPopMenuSetLook(self, info):
		lister = info['ownerComp']
		row = info['row']
		col = 0
		# get element from nuggetlist based on row
		_element = info['cellText']
		# get lister reference
		if _element.startswith('P: '):
			lister.SetCellLook(row, col, 'buttonParent')
			pass
		if _element.startswith('G: '):
			lister.SetCellLook(row, col, 'buttonGlobal')
			pass
		if _element.startswith('iop'):
			lister.SetCellLook(row, col, 'buttonIop')
			pass
		pass
				
	def ParentHierarchyContent(self):
		self.ParentShortcutList = []
		self.ParentCompList = []
		self.GetInfo()
		
		# Define the list
		my_list = self.ParentShortcutList
		my_list.reverse()

		# Replace empty strings with '___'
		my_list = ['___' if i == '' else i for i in my_list if i != None]

		# Join the items in the list with '/' as the separator
		result = ''
		if my_list:
			result = " / ".join(my_list)
			result = "/ " + result + ' /'
			self.ParentBarcontainer.par.Items.val = [result]
		return result

	def GetInfo(self, comp = None):
		'''Get parent shortcuts recursively in a list'''
		if comp is None:
			comp = op(self.NavbarContent)
			self.ParentShortcutList = []
			self.ParentCompList = []
		if comp == op('/'):
			return
		if comp is None:
			return
		
		self.ParentShortcutList.append(tdu.tryExcept(lambda: comp.par.parentshortcut.eval(), None))
		self.ParentCompList.append(comp)
		if _parent := comp.parent():
			self.GetInfo(_parent)


####

	def ShowHideNugget(self, show):
		if show:
			self.ParentNuggetContainer.par.Open.pulse()
			self.ParentNuggetContainer.op('lister').scroll(0, 0)
		else:
			if not self.keepOpen:
				self.ParentNuggetContainer.par.Close.pulse()

	def ShowHideBar(self, show):
		if show:
			self.ParentBarcontainer.par.Open.pulse()
		else:
			self.ParentBarcontainer.par.Close.pulse()

	
	def onNuggetItemClicked(self, info, openEditor = False):
		nugget_comp = self.curr_comp_save
		target_comp = op(op('../panenav/out1').text.strip()).ops('*')
		if not target_comp:
			target_comp = op(op('../panenav/out1').text.strip())
		else:
			target_comp = target_comp[0]
			
		item = info['item']
		clipboard_text = None
		if item.startswith('P: '):
			# get parent shortcut
			parent_shortcut = item.split(':')[1].strip()
			clipboard_text = f'parent.{parent_shortcut}'
			
			if openEditor:
				nugget_comp.openParameters()
		elif item.startswith('G: '):
			# get global shortcut
			global_shortcut = item.split(':')[1].strip()
			clipboard_text = f'op.{global_shortcut}'
			if openEditor:
				nugget_comp.openParameters()
			pass
		elif re.match(r'iop\d+:\s', item):
			# get internal op shortcut
			internal_shortcut = item.split(' ')[1].strip()
			clipboard_text = f'iop.{internal_shortcut}'
			if openEditor:
				nugget_comp.internalOPs[internal_shortcut].openParameters()
			pass
		elif re.match(r'(\w+):(.+)', item):
				
			# get parameter shortcut
			par_name = item.split(':')[0].strip()
			clipboard_text = TDF.getShortcutPath(target_comp, nugget_comp)
			# get par
			_par = nugget_comp.par[par_name]
			if _seqBlock := _par.sequenceBlock:
				# TODO: get sequencepar name from parname which is {sequencename}{number}{sequenceparname}
				sequenceparname = par_name.split(f'{_seqBlock.sequence.name}{_seqBlock.index}')[1]
				clipboard_text += f'.seq.{_seqBlock.sequence.name}[{_seqBlock.index}].par.{sequenceparname.capitalize()}'
			elif _par.isSequence:
				clipboard_text += f'.seq.{par_name}'
			else:
				clipboard_text += f'.par.{par_name}'
			
			if openEditor:
				if not self.compEditor.op('window').isOpen:
					self.compEditor.Open(nugget_comp)
				else:
					self.compEditor.Connect(nugget_comp)
				self.compEditor.CurrentPage = _par.page.name
				self.compEditor.CurrentPar = _par
				self.compEditor.RefreshListers()
				_comp_editor_pages = self.compEditor.op('pagesAndParameters/listerPages')
				_comp_editor_pars = self.compEditor.op('pagesAndParameters/listerPars')
				_page = _par.page.name
				
				# get page index from comp editor pages
				_page_list = list(filter(lambda x: x['pageName'] == _page, _comp_editor_pages.Data))
				_page_idx = _page_list[0]['sourceIndex']
				if _page_idx != 'Auto-Header':
					_comp_editor_pages.SelectRow(_page_idx+1)
					_comp_editor_pages.scroll(_page_idx, 0)

				if len(_par.parGroup) > 1:
					par_name = _par.parGroup.name
				_par_list = list(filter(lambda x: x['ParName'] == par_name, _comp_editor_pars.Data))
				_par_idx = _par_list[0]['sourceIndex']
				if _par_idx != 'Auto-Header':
					_comp_editor_pars.SelectRow(_par_idx+1)
					_comp_editor_pars.scroll(_par_idx, 0)
			pass

		if clipboard_text:
			ui.clipboard = clipboard_text
			ui.status = f'Copied to clipboard: {clipboard_text}'
		self.ownerComp.op('../panenav/path').panel.celloverid = -1

