'''Info Header Start
Name : default_callbacks
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
# OpFam Callbacks Template
#
# All callbacks receive an info dict. Pre-action callbacks can:
#   1. Return True/False/None to control flow
#   2. Modify info dict keys to change what gets acted on
#
# Modified info keys are passed through to the caller, so changing
# info['lookupName'] in onPlaceOp will place a different operator.

# FNS: the family's members are also toolkit packages, and their masters
# (plus any doorstep copy the installer placed) live in the toolkit
# container with a FamManifest of their own. TDFam finds placed operators by
# manifest tag across the whole project, so without this guard Create Stubs
# (All) would stub the masters and Update (All) would replace them from the
# family folder. Everything inside the toolkit container belongs to the FNS
# updater; the three pre-hooks below skip it (docs/OperatorFamilyFromStore.md).

def _inToolkit(comp):
	"""True for an operator inside the container that holds this family."""
	if comp is None:
		return False
	home = me.parent().parent()
	if home is None or home.path == '/':
		return False
	return comp.path == home.path or comp.path.startswith(home.path + '/')

def onPreInstall(info):
	"""Called before the family is installed into the registry."""
	pass

def onPostInstall(info):
	"""Called after the family is installed into the registry."""
	pass

def onPreUninstall(info):
	"""Called before the family is uninstalled from the registry."""
	pass

def onPostUninstall(info):
	"""Called after the family is uninstalled from the registry."""
	pass

def onPlaceOp(info):
	"""
	Called before placing an operator from the TAB menu.

	info keys:
		lookupName (str) - operator name, MODIFIABLE to swap operator
		panelValue (int) - click position

	Return: True = place, False = cancel+close, None = ActionOp (keep menu)

	Example - swap operator:
		if some_condition:
			info['lookupName'] = 'alternative_operator'
		return True
	"""
	return True

def onPostPlaceOp(info):
	"""
	Called after operator placement.

	info keys:
		clone - the placed operator
	"""
	pass

def onSupportDot(info):
	"""
	Example callback for a manifest pop_menu item.

	In family_info:
		"PopMenu": [
			{"label": "Support", "callback": "onSupportDot"}
		]

	Or in OpInfo:
		"pop_menu": [
			{"label": "Support", "callback": "onSupportDot"}
		]

	info keys:
		family - family name
		opType - OP Create menu op type
		opLabel - OP Create menu label
		item - clicked menu item label
		menuEntry - original pop_menu entry dict
		scope - 'family' for family_info.PopMenu, 'operator' for OpInfo.pop_menu
	"""
	pass

def onPreStub(info):
	"""
	Called before stubbing an operator.

	info keys:
		comp - the operator to stub, MODIFIABLE

	Return: True = proceed, False = skip this operator
	"""
	return not _inToolkit(info.get('comp'))

def onPostStub(info):
	"""
	Called after stubbing an operator.

	info keys:
		stub - the stub component
		original - the original component
	"""
	pass

def onCaptureExtraInfo(info):
	"""
	Called before stub/update to capture arbitrary data for later restoration.

	info keys:
		comp - the operator about to be stubbed/updated (full access)
		scenario (str) - 'stub' or 'update'

	Set info['returnValue'] to a dict of data to preserve.
	This dict is passed as 'extraInfo' in onPostReplace/onPostUpdate.

	Example:
		# info['returnValue'] = {
		#     'customState': info['comp'].op('state').text,
		#     'userData': info['comp'].fetch('myData', None),
		# }
	"""
	pass

def onPreReplace(info):
	"""
	Called before replacing a stub with the real operator.

	info keys:
		stub - the stub to replace, MODIFIABLE

	Return: True = proceed, False = skip this stub
	"""
	return not _inToolkit(info.get('stub'))

def onPostReplace(info):
	"""
	Called after replacing a stub with the real operator.

	info keys:
		newComp - the restored operator
		stub - the original stub (about to be destroyed)
		extraInfo (dict) - data captured by onCaptureExtraInfo, or {}

	Example:
		# extra = info['extraInfo']
		# if extra.get('customState'):
		#     info['newComp'].op('state').text = extra['customState']
	"""
	pass

def onPreUpdate(info):
	"""
	Called before updating an operator to a new version.

	info keys:
		oldComp - the existing operator
		master - the new master to update from, MODIFIABLE

	Return: True = proceed, False = skip this operator
	"""
	return not _inToolkit(info.get('oldComp'))

def onPostUpdate(info):
	"""
	Called after updating an operator to a new version.

	info keys:
		newComp - the updated operator
		extraInfo (dict) - data captured by onCaptureExtraInfo, or {}

	Example:
		# extra = info['extraInfo']
		# if extra.get('customState'):
		#     info['newComp'].op('state').text = extra['customState']
	"""
	pass

def onPreserveSpecialParams(info):
	"""
	Called during update/replace to preserve custom parameters.

	info keys:
		newComp - the new operator
		source - the old operator or stored params dict
	"""
	pass

def onCaptureChildrenParams(info):
	"""
	Called after capturing children params during stubbing.
	Modify children_data in place to add/remove entries.

	info keys:
		comp - the operator being stubbed
		children_data (dict) - captured params by relative path, MODIFIABLE
	"""
	pass

def onDeployManifest(info):
	"""
	Called for each operator COMP after its manifest is deployed/updated.

	info keys:
		comp - the operator COMP that received the manifest
		opType (str) - the operator type
		OpInfo (dict) - validated operator info
		ParRetain (dict) - parameter retention rules
		Shortcuts (dict) - keyboard shortcut mappings
	"""
	pass
