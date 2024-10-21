def onOffToOn(channel, sampleIndex, val, prev):
	package = mod(me.dock.name).NoNode
	package.OnChopExec(package.ChopExecType.OffToOn, channel, sampleIndex, val, prev)
	return
