"""Build the droppable install artifacts from InstallerExt.py.

Runs INSIDE TouchDesigner:

    exec(open('packaging/build_installer.py').read())
    result = BuildInstaller()    # packaging/dist/FNS_Installer.tox
    result = BuildBootstrap()    # packaging/dist/FunctionStore_tools_2025.tox

Both are BUILD ARTIFACTS, not hand-made components: they embed a snapshot
of InstallerExt.py, so editing that file means rebuilding. Constructing
them from a script keeps the two from drifting and means the artifacts can
be recreated on any machine.

FNS_Installer.tox is the bare installer for a project that already has a
toolkit container. FunctionStore_tools_2025.tox is the ONE-DROP BOOTSTRAP:
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

import os

STAGING = '/sys/quiet'          # ephemeral: never saved with the project
COMP_NAME = 'FNS_Installer'
ROOT_NAME = 'FunctionStore_tools_2025'
OUT = 'packaging/dist/FNS_Installer.tox'
OUT_BOOTSTRAP = 'packaging/dist/%s.tox' % ROOT_NAME
UPDATER_TOX = 'packaging/dist/FNS_Updater.tox'

WEBBROWSER_TOX = 'packaging/webBrowser.tox'

BOOTSTRAP_README = """FunctionStore_tools -- bootstrap
================================

This container IS the toolkit root. To fill it:

1. FNS_Installer: pulse "Pick Tools". A picker opens (in the webBrowser
   panel here); it fetches the catalog from the bucket on first run.
2. Pick your tools, hit "Review install...", then "Install".
   Packages land right here.

No browser? Set "Selection" to a selection.json from the configurator
by hand, pulse "Plan", then "Install".

Later updates: FNS_Updater -> Refresh Store, Check for Updates,
Update This Project.
"""


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def _installerComp(parent):
    """Create the FNS_Installer COMP inside `parent` and return it."""
    comp = parent.create(baseCOMP, COMP_NAME)
    comp.nodeX, comp.nodeY = 0, 0

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
    p.default = p.val = 9877
    p.help = 'Local port the served configurator listens on.'
    p = pg.appendStr('Status')[0]
    p.readOnly = True

    ext = comp.create(textDAT, 'InstallerExt')
    with open(_repo('packaging/InstallerExt.py'), encoding='utf-8') as f:
        ext.text = f.read()
    ext.nodeX, ext.nodeY = -400, 0
    comp.par.extension1 = "op('./InstallerExt').module.InstallerExt(me)"
    comp.par.promoteextension1 = True
    comp.par.reinitextensions.pulse()

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
    with open(_repo('packaging/configurator/index.html'), encoding='utf-8') as f:
        page.text = f.read()
    page.nodeX, page.nodeY = -400, -500

    wcb = comp.create(textDAT, 'webserver_callbacks')
    wcb.text = ('# Delegate to the extension -- single implementation.\n\n'
                'def onHTTPRequest(webServerDAT, request, response):\n'
                '\treturn parent().ServeRequest(request, response)\n')
    wcb.nodeX, wcb.nodeY = 0, -500

    ws = comp.create(webserverDAT, 'webserver')
    ws.par.active = False
    ws.par.port = 9877
    ws.par.callbacks = 'webserver_callbacks'
    ws.nodeX, ws.nodeY = 200, -500
    return comp


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
    return _export(comp, out_path, stage)


def BuildBootstrap(out_path=OUT_BOOTSTRAP):
    """The one-drop bootstrap: the toolkit root with installer + FNS_Updater.

    The root ships with the dev root's identity -- global and parent
    shortcut `FNS` -- because shipped tools reach for `parent.FNS` (only
    ever through the guarded `tdu.tryExcept` idiom, but the shortcut is
    what lets a root-level control still resolve). It does NOT carry the
    dev root's Active/UI parameter surface: per-tool controls belong to
    the registry-derived settings UI, not to root pars.
    """
    updater = _repo(UPDATER_TOX)
    if not os.path.exists(updater):
        return {'exported': False,
                'error': "%s missing -- run Build(export=['FNS_Updater']) first"
                         % UPDATER_TOX}
    stage = _stage('bootstrap_build')
    root = stage.create(baseCOMP, ROOT_NAME)
    root.par.opshortcut = 'FNS'
    root.par.parentshortcut = 'FNS'

    inst = _installerComp(root)
    inst.nodeX, inst.nodeY = 0, 0

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

    # the picker's display surface: TD's palette webBrowser (Web Render
    # TOP + interaction), vendored at packaging/webBrowser.tox. The
    # installer's Configure points it at the served page and opens it.
    browser_tox = _repo(WEBBROWSER_TOX)
    if not os.path.exists(browser_tox):
        stage.destroy()
        return {'exported': False,
                'error': '%s missing -- vendored webBrowser not found' % WEBBROWSER_TOX}
    before = {c.id for c in root.children}
    root.loadTox(browser_tox)
    fresh = [c for c in root.children if c.id not in before]
    web = fresh[0] if fresh else root.op('webBrowser')
    if web is None:
        stage.destroy()
        return {'exported': False, 'error': 'webBrowser failed to load from %s' % browser_tox}
    if web.name != 'webBrowser':
        web.name = 'webBrowser'
    web.nodeX, web.nodeY = 350, -250
    web.par.Address = ''      # nothing to show until Configure serves the page

    return _export(root, out_path, stage)
