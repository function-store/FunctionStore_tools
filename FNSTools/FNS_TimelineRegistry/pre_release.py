# Embody pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/storage edits only). Scrubs all host-registration state so the
# released TimelineRegistry ships inactive: it installs/updates the /sys
# global on first load but registers nothing until a user configures it.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key
# ('TimelineRegistryExtStored'); legacy top-level keys scrubbed too.
for key in ('TimelineRegistryExtStored', 'PaneRegistry', 'HostCanonical'):
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
p.Menuorder = -1
p.Displayed = True
p.Barwidth = 0
p.Barheight = 0
p.Zone = 'transport'
p.Callback = ''
p.Promotepars = False  # shippers may opt out per-tool; the bare registry ships with the default
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on

# never ship bound to this repo's suspect tox, and never ship wearing this
# repo's tracker tag -- Private Investigator must not adopt a stray copy that
# landed in someone else's project.
p.enableexternaltox = False
p.externaltox = ''
comp.tags = [t for t in comp.tags if t != 'pi_suspect']
