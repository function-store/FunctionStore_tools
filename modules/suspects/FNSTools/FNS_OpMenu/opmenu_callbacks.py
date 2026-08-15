"""FNS_OpMenu's own contributions to TD's Insert Operator dialog.

Published through this component's OpMenuRegistry host, which holds only a
reference to this DAT -- the behaviour lives here, with the tool that owns
it. See OpMenuRegistryExt for the full callback protocol.
"""


SEARCH_WORDS_TABLE = 'OpSearchWords'


def onSearchWords():
	"""Extra fuzzy-search words per operator type.

	AFFECTS: the 'score' column of rows in /ui/dialogs/menu_op/nodetable,
	applied by the script_inject stage this component publishes below.

	Read straight from the OpSearchWords table: the table IS the data, so an
	edit shows up on the next cook with no cached copy to keep in sync. The
	registry calls this once per cook, not once per row.
	"""
	table = me.parent().op(SEARCH_WORDS_TABLE)
	if table is None:
		debug('FNS_OpMenu: no %r table' % SEARCH_WORDS_TABLE)
		return {}
	words = {}
	for row in table.rows()[1:]:
		optype = row[0].val.strip()
		if not optype:
			continue
		words[optype] = [w.strip() for w in row[1].val.split(',') if w.strip()]
	return words


def onChainNodes():
	"""The stage that APPLIES the registry's aggregated contributions.

	script_inject rescores and relabels TD's operator table using
	op.FNS_OPMENUREGISTRY.SearchWords and .Decorators -- i.e. every tool's
	contributions, not just this one's. It lives here rather than in the
	registry because it is bound to TD's node-table schema (its columns, its
	score range, its 'layouts/...' type strings); keeping that opinion in a
	tool leaves the registry itself schema-agnostic.
	"""
	return [me.parent().op('script_inject')]
