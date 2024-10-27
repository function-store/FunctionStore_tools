
def onValueChange(par, prev):
	## In Extension code implement as follows:
	# def On<Insert Paramname Here>(self, _par, _val, _prev):
	# 	...
	package = mod(me.dock.name).NoNode
	package.OnParExec(package.ParExecType.ValueChange, par, par.eval(), prev)

