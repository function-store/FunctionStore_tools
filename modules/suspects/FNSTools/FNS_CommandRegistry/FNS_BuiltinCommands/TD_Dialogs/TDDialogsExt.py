'''Info Header Start
Name : TDDialogsExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
"""TD_Dialogs - built-in TouchDesigner dialog / window / pane commands.

TD's own actions from the official Python API (UI Class, Pane Class,
TDFunctions), registered with FNS_CommandRegistry so they surface in the
launcher palette in ANY project the companion is loaded into - no
FunctionStore tools required. Sibling TD_Session owns the project /
session / file half; the split respects the registry's
24-commands-per-owner cap. Survey source:
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
	derived from the method name: `td.dialogs.open-textport` style.

	The canonical id is a CROSS-PACKAGE identity (registry >= 1.9.0): when
	two packages ship the same command, the newest Pkgversion wins and the
	older set is shadowed instead of doubling the list. Any other package
	that ships these commands must derive the id by this same rule."""
	def mark(f):
		meta.setdefault('canonical', 'td.dialogs.' + _kebab(f.__name__))
		return FNSCommand.fns_command(builtin=True, **meta)(f)
	return mark(fn) if fn is not None else mark


class TDDialogsExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		run('args[0]._announceCommands()', self, delayFrames=60)

	def onInitTD(self):
		# Reinits announce again - registration is idempotent.
		run('args[0]._announceCommands()', self, delayFrames=60)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def _defer(self, fn):
		"""Window openers run a frame later so the bus reply escapes first."""
		run(fn, delayFrames=1)
		return {'ok': True, 'started': True}

	# --- dialogs & windows -------------------------------------------------

	@fns_command
	def OpenTextport(self):
		"""Open the Textport."""
		return self._defer(lambda: ui.openTextport())

	@fns_command
	def OpenErrors(self):
		"""Open the Errors dialog."""
		return self._defer(lambda: ui.openErrors())

	@fns_command
	def OpenConsole(self):
		"""Open the OS console window (not the Textport)."""
		return self._defer(lambda: ui.openConsole())

	@fns_command
	def OpenPerformanceMonitor(self):
		"""Open the Performance Monitor."""
		return self._defer(lambda: ui.openPerformanceMonitor())

	@fns_command
	def OpenBeat(self):
		"""Open the beat / tap-tempo dialog."""
		return self._defer(lambda: ui.openBeat())

	@fns_command
	def OpenBookmarks(self):
		"""Open the Bookmarks dialog."""
		return self._defer(lambda: ui.openBookmarks())

	@fns_command
	def OpenKeyManager(self):
		"""Open the Key Manager dialog."""
		return self._defer(lambda: ui.openKeyManager())

	@fns_command(label='Open MIDI Device Mapper')
	def OpenMidiMapper(self):
		"""Open the MIDI Device Mapper dialog."""
		return self._defer(lambda: ui.openMIDIDeviceMapper())

	@fns_command
	def OpenPaletteBrowser(self):
		"""Open the Palette Browser."""
		return self._defer(lambda: ui.openPaletteBrowser())

	@fns_command(label='Open Operator Snippets')
	def OpenSnippets(self, optype: str = ''):
		"""Open Operator Snippets, optionally for one type (e.g. noiseTOP)."""
		if optype:
			return self._defer(lambda: ui.openOperatorSnippets(optype))
		return self._defer(lambda: ui.openOperatorSnippets())

	@fns_command
	def OpenPreferences(self):
		"""Open the Preferences dialog."""
		return self._defer(lambda: ui.openPreferences())

	@fns_command
	def OpenWindowPlacement(self):
		"""Open the Window Placement dialog."""
		return self._defer(lambda: ui.openWindowPlacement())

	@fns_command
	def OpenSearch(self):
		"""Open the Search / Replace dialog."""
		return self._defer(lambda: ui.openSearch())

	@fns_command
	def ImportFile(self):
		"""Open TD's Import File dialog."""
		return self._defer(lambda: ui.openImportFile())

	@fns_command
	def ExportMovie(self, top: str = ''):
		"""Open the Export Movie dialog, optionally preloaded with a TOP path."""
		if top:
			target = op(top)
			if target is None:
				return {'ok': False, 'error': f'no operator at {top!r}'}
			return self._defer(lambda: ui.openExportMovie(target.path))
		return self._defer(lambda: ui.openExportMovie())

	@fns_command
	def OpenVersion(self):
		"""Open the version / about dialog."""
		return self._defer(lambda: ui.openVersion())

	# --- panes & navigation ------------------------------------------------

	@fns_command
	def MaximizePane(self):
		"""Toggle maximize on the current pane."""
		pane = ui.panes.current
		pane.maximize = not pane.maximize
		return {'ok': True, 'maximize': bool(pane.maximize)}

	@fns_command(label='Tear away pane')
	def TearAwayPane(self):
		"""Tear the current pane into its own OS window."""
		return self._defer(lambda: ui.panes.current.tearAway())

	@fns_command(label='Floating copy of pane')
	def FloatingPaneCopy(self):
		"""Open a floating copy of the current pane."""
		return self._defer(lambda: ui.panes.current.floatingCopy())

	@fns_command(label='Set pane type')
	def SetPaneType(self, kind: Literal[
		'networkeditor', 'panel', 'geometryviewer', 'topviewer',
		'chopviewer', 'animationeditor', 'textport', 'parameters',
		'opbrowser',
	]):
		"""Change the current pane to another pane type."""
		pane_type = getattr(PaneType, kind.upper(), None)
		if pane_type is None:
			return {'ok': False, 'error': f'unknown pane type: {kind}'}
		ui.panes.current.changeType(pane_type)
		return {'ok': True, 'kind': kind}

	@fns_command(label='Show op in floating pane')
	def ShowOp(self, path: str):
		"""Open a floating network pane on an operator path."""
		target = op(path)
		if target is None:
			return {'ok': False, 'error': f'no operator at {path!r}'}
		import TDFunctions
		return self._defer(lambda: TDFunctions.showInPane(target, inPane='Floating'))

	@fns_command(label='Home network view')
	def HomeNetwork(self):
		"""Home the current network editor's view."""
		pane = ui.panes.current
		if not hasattr(pane, 'home'):
			return {'ok': False, 'error': 'current pane is not a network editor'}
		pane.home()
		return {'ok': True}
