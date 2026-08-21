


'''Info Header Start
Name : ExtNoUI
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
Saveversion : 2025.33070
Info Header End'''
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import
###

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

class ExtNoUI:
	# TODO: is there a safer way to make sure we always restore to the "actual" height? currently using magic number 75 at one place
	# ------ but I guess you need something at least, the actual height gets stored anyway on first hide
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.timeline = op('/ui/dialogs/timeline')
		self._timeline_height_saved = self.ownerComp.fetch('timeline_height', 75)
		self.Shortcuts = tdu.Dependency('')
		self._setShortcuts()
		self._save_bg_color = self.bg_color if self.play_state else [0.25, 0.25, 0.25]
		self.UpdatePlayState(self.play_state)
		fnsLog('HideTimeline: init')

	@property
	def pause_indicator_ui_element(self):
		val = self.evalPauseindicator
		return val if val and val in ui.colors else 'default.bg'
		
	@property
	def play_state(self):
		return self.ownerComp.op('null_state')['play'].eval()

	@property
	def bg_color(self):
		return ui.colors[self.pause_indicator_ui_element]

	@bg_color.setter
	def bg_color(self, value):
		ui.colors[self.pause_indicator_ui_element] = value

	@property
	def module_enabled(self):
		return self.evalEnabletimeline

	@property
	def timeline_height(self):
		return self.timeline.par.h.eval()

	@timeline_height.setter
	def timeline_height(self, value):
		self.timeline.par.h.val = value
		if value > 0:  # Only store non-zero values
			self.ownerComp.store('timeline_height', value)

	def SetStateTimeline(self, on_create = None, on_start = None):
		if on_create:
			state = not self.evalHidetimeline
		elif on_start:
			state = not self.evalStateonstartuptimeline
		
		self._setStateTimeline(state)


	def _setStateTimeline(self, state=None):
		if not self.module_enabled:
			return

		if state is None:
			state = not bool(self.timeline_height)  # Toggle based on current height
		fnsLog(f'HideTimeline: timeline {"shown" if state else "hidden"}', level='DEBUG')

		if state:
			height = max(self._timeline_height_saved, 75)  # Ensure we never restore to 0
			if self.timeline_height == 0:
				self.timeline_height = height
		else:
			if self.timeline_height != 0:  # Only save if current height is non-zero
				self._timeline_height_saved = self.timeline_height
			self.timeline_height = 0
			
		self.parHidetimeline.val = not state

		self._updateUIPlayState(self.play_state)#####################


	def _setShortcuts(self):
		shortcuts = []
		for _par in self.ownerComp.pars('Shortcut*'):
			shortcuts.append(_par.eval())
		self.Shortcuts.val = shortcuts


	def onParHidetimeline(self, value):
		self._setStateTimeline(not value)

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Toggle timeline', state={'method': 'TimelineShown'})
	def ToggleTimeline(self):
		"""Show or hide the timeline bar."""
		if not self.module_enabled:
			return {'ok': False, 'error': 'HideTimeline is disabled - turn Enable Timeline Module on first'}
		self._setStateTimeline()
		return {'ok': True, 'shown': bool(self.timeline_height)}

	def OnShortcut(self, shortcutName):
		self._setStateTimeline()

	def UpdatePlayState(self, state):
		if self.evalHidetimeline or (not self.evalHidetimeline and state):
			self._updateUIPlayState(state)
			
	def _updateUIPlayState(self, state):
		_save_bg_color = self.bg_color
		self.bg_color = self.evalGroupPausestatecolor if state == False else self._save_bg_color
		if not state and any(abs(a - b) > 0.001 for a, b in zip(_save_bg_color, self.evalGroupPausestatecolor)):
			self._save_bg_color = _save_bg_color
		pass

	def onParGroupPausestatecolor(self, vals):
		self.bg_color = vals


	def onParPauseindicator(self, vals):
		self.UpdatePlayState(self.play_state)


	def TimelineShown(self):
		"""Is the timeline bar currently visible?"""
		return bool(self.timeline_height)
