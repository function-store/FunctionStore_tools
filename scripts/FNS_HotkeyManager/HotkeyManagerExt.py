import re
from dataclasses import dataclass, field
from typing import Optional, Union, List
import TDFunctions as TDF

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
############

KILL = False

@dataclass
class HotkeyParData:
	path: str
	par: str
	type: str = ""
	custom_val: str = ""
	custom_bindExpr: str = ""
	custom_expr: str = ""
	# CHOP specific
	keys_val: str = ""
	keys_bindExpr: str = ""
	keys_expr: str = ""
	modifiers_val: str = ""
	modifiers_bindExpr: str = ""
	modifiers_expr: str = ""
	# DAT specific
	dat_keys_val: str = ""
	dat_keys_bindExpr: str = ""
	dat_keys_expr: str = ""
	dat_shortcuts_val: str = ""
	dat_shortcuts_bindExpr: str = ""
	dat_shortcuts_expr: str = ""
	
	def to_row(self) -> List[str]:
		"""Convert the dataclass to a table row"""
		return [
			self.path,
			self.par,
			self.type,
			"",
			self.custom_val,
			self.custom_expr,
			"",
			self.keys_val,
			self.keys_expr,
			self.modifiers_val,
			self.modifiers_expr,
			"",
			self.dat_keys_val,
			self.dat_keys_expr,
			self.dat_shortcuts_val,
			self.dat_shortcuts_expr
		]

