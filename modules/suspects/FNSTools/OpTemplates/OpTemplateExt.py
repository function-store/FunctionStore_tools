
'''Info Header Start
Name : OpTemplateExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
from functools import cached_property
from collections import defaultdict
import itertools
import os
import re

# --- the toolkit's folder in the user palette ------------------------------
# <user palette>/FNSTools (docs/PaletteFolderContract.md). Until 2026-09-18
# this was FNStools_ext; a legacy folder is renamed into place the first
# time any reader looks. This function is carried verbatim by every FNS
# extension that reads the folder: they ship as separate toxes and cannot
# share a module, and whichever reader gets there first must be able to
# migrate on its own. Master copy: FNS_Updater/ExtUpdater.py.
PALETTE_DIR = 'FNSTools'
LEGACY_PALETTE_DIR = 'FNStools_ext'


def _fnsPaletteRoot():
	"""'<user palette>/FNSTools', migrating a legacy FNStools_ext folder into
	place on first sight; '' when this install has no user palette folder."""
	try:
		base = str(app.userPaletteFolder).replace('\\', '/').rstrip('/')
	except Exception:
		return ''
	if not base:
		return ''
	new = '%s/%s' % (base, PALETTE_DIR)
	legacy = None
	try:
		for fn in os.listdir(base):
			if fn.lower() == LEGACY_PALETTE_DIR.lower() and os.path.isdir('%s/%s' % (base, fn)):
				legacy = '%s/%s' % (base, fn)
				break
	except Exception:
		pass
	if legacy is None:
		return new
	if not os.path.isdir(new):
		try:
			os.rename(legacy, new)
			return new
		except OSError as e:
			# a file held open, most likely; this session keeps using the
			# old folder and the next start tries again
			debug('FNS: could not rename %s to %s (%s)' % (legacy, new, e))
			return legacy
	# both exist (a race, or an older launcher recreated the legacy
	# folder): whatever the legacy folder holds that the new one lacks
	# moves over, and the legacy folder goes once it is empty
	# entry by entry, each on its own: a folder something still watches
	# (TDFam's Folder DAT on the old family tree) refuses to move, and that
	# must not keep the store or the config from moving. A folder both
	# sides hold is merged the same way one level down, because a reader
	# that seeds its file when it is missing (OpTemplates) can have made
	# the new folder before this ran. A FILE both sides hold stays as the
	# new side has it, and the legacy copy is kept aside under
	# FNSTools/legacy_<old name>/ at its old relative path, never deleted:
	# the new side's file is usually the later state, but it can be a seed
	# (OpTemplates writes its default library when its file is missing)
	# while the legacy one is the user's work. OpTemplates looks there
	# before seeding again. Deleting it lost a user's library (2026-09-18).
	left = []

	def merge(src_dir, dst_dir):
		for fn in os.listdir(src_dir):
			src, dst = '%s/%s' % (src_dir, fn), '%s/%s' % (dst_dir, fn)
			try:
				if not os.path.exists(dst):
					os.rename(src, dst)
				elif os.path.isdir(src) and os.path.isdir(dst):
					merge(src, dst)
					if not os.listdir(src):
						os.rmdir(src)
				elif os.path.isfile(src) and os.path.isfile(dst):
					rel = os.path.relpath(src, legacy).replace('\\', '/')
					keep = '%s/legacy_%s/%s' % (new, LEGACY_PALETTE_DIR, rel)
					if os.path.exists(keep):
						os.remove(src)
					else:
						os.makedirs(os.path.dirname(keep), exist_ok=True)
						os.rename(src, keep)
			except OSError as e:
				left.append('%s (%s)' % (fn, e))

	try:
		merge(legacy, new)
		if not os.listdir(legacy):
			os.rmdir(legacy)
	except Exception as e:
		left.append(str(e))
	if left:
		debug('FNS: legacy palette folder %s not fully merged: %s' % (legacy, '; '.join(left)))
	return new

import TDFunctions
import shutil

# --- finding a library the user already has --------------------------------
# The global library is one file, <palette>/FNSTools/OpTemplates/<base>.tox.
# Older versions could leave the user's real set under another name: the
# `_2023` copy TouchDesigner 2023 saved to, an `OPTemplates<N>.tox` from the
# old "Create New" choice, or a copy the palette migration kept aside in
# legacy_<old folder name>/ when both folders held the file. Seeding the shipped
# defaults over any of those read as "my templates are gone" (field report
# 2026-09-25). Pure file logic, no TD, so tests/test_optemplates_library.py
# runs it on a scratch folder.
LIBRARY_FILE_RE = re.compile(r'^optemplates\d+(_2023)?\.tox$', re.I)
# The global library's folder under <palette>/FNSTools. Libraryfolder
# overrides it: the development project names `OpTemplates_dev` so the set it
# curates (which is what ships as the seed) stops sharing a file with the
# templates saved while merely USING the toolkit. Empty is the default and the
# only value an export may carry (docs/ConfigScope.md).
_DEFAULT_LIBRARY_SUBFOLDER = 'OpTemplates'
CHECKED_MARKER = '.library_checked'


def seedMarker(path):
	"""The sidecar that says `path` holds the shipped defaults, not user work."""
	return os.path.splitext(path)[0] + '.seeded'


def libraryCandidates(folder, legacy_folder):
	"""Library files a user saved, newest first: OPTemplates<N>.tox and the
	_2023 copies in the folder and in the migration's keep-aside folder.
	Files marked as seeds are left out."""
	found = []
	for d in (folder, legacy_folder):
		try:
			names = os.listdir(d)
		except OSError:
			continue
		for fn in names:
			f = '%s/%s' % (d, fn)
			if LIBRARY_FILE_RE.match(fn) and os.path.isfile(f) and not os.path.exists(seedMarker(f)):
				found.append(f)
	found.sort(key=lambda f: os.path.getmtime(f), reverse=True)
	return found


def adoptExistingLibrary(path, folder, legacy_folder):
	"""Make `path` hold the user's newest library before anything seeds it.

	Runs when `path` is missing, when it holds a seed, and once per machine
	(the checked marker) so a library saved under another name more
	recently than `path` is picked up after an upgrade. Never deletes: a
	file it replaces is kept beside it as <name>.before-adopt.tox. Returns
	the adopted source, or None."""
	checked = os.path.exists('%s/%s' % (folder, CHECKED_MARKER))
	seeded = os.path.exists(path) and os.path.exists(seedMarker(path))
	adopted = None
	if not os.path.exists(path) or seeded or not checked:
		best = next(iter(libraryCandidates(folder, legacy_folder)), None)
		same = best is not None and os.path.exists(path) and os.path.samefile(best, path)
		if best is not None and not same:
			os.makedirs(folder, exist_ok=True)
			if os.path.exists(path):
				shutil.copy2(path, os.path.splitext(path)[0] + '.before-adopt.tox')
			shutil.copy2(best, path)
			if os.path.exists(seedMarker(path)):
				os.remove(seedMarker(path))
			adopted = best
	if os.path.isdir(folder) and not checked:
		io_path = '%s/%s' % (folder, CHECKED_MARKER)
		with open(io_path, 'w') as f:
			f.write('checked for existing template libraries\n')
	return adopted


def clearSeedMark(path):
	"""A save makes the file the user's: drop the seed marker."""
	try:
		if os.path.exists(seedMarker(path)):
			os.remove(seedMarker(path))
	except OSError:
		pass

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class OpTemplateExt:

	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.op_families = [fam.__name__ for fam in OP.__subclasses__()]
		self.pop_tab = self.ownerComp.op('table_pop_templates')
		self.pendingOrigOP = None
		self.pendingTemplates = []
		self.all_optypes = self.getAllOptypes()
		self.defaultTemplates = op('OPTemplates1')
		self.inputOpTypes = ['inTOP','inCHOP','inSOP','inMAT','inDAT','inPOP']
		self.outputOpTypes = ['outTOP','outCHOP','outSOP','outMAT','outDAT','outPOP']
		self.opFamilyConvertTypes = ['choptoTOP','dattoCHOP','toptoCHOP','soptoCHOP',
			       					'choptoDAT','soptoDAT','chopexecDAT',
									'choptoSOP','trailSOP','toptoPOP','poptoTOP','choptoPOP',
									'soptoPOP','dattoPOP','poptoCHOP','poptoDAT','poptoSOP']
		fnsLog('OpTemplates: init')
		self._ensurePars()
		self._adoptAdvancedBase()
		# The scope is a persisted par: apply it after ConfigRegistry has
		# restored this tool's pars (same window as the Keys carry-over).
		try:
			run("op.FNS_OPTEMPLATES.ext.OpTemplateExt.applyScope()",
				delayFrames=60, delayRef=op.TDResources)
		except Exception:
			pass
		# The alternatives shortcut lives on FNS_OpMenuRegistry now. Deferred so
		# ConfigRegistry has restored this tool's pars first: a user's customised
		# Keys is what has to reach the registry. Resolved by shortcut at call
		# time, never a cached self.
		try:
			run("op.FNS_OPTEMPLATES.ext.OpTemplateExt.adoptShortcut()",
				delayFrames=90, delayRef=op.TDResources)
		except Exception:
			pass

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def getAllOptypes(self):
		all_optypes = []
		bigfams = [OP, COMP]
		for bigfam in bigfams:
			for sub in bigfam.__subclasses__():
				for _optype in sub.__subclasses__():
					all_optypes.append(_optype.__name__)
	
		return all_optypes
	
	# ---- library scope (docs/OpTemplatesLibraryScope.md) ------------------
	# One active library. Global: the tool's base loaded from the palette file.
	# Project: a COMP at the network root, outside the toolkit, found by tag.
	LIBRARY_TAG = 'FNS_OpTemplatesLibrary'
	PROJECT_LIBRARY_NAME = 'OpTemplatesLibrary'
	SCOPES = ('follow', 'global', 'project')

	def _ensurePars(self):
		"""Get-or-create the scope pars; never destroys a user's value."""
		page = next((pg for pg in self.ownerComp.customPages if pg.name == 'Custom'), None)
		if page is None:
			page = self.ownerComp.appendCustomPage('Custom')
		p = self.ownerComp.par['Libraryscope']
		if p is None:
			p = page.appendMenu('Libraryscope', label='Library Scope')[0]
			p.menuNames = list(self.SCOPES)
			p.menuLabels = ['Follow config scope', 'Global (user palette)', 'Project (this .toe)']
			p.default = 'follow'
			p.val = 'follow'
			tp = self.ownerComp.par['Templates']
			if tp is not None:
				p.order = tp.order - 0.5
		p.help = ('Where the active templates library lives. Global: one .tox in your '
				  'user palette folder, shared by every project on this machine. '
				  'Project: a component at the network root outside FNSTools, saved '
				  'with this .toe and kept across toolkit updates. Follow: whatever the '
				  "toolkit's Config Scope says. A missing library is created from the "
				  'set that is loaded now; the shipped templates are only the seed.')
		p = self.ownerComp.par['Pushtoglobal']
		if p is None:
			p = page.appendPulse('Pushtoglobal', label='Push To Global')[0]
			sp = self.ownerComp.par['Savetemplates']
			if sp is not None:
				p.order = sp.order + 0.5
		p.help = ('Write the active library to the global palette file, so a set built '
				  'in this project becomes the one every project on this machine loads. '
				  'Asks before overwriting an existing file.')
		p = self.ownerComp.par['Libraryfolder']
		if p is None:
			p = page.appendStr('Libraryfolder', label='Library Folder')[0]
			p.default = ''
			p.val = ''
			sp = self.ownerComp.par['Libraryscope']
			if sp is not None:
				p.order = sp.order + 0.25
		p.help = ('Folder under <user palette>/FNSTools that holds the global '
				  'library. Empty uses OpTemplates, which is right for everyone '
				  'except a development project that must keep its curated set '
				  'apart from the one it uses day to day. Global scope only; '
				  'cleared on export, so it never ships.')
		tp = self.ownerComp.par['Templates']
		if tp is not None:
			tp.readOnly = True
			tp.help = ('The library the scope resolved to. Read-only: change Library '
					   'Scope instead.')

	def _projectRoot(self):
		fns = getattr(op, 'FNS', None)
		return fns.parent() if fns is not None else op('/')

	def _configScope(self):
		fns = getattr(op, 'FNS', None)
		cs = fns.par['Configscope'] if fns is not None else None
		v = str(cs.eval()).strip() if cs is not None else ''
		return v if v in ('global', 'project') else 'global'

	@property
	def scope(self):
		"""'global' or 'project': the Libraryscope par with 'follow' resolved
		against the toolkit root's Config Scope (a tool without the root
		keeps the historical default, the palette file)."""
		p = self.ownerComp.par['Libraryscope']
		v = str(p.eval()).strip() if p is not None else 'follow'
		if v not in ('global', 'project'):
			v = self._configScope()
		return v

	def projectLibrary(self):
		"""The tagged project library at the network root, or None."""
		root = self._projectRoot()
		for c in root.findChildren(tags=[self.LIBRARY_TAG], maxDepth=1):
			if c.valid and c.isCOMP:
				return c
		return None

	def ensureProjectLibrary(self):
		"""The project library, created from the loaded set when absent.

		The copy is severed from the palette file (a copied base inherits the
		externaltox binding, and boot would reload the wrong content into
		it), placed beside the toolkit container, cooking off like every
		library base."""
		lib = self.projectLibrary()
		if lib is not None:
			return lib
		root = self._projectRoot()
		seed = self.defaultTemplates
		lib = root.copy(seed, name=self.PROJECT_LIBRARY_NAME)
		lib.par.enableexternaltox = False
		lib.par.externaltox = ''
		for tag in ('pi_suspect', 'FNS_externalized'):
			if tag in lib.tags:
				lib.tags.remove(tag)
		lib.tags.add(self.LIBRARY_TAG)
		lib.allowCooking = False
		fns = getattr(op, 'FNS', None)
		if fns is not None and fns.parent() is root:
			step = ((int(fns.nodeWidth) + 200 + 199) // 200) * 200
			lib.nodeX, lib.nodeY = int(fns.nodeX) + step, int(fns.nodeY)
		lib.comment = 'OpTemplates project library: saved with this .toe, kept across toolkit updates. Found by tag, not by path.'
		fnsLog(f'OpTemplates: created the project library {lib.path} from {seed.path}')
		return lib

	def _adoptAdvancedBase(self):
		"""Migration: a base the retired Advanced mode pointed at, outside the
		tool, becomes the project library by tag."""
		tp = self.ownerComp.par['Templates']
		comp = tp.eval() if tp is not None else None
		if comp is None or not comp.valid:
			return
		inside = comp.path == self.ownerComp.path or comp.path.startswith(self.ownerComp.path + '/')
		if not inside and self.LIBRARY_TAG not in comp.tags and self.projectLibrary() is None:
			comp.tags.add(self.LIBRARY_TAG)
			fnsLog(f'OpTemplates: adopted {comp.path} as the project library')

	@property
	def templatesCOMP(self):
		if self.scope == 'project':
			return self.projectLibrary() or self.ensureProjectLibrary()
		return self.defaultTemplates

	# Interactive flip project -> global, with both a project library and a
	# palette file present: the same three-way choice the config scope offers.
	FLIP_PUSH, FLIP_ADOPT, FLIP_STAY = 0, 1, 2

	def _confirmGlobalFlip(self, lib, path):
		"""Ask what a project -> global flip means for the project set.
		Separate so tests can stand in for the modal."""
		return ui.messageBox(
			'Templates: switch to global',
			f"Your project library '{lib.name}' stays in this project, but the global "
			f"set in '{os.path.basename(path)}' becomes the active one.\n\n"
			'Push to Global overwrites the global file with the project set first. '
			'Adopt Global loads the global set as it is. Stay Project keeps the scope.',
			buttons=['Push to Global', 'Adopt Global', 'Stay Project'])

	def applyScope(self, prompt=False):
		"""Make the active library match the scope: wire or unwire the palette
		file on the tool's base, mirror the result into Templates, refresh.

		A flip never overwrites anything by itself: a missing global file is
		created from what is loaded now (the project library when one is
		active, else the tool's base); a missing project library is created
		from the tool's base on first use. `prompt` is the interactive path
		(the parexec behind the menu): a project -> global flip with both a
		project library and a global file present asks Push / Adopt / Stay,
		as the config-scope flip does. Scripts and boot pass nothing and
		never see a modal."""
		scope = self.scope
		base = self.defaultTemplates
		ext_par = base.par.externaltox
		prev = getattr(self, '_appliedScope', None)
		if scope == 'global':
			path = self.ExternalPath
			lib = self.projectLibrary()
			if (prompt and prev == 'project' and lib is not None
					and os.path.exists(path)):
				choice = self._confirmGlobalFlip(lib, path)
				if choice == self.FLIP_STAY:
					self.ownerComp.par.Libraryscope = 'project'
					fnsLog('OpTemplates: flip to global cancelled, staying project')
					return lib
				if choice == self.FLIP_PUSH:
					lib.save(path, createFolders=True)
					clearSeedMark(path)
					fnsLog(f'OpTemplates: pushed {lib.path} to {path} on the flip')
			adopted = None
			try:
				# The keep-aside folder holds the USER's pre-migration set. A
				# redirected folder (the dev project's) must never adopt it:
				# adoption copies the NEWEST candidate over the target, which
				# would replace the dev library with an old user one.
				legacy_dir = ('' if self._libraryFolderOverridden() else
							  '%s/legacy_%s/OpTemplates' % (os.path.dirname(self.extFolder), LEGACY_PALETTE_DIR))
				adopted = adoptExistingLibrary(path, self.extFolder, legacy_dir)
			except Exception as e:
				fnsLog(f'OpTemplates: looking for an existing library failed: {e}', level='WARNING')
			if adopted:
				fnsLog(f'OpTemplates: adopted your library {adopted} as {path}')
			if not os.path.exists(path):
				seed = lib or base
				seed.save(path, createFolders=True)
				if seed is base:
					# the shipped set, not user work: a later start may still
					# replace it with a library found under another name
					with open(seedMarker(path), 'w') as f:
						f.write('seeded from the shipped templates\n')
				fnsLog(f'OpTemplates: created the global library {path} from {seed.path}')
			wired = (base.par.enableexternaltox.eval() and ext_par.mode == ParMode.EXPRESSION
					 and ext_par.expr == self.ExternalPathExpr())
			if not wired or adopted or (prompt and prev == 'project'):
				self.externalExprUpdate(ext_par, True, self.ExternalPathExpr())
				base.par.enableexternaltox = True
				base.par.reinitnet.pulse()
			active = base
		else:
			if base.par.enableexternaltox.eval() or ext_par.eval():
				self.externalExprUpdate(ext_par, False)
				base.par.enableexternaltox = False
			active = self.ensureProjectLibrary()
		tp = self.ownerComp.par['Templates']
		if tp is not None and tp.eval() is not active:
			tp.readOnly = False
			tp.val = active.path
			tp.readOnly = True
		self._appliedScope = scope
		fnsLog(f'OpTemplates: library scope {scope} -> {active.path}')
		run("parent.OpTemplate.RefreshCachedTemplates()", fromOP=self.ownerComp.op('OpTemplateExt'), endFrame=True)
		return active

	def PushToGlobal(self):
		"""Write the active library to the palette file (asks before an
		overwrite). User-initiated only: it prompts."""
		path = self.ExternalPath
		lib = self.templatesCOMP
		if os.path.exists(path):
			if ui.messageBox('Push to global',
							 f"'{os.path.basename(path)}' already exists in your palette. Overwrite it with {lib.name}?",
							 buttons=['Overwrite', 'Cancel']) != 0:
				return False
		lib.save(path, createFolders=True)
		clearSeedMark(path)
		fnsLog(f'OpTemplates: pushed {lib.path} to {path}')
		if self.scope == 'global':
			self.defaultTemplates.par.reinitnet.pulse()
			run("parent.OpTemplate.RefreshCachedTemplates()", fromOP=self.ownerComp.op('OpTemplateExt'), endFrame=True)
		return True

	KEYS_MIRROR_EXPR = ("op.FNS_OPMENUREGISTRY.par.Shortcutalternatives.eval() "
						"if hasattr(op, 'FNS_OPMENUREGISTRY') and op.FNS_OPMENUREGISTRY.par['Shortcutalternatives'] is not None "
						"else ('alt ctrl' if app.osName == 'Windows' else 'cmd ctrl')")

	def adoptShortcut(self):
		"""Keys used to be the gate; the registry's Shortcutalternatives is.

		A user's customised Keys (a CONSTANT restored by ConfigRegistry) is
		carried into the registry ONCE, while the registry is still at its
		default, so their shortcut keeps working after the move. Then Keys
		becomes a read-only mirror of the registry's par: one setting, shown
		in both places, edited in one."""
		reg = getattr(op, 'FNS_OPMENUREGISTRY', None)
		keys = self.ownerComp.par['Keys']
		if keys is None:
			return
		target = reg.par['Shortcutalternatives'] if reg is not None else None
		if target is not None and keys.mode == ParMode.CONSTANT:
			mine = str(keys.val).strip()
			if mine and mine != str(target.eval()).strip() and str(target.eval()).strip() == str(target.default).strip():
				target.val = mine
				fnsLog(f'OpTemplates: carried the Keys shortcut {mine!r} onto FNS_OpMenuRegistry')
		if keys.expr != self.KEYS_MIRROR_EXPR or keys.mode != ParMode.EXPRESSION:
			keys.expr = self.KEYS_MIRROR_EXPR
			keys.mode = ParMode.EXPRESSION
		keys.help = ('Mirrors the Alternatives Shortcut on FNS_OpMenuRegistry, which is '
					 'where the alternatives are offered from now. Change it there.')
		keys.readOnly = True   # a mirror: the hotkey manager lists the registry's par, not this

	@property
	def hotkey(self):
		return bool(self.ownerComp.op('null_hk')[0])
	
	def find_keywords_in_input(self, keywords, input):
		for k in keywords:
			if k in input:
				return k
	

	@cached_property
	def Templates(self) -> dict[str, OP]:
		# Templates can be
		templates = self.templatesCOMP
		
		all_ops = list(itertools.chain.from_iterable(_comp.ops('*') for _comp in templates.ops('*')))

		_ops = list(filter(lambda _op: not _op.inputs and _op.family in self.op_families and not _op.dock, all_ops))
		# for COMPs need to have the OP type name in their name
		# we add the name to the list and use this rule later
		types_ops = defaultdict(list)
		for _op in _ops:
			types_ops[_op.parent().name].append(_op)

		return types_ops
	
	def log(self, smth):
		fnsLog('OpTemplates:', smth)
	

	def OnNewOp(self, _op: OP):
		"""Kept for callers; the engine lives in FNS_OpMenuRegistry now.

		OpTemplates publishes its library through onAlternatives() and the
		registry's global watches for new operators, holds the modifier gate
		(its Shortcutalternatives par) and places. Forwarding here would fire
		a second placement for the same keypress, so this is a no-op with a
		name. See docs/OpAlternatives.md."""
		return

	def PlaceTemplate(self, orig_op=None, template_ops=None):
		"""Place a template through the registry (kept for the popMenu
		callbacks and any external caller)."""
		reg = getattr(op, 'FNS_OPMENUREGISTRY', None)
		if reg is None or not orig_op or not template_ops:
			return False
		return reg.PlaceAlternative(orig_op, template_ops[0])


##################### BULKY GOODS #####################
	def placeOPchain(self, orig_op, template_ops):
		'''
		Handles single operators, operator chains, docked operators, as well as inserting between operators,
		and restoring relative positions --- all at the same time
		'''

		def index_connections(orig_op, op_attr, conn_attr):
			'''
			`index` attribute of OP.outputs[0].inputConnectors[0].connections seems incorrect?
			This method builds a structure of OP:[indices] as in input/output connections for all slots (indexed) of all original output/input ops.

			op_attr in [inputs, outputs]
			connn_attr in [outputConnectors, inputConnectors]
			'''
			conns_indexed = defaultdict(list)
			for inOp in set(getattr(orig_op, op_attr)):
				for idx, _connector in enumerate(getattr(inOp, conn_attr)):
					for _connection in _connector.connections:
						if _connection and _connection.owner is orig_op:
							conns_indexed[inOp].append(idx)
			return conns_indexed
		
		def restore_connections(conns_indexed, connector_attr, new_op):
			'''restore original connections before replacing the template with one or more ops/comps
			connector_attr == inputConnectors /// outputConnectors'''
			to_connect = new_op
			if conns_indexed:
				for op, indices in conns_indexed.items():
					for connector_idx in indices:
						# this is gonna look weird, but in case of COMPS we are not simply connecting to an OP but a connector
						if new_op.family == 'COMP':
							invert_conn_attr = 'outputConnectors' if connector_attr == 'inputConnectors' else 'inputConnectors'
							to_connect = getattr(new_op, invert_conn_attr)[0]
							if not to_connect:
								return
							
						getattr(op, connector_attr)[connector_idx].connect(to_connect)
							
		def bfs(op):
			'''breadth first search'''
			from collections import deque
			visited = set([op])
			queue = deque([op])
			result = []
			while queue:
				op = queue.popleft()
				if op:
					result.append(op)
					for output in op.outputs:
						if output not in visited:
							visited.add(output)
							queue.append(output)
			return result
		
		def get_new_root(_parent, orig_type):
			new_root_op = _parent.findChildren(tags=['TEMPLATE_ROOT'], depth=1) # TODO: adding `type=orig_type` to the search breaks 
																				#SystemError: <built-in method findChildren of td.baseCOMP object at 0x0000021F5322BF00> returned a result with an error set 
			new_root_op = sorted(new_root_op, key=lambda _op: _op.OPType == orig_type) # prioritize this attribute
			if new_root_op:
				new_root_op = new_root_op[0]
				return new_root_op

		def new_ops_bfs_sorted(_parent, orig_type):
			new_root_op = get_new_root(_parent, orig_type)
			new_ops = bfs(new_root_op)
			return new_ops

		def get_famconvert(orig_op):
			if orig_op.OPType not in self.opFamilyConvertTypes:
				return None
			from_type = next((sub.lower() for sub in self.op_families if sub.lower() in orig_op.OPType), None)

			if from_type:
				if hasattr(orig_op.par, from_type):
					return (from_type, getattr(orig_op.par, from_type).val)
			return 
			
		def set_famconvert(new_op, orig_famconvert):
			if hasattr(new_op.par, orig_famconvert[0]):
				setattr(new_op.par, orig_famconvert[0], orig_famconvert[1])

		# save all relevant info before destroying
		template_op = template_ops[0]
		_parent = orig_op.parent()
		op_pos = (orig_op.nodeX, orig_op.nodeY)
		orig_type = orig_op.OPType
		orig_famconvert = get_famconvert(orig_op)

		# Build a structure of OP:[indices] 
		# meaning input/output connections (OPs) for all in/out slots (indexed) of all original output/input ops.
		in_conns_indexed = index_connections(orig_op, 'inputs', 'outputConnectors')
		out_conns_indexed = index_connections(orig_op, 'outputs', 'inputConnectors')

		# bye-bye
		orig_op.destroy()
  
		ui.undo.startBlock(f'Replacing {orig_op.path} with template!')
		
		to_clean = []
		if template_op.OPType == 'baseCOMP':
			self.primeNewCOMPTemplate(template_op) # making sure
			ops_to_copy = template_ops[0].findChildren(depth=1)

			if template_op.inputConnectors and (_roots := template_op.inputConnectors[0].inOP.outputs):
				ops_to_copy.remove(template_op.inputConnectors[0].inOP)
				for _op in _roots:
					_op.tags.add('TEMPLATE_IN')
					_op.tags.add('TEMPLATE_ROOT')
					to_clean.append(_op)
			else:
				_root = template_op.findChildren(key=lambda _op: _op.OPType == orig_type and not _op.inputs)

				if _root:
					for _r in _root:
						to_clean.append(_r)
					_root = _root[0]
				else:
					_root = ops_to_copy[0]
					for _r in ops_to_copy:
						to_clean.append(_r)
				_root.tags.add('TEMPLATE_ROOT')
			
			if template_op.outputConnectors and (_outs := template_op.outputConnectors[0].outOP.inputs):
				_outs[0].tags.add('TEMPLATE_OUT')			
				for _out in _outs:
					to_clean.append(_out)
				ops_to_copy.remove(template_op.outputConnectors[0].outOP)
			else:
				to_clean.append(_root)
		else:
			# we have to tag something as TEMPLATE_ROOT from operators to copy
			# op-chain case
			template_op.tags.add('TEMPLATE_ROOT')
			to_clean.append(template_op)
			ops_to_copy = bfs(template_op)
			
			if orig_famconvert:
				set_famconvert(template_op, orig_famconvert)
		
		for _op in ops_to_copy:
			_op.tags.add('TEMPLATE_COPY')
			to_clean.append(_op)

		# wish I found these methods earlier
		ui.copyOPs(ops_to_copy)
		ui.pasteOPs(_parent, x=op_pos[0], y=op_pos[1]) # wish this returned the pasted OP references
		
		for new_op in _parent.findChildren(tags=['TEMPLATE_COPY'], depth=1):
			new_op.bypass = False
			new_op.allowCooking = True
			new_op.tags.remove('TEMPLATE_COPY')

		# now we need to reconnect the ins and outs if any... gonna be a bit messy :)

		# below is only relevant when chaining OPs
		# check if we had inOPs, easy case
		if new_in_ops := _parent.findChildren(tags=['TEMPLATE_IN'], depth=1):
			for _op in new_in_ops:
				restore_connections(in_conns_indexed, 'outputConnectors', _op)
				_op.tags.remove('TEMPLATE_IN')
		else:
			# if we didn't have any inOPs we use our guess tagged as TEMPLATE_ROOT for the input, and finding the output
			# first in list should be the reference op
			_inOP = get_new_root(_parent, orig_type)
			
			to_clean.append(_inOP)
			restore_connections(in_conns_indexed, 'outputConnectors', _inOP)
		
		if new_out_ops := _parent.findChildren(tags=['TEMPLATE_OUT'], depth=1):
			_outOP = new_out_ops[0]
			for _op in new_out_ops:
				_op.tags.remove('TEMPLATE_OUT')
		else:
			# this is our best bet what the last op in the chain is
			new_ops = new_ops_bfs_sorted(_parent, orig_type)
			if new_ops:
				_outOP = new_ops[-1]
			else:
				_outOP = None

		if _outOP:
			if 'TEMPLATE_ROOT' in _outOP.tags:
				_outOP.tags.remove('TEMPLATE_ROOT')
			restore_connections(out_conns_indexed, 'inputConnectors', _outOP)

		self.clean_all_tags(_parent)		
		# for _op_clean in to_clean:
		# 	self.clean_tags(_op_clean, _parent)

		ui.undo.endBlock()
		self.pendingOrigOP = None

	def clean_all_tags(self, _parent):
		_tags = ['TEMPLATE_OUT', 'TEMPLATE_IN', 'TEMPLATE_COPY', 'TEMPLATE_ROOT']
		for _op in _parent.findChildren(tags=_tags, depth=1):
			for tag in _tags:
				if tag in _op.tags:
					_op.tags.remove(tag)

	def clean_tags(self, _op, _parent):
		_tags = ['TEMPLATE_OUT', 'TEMPLATE_IN', 'TEMPLATE_COPY', 'TEMPLATE_ROOT']
		for tag in _tags:
			if tag in _op.tags:
				_op.tags.remove(tag)



