"""FNSCommand - quick-launch command helpers (FNS_CommandRegistry).

Mark promoted (uppercase) extension methods as commands with
@fns_command, then call announce() once from your extension's DEFERRED
init. The attribute is the contract - a `_fns_command` dict on a
promoted method - so this module is convenience, not coupling: it
imports nothing of the registry, works with no registry anywhere, and
any vendored copy of these functions is compatible forever.

The registry harvests marked methods by reflection and derives whatever
the decorator omits from the method itself: label from the CamelCase
name, help from the docstring's first line, params from the signature
(type hints -> styles, typing.Literal[...] -> menu, defaults ->
defaults, a missing default makes the param required).

Usage (the docked-ExtUtils import is available at class-compile time,
so load order can never break it):

	FNSCommand = next(
		d for d in me.docked if 'ExtUtils' in d.tags
	).mod('FNSCommand')  # import

	class MyToolExt:
		@FNSCommand.fns_command(help='Set the project tempo')
		def SetBpm(self, bpm: float = 120, sync: bool = False):
			...

		def onInitTD(self):
			run('args[0]._announceCommands()', self, delayFrames=60)

		def _announceCommands(self):
			FNSCommand.announce(self.ownerComp)

See docs/fns-command-registry.md in the TDXLPP repo for the full
contract (spec fields, param styles, coercion rules).
"""


CONTEXT_TOKENS = ('network', 'selected', 'current', 'rollover-op', 'rollover-par')


def fns_command(fn=None, *, id=None, label=None, help='', params=None,
				args=None, kwargs=None, hidden=False, builtin=False,
				state=None, surface=None, capability=None, context=None,
				canonical=None):
	"""Mark a promoted extension method as a quick-launch command.

	Pure metadata - safe at class-compile time with no registry present.
	Every argument is optional; anything omitted is derived from the
	method at harvest. Works bare (@fns_command) or with arguments
	(@fns_command(label='...', params=[...])). hidden=True declares the
	command surfaced only when a user opts in (consumers keep it off
	their default listings - an "advanced" affordance, not a secret).
	builtin=True marks TD/system functionality (registry >= 1.4.0):
	consumers list it with their native commands rather than under
	tools - FNS tools should not normally set it.

	state (registry >= 1.6.0) declares where the command's live value
	lives so consumers can chip it (ON/OFF on toggles, the number on
	setters): 'Parname' names a custom par on the owner COMP, or
	{'method': 'GetX'} names a promoted no-arg method for computed
	state. Evaluated at QUERY time by the registry - never stale, and
	it MUST be trivially cheap (a par read, a one-liner).

	surface (registry >= 1.7.0) names the consumer surfaces the command
	wants to appear on - a token or list of tokens. Absent = today's
	behaviour (quick-launch only). Known surfaces: 'quick', 'session'
	(the launcher's Current-view companion bar), 'context-menu' (its
	session right-click menu). Consumers ignore tokens they don't
	serve, so new surfaces cost nothing to declare early.

	capability (registry >= 1.7.0) marks the command as part of a
	BLESSED capability ('fns.collect') - consumers that recognise the
	id may render rich native UI for the command group; ones that
	don't fall back to generic rendering. Never a gate.

	context (registry >= 1.8.0) declares WHAT the command acts on, which
	is a different axis from `surface` (where it is SHOWN). It lets a
	consumer contextualise: grey out a command whose subject is absent,
	and pre-resolve that subject before invoking. A token or a list of
	tokens; absent means the command needs nothing external.

		'network'       the current pane's owner COMP
		'selected'      the operator(s) selected in that pane
		'current'       the single current operator
		'rollover-op'   the operator under the cursor
		'rollover-par'  the parameter under the cursor

	The vocabulary deliberately matches Envoy's get_focus, so the two
	systems answer "what is the user looking at?" with the same words
	rather than inventing a second dialect. A LIST means any of them
	will do, and resolve_context() returns the first that resolves -
	e.g. context=['selected', 'current'] for a command happy with
	either.

	canonical (registry >= 1.9.0) is a CROSS-PACKAGE identity, used only
	to decide which of two packages offering the same command wins:
	newest `Pkgversion` wins, a tie keeps the incumbent, and it never
	prompts - the same rule the registry family uses for promoted
	globals. The winner's spec replaces the loser's entire; the loser is
	listed by the registry's Shadowed() rather than dropped silently.

	It is deliberately OPT-IN and never derived from `id`. `toggleactive`
	appears twelve times across twelve different tools, and `path#id`
	already keeps them apart - deriving identity from the id would
	collapse twelve working commands into one. Declare it only when two
	packages genuinely offer the SAME command, e.g.
	canonical='fns.swapops.swap-selected'.

	Declaring it is free: a consumer that does not know the field
	ignores it, exactly as `surface` and `capability` were added.
	"""
	def mark(f):
		f._fns_command = {
			'id': id, 'label': label, 'help': help,
			'params': params, 'args': args, 'kwargs': kwargs,
			'hidden': hidden, 'builtin': builtin, 'state': state,
			'surface': surface, 'capability': capability,
			'context': context, 'canonical': canonical,
		}
		return f
	return mark(fn) if callable(fn) else mark


def resolve_context(context):
	"""The live subject a context token names, as (token, subject).

	Returns (None, None) when nothing resolves. Pure td access with no
	registry involved, so a consumer can call this knowing nothing about
	FNS - and a vendored copy keeps working forever, which is the whole
	contract of this module.

	A command whose context does NOT resolve is better offered greyed
	out than hidden: the user can still see it exists and learn what it
	wants, which a missing entry cannot teach.
	"""
	if not context:
		return (None, None)
	tokens = [context] if isinstance(context, str) else list(context)
	for token in tokens:
		subject = _resolve_one(token)
		if subject is not None:
			return (token, subject)
	return (None, None)


def _resolve_one(token):
	"""One token's subject, or None. Never raises."""
	try:
		if token == 'network':
			return ui.panes.current.owner
		if token == 'selected':
			selected = ui.panes.current.owner.selectedChildren
			return list(selected) if selected else None
		if token == 'current':
			return ui.panes.current.owner.currentChild
		if token == 'rollover-op':
			return ui.rolloverOp
		if token == 'rollover-par':
			# the ParGroup only when it is genuinely multi-component -- the
			# same "decide from what is hovered" rule the par tools follow
			group = getattr(ui, 'rolloverParGroup', None)
			if group is not None and len(group) > 1:
				return group
			return ui.rolloverPar
	except Exception:
		return None
	return None


def announce(comp):
	"""Tag COMP as a command carrier and announce it to the registry.

	The tag is TD-native (needs no registry) and doubles as the DURABLE
	announcement: a registry that arrives - or is version-replaced -
	later rediscovers COMP by rescanning tags, re-harvesting the live
	class. The guarded Register(comp) makes a listening registry harvest
	the marked methods right now. Call from a DEFERRED extension init
	(run(..., delayFrames=60)) so the registry's own promotion and TDN
	imports have settled. Never raises; returns the registry's reply
	dict, or None when no registry is present.
	"""
	try:
		comp.tags.add('fnscommands')
	except Exception:
		pass
	try:
		reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
		if reg is not None and hasattr(reg, 'Register'):
			return reg.Register(comp)
	except Exception:
		pass
	return None
