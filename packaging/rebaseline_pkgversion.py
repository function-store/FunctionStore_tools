"""Rebaseline every package's version to BASELINE (owner decision 2026-08-28).

The v3 release restarts package versions at 3.0.0. This script applies that
baseline to the LIVE project, idempotently, encoding the version contract as
it actually is:

  * `FNS_About/Pkgversion` (constant, on each package's vendored About COMP)
    is the SOURCE OF TRUTH -- the one hand-maintained number.
  * The package root's `Pkgversion` is a MIRROR (expression or bind on
    `./FNS_About`), which is what build_manifest reads. A root left in
    constant mode is a drift channel and gets repaired to the mirror --
    FNS_Updater had exactly this (root hand-bumped to 1.3.0, About stranded
    at 1.0.10).
  * `Version` is only a FALLBACK for components that predate Pkgversion
    (RegistryBase._get_version reads Pkgversion first). On FNS packages it
    must never be an independently-maintained second number, so constant
    Version pars become mirrors of the same About par. TDX_SearchPalette is
    exempt (third-party pattern, its Version reads its own Help COMP).

Run INSIDE TouchDesigner (execute_python or textport):

    exec(open('packaging/rebaseline_pkgversion.py', encoding='utf-8').read())
    print(Rebaseline(dry=True))     # report only
    print(Rebaseline())             # apply

Live pars persist only when the suspect toxes / .toe are saved (the release
landing pass) -- until then a project reload reverts them, and re-running
this script is the one-call recovery.
"""

BASELINE = '3.0.0'
MIRROR = "op('./FNS_About').par.Pkgversion"
RAILS = ('FNS_Installer', 'webBrowser')
VERSION_EXEMPT = ('TDX_SearchPalette',)


def _packages():
    """Same roster the manifest ships: depth-1 tracked suspects."""
    out = []
    for c in op('/FNSTools').children:
        if c.family != 'COMP' or c.name in RAILS:
            continue
        p = getattr(c.par, 'externaltox', None)
        if not (p and p.eval() and 'pi_suspect' in c.tags):
            continue
        out.append(c)
    return sorted(out, key=lambda c: c.name.lower())


def Rebaseline(dry=False):
    bumped, already, root_fixed, ver_mirrored, problems = [], [], [], [], []
    for c in _packages():
        try:
            about = c.op('FNS_About')
            ap = getattr(about.par, 'Pkgversion', None) if about else None
            if ap is None:
                problems.append((c.name, 'no FNS_About/Pkgversion'))
                continue
            old = str(ap.eval())
            if old == BASELINE:
                already.append(c.name)
            else:
                if not dry:
                    ap.val = BASELINE
                    ap.default = BASELINE
                bumped.append((c.name, old))

            rp = getattr(c.par, 'Pkgversion', None)
            if rp is not None and rp.mode == ParMode.CONSTANT:
                if not dry:
                    rp.expr = MIRROR
                    rp.mode = ParMode.EXPRESSION
                root_fixed.append(c.name)

            vp = getattr(c.par, 'Version', None)
            if (vp is not None and vp.mode == ParMode.CONSTANT
                    and c.name not in VERSION_EXEMPT):
                if not dry:
                    ro = vp.readOnly
                    vp.readOnly = False
                    vp.expr = MIRROR
                    vp.mode = ParMode.EXPRESSION
                    vp.readOnly = ro
                ver_mirrored.append(c.name)
        except Exception as e:
            problems.append((c.name, str(e)))
    return {'baseline': BASELINE, 'dry': dry,
            'bumped': bumped, 'already': len(already),
            'root_repaired': root_fixed, 'version_mirrored': ver_mirrored,
            'problems': problems}
