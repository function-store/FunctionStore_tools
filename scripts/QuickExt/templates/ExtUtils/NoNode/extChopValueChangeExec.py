
def onValueChange(channel, sampleIndex, val, prev):
	package = mod(me.dock.name)
	package.NoNode.OnChopExec(package.ChopExecType.ValueChange, channel, sampleIndex, val, prev)
	return
	