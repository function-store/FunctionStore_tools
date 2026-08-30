"""Build the droppable install artifacts from InstallerExt.py.

Runs INSIDE TouchDesigner:

    exec(open('packaging/build_installer.py').read())
    result = BuildInstaller()    # packaging/dist/FNS_Installer.tox
    result = BuildBootstrap()    # packaging/dist/FNSTools.tox

Both are BUILD ARTIFACTS, not hand-made components: they embed a snapshot
of InstallerExt.py, so editing that file means rebuilding. Constructing
them from a script keeps the two from drifting and means the artifacts can
be recreated on any machine.

FNS_Installer.tox is the bare installer for a project that already has a
toolkit container. FNSTools.tox is the ONE-DROP BOOTSTRAP:
the (empty) toolkit root itself, carrying the installer, a copy of the
FNS_Updater package, and the vendored palette webBrowser, so a bare project
goes from nothing to installed without ever leaving TD --

    drop it in  ->  installer: "Pick Tools"  ->  the configurator opens
    in the webBrowser panel, first run auto-refreshes the store  ->
    pick, "Review install...", Install (into the root it lives in)

The bootstrap embeds the FNS_Updater artifact, so `Build(export=['FNS_Updater'])`
must have run first; a stale copy is self-healing (its live Pkgversion is
what the updater compares, so the first update pass replaces it).
"""

import json
import os

STAGING = '/sys/quiet'          # ephemeral: never saved with the project
COMP_NAME = 'FNS_Installer'
ROOT_NAME = 'FNSTools'
OUT = 'packaging/dist/FNS_Installer.tox'
OUT_BOOTSTRAP = 'packaging/dist/%s.tox' % ROOT_NAME
UPDATER_TOX = 'packaging/dist/FNS_Updater.tox'

# The installer's version. Packages carry their hand-maintained Pkgversion
# on the live component; the bare installer rail is CODE-BUILT, so its one
# governed field lives here instead -- bump it on any installer change.
# Both rails are stamped from this constant at build time (the bootstrap's
# installer is a copy of the live dev comp, re-stamped so the two rails
# can never ship different answers), which also makes the live dev comp's
# own Pkgversion a mirror of this value, not a second source.
INSTALLER_VERSION = '3.1.0'
# publish.Stage() runs on the shell with no TD, so the version each rail
# was built at rides this sidecar from the build to the staged manifest's
# `rails` block. Without it a rail is recallable only by hash, which no
# human can read back to "which installer is that?".
RAILS_VERSIONS = 'packaging/dist/rails_versions.json'

WEBBROWSER_TOX = 'packaging/webBrowser.tox'

BOOTSTRAP_README = """FunctionStore_tools -- bootstrap
================================

This container IS the toolkit root. The first time it is dropped into a
project the picker opens by itself (exec_root_welcome); it fetches the
catalog from the bucket, offers a starting point, and installs what you
pick right here. To open it again later: the root's "Pick Tools"
parameter (FNSTools page), or FNS_Installer -> "Pick Tools (browser)".

No browser? Set FNS_Installer's "Selection" to a selection.json from
the configurator by hand, pulse "Plan", then "Install".

Later updates: FNS_Updater -> Refresh Store, Check for Updates,
Update This Project.
"""


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def _stampInstallerVersion(comp):
    """Ensure `comp` carries Pkgversion = INSTALLER_VERSION, same shape as
    every package's (About page, read-only in the dialog -- edits go
    through this constant, and scripts still write through readOnly)."""
    p = getattr(comp.par, 'Pkgversion', None)
    if p is None:
        about = next((pg for pg in comp.customPages if pg.name == 'About'),
                     None)
        if about is None:
            about = comp.appendCustomPage('About')
        p = about.appendStr('Pkgversion', label='Package Version')[0]
        p.readOnly = True
    p.default = p.val = INSTALLER_VERSION


def _recordRailVersion(rail_filename):
    """Merge one rail's build version into the sidecar publish.Stage reads."""
    path = _repo(RAILS_VERSIONS)
    try:
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
    except Exception:
        doc = {}
    doc[rail_filename] = INSTALLER_VERSION
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1)
        f.write('\n')