class HotkeyManagerExt:##
	'''#TODO: REFACTOR THIS!!! THERE IS A LOT OF DUPLICATED CODE!!!'''
	def __init__(self, ownerComp):
		if KILL:
			return
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		
		self.ownerComp = ownerComp

		
		self.keyboardin_chop_pars = ['keys', 'modifiers']
		self.keyboardin_dat_pars = ['keys', 'shortcuts']
		self.comp_pars_substrings = ['key', 'shortcut', 'hotkey']
		self.comp_pars_exceptions = ['opshortcut','parentshortcut','arrowkeys','savehotkeys','loadhotkeys','shortcutactive']
		self.comp_except = ['popMenu']
		
		self.searchRoot = parent.FNS
		self.hotkeyTable : tableDAT = self.ownerComp.op('table_gathered_hotkeys')
		self.defaultTable : tableDAT = self.ownerComp.op('table_default_hotkeys')
		self.supressWatch = False
		self.logger = self.ownerComp.op('Logger').ext.Logger
		self.logger.SetTextPort(False)
		self.logger.log("HotkeysExt initialized")


		self.AllHotkeys = self.AllHotkeyPars()
		self.onStart()####
		return

	
	def AllHotkeyPars(self) -> List[tuple]:
		"""Return a list of tuples containing (operator, parameter_name) for all hotkey parameters"""
		self.logger.log("Starting AllHotkeyPars collection...", textport=True)
		result = []
		pars_found_debug = []  # Store parameter details for debugging comparison
		
		root: COMP = self.searchRoot
		
		# Find all keyboardinCHOP operators
		chop_pars_found = 0
		for op in root.findChildren(type=keyboardinCHOP):	
			if 'KeyModifiers' in op.path:
				continue
				
			for par_name in self.keyboardin_chop_pars:
				_par = getattr(op.par, par_name, None)
				if _par is not None:
					# Set the appropriate fields based on parameter
					if par_name == "keys":
						keys_val = _par.eval() if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND else ""
						keys_expr = _par.expr if _par.mode == ParMode.EXPRESSION and 'app.osName' in _par.expr else ""
						if keys_val or keys_expr:
							result.append((op, par_name))
							debug_info = f"CHOP: {op.path}.{par_name} - val: '{keys_val}', expr: '{keys_expr}'"
							pars_found_debug.append(debug_info)
							chop_pars_found += 1
							self.logger.log(f"AllHotkeyPars: CHOP {op.path} has {par_name} data", textport=False)
					elif par_name == "modifiers":
						mod_val = _par.eval() if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND else ""
						mod_expr = _par.expr if _par.mode == ParMode.EXPRESSION and 'app.osName' in _par.expr else ""
						if mod_val or mod_expr:
							result.append((op, par_name))
							debug_info = f"CHOP: {op.path}.{par_name} - val: '{mod_val}', expr: '{mod_expr}'"
							pars_found_debug.append(debug_info)
							chop_pars_found += 1
							self.logger.log(f"AllHotkeyPars: CHOP {op.path} has {par_name} data", textport=False)
				
		self.logger.log(f"AllHotkeyPars: Found {chop_pars_found} CHOP parameters", textport=True)
		
		# Find all keyboardinDAT operators with keys or shortcuts parameters
		dat_pars_found = 0
		for op in root.findChildren(type=keyboardinDAT):
			if 'KeyModifiers' in op.path:
				continue
				
			# Check if the DAT has any of the relevant parameters
			has_hotkey_pars = any(hasattr(op.par, par_name) for par_name in self.keyboardin_dat_pars)
			
			if has_hotkey_pars:
				for par_name in self.keyboardin_dat_pars:
					_par = getattr(op.par, par_name, None)
					if _par is not None:
						# Set the appropriate fields based on parameter
						if par_name == "keys":
							if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND:
								_keys_val = _par.eval()
								if _keys_val:
									# Define ignored keys pattern
									ignored_keys = ['ctrl', 'alt', 'shift', 'cmd', 'esc', 'enter', 'tab']
									# Dynamically create regex pattern from the ignored_keys list
									# Remove space from the list for the pattern (handled separately)
									keys_for_pattern = [k for k in ignored_keys if k != ' ']
									# Join keys with | for alternation in regex
									keys_pattern = '|'.join(keys_for_pattern)
									# Create the full pattern - match whole string with only ignored keys separated by whitespace
									pattern = r'^(?:\s*(?:' + keys_pattern + r')(?:\s+|$))*$'
									
									# If it matches the pattern (contains only ignored keys), skip this parameter
									if re.match(pattern, _keys_val.lower()):
										continue
									
									result.append((op, par_name))
									debug_info = f"DAT: {op.path}.{par_name} - val: '{_keys_val}'"
									pars_found_debug.append(debug_info)
									dat_pars_found += 1
									self.logger.log(f"AllHotkeyPars: DAT {op.path} has {par_name} value", textport=False)
							elif _par.mode == ParMode.EXPRESSION:
								if _par.expr and 'app.osName' in _par.expr:
									result.append((op, par_name))
									debug_info = f"DAT: {op.path}.{par_name} - expr: '{_par.expr}'"
									pars_found_debug.append(debug_info)
									dat_pars_found += 1
									self.logger.log(f"AllHotkeyPars: DAT {op.path} has {par_name} expr", textport=False)

						elif par_name == "shortcuts":
							if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND:
								_shortcuts_val = _par.eval()
								if _shortcuts_val:
									result.append((op, par_name))
									debug_info = f"DAT: {op.path}.{par_name} - val: '{_shortcuts_val}'"
									pars_found_debug.append(debug_info)
									dat_pars_found += 1
									self.logger.log(f"AllHotkeyPars: DAT {op.path} has {par_name} value", textport=False)
							elif _par.mode == ParMode.EXPRESSION:
								if _par.expr and 'app.osName' in _par.expr:
									result.append((op, par_name))
									debug_info = f"DAT: {op.path}.{par_name} - expr: '{_par.expr}'"
									pars_found_debug.append(debug_info)
									dat_pars_found += 1
									self.logger.log(f"AllHotkeyPars: DAT {op.path} has {par_name} expr", textport=False)
		
		self.logger.log(f"AllHotkeyPars: Found {dat_pars_found} DAT parameters", textport=True)
		
		# Find components with custom parameters related to hotkeys
		comp_pars_found = 0
		all_comps = root.findChildren(type=COMP)
		self.logger.log(f"AllHotkeyPars: Searching through {len(all_comps)} COMPs", textport=True)
		
		for op in all_comps:
			if any(_sub in op.path for _sub in self.comp_except):
				continue
				
			custompar_names = [par.name for par in op.customPars]
			
			for _par_name in custompar_names:
				# Skip parameters that match any of our exception patterns
				if any(_sub in _par_name.lower() for _sub in self.comp_pars_exceptions):
					continue
					
				# Check if this parameter name contains any of our hotkey substrings
				if any(_sub in _par_name.lower() for _sub in self.comp_pars_substrings):
					_par = getattr(op.par, _par_name, None)
					if _par is not None:
						custom_val = _par.eval() if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND else ""
						custom_expr = _par.expr if _par.mode == ParMode.EXPRESSION and 'app.osName' in _par.expr else ""
						
						# Only count if we have a value or expression
						if custom_val or custom_expr:
							result.append((op, _par_name))
							debug_info = f"COMP: {op.path}.{_par_name} - val: '{custom_val}', expr: '{custom_expr}'"
							pars_found_debug.append(debug_info)
							comp_pars_found += 1
							self.logger.log(f"AllHotkeyPars: COMP {op.path} has hotkey param {_par_name}", textport=False)
		
		self.logger.log(f"AllHotkeyPars: Found {comp_pars_found} COMP parameters", textport=True)
		self.logger.log(f"AllHotkeyPars: Total parameters found: {len(result)}", textport=True)
		return result

	def onStart(self):
		self.logger.log("Starting hotkeys initialization...")
		self.setAllHotkeys()
		self.logger.log("Hotkey initialization complete")

	def onParSavehotkeys(self):
		self.logger.log("Saving hotkeys...")
		self.gatherAllHotkeys()
		pass

	def onParLoadhotkeys(self):
		self.logger.log("Loading hotkeys...")
		self.supressWatch = True
		self.setAllHotkeys()
		run(
			"args[0].supressWatch = False",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)
		pass

	def onParLoaddefault(self):
		self.logger.log("Loading default hotkeys...", textport=True)
		self.supressWatch = True
		self.setAllHotkeys(default=True)
		run(
			"args[0].supressWatch = False",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)
		self.hotkeyTable.clear()
		# copy over
		self.hotkeyTable.copy(self.defaultTable)
		self.logger.log("Default hotkeys loaded", textport=False)
		pass

	def onParForcedefault(self, val):
		if val:
			self.onParLoaddefault()

	def onShortcutChanged(self, _par: Par):
		if self.supressWatch:
			return
		choice = ui.messageBox('Shortcut Changed', f'Shortcut "{_par.owner.name}:{_par.name}" changed to "{_par.eval()}". Do you want to externalize this?', buttons=['No','Yes'])
		if choice:
			self.logger.log(f"Shortcut '{_par.owner.name}:{_par.name}' changed to '{_par.eval()}'")
			self.gatherAllHotkeys()
	
	def getOPFromPath(self, _path: str) -> OP:
		try:
			return eval(f'parent.FNS.{_path}')
		except Exception as e:
			self.logger.log(f"Error evaluating path {_path}: {e}", textport=False)
			return None

	def setAllHotkeys(self, default=False):
		self.logger.log("Setting all hotkeys...")
		hotkeyTable = self.hotkeyTable if not (self.evalForcedefault or default) else self.defaultTable
		headers_row = hotkeyTable.row(0)
		headers = [h.val for h in headers_row]
		self.logger.log(f"Processing {hotkeyTable.numRows-1} hotkeys")
		
		success = 0

		for row_idx in range(1, hotkeyTable.numRows):
			row = hotkeyTable.row(row_idx)
			_values = [cell.val for cell in row]
			_data = dict(zip(headers, _values))
			
			_path = _data.get('path', '')

			_op = self.getOPFromPath(_path)
			
			if _op is None:
				self.logger.log(f"No operator found for path {_path}")
				continue
				
			_par_names = _data.get('par', '').split(', ')
			_type = _data.get('type', '')
			
			self.logger.log(f"Setting {_type} hotkey for {_op.name}: {_par_names}", textport=False)
			
			if _type == "COMP":
				# Handle custom parameter hotkeys
				for _par_name in _par_names:
					_par = getattr(_op.par, _par_name, None)
					if _par is None:
						self.logger.log(f"No parameter '{_par_name}' found on operator {_op}")
						continue
						
					_val = _data.get('custom_val', '')
					_expr = _data.get('custom_expr', '')
					
					if _expr:
						self.logger.log(f"Setting expression for {_op}.par.{_par_name}: {_expr}", textport=False)
						_par.expr = _expr
						success += 1
					else:
						self.logger.log(f"Setting value for {_op}.par.{_par_name}: {_val}", textport=False)
						_par.val = _val
						success += 1

			elif _type == "CHOP":
				# Handle CHOP-specific parameters
				chop_success = 0
				for _par_name in _par_names:
					if _par_name == "keys":
						_keys_par = _op.par.keys
						if _keys_par is not None:
							_val = _data.get('chop_keys_val', '')
							_expr = _data.get('chop_keys_expr', '')
							if _expr:
								self.logger.log(f"Setting CHOP keys expression for {_op}: {_expr}", textport=False)
								_keys_par.expr = _expr
								chop_success += 1
							else:
								self.logger.log(f"Setting CHOP keys value for {_op}: {_val}", textport=False)
								_keys_par.val = _val
								chop_success += 1

					if _par_name == "modifiers":
						_mod_par = _op.par.modifiers
						if _mod_par is not None:
							_val = _data.get('chop_modifiers_val', '')
							_expr = _data.get('chop_modifiers_expr', '')
							if _expr:
								self.logger.log(f"Setting CHOP modifiers expression for {_op}: {_expr}", textport=False)
								_mod_par.expr = _expr
								chop_success += 1
							else:
								self.logger.log(f"Setting CHOP modifiers value for {_op}: {_val}", textport=False)
								_mod_par.val = _val
								chop_success += 1
				if chop_success:
					success += 1

			elif _type == "DAT":
				# Handle DAT-specific parameters
				dat_success = 0
				for _par_name in _par_names:
					if _par_name == "keys":
						_keys_par = _op.par.keys
						if _keys_par is not None:
							_val = _data.get('dat_keys_val', '')
							_expr = _data.get('dat_keys_expr', '')
							if _expr:
								self.logger.log(f"Setting DAT keys expression for {_op}: {_expr}", textport=False)
								_keys_par.expr = _expr
								dat_success += 1
							else:
								self.logger.log(f"Setting DAT keys value for {_op}: {_val}", textport=False)
								_keys_par.val = _val
								dat_success += 1

					if _par_name == "shortcuts":
						_shortcuts_par = _op.par.shortcuts
						if _shortcuts_par is not None:
							_val = _data.get('dat_shortcuts_val', '')
							_expr = _data.get('dat_shortcuts_expr', '')
							if _expr:
								self.logger.log(f"Setting DAT shortcuts expression for {_op}: {_expr}", textport=False)
								_shortcuts_par.expr = _expr
								dat_success += 1
							else:
								self.logger.log(f"Setting DAT shortcuts value for {_op}: {_val}", textport=False)
								_shortcuts_par.val = _val
								dat_success += 1
				if dat_success:
					success += 1

		self.logger.log(f"Successfully loaded {success} hotkeys", textport=True)

	def gatherAllHotkeys(self):
		self.logger.log("Starting gatherAllHotkeys collection...", textport=True)
		gather_pars_debug = []  # Store parameter details for debugging comparison
		
		root: COMP = self.searchRoot
		gathered_hotkeys_table: tableDAT = self.ownerComp.op('table_gathered_hotkeys')
		
		# Clear the table and set headers
		gathered_hotkeys_table.clear()
		headers = [
			"path", "par", "type", "_COMP_", 
			"custom_val", "custom_expr", 
			"_CHOP_", 
			"chop_keys_val", "chop_keys_expr", 
			"chop_modifiers_val", "chop_modifiers_expr", 
			"_DAT_", 
			"dat_keys_val", "dat_keys_expr", 
			"dat_shortcuts_val", "dat_shortcuts_expr"
		]
		gathered_hotkeys_table.appendRow(headers)
		
		hotkeys_data = []
		ops_found = []  # Track found operators for comparison
		ops_paths = []  # Track paths for easier comparison
		
		self.logger.log("Searching for CHOP keyboard operators...")
		
		# Find all keyboardinCHOP operators#
		chops_found = 0
		chop_pars_found = 0
		for _keyboardinCHOP in root.findChildren(type=keyboardinCHOP):	
			if 'KeyModifiers' in _keyboardinCHOP.path:
				continue
				
			data = HotkeyParData(
				path=self._getPathFromOP(_keyboardinCHOP),
				par=', '.join(self.keyboardin_chop_pars),
				type="CHOP"
			)
			has_data = False
			chop_pars_in_op = 0
			
			for par_name in self.keyboardin_chop_pars:
				_par = getattr(_keyboardinCHOP.par, par_name, None)
				if _par is not None:
					# Set the appropriate fields based on parameter
					if par_name == "keys":
						data.keys_val = _par.eval() if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND else ""
						data.keys_expr = _par.expr if _par.mode == ParMode.EXPRESSION and 'app.osName' in _par.expr else ""
						if data.keys_val or data.keys_expr:
							has_data = True
							chop_pars_in_op += 1
							chop_pars_found += 1
							debug_info = f"CHOP: {_keyboardinCHOP.path}.{par_name} - val: '{data.keys_val}', expr: '{data.keys_expr}'"
							gather_pars_debug.append(debug_info)
							self.logger.log(f"gatherAllHotkeys: CHOP {_keyboardinCHOP.path} has keys data", textport=False)
					elif par_name == "modifiers":
						data.modifiers_val = _par.eval() if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND else ""
						data.modifiers_expr = _par.expr if _par.mode == ParMode.EXPRESSION and 'app.osName' in _par.expr else ""
						if data.modifiers_val or data.modifiers_expr:
							has_data = True
							chop_pars_in_op += 1
							chop_pars_found += 1
							debug_info = f"CHOP: {_keyboardinCHOP.path}.{par_name} - val: '{data.modifiers_val}', expr: '{data.modifiers_expr}'"
							gather_pars_debug.append(debug_info)
							self.logger.log(f"gatherAllHotkeys: CHOP {_keyboardinCHOP.path} has modifiers data", textport=False)
			if has_data:
				hotkeys_data.append(data)
				ops_found.append(_keyboardinCHOP)
				ops_paths.append(_keyboardinCHOP.path)
				chops_found += 1
		
		self.logger.log(f"gatherAllHotkeys: Found {chops_found} CHOP keyboard operators with {chop_pars_found} parameters")
		self.logger.log("Searching for DAT keyboard operators...")
		
		# Find all keyboardinDAT operators with keys or shortcuts parameters
		dats_found = 0
		dat_pars_found = 0
		for _keyboardinDAT in root.findChildren(type=keyboardinDAT):
			if 'KeyModifiers' in _keyboardinDAT.path:
				continue
				
			# Check if the DAT has any of the relevant parameters
			has_hotkey_pars = any(hasattr(_keyboardinDAT.par, par_name) for par_name in self.keyboardin_dat_pars)
			
			if has_hotkey_pars:
				data = HotkeyParData(
					path=self._getPathFromOP(_keyboardinDAT),
					par=', '.join(self.keyboardin_dat_pars),
					type="DAT"
				)
				
				has_data = False
				dat_pars_in_op = 0
				
				for par_name in self.keyboardin_dat_pars:
					_par = getattr(_keyboardinDAT.par, par_name, None)
					if _par is not None:
						# Set the appropriate fields based on parameter
						if par_name == "keys":
							if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND:
								_keys_val = _par.eval()
								if _keys_val:
									# Define ignored keys pattern
									ignored_keys = ['ctrl', 'alt', 'shift', 'cmd', 'esc', 'enter', 'tab']
									# Dynamically create regex pattern from the ignored_keys list
									# Remove space from the list for the pattern (handled separately)
									keys_for_pattern = [k for k in ignored_keys if k != ' ']
									# Join keys with | for alternation in regex
									keys_pattern = '|'.join(keys_for_pattern)
									# Create the full pattern - match whole string with only ignored keys separated by whitespace
									pattern = r'^(?:\s*(?:' + keys_pattern + r')(?:\s+|$))*$'
									
									# If it matches the pattern (contains only ignored keys), skip this parameter
									if re.match(pattern, _keys_val.lower()):
										continue
									
									data.dat_keys_val = _keys_val
									has_data = True
									dat_pars_in_op += 1
									dat_pars_found += 1
									debug_info = f"DAT: {_keyboardinDAT.path}.{par_name} - val: '{_keys_val}'"
									gather_pars_debug.append(debug_info)
									self.logger.log(f"gatherAllHotkeys: DAT {_keyboardinDAT.path} has keys value", textport=False)
							elif _par.mode == ParMode.EXPRESSION:
								data.dat_keys_expr = _par.expr if 'app.osName' in _par.expr else ""
								if data.dat_keys_expr:
									has_data = True
									dat_pars_in_op += 1
									dat_pars_found += 1
									debug_info = f"DAT: {_keyboardinDAT.path}.{par_name} - expr: '{data.dat_keys_expr}'"
									gather_pars_debug.append(debug_info)
									self.logger.log(f"gatherAllHotkeys: DAT {_keyboardinDAT.path} has keys expr", textport=False)

						elif par_name == "shortcuts":
							if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND:
								data.dat_shortcuts_val = _par.eval()
								if data.dat_shortcuts_val:
									has_data = True
									dat_pars_in_op += 1
									dat_pars_found += 1
									debug_info = f"DAT: {_keyboardinDAT.path}.{par_name} - val: '{data.dat_shortcuts_val}'"
									gather_pars_debug.append(debug_info)
									self.logger.log(f"gatherAllHotkeys: DAT {_keyboardinDAT.path} has shortcuts value", textport=False)
							elif _par.mode == ParMode.EXPRESSION:
								data.dat_shortcuts_expr = _par.expr if 'app.osName' in _par.expr else ""
								if data.dat_shortcuts_expr:
									has_data = True
									dat_pars_in_op += 1
									dat_pars_found += 1
									debug_info = f"DAT: {_keyboardinDAT.path}.{par_name} - expr: '{data.dat_shortcuts_expr}'"
									gather_pars_debug.append(debug_info)
									self.logger.log(f"gatherAllHotkeys: DAT {_keyboardinDAT.path} has shortcuts expr", textport=False)
				
				if has_data:
					hotkeys_data.append(data)
					ops_found.append(_keyboardinDAT)
					ops_paths.append(_keyboardinDAT.path)
					dats_found += 1

		self.logger.log(f"gatherAllHotkeys: Found {dats_found} DAT keyboard operators with {dat_pars_found} parameters")
		self.logger.log("Searching for component custom parameters...")

		all_comps = root.findChildren(type=COMP)
		self.logger.log(f"gatherAllHotkeys: Searching through {len(all_comps)} COMPs", textport=True)
		
		comps_found = 0
		comp_pars_found = 0
		for _comp in all_comps:
			if any(_sub in _comp.path for _sub in self.comp_except):
				continue
				
			# list all custompar names of the comp
			custompar_names = [par.name for par in _comp.customPars]
			found_hotkey = False
			comp_pars_in_op = 0
			
			# check if any of the custompar names contain any of the comp_pars_substrings
			for _par_name in custompar_names:
				# Skip parameters that match any of our exception patterns
				if any(_sub in _par_name.lower() for _sub in self.comp_pars_exceptions):
					continue
					
				# Check if this parameter name contains any of our hotkey substrings  
				if any(_sub in _par_name.lower() for _sub in self.comp_pars_substrings):
					_par = getattr(_comp.par, _par_name, None)
					if _par is not None:
						data = HotkeyParData(
							path=self._getPathFromOP(_comp),
							par=_par_name,
							type="COMP"
						)
						
						data.custom_val = _par.eval() if _par.mode == ParMode.CONSTANT or _par.mode == ParMode.BIND else ""
						data.custom_expr = _par.expr if _par.mode == ParMode.EXPRESSION and 'app.osName' in _par.expr else ""
						
						# Only count if we have a value or expression
						if data.custom_val or data.custom_expr:
							debug_info = f"COMP: {_comp.path}.{_par_name} - val: '{data.custom_val}', expr: '{data.custom_expr}'"
							gather_pars_debug.append(debug_info)
							self.logger.log(f"gatherAllHotkeys: COMP {_comp.path} has param {_par_name}", textport=False)
							hotkeys_data.append(data)
							found_hotkey = True
							comp_pars_in_op += 1
							comp_pars_found += 1
			
			# If this component has at least one valid hotkey parameter, add it to our results
			if found_hotkey and _comp not in ops_found:
				ops_found.append(_comp)
				ops_paths.append(_comp.path)
				comps_found += 1

		self.logger.log(f"gatherAllHotkeys: Found {comps_found} COMP operators with {comp_pars_found} parameters")
		self.logger.log(f"gatherAllHotkeys: Total ops found: {len(ops_found)} with {len(gather_pars_debug)} total parameters")
		
		
		# Compare with property parameter list if it exists
		if hasattr(self.ownerComp.storage, 'allHotkeyParsDebug'):
			property_pars = self.ownerComp.storage.allHotkeyParsDebug
			
			# Find differences
			in_property_not_gathered = [p for p in property_pars if p not in gather_pars_debug]
			in_gathered_not_property = [p for p in gather_pars_debug if p not in property_pars]
			
			if in_property_not_gathered:
				self.logger.log(f"DISCREPANCY: Parameters in AllHotkeyPars but not in gather ({len(in_property_not_gathered)}):", textport=True)
				for i, item in enumerate(in_property_not_gathered):
					self.logger.log(f"  {i+1}. {item}", textport=True)
			
			if in_gathered_not_property:
				self.logger.log(f"DISCREPANCY: Parameters in gather but not in AllHotkeyPars ({len(in_gathered_not_property)}):", textport=True)
				for i, item in enumerate(in_gathered_not_property):
					self.logger.log(f"  {i+1}. {item}", textport=True)
				
			if not in_property_not_gathered and not in_gathered_not_property:
				self.logger.log("MATCH: Both methods found exactly the same parameters!", textport=True)
		
		# Add rows to the table
		for data in hotkeys_data:
			gathered_hotkeys_table.appendRow(data.to_row())
		
		return gathered_hotkeys_table


	def _getPathFromOP(self, _op: OP) -> str:
		path = TDF.getShortcutPath(self.searchRoot, _op)
		return path


