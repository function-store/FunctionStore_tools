# Embody pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/storage edits only). Scrubs all host-registration state so the
# released NavbarRegistry ships inactive: it installs/updates the /sys
# global on first load but registers nothing until a user configures it.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key
# ('NavbarRegistryExtStored'); legacy top-level keys scrubbed too.
for key in ('NavbarRegistryExtStored', 'PaneRegistry', 'HostCanonical'):
	if key in comp.storage:
		comp.unstore(key)

p = comp.par
p.Autoregister = False
p.Canonicalname = ''
p.Regstatus.val = ''
p.Comp = '..'
p.Menuorder = -1
p.Align = 'right'
p.Kind = 'widget'
p.Displayed = True
p.Callback = ''
p.Barwidth = 0
p.Helpurl = ''
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on
# never ship an external-tox binding (a copied binding silently reloads
# someone else's content -- paid for once)
p.enableexternaltox = False
p.externaltox = ''
