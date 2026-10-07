# Timer CHOP callbacks - signatures match TD 2025 timerCHOP template.
# Only onCycle acts: it fires when a full cycle completes, so flipping
# Active on does not save instantly (onCycleStart would).

def onInitialize(timerOp, callCount):
	return 0

def onReady(timerOp):
	return

def onStart(timerOp):
	return

def onTimerPulse(timerOp, segment):
	return

def whileTimerActive(timerOp, segment, cycle, fraction):
	return

def onSegmentEnter(timerOp, segment, interrupt):
	return

def onSegmentExit(timerOp, segment, interrupt):
	return

def onCycleStart(timerOp, segment, cycle):
	return

def onCycleEndAlert(timerOp, segment, cycle, alertSegment, alertDone, interrupt):
	return

def onCycle(timerOp, segment, cycle):
	try:
		timerOp.parent().Tick()
	except Exception as e:
		debug(f'timer_autosave: {e}')
	return

def onDone(timerOp, segment, interrupt):
	return

def onSubrangeStart(timerOp):
	return