####################################################################	

	def DropOp(self, _op):
		fnsLog(f'OpTemplates: storing {_op.path} as template for {_op.OPType}')
		comp = self.createOrReturnTypeBase(_op.OPType, allowCooking=False)
		self.colorNewBase([comp])
		new_op = comp.copy(_op, includeDocked=True)
		TDFunctions.arrangeNode(new_op)
		self.RefreshCachedTemplates()
		return
	
	def createOrReturnTypeBase(self, optype, allowCooking=True):
		temps = self.templatesCOMP
		if comps := temps.findChildren(name=optype):
			comp = comps[0]
		else:
			comp = temps.create(baseCOMP, optype)
			TDFunctions.arrangeNode(comp)
			comp.allowCooking = allowCooking
		return comp

	def OpenTemplateBase(self, optype):
		comp = self.createOrReturnTypeBase(optype)
		self.colorNewBase([comp])
		self.RefreshCachedTemplates()
		p = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name=optype)
		p.owner = comp

	def colorNewBase(self, new_ops):
		for _op in new_ops:
			if _op.parent() == self.templatesCOMP and _op.OPType == 'baseCOMP':
				self.ColorBaseCOMPbyName(_op)

	def OnTemplatesUpdate(self, new_ops):
		self.RefreshCachedTemplates()
		self.colorNewBase(new_ops)
		pass


	def RefreshCachedTemplates(self):
		if hasattr(self, 'Templates'):  # This will check if 'my_property' is cached
			del self.__dict__['Templates']


	def ColorBaseCOMPbyName(self, _op):
		def find_first_match(input_str, criteria):
			for c in criteria:
				if c in input_str:
					return c
			return None
		op_family = find_first_match(_op.name, self.op_families)
		if op_family:
			_op.color = ui.colors[op_family]
		

	def updateTitleColor(self, op_family):
		self.ownerComp.op('popMenuConfig').parGroup.Titlecolor = ui.colors[op_family]


	def primeNewCOMPTemplate(self, comp):
		comp.allowCooking = False
		pass


	def OpenTemplatesFloating(self):
		p = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name="Templates")
		p.owner = self.templatesCOMP
	
	

	
