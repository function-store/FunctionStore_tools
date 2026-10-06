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

# --- Envoy's bot never ships ------------------------------------------------
# Envoy draws its bot as envoy_bot_* annotate COMPs into whatever network a
# pane has open, and a tox saved while a pane showed the tool carries all
# of them (ComplexOp's first save did, 2026-09-23). The three sequencer
# hooks stripped them one by one; this is the fleet-wide backstop.
for _bot in _c0.findChildren(name='envoy_bot*', includeUtility=True):
    try:
        _bot.destroy()
    except Exception:
        pass

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

# --- no shipped web server listens beyond loopback ------------------------
# A Web Server DAT with a BLANK Local Address listens on EVERY interface
# (Derivative: "When left blank, the Web Server DAT will listen on all
# interfaces"). Every server in this toolkit builds 127.0.0.1 URLs and has no
# authentication, so a blank value shipped an unauthenticated surface to the
# whole LAN. The owning extensions now re-assert this at ensure/Configure
# time; this is the backstop that makes it true of the ARTIFACT regardless of
# which code path created the DAT, or how old the staged copy's server is.
for _ws in _c0.findChildren(type=webserverDAT):
    try:
        _p = _ws.par.localaddress
        if _p.mode != ParMode.CONSTANT:
            _p.mode = ParMode.CONSTANT
        _p.val = '127.0.0.1'
    except Exception:
        pass

for _t in _c0.findChildren(name='vc_data', type=tableDAT):
    try:
        _t.destroy()
    except Exception:
        pass

# --- FNS_About.Owner names the COMP it sits in, never a dev-project path --
# FNS_About copies are stamped, not cloned (every one has an empty clone
# master), and 56 of 57 in the dev project carry Owner as a CONSTANT -- 20
# of them the absolute path of the tool inside THIS checkout. Nothing in the
# toolkit reads Owner any more (the retired stub generator did), but a
# constant absolute path warns "Invalid path" in any project where the tool
# lands elsewhere: the launcher's carried registries, a renamed toolkit
# root, a `placement: root` package. Ship it as the expression that is true
# everywhere; the dev copies stay as they are until a fleet sweep.
for _fa in _c0.findChildren(name='FNS_About', type=COMP):
    _p = getattr(_fa.par, 'Owner', None)
    if _p is None:
        continue
    try:
        _p.expr = 'parent()'
        _p.mode = ParMode.EXPRESSION
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

# --- console exposure ships DORMANT; the install rail enables it ----------
# A tool that contributes an FNS_Console tab carries a console host. A
# registry host bootstraps its own /sys global in a bare project -- right for
# a toolbar button (it adds capability), wrong for the console, whose
# exposure REMOVES a local surface: the host switches the tool's own web
# render off once the console serves the page. Shipped with Expose on, a
# standalone ColorUI drop would raise a console nobody asked for and kill
# its own panel.
#
# So every artifact ships with Expose off, and ONE artifact serves both
# regimes: a standalone drop stays in local mode; a toolkit install flips
# Expose on as it lands the package (InstallerExt.ExposeConsoleHosts). The
# flag lives on the tool's Registry page, which the config registry
# persists, so after that first decision the user's own choice roams and
# survives updates. Rule, for any future surface with the same property:
# a host whose exposure takes a local surface away ships dormant and is
# enabled by the install rail, never by bootstrapping itself.
for _c in [_c0] + _c0.findChildren(type=COMP):
    _host = _c.op('FNS_Console') if _c.name != 'FNS_Console' else None
    if _host is None:
        continue
    for _owner, _name in ((_c, 'Csautoregister'), (_host, 'Autoregister')):
        _p = getattr(_owner.par, _name, None)
        if _p is None:
            continue
        try:
            if _p.mode != ParMode.CONSTANT:
                _p.mode = ParMode.CONSTANT
            _p.val = False
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

# --- About is the last custom page ----------------------------------------
# With Version Ctrl gone, About closes the parameter dialog: the tool's own
# pages first, credit and version last. Pages land in creation order, so one
# added after About while authoring rode into the artifact ahead of it
# (measured 2026-10-01: FNS_OpSequencer shipped About before Easing,
# FNS_OpMenuRegistry before Alternatives). The other pages keep their order.
# Plain loops: this file runs under exec(), where a comprehension cannot see
# the script's own names.
for _c in [_c0] + _c0.findChildren(type=COMP):
    _names = []
    for _pg in _c.customPages:
        _names.append(_pg.name)
    if 'About' not in _names or _names[-1] == 'About':
        continue
    _order = []
    for _n in _names:
        if _n != 'About':
            _order.append(_n)
    _order.append('About')
    try:
        _c.sortCustomPages(*_order)
    except Exception as _e:
        try:
            op.Embody.Log('pre_release: could not move About last on %s: %s' % (_c.path, _e), 'WARNING')
        except Exception:
            pass

