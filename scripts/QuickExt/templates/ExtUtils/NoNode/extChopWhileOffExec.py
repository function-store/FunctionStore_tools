def whileOff(channel, sampleIndex, val, prev):
	package = mod(me.dock.name).NoNode
	package.OnChopExec(package.ChopExecType.WhileOff, channel, sampleIndex, val, prev)
	return
