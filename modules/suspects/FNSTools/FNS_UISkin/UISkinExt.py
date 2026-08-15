"""FNS_UISkin -- appearance customization for TouchDesigner's own UI chrome.

One parameter per customizable target, applied directly. This tool does NOT
publish through a registry: skinning contributes nothing to a surface's
behaviour (no search words, no menu items, no injected operators), it only
overwrites a parameter on chrome TD already owns. Routing that through the
op-menu registry made every skinnable panel a registry concept for no gain.

SKIN_TARGETS below is the single source of truth: it generates the parameter
pages, and Apply() reads it. Adding a knob is ONE row -- no par to create by
hand, no second list to keep in sync.
"""


class UISkinExt:

	# (page, par name, label, help, target patterns)
	#
	# Patterns are absolute /ui paths on purpose -- TD's own fixed chrome, not
	# project structure -- and are resolved with ops(), so one parameter can
	# drive a whole family. The pane bar is why that matters: TD keeps a
	# template plus one live bar per open pane, and they must all match.
	SKIN_TARGETS = (
		('Op Menu', 'Opmenuempty', 'Empty Panel',
		 'Background behind the large area shown before an operator family is picked.',
		 ('/ui/dialogs/menu_op/emptypanel',)),
		('Op Menu', 'Opmenunode', 'Node Panel',
		 'Background behind the operator list.',
		 ('/ui/dialogs/menu_op/nodepanel',)),
		('Op Menu', 'Opmenufamily', 'Family Panel',
		 'Background behind the TOP/CHOP/SOP family buttons.',
		 ('/ui/dialogs/menu_op/familypanel',)),
		('Op Menu', 'Opmenusearch', 'Search Panel',
		 'Background behind the search field row.',
		 ('/ui/dialogs/menu_op/searchpanel',)),

		('Toolbar', 'Toolbarempty', 'Empty Panel',
		 'Background of the bookmark bar -- the toolbar surface.',
		 ('/ui/dialogs/bookmark_bar/emptypanel',)),

		('Main Menu', 'Mainmenuempty', 'Empty Panel',
		 'Background of the main menu bar.',
		 ('/ui/dialogs/mainmenu/emptypanel',)),

		('Pane Bar', 'Panebarempty', 'Empty Panel',
		 'Background of EVERY pane bar at once: TD\'s template plus one per open '
		 'pane. New panes are picked up by the healing tick, so a pane split '
		 'later still matches.',
		 ('/ui/dialogs/panebar/panebar_default/emptypanel',
		  '/ui/panes/panebar/*/emptypanel')),
	)

	# Pane bars come and go as the user splits panes, so a claim has to be
	# re-asserted rather than applied once. Only runs while something is
	# actually claimed.
	HEAL_FRAMES = 120

	# Pre-claim values, keyed by panel path. TD ships these panels EMPTY, so
	# anything found in one was put there by the user -- releasing a claim
	# must hand back exactly what was found, not blank it.
	ORIGINALS = 'Originals'

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		if self.ORIGINALS not in self.ownerComp.storage:
			self.ownerComp.store(self.ORIGINALS, {})
		self._healing = False

	def onInitTD(self):
		"""Build any missing parameters, then assert the skin."""
		run('args[0].EnsurePars()', self, delayFrames=1, delayRef=op.TDResources)
		run('args[0].Apply()', self, delayFrames=5, delayRef=op.TDResources)

	# --- parameters ---

	def EnsurePars(self):
		"""Create one TOP parameter per SKIN_TARGETS row, in order.

		Idempotent -- an existing parameter keeps its value, so this is safe
		on every init and after adding a row.
		"""
		for page_name, par_name, label, help_text, _ in self.SKIN_TARGETS:
			if getattr(self.ownerComp.par, par_name, None) is not None:
				continue
			page = next((p for p in self.ownerComp.customPages
						 if p.name == page_name), None)
			if page is None:
				page = self.ownerComp.appendCustomPage(page_name)
			p = page.appendTOP(par_name, label=label)[0]
			p.default = ''
			p.val = ''
			p.help = help_text
		# pages otherwise sit in whatever order they happened to be created
		# in (a page destroyed and remade lands last) -- pin them to the order
		# the rows are written in, which is the order a reader expects
		wanted = []
		for page_name, _, _, _, _ in self.SKIN_TARGETS:
			if page_name not in wanted:
				wanted.append(page_name)
		if [p.name for p in self.ownerComp.customPages][:len(wanted)] != wanted:
			self.ownerComp.sortCustomPages(*wanted)

	# --- applying ---

	def _targets(self, patterns):
		"""Live panels a parameter drives -- resolved fresh every time, since
		pane bars appear and disappear with pane splits."""
		found = []
		for panel in ops(*patterns):
			if panel is not None and panel.valid and getattr(panel.par, 'top', None) is not None:
				found.append(panel)
		return found

	def Apply(self):
		"""Push every skin parameter onto its targets, or restore if blank.

		Idempotent and safe to call from anywhere: a parameter holding a
		valid TOP claims its panels, a blank one hands them back to whatever
		was in them before this tool first touched them.
		"""
		originals = dict(self.ownerComp.fetch(self.ORIGINALS, {}, search=False))
		captured = False
		for _, par_name, _, _, patterns in self.SKIN_TARGETS:
			par = getattr(self.ownerComp.par, par_name, None)
			if par is None:
				continue
			top = par.eval()
			claimed = top is not None and getattr(top, 'valid', False)
			for panel in self._targets(patterns):
				target = panel.par.top
				if panel.path not in originals:
					originals[panel.path] = str(target.eval() or '')
					captured = True
				desired = top.path if claimed else originals[panel.path]
				if str(target.eval() or '') != str(desired or ''):
					try:
						target.val = desired
					except Exception as e:
						debug(f'FNS_UISkin: {par_name} -> {panel.path}: {e}')
		if captured:
			self.ownerComp.store(self.ORIGINALS, originals)
		self._armHeal()

	def _armHeal(self):
		"""Keep re-asserting while anything is claimed, so chrome TD rebuilds
		(a new pane bar, a reopened dialog) picks the skin up too."""
		if self._healing or not self.Claims:
			return
		self._healing = True
		run('args[0]._heal()', self, delayFrames=self.HEAL_FRAMES, delayRef=op.TDResources)

	def _heal(self):
		self._healing = False
		if not self.ownerComp.valid:
			return
		if self.Claims:
			self.Apply()

	def Release(self):
		"""Hand every target back to its pre-claim value and forget it.

		Blanks the parameters too, so a later Apply() re-captures from a
		clean slate. This is what to call before removing the tool.
		"""
		for _, par_name, _, _, _ in self.SKIN_TARGETS:
			par = getattr(self.ownerComp.par, par_name, None)
			if par is not None:
				par.val = ''
		self.Apply()
		self.ownerComp.store(self.ORIGINALS, {})

	@property
	def Claims(self):
		"""{par name: TOP path} for the parameters currently claiming a panel."""
		claims = {}
		for _, par_name, _, _, _ in self.SKIN_TARGETS:
			par = getattr(self.ownerComp.par, par_name, None)
			top = par.eval() if par is not None else None
			if top is not None and getattr(top, 'valid', False):
				claims[par_name] = top.path
		return claims

	@property
	def SkinnedPanels(self):
		"""{panel path: TOP path} -- every panel this tool is currently driving."""
		out = {}
		for _, par_name, _, _, patterns in self.SKIN_TARGETS:
			par = getattr(self.ownerComp.par, par_name, None)
			top = par.eval() if par is not None else None
			if top is None or not getattr(top, 'valid', False):
				continue
			for panel in self._targets(patterns):
				out[panel.path] = top.path
		return out
