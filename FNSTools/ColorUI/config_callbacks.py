"""ConfigRegistry callbacks for ColorUI.

Persists the ACTIVE palette state -- the 'colors' overrides dict -- so UI
colors follow the user across projects and survive toolkit updates.
Restore stores the dict back and re-applies it through the extension,
gated on the tool's Autoload toggle. ColorUI's File Import/Export stays
as the user-facing palette exchange.
"""


def onConfigSave():
	tool = me.parent()
	out = {}
	colors = tool.fetch('colors', None, search=False)
	if colors:
		out['colors'] = dict(colors)
	return out


def onConfigLoad(data):
	tool = me.parent()
	colors = data.get('colors')
	# legacy configs from the par-sequence UI kept families separately
	fams = data.get('fam_colors')
	merged = {}
	if colors:
		merged.update(colors)
	if fams:
		merged.update(fams)
	if merged:
		tool.store('colors', merged)
		if tool.par.Autoload.eval():
			ext = tool.ext.ExtColorUI
			ext.ApplyOverrides()
			ext.SendState()
	return
