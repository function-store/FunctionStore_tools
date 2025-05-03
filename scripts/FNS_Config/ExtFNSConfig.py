import TDJSON
import json

class ExtFNSConfig:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.exceptions = ['Version Ctrl','About','Info','Callbacks']
		self.extraAttrs = ['val','eval','expr','bindExpr','mode']

	@property
	def file_path(self):
		return self.ownerComp.par.Path.eval()

	def filter_keys_from_second_level(self, nested_dict, keys_to_remove):
		# Create a new dictionary to hold the filtered result
		filtered_dict = {}

		# Iterate over the first-level keys and values
		for key, sub_dict in nested_dict.items():
			if isinstance(sub_dict, dict):
				# Create a new sub-dictionary excluding the specified keys
				filtered_sub_dict = {sub_key: sub_value for sub_key, sub_value in sub_dict.items() if sub_key not in keys_to_remove}
				filtered_dict[key] = filtered_sub_dict
			else:
				# If the value is not a dictionary, just copy it over
				filtered_dict[key] = sub_dict
		
		return filtered_dict

	def SaveAllToJSON(self):
		debug('Saving all configs to JSON')
		full_data = {}
		full_data['op.FNS'] = TDJSON.opToJSONOp(op.FNS, forceAttrLists=False, extraAttrs=self.extraAttrs)
		for _op in parent.FNS.findChildren(depth=1, key=lambda x: x.family == 'COMP' and not x.type in ['annotate','comment','network']):
			if _op is not None:
				full_data[f"op.FNS.op('{_op.name}')"] = TDJSON.opToJSONOp(_op, forceAttrLists=False, extraAttrs=self.extraAttrs)

		filtered_data = self.filter_keys_from_second_level(full_data, self.exceptions)
		self.toFile(filtered_data)

	def toFile(self, data):
		with open(self.file_path, 'w') as fp:
			json.dump(data, fp)

	def LoadAllFromJSON(self):
		debug('Loading all configs from JSON')
		with open(self.file_path) as json_file:
			full_data = json.load(json_file)
			for _comp_shortcut, _data in full_data.items():
				try:
					_op = eval(_comp_shortcut)
					TDJSON.addParametersFromJSONOp(_op, _data)
					self.dealWithExtraAttrs(_op, _data)
				except Exception as e:
					print(f"Error loading {_comp_shortcut}: {e}")
					#debug(_data)

	def dealWithExtraAttrs(self, _op, _pages_data):
		for _page_data in _pages_data.values():
			for _par_name, _par_data in _page_data.items():
				for _extra_attr in self.extraAttrs:
					_target_par = getattr(_op.parGroup, _par_data['name'])
					_extra_attr_val = _par_data[_extra_attr]
					if _extra_attr in ['eval']:
						continue
					if _extra_attr == 'mode':
						_mode = getattr(ParMode,_extra_attr_val)
						setattr(_target_par, _extra_attr, _mode)
						if _mode in [ParMode.BIND]:
							_target_par.val = _par_data['eval']
					else:
						setattr(_target_par, _extra_attr, _extra_attr_val)

	def Saveall(self, _):
		self.SaveAllToJSON()
	
	def Loadall(self, _):
		self.LoadAllFromJSON()

	def OnStart(self):
		post_update = parent.FNS.fetch('post_update', False)
		if post_update or self.ownerComp.par.Autoload.eval():
			self.LoadAllFromJSON()
			parent.FNS.unstore('post_update')
			# okay I really fucked this up, so mega-hack below
			op.FNS_RPLS.par.Limitdepth = False
			op.FNS_OUTPUT.par.Spoutactive = False
			op.FNS_OUTPUT.par.Ndiactive = False
			self.SaveAllToJSON()
		
		pass