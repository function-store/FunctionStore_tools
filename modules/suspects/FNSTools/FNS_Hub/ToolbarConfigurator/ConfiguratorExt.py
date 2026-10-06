"""Toolbar Configurator -- the FNS_Hub tab that drives FNS_ToolbarRegistry.

A thin surface description over ConfiguratorBase (the one configurator
implementation, next to this DAT in FNS_Hub). What is toolbar-specific:
dividers and widths (both owned here), TD's own bar icons adopted from the
bar's `emptypanel` anchor, no sides.

Persistence model:
- Tool/chrome entries: their HOST publishers persist order/display/width
  (the registry writes manager edits back to host pars).
- Dividers + built-in overrides: THIS component owns them, in the `state`
  table, republished/re-applied on every start (/ui and /sys do not
  persist) and roamed by the hub's config_callbacks.
"""

ConfiguratorBase = mod('../ConfiguratorBase').ConfiguratorBase


class ConfiguratorExt(ConfiguratorBase):

	CFG_NAME = 'ToolbarConfigurator'
	REGISTRY_SHORTCUT = 'FNS_TOOLBARREGISTRY'
	REGISTRY_EXT = 'ToolbarRegistryExt'
	REGISTRY_NAME = 'FNS_ToolbarRegistry'
	BAR_PATH = '/ui/dialogs/bookmark_bar'
	ITEM_PREFIX = 'tbmirror_'
	HUB_TAB = 'toolbar'
	ORIGIN_PANE = 'tbcfg_origin'
	PKG_LABEL = 'toolbar package'
	BUILTIN_NOUN = 'built-in icons'
	OWN_NOUN = 'buttons, dividers and groups'

	HAS_DIVIDERS = True
	HAS_WIDTH = True

	# kind, name, order, width, display
	DEFAULT_STATE = (
		('divider', 'Divider1', '1', '33', '1'),
		('divider', 'Divider2', '8', '3', '1'),
		('divider', 'Divider3', '13', '3', '1'),
		('divider', 'Divider4', '16', '3', '1'),
		('divider', 'Divider5', '20', '3', '1'),
		('divider', 'Divider6', '23', '3', '1'),
	)

	def _builtinWidgets(self):
		"""Panels anchored to the bar's emptypanel that are not our mirrors."""
		bar = op(self.BAR_PATH)
		ep = bar.op('emptypanel') if bar else None
		if ep is None:
			return []
		out = []
		for conn in ep.outputCOMPConnectors[0].connections:
			o = conn.owner
			if o is None or not o.valid or o.name.startswith(self.ITEM_PREFIX) or o is ep:
				continue
			out.append(o)
		out.sort(key=lambda o: float(o.par.alignorder.eval()) if hasattr(o.par, 'alignorder') else 0.0)
		return out

	def _adoptCandidates(self):
		# every bar icon is adoptable: the bookmark bar is a simple row
		return self._builtinWidgets()

	def _adoptCall(self, api, o, stored, disp):
		api.AdoptBarWidget(o, o.name, order=stored, display=disp)
