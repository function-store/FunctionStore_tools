"""Navbar Configurator -- the FNS_Hub tab that drives FNS_NavbarRegistry.

A thin surface description over ConfiguratorBase (the one configurator
implementation, next to this DAT in FNS_Hub). What is navbar-specific:
entries have a side (left/right of the path area) and a kind (widget /
overlay / logic), overrides land on the default bar template AND every live
pane bar, and only stock buttons unambiguously in the linear flow are
adopted (the pane bar's mode panels share alignorder 1.0, its overlays ride
layer 1, `panenav` is the fill pivot).

Persistence model:
- Tool/chrome entries: their HOST publishers persist side/order/display
  (the registry writes manager edits back to host pars).
- Built-in (stock pane bar) show overrides: THIS component owns them, in
  the `state` table, re-applied on every start (/ui and /sys do not
  persist) and roamed by the hub's config_callbacks.
"""

ConfiguratorBase = mod('../ConfiguratorBase').ConfiguratorBase


class ConfiguratorExt(ConfiguratorBase):

	CFG_NAME = 'NavbarConfigurator'
	REGISTRY_SHORTCUT = 'FNS_NAVBARREGISTRY'
	REGISTRY_EXT = 'NavbarRegistryExt'
	REGISTRY_NAME = 'FNS_NavbarRegistry'
	BAR_PATH = '/ui/dialogs/panebar/panebar_default'
	PANE_BARS_PATH = '/ui/panes/panebar'
	ITEM_PREFIX = 'nbitem_'
	HUB_TAB = 'navbar'
	ORIGIN_PANE = 'nbcfg_origin'
	PKG_LABEL = 'navbar package'
	BUILTIN_NOUN = 'built-in pane-bar buttons'
	OWN_NOUN = 'items and groups'

	HAS_SIDES = True
	HAS_KINDS = True
	STAMP_EXTRA_PARS = {'Align': 'right', 'Kind': 'widget'}

	def _adoptCall(self, api, o, stored, disp):
		api.AdoptBarWidget(o.name, side='left', order=stored, display=disp)