#### EXTERNAL STUFF #####	

	def _librarySubfolder(self):
		"""The library folder under <palette>/FNSTools: Libraryfolder when
		set, the default otherwise. A bare folder name, never a path."""
		p = self.ownerComp.par['Libraryfolder']
		v = str(p.eval()).strip().strip('/').strip(chr(92)) if p is not None else ''
		return v or _DEFAULT_LIBRARY_SUBFOLDER

	def _libraryFolderOverridden(self):
		return self._librarySubfolder() != _DEFAULT_LIBRARY_SUBFOLDER

	@property
	def extFolder(self):
		return _fnsPaletteRoot() + '/' + self._librarySubfolder()

	def ExternalPathExpr(self, name=None):
		# the global file is always named after the tool's own base, whatever
		# library is active (the project library is a .toe citizen)
		if name == None:
			name = self.defaultTemplates.name + ('_2023' if app.build.startswith('2023') else '')
		return f"app.userPaletteFolder + '/FNSTools/{self._librarySubfolder()}/{name}.tox'"
	
	@property
	def ExternalPath(self):
		return eval(self.ExternalPathExpr())

	
	def get_new_name(self, directory, filename):
		# Extract name and extension
		name, ext = os.path.splitext(filename)
		
		# Extract the base name (without trailing digits)
		match = re.search(r'(\d+)$', name)
		if match:
			base_name = name[:match.start()]
			current_num = int(match.group())
		else:
			base_name = name
			current_num = 0
		
		# Find the highest digit of matching filenames in the directory
		max_num = current_num
		for f in os.listdir(directory):
			if f.startswith(base_name) and f.endswith(ext):
				f_name, _ = os.path.splitext(f)
				f_match = re.search(r'(\d+)$', f_name)
				if f_match:
					max_num = max(max_num, int(f_match.group()))
		
		# If the filename exists or the current number is already the highest, increment the number
		num = max_num + 1
		while os.path.exists(os.path.join(directory, f"{base_name}{num}{ext}")):
			num += 1
			
		return f"{base_name}{num}{ext}"

	def externalExprUpdate(self, extpar, enable, path_expr = None):
			extpar.expr = path_expr if enable else ''
			extpar.mode = ParMode.EXPRESSION if enable else ParMode.CONSTANT


	def TemplateSave(self):
		"""Persist the active library: the palette file under global scope,
		the project itself under project scope. User-initiated: it prompts."""
		confirm = not ui.messageBox("Confirm", "You are about to overwrite your templates.", buttons=['OK', 'Cancel'])
		if not confirm:
			return
		if self.scope == 'global':
			self.templatesCOMP.save(self.ExternalPath, createFolders=True)
			clearSeedMark(self.ExternalPath)
			fnsLog(f'OpTemplates: saved the global library to {self.ExternalPath}')
		else:
			project.save()

	def ExternalChange(self, onSave=False, startup=False, enable=None):
		"""Retired with the External toggle; the scope decides now."""
		return self.applyScope()

	def RefreshTemplates(self):
		"""Reload the active library: from the palette file under global scope;
		the project library has nothing to reload, its cache is refreshed."""
		if self.scope == 'global':
			self.defaultTemplates.par.reinitnet.pulse()
		run("parent.OpTemplate.RefreshCachedTemplates()", fromOP=self.ownerComp.op('OpTemplateExt'), endFrame=True)

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Open templates')
	def OpenTemplates(self):
		"""Open the OP templates browser (floating)."""
		self.OpenTemplatesFloating()
		return {'ok': True}

	@FNSCommand.fns_command(label='Add selection to templates', context='selected')
	def AddToTemplates(self):
		"""Save the current selection as a new template."""
		self.TemplateSave()
		return {'ok': True}

	@FNSCommand.fns_command(label='Save templates', hidden=True)
	def SaveTemplates(self):
		"""Write the templates tox to disk."""
		self.ownerComp.par.Savetemplates.pulse()
		return {'ok': True}

	@FNSCommand.fns_command(label='Refresh templates', hidden=True)
	def RefreshTemplatesCmd(self):
		"""Reload the templates from disk."""
		self.ownerComp.par.Refreshtemplates.pulse()
		return {'ok': True}
