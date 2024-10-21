def onOnToOff(channel, sampleIndex, val, prev):
	package = mod(me.dock.name).NoNode
	package.OnChopExec(package.ChopExecType.OnToOff, channel, sampleIndex, val, prev)
	return
