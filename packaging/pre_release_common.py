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

# --- retire root-panel bindings from the artifact ------------------------
# Authored tools bind pars to hand-made control pars on the toolkit ROOT
# (parent.FNS.par.*). No install target has those pars, so shipped binds
# dangle and every install cooks with errors. Freeze them to their stored
# constant: the ConfigRegistry settings UI is the control surface installs
# get instead.
#
# DELIBERATELY `.val`, never `.eval()`: evaluating a dangling reference on
# the same-frame staged copy aborts the whole hook run at a level no
# `except` in this file can catch (cost a day -- v2.12.1 shipped three
# stale artifacts because of it). The stored constant is also the better
# value: it is the authored default, not whatever the author's live root
# panel happened to be set to at export time.
for _c in [_c0] + _c0.findChildren(type=COMP):
    for _p in _c.customPars:
        try:
            _bound = _p.bindExpr and 'parent.FNS' in _p.bindExpr
            _exprd = (_p.mode == ParMode.EXPRESSION and _p.expr
                      and 'parent.FNS' in _p.expr)
            if not (_bound or _exprd):
                continue
            _v = _p.val
            _p.mode = ParMode.CONSTANT
            _p.val = _v
        except Exception:
            pass

for _t in _c0.findChildren(name='vc_data', type=tableDAT):
    try:
        _t.destroy()
    except Exception:
        pass

# --- scrub baked log data from vendored ExtUtils copies -------------------
# The QuickExt stub machinery (ExtUtils/extStubser) rides inside FNS_About
# and registry hosts across the fleet, and its logger tables still carry
# 2024 log lines from the author's 2023 project -- dead bytes in every
# artifact and a checkout-path leak. Clear them on the staged copy.
for _d in _c0.findChildren(type=DAT):
    try:
        if 'extStubser' in _d.path and _d.name in ('out1', 'logger'):
            _d.clear()
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
