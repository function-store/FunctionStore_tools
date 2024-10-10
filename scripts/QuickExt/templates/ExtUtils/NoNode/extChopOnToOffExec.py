
def onOnToOff(channel, sampleIndex, val, prev):
	package = mod(me.dock.name)
	package.NoNode.OnChopExec(package.NoNode.ChopExecType.OnToOff, channel, sampleIndex, val, prev)
	return
