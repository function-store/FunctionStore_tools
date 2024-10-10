
def whileOn(channel, sampleIndex, val, prev):
	package = mod(me.dock.name)
	package.NoNode.OnChopExec(package.ChopExecType.WhileOn, channel, sampleIndex, val, prev)
	return