def _installerComp(parent):
    """Create the FNS_Installer COMP inside `parent` and return it."""
    comp = parent.create(baseCOMP, COMP_NAME)
    comp.nodeX, comp.nodeY = 0, 0
    _stampInstallerVersion(comp)

    pg = comp.appendCustomPage('Install')
    p = pg.appendPulse('Configure', label='Pick Tools (browser)')[0]
    p.help = ("Serve the configurator on localhost and open it -- in the "
              "webBrowser panel next to this COMP if there is one, else "
              "your system browser. The selection comes straight back to "
              "this installer; no file to download.")
    p = pg.appendFile('Selectionfile', label='Selection')[0]
    p.help = 'A selection.json produced by the configurator.'
    p = pg.appendFile('Manifestfile', label='Manifest')[0]
    p.help = ("Leave blank to use the palette store's manifest (refresh the "
              "store with FNS_Updater first); artifacts are found beside the "
              "manifest. Dev fallback: packaging/manifest.json.")
    p = pg.appendStr('Target', label='Install Into')[0]
    p.help = ("Leave blank to install into the toolkit container this "
              "installer sits in (the bootstrap), else the project's, "
              "else a new one.")
    pg.appendPulse('Plan', label='Plan (dry run)')
    pg.appendPulse('Install', label='Install')
    p = pg.appendToggle('Replace', label='Replace Existing')[0]
    p.help = 'Re-load packages that are already installed.'
    p = pg.appendToggle('Removeunselected', label='Remove Unselected')[0]
    p.help = ("Apply semantics: manifest TOOLS present in the target but "
              "absent from the selection are removed (COMP + install "
              "record; settings stay in the palette config for "
              "reinstall). The served picker always applies removals -- "
              "its plan shows them. Core is never removed.")
    p = pg.appendMenu('Packagefiles', label='Package Files')[0]
    p.menuNames = ['embedded', 'shared', 'project']
    p.menuLabels = ['Embedded in this project',
                    'Shared (palette store)',
                    'This project\'s own folder']
    p.default = p.val = 'embedded'
    p.startSection = True
    p.help = ("Where the installed package .tox files live. Embedded: inside "
              "the .toe -- one file to move. Shared: bound to the palette "
              "store, so refreshing the store updates every project that "
              "shares it. Project: each project owns its copies, so one can "
              "hold a modified package without affecting the others. Bound "
              "packages update by rewriting the file, not by replacing the "
              "component.")
    p = pg.appendFolder('Packagefolder', label='Package Folder')[0]
    p.help = ("Only used by 'This project's own folder'. Blank means "
              "<project folder>/FNStools.")
    p = pg.appendInt('Port', label='Configurator Port')[0]
    p.normMin, p.normMax = 1024, 65535
    p.default = p.val = 36760    # above the console's 36710-36759 block
    p.help = 'Local port the served configurator listens on.'
    p = pg.appendStr('Status')[0]
    p.readOnly = True

    ext = comp.create(textDAT, 'InstallerExt')
    ext.nodeX, ext.nodeY = -400, 0
    comp.par.extension1 = "op('./InstallerExt').module.InstallerExt(me)"
    comp.par.promoteextension1 = True

    plan = comp.create(tableDAT, 'plan')
    plan.nodeX, plan.nodeY = 0, -250

    pe = comp.create(parameterexecuteDAT, 'parexec_pulses')
    pe.nodeX, pe.nodeY = -400, -250
    pe.par.op = comp
    pe.par.pars = 'Plan Install Configure'
    pe.par.custom = True
    pe.par.builtin = False
    pe.par.valuechange = False
    pe.par.onpulse = True          # NOT `pulse` -- that par does not exist
    pe.text = ('# Route the COMP pulses to the extension.\n\n'
               'def onPulse(par):\n'
               '\tif par.name == "Plan":\n'
               '\t\tparent().Plan()\n'
               '\telif par.name == "Install":\n'
               '\t\tparent().Install()\n'
               '\telif par.name == "Configure":\n'
               '\t\tparent().Configure()\n'
               '\treturn\n')

    # the served configurator: page + server, dormant until Configure
    page = comp.create(textDAT, 'configurator_html')
    page.nodeX, page.nodeY = -400, -500

    wcb = comp.create(textDAT, 'webserver_callbacks')
    wcb.text = ('# Delegate to the extension -- single implementation.\n\n'
                'def onHTTPRequest(webServerDAT, request, response):\n'
                '\treturn parent().ServeRequest(request, response)\n')
    wcb.nodeX, wcb.nodeY = 0, -500

    ws = comp.create(webserverDAT, 'webserver')
    ws.par.active = False
    ws.par.port = 36760
    # Blank = every interface (Derivative). The picker drives /selection and
    # /install with no authentication, so it is loopback-only. InstallerExt
    # re-asserts this on every Configure() to repair installers built before
    # this line; setting it here means a fresh build is never wrong even once.
    ws.par.localaddress = '127.0.0.1'
    ws.par.callbacks = 'webserver_callbacks'
    ws.nodeX, ws.nodeY = 200, -500
    _refreshInstallerSources(comp)
    return comp


def _refreshInstallerSources(comp):
    """Re-embed the installer's two source snapshots from the repo.

    The installer is a resident of the dev root (EnsureDevRails) and ships
    inside the castrated bootstrap as-is, so the snapshots it carries are
    what users run. Both the dev refresh and BuildBootstrap call this, so
    neither copy can be older than packaging/InstallerExt.py and
    packaging/configurator/index.html.
    """
    ext = comp.op('InstallerExt')
    with open(_repo('packaging/InstallerExt.py'), encoding='utf-8') as f:
        ext.text = f.read()
    page = comp.op('configurator_html')
    with open(_repo('packaging/configurator/index.html'), encoding='utf-8') as f:
        page.text = f.read()
    comp.par.reinitextensions.pulse()
    return comp


