
def whileOff(channel, sampleIndex, val, prev):
	package = mod(me.dock.name)
	package.NoNode.OnChopExec(package.ChopExecType.WhileOff, channel, sampleIndex, val, prev)
	return
