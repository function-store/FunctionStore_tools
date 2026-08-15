# Embody pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/storage edits only). Scrubs all host-registration state so the
# released MainMenuRegistry ships inactive: it installs/updates the /sys
# global on first load but registers nothing until a user configures it.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key
# ('MainMenuRegistryExtStored'); legacy top-level keys scrubbed too.
for key in ('MainMenuRegistryExtStored', 'PaneRegistry', 'HostCanonical'):
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
p.Align = 'right'
p.Displayed = True
p.Callback = ''
p.Barwidth = 0
p.Helpurl = ''
p.Promotepars = True  # shippers may opt out per-tool; the bare registry ships with the default
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on
# never ship an external-tox binding (a copied binding silently reloads
# someone else's content -- paid for once)
p.enableexternaltox = False
p.externaltox = ''
