
def onPulse(par):
	## In Extension code implement as follows:
	# def On<Insert Paramname Here>(self, _par):
	# 	...
	package = mod(me.dock.name).NoNode
	package.OnParExec(package.ParExecType.OnPulse, par)