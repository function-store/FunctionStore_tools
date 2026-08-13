"""Build packaging/dist/FNS_Installer.tox from InstallerExt.py.

Runs INSIDE TouchDesigner:

    exec(open('packaging/build_installer.py').read()); result = BuildInstaller()

The installer COMP is a BUILD ARTIFACT, not a hand-made component: it
embeds a snapshot of InstallerExt.py, so editing that file means rebuilding
the tox. Constructing it from a script keeps the two from drifting and
means the artifact can be recreated on any machine.

It is deliberately tiny (~4 KB) and self-contained -- the portable export
inlines the extension DAT and clears its file binding -- so it can be
dropped into a project that has nothing else installed.
"""

import os

STAGING = '/sys/quiet'          # ephemeral: never saved with the project
COMP_NAME = 'FNS_Installer'
OUT = 'packaging/dist/FNS_Installer.tox'


def _repo(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def BuildInstaller(out_path=OUT):
    stage = op(STAGING).op('installer_build')
    if stage:
        stage.destroy()
    stage = op(STAGING).create(baseCOMP, 'installer_build')
    comp = stage.create(baseCOMP, COMP_NAME)
    comp.nodeX, comp.nodeY = 0, 0

    pg = comp.appendCustomPage('Install')
    p = pg.appendFile('Manifestfile', label='Manifest')[0]
    p.default = p.val = 'packaging/manifest.json'
    p = pg.appendFile('Selectionfile', label='Selection')[0]
    p.default = p.val = 'packaging/example-selection.json'
    p = pg.appendStr('Target', label='Install Into')[0]
    p.help = "Leave blank to use this project's toolkit container, or create one."
    pg.appendPulse('Plan', label='Plan (dry run)')
    pg.appendPulse('Install', label='Install')
    p = pg.appendToggle('Replace', label='Replace Existing')[0]
    p.help = 'Re-load packages that are already installed.'
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
    pe.par.pars = 'Plan Install'
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
               '\treturn\n')

    dest = _repo(out_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    op.Embody.ExportPortableTox(target=comp, save_path=dest)
    ok = os.path.exists(dest)
    info = {'built': comp.path, 'out': dest, 'exported': ok,
            'bytes': os.path.getsize(dest) if ok else 0,
            'extensions_ready': bool(comp.extensionsReady),
            'errors': comp.errors(recurse=True).splitlines()[:3] or 'clean'}
    stage.destroy()
    return info