def _resetInstallerState(comp):
    """Blank the per-project state before shipping a copy of the installer:
    a dev selection path, a status line or a live server are not things a
    fresh drop should inherit."""
    for name in ('Selectionfile', 'Manifestfile', 'Target', 'Status'):
        p = getattr(comp.par, name, None)
        if p is not None:
            p.val = ''
    plan = comp.op('plan')
    if plan is not None:
        plan.clear()
    ws = comp.op('webserver')
    if ws is not None:
        ws.par.active = False
    # A Private-Investigator-tracked dev installer is bound to its suspects
    # .tox; a NESTED externaltox survives ExportPortableTox, so the shipped
    # copy must be cut loose or it would point at a path only the dev
    # machine has.
    for name, value in (('enableexternaltox', False), ('externaltox', '')):
        p = getattr(comp.par, name, None)
        if p is not None:
            p.val = value


# packaging/webBrowser.tox is the FNS webBrowser: TD's palette component
# with the visibility policy INSIDE it (Render Only While Window Open /
# Render Only While Viewer Active -- a Web Render cooks a whole browser
# process otherwise) and the render's Source/DAT mirrored on its custom
# pars, so every instance (this rail, ColorUI's panel) clones the same
# master and keeps its own configuration on its own parameters.
# /FNSTools/webBrowser is that master.
def _ensureBrowserPolicy(web):
    """A rail instance renders only while someone can see it; the
    component's own watchers do the work, so there is nothing beside it.
    Watchpane covers the case the first two cannot: shown in a PANEL
    pane via a Select COMP mirror (a Hub/Console tab), where the
    browser is in nobody's window and nobody's viewer."""
    for n, v in (('Watchwindow', True), ('Watchviewer', True),
                 ('Watchpane', True)):
        p = getattr(web.par, n, None)
        if p is not None:
            p.val = v
    return web


def _loadWebBrowser(root, x, y):
    """The picker's display surface: the FNS webBrowser, vendored at
    packaging/webBrowser.tox. Returns (comp, error)."""
    browser_tox = _repo(WEBBROWSER_TOX)
    if not os.path.exists(browser_tox):
        return None, '%s missing -- vendored webBrowser not found' % WEBBROWSER_TOX
    before = {c.id for c in root.children}
    root.loadTox(browser_tox)
    fresh = [c for c in root.children if c.id not in before]
    web = fresh[0] if fresh else root.op('webBrowser')
    if web is None:
        return None, 'webBrowser failed to load from %s' % browser_tox
    if web.name != 'webBrowser':
        web.name = 'webBrowser'
    web.nodeX, web.nodeY = x, y
    web.par.Address = ''      # nothing to show until Configure serves the page
    _ensureBrowserPolicy(web)
    return web, None


# The rails are RESIDENTS of the dev root, not build-time injections: the
# bootstrap is the dev root castrated, so whatever the dev root carries is
# what ships -- and a second, build-only copy is exactly the drift the
# castration was adopted to end. Run this after editing InstallerExt.py or
# configurator/index.html (it re-embeds both), or to (re)create the rails:
#
#     exec(open('packaging/build_installer.py').read())
#     EnsureDevRails()
#
RAIL_POSITIONS = {COMP_NAME: (600, -375), 'webBrowser': (1400, -375)}


def EnsureDevRails(root=None):
    """Make the live toolkit root carry the install rails, current.

    Idempotent: an existing FNS_Installer gets its source snapshots
    refreshed in place (pars and layout untouched); a missing one is
    built; a missing webBrowser is loaded from the vendored tox. Positions
    for NEW comps come from RAIL_POSITIONS, chosen beside FNS_Updater in
    the dev root -- an existing comp is never moved.
    """
    root = root or getattr(op, 'FNS', None)
    if root is None or not root.valid:
        return {'ok': False, 'error': 'no live toolkit root (op.FNS)'}
    out = {'ok': True, 'root': root.path}
    inst = root.op(COMP_NAME)
    if inst is None:
        inst = _installerComp(root)
        inst.nodeX, inst.nodeY = RAIL_POSITIONS[COMP_NAME]
        out['installer'] = 'built'
    else:
        _refreshInstallerSources(inst)
        out['installer'] = 'refreshed'
    web = root.op('webBrowser')
    if web is None:
        web, err = _loadWebBrowser(root, *RAIL_POSITIONS['webBrowser'])
        if err:
            out['ok'] = False
            out['error'] = err
            return out
        out['webBrowser'] = 'loaded'
    else:
        out['webBrowser'] = 'present'
        _ensureBrowserPolicy(web)
    errs = inst.errors(recurse=True).splitlines()[:3]
    out['installer_errors'] = errs or 'clean'
    return out


def _stage(name):
    stage = op(STAGING).op(name)
    if stage:
        stage.destroy()
    return op(STAGING).create(baseCOMP, name)


