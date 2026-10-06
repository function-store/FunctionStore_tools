'''Info Header Start
Name : FNSCommandRegistryExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
"""
FNS_CommandRegistry - runtime command registry, FNS registry-family shape.

Tools running in a project announce commands here at runtime ("here I am,
I can do this and that"). Consumers are anything that can resolve the
global shortcut - the TDXLU launcher lists them in its quick-launch
palette (under the commands prefix `>` and the tools prefix `?`) and
executes them over the utility TCP bus (`fns_commands` /
`fns_run_command`, see utility/heartbeat/PROTOCOL.md), but the registry
is a generic API layer: navbars, hotkey managers, or any other surface
can read `Commands()` and call `Run(key)` the same way.

Family shape (mirrors the FNS_*Registry components in FunctionStore
tools): the copy shipped inside TDXLauncherUtility is a SHIPPER. On init
it promotes a copy of itself into `/sys/FNS_Registries` (surviving utility
updates and removal for the lifetime of the TD process), that copy claims
the global OP shortcut `op.FNS_COMMANDREGISTRY`, and a newer shipped
version replaces an older global, carrying its registrations across.
Dormant shippers forward every call to the global instance.

Tools MUST call in guarded - no registry is ever guaranteed to exist in
a project (see docs/fns-command-registry.md for the full contract):

	reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
	if reg is not None and hasattr(reg, 'Register'):
		reg.Register(me.parent(), [
			{'id': 'toggle', 'label': 'Toggle HydroHomie',
			 'help': 'Show or hide the reminder overlay',
			 'method': 'Toggle'},
		])

Push registrations live in the global extension instance; `/sys` outlives
project loads, and registrations whose owner path no longer resolves are
pruned lazily. Tools that also tag their COMP `fnscommands` and expose a
promoted `FnsCommands()` returning the same spec list survive every
ordering: the registry rescans tagged COMPs whenever a (new) global
instance initializes.

Multiple instances of one tool (registry >= 1.11.0): every owner COMP
registers on its own path, so N copies of a tool are N independent
command sets whose keys never collide. Two optional promoted hooks on the
owner make them legible and keep curation shared: `FnsInstance()` returns
a short label for THIS copy (evaluated on every Commands() build, like
`state`, and sent as `instance`), and `FnsToolName()` returns the tool's
public name when the COMP name varies per copy (`Scope1`, `Scope2`), so
favourites, overrides and presets keyed on `tool#id` apply to every copy.
"""

import inspect
import json
import re
import typing


def _publicName(name):
	"""A tool's PUBLIC name: its COMP name with a leading FNS_ removed.

	The prefix is an operator-name convention (it groups the toolkit in a
	network and keeps a dropped COMP from colliding with a user's own
	`Console`). In a LIST it is noise, and worse than noise once the list
	is sorted: every FNS tool collapses under "F" and the letter that
	tells them apart is the fifth character. Consumers show this field,
	so this is where the prefix comes off. See docs/PublicToolNames.md.

	This is also the curation identity (`tool#id`), so it is as permanent
	as a command id: renaming a tool's public name orphans favourites,
	hidden overrides and presets exactly as renaming an id does.
	"""
	return name[4:] if name.startswith('FNS_') else name


class FNSCommandRegistryExt:
	"""Registry of tool-announced commands (see module doc)."""

	REGISTRY_NAME = 'FNS_CommandRegistry'
	SHORTCUT = 'FNS_COMMANDREGISTRY'
	REGISTRY_VERSION = '1.12.0'

	# Promoted globals share one /sys container -- family convention with
	# the FNS_*Registry components in FunctionStore tools -- rather than
	# sitting loose among TD's own /sys furniture.
	SYS_HOME = 'FNS_Registries'

	# Tools opt into init-rescan discovery by carrying this tag AND a
	# promoted FnsCommands() method returning their spec list.
	TOOL_TAG = 'fnscommands'
	# The shipped built-in command owners live inside this master; the
	# runtime /sys copy must not carry a second set (see _sanitizeSysCopy).
	BUILTINS_NAME = 'FNS_BuiltinCommands'
	MAX_COMMANDS_PER_TOOL = 24
	# A catalogue owner (tagged CATALOG_TAG) serves one command per item it
	# offers -- FNS_Installer's install-<Package> rows -- so it gets a larger
	# cap (registry >= 1.12.0, docs/CommandAvailability.md).
	CATALOG_TAG = 'fnscatalog'
	MAX_CATALOG_COMMANDS = 128
	MAX_PARAMS_PER_COMMAND = 6
	MAX_SURFACES_PER_COMMAND = 8
	PARAM_STYLES = ('str', 'int', 'float', 'toggle', 'menu')
	_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_\-]{0,47}$')
	# Surface tokens (registry >= 1.7.0): consumer surfaces a command wants
	# to appear on. The registry is taste-free here — any well-formed token
	# is accepted and consumers ignore ones they don't serve, so new
	# surfaces are additive with no registry change. Known today: 'quick'
	# (the default when the field is absent), 'session' (the launcher's
	# Current-view companion bar), 'context-menu' (its session right-click
	# menu).
	_SURFACE_RE = re.compile(r'^[a-z0-9][a-z0-9_\-]{0,23}$')
	# Capability ids (registry >= 1.7.0): a well-known, namespaced marker
	# ('fns.collect') telling consumers this command belongs to a BLESSED
	# capability they may render rich native UI for. Unknown ids simply get
	# the generic rendering — progressive enhancement, never a gate.
	_CAPABILITY_RE = re.compile(r'^[a-z0-9][a-z0-9_.\-]{0,63}$')
	_CANONICAL_RE = re.compile(r'^[a-z0-9][a-z0-9_.\-]{0,63}$')
	# Context tokens (registry >= 1.8.0): WHAT the command acts on, which is
	# a different axis from `surface` (where it is SHOWN). Lets a consumer
	# grey out a command whose subject is absent and pre-resolve the subject
	# before invoking. Validated for SHAPE only, like surface -- the known
	# set below is the blessed vocabulary, not a whitelist, so a future
	# token needs no registry bump. It matches Envoy's get_focus on purpose.
	CONTEXT_TOKENS = ('network', 'selected', 'current',
					  'rollover-op', 'rollover-par')
	MAX_CONTEXTS_PER_COMMAND = 5
	_CONTEXT_RE = re.compile(r'^[a-z0-9][a-z0-9_\-]{0,23}$')

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		# owner path -> {'tool': name, 'commands': [clean spec, ...]}
		self._registry = {}
		self._rev = 0
		# Deferred + idempotent: TDN import may rebuild children after
		# init, and tools may still be initializing themselves.
		run('args[0].postInit()', self, delayFrames=10)

	def postInit(self):
		self._ensureGlobalRegistry()
		if self._isGlobal():
			self.RescanTools()
		else:
			g = self._globalRegistry()
			self._setStatus(
				f'dormant shipper - global at {g.path}' if g is not None
				else 'dormant shipper - no global registry'
			)

	def Version(self):
		"""This instance's registry version (family version-compare)."""
		return self.REGISTRY_VERSION

	def Rev(self):
		"""Monotonic change counter - bumps on every registry mutation."""
		g = self._forwardTarget()
		if g is not None:
			return g.Rev()
		return int(self._rev)

	# --- registration ------------------------------------------------------

	def Register(self, owner, commands=None):
		"""Replace OWNER's registered command set. Never raises.

		owner: the tool's COMP (or its path). commands: list of dicts
		{'id', 'label', 'method', optional 'help', 'args', 'kwargs',
		'params'} — params declare USER-suppliable keyword arguments
		({'name', optional 'label', 'style' (str|int|float|toggle|menu),
		'required', 'default', 'menu', 'help'}); consumers prompt for
		them and Run coerces + validates the values by declared style.

		commands=None HARVESTS instead: promoted (uppercase) extension
		methods carrying a `_fns_command` dict attribute — the decorator
		protocol — become the command set, with id/label/help/params
		falling back to the method name, its docstring's first line, and
		its signature (type hints -> styles, typing.Literal -> menu,
		defaults -> defaults, no default -> required).

		An empty list unregisters. Returns {'ok': bool, ...}.
		"""
		g = self._forwardTarget()
		if g is not None:
			return g.Register(owner, commands)
		try:
			comp = self._resolveOwner(owner)
			if comp is None:
				return {'ok': False, 'error': f'owner not found: {owner}'}
			if commands is None:
				commands = self._harvestDecorated(comp)
				# The tag doubles as the DURABLE announcement: a future
				# registry (first injection, version replacement) rediscovers
				# this announcer by rescanning tags and re-harvests the live
				# class. Harvest path only — an explicit-spec registration
				# must NOT be auto-tagged, or a later rescan would harvest
				# the (markless) COMP and wipe its explicit set.
				if commands:
					try:
						comp.tags.add(self.TOOL_TAG)
					except Exception:
						pass
			specs = []
			seen = set()
			commands = list(commands or [])
			cap = (self.MAX_CATALOG_COMMANDS if self.CATALOG_TAG in comp.tags
				   else self.MAX_COMMANDS_PER_TOOL)
			dropped = max(0, len(commands) - cap)
			if dropped:
				# never silently: the drop is logged once per owner and named
				# on the result
				warned = getattr(self, '_capWarned', None)
				if warned is None:
					warned = self._capWarned = set()
				if comp.path not in warned:
					warned.add(comp.path)
					debug(f'FNS_CommandRegistry: {comp.path} offered {len(commands)} commands, '
						  f'the cap is {cap}; {dropped} dropped')
			for spec in commands[:cap]:
				clean = self._cleanSpec(spec)
				if clean['id'] in seen:
					return {'ok': False, 'error': f"duplicate command id: {clean['id']}"}
				seen.add(clean['id'])
				specs.append(clean)
			if not specs:
				self._registry.pop(comp.path, None)
			else:
				self._registry[comp.path] = {
					'tool': self._toolName(comp), 'commands': specs}
			self._bump()
			return {
				'ok': True,
				'tool': self._toolName(comp),
				'registered': len(specs),
				'rev': self._rev,
				**({'dropped': dropped, 'cap': cap} if dropped else {}),
			}
		except Exception as e:
			return {'ok': False, 'error': str(e)}

	def Unregister(self, owner):
		"""Drop OWNER's commands (COMP or path). Never raises."""
		g = self._forwardTarget()
		if g is not None:
			return g.Unregister(owner)
		try:
			path = None
			comp = self._resolveOwner(owner)
			if comp is not None:
				path = comp.path
			elif isinstance(owner, str):
				# The tool may already be mid-destroy - accept its path.
				path = owner
			removed = self._registry.pop(path, None) is not None if path else False
			if removed:
				self._bump()
			return {'ok': True, 'removed': removed, 'rev': self._rev}
		except Exception as e:
			return {'ok': False, 'error': str(e)}

	def RescanTools(self):
		"""Collect commands from every COMP tagged TOOL_TAG: its promoted
		FnsCommands() spec list when it has one, else its decorated
		(`_fns_command`-marked) methods. Safety net for load order: covers
		tools that registered before the global registry (re)initialized —
		and, for tag+decorator tools, replaces push registration entirely."""
		g = self._forwardTarget()
		if g is not None:
			return g.RescanTools()
		found = 0
		try:
			# `op('/')`, not `root` -- root is not reliably bound in every
			# exec context (project rule, td-python.md).
			tagged = op('/').findChildren(tags=[self.TOOL_TAG], maxDepth=None)
			# /sys is NOT reachable from a '/' sweep -- measured: the same
			# tag query returns 44 from '/' and finds neither of the two
			# tagged COMPs under /sys. The registry-family tools live there
			# BY DESIGN (only the promoted global may register), so without
			# this second pass the tag -- which is supposed to be the durable
			# rediscovery mechanism -- can never find them, and a registry
			# that reinitialises loses their commands until something calls
			# Register() by hand.
			sys_home = op('/sys')
			if sys_home is not None:
				seen = {c.path for c in tagged}
				tagged = list(tagged) + [
					c for c in sys_home.findChildren(tags=[self.TOOL_TAG], maxDepth=None)
					if c.path not in seen
				]
		except Exception as e:
			debug(f'FNS_CommandRegistry: rescan failed: {e}')
			tagged = []
		for comp in tagged:
			if comp is self.ownerComp:
				continue
			try:
				getter = getattr(comp, 'FnsCommands', None)
				specs = getter() or [] if callable(getter) else None
				res = self.Register(comp, specs)  # None -> harvest decorated
				if res.get('ok') and res.get('registered', 0) > 0:
					found += 1
				elif not res.get('ok'):
					debug(f"FNS_CommandRegistry: {comp.path}: {res.get('error')}")
			except Exception as e:
				debug(f'FNS_CommandRegistry: {comp.path}: {e}')
		self._refreshSurface()
		return {'ok': True, 'tools': found, 'rev': self._rev}

	# --- consumption (launcher bus verbs land here via the Utility ext,
	# --- but any in-TD consumer may call these directly) -------------------

	def Commands(self):
		"""Flat wire-ready list; prunes registrations whose tool is gone.

		Declared `state` / param `current` references are evaluated HERE,
		at query time, against the live tool — so the values consumers see
		are always current, with no re-registration on state change. A
		reference that fails to evaluate simply omits its key."""
		g = self._forwardTarget()
		if g is not None:
			return g.Commands()
		out = []
		pruned = False
		for path in list(self._registry):
			entry = self._registry[path]
			comp = op(path)
			if comp is None or not comp.valid:
				del self._registry[path]
				pruned = True
				continue
			# A tool that cannot run offers nothing (registry >= 1.12.0,
			# docs/CommandAvailability.md): hidden, not greyed, and the
			# registration is kept so it returns the moment the tool is on.
			if self._ownerUnavailable(comp, entry) is not None:
				continue
			# Evaluated once per owner, fresh on every build: a copy retargeted
			# at runtime relabels on the next fetch with no re-announce.
			instance = self._evalInstance(comp)
			for c in entry['commands']:
				if c.get('enabled') and not self._isEnabled(comp, entry, c):
					continue
				item = {
					'key': f"{path}#{c['id']}",
					'tool': entry['tool'],
					'id': c['id'],
					'label': c['label'],
					'help': c['help'],
					'path': path,
				}
				if instance is not None:
					item['instance'] = instance
				if c.get('params'):
					item['params'] = self._paramsForWire(comp, c['params'])
				if c.get('state'):
					val = self._evalStateRef(comp, c['state'])
					if val is not None:
						item['state'] = val
				if c.get('hidden'):
					item['hidden'] = True
				if c.get('builtin'):
					item['builtin'] = True
				if c.get('surface'):
					item['surface'] = list(c['surface'])
				if c.get('capability'):
					item['capability'] = c['capability']
				if c.get('context'):
					item['context'] = list(c['context'])
				if c.get('canonical'):
					item['canonical'] = c['canonical']
				out.append(item)
		if pruned:
			self._bump()
		out = self._arbitrate(out)
		out.sort(key=lambda c: (c['tool'].lower(), c['label'].lower()))
		return out

	def Run(self, key, args=None, kwargs=None):
		"""Execute one registered command by key ('<owner path>#<id>').

		Calls the tool's promoted method synchronously so the caller gets
		the real outcome - registered handlers should be quick actions.
		Never raises. Returns {'ok': bool, ...}.
		"""
		g = self._forwardTarget()
		if g is not None:
			return g.Run(key, args=args, kwargs=kwargs)
		try:
			key = str(key or '')
			path, _, cid = key.partition('#')
			entry = self._registry.get(path)
			spec = None
			if entry:
				spec = next((c for c in entry['commands'] if c['id'] == cid), None)
			if spec is None:
				return {'ok': False, 'error': f'unknown command: {key}'}
			comp = op(path)
			if comp is None or not comp.valid:
				del self._registry[path]
				self._bump()
				return {'ok': False, 'error': f"{entry['tool']} is no longer in the project"}
			why = self._ownerUnavailable(comp, entry)
			if why is None and spec.get('enabled') and not self._isEnabled(comp, entry, spec):
				why = f"{entry['tool']} is disabled"
			if why is not None:
				return {'ok': False, 'unavailable': True, 'error': why, 'key': key}
			fn = getattr(comp, spec['method'], None)
			if not callable(fn):
				return {
					'ok': False,
					'error': f"{entry['tool']} has no callable {spec['method']}",
				}
			call_args = list(args) if isinstance(args, (list, tuple)) else list(spec['args'])
			# Registered kwargs are the base; caller kwargs overlay them, with
			# declared params coerced + validated by style (the registry owns
			# validation so every consumer gets the same contract). Missing
			# declared params fall back to their default; required ones
			# without a value refuse the run.
			call_kwargs = dict(spec['kwargs'])
			declared = {p['name']: p for p in spec.get('params', [])}
			if isinstance(kwargs, dict):
				for k, v in kwargs.items():
					p = declared.get(k)
					if p is not None:
						try:
							call_kwargs[k] = self._coerceParamValue(p, v)
						except ValueError as ve:
							return {'ok': False, 'error': str(ve)}
					else:
						call_kwargs[k] = v
			for name, p in declared.items():
				if name in call_kwargs:
					continue
				if 'default' in p:
					call_kwargs[name] = p['default']
				elif p.get('required'):
					return {'ok': False, 'error': f'missing required argument: {name}'}
			try:
				result = fn(*call_args, **call_kwargs)
			except Exception as e:
				return {'ok': False, 'error': f"{entry['tool']}.{spec['method']}: {e}"}
			out = {'ok': True}
			if isinstance(result, dict):
				# Let the tool's own verdict through (an explicit ok:False wins).
				out.update(result)
			elif result is not None:
				try:
					json.dumps(result)
					out['result'] = result
				except (TypeError, ValueError):
					out['result'] = str(result)
			out.setdefault('ok', True)
			out['key'] = key
			out['tool'] = entry['tool']
			instance = self._evalInstance(comp)
			if instance is not None:
				out['instance'] = instance
			return out
		except Exception as e:
			return {'ok': False, 'error': str(e)}

	# --- family shape: /sys promotion + global shortcut --------------------

	def _sysHome(self, create=False):
		"""`/sys/FNS_Registries` -- where the promoted globals live.

		Global OP shortcuts resolve from any depth, so the nesting is
		invisible to callers. Only the promotion path passes create=True,
		so merely asking never grows a container."""
		sysc = op('/sys')
		if sysc is None:
			return None
		home = sysc.op(self.SYS_HOME)
		if home is None and create:
			try:
				home = sysc.create(baseCOMP, self.SYS_HOME)
				home.color = (0.35, 0.45, 0.55)
				anchor = sysc.op('TDDialogs') or sysc.op('TDResources')
				if anchor is not None:
					home.nodeX = anchor.nodeX
					home.nodeY = anchor.nodeY - 300
			except Exception as e:
				debug(f'FNS_CommandRegistry: could not create {self.SYS_HOME}: {e}')
				return None
		return home

	def _isGlobal(self):
		"""Is THIS instance the process-wide registry? (residency in the
		/sys home, or legacy: it already holds the shortcut.)"""
		try:
			par = self.ownerComp.parent()
			# bare '/sys' is the pre-container home -- still counts, so a
			# process that started before the move keeps working
			if par is not None and par.path in ('/sys', '/sys/' + self.SYS_HOME):
				return True
			return getattr(op, self.SHORTCUT, None) is self.ownerComp
		except Exception:
			return False

	def _globalRegistry(self):
		"""The live global instance, excluding self. Shortcut first, then
		a /sys scan (family convention)."""
		reg = getattr(op, self.SHORTCUT, None)
		if reg is not None and reg.valid and reg is not self.ownerComp:
			return reg
		for home in (self._sysHome(), op('/sys')):
			if home is None:
				continue
			try:
				for child in home.findChildren(name=self.REGISTRY_NAME + '*', maxDepth=1):
					if child is not self.ownerComp and child.valid:
						return child
			except Exception:
				continue
		return None

	def _forwardTarget(self):
		"""Global instance every call defers to when this one is a dormant
		shipper; None when this instance should answer itself."""
		if self._isGlobal():
			return None
		return self._globalRegistry()

	def Repromote(self):
		"""Dev helper: replace the /sys global with a fresh copy of THIS
		shipper, migrating registrations — regardless of version.

		Needed while iterating on this file: the /sys copy is deliberately
		file-detached, so a multi-save edit session can strand it on
		whichever intermediate save first bumped REGISTRY_VERSION (the
		later saves reach only the dormant shipper). Never raises."""
		try:
			cur = self._globalRegistry()
			state, rev = {}, 0
			if cur is not None:
				try:
					ext = cur.ext.FNSCommandRegistryExt
					state = dict(ext._registry)
					rev = int(ext._rev)
				except Exception:
					pass
				cur.destroy()
			home = self._sysHome(create=True)
			if home is None:
				return {'ok': False, 'error': '/sys not found'}
			new = home.copy(self.ownerComp, name=self.REGISTRY_NAME)
			new.allowCooking = True
			self._sanitizeSysCopy(new)
			new.par.opshortcut = self.SHORTCUT
			if state:
				self._migrateState(new, state, rev)
			return {'ok': True, 'path': new.path, 'migrated': len(state)}
		except Exception as e:
			return {'ok': False, 'error': str(e)}

	def _ensureGlobalRegistry(self):
		"""Promote a copy of this shipper into /sys (or replace an older
		global, migrating its registrations). Idempotent, never raises."""
		try:
			if self._isGlobal():
				self.ownerComp.par.opshortcut = self.SHORTCUT
				return
			cur = self._globalRegistry()
			state, rev = {}, 0
			if cur is not None:
				# a global parked directly in /sys predates the
				# FNS_Registries home: relocate it whatever its version, so
				# the two homes never both hold a live global
				cur_parent = cur.parent()
				parked = cur_parent is not None and cur_parent.path == '/sys'
				theirs = self._verTuple(self._peerVersion(cur))
				if not parked and self._verTuple(self.REGISTRY_VERSION) <= theirs:
					return  # current global is same or newer - stay dormant
				try:
					ext = cur.ext.FNSCommandRegistryExt
					state = dict(ext._registry)
					rev = int(ext._rev)
				except Exception:
					pass
				debug(
					f'FNS_CommandRegistry: replacing global '
					f'{self._peerVersion(cur)} with {self.REGISTRY_VERSION}'
				)
				cur.destroy()
			home = self._sysHome(create=True)
			if home is None:
				debug('FNS_CommandRegistry: /sys not found, cannot promote')
				return
			new = home.copy(self.ownerComp, name=self.REGISTRY_NAME)
			new.allowCooking = True
			self._sanitizeSysCopy(new)
			new.par.opshortcut = self.SHORTCUT
			if state:
				self._migrateState(new, state, rev)
		except Exception as e:
			debug(f'FNS_CommandRegistry: promotion failed: {e}')

	def _sanitizeSysCopy(self, comp):
		"""Detach the /sys copy from Embody file sync - it is a runtime
		clone, not an externalized artifact - and drop the shipped built-in
		owners, which register from the master like any other tool.

		A second set inside the copy would announce the same commands from
		a /sys path that RescanTools can never rediscover (root.findChildren
		does not see /sys), so it would be pruned and re-announced forever
		and, with canonical ids, shadow the master's set on a boot-order
		coin toss."""
		try:
			builtins = comp.op(self.BUILTINS_NAME)
			if builtins is not None:
				builtins.destroy()
		except Exception:
			pass
		strategy_tags = {'py', 'txt', 'tsv', 'json', 'xml', 'glsl', 'tdn'}
		try:
			kids = comp.findChildren(maxDepth=None)
		except Exception:
			kids = []
		for c in [comp] + list(kids):
			try:
				if hasattr(c.par, 'file'):
					c.par.file = ''
				if hasattr(c.par, 'syncfile'):
					c.par.syncfile = False
				c.tags = set(c.tags) - strategy_tags
			except Exception:
				continue

	def _migrateState(self, new_comp, state, rev, attempts=20):
		"""Hand the old global's registrations to the fresh copy once its
		extension has initialized (retry across frames like the family's
		global-extension-init loop)."""
		try:
			ext = new_comp.ext.FNSCommandRegistryExt
			ext._registry = dict(state)
			ext._rev = int(rev)
			ext._bump()
			return
		except Exception:
			pass
		if attempts > 0:
			run(
				lambda: self._migrateState(new_comp, state, rev, attempts - 1),
				delayFrames=10,
			)
		else:
			debug('FNS_CommandRegistry: state migration gave up')

	def _peerVersion(self, comp):
		try:
			fn = getattr(comp, 'Version', None)
			if callable(fn):
				return str(fn())
		except Exception:
			pass
		return '0.0.0'

	@staticmethod
	def _verTuple(ver):
		out = []
		for part in str(ver or '').split('.'):
			digits = ''.join(ch for ch in part if ch.isdigit())
			out.append(int(digits) if digits else 0)
		return tuple(out or [0])

	# --- canonical-id arbitration (registry >= 1.9.0) ----------------------

	@staticmethod
	def _verKey(ver):
		"""Comparable version key, PADDED so 1.0 equals 1.0.0.

		The registry family compares whole versions and treats a shorter
		one as EQUAL, not lower. A bare tuple would sort (1, 0) below
		(1, 0, 0) and silently demote a package that happened to write
		its version with two components."""
		parts = []
		for part in str(ver or '').split('.'):
			digits = ''.join(ch for ch in part if ch.isdigit())
			parts.append(int(digits) if digits else 0)
		while len(parts) < 4:
			parts.append(0)
		return tuple(parts[:4])

	def _packageVersion(self, comp):
		"""The registrator's Pkgversion, or '0.0.0' when it declares none.

		Absent is treated as LOWEST rather than as a refusal to arbitrate.
		Refusing would mean serving both copies, which is the exact outcome
		the arbitration exists to prevent. So a package that declares a
		version always beats one that does not, and two undeclared ones tie
		-- which the tie rule settles in favour of the incumbent."""
		if comp is None or not comp.valid:
			return '0.0.0'
		try:
			if hasattr(comp.par, 'Pkgversion'):
				val = str(comp.par.Pkgversion.eval() or '').strip()
				if val:
					return val
			about = comp.op('FNS_About')
			if about is not None and hasattr(about.par, 'Pkgversion'):
				val = str(about.par.Pkgversion.eval() or '').strip()
				if val:
					return val
		except Exception:
			pass
		return '0.0.0'

	def _arbitrate(self, items):
		"""Resolve commands declaring the same canonical id.

		NEWEST WINS, TIES KEEP THE INCUMBENT, AND IT NEVER PROMPTS -- the
		same rule the registry family uses when a shipped registry replaces
		an older promoted global. Reused deliberately: commands and globals
		should not need two arbitration policies in one head.

		The winner REPLACES the loser entire. A consumer asking for a
		canonical id gets one package's answer, not a merge of two -- a
		merge reads plausible and behaves surprisingly, because a surface
		or capability declared only by the LOSER would survive into the
		winning command.

		Losers are recorded for Shadowed() rather than dropped silently: a
		command that vanishes from a palette with no way to ask why is very
		hard to debug from the consumer side.

		Commands with no canonical id are never touched, which is why this
		is inert today -- nothing in the toolkit declares one yet.
		"""
		best = {}
		for item in items:
			cid = item.get('canonical')
			if not cid:
				continue
			ver = self._packageVersion(op(item['path']))
			item['pkgversion'] = ver
			cur = best.get(cid)
			# strict > keeps the FIRST-registered entry on a tie (incumbent)
			if cur is None or self._verKey(ver) > self._verKey(cur[0]):
				best[cid] = (ver, item)
		if not best:
			self._shadowed = []
			return items
		# The winner is a PACKAGE, not a single registration: every instance
		# of the winning tool keeps its command (registry >= 1.11.0). Keeping
		# one copy would silently hide the others, which is the multi-instance
		# design failing, not two packages competing.
		winning_tool = {cid: v[1]['tool'] for cid, v in best.items()}
		out, shadowed = [], []
		for item in items:
			cid = item.get('canonical')
			if not cid or item['tool'] == winning_tool[cid]:
				out.append(item)
				continue
			shadowed.append({
				'key': item['key'],
				'canonical': cid,
				'pkgversion': item.get('pkgversion', '0.0.0'),
				'lost_to': best[cid][1]['key'],
				'winner_version': best[cid][0],
			})
		self._shadowed = shadowed
		return out

	def Shadowed(self):
		"""Commands withheld because another package won their canonical id.

		Empty in the normal case. A consumer can surface this to explain
		why a command it expected is absent from Commands()."""
		target = self._forwardTarget()
		if target is not None:
			return target.Shadowed()
		return list(getattr(self, '_shadowed', []))

	# --- internals ---------------------------------------------------------

	# --- decorator protocol harvesting -------------------------------------
	# The contract is the ATTRIBUTE, not any particular decorator: a promoted
	# (uppercase) extension method carrying a `_fns_command` dict is a
	# command. The canonical decorator (pure metadata, no registry import,
	# safe at class-compile time regardless of load order) is:
	#
	#	def fns_command(fn=None, *, id=None, label=None, help='',
	#					params=None, args=None, kwargs=None):
	#		def mark(f):
	#			f._fns_command = {'id': id, 'label': label, 'help': help,
	#							  'params': params, 'args': args,
	#							  'kwargs': kwargs}
	#			return f
	#		return mark(fn) if callable(fn) else mark

	def _harvestDecorated(self, comp):
		"""Spec list from `_fns_command`-marked promoted methods across
		COMP's extensions. Metadata gaps fill from the function itself:
		label from the CamelCase name, help from the docstring's first
		line, params from the signature."""
		specs = []
		seen = set()
		for ext in comp.extensions:
			if ext is None:
				continue
			cls = type(ext)
			for name in dir(cls):
				if name.startswith('_') or not name[:1].isupper() or name in seen:
					continue
				fn = getattr(cls, name, None)
				meta = getattr(fn, '_fns_command', None)
				if not isinstance(meta, dict):
					continue
				seen.add(name)
				spec = {
					'method': name,
					'id': meta.get('id') or name.lower(),
					'label': meta.get('label') or self._labelFromName(name),
					'help': meta.get('help')
					or (inspect.getdoc(fn) or '').split('\n')[0].strip(),
				}
				params = meta.get('params')
				if params is None:
					params = self._paramsFromSignature(fn)
				if params:
					spec['params'] = params
				if meta.get('args'):
					spec['args'] = meta['args']
				if meta.get('kwargs'):
					spec['kwargs'] = meta['kwargs']
				if meta.get('hidden'):
					spec['hidden'] = True
				if meta.get('builtin'):
					spec['builtin'] = True
				if meta.get('state'):
					spec['state'] = meta['state']
				if meta.get('enabled'):
					spec['enabled'] = meta['enabled']
				if meta.get('surface'):
					spec['surface'] = meta['surface']
				if meta.get('capability'):
					spec['capability'] = meta['capability']
				if meta.get('context'):
					spec['context'] = meta['context']
				# Harvest never carried the 1.9.0 field, so a decorated command
				# could declare a canonical id and still never be arbitrated.
				if meta.get('canonical'):
					spec['canonical'] = meta['canonical']
				specs.append(spec)
		return specs

	@staticmethod
	def _labelFromName(name):
		"""'SetBpm' -> 'Set Bpm' — a readable fallback, not a beauty prize."""
		return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)

	@staticmethod
	def _paramsFromSignature(fn):
		"""Derive param declarations from a marked method's signature:
		type hints -> styles (typing.Literal -> menu), defaults ->
		defaults, no default -> required. Un-annotated params with no
		usable default stay 'str' — the registry's do-no-harm default."""
		try:
			sig = inspect.signature(fn)
		except (TypeError, ValueError):
			return []
		# Annotations may be STRINGS (PEP 563 / exec contexts) — resolve
		# them first, else every `ann is float` check silently misses and
		# styles degrade to default-value inference.
		try:
			hints = typing.get_type_hints(fn)
		except Exception:
			hints = {}
		_BY_NAME = {'int': int, 'float': float, 'bool': bool, 'str': str}
		out = []
		for pname, p in list(sig.parameters.items())[1:]:  # skip self
			if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
				continue
			spec = {'name': pname}
			ann = hints.get(pname)
			if ann is None:
				ann = p.annotation if p.annotation is not inspect.Parameter.empty else None
				if isinstance(ann, str):
					ann = _BY_NAME.get(ann.strip())
			origin = typing.get_origin(ann) if ann is not None else None
			if origin is typing.Literal:
				spec['style'] = 'menu'
				spec['menu'] = [str(v) for v in typing.get_args(ann)]
			elif ann is bool:
				spec['style'] = 'toggle'
			elif ann is int:
				spec['style'] = 'int'
			elif ann is float:
				spec['style'] = 'float'
			elif ann is str:
				spec['style'] = 'str'
			elif p.default is not inspect.Parameter.empty and p.default is not None:
				spec['style'] = {bool: 'toggle', int: 'int', float: 'float'}.get(
					type(p.default), 'str'
				)
			if p.default is inspect.Parameter.empty:
				spec['required'] = True
			elif p.default is not None:
				spec['default'] = p.default
			out.append(spec)
		return out

	# --- live state evaluation (query time) --------------------------------

	def _paramsForWire(self, comp, params):
		"""Wire copy of a command's param declarations with each `current`
		reference replaced by its evaluated value (or dropped on failure).
		Params without `current` pass through untouched."""
		if not any('current' in p for p in params):
			return params
		out = []
		for p in params:
			ref = p.get('current')
			if not ref:
				out.append(p)
				continue
			wp = {k: v for k, v in p.items() if k != 'current'}
			val = self._evalStateRef(comp, ref, cap=64)
			if val is not None:
				wp['current'] = val
			out.append(wp)
		return out

	# --- multiple instances (registry >= 1.11.0) ---------------------------

	_TOOL_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_\-.]{0,63}$')
	MAX_INSTANCE_CHARS = 32

	def _toolName(self, comp):
		"""The owner's public tool name: its promoted FnsToolName() when it
		returns a well-formed name, else the COMP name minus a leading FNS_.

		The hook exists for tools that live as several copies whose COMP
		names differ (`Scope1`, `Scope2`). Without it each copy is its own
		`tool#id` identity, so a favourite, override or preset set on one
		copy misses the others, and adding a copy orphans nothing but also
		inherits nothing. A malformed return falls back rather than failing
		the registration: the name is curation identity, never a gate."""
		try:
			fn = getattr(comp, 'FnsToolName', None)
			if callable(fn):
				name = str(fn() or '').strip()
				if self._TOOL_NAME_RE.match(name):
					return name
		except Exception:
			pass
		return _publicName(comp.name)

	def _evalInstance(self, comp):
		"""The owner's instance label from its promoted FnsInstance(), or None.

		Trimmed to MAX_INSTANCE_CHARS; empty, missing or failing hooks all
		yield None so the item simply carries no `instance` key -- a broken
		label never breaks the listing, same guard as `state`."""
		try:
			fn = getattr(comp, 'FnsInstance', None)
			if not callable(fn):
				return None
			val = fn()
			if val is None:
				return None
			val = str(val).strip()[:self.MAX_INSTANCE_CHARS]
			return val or None
		except Exception:
			return None

	# --- availability (registry >= 1.12.0) ---------------------------------
	# docs/CommandAvailability.md: a surface offers only what the project can
	# run. Owner-level conditions hide every command of the owner; `enabled`
	# hides one command. Nothing here unregisters.

	@staticmethod
	def _ownerUnavailable(comp, entry):
		"""The reason the owner cannot run right now, or None."""
		try:
			if getattr(comp, 'bypass', False):
				return f"{entry['tool']} is bypassed"
			o = comp
			while o is not None and o.path != '/':
				if not o.allowCooking:
					return f"{entry['tool']} has cooking off"
				o = o.parent()
		except Exception:
			return None
		return None

	def _isEnabled(self, comp, entry, spec) -> bool:
		"""A command's declared `enabled` reference, evaluated live. A
		reference that fails to evaluate counts as enabled and is logged once
		per owner: a broken reference must not make a working tool vanish."""
		ref = spec['enabled']
		try:
			if 'par' in ref:
				par = getattr(comp.par, ref['par'], None)
				if par is None:
					raise LookupError('no par %s' % ref['par'])
				return bool(par.eval())
			fn = getattr(comp, ref['method'], None)
			if not callable(fn):
				raise LookupError('no method %s' % ref['method'])
			return bool(fn())
		except Exception as e:
			logged = getattr(self, '_enabledWarned', None)
			if logged is None:
				logged = self._enabledWarned = set()
			if comp.path not in logged:
				logged.add(comp.path)
				debug(f"FNS_CommandRegistry: {entry['tool']} enabled reference failed ({e}); treated as enabled")
			return True

	def _evalStateRef(self, comp, ref, cap=16):
		"""Evaluate one state/current reference ({'par': name} or
		{'method': name}) against the live tool. Returns True/False for
		toggles and bool results, a trimmed string for everything else
		(floats via '%g' so 120.0 reads as 120), or None on ANY failure —
		a broken tool never breaks the listing."""
		try:
			if 'par' in ref:
				par = getattr(comp.par, ref['par'], None)
				if par is None:
					return None
				val = par.eval()
				if getattr(par, 'style', '') == 'Toggle':
					return bool(val)
			else:
				fn = getattr(comp, ref['method'], None)
				if not callable(fn):
					return None
				val = fn()
			if isinstance(val, bool):
				return val
			if isinstance(val, float):
				return format(val, 'g')[:cap]
			if val is None:
				return None
			return str(val)[:cap]
		except Exception:
			return None

	def _cleanStateRef(self, cid, what, ref):
		"""Normalize a state/current declaration to {'par': name} or
		{'method': name}. Existence is NOT checked here — owners may build
		pars late; the query-time guard covers it."""
		if isinstance(ref, str):
			name = ref.strip()
			if name.isidentifier():
				return {'par': name}
		elif isinstance(ref, dict):
			name = str(ref.get('method') or '').strip()
			if name.isidentifier():
				return {'method': name}
		raise ValueError(
			f"command {cid!r}: {what} must be a par name or {{'method': name}}"
		)

	def _resolveOwner(self, owner):
		comp = op(owner) if isinstance(owner, str) else owner
		if comp is None or not getattr(comp, 'valid', False):
			return None
		return comp

	def _cleanSpec(self, spec):
		if not isinstance(spec, dict):
			raise ValueError('command spec must be a dict')
		cid = str(spec.get('id') or '').strip()
		if not self._ID_RE.match(cid):
			raise ValueError(f'bad command id: {cid!r} (alnum/underscore/dash, <=48 chars)')
		label = str(spec.get('label') or '').strip()[:80]
		if not label:
			raise ValueError(f'command {cid!r} has no label')
		method = str(spec.get('method') or '').strip()
		if not method.isidentifier():
			raise ValueError(f'command {cid!r}: bad method name {method!r}')
		help_text = str(spec.get('help') or '').strip()[:200]
		# Tool-declared default visibility: hidden commands exist on the wire
		# but consumers don't surface them unless the user opts in. This is
		# metadata, not user preference — user overrides live consumer-side.
		hidden = bool(spec.get('hidden', False))
		# Built-in marker: the command is TD/system functionality rather than
		# a third-party tool's — consumers may present it in their native
		# command listing instead of the tools listing.
		builtin = bool(spec.get('builtin', False))
		args = spec.get('args')
		args = list(args) if isinstance(args, (list, tuple)) else []
		kwargs = spec.get('kwargs')
		kwargs = dict(kwargs) if isinstance(kwargs, dict) else {}
		params = spec.get('params')
		params = list(params) if isinstance(params, (list, tuple)) else []
		if len(params) > self.MAX_PARAMS_PER_COMMAND:
			raise ValueError(
				f'command {cid!r}: too many params (max {self.MAX_PARAMS_PER_COMMAND})'
			)
		clean_params = []
		seen_names = set()
		for p in params:
			cp = self._cleanParam(cid, p)
			if cp['name'] in seen_names:
				raise ValueError(f"command {cid!r}: duplicate param {cp['name']!r}")
			seen_names.add(cp['name'])
			clean_params.append(cp)
		json.dumps([args, kwargs, clean_params])  # must survive the wire
		clean = {
			'id': cid,
			'label': label,
			'help': help_text,
			'method': method,
			'args': args,
			'kwargs': kwargs,
			'params': clean_params,
			'hidden': hidden,
			'builtin': builtin,
		}
		# Live state reference (registry >= 1.6.0): evaluated fresh on every
		# Commands() build, so consumers can chip the current value. Must be
		# trivially cheap — a par read or a one-line getter.
		state = spec.get('state')
		if state:
			clean['state'] = self._cleanStateRef(cid, 'state', state)
		# Availability reference (registry >= 1.12.0): same shape as `state`;
		# a false value hides the command and Run refuses it.
		enabled = spec.get('enabled')
		if enabled:
			clean['enabled'] = self._cleanStateRef(cid, 'enabled', enabled)
		# Surface targeting + blessed-capability marker (registry >= 1.7.0).
		# Both optional; absent means today's exact behaviour (quick-launch
		# only, generic rendering).
		surface = self._cleanSurface(cid, spec.get('surface'))
		if surface:
			clean['surface'] = surface
		capability = spec.get('capability')
		if capability:
			capability = str(capability).strip().lower()
			if not self._CAPABILITY_RE.match(capability):
				raise ValueError(
					f'command {cid!r}: bad capability id {capability!r} '
					'(lowercase alnum/dot/underscore/dash, <=64 chars)'
				)
			clean['capability'] = capability
		# What the command acts on (registry >= 1.8.0). Absent means the
		# command needs nothing external -- exactly today's behaviour.
		context = self._cleanContext(cid, spec.get('context'))
		if context:
			clean['context'] = context
		# Cross-package identity (registry >= 1.9.0). OPT-IN, never derived
		# from `id`: `toggleactive` appears 12 times across 12 DIFFERENT
		# tools and `path#id` already separates them, so deriving identity
		# from the id would collapse twelve working commands into one.
		# Absent means the command is never arbitrated -- today's behaviour.
		canonical = spec.get('canonical')
		if canonical:
			canonical = str(canonical).strip().lower()
			if not self._CANONICAL_RE.match(canonical):
				raise ValueError(
					f'command {cid!r}: bad canonical id {canonical!r} '
					'(lowercase alnum/dot/underscore/dash, <=64 chars)'
				)
			clean['canonical'] = canonical
		return clean

	def _cleanContext(self, cid, value):
		"""Normalize a context declaration to a deduped token list.

		Accepts a single token or a list; None/empty stays [] (= needs
		nothing). A list means ANY of them will do and the consumer takes
		the first that resolves. Shape-only validation, same reasoning as
		surface: CONTEXT_TOKENS is the blessed vocabulary, not a whitelist,
		so a token TD grows later needs no registry change."""
		if not value:
			return []
		items = [value] if isinstance(value, str) else list(value) \
			if isinstance(value, (list, tuple)) else None
		if items is None:
			raise ValueError(
				f'command {cid!r}: context must be a token or list of tokens'
			)
		out = []
		for item in items[:self.MAX_CONTEXTS_PER_COMMAND]:
			token = str(item).strip().lower()
			if not self._CONTEXT_RE.match(token):
				raise ValueError(
					f'command {cid!r}: bad context token {token!r} '
					'(lowercase alnum/underscore/dash, <=24 chars)'
				)
			if token not in out:
				out.append(token)
		return out

	def _cleanSurface(self, cid, value):
		"""Normalize a surface declaration to a deduped token list.

		Accepts a single token or a list; None/empty stays [] (= the
		default surface, quick-launch). Tokens are validated for shape
		only, never against a known-value list — consumers ignore surfaces
		they don't serve, which is what keeps new surfaces additive."""
		if not value:
			return []
		items = [value] if isinstance(value, str) else list(value) \
			if isinstance(value, (list, tuple)) else None
		if items is None:
			raise ValueError(
				f'command {cid!r}: surface must be a token or list of tokens'
			)
		out = []
		for item in items[:self.MAX_SURFACES_PER_COMMAND]:
			token = str(item).strip().lower()
			if not self._SURFACE_RE.match(token):
				raise ValueError(
					f'command {cid!r}: bad surface token {token!r} '
					'(lowercase alnum/underscore/dash, <=24 chars)'
				)
			if token not in out:
				out.append(token)
		return out

	def _cleanParam(self, cid, p):
		"""Validate one user-suppliable parameter declaration."""
		if not isinstance(p, dict):
			raise ValueError(f'command {cid!r}: param spec must be a dict')
		name = str(p.get('name') or '').strip()
		if not name.isidentifier() or name.startswith('_'):
			raise ValueError(f'command {cid!r}: bad param name {name!r}')
		style = str(p.get('style') or 'str').strip().lower()
		if style not in self.PARAM_STYLES:
			raise ValueError(
				f'command {cid!r}: param {name!r} style must be one of {self.PARAM_STYLES}'
			)
		menu = p.get('menu')
		menu = [str(m).strip()[:40] for m in menu][:16] if isinstance(menu, (list, tuple)) else []
		if style == 'menu' and not menu:
			raise ValueError(f'command {cid!r}: menu param {name!r} needs menu entries')
		out = {
			'name': name,
			'label': str(p.get('label') or name).strip()[:40],
			'style': style,
			'required': bool(p.get('required', False)),
			'help': str(p.get('help') or '').strip()[:120],
		}
		if menu:
			out['menu'] = menu
		default = p.get('default')
		if default is not None:
			# Stored as coerced so Run's fill-in needs no special casing.
			out['default'] = self._coerceParamValue(out, default)
		# Live prefill reference (registry >= 1.6.0): evaluated at query
		# time; consumers seed the prompt with it instead of the default.
		cur = p.get('current')
		if cur:
			out['current'] = self._cleanStateRef(cid, f'param {name!r} current', cur)
		return out

	def _coerceParamValue(self, param, value):
		"""Coerce/validate one incoming value by the param's declared style.
		Raises ValueError with a caller-legible message."""
		style = param['style']
		name = param['name']
		if style == 'int':
			try:
				return int(str(value).strip())
			except Exception:
				raise ValueError(f'{name}: not an integer: {value!r}')
		if style == 'float':
			try:
				return float(str(value).strip())
			except Exception:
				raise ValueError(f'{name}: not a number: {value!r}')
		if style == 'toggle':
			s = str(value).strip().lower()
			if s in ('1', 'true', 'on', 'yes'):
				return True
			if s in ('0', 'false', 'off', 'no'):
				return False
			raise ValueError(f'{name}: not a toggle value: {value!r} (use on/off)')
		if style == 'menu':
			s = str(value).strip()
			if s not in param.get('menu', []):
				raise ValueError(
					f"{name}: {s!r} is not one of {param.get('menu', [])}"
				)
			return s
		return str(value)

	def _bump(self):
		self._rev += 1
		self._refreshSurface()

	def _setStatus(self, msg):
		try:
			if hasattr(self.ownerComp.par, 'Status'):
				self.ownerComp.par.Status.val = str(msg)[:120]
		except Exception:
			pass

	def _refreshSurface(self):
		"""Mirror the registry into the commands table + Status readout."""
		table = self.ownerComp.op('commands')
		if table is not None:
			table.clear()
			table.appendRow(['tool', 'id', 'label', 'method', 'path'])
			for path in sorted(self._registry):
				entry = self._registry[path]
				for c in entry['commands']:
					table.appendRow([entry['tool'], c['id'], c['label'], c['method'], path])
		n_tools = len(self._registry)
		n_cmds = sum(len(e['commands']) for e in self._registry.values())
		self._setStatus(f'{n_cmds} commands from {n_tools} tools (rev {self._rev})')
