
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
#########

class HydroHomieExt:
	### TODO: REFACTOR: WHY AM I SO HACKY TODAY?
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.Show = tdu.Dependency(False)
		self.timer: timerCHOP = self.ownerComp.op('timer1')
		self.button = self.ownerComp.op('buttonMomentary')
		self.onStart()

	@property
	def display(self):
		return self.ownerComp.par.display.eval()
	
	@display.setter
	def display(self, _val):
		self.ownerComp.par.display.val = _val

	def onStart(self):
		#self.onParEnable(self.evalEnable)
		if self.evalEnable:
			self.button.allowCooking = True
			self.ownerComp.op('timer3').par.start.pulse()
			self.timer.par.start.pulse()
		else:
			self.timer.par.initialize.pulse()
			self.button.allowCooking = False
		run('args[0].display = args[1]', self, self.evalEnable and self.evalOnstartactive, delayFrames=1)
		#self.display = self.evalEnable and self.evalOnstartactive
		#if self.evalEnable:
			#self.timer.par.start.pulse()
		
		
	def onTimerDone(self):
		if self.evalEnable:
			#self.ownerComp.op('timer3').par.initialize.pulse()
			self.ownerComp.op('timer3').par.start.pulse()
			run('args[0].display = args[1]', self, True, delayFrames=1)
		
	def Dismiss(self):
		#self.Show.val = False
		if self.evalEnable:
			self.timer.par.start.pulse()

	def onParEnable(self, _val):
		if _val:
			self.button.allowCooking = True
			self.ownerComp.op('timer3').par.start.pulse()
			run('args[0].display = args[1]', self, True, delayFrames=1)
		else:
			self.timer.par.initialize.pulse()
			self.button.allowCooking = False
		


	


