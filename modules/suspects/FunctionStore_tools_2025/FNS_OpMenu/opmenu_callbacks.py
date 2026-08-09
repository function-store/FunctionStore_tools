"""FNS_OpMenu's own contributions to TD's Insert Operator dialog.

Published through this component's OpMenuRegistry host, which holds only a
reference to this DAT -- the behaviour lives here, with the tool that owns
it. See OpMenuRegistryExt for the full callback protocol.
"""


def onSearchWords():
	"""Extra fuzzy-search words per operator type.

	Sourced from this component's OpSearchWords table via its own extension,
	so edits to the table (watched by datexec1) are picked up live.
	"""
	comp = me.parent()
	if comp is None or not comp.extensionsReady:
		return {}
	try:
		return dict(comp.SearchWordDict)
	except Exception as e:
		debug('FNS_OpMenu: search words unavailable:', e)
		return {}
