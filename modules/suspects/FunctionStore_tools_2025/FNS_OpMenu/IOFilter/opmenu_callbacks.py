"""IOFilter's contributions to TD's Insert Operator dialog.

Published through the OpMenuRegistry host next to this DAT. What the legacy
installer hardcoded -- splice script_IOFilter into the node table's chain,
inject radioExpose into the dialog's search panel -- IOFilter now declares
for itself, so the op-menu component holds no knowledge of this tool.

The Active toggle is read HERE too: whether IOFilter contributes at all is
IOFilter's own decision, not a special case in the installer. parexec_active
calls the registry back when the toggle flips.
"""


def _enabled():
	"""The user-facing switch: Iofilteractive on FNS_OpMenu itself --
	the tool owns its toggle, no root parameter involved."""
	try:
		return bool(me.parent(2).par.Iofilteractive.eval())
	except Exception as e:
		debug('IOFilter: Iofilteractive unreadable, defaulting on:', e)
		return True


def onChainNodes():
	"""The filter stage, spliced downstream of the registry's own node."""
	if not _enabled():
		return []
	return [me.parent().op('script_IOFilter')]


def onPanels():
	"""The io / -io / all radio, anchored to the dialog's search panel."""
	if not _enabled():
		return []
	return [(me.parent().op('radioExpose'), 'searchpanel')]
