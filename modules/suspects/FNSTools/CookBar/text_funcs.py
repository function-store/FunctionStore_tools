def active(active):
	parent().store('active', active)
	targetCOMP = me.fetch('targetCOMP')
	if active:
		activateBgName()
		updateRes()
		if targetCOMP:
			addNewBg(targetCOMP)
	else:
		rmOldBg(targetCOMP)
		deactiveBgName()

def check():
	
	if not op('null_cook_bar_bg'):
		activateBgName()

	op('text_tscript_check_winplacement').run()

	pane = currentPane()
	if pane is None:
		return

	# FNSTools: a different pane has its own size even at the same ratio.
	if pane.id != me.fetch('paneId', None):
		parent().store('paneId', pane.id)
		updateRes(pane)

	oldRatio = me.fetch('netRatio')
	newRatio = pane.ratio
	if newRatio != oldRatio:
		updateRes(pane)
		parent().store('netRatio', newRatio)

	oldTargetCOMP = me.fetch('targetCOMP')
	newTargetCOMP = pane.owner
	if newTargetCOMP != oldTargetCOMP:
		parent().store('targetCOMP', newTargetCOMP)
		if oldTargetCOMP:
			rmOldBg(oldTargetCOMP)
		addNewBg(newTargetCOMP)

	oldX = me.fetch('netX')
	newX = pane.x
	if newX != oldX:
		parent().store('netX', newX)

	oldY = me.fetch('netY')
	newY = pane.y
	if newY != oldY:
		parent().store('netY', newY)

	oldZoom = me.fetch('netZoom')
	newZoom = pane.zoom
	if newZoom != oldZoom:
		parent().store('netZoom', newZoom)


def currentPane():
	# FNSTools: follow the network editor you are working in. The original
	# read ui.panes[0], the first pane, so with split panes the bars could draw
	# in a network you were not looking at. ui.panes.current can name a pane
	# that was closed (measured: 'pane2', open False, absent from ui.panes),
	# so only an open network editor counts; failing that, the pane the bar
	# was already following, then the first open network editor.
	def usable(p):
		return p is not None and p.type == PaneType.NETWORKEDITOR and getattr(p, 'open', True)
	cur = ui.panes.current
	if usable(cur):
		return cur
	last = parent().fetch('paneId', None)
	for p in ui.panes:
		if usable(p) and p.id == last:
			return p
	for p in ui.panes:
		if usable(p):
			return p
	return None


def updateRes(pane=None):
	pane = pane or currentPane()
	if pane is None:
		return
	z = pane.zoom
	pane.fitWidth(1)
	w = pane.zoom
	pane.fitHeight(1)
	h = pane.zoom
	pane.zoom  = z
	parent().store('netWidth', w)
	parent().store('netHeight', h)


def addNewBg(targetCOMP):
	if targetCOMP:
		disableOPsDisplay(targetCOMP)
		dimAnnotationBacks(targetCOMP)

	if not targetCOMP.op('select_cook_bar_bg'):
		selectBgTOP = targetCOMP.create(selectTOP, 'select_cook_bar_bg')
		bgTOPRef = "op('" + op('null_cook_bar_bg').path + "')"
		topParScript = bgTOPRef + " if " + bgTOPRef + " else (mod('text_cook_bar_suicide').suicide(me) if op('text_cook_bar_suicide') else '')"
		selectBgTOP.par.top.expr = topParScript
		selectBgTOP.display = True
	
	if not targetCOMP.op('text_cook_bar_suicide'):
		suicideDAT = targetCOMP.create(textDAT, 'text_cook_bar_suicide')
		suicideScript = """\
def suicide(victim):
	suicideScript = '''
args[0].destroy()
'''
	run(suicideScript, victim)
	me.destroy()
	return ''
"""
		suicideDAT.text = suicideScript
	
	hideOPs = [
		targetCOMP.op('select_cook_bar_bg'),
		targetCOMP.op('text_cook_bar_suicide')
	]
	init = parent().fetch('init')
	if init:
		for hideOP in hideOPs:
			hideOP.expose = False
	else:
		delayScript = '''
for hideOP in args[0]:
	hideOP.expose = False
'''
		run(delayScript, hideOPs, delayFrames=1)
		parent().store('init', True)


