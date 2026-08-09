"""OpMenuRegistry callbacks -- contributions to TD's Insert Operator dialog.

Spawned by the 'Create Callbacks' pulse on an OpMenuRegistry host, which
also points that host's Callback parameter at this DAT. Nothing else is
needed: fill in the hooks you want and the dialog picks them up.

HOW IT WORKS
    Your tool ships ONE registry host + ONE of these DATs. The host
    registers your tool with the /sys global registry, and the entry stores
    only a REFERENCE to this DAT -- the behaviour lives here, with your
    tool, and travels inside your tool's .tox. The op-menu component never
    needs to know your tool exists.

THE CONTRACT
    EVERY HOOK IS OPTIONAL. The registry probes this module for the names
    below and uses whatever it finds, so a tool that only adds search words
    defines only onSearchWords(). As shipped this file contributes NOTHING
    -- every hook returns empty. Uncomment the example lines, or write your
    own, to start contributing.

    `me` is this DAT, so `me.parent()` is your tool. Resolve everything
    from there -- never an absolute path, never a global shortcut.

    A hook that raises is contained: the registry reports it with debug(),
    skips that one contribution, and the dialog keeps working.

LIVE TOGGLES
    Returning empty WITHDRAWS a contribution -- the registry prunes
    whatever it had injected. That is how you make a contribution
    conditional: decide it HERE (it is your tool's decision, not the
    registry's), then call op.OPMENUREGISTRY.Resync() when your condition
    changes, or let the ~2s healing tick pick it up.
    See FNS_OpMenu/IOFilter for a worked example driven by a parameter.
"""


def onSearchWords():
	"""Extra fuzzy-search words per operator type.

	-> dict: {opType: [word, ...]}

	Merged with every other tool's contribution; duplicates are dropped and
	blanks stripped. Typing any of your words in the dialog's search field
	then matches that operator type.
	"""
	# return {'noiseTOP': ['grain', 'fractal', 'perlin']}
	return {}


def onDecorateLabel(opType, label):
	"""Rewrite one row's label in the operator table.

	-> str to replace the label, or None to leave it alone.

	Called once per visible row, per cook, for EVERY operator type -- keep
	it cheap. Resolve anything expensive once (e.g. a cached property on
	your extension), never per call. Decorators chain: if several tools
	decorate, each sees the previous one's result.
	"""
	# if opType in me.parent().MyInterestingTypes:
	# 	return label + ' *'
	return None


def onMenuItems():
	"""Items this tool adds to the node table's right-click menu.

	-> list of str.

	They are appended after TD's own three (Help / Python Help / Operator
	Snippets), in registration order across tools.
	"""
	# return ['Do Something...']
	return []


def onMenuItem(label, opType):
	"""One of YOUR menu items was clicked.

	label   -- which of your onMenuItems() entries was chosen
	opType  -- the operator type of the row that was right-clicked

	Only your own items reach this; TD's built-ins are handled upstream.
	"""
	# comp = me.parent()
	# if comp is not None and comp.extensionsReady:
	# 	comp.DoSomething(opType)
	return


def onChainNodes():
	"""Script DATs to splice into the operator table's filter chain.

	-> list of scriptDAT, in the order you want them applied.

	The registry copies each one into the dialog downstream of its own
	node, keeps the chain wired, and prunes the copies when you stop
	publishing them. Use this to filter or rewrite the operator table
	itself (see IOFilter, which hides or isolates I/O operators).

	Each stage cooks with the previous stage's table as its input.
	"""
	# return [me.parent().op('script_MyFilter')]
	return []


def onPanels():
	"""Panel COMPs to inject into the dialog.

	-> list of (comp, anchor_name).

	anchor_name names a panel inside /ui/dialogs/menu_op whose output the
	injected panel's input is wired to -- 'searchpanel' puts it beside the
	search field. WITHOUT an anchor the panel drops out of the dialog's
	layout flow and will not be visible.
	"""
	# return [(me.parent().op('myPanel'), 'searchpanel')]
	return []
