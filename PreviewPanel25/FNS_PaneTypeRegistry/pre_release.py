# Pre-release hook -- runs on the STAGED COPY before the portable tox is
# written (extensions NOT initialized there; direct par/storage edits only).
#
# This is what makes the unbind-save-rebind dance unnecessary. The DEV copy
# keeps its file bindings (scripts/shared/RegistryBase.py and this package's
# own .py files) so edits hot-reload normally; the RELEASED artifact gets
# those bindings stripped here, so it ships with the text embedded and
# nothing repo-relative to dangle in a foreign project or in the Palette.
#
# args[0] = resolved save path.

comp = me.parent()

# --- ship standalone: no repo-relative file references, text embedded ---
for _dat in comp.findChildren(type=DAT):
	_fp = getattr(_dat.par, 'file', None)
	if _fp is None or not _fp.eval():
		continue
	try:
		_dat.par.syncfile = False
		_dat.par.loadonstart = False
		_dat.par.write = False
		_fp.mode = ParMode.CONSTANT
		_fp.val = ''
	except Exception:
		pass
	# tracker identities belong to this repo, not to the shipped copy
	for _tag in ('FNS_externalized', 'py', 'tdn', 'pi_suspect'):
		if _tag in _dat.tags:
			_dat.tags.remove(_tag)

# --- ship inert: install/upgrade the /sys global, register nothing ---
# StorageManager keeps its items inside one container key.
for key in ('PaneTypeRegistryExtStored', 'PaneRegistry', 'HostCanonical'):
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
p.Callback = ''
p.Promotepars = False  # shippers may opt out per-tool; the bare registry ships with the default
p.opshortcut = ''
p.clone = ''          # never ship with in-project cloning on

# never ship bound to this repo's suspect tox
p.enableexternaltox = False
p.externaltox = ''

for _tag in ('pi_suspect', 'tdn'):
	if _tag in comp.tags:
		comp.tags.remove(_tag)
