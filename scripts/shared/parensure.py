"""parensure -- ensure custom parameters from code, declaratively.

Each parameter is one dict; EnsurePars() walks the declarations in
order, creates what is missing, corrects style drift (a declaration
whose style changed destroys and recreates the par), refreshes
label / help / ranges / menus every init, and never touches the value
or mode of a parameter that already exists -- so user edits, bindings
and expressions survive every reinit.

Newly created numeric parameters get their VALUE set to the declared
default: TD creates custom pars at 0 (or the clamped minimum), not at
their default, and a page full of zeroed speeds reads as broken.

Adapted from alphamoonbase's tdp-TouchUtilCollection ensure pattern
(EnsureExtension / parfield), reduced to the dict-driven core this
project needs. Shared on disk between GeoPilot and, later, other
components of the opSequencer family -- see
briefs/2026-08-28-geopilot-split.md.

Single-value styles only (Float, Int, Str, Toggle, Pulse, Menu,
StrMenu, OP-family, File, Folder, Header). Multi-value ParGroups
(XYZ, RGB) are not handled here.

A declaration:

    {'name': 'Movespeed', 'style': 'Float', 'page': 'Pilot',
     'label': 'Move Speed', 'default': 5.0,
     'min': 0.0, 'clampMin': True, 'normMin': 0.0, 'normMax': 20.0,
     'help': 'Units per second at full deflection.',
     'startSection': True}

Menu styles add 'menuNames' (and optionally 'menuLabels').
"""

# attributes copied onto the par whenever declared, new or not
ATTRS = ('label', 'default', 'min', 'max', 'clampMin', 'clampMax',
         'normMin', 'normMax', 'help', 'startSection', 'order',
         'readOnly', 'enableExpr', 'menuSource')

# styles whose pars carry no persistent value to seed
VALUELESS = ('Pulse', 'Momentary', 'Header')


def EnsurePage(comp, name):
	"""The named custom page, created at the end if missing."""
	for page in comp.customPages:
		if page.name == name:
			return page
	return comp.appendCustomPage(name)


def EnsurePars(comp, decls):
	"""Ensure every declared parameter exists on comp. Returns how many
	were newly created."""
	created = 0
	for d in decls:
		created += _ensureOne(comp, d)
	return created


def _ensureOne(comp, d):
	page = EnsurePage(comp, d['page'])
	par = comp.par[d['name']]
	if par is not None and par.style != d['style']:
		par.destroy()
		par = None
	isNew = par is None
	if isNew:
		getattr(page, 'append' + d['style'])(d['name'])
		par = comp.par[d['name']]
	if par.page != page:
		par.page = page
	for a in ATTRS:
		if a in d:
			setattr(par, a, d[a])
	if 'menuNames' in d:
		par.menuNames = list(d['menuNames'])
		par.menuLabels = list(d.get('menuLabels', d['menuNames']))
	if isNew and 'default' in d and d['style'] not in VALUELESS:
		par.val = d['default']
	return 1 if isNew else 0