def rmOldBg(targetCOMP, clear=True):
	# FNSTools: clear=False puts everything back but leaves the records for a
	# caller to clear later (CookBarExt.onDestroyTD: a store() on this COMP
	# while it cooks is a cook dependency loop).
	if targetCOMP:
		oldOPs = [
			targetCOMP.op('select_cook_bar_bg'),
			targetCOMP.op('text_cook_bar_suicide')
		]
		for oldOP in oldOPs:
			if oldOP:
				oldOP.destroy()
	restoreOPsDisplay(clear)
	restoreAnnotationBacks(clear)


def disableOPsDisplay(targetCOMP):
	# FNSTools: only the open network's own TOPs compete for its background,
	# so only they are switched off (this used to reach every TOP at every
	# depth below), and each one is remembered so leaving puts it back.
	hidden = list(parent().fetch('hiddenDisplay', []) or [])
	for child in targetCOMP.findChildren(type=TOP, maxDepth=1):
		if child.display:
			if child.name != 'select_cook_bar_bg':
				child.display = False
				hidden.append(child.path)
	parent().store('hiddenDisplay', hidden)


def restoreOPsDisplay(clear=True):
	hidden = parent().fetch('hiddenDisplay', []) or []
	for path in hidden:
		hiddenOP = op(path)
		if hiddenOP is not None:
			hiddenOP.display = True
	if clear and hidden:
		parent().store('hiddenDisplay', [])


def dimAnnotationBacks(targetCOMP):
	# FNSTools: an annotation's back colour covers the bars drawn behind it.
	# While the bar is in a network, each Annotate COMP's Back Color Alpha
	# drops to the tool's Annotation Alpha (never raised), and leaving puts
	# back exactly what was there: value, expression or bind.
	# Annotations are utility ops, which op() cannot find, so each one is
	# remembered by its network and its name.
	saved = list(parent().fetch('dimmedAnnotations', []) or [])
	seen = set((s[0], s[1]) for s in saved)
	limit = float(parent().par.Annotationalpha.eval()) if hasattr(parent().par, 'Annotationalpha') else 0.2
	for ann in targetCOMP.findChildren(type=annotateCOMP, maxDepth=1, includeUtility=True):
		p = getattr(ann.par, 'Backcoloralpha', None)
		if p is None or (targetCOMP.path, ann.name) in seen:
			continue
		if p.mode == ParMode.EXPRESSION:
			kept = ('expr', p.expr)
		elif p.mode == ParMode.BIND:
			kept = ('bind', p.bindExpr)
		else:
			kept = ('val', float(p.eval()))
		saved.append((targetCOMP.path, ann.name) + kept)
		p.val = min(float(p.eval()), limit)
	parent().store('dimmedAnnotations', saved)


def restoreAnnotationBacks(clear=True):
	dimmed = parent().fetch('dimmedAnnotations', []) or []
	for compPath, name, kind, value in dimmed:
		comp = op(compPath)
		found = comp.findChildren(name=name, type=annotateCOMP, maxDepth=1, includeUtility=True) if comp is not None else []
		p = getattr(found[0].par, 'Backcoloralpha', None) if found else None
		if p is None:
			continue
		if kind == 'expr':
			p.expr = value
			p.mode = ParMode.EXPRESSION
		elif kind == 'bind':
			p.bindExpr = value
			p.mode = ParMode.BIND
		else:
			p.val = value
	if clear and dimmed:
		parent().store('dimmedAnnotations', [])


def storeWinRes(newWinWidth, newWinHeight):
	oldWinWidth = parent().fetch('winWidth')
	oldWinHeight = parent().fetch('winHeight')
	if newWinWidth != oldWinWidth or newWinHeight != oldWinHeight:
		updateRes()
		parent().store('winWidth', newWinWidth)
		parent().store('winHeight', newWinHeight)


def activateBgName():
	deactivatedBgTOP = op('null_cook_bar_bg__deactivated')
	if deactivatedBgTOP:
		deactivatedBgTOP.name = 'null_cook_bar_bg'


def deactiveBgName():
	bgTOP = op('null_cook_bar_bg')
	if bgTOP:
		bgTOP.name = 'null_cook_bar_bg__deactivated'
