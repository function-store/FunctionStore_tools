# Pre-release hook -- runs on the STAGED COPY before the portable tox is
# written (extensions NOT initialized there; direct par/storage edits only).
# Scrubs all host-registration state so the released ConfigRegistry ships
# inactive: it installs/updates the /sys global on first load but registers
# nothing until a user configures it.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key
# ('ConfigRegistryExtStored'); legacy top-level keys and lineage relics
# (containers inherited from the master this registry was copied from)
# scrubbed too.
for key in ('ConfigRegistryExtStored', 'PaneRegistry', 'HostCanonical',
            'ToolbarRegistryExtStored', 'OpMenuRegistryExtStored'):
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
p.Callback = ''
p.Autoload = True
p.Persistpars = True
p.Excludepars = ''
p.Excludepages = ''
p.Promotepars = False  # shippers may opt out per-tool; the bare registry ships with the default
p.Configfile = ''
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on

# never ship bound to this repo's suspect tox
p.enableexternaltox = False
p.externaltox = ''