# --- a tool opens on its FIRST custom page --------------------------------
# The page a parameter dialog opens on is whatever the AUTHOR last clicked,
# and it rides into the artifact like any other live state: measured
# 2026-09-18, FNS_ColorUI shipped opening on `Registry` when its first custom
# page is `ColorUI`. Runs LAST, after the Version Ctrl page is destroyed --
# destroying the current page is exactly what would leave this dangling.
try:
    _pages = list(_c0.customPages)
    if _pages:
        _c0.currentPage = _pages[0]
except Exception:
    pass

# --- no artifact ships the author's atmosphere ----------------------------
# A package whose ROOT is a real object (a Camera COMP, a Geometry COMP) has
# every built-in of that operator in the artifact, and those are SCENE state,
# not package content. FNS_CamSequencer shipped fog 'linear' with fognear 700
# and fogfar 5200 straight out of the author's project, so every install
# arrived with atmosphere on a camera nobody asked to be foggy (reported by a
# user, 2026-09-18).
#
# Fog only, deliberately. A blanket reset of built-ins would be the wrong
# cure: a panel COMP's size, a TOP's resolution and a camera's projection are
# all things a tool legitimately authors. Fog is the one that is never the
# tool's business. Anything else per-package, in that package's own hook.
for _c in [_c0] + _c0.findChildren(type=COMP):
    _p = getattr(_c.par, 'fog', None)
    if _p is None:
        continue
    try:
        if _p.mode != ParMode.CONSTANT:
            _p.mode = ParMode.CONSTANT
        _p.val = _p.default
    except Exception:
        pass

# --- no artifact ships a config-file override -----------------------------
# Configfile (Config page, every ConfigRegistry master and host) redirects the
# aggregated settings JSON away from <palette>/FNSTools/config. The author's
# development project points its master at FNStools_config.dev.json so its
# settings stop roaming into every project where the toolkit is merely USED
# (owner, 2026-09-30). That value must never leave the dev checkout: shipped
# in FNS_ConfigRegistry it would move every user's settings to a file named
# for a development setup, and StampHost copies the master, so a host stamped
# inside the dev project would carry it into whichever package received it.
# Reset to the default on the staged copy, wherever it appears. Empty is the
# only value a user install should ever arrive with.
for _c in [_c0] + _c0.findChildren(type=COMP):
    _p = getattr(_c.par, 'Configfile', None)
    if _p is None:
        continue
    try:
        # CONSTANT mode alone is not enough: TD keeps the expression text
        # on the par, dormant, and one click on the expression toggle in a
        # user's parameter dialog would bring the dev path back. Measured on
        # an export read-back, 2026-09-30. Clear the text, then pin the value.
        _p.expr = ''
        _p.mode = ParMode.CONSTANT
        _p.val = _p.default
    except Exception:
        pass

# --- no artifact ships a development twin folder --------------------------
# The development project keeps its user data in `_dev` twins of the
# palette folders it would otherwise share with the projects where the
# toolkit is merely used: OpTemplates_dev/ for the template library,
# tables_dev/ for the hotkey table (owner, 2026-09-30; docs/ConfigScope.md).
# Those paths live in DAT `file` expressions and in the OpTemplates base's
# `externaltox`, and a shipped one would send every user's edits to a folder
# named for a development setup. Rewrite any `/FNSTools/<name>_dev/` back to
# `/FNSTools/<name>/` on every operator in the package, DATs included, which is
# why this walks all children and not just COMPs. ExternalTables keeps the
# folder as a bare `FNSTools/tables_dev` in its Foldername par, with no slash
# on either side, so the match ends at a slash OR the end of the value (and a
# name that merely starts with `_dev`, like `tables_devices`, is left alone).
import re as _re
_DEV_TWIN = _re.compile(r'FNSTools/([A-Za-z0-9]+)_dev(?=/|$)')
for _o in [_c0] + _c0.findChildren():
    for _pn in ('file', 'externaltox', 'folder', 'Foldername'):
        _p = getattr(_o.par, _pn, None)
        if _p is None:
            continue
        try:
            if _p.mode == ParMode.EXPRESSION and _DEV_TWIN.search(_p.expr or ''):
                _p.expr = _DEV_TWIN.sub(r'FNSTools/\1', _p.expr)
            elif _p.mode == ParMode.CONSTANT and _DEV_TWIN.search(str(_p.val)):
                _p.val = _DEV_TWIN.sub(r'FNSTools/\1', str(_p.val))
        except Exception:
            pass
