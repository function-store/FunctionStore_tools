
def onColChange(dat, cols):
	package = mod(me.dock.name)
	package.NoNode.OnDatExec(package.DatExecType.ColChange, dat, cols=cols)
	return
