"""MainMenu Configurator -- the FNS_Hub tab that drives FNS_MainMenuRegistry.

A thin surface description over ConfiguratorBase (the one configurator
implementation, next to this DAT in FNS_Hub). What is main-menu-specific:
entries have a side (left/right of the stretchy `stringfield` pivot), and
the stock left-cluster items (wiki .. realtime) are AUTO-ADOPTED so entries
can be ordered between them. First adoption seeds the whole left sequence
from the items' LIVE X POSITIONS -- alignorder alone cannot order the bar's
duplicate-alignorder pair (gpuUsage/realtime both 3.4), but pixels can --
and anchors that pointed at a now-adopted item are cleared (ordering
expresses the position from here on). The File/Edit menu strip, the
stringfield pivot and the OpFamUI/update corner stay unmanaged landmarks.

Persistence model:
- Tool entries: their HOST publishers persist side/order/display (the
  registry writes manager edits back to host pars).
- Adopted built-ins' order/display (+ td_order for Restore): THIS component
  owns them, in the `state` table, re-applied on every start (/ui and /sys
  do not persist) and roamed by the hub's config_callbacks.
"""

ConfiguratorBase = mod('../ConfiguratorBase').ConfiguratorBase


class ConfiguratorExt(ConfiguratorBase):

	CFG_NAME = 'MainMenuConfigurator'
	REGISTRY_SHORTCUT = 'FNS_MAINMENUREGISTRY'
	REGISTRY_EXT = 'MainMenuRegistryExt'
	REGISTRY_NAME = 'FNS_MainMenuRegistry'
	BAR_PATH = '/ui/dialogs/mainmenu'
	ITEM_PREFIX = 'mmitem_'
	HUB_TAB = 'mainmenu'
	ORIGIN_PANE = 'mmcfg_origin'
	PKG_LABEL = 'main-menu package'
	BUILTIN_NOUN = 'built-in menu-bar items'
	OWN_NOUN = 'items and groups'

	HAS_SIDES = True
	STAMP_EXTRA_PARS = {'Align': 'right'}
	# layer is NOT part of the adoption filter (only pivot detection):
	# gpuUsage rides layer 5 yet aligns like any fixed item -- the pane bar's
	# layer==0 rule would strand it as an unmanageable landmark in the middle
	# of the managed run. Duplicate alignorders are allowed; live X resolves
	# ties the way the user actually sees them.
	ADOPT_LAYER0_ONLY = False
	ADOPT_UNIQUE_ALIGNORDER = False
	ADOPT_SORT_BY_X = True

	def _resolveAdopted(self, bar, info):
		p = info.get('panel_path')
		return op(p) if p else None

	def _adoptCall(self, api, o, stored, disp):
		api.AdoptBarWidget(o, o.name, side='left', order=stored, display=disp)

	def _adoptBuiltins(self, api):
		"""Adoption with a position snapshot: SNAPSHOT the on-screen order
		BEFORE adopting anything -- every AdoptBarWidget re-flows the bar,
		so positions read mid-adoption are churn, not truth (paid for once:
		entries jumped ahead of `wiki` because their mirrors had already
		moved)."""
		if api is None:
			return
		existing = api.Widgets
		fresh = [o for o in self._adoptCandidates() if o.name not in existing]
		if not fresh:
			return
		bar = op(self.BAR_PATH)
		left_x = [(o.x, o.name) for o in fresh]
		for name, info in existing.items():
			if info.get('side', 'right') != 'left':
				continue
			o = (self._resolveAdopted(bar, info) if info.get('adopted') == '1'
				 else bar.op(api._mirrorName(name)))
			if o is not None:
				left_x.append((o.x, name))
		left_x.sort()
		unordered = []
		for o in fresh:
			row = self._stateRow(o.name) or {}
			disp = bool(o.par.display.eval()) if hasattr(o.par, 'display') else True
			td_order = row.get('td_order') or ''
			if not td_order:
				try:
					td_order = str(float(o.par.alignorder.eval()))
				except Exception:
					td_order = ''
			self._writeState('builtin', o.name, display=1 if disp else 0,
							 td_order=td_order, side='left')
			stored = (self._stateRow(o.name) or {}).get('order')
			self._adoptCall(api, o, int(stored) if stored else None, disp)
			if not stored:
				unordered.append(o.name)
		if unordered:
			# first adoption: seed the left sequence from the snapshot, so
			# the bar keeps exactly the order the user was looking at
			rest = [n for n in api.WidgetSequence
					if n not in {n2 for _, n2 in left_x}]
			self.PushSequence([n for _, n in left_x] + rest)
			for name, info in api.Widgets.items():
				if info.get('anchor') and info['anchor'] in {o.name for o in fresh}:
					api.SetWidgetAnchor(name, None)
