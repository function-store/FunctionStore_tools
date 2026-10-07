# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

def onOffToOn(channel, sampleIndex, val, prev):
	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	# Enable state lives in each parameter's enableExpr; this only relabels
	# Power and seeds a natural-log base when Logarithm is picked.
	if val == 4 and prev != 4:
		parent().par.Power = 2.71828
	parent().par.Power.label = "Base" if val == 4 else "Power"
	return
