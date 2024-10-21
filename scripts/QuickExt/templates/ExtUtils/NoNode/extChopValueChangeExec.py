def onValueChange(channel, sampleIndex, val, prev):
	package = mod(me.dock.name).NoNode
	package.OnChopExec(package.ChopExecType.ValueChange, channel, sampleIndex, val, prev)
	return
	