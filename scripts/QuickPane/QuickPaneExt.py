class QuickPaneExt:
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

		self.leftPane = None
		self.rightPane = None
		self.topPane = None
		self.bottomPane = None
		self.pane_map = {
			'left': 'leftPane',
			'right': 'rightPane',
			'top': 'topPane',
			'bottom': 'bottomPane'
		}

	@property
	def allPanes(self):
		return [pane.owner for pane in ui.panes]

	def OnOpenDir(self, dir='left'):
		curr_comp = ui.panes.current.owner.currentChild
		if not curr_comp:
			return

		pane_actions = {
			'left': ('leftPane', lambda: ui.panes.current.splitLeft()),
			'right': ('rightPane', lambda: ui.panes.current.splitRight()),
			'top': ('topPane', lambda: ui.panes.current.splitTop()),
			'bottom': ('bottomPane', lambda: ui.panes.current.splitBottom())
		}

		pane_ratios = {
			'left': self.ownerComp.par.Ratiow.eval(),
			'right': self.ownerComp.par.Ratiow.eval(),
			'top': 1-self.ownerComp.par.Ratioh.eval(),
			'bottom': 1-self.ownerComp.par.Ratioh.eval()
		}

		pane_attr, split_method = pane_actions.get(dir, (None, None))
		if not pane_attr:
			return  # Direction not recognized

		pane_exists = lambda _my_pane: _my_pane.id in [pane.id for pane in ui.panes] if _my_pane else None
		my_pane = getattr(self, pane_attr)
		if not pane_exists(my_pane) and curr_comp.isCOMP:
			new_pane = split_method()
			setattr(self, pane_attr, new_pane)
		else:
			self.onCloseDir(dir)
			return
		
		if new_pane:
			new_pane.owner = curr_comp
			new_pane.home()
			new_pane.ratio = pane_ratios.get(dir)
			panenav = op(f'/ui/panes/panebar/{new_pane.name}/panenav')
			if panenav:
				self.setBorder(panenav, 1)

	def onCloseDir(self, dir='left'):
		pane_attr = self.pane_map.get(dir)
		if pane_attr:
			pane = getattr(self, pane_attr)

		if pane:
			panenav = op(f'/ui/panes/panebar/{pane.name}/panenav')
			if panenav:
				self.setBorder(panenav, 0)
			setattr(self, pane_attr, None)
			pane.close()

	def clearBorders(self):
		for _pane in ui.panes:
			if _pane.type == PaneType.NETWORKEDITOR:
				panenav = op(f'/ui/panes/panebar/{_pane.name}/panenav')
				self.setBorder(panenav, 0)


	def setBorder(self, panenav, state):
		panenav.parGroup.bordera = (0.1, 0.4, 0.1)
		panenav.par.borderover = state
		panenav.par.leftborder = state
		panenav.par.rightborder = state
		panenav.par.bottomborder = state
		panenav.par.topborder = state