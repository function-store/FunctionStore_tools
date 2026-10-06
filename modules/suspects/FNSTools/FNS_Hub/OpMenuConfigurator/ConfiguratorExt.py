"""OpMenu Configurator -- the FNS_Hub tab that drives FNS_OpMenuRegistry.

The OP Create dialog has no bar: its registry holds CONTRIBUTIONS (search
words, row decorations, right-click items, filter stages) published by
tools, each with an order and a display flag. This tab lets the user
reorder and enable/disable those contributions. No sides, no dividers, no
groups, no built-ins, no drop-to-register (a contribution needs a callbacks
DAT to contribute anything -- a bare stamped host would be noise).

ConfiguratorBase expects the RegistryBase widget model (Widgets /
WidgetSequence / SetWidgetSequence / SetWidgetDisplay); _OpMenuApi adapts
the OpMenu manager API to exactly that shape, so the base runs unchanged.
The state table stays empty: every contribution has a host publisher that
persists its own order/display, so there is nothing this component owns.
"""

ConfiguratorBase = mod('../ConfiguratorBase').ConfiguratorBase


class _OpMenuApi:
	"""FNS_OpMenuRegistry seen through the widget model the base reads."""

	def __init__(self, reg):
		self._reg = reg
		self.stored = {'PaneRegistry': {}}   # nothing virtual lives here

	@property
	def Widgets(self):
		out = {}
		for name, info in (self._reg.Contributors or {}).items():
			d = dict(info)
			d.setdefault('display', '1')
			d.setdefault('menu_order', '0')
			out[name] = d
		return out

	@property
	def WidgetSequence(self):
		def key(item):
			name, info = item
			try:
				return (int(info.get('menu_order', 0)), name.lower())
			except (TypeError, ValueError):
				return (1 << 30, name.lower())
		return [n for n, _ in sorted(self.Widgets.items(), key=key)]

	@property
	def Groups(self):
		return {}

	def _registeredNamesInOrder(self):
		return self.WidgetSequence

	def _isGroupMarker(self, info):
		return False

	def _scanGroups(self, names):
		return {}, []

	def GroupPath(self, name):
		return ''

	def GroupVisible(self, gid):
		return True

	def SetWidgetSequence(self, names):
		for i, n in enumerate(names):
			self._reg.SetContributorOrder(n, i)
		self._reg.Resync()

	def SetWidgetDisplay(self, name, visible):
		self._reg.SetContributorDisplay(name, bool(visible))
		self._reg.Resync()

	def WidgetTarget(self, name):
		info = (self._reg.Contributors or {}).get(name) or {}
		p = info.get('panel_path')
		return op(p) if p else None

	def OpenDocs(self, name):
		return self._reg.OpenDocs(name)

	def _syncSurface(self):
		self._reg.Resync()


class ConfiguratorExt(ConfiguratorBase):

	CFG_NAME = 'OpMenuConfigurator'
	REGISTRY_SHORTCUT = 'FNS_OPMENUREGISTRY'
	REGISTRY_EXT = 'OpMenuRegistryExt'
	REGISTRY_NAME = 'FNS_OpMenuRegistry'
	BAR_PATH = ''                      # no bar: the surface is TD's OP Create dialog
	HUB_TAB = 'opmenu'
	ORIGIN_PANE = 'omcfg_origin'
	PKG_LABEL = 'OP menu contribution'

	HAS_GROUPS = False
	SUPPORTS_DROP = False
	ADOPTS_BUILTINS = False

	def _api(self):
		reg = getattr(op, self.REGISTRY_SHORTCUT, None)
		if reg is not None and hasattr(reg.ext, self.REGISTRY_EXT):
			return _OpMenuApi(getattr(reg.ext, self.REGISTRY_EXT))
		return None

	def _originOf(self, info):
		# the contributing TOOL, not the host's parent path segment
		p = info.get('panel_path', '')
		parts = [x for x in p.split('/') if x]
		return parts[-1] if parts else 'chrome'

	def _showBuiltins(self):
		return False

	def _adoptCall(self, api, o, stored, disp):
		pass
