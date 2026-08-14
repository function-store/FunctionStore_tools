# Generic FNS pre-release strip -- exec'd by every package's `pre_release`
# hook (a one-liner stamped on all 39 packages):
#
#     exec(open('packaging/pre_release_common.py').read())
#
# Runs on the STAGED COPY in /sys/quiet (extensions not initialized there;
# par/table edits only), so the live component is never touched. Exports
# only ever happen from the source checkout, so the relative open() always
# resolves.
#
# Private Investigator's apparatus is authoring-side only: the `Version
# Ctrl` page fronts `vc_data`, and both describe THIS checkout's save
# history, not the artifact. `Pkgversion` (About page) is the shipped
# version story; a second, stale one would just invite confusion.
#
# Pars are destroyed BEFORE their page: TD relocates a destroyed page's
# surviving pars onto another page instead of deleting them.

_c0 = me.parent()

for _t in _c0.findChildren(name='vc_data', type=tableDAT):
    try:
        _t.destroy()
    except Exception:
        pass

for _c in [_c0] + _c0.findChildren(type=COMP):
    for _pg in list(_c.customPages):
        if _pg.name != 'Version Ctrl':
            continue
        for _p in list(_pg.pars):
            try:
                _p.destroy()
            except Exception:
                pass
        try:
            _pg.destroy()
        except Exception:
            pass
