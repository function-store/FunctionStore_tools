# Pre-release hook -- runs on the STAGED COPY before the portable tox is
# written (extensions NOT initialized there; direct par/storage edits only).
# Scrubs all host-registration state so the released FNS_HubRegistry ships
# inactive: it installs/updates the /sys global on first load but publishes
# no tab until a tool configures a host.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key; legacy top-level
# keys and lineage relics scrubbed too.
for key in ('HubRegistryExtStored', 'PaneRegistry', 'HostCanonical', 'post_update'):
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
p.Tabcontent = ''
p.Tabparams = ''
p.Tablabel = ''
p.Taborder = 50
p.Helpurl = ''
p.Promotepars = False
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on

# never ship bound to this repo's suspect tox
p.enableexternaltox = False
p.externaltox = ''
if 'pi_suspect' in comp.tags:
	comp.tags.remove('pi_suspect')
