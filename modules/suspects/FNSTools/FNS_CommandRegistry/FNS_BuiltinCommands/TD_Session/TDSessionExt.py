'''Info Header Start
Name : TDSessionExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
"""TD_Session - built-in TouchDesigner project / session commands.

TD's own project, performance and file actions from the official Python
API (Project Class, App Class, UI Class), registered with
FNS_CommandRegistry so they surface in the launcher palette in ANY
project the companion is loaded into - no FunctionStore tools required.
Sibling TD_Dialogs owns the dialog / pane half; the split respects the
registry's 24-commands-per-owner cap. Survey source:
FunctionStore_tools_PUB/docs/CommandRegistryCandidates.md.

The decorator comes from the shared FNSCommand module in the docked
ExtUtilsMinimal (the slim shape: no NoNode, no announcer; FNSCommand is
file-synced to the CustomParTools/QuickExt master, one source of
truth), resolvable at class-compile time. Every
command here is TD/system functionality, so the local `fns_command`
below brands builtin=True and derives a canonical id from the method
name. Wire contract: docs/fns-command-registry.md in the TDXLPP repo;
the FNSTools side is docs/CommandRegistration.md.
"""

FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand')  # import
###

import re
from typing import Literal

def _kebab(name):
	return re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()


def fns_command(fn=None, **meta):
	"""The shared decorator, branded builtin=True and given a canonical id
	derived from the method name: `td.session.open-textport` style.

	The canonical id is a CROSS-PACKAGE identity (registry >= 1.9.0): when
	two packages ship the same command, the newest Pkgversion wins and the
	older set is shadowed instead of doubling the list. Any other package
	that ships these commands must derive the id by this same rule."""
	def mark(f):
		meta.setdefault('canonical', 'td.session.' + _kebab(f.__name__))
		return FNSCommand.fns_command(builtin=True, **meta)(f)
	return mark(fn) if fn is not None else mark


class TDSessionExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		run('args[0]._announceCommands()', self, delayFrames=60)

	def onInitTD(self):
		# Reinits announce again - registration is idempotent.
		run('args[0]._announceCommands()', self, delayFrames=60)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def _defer(self, fn, frames=1):
		"""Run later so the bus reply escapes first."""
		run(fn, delayFrames=frames)
		return {'ok': True, 'started': True}

	def _pickCurrentOp(self):
		"""The op the user means: current pane's first selected child,
		else its current child, else the pane owner itself."""
		try:
			owner = getattr(ui.panes.current, 'owner', None)
			if owner is None:
				return None
			sel = list(getattr(owner, 'selectedChildren', []) or [])
			if sel:
				return sel[0]
			return getattr(owner, 'currentChild', None) or owner
		except Exception:
			return None

	# --- project & session -------------------------------------------------

	@fns_command
	def SaveProject(self):
		"""Save the project (respects the Increment Filename preference)."""
		project.save()
		return {'ok': True, 'name': project.name}

	@fns_command(label='Save project + external toxes')
	def SaveProjectWithToxes(self):
		"""Save the project AND write all dirty external .tox files."""
		project.save(saveExternalToxs=True)
		return {'ok': True, 'name': project.name}

	@fns_command(label='Load recent file')
	def LoadRecent(self, index: int = 1):
		"""Load a File > Recent entry (1 = most recent). CLOSES this project."""
		files = list(app.recentFiles)
		if not files:
			return {'ok': False, 'error': 'no recent files'}
		if not 1 <= index <= len(files):
			return {'ok': False, 'error': f'index out of range (1-{len(files)})'}
		path = files[index - 1]
		# Deferred well past the reply - loading tears this session down.
		return {**self._defer(lambda: project.load(path), frames=30), 'file': path}

	@fns_command(label='Quit TouchDesigner')
	def QuitTouchDesigner(self):
		"""Quit TD (prompts about unsaved changes first)."""
		return self._defer(lambda: project.quit(), frames=30)

	@fns_command(state={'method': 'RealtimeEnabled'})
	def ToggleRealtime(self):
		"""Toggle realtime playback mode."""
		project.realTime = not project.realTime
		return {'ok': True, 'realtime': bool(project.realTime)}

	@fns_command(hidden=True, state={'method': 'CookRate'})
	def SetCookRate(self, fps: float):
		"""Set the project cook rate (advanced)."""
		project.cookRate = fps
		return {'ok': True, 'fps': float(project.cookRate)}

	@fns_command(label='Toggle window on top', state={'method': 'WindowOnTop'})
	def ToggleWindowOnTop(self):
		"""Toggle keep-on-top for TD's main window."""
		project.windowOnTop = not project.windowOnTop
		return {'ok': True, 'on_top': bool(project.windowOnTop)}

	@fns_command(label='Toggle perform on start', state={'method': 'PerformOnStart'})
	def TogglePerformOnStart(self):
		"""Toggle whether this project opens straight into perform mode."""
		project.performOnStart = not project.performOnStart
		return {'ok': True, 'perform_on_start': bool(project.performOnStart)}

	# --- performance & playback --------------------------------------------

	@fns_command(state={'method': 'PerformModeOn'})
	def TogglePerformMode(self):
		"""Toggle perform mode."""
		ui.performMode = not ui.performMode
		return {'ok': True, 'perform': bool(ui.performMode)}

	@fns_command(hidden=True, state={'method': 'PowerOn'})
	def TogglePower(self):
		"""MASTER power switch - off halts ALL processing (advanced)."""
		app.power = not app.power
		return {'ok': True, 'power': bool(app.power)}

	@fns_command(label='Set master volume', state={'method': 'MasterVolume'})
	def SetMasterVolume(self, level: float):
		"""Set TD's master audio volume (0-1)."""
		ui.masterVolume = max(0.0, min(1.0, level))
		return {'ok': True, 'level': float(ui.masterVolume)}

	# --- live state getters (registry `state` refs; query-time, cheap) -----
	# Promoted so the registry can reach them, but NOT decorated - only
	# `_fns_command`-marked methods become commands. Bool returns chip as
	# ON/OFF; floats chip as trimmed numbers and seed value prompts.

	def RealtimeEnabled(self):
		return bool(project.realTime)

	def CookRate(self):
		return float(project.cookRate)

	def WindowOnTop(self):
		return bool(project.windowOnTop)

	def PerformOnStart(self):
		return bool(project.performOnStart)

	def PerformModeOn(self):
		return bool(ui.performMode)

	def PowerOn(self):
		return bool(app.power)

	def MasterVolume(self):
		return float(ui.masterVolume)

	# --- files & folders ---------------------------------------------------

	@fns_command
	def OpenProjectFolder(self):
		"""Show the project's folder in Explorer / Finder."""
		return self._defer(lambda: ui.viewFile(project.folder))

	@fns_command(label='Open TD folder')
	def OpenTdFolder(self, folder: Literal[
		'userpalette', 'desktop', 'temp', 'preferences', 'bin',
		'samples', 'install',
	]):
		"""Show one of TD's own folders in Explorer / Finder."""
		attr = {
			'userpalette': 'userPaletteFolder',
			'desktop': 'desktopFolder',
			'temp': 'tempFolder',
			'preferences': 'preferencesFolder',
			'bin': 'binFolder',
			'samples': 'samplesFolder',
			'install': 'installFolder',
		}[folder]
		target = str(getattr(app, attr))
		return {**self._defer(lambda: ui.viewFile(target)), 'folder': target}

	@fns_command(label='Copy op path')
	def CopyOpPath(self):
		"""Copy the selected operator's path to the clipboard."""
		target = self._pickCurrentOp()
		if target is None:
			return {'ok': False, 'error': 'no current operator'}
		ui.clipboard = target.path
		return {'ok': True, 'path': target.path}

	@fns_command(label='Open op parameters')
	def OpenOpParameters(self):
		"""Open a floating parameter dialog for the selected operator."""
		target = self._pickCurrentOp()
		if target is None:
			return {'ok': False, 'error': 'no current operator'}
		return {**self._defer(lambda: target.openParameters()), 'path': target.path}

	@fns_command(label='Open op viewer')
	def OpenOpViewer(self):
		"""Open the selected operator's viewer window."""
		target = self._pickCurrentOp()
		if target is None:
			return {'ok': False, 'error': 'no current operator'}
		return {**self._defer(lambda: target.openViewer()), 'path': target.path}
