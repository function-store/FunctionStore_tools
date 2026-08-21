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


def fns_command(fn=None, *, id=None, label=None, help='', params=None,
				args=None, kwargs=None, hidden=False, builtin=False):
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
	"""
	def mark(f):
		f._fns_command = {
			'id': id, 'label': label, 'help': help,
			'params': params, 'args': args, 'kwargs': kwargs,
			'hidden': hidden, 'builtin': builtin,
		}
		return f
	return mark(fn) if callable(fn) else mark


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
