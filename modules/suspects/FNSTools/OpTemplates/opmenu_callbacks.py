"""OpTemplates' contributions to TD's Insert Operator dialog.

Everything the op menu shows on behalf of OpTemplates is decided HERE,
inside the tool: the '>>>' marker on operator types that have a template,
and the 'Edit Templates...' right-click item. The OpMenuRegistry host next
to this DAT publishes it and holds only a reference -- the op-menu component
never names OpTemplates, and this behaviour travels inside OpTemplates' own
tox. See OpMenuRegistryExt for the full callback protocol.
"""

MARK = ' >>>'
EDIT_TEMPLATES = 'Edit Templates...'


def _templates():
	"""This tool's optype -> [template ops] map, or None when unavailable."""
	comp = me.parent()
	if comp is None or not comp.extensionsReady:
		return None
	try:
		return comp.Templates
	except Exception as e:
		debug('OpTemplates: templates unavailable:', e)
		return None


def onDecorateLabel(opType, label):
	"""The registry marks every type that has an alternative, this library's
	included, so the mark reads the same whoever contributed it. Nothing to
	add here any more."""
	return None


def onAlternatives():
	"""This tool's library, offered as alternatives: {opType: [template op]}.

	The registry labels each bare op with its name, so a template called
	`lfo_smooth` under `lfoCHOP` shows up as exactly that. Placement, the
	popup and the hotkey gate are the registry's; this only says what exists.
	"""
	return _templates() or {}


def onShippedAlternatives():
	"""The types the tool's OWN base offers -- what ships in the tox -- for
	the manifest's alternatives_for. onAlternatives() reads the ACTIVE
	library, which on a developer's machine is their palette or project set;
	the store must advertise the shipped set, not that."""
	comp = me.parent()
	if comp is None or not comp.extensionsReady:
		return {}
	base = comp.op('OPTemplates1')
	if base is None:
		return {}
	out = {}
	for type_base in base.children:
		if not type_base.isCOMP:
			continue
		ops = [o for o in type_base.children if not o.inputs and not o.dock]
		if ops:
			out[type_base.name] = ops
	return out


def onMenuItems():
	"""Right-click items this tool adds to the node table."""
	return [EDIT_TEMPLATES]


def onMenuItem(label, opType):
	"""Open (or create) the template base for the clicked operator type."""
	if label != EDIT_TEMPLATES:
		return
	comp = me.parent()
	if comp is None or not comp.extensionsReady:
		return
	comp.OpenTemplateBase(opType)
