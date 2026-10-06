"""Move `Pkgversion` off its dedicated `Package` page onto `About`.

One-shot migration. Runs INSIDE TouchDesigner (needs `op`, `project`).
Drive it from Envoy with:

    exec(open('packaging/migrate_pkgversion_page.py').read()); result = Migrate()

A whole custom page for one string par was page clutter. `About` is
already the meta page the toolkit converges on (RegistryBase orders
Registry ahead of About / Common / Version Ctrl), so the version belongs
there. Nothing anywhere reads the page: build_manifest.py, publish.py and
ExtUpdater.py all do `getattr(comp.par, 'Pkgversion')`, which is
page-agnostic, so the move changes no rail.

WHAT THE LIVE SURVEY FOUND (2026-08-14), which this also repairs:

  * The `Package` pages were not holding just Pkgversion -- registry
    section pars (Cf*/Tb*/Nb*/Om*) were stranded there while each comp's
    `Registry` page sat empty. That is TD's page-churn rehoming (see
    RegistryBase._reclaimToolPar): destroying a page RELOCATES its pars,
    it does not delete them. Those strays go back to `Registry`;
    _orderToolSection re-orders them at next registration.
  * Five comps had lost `Pkgversion` entirely (a tox reload reverts page
    state) while manifest.json still publishes 1.0.0 for them. They are
    re-stamped at the manifest's value, so Compare() reads `current`,
    not `unversioned`.

MECHANICS (RegistryBase._reclaimToolPar is the precedent):
  * `par.page = <Page>` relocates a custom par between custom pages.
  * The emptied `Package` page is destroyed only once verifiably empty,
    so nothing can be silently rehomed by the destroy itself.

A page move alone is NOT a reason to bump Pkgversion -- the live
components now differ from the last-exported artifacts, and that is fine
until the next release re-exports them.
"""

OLD_PAGE = 'Package'
NEW_PAGE = 'About'
REG_PAGE = 'Registry'          # RegistryBase.TOOL_PAGE_NAME
STAMP = '1.0.0'                # what manifest.json already publishes
LABEL = 'Package Version'      # matches the surviving stamped pars

# Same roster the manifest is built from -- one discovery, no second list
# to drift.
exec(open('packaging/build_manifest.py', encoding='utf-8').read())


def _page(comp, name):
    return next((pg for pg in comp.customPages if pg.name == name), None)


# registry section par = 2-char registry prefix + one of these stems
# (RegistryBase TOOL_PAGE_PREFIX + section par names, lowercased)
_SECTION_STEMS = ('section', 'autoregister', 'register', 'regstatus',
                  'createcallbacks', 'autoload', 'persistpars',
                  'excludepars', 'excludepages', 'menuorder',
                  'displayed', 'barwidth', 'align')


def _isSectionPar(name):
    return name != 'Pkgversion' and name[2:].lower() in _SECTION_STEMS


def Migrate(dry=False):
    moved, already, stamped, reclaimed, dropped, kept, errors = \
        [], [], [], [], [], [], []
    for c in Packages():
        try:
            about = _page(c, NEW_PAGE)
            if about is None and not dry:
                about = c.appendCustomPage(NEW_PAGE)

            p = getattr(c.par, 'Pkgversion', None)
            if p is None:
                if not dry:
                    about.appendStr('Pkgversion', label=LABEL)
                    p = c.par.Pkgversion
                    p.default = STAMP
                    p.val = STAMP
                    # cosmetic: hand-edits go through the PI lister / the
                    # release flow, not the par dialog (scripts still write)
                    p.readOnly = True
                stamped.append(c.name)
            elif p.page.name == NEW_PAGE:
                already.append(c.name)
            else:
                if not dry:
                    p.page = about
                moved.append(c.name)

            old = _page(c, OLD_PAGE)
            if old is None:
                continue

            # Registry section pars stranded here by page churn go home;
            # anything unexpected stays put and blocks the page destroy.
            reg = _page(c, REG_PAGE)
            blockers = []
            for x in list(old.pars):
                if x.name == 'Pkgversion':
                    continue          # moved above (or about to be, in dry)
                if reg is not None and _isSectionPar(x.name):
                    if not dry:
                        x.page = reg
                    reclaimed.append(f'{c.name}.{x.name}')
                else:
                    blockers.append(x.name)

            if blockers:
                kept.append(f'{c.name}: {blockers}')
            elif dry:
                dropped.append(c.name)
            elif not list(old.pars):
                old.destroy()
                dropped.append(c.name)
            else:
                kept.append(f'{c.name}: {[x.name for x in old.pars]}')
        except Exception as e:
            errors.append(f'{c.name}: {e}')
    return {'dry': dry, 'moved': moved, 'already': already, 'stamped': stamped,
            'reclaimed': reclaimed, 'page_dropped': dropped,
            'page_kept': kept, 'errors': errors}
