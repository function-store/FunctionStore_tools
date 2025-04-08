
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class ExtMidiBypasser:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)


	@property
	def AllMidiOps(self):
		all_midis = []
		# look in operators stemming from root, but not '/local' or '/sys', or '/ui'
		device_id = self.evalDeviceid
		for _op in op('/').findChildren(key=lambda x: x.opType in ['midiinCHOP', 'midioutCHOP','midiinDAT']):
			if _op.path.startswith('/local') or _op.path.startswith('/sys') or _op.path.startswith('/ui'):
				continue
			all_midis.append(_op)
		return all_midis

	def DoBypass(self, _val: bool, channel: int = None):
		for _op in self.AllMidiOps:
			if channel is not None and int(_op.par.id.eval()) != channel:
				continue
			_op.bypass = _val

			
			if _val == False:
				to_reset = []
				if self.evalResetchannels:
					to_reset.append('resetchannelspulse')
				if self.evalResetvalues:
					to_reset.append('resetpulse')
					
				for _p in to_reset:
					if _op.par[_p] is not None:
						_op.par[_p].pulse()

	def onParResetmidi(self):
		self.BypassOnOff(self.evalDeviceid)

	def OnParResetall(self):
		self.onParResetall()

	def onParResetall(self):
		self.BypassOnOff()
		pass

	def BypassOnOff(self, channel: int = None):
		self.DoBypass(True, channel)
		run('parent().DoBypass(False, args[0])', channel, delayMilliSeconds=self.ownerComp.par.Resetdelayms.eval(), fromOP=me)
	
