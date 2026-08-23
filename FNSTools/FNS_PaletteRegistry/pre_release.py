# Pre-release hook -- runs on the STAGED COPY before the portable tox is
# written (extensions NOT initialized there; direct par/storage edits only).
# Scrubs all host-registration state so the released FNS_PaletteRegistry
# ships inert: it installs/updates the /sys global on first load but
# registers no tab until a tool configures a host.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key; legacy top-level
# keys and lineage relics scrubbed too.
for key in ('PaletteRegistryExtStored', 'PaneRegistry', 'HostCanonical'):
	if key in comp.storage:
		comp.unstore(key)

# hosts ship with Registration pars BOUND to the tool's Registry page;
# the staged copy has no tool above it -- unbind before scrubbing
for _page in comp.customPages:
	if _page.name == 'Registration':
		for _p in _page.pars:
			try:
				_p.mode = ParMode.CONSTANT
			except Exception:
				pass

p = comp.par
p.Autoregister = False
p.Canonicalname = ''
p.Regstatus.val = ''
p.Comp = '..'
p.Panel = '..'
p.Callback = ''
p.Tablabel = ''
p.Taborder = 50
p.Displayed = True
p.Promotepars = False

# extra tabs are the DEV's configuration, never the shipped default. TD keeps
# a minimum of one block, so reset to a single empty one (empty Canonical
# Name = no tab).
try:
	_seq = comp.seq.Tab
	_seq.numBlocks = 1
	_b = _seq[0]
	_b.par.Name = ''
	_b.par.Source = ''
	_b.par.Label = ''
	_b.par.Order = 50
	_b.par.Shown = True
except Exception:
	pass
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on

# never ship bound to a dev project's suspect tox
p.enableexternaltox = False
p.externaltox = ''
if 'pi_suspect' in comp.tags:
	comp.tags.remove('pi_suspect')

# the strip and mirrors are runtime-only state in /ui on the /sys global;
# a master never carries surface ops, but a copy taken from a global would
for _o in list(comp.ops('fnspal_*')):
	try:
		_o.destroy()
	except Exception:
		pass
