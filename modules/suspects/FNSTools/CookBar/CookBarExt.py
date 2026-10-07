"""CookBar: quick-launch commands, and keeping the viewed network clean.

Thin on purpose. The bar itself is Anton Heestand's original scripts
(text_funcs and the callback DATs); this extension gives them commands and
the two moments they had no answer for: a project save while the bar is on,
and the tool going away while the bar is on. Both would otherwise leave the
network's display flags off and its annotations dimmed.
"""

FNSCommand = (next((d for d in me.docked if 'ExtUtils' in d.tags), None) or next((c for c in me.parent().children if 'ExtUtils' in c.tags), None)).mod('FNSCommand')  # import


class CookBarExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

	def onInitTD(self):
		# The slim ExtUtils has no announcer: announce past the registry's
		# /sys promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)
		# A reinit ran the old instance's onDestroyTD first, which put the
		# network back and cleared its records a frame later; draw over it
		# again after that, if the bar is still on.
		run('args[0].valid and args[0].ext.CookBarExt.reapply()', self.ownerComp, delayFrames=2, delayRef=op.TDResources)

	def onDestroyTD(self):
		# Runs inside destroy() with the network still readable, and on every
		# reinit (onInitTD re-applies then). Two things stay out of here:
		# - promoted lookups on the owner: on a reinit they wait on the
		#   extensions being rebuilt and hang TD for good;
		# - store() on the owner: this runs inside the owner's own cook, and a
		#   write to its storage there is a cook dependency loop (measured: the
		#   warning on every reinit). The values go back now; the records that
		#   listed them are cleared a frame later, which a destroy never gets.
		try:
			self._funcs().rmOldBg(self._target(), clear=False)
		except Exception as e:
			debug('CookBar: could not put the network back: %s' % e)
		run('args[0].valid and args[0].ext.CookBarExt.forgetRestored()', self.ownerComp, delayFrames=1, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	# ---------------------------------------------- the viewed network

	def _funcs(self):
		return self.ownerComp.op('text_funcs').module

	def _target(self):
		target = self.ownerComp.fetch('targetCOMP', None, search=False)
		return target if target is not None and target.valid else None

	def putBack(self):
		"""Return the viewed network to how it was, keeping the bar switched on."""
		try:
			self._funcs().rmOldBg(self._target())
		except Exception as e:
			debug('CookBar: could not put the network back: %s' % e)

	def forgetRestored(self):
		"""Clear the records of what onDestroyTD already put back."""
		for key in ('hiddenDisplay', 'dimmedAnnotations'):
			if self.ownerComp.fetch(key, [], search=False):
				self.ownerComp.store(key, [])

	def reapply(self):
		"""Draw the bar into the viewed network again, if it is on."""
		if not self.ownerComp.par.Active.eval():
			return
		target = self._target()
		if target is not None:
			self._funcs().addNewBg(target)

	def beforeSave(self):
		"""Project pre-save: the saved project must not keep the bar's changes."""
		on = bool(self.ownerComp.par.Active.eval()) and self._target() is not None
		self.ownerComp.store('putBackForSave', on)
		if on:
			self.putBack()

	def afterSave(self):
		"""Project post-save: draw the bar again if it was on before the save."""
		if self.ownerComp.fetch('putBackForSave', False, search=False):
			self.ownerComp.store('putBackForSave', False)
			self.reapply()

	# ---------------------------------------------- commands

	@FNSCommand.fns_command(label='Toggle cook bar', state={'method': 'BarActive'})
	def ToggleCookBar(self):
		"""Show or hide each operator's cook time and GPU memory above it in the network editor."""
		p = self.ownerComp.par.Active
		if not p.enable:
			return {'ok': False, 'error': 'the timeline is paused; Cook Bar draws while it plays'}
		p.val = not p.eval()
		return {'ok': True, 'active': bool(p.eval())}

	@FNSCommand.fns_command(label='Open Global Hog CHOP')
	def OpenHog(self):
		"""Open the Global Hog CHOP's parameters, to eat frame time on purpose while you watch the bars."""
		hog = self.ownerComp.op('hog_global')
		if hog is None:
			return {'ok': False, 'error': 'hog_global is missing'}
		hog.openParameters()
		return {'ok': True}

	@FNSCommand.fns_command(label='Toggle Global Hog CHOP', hidden=True, state={'method': 'HogActive'})
	def ToggleHog(self):
		"""Switch the Global Hog CHOP on or off. It DELIBERATELY eats frame time (stress test)."""
		hog = self.ownerComp.op('hog_global')
		if hog is None:
			return {'ok': False, 'error': 'hog_global is missing'}
		hog.par.active = not hog.par.active.eval()
		return {'ok': True, 'active': bool(hog.par.active.eval())}

	# ---------------------------------------------- parameter pulses (parexec_ext)

	def _onOpenhogPulse(self, par):
		self.OpenHog()

	def BarActive(self):
		"""Whether the bars are on (the Toggle cook bar chip)."""
		return bool(self.ownerComp.par.Active.eval())

	def HogActive(self):
		"""Whether the Global Hog CHOP is on (the Toggle Global Hog CHOP chip)."""
		hog = self.ownerComp.op('hog_global')
		return bool(hog.par.active.eval()) if hog is not None else False
