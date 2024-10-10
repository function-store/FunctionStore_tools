
def onOffToOn(channel, sampleIndex, val, prev):
	package = mod(me.dock.name)
	package.NoNode.OnChopExec(package.ChopExecType.OffToOn, channel, sampleIndex, val, prev)
	return