def _export(comp, out_path, stage):
    dest = _repo(out_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    op.Embody.ExportPortableTox(target=comp, save_path=dest)
    ok = os.path.exists(dest)
    info = {'built': comp.path, 'out': dest, 'exported': ok,
            'bytes': os.path.getsize(dest) if ok else 0,
            'errors': comp.errors(recurse=True).splitlines()[:3] or 'clean'}
    stage.destroy()
    return info


def BuildInstaller(out_path=OUT):
    """The bare installer COMP, for a project that already has the root."""
    stage = _stage('installer_build')
    comp = _installerComp(stage)
    info = _export(comp, out_path, stage)
    if info.get('exported'):
        _recordRailVersion(os.path.basename(out_path))
        info['version'] = INSTALLER_VERSION
    return info


# The toolkit root's entry points. ONE definition, used by both roots --
# the shipped bootstrap and the dev root -- because a user cannot tell the
# two apart and neither should carry pars the other lacks. Per-tool controls
# are NOT here; they belong to the registry-derived settings UI. What lives
# here is only what any root can answer for.
ROOT_PAGE = 'FNSTools'
ROOT_ENTRY_POINTS = (
    ('Picktools', 'Pick Tools',
     'Install and remove tools. Once the config registry is installed this '
     'opens the FNS console on its Install & remove tab (in the webBrowser '
     'panel beside the installer when the root has one); before that -- '
     'the bare bootstrap -- the installer\'s own picker. Unchecking an '
     'installed tool removes it; its settings are kept for the next '
     'install.'),
    ('Openinstaller', 'Installer Parameters',
     'The FNS_Installer\'s parameter dialog: the manual rail. Point '
     'Selection at a selection.json, Plan, Install, and choose where '
     'package files live. Pick Tools is the normal path.'),
    ('Opensettings', 'Open Settings',
     'The FNS console on its Settings tab (in the webBrowser panel beside '
     'the installer when the root has one, else your system browser): '
     'every installed tool\'s settings on one scrollable page, config '
     'export/import, and the global/project scope switch. Install & '
     'remove is its second tab.'),
)
# Three pulses, three distinct roles, and the console is the hub for two of
# them: Pick Tools deep-links to its Install & remove tab (#tools) and Open
# Settings to its Settings tab -- both in the in-TD webBrowser panel when
# the root has one, so the whole flow stays inside TD (the panel handles
# the console fully, file dialog included; export also writes its file
# server-side). Pick Tools falls back to the installer's own picker only
# while core is not installed yet; Installer Parameters is the manual rail.
# Guarded on every side: a root without an installer, or without the config
# registry, logs and returns rather than raising inside a pulse callback.
# The registry is resolved the way every cross-tool caller does it -- getattr
# on the global shortcut, which IS the feature detect (ConfiguratorDistribution
# 1.1) -- so Open Settings keeps working in a root the installer was removed
# from.
ROOT_PULSE_TEXT = (
    '# Root-level entry points. Generated by packaging/build_installer.py --\n'
    '# edit it there; EnsureRootEntryPoints re-applies it.\n'
    '#   Pick Tools  -> FNS console, Install & remove tab (in-TD panel when\n'
    '#                  present); the installer\'s own picker before core exists\n'
    '#   Open Settings -> FNS console, Settings tab (in-TD panel when present)\n'
    '#   Installer Parameters -> the manual rail (selection.json / Plan / Install)\n\n'
    'def _console(tab):\n'
    '\t# FNS_Console serves the page; an older core without it still answers\n'
    '\t# through the config registry\'s forward. None = neither is installed.\n'
    '\tcon = getattr(op, "FNS_CONSOLE", None)\n'
    '\tif con is not None:\n'
    '\t\treturn con.Open(tab=tab, panel=True)\n'
    '\treg = getattr(op, "FNS_CONFIGREGISTRY", None)\n'
    '\tif reg is not None:\n'
    '\t\treturn reg.OpenSettingsUI(tab=tab, panel=True)\n'
    '\treturn None\n\n'
    'def onPulse(par):\n'
    '\tinst = parent().op(%r)\n'
    '\tif par.name == "Opensettings":\n'
    '\t\tres = _console("settings")\n'
    '\t\tif res is None:\n'
    '\t\t\tdebug("FNSTools: no FNS_Console installed yet -- Pick Tools installs core first")\n'
    '\t\telif isinstance(res, dict) and not res.get("ok"):\n'
    '\t\t\tdebug("FNSTools: console did not open --", res.get("why"))\n'
    '\telif par.name == "Picktools":\n'
    '\t\tres = _console("tools")\n'
    '\t\tif res is not None:\n'
    '\t\t\tif isinstance(res, dict) and not res.get("ok"):\n'
    '\t\t\t\tdebug("FNSTools: console did not open --", res.get("why"))\n'
    '\t\telif inst is not None:\n'
    '\t\t\tinst.par.Configure.pulse()\n'
    '\t\telse:\n'
    '\t\t\tdebug("FNSTools: no installer in this root")\n'
    '\telif par.name == "Openinstaller":\n'
    '\t\tif inst is None:\n'
    '\t\t\tdebug("FNSTools: no installer in this root")\n'
    '\t\t\treturn\n'
    '\t\tinst.openParameters()\n' % COMP_NAME)


# The first-run welcome: an Execute DAT whose onCreate fires whenever the
# DAT comes into being -- dropped from the bootstrap .tox, loaded with the
# project, copied, pasted. Exactly one of those is a first run, the drop,
# and a storage flag on the root tells them apart: the shipped root
# carries no storage at all (_bootstrapRoot unstores everything), and
# everything after the first firing does. Two more guards: the dev master
# (root externaltox set) never welcomes, and neither does the copy staged
# for a build, which still carries that binding when this DAT is created.
# The paste rail stores the same flag right after loadTox, so a scripted
# drop installs its selection without a picker appearing over it.
WELCOME_EXEC_NAME = 'exec_root_welcome'
WELCOME_FLAG = 'FNS_welcomed'
WELCOME_DELAY_FRAMES = 90   # the paste rail waits the same before handing over
WELCOME_RELOCATE_FRAMES = 30   # move first, welcome after (on the copy)
WELCOME_EXEC_TEXT = ('''\
# First-run welcome. Generated by packaging/build_installer.py --
# edit it there; EnsureRootEntryPoints re-applies it.
#
# onCreate fires for every way this DAT can come into being (drop,
# project load, copy, paste). Only the drop is a first run: the
# shipped root has no storage, and the flag below is set the moment
# it fires. A root bound to a dev tox (externaltox) never welcomes.
#
# A drop into a NESTED network first moves the root home: the toolkit
# belongs at /. The move is copy-to-/ + destroy, run as a DETACHED
# script (the destroy takes this very DAT with it), and the copy's own
# onCreate is inert because storage travels with the copy -- so the
# script re-arms the welcome on the copy itself. No move when / already
# holds a same-named comp (an installed toolkit), when the paste rail
# took over, or in the toolkit's own dev project (bootstraps get
# dropped into scratch containers there on purpose).

FLAG = %(flag)r
DELAY = %(delay)d

_RELOCATE = \'\'\'
old = op(@PATH@)
if old is not None and old.valid and old.fetch(%(flag)r, None, search=False) == "pending":
\twe = None
\tdest = op("/")
\tif dest.op(@NAME@) is None:
\t\tnew = dest.copy(old)
\t\told.destroy()
\t\tif new.name != @NAME@:
\t\t\ttry:
\t\t\t\tnew.name = @NAME@
\t\t\texcept Exception:
\t\t\t\tpass
\t\tnew.store(%(flag)r, "pending")
\t\twe = new.op(%(exec)r)
\telse:
\t\twe = old.op(%(exec)r)
\tif we is not None:
\t\trun("args[0].valid and args[0].module.welcome()", we,
\t\t    delayFrames=%(delay)d, delayRef=op.TDResources)
\'\'\'

def onCreate():
\troot = me.parent()
\ttry:
\t\tif root.par.externaltox.eval():
\t\t\treturn
\texcept Exception:
\t\treturn
\tif root.fetch(FLAG, None, search=False) is not None:
\t\treturn
\troot.store(FLAG, "pending")
\thome = root.parent()
\tif (home is not None and home.path != "/"
\t\t\tand op("/").op(root.name) is None and not _isDev(root)):
\t\tscript = (_RELOCATE.replace("@PATH@", repr(root.path))
\t\t\t\t  .replace("@NAME@", repr(root.name)))
\t\trun(script, delayFrames=%(relocate)d, delayRef=op.TDResources)
\t\treturn
\t# the installer extension and the webBrowser need frames to come up
\trun("args[0].valid and args[0].module.welcome()", me,
\t    delayFrames=DELAY, delayRef=op.TDResources)
\treturn

def _isDev(root):
\t# cannot tell = do not move
\ttry:
\t\tm = root.op("FNS_Installer/InstallerExt")
\t\treturn m is None or bool(m.module.IsDevProject())
\texcept Exception:
\t\treturn True

def welcome():
\troot = me.parent()
\tif root.fetch(FLAG, None, search=False) != "pending":
\t\treturn          # the paste rail took over, or someone already did
\troot.store(FLAG, "shown")
\tpar = getattr(root.par, "Picktools", None)
\tif par is None:
\t\tdebug("FNSTools: no Pick Tools on this root -- nothing to open")
\t\treturn
\ttry:
\t\tpar.pulse()
\texcept Exception as e:
\t\tdebug("FNSTools: first-run welcome could not open Pick Tools --", e)
''' % {'flag': WELCOME_FLAG, 'delay': WELCOME_DELAY_FRAMES,
       'exec': WELCOME_EXEC_NAME, 'relocate': WELCOME_RELOCATE_FRAMES})


# The root's config callbacks: what the root remembers in the roaming
# config beyond its pars. One entry today -- `last_install`, derived on
# every SaveAll from the rails' `installed` table, so a fresh bootstrap on
# the same machine (or a synced palette) can offer "Set up like last
# time". Derived, never hand-maintained: the table is written per package
# as it lands, so the record cannot drift from what the project holds. A
# root with no table (never installed through the rails -- the dev master,
# a hand-built root) keeps whatever another project wrote rather than
# erasing it, because it has nothing truer to say. Scope is honoured by the
# registry itself: under project scope the snapshot runs but the file is
# never written, and the read-back here is skipped too.
CONFIG_CALLBACKS_NAME = 'config_callbacks'
ROOT_CANONICAL = 'FNS'
CONFIG_CALLBACKS_TEXT = (
    '# Root-level config state. Generated by packaging/build_installer.py --\n'
    '# edit it there; EnsureRootEntryPoints re-applies it.\n'
    '#\n'
    '# onConfigSave: remember what this project installed (the rails\'\n'
    '# `installed` table, written per package as it lands) so a fresh\n'
    '# bootstrap can offer "Set up like last time". A root with no table\n'
    '# keeps the record another project wrote instead of erasing it.\n\n'
    'import time\n\n'
    'KEY = "last_install"\n'
    'CANONICAL = %r\n\n'
    'def onConfigSave():\n'
    '\troot = me.parent()\n'
    '\tt = root.op("installed")\n'
    '\tnames = []\n'
    '\tif t is not None and t.numRows > 1 and t[0, 0].val == "package":\n'
    '\t\tnames = sorted(t[i, 0].val for i in range(1, t.numRows) if t[i, 0].val)\n'
    '\tif not names:\n'
    '\t\treturn _previous(root)\n'
    '\trec = {"packages": names, "project": project.name,\n'
    '\t\t   "when": time.strftime("%%Y-%%m-%%dT%%H:%%M:%%S")}\n'
    '\tinst = root.op(%r)\n'
    '\tp = getattr(inst.par, "Packagefiles", None) if inst is not None else None\n'
    '\tif p is not None:\n'
    '\t\trec["bind"] = str(p.eval())\n'
    '\treturn {KEY: rec}\n\n'
    'def _previous(root):\n'
    '\t# the authored scope record is on the root; a missing par reads as global\n'
    '\tscope = getattr(root.par, "Configscope", None)\n'
    '\tif scope is not None and str(scope.eval()) == "project":\n'
    '\t\treturn {}          # never read the roaming file under project scope\n'
    '\treg = getattr(op, "FNS_CONFIGREGISTRY", None)\n'
    '\tif reg is None:\n'
    '\t\treturn {}\n'
    '\ttry:\n'
    '\t\tprev = reg.ConfigData.get("tools", {}).get(CANONICAL, {}).get("state", {}).get(KEY)\n'
    '\texcept Exception:\n'
    '\t\tprev = None\n'
    '\treturn {KEY: prev} if prev else {}\n\n'
    'def onConfigLoad(data):\n'
    '\t# nothing to re-apply: the record is read by the installer on a bare root\n'
    '\treturn\n'
    % (ROOT_CANONICAL, COMP_NAME))


def EnsureRootEntryPoints(root):
    """Give a toolkit root its entry-point pars, the forwarder DAT, the
    first-run welcome DAT and the root's config callbacks.

    Called by BuildBootstrap for the shipped root, and runnable against a
    live one so the two never drift:

        exec(open('packaging/build_installer.py').read())
        EnsureRootEntryPoints(op.FNS)

    Idempotent -- an existing page, par or forwarder is reused and brought
    up to date rather than duplicated, so it is safe to re-run after this
    definition changes.
    """
    pg = None
    for page in root.customPages:
        if page.name == ROOT_PAGE:
            pg = page
            break
    if pg is None:
        pg = root.appendCustomPage(ROOT_PAGE)
    for name, label, help_text in ROOT_ENTRY_POINTS:
        par = getattr(root.par, name, None)
        if par is None:
            par = pg.appendPulse(name, label=label)[0]
        par.label = label
        par.help = help_text
    pe = root.op('parexec_root_pulses')
    if pe is None:
        pe = root.create(parameterexecuteDAT, 'parexec_root_pulses')
        pe.nodeX, pe.nodeY = -350, -250
    pe.par.op = root
    pe.par.pars = ' '.join(n for n, _, _ in ROOT_ENTRY_POINTS)
    pe.par.custom = True
    pe.par.builtin = False
    pe.par.valuechange = False
    pe.par.onpulse = True
    pe.text = ROOT_PULSE_TEXT
    we = root.op(WELCOME_EXEC_NAME)
    if we is None:
        # Creating it fires its own onCreate once, here and now -- inert on
        # a dev master and on a staged build copy (externaltox guard).
        we = root.create(executeDAT, WELCOME_EXEC_NAME)
        we.nodeX, we.nodeY = -550, -375
    we.par.create = True
    for name in ('start', 'exit', 'framestart', 'frameend',
                 'playstatechange', 'devicechange',
                 'projectpresave', 'projectpostsave'):
        setattr(we.par, name, False)
    we.text = WELCOME_EXEC_TEXT
    cb = root.op(CONFIG_CALLBACKS_NAME)
    if cb is None:
        cb = root.create(textDAT, CONFIG_CALLBACKS_NAME)
        cb.nodeX, cb.nodeY = -550, -500
    cb.text = CONFIG_CALLBACKS_TEXT
    # the root's config host reads its hooks from the DAT its Callback par
    # names (a bare sibling name, resolved against the root's network)
    host = root.op(ROOT_HOST)
    wired = None
    if host is not None:
        cb_par = getattr(host.par, 'Callback', None)
        if cb_par is not None:
            if cb_par.eval() is not cb:
                cb_par.val = cb.name
            wired = host.path
    return {'root': root.path, 'page': pg.name,
            'pars': [n for n, _, _ in ROOT_ENTRY_POINTS],
            'forwarder': pe.path, 'welcome': we.path,
            'config_callbacks': cb.path, 'config_host': wired}


# Dev-only par pages, removed from the shipped root. Version Ctrl is
# authoring metadata (Vcname/Vcauthor/Vcbuild/save timestamps) that means
# nothing in a user's project. About and Registry SHIP: the update controls
# are user-facing, and the root is itself a config-registry host, so a
# shipped root keeps roaming its own settings.
BOOTSTRAP_STRIP_PAGES = ('Version Ctrl',)
# Dev-root children that ship INSIDE the bootstrap: the install rails, and
# the root's own config host (canonical `FNS`) -- the root is a config-
# registry host like any tool, and without it a user's root has no section
# in the roaming config: no root-level state roams, and the "Set up like
# last time" record has nowhere to live. FNS_Updater is deliberately not
# here -- the dev copy is an Embody-tracked master with file bindings, so
# the shipped one is the clean dist artifact.
ROOT_HOST = 'FNS_ConfigHost'
BOOTSTRAP_KEEP = (COMP_NAME, 'webBrowser', ROOT_HOST)


def _severHost(host):
    """Cut a kept registry host loose from the dev checkout before it ships:
    its suspects-tox binding (a NESTED externaltox survives the portable
    export and would point at a path only the dev machine has), the tracker
    tag, and the registration status the dev project stamped on it. The
    same recipe every stamp path applies (fns-registry skill)."""
    for name, value in (('enableexternaltox', False), ('externaltox', ''),
                        ('Regstatus', '')):
        p = getattr(host.par, name, None)
        if p is not None:
            try:
                p.mode = ParMode.CONSTANT
                p.val = value
            except Exception:
                pass
    for tag in ('pi_suspect',):
        if tag in host.tags:
            host.tags.remove(tag)
    # Private Investigator's apparatus is authoring-side only: the Version
    # Ctrl page fronts vc_data through BIND pars, so the table and the page
    # go together (pars before the page -- TD relocates a destroyed page's
    # surviving pars instead of deleting them) or every install cooks with
    # a dangling-bind error on the host. Same strip pre_release_common
    # applies to every exported package.
    for pg in list(host.customPages):
        if pg.name != 'Version Ctrl':
            continue
        for p in list(pg.pars):
            try:
                p.destroy()
            except Exception:
                pass
        try:
            pg.destroy()
        except Exception:
            pass
    vc = host.op('vc_data')
    if vc is not None:
        vc.destroy()
    return host


def _bootstrapRoot(stage):
    """The shipped root: the LIVE dev root, castrated -- not a lookalike.

    Building a second root from scratch is what let the two drift: every
    top-level par had to be declared twice and stay in step by hand. The
    bootstrap is the same comp with the dev-only bits removed, so there is
    one set of top-level pars and it is the one being used every day.

    Castration is: no children (the installer fetches everything, so the
    shipped root is empty), no dev-only par pages, no authoring storage.
    Identity is inherited rather than re-declared -- the `FNS` global and
    parent shortcuts come with the copy, and are re-asserted here because
    shipped tools reach for `parent.FNS` through the guarded tryExcept
    idiom and a missing shortcut makes those lookups fail quietly.

    Returns (root, error). Refuses rather than silently shipping a
    different root when there is no live one to copy.
    """
    dev = getattr(op, 'FNS', None)
    if dev is None or not dev.valid:
        return None, ('no live toolkit root (op.FNS) to derive the bootstrap '
                      'from -- open the dev project and run this there')
    root = stage.copy(dev, name=ROOT_NAME)
    # Drop the inherited shortcuts while the surgery runs: the copy arrives
    # holding opshortcut/parentshortcut = 'FNS', and two ops claiming the
    # same global shortcut is a state nothing here needs. Re-asserted at the
    # end, once this is a root again rather than a comp being taken apart.
    root.par.opshortcut = ''
    root.par.parentshortcut = ''
    # Bake the dev root's live state into the shipped pars, BEFORE the
    # children go. Evaluating here is the whole point: this is the one place
    # the binds and expressions still resolve, because the config host they
    # point at is still below us. A moment later it is not, and pre_release
    # pays this same price on host Registration pars -- a shipped copy whose
    # bind master was removed carries an expression that errors on load.
    #
    # The evaluated value becomes .default as well as .val. Without that, a
    # user hitting "reset to default" on the bundle gets whatever the par
    # happened to be created with in the dev comp, which is not the state we
    # shipped and may be a value no shipped install should ever hold.
    for page in root.customPages:
        for p in page.pars:
            if p.style in ('Pulse', 'Momentary', 'Header'):
                continue          # nothing to freeze; .default is meaningless
            try:
                val = p.eval()
            except Exception:
                continue          # unresolvable already -- leave it alone
            try:
                p.mode = ParMode.CONSTANT
                p.default = val
                p.val = val
            except Exception:
                pass              # read-only or otherwise unsettable
    # Children come off in WAVES, not one pass. `.destroy()` takes an op's
    # DOCKED ops with it -- `logger` docks its callbacks, `LICENSE` docks
    # the docsHelper comps -- so a list snapshotted up front goes dangling
    # mid-loop, and destroying a stale handle raises "Invalid OP object"
    # roughly half way through. Re-snapshot each pass and skip whatever a
    # previous destroy already claimed. Bounded, so a child that refuses to
    # die reports itself instead of spinning forever. The install rails
    # (BOOTSTRAP_KEEP) survive the cull: they are dev-root residents and
    # ship as they are -- see EnsureDevRails.
    for _ in range(20):
        kids = [c for c in root.children
                if c.valid and c.name not in BOOTSTRAP_KEEP]
        if not kids:
            break
        for child in kids:
            if child.valid:
                try:
                    child.destroy()
                except Exception:
                    pass
    left = [c.name for c in root.children
            if c.valid and c.name not in BOOTSTRAP_KEEP]
    if left:
        return None, 'could not empty the staged root; still holds: %s' % (
            ', '.join(sorted(left)[:10]))
    for page in list(root.customPages):
        if page.name in BOOTSTRAP_STRIP_PAGES:
            page.destroy()
    for key in list(root.storage):
        root.unstore(key)
    root.par.opshortcut = 'FNS'
    root.par.parentshortcut = 'FNS'
    return root, None


def BuildBootstrap(out_path=OUT_BOOTSTRAP):
    """The one-drop bootstrap: the toolkit root with installer + FNS_Updater.

    The root is a castrated copy of the live dev root (see _bootstrapRoot),
    so the bundle a user drops and the root we develop in cannot diverge in
    their top-level parameters. Per-tool controls are still absent by
    design: those belong to the registry-derived settings UI, reachable
    from the root's own 'Open Settings' pulse.
    """
    updater = _repo(UPDATER_TOX)
    if not os.path.exists(updater):
        return {'exported': False,
                'error': "%s missing -- run Build(export=['FNS_Updater']) first"
                         % UPDATER_TOX}
    stage = _stage('bootstrap_build')
    root, err = _bootstrapRoot(stage)
    if err:
        stage.destroy()
        return {'exported': False, 'error': err}

    # The rails came along with the copy (dev-root residents); a root that
    # somehow lacks one gets it built/loaded here so the bundle is whole.
    # Either way the shipped installer embeds CURRENT sources and no
    # per-project state.
    inst = root.op(COMP_NAME)
    if inst is None:
        inst = _installerComp(root)
        inst.nodeX, inst.nodeY = 0, 0
    else:
        _refreshInstallerSources(inst)
    # Copied from the live dev comp, so re-stamp from the constant: the
    # bare rail and the bootstrap's installer must never ship different
    # version answers.
    _stampInstallerVersion(inst)
    _resetInstallerState(inst)
    host = root.op(ROOT_HOST)
    if host is None:
        stage.destroy()
        return {'exported': False,
                'error': '%s missing from the dev root -- the shipped root '
                         'needs its config host' % ROOT_HOST}
    _severHost(host)

    before = {c.id for c in root.children}
    root.loadTox(updater)
    fresh = [c for c in root.children if c.id not in before]
    upd = fresh[0] if fresh else root.op('FNS_Updater')
    if upd is None:
        stage.destroy()
        return {'exported': False, 'error': 'FNS_Updater failed to load from %s' % updater}
    if upd.name != 'FNS_Updater':
        upd.name = 'FNS_Updater'
    upd.nodeX, upd.nodeY = 350, 0

    readme = root.create(textDAT, 'README')
    readme.text = BOOTSTRAP_README
    readme.nodeX, readme.nodeY = -350, 0
    readme.viewer = True

    # the picker's display surface, kept from the dev root or loaded fresh;
    # the installer's Configure points it at the served page and opens it.
    web = root.op('webBrowser')
    if web is None:
        web, err = _loadWebBrowser(root, 350, -250)
        if err:
            stage.destroy()
            return {'exported': False, 'error': err}
    else:
        web.par.Address = ''  # nothing to show until Configure serves the page
        _ensureBrowserPolicy(web)
        web.par.Active = False   # the staged copy is never open; ship it dormant
        # the shipped rail must not clone a master only the dev project has
        web.par.enablecloning = False
        web.par.clone = ''

    EnsureRootEntryPoints(root)

    info = _export(root, out_path, stage)
    if info.get('exported'):
        _recordRailVersion(os.path.basename(out_path))
        info['version'] = INSTALLER_VERSION
    return info
