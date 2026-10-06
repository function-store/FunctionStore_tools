# Pre-release hook -- runs on the STAGED COPY before the portable tox is
# written (extensions NOT initialized there; direct par/storage edits only).
# Scrubs all host-registration state so the released FNS_Console ships
# inactive: it installs/updates the /sys global on first load but registers
# no tab until a tool configures a host.
# args[0] = resolved save path.

comp = me.parent()

# StorageManager keeps its items inside one container key; legacy top-level
# keys and lineage relics scrubbed too.
for key in ('ConsoleRegistryExtStored', 'PaneRegistry', 'HostCanonical'):
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
p.Tabpage = ''
p.Tabapi = ''
p.Localbrowser = ''
p.Tablabel = ''
p.Taborder = 50
p.Promotepars = False
p.opshortcut = ''
p.clone = ''  # never ship with in-project cloning on

# never ship bound to this repo's suspect tox
p.enableexternaltox = False
p.externaltox = ''

# the server is runtime-only state on the /sys global; a master never
# carries one, but a copy taken from a global would
_srv = comp.op('console_server')
if _srv is not None:
	_srv.par.active = False
	_srv.destroy()

# The generic FNS strip runs LAST, after this package's own scrub: root-panel
# binds frozen, web servers pinned to loopback, vc_data / Version Ctrl pages
# gone, stubser logs cleared, console exposure dormant, FNS_About.Owner an
# expression. Every package runs it; the 25 that did not shipped their PI
# bookkeeping and dev-project paths in v3.1.3 (packaging/pre_release_common.py).
exec(open('packaging/pre_release_common.py').read())
