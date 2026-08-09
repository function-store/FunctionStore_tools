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
	"""Mark operator types that have a template behind them."""
	templates = _templates()
	if templates and opType in templates:
		return label + MARK
	return None


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
