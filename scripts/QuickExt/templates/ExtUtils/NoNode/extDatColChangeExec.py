def onColChange(dat, cols):
	package = mod(me.dock.name).NoNode
	package.OnDatExec(package.DatExecType.ColChange, dat, cols=cols)
	return
