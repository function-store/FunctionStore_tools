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

import os

STAGING = '/sys/quiet'          # ephemeral: never saved with the project
COMP_NAME = 'FNS_Installer'
ROOT_NAME = 'FNSTools'
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


def _loadWebBrowser(root, x, y):
    """The picker's display surface: TD's palette webBrowser (Web Render
    TOP + interaction), vendored at packaging/webBrowser.tox. Returns
    (comp, error)."""
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
    return _export(comp, out_path, stage)


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
    'def onPulse(par):\n'
    '\tinst = parent().op(%r)\n'
    '\treg = getattr(op, "FNS_CONFIGREGISTRY", None)\n'
    '\tif par.name == "Opensettings":\n'
    '\t\tif reg is None:\n'
    '\t\t\tdebug("FNSTools: no FNS_ConfigRegistry installed yet -- Pick Tools installs core first")\n'
    '\t\t\treturn\n'
    '\t\tres = reg.OpenSettingsUI(tab="settings", panel=True)\n'
    '\t\tif isinstance(res, dict) and not res.get("ok"):\n'
    '\t\t\tdebug("FNSTools: console did not open --", res.get("why"))\n'
    '\telif par.name == "Picktools":\n'
    '\t\tif reg is not None:\n'
    '\t\t\tres = reg.OpenSettingsUI(tab="tools", panel=True)\n'
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


def EnsureRootEntryPoints(root):
    """Give a toolkit root its entry-point pars and the forwarder DAT.

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
    return {'root': root.path, 'page': pg.name,
            'pars': [n for n, _, _ in ROOT_ENTRY_POINTS],
            'forwarder': pe.path}


# Dev-only par pages, removed from the shipped root. Version Ctrl is
# authoring metadata (Vcname/Vcauthor/Vcbuild/save timestamps) that means
# nothing in a user's project. About and Registry SHIP: the update controls
# are user-facing, and the root is itself a config-registry host, so a
# shipped root keeps roaming its own settings.
BOOTSTRAP_STRIP_PAGES = ('Version Ctrl',)
# Dev-root children that ship INSIDE the bootstrap: the install rails.
# FNS_Updater is deliberately not here -- the dev copy is an Embody-tracked
# master with file bindings, so the shipped one is the clean dist artifact.
BOOTSTRAP_KEEP = (COMP_NAME, 'webBrowser')


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
    _resetInstallerState(inst)

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

    EnsureRootEntryPoints(root)

    return _export(root, out_path, stage)
