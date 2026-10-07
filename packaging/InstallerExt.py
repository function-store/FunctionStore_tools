"""FNS_Installer -- install a picked subset of the toolkit.

ONE implementation, two entry points:
  * as a COMP extension (drop FNS_Installer.tox into a project, set the two
    file parameters, pulse Plan then Install);
  * as a script, via packaging/install.py, for headless/Envoy use.

Consumes what the rest of the packaging track produces: `manifest.json`
(what exists) and a configurator `selection.json` (what you want). Step 3
of docs/ConfiguratorDistribution.md §4 -- the rail that needs no web
presence, because the artifacts can simply be local files.

ORDER MATTERS. Core lands first: every tool ships a stamped registry HOST
whose master lives in a core package, and a host with no master cannot
clone. The manifest's `requires` already encodes that, so the plan is a
topological walk of it rather than a hardcoded list.
"""

import hashlib
import json
import os

# --- the toolkit's folder in the user palette ------------------------------
# <user palette>/FNSTools (docs/PaletteFolderContract.md). Until 2026-09-18
# this was FNStools_ext; a legacy folder is renamed into place the first
# time any reader looks. This function is carried verbatim by every FNS
# extension that reads the folder: they ship as separate toxes and cannot
# share a module, and whichever reader gets there first must be able to
# migrate on its own. Master copy: FNS_Updater/ExtUpdater.py.
PALETTE_DIR = 'FNSTools'
LEGACY_PALETTE_DIR = 'FNStools_ext'


def _fnsPaletteRoot():
    """'<user palette>/FNSTools', migrating a legacy FNStools_ext folder into
    place on first sight; '' when this install has no user palette folder."""
    try:
        base = str(app.userPaletteFolder).replace('\\', '/').rstrip('/')
    except Exception:
        return ''
    if not base:
        return ''
    new = '%s/%s' % (base, PALETTE_DIR)
    legacy = None
    try:
        for fn in os.listdir(base):
            if fn.lower() == LEGACY_PALETTE_DIR.lower() and os.path.isdir('%s/%s' % (base, fn)):
                legacy = '%s/%s' % (base, fn)
                break
    except Exception:
        pass
    if legacy is None:
        return new
    if not os.path.isdir(new):
        try:
            os.rename(legacy, new)
            return new
        except OSError as e:
            # a file held open, most likely; this session keeps using the
            # old folder and the next start tries again
            debug('FNS: could not rename %s to %s (%s)' % (legacy, new, e))
            return legacy
    # both exist (a race, or an older launcher recreated the legacy
    # folder): whatever the legacy folder holds that the new one lacks
    # moves over, and the legacy folder goes once it is empty
    # entry by entry, each on its own: a folder something still watches
    # (TDFam's Folder DAT on the old family tree) refuses to move, and that
    # must not keep the store or the config from moving. A folder both
    # sides hold is merged the same way one level down, because a reader
    # that seeds its file when it is missing (OpTemplates) can have made
    # the new folder before this ran. A FILE both sides hold stays as the
    # new side has it, and the legacy copy is kept aside under
    # FNSTools/legacy_<old name>/ at its old relative path, never deleted:
    # the new side's file is usually the later state, but it can be a seed
    # (OpTemplates writes its default library when its file is missing)
    # while the legacy one is the user's work. OpTemplates looks there
    # before seeding again. Deleting it lost a user's library (2026-09-18).
    left = []

    def merge(src_dir, dst_dir):
        for fn in os.listdir(src_dir):
            src, dst = '%s/%s' % (src_dir, fn), '%s/%s' % (dst_dir, fn)
            try:
                if not os.path.exists(dst):
                    os.rename(src, dst)
                elif os.path.isdir(src) and os.path.isdir(dst):
                    merge(src, dst)
                    if not os.listdir(src):
                        os.rmdir(src)
                elif os.path.isfile(src) and os.path.isfile(dst):
                    rel = os.path.relpath(src, legacy).replace('\\', '/')
                    keep = '%s/legacy_%s/%s' % (new, LEGACY_PALETTE_DIR, rel)
                    if os.path.exists(keep):
                        os.remove(src)
                    else:
                        os.makedirs(os.path.dirname(keep), exist_ok=True)
                        os.rename(src, keep)
            except OSError as e:
                left.append('%s (%s)' % (fn, e))

    try:
        merge(legacy, new)
        if not os.listdir(legacy):
            os.rmdir(legacy)
    except Exception as e:
        left.append(str(e))
    if left:
        debug('FNS: legacy palette folder %s not fully merged: %s' % (legacy, '; '.join(left)))
    return new

import shutil
import time

DEFAULT_MANIFEST = 'packaging/manifest.json'

# What each package was installed FROM. UPDATER/ExtUpdater.py reads exactly
# these four columns to decide what is stale, so the two must stay in step.
# It lives in the project because it is project state: it travels with the
# .toe, and it is what makes an interrupted pass safe to simply re-run.
INSTALLED_DAT = 'installed'
# the root's own config host, shipped inside the bootstrap (build_installer.ROOT_HOST)
ROOT_HOST = 'FNS_ConfigHost'
INSTALLED_COLS = ['package', 'sha256', 'release', 'when', 'remember']
# `remember`: '1' (or empty, every row written before the column existed) is
# part of the project's setup -- it rides the root's last_install record into
# the next project's "Set up like last time". '0' was PLACED here only (the
# picker's Place on a `placeonce` package): installed and updated like any
# other, never carried into another project. docs/PlaceOnce.md.
REMEMBER_COL = 4


def _isPlacedOnly(t, i):
    """Row i of the installed table was placed here only (remember == '0')."""
    try:
        return t.numCols > REMEMBER_COL and t[i, REMEMBER_COL].val == '0'
    except Exception:
        return False


def PlacedOnly(parent_comp):
    """Names this project holds as placed-only (never remembered)."""
    t = parent_comp.op(INSTALLED_DAT) if parent_comp is not None else None
    if t is None or t.numRows < 2 or t[0, 0].val != INSTALLED_COLS[0]:
        return set()
    return {t[i, 0].val for i in range(1, t.numRows)
            if t[i, 0].val and _isPlacedOnly(t, i)}


# --- tools this machine has been shown --------------------------------
# docs/NewToolsAndFamilyFreshness.md, C. The picker announces a tool once,
# the first time this machine opens it after a release adds it. "Shown" is
# machine-wide (every project on the machine agrees), in the palette's
# config folder. Pure file logic apart from the palette root, so
# tests/test_new_tools.py runs it on a scratch folder.
SEEN_SUBPATH = 'config/seen_packages.json'


def _seenPath(root=None):
    return '%s/%s' % (root if root is not None else _fnsPaletteRoot(), SEEN_SUBPATH)


def _pickableTools(manifest):
    """The names the picker offers as cards: tools, never a companion."""
    # a preview (not released yet) is never announced or recorded as shown:
    # it is announced to everyone the release it goes public
    return [str(p.get('name')) for p in (manifest or {}).get('packages', [])
            if p.get('kind') == 'tool' and not p.get('companion') and p.get('name')
            and not p.get('preview')]


def _introducedNow(pkg):
    """A package this release line introduced (its note says so)."""
    return str(pkg.get('whatsnew') or '').strip().lower().startswith('new package')


def SeenPackages(root=None):
    """The names this machine has been shown, or None before the first
    record exists."""
    path = _seenPath(root)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        return [str(n) for n in (doc.get('seen') or [])]
    except Exception:
        return None


def _seenDoc(root=None):
    path = _seenPath(root)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _writeSeenDoc(doc, root=None):
    path = _seenPath(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.part'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1)
    os.replace(tmp, path)


def MarkSeen(names, root=None):
    """Add `names` to the machine's shown list; returns the new list. The
    record's other keys (the announce preference) are kept."""
    doc = _seenDoc(root)
    have = set(str(n) for n in (doc.get('seen') or []))
    have.update(str(n) for n in (names or []) if n)
    doc.update({'schema': 1, 'seen': sorted(have)})
    _writeSeenDoc(doc, root)
    return sorted(have)


def AnnounceNewTools(root=None):
    """Does the picker open "New since you last looked" by itself? On
    unless the user turned it off (owner, 2026-09-25: a preference)."""
    return _seenDoc(root).get('announce') is not False


def SetAnnounceNewTools(on, root=None):
    doc = _seenDoc(root)
    doc['schema'] = 1
    doc.setdefault('seen', [])
    if on:
        doc.pop('announce', None)
    else:
        doc['announce'] = False
    _writeSeenDoc(doc, root)
    return bool(on)


def UnseenTools(manifest, installed=(), firstrun=False, root=None):
    """The picker's "new since you last looked": tools this machine has not
    been shown, never the whole catalog to someone new.

    - A first run (a fresh bootstrap) is shown nothing: every current tool
      is recorded as shown, and the guided setup is the introduction.
    - An install with no record yet (everyone on the release that brings
      this) starts from what it knows: everything is shown except the
      tools this release line introduced that it has not installed.
    - After that, whatever the record lacks is new.
    """
    tools = _pickableTools(manifest)
    seen = SeenPackages(root)
    if seen is None:
        if firstrun:
            MarkSeen(tools, root)
            return []
        index = {str(p.get('name')): p for p in (manifest or {}).get('packages', [])}
        have = set(installed or ())
        fresh = [n for n in tools if _introducedNow(index.get(n) or {}) and n not in have]
        MarkSeen([n for n in tools if n not in fresh], root)
        return sorted(fresh)
    known = set(seen)
    return sorted(n for n in tools if n not in known)


def RecordFirstInstall(manifest, root=None):
    """A first install the picker never saw (TDX Launcher Ultra, the paste
    rail, any headless Install) is a first run too: whatever picked its
    tools was the introduction, so every current tool is recorded as shown.
    Only while the machine has no record; True when it wrote one."""
    if SeenPackages(root) is not None:
        return False
    MarkSeen(_pickableTools(manifest), root)
    return True


# --- pure helpers (no COMP required) ----------------------------------

def RepoPath(*parts):
    return os.path.join(project.folder, *parts).replace('\\', '/')


def LoadJson(path, what):
    full = path if os.path.isabs(path) else RepoPath(path)
    if not os.path.exists(full):
        raise FileNotFoundError('%s not found: %s' % (what, full))
    with open(full, 'r', encoding='utf-8') as f:
        return json.load(f)


def _order(names, index):
    """Core-first topological order over `requires`.

    Cycles cannot arise while tools depend only on core (the rule the
    manifest generator enforces), but a cycle must never hang an
    installer, so a revisited name is emitted rather than spun on.
    """
    done, out = set(), []

    def visit(name, seen):
        if name in done or name not in index:
            return
        if name in seen:
            out.append(name)
            done.add(name)
            return
        for dep in index[name].get('requires', []):
            visit(dep, seen | {name})
        if name not in done:
            out.append(name)
            done.add(name)

    for n in names:
        visit(n, set())
    return out


ROOT_NAME = 'FNSTools'


def DefaultTarget(owner=None):
    """Where packages land.

    An installer that ships INSIDE a container (the bootstrap .tox)
    installs into that container, WHATEVER it is called -- TD numbers a
    second drop to FunctionStore_tools_20261, and matching the parent by
    its literal name sent that installer at the OTHER copy's root.
    Otherwise: the project's toolkit container if it has one, else a new
    one next to Embody (dev) or at / (a bare project).
    """
    if owner is not None:
        parent = owner.parent()
        if parent is not None and parent.path != '/':
            return parent.path
    existing = op('/' + ROOT_NAME)
    if existing is not None:
        return existing.path
    embody = getattr(op, 'Embody', None)
    home = embody.parent().path if embody is not None else '/'
    return home.rstrip('/') + '/' + ROOT_NAME


def PanePlacement(fallback_path, lock=None):
    """Where a `placement: pane` package lands: the network the user is
    working in -- the current pane's owner when that pane is a network
    editor, else the first network editor's owner.

    Returns (path, note). Falls back to `fallback_path` (with the reason
    in the note) when no network editor is open, or when the visible
    network is one an install must not touch: a source checkout
    (SourceLock), or /ui and /sys, which TD rebuilds on open so anything
    landed there silently vanishes with the session.
    """
    try:
        pane = ui.panes.current
        if pane is None or pane.type != PaneType.NETWORKEDITOR:
            pane = next((p for p in ui.panes
                         if p.type == PaneType.NETWORKEDITOR), None)
        owner = pane.owner if pane is not None else None
    except Exception:
        owner = None
    if owner is None:
        return fallback_path, 'no network editor open'
    top = '/' + owner.path.lstrip('/').split('/', 1)[0] if owner.path != '/' else '/'
    if top in ('/ui', '/sys'):
        return fallback_path, ('%s is rebuilt on every project open -- '
                               'nothing lands there' % top)
    why = (lock or SourceLock)(owner.path)
    if why:
        return fallback_path, why
    return owner.path, ''


def CommunityLock(target_path):
    """Why a community tool may not be ADDED to `target_path`, or ''.

    Narrower than SourceLock on purpose: a community placement adds one new
    component and never replaces or removes anything, so a network Embody
    tracks (the project root, typically) is fine to add to. What stays off
    limits is the toolkit's own source tree in its development project."""
    home = _sourceHome()
    if home and (target_path == home or target_path.startswith(home + '/')):
        return ('%s is inside the toolkit source (%s); open another network '
                'to place it in' % (target_path, home))
    return ''


def StoreFolder():
    """The machine-wide palette store. By contract a MIRROR of the bucket:
    nothing in it is anyone's work, so a file that disagrees with the
    manifest is stale cache, never a modification to preserve."""
    return '%s/store' % _fnsPaletteRoot()


def DefaultManifest():
    """The manifest to read when none is given: the palette store's, if the
    store has ever been refreshed -- artifacts sit beside it, so a user
    project needs no further configuration -- else the repo's (dev)."""
    store = StoreFolder() + '/manifest.json'
    if os.path.exists(store):
        return store
    return DEFAULT_MANIFEST


def _inStore(path):
    return (os.path.normcase(os.path.dirname(os.path.abspath(path)))
            == os.path.normcase(os.path.abspath(StoreFolder())))


# --- the source-checkout lock ------------------------------------------
# The toolkit's own dev project carries an FNS_Installer too (the bootstrap
# is that root castrated), and the picker pre-checks every live child of
# its target -- so an Apply there would REMOVE authored masters. This
# mirrors the updater's _refuseReason, layer for layer: the source tree is
# detected by the packaging generator beside the .toe (no install has one)
# AND the target being the container it exports from; Embody-tracked rows
# under the target are the finer second lock. A scratch container elsewhere
# in the source project stays installable -- that is how installs are
# tested (ConfiguratorDistribution 4.1).

def _sourceHome():
    """The container the source checkout exports from, read off
    build_manifest.py's TOOLKIT constant; '' when this is not a source
    checkout."""
    gen = os.path.join(project.folder, 'packaging', 'build_manifest.py')
    if not os.path.exists(gen):
        return ''
    try:
        with open(gen, encoding='utf-8') as f:
            for line in f:
                if line.startswith('TOOLKIT'):
                    return line.split('=', 1)[1].strip().strip('\'"')
    except Exception:
        pass
    return ''


def _embodyRows(comp_path):
    """Externalization rows Embody tracks at or under this path."""
    tsv = os.path.join(project.folder, 'externalizations.tsv')
    if not os.path.exists(tsv):
        return []
    prefix = comp_path + '/'
    hits = []
    try:
        with open(tsv, 'r', encoding='utf-8') as f:
            for line in f:
                path = line.split('\t', 1)[0]
                if path == comp_path or path.startswith(prefix):
                    hits.append(path)
    except Exception:
        pass
    return hits


def SourceLock(target_path):
    """Why nothing may be installed into or removed from `target_path`,
    or '' when it is an ordinary install target."""
    home = _sourceHome()
    if home and target_path == home:
        return ('%s is the toolkit SOURCE root: its components are authored '
                'here, not installed, and the published .tox files are its '
                'output. Point Install Into at a scratch container instead.'
                % target_path)
    rows = _embodyRows(target_path)
    if rows:
        return ('Embody authors %d tracked file(s) under %s; installing or '
                'removing here would destroy work.' % (len(rows), target_path))
    return ''


def IsDevProject():
    """True when Private Investigator's DEV toggle says this is the toolkit's
    own development project. PI is the authoring apparatus (release toxes,
    the publish rails); the toggle is the owner's explicit declaration, so
    nothing here infers dev-ness from folder contents. Found by the par,
    not by a path: PI carries no shortcut and a root-level name is not a
    contract."""
    for c in op('/').children:
        if c.family != 'COMP':
            continue
        p = getattr(c.par, 'Dev', None)
        if p is not None:
            try:
                return bool(p.eval())
            except Exception:
                return False
    return False


def FolderLock(folder):
    """Why package files may not be written to `folder`, or ''.

    'project' mode copies artifacts into <project folder>/FNStools by
    default. In the toolkit's own development project that folder IS the
    externalized source tree (Embody writes every authored extension
    there -- and Windows does not distinguish FNStools from FNSTools), so
    a test install with the wrong menu value would bury generated .tox
    files among tracked sources. Gated on PI's DEV toggle; an explicit
    Package Folder OUTSIDE the project folder stays allowed."""
    if not folder or folder == 'shared':
        return ''
    if not IsDevProject():
        return ''
    root = os.path.normcase(os.path.abspath(project.folder))
    dest = os.path.normcase(os.path.abspath(folder if os.path.isabs(folder)
                                            else RepoPath(folder)))
    if dest == root or dest.startswith(root + os.sep):
        return ("Package Files 'project' would write into %s, inside the "
                "toolkit's development project (Private Investigator: DEV "
                "on) -- its source tree. Choose Embedded or Shared, or point "
                "Package Folder outside the project folder."
                % folder.replace('\\', '/'))
    return ''


def _artifactPath(art, name, manifest_path):
    """Where this artifact actually is.

    Artifacts sit NEXT TO the manifest that describes them -- that is true
    of the published bucket and of the palette store, so installing from
    either needs no extra configuration. The repo-relative `path` is the
    fallback, which is what a dev checkout (packaging/dist/) uses.
    """
    full_manifest = (manifest_path if os.path.isabs(manifest_path)
                     else RepoPath(manifest_path))
    beside = os.path.join(os.path.dirname(full_manifest), name + '.tox')
    if os.path.exists(beside):
        return beside.replace('\\', '/')
    return RepoPath(art['path']) if art.get('path') else beside.replace('\\', '/')


def _artifactFor(pkg, vid='base'):
    """One build's artifact off a manifest row: the Base build is the
    row's own `artifact`, a variant's sits under `variants.<vid>`."""
    if vid and vid != 'base':
        return (((pkg or {}).get('variants') or {}).get(vid) or {}).get('artifact')
    return (pkg or {}).get('artifact')


def VariantPicks(manifest, target):
    """{name: vid} for every manifest row with variants: the highest build
    the account holds, asked of the FNS_Updater beside the target root
    (the same answer its fetch list gives, so the plan and the download
    agree). No updater, or no answer, is the Base build."""
    picks = {}
    root = op(target) if target else None
    upd = root.op('FNS_Updater') if root is not None else None
    for pkg in manifest.get('packages', []):
        if not pkg.get('variants'):
            continue
        vid = 'base'
        try:
            if upd is not None and getattr(upd, 'BestVariant', None) is not None:
                vid = str(upd.BestVariant(pkg['name'], manifest) or 'base')
        except Exception:
            vid = 'base'
        picks[pkg['name']] = vid
    return picks


def ResolvePlan(selection_path, manifest_path=DEFAULT_MANIFEST, target=None,
                minimal=False, sources=None):
    """Resolve a selection into an ordered install plan. Never mutates.

    `selection_path` may be a dict, for callers that build a selection in
    memory rather than reading one off disk (the command rail).

    `minimal` installs EXACTLY what was asked plus its derived
    `requires`, skipping the core force -- for a request that arrives
    programmatically ("install autosave") rather than as a user picking a
    toolkit. See docs/LauncherToolkitBoundary.md: forcing 10 core
    packages onto someone who asked for one feature is a bait-and-switch,
    and these self-contained packages plug into none of it.

    `sources` maps package name -> a local artifact path, letting a
    caller install from bytes it already has (a launcher's bundled free
    artifact) instead of the store. Such a file is a hash_warning rather
    than `stale` when it disagrees with the manifest -- stale means "the
    store lied", which a deliberately-supplied path never is -- so it
    installs, records the sha that actually landed, and Compare() offers
    the manifest's version as an upgrade once the machine is online.
    """
    manifest = LoadJson(manifest_path, 'manifest')
    sel = (selection_path if isinstance(selection_path, dict)
           else LoadJson(selection_path, 'selection'))
    index = {p['name']: p for p in manifest['packages']}
    sources = {str(k): str(v) for k, v in (sources or {}).items()}
    # A SELECTION may ask for minimal too, not just a caller. That is what
    # lets an existing integration opt in without adopting a new code
    # path: anything that already writes a selection.json and pulses
    # Install (the launcher's fns_install verb does exactly this) gets
    # minimal behaviour by adding one key, rather than by moving to the
    # command rail.
    minimal = bool(minimal or sel.get('minimal'))

    wanted = list(sel.get('install') or (sel.get('core', []) + sel.get('tools', [])))
    unknown = [n for n in wanted if n not in index]
    # Companions (manifest `companion: family`) exist only for others: the
    # FNS operator family, its TDFam registry and the FNS tab have nothing
    # to show without a family member (owner decision 2026-09-17). Whatever
    # a selection says about them, they install exactly when it holds a
    # member and not otherwise -- so an installed family with no members
    # left becomes an ordinary removal candidate below.
    #
    # And a member does not force it (owner decision 2026-09-17): some
    # users want the tools in their palette without a new tab in the OP
    # Create dialog. The selection's `family` flag decides; a selection
    # that does not say keeps the project as it is (FamilyWanted).
    tgt = target or DefaultTarget()
    if isinstance(tgt, OP):
        tgt = tgt.path
    root_comp = op(tgt)
    companions = [p['name'] for p in manifest['packages']
                  if p.get('companion') == 'family']
    if companions:
        has_member = any(index[n].get('family') for n in wanted if n in index)
        wanted = [n for n in wanted if n not in companions]
        if has_member and FamilyWanted(sel, index, companions, root_comp):
            wanted.extend(companions)
    # Core is not optional: a selection that omits it is a broken selection,
    # not a request to go without the infrastructure every tool plugs into.
    # UNLESS this is a minimal request, where the caller named what it
    # wants and `requires` still supplies anything those packages actually
    # depend on (_order walks it transitively).
    if not minimal:
        for c in manifest.get('core', []):
            if c not in wanted:
                wanted.append(c)

    # PLACE (docs/PlaceOnce.md): tools put into THIS project without joining
    # the setup, so "Set up like last time" never carries them on. They are
    # wanted like any tool; what differs is the record (remember = '0') and,
    # for an FNS family member, that placing spawns a copy into the working
    # network instead of only recording it. A package both ticked and placed
    # is simply ticked. A selection that does not SAY `place` (like last
    # time, a paste, an older writer) knows nothing about placed tools and
    # must never remove them: they are kept as they are.
    remembered = set(sel.get('tools') or []) | set(sel.get('install') or [])
    place_said = 'place' in sel
    placing = [n for n in (sel.get('place') or [])
               if n in index and index[n].get('kind') == 'tool'
               and n not in remembered]
    unknown += [n for n in (sel.get('place') or []) if n not in index]
    placed_before = PlacedOnly(root_comp)
    keep_placed = set() if place_said else placed_before
    for n in placing:
        if n not in wanted:
            wanted.append(n)

    ordered = _order([n for n in wanted if n in index], index)
    # which build of each variant package lands (docs/TierVariants.md)
    picks = VariantPicks(manifest, tgt)

    # Manifest TOOLS present in the target but not selected are removal
    # candidates -- the picker edits the project's state, not just adds to
    # it. Core is never a candidate (wanted always includes it), and
    # comps the manifest does not know (installer, webBrowser, DATs, the
    # user's own work) are never touched.
    # A minimal request is ADDITIVE and must never remove: `wanted` is one
    # package, so the ordinary "not selected means remove it" rule would
    # treat the user's whole toolkit as removal candidates. This is the
    # sharpest hazard in the minimal path -- a launcher asking for
    # autosave could otherwise uninstall everything else.
    tool_names = {p['name'] for p in manifest['packages'] if p['kind'] == 'tool'}
    # The root's own config host is a COMP child named like the catalogued
    # FNS_ConfigHost package; it is the root's, never a selection's, and
    # removing it silently cost a project its roaming root settings and
    # its last-install record (seen live 2026-09-13: "removed
    # FNS_ConfigHost" in a fresh install's report).
    to_remove = [] if minimal else (
        sorted(c.name for c in root_comp.children
               if c.family == 'COMP' and c.name in tool_names
               and c.name != ROOT_HOST
               and c.name not in wanted
               and c.name not in keep_placed) if root_comp else [])

    # `placement: pane` packages land in the user's working network and
    # `placement: root` ones beside the toolkit container -- neither is a
    # target-root child, so "already installed" is the install RECORD (or
    # the doorstep comp), and unselecting one goes through RemoveTools'
    # doorstep branch: a copy beside the root is removed for real, copies
    # deeper in the user's networks are only forgotten. The ONE exception:
    # a spawn that fell back into the target root itself is already in
    # to_remove above and must not also appear here.
    spawn_names = {p['name'] for p in manifest['packages']
                   if p.get('placement') in ('pane', 'root', 'none')}
    recorded = set()
    rec_t = root_comp.op(INSTALLED_DAT) if root_comp else None
    if rec_t is not None:
        recorded = {rec_t[i, 0].val for i in range(1, rec_t.numRows)
                    if rec_t[i, 0].val}
    # a placed tool is recorded whatever its placement (a default-placement
    # tool placed once is still a record to drop when it is unplaced), so
    # the placed-only names join the candidates here
    to_unrecord = sorted((((recorded & spawn_names) | (placed_before - set(to_remove)))
                          & tool_names)
                         - set(wanted) - set(to_remove) - keep_placed)

    steps, missing, hash_warnings = [], [], []
    for name in ordered:
        pkg = index[name]
        vid = picks.get(name, 'base')
        art = _artifactFor(pkg, vid)
        if not art:
            missing.append(name)
            continue
        supplied = sources.get(name, '')
        stem = name if vid == 'base' else '%s.%s' % (name, vid)
        path = supplied or _artifactPath(art, stem, manifest_path)
        # an absent file is a DOWNLOAD, not a failure: the picker fetches
        # exactly the selection at install time, so planning must work
        # against a store that holds only the manifest
        have = os.path.exists(path)
        # a present store file is only trustworthy if its bytes are the
        # manifest's bytes -- the store is a mirror, and a mirror can lag.
        # Elsewhere (dev dist/, a hand-pointed manifest) a mismatch can be
        # deliberately staged local work, so it is reported, never refetched.
        stale = False
        if have and art.get('sha256'):
            try:
                matches = _fileSha(path) == art['sha256']
            except Exception:
                matches = True     # unreadable surfaces at loadTox instead
            if not matches:
                # `stale` means the STORE lied -- a mirror that lagged the
                # manifest. A path a caller deliberately supplied never
                # lies; it is simply older, so it warns and installs.
                if _inStore(path) and not supplied:
                    stale = True
                else:
                    hash_warnings.append(name)
        placement = pkg.get('placement', 'toolkit') or 'toolkit'
        place = name in placing
        # placing a 'none' package (an FNS family member) means a copy in
        # the working network, the way the OP Create dialog would drop one
        if place and placement == 'none':
            placement = 'pane'
        # pane packages live wherever the user spawned them, so presence
        # is the install record; root ones live at a KNOWN address (beside
        # the toolkit container), so presence is the comp itself; 'none'
        # packages are never placed anywhere at all -- an FNS family member
        # is reached from the OP Create dialog and the family folder on
        # disk -- so the record is the only thing that can answer
        if place and placement == 'pane':
            present = name in placed_before     # placed already, not just ticked
        elif placement in ('pane', 'none'):
            present = name in recorded
        elif placement == 'root':
            home_path = tgt.rsplit('/', 1)[0] or '/'
            present = op(home_path + '/' + name) is not None
        else:
            present = op(tgt + '/' + name) is not None
        steps.append({'name': name, 'kind': pkg['kind'], 'path': path,
                      'sha256': art.get('sha256', ''),
                      'bytes': art.get('bytes', 0),
                      'release': manifest.get('release', ''),
                      'have': have, 'stale': stale,
                      'placement': placement,
                      'variant': vid,
                      'place': place,
                      'present': present})
    return {'target': tgt, 'steps': steps, 'order': [s['name'] for s in steps],
            # non-empty = every executor refuses; the reason is shown as-is
            'locked': SourceLock(tgt),
            'already_present': [s['name'] for s in steps if s['present']],
            # stale store copies re-download even when the package is
            # already present: Replace installs from the file, and healing
            # the mirror is never wrong
            # A 'none' package (an FNS family member) is "present" by its
            # record alone, but its only home IS the store file: the
            # family folder mirrors the store. A recorded member with no
            # file must still be fetched, or it never reaches the FNS tab
            # (docs/NewToolsAndFamilyFreshness.md, A).
            'to_fetch': [s['name'] for s in steps
                         if s['stale'] or (not s['have'] and (
                             not s['present'] or s['placement'] == 'none'))],
            'stale_store': [s['name'] for s in steps if s['stale']],
            'hash_warnings': hash_warnings,
            'to_remove': to_remove,
            'to_unrecord': to_unrecord,
            'placing': [s['name'] for s in steps if s['place']],
            'minimal': bool(minimal),
            'missing_artifact': missing, 'unknown_packages': unknown}


def _verify(comp):
    """Installed means the COMP exists, its extensions are up and it
    reports no errors -- not merely that loadTox returned.

    An error is given ONE forced recook before it counts: expressions
    that reference the package's own extension (`ext.X...`) evaluate
    during loadTox BEFORE the extension exists, and the resulting error
    sticks on nodes that nothing recooks (seen on FNS_HotkeyManager's
    parexec). Recooking with the extension up separates that init-order
    noise from real breakage."""
    if comp is None or not comp.valid:
        return {'ok': False, 'why': 'comp missing after load'}
    errs = comp.errors(recurse=True)
    if errs:
        try:
            comp.cook(force=True, recurse=True)
        except Exception:
            pass
        errs = comp.errors(recurse=True)
    return {'ok': not errs, 'why': (errs.splitlines()[0][:120] if errs else ''),
            'ops': len(comp.findChildren()),
            'extensions_ready': bool(comp.extensionsReady)}


def _bindPackage(comp, step, bind):
    """Point an installed package at a .tox on disk, per `bind`:

        None        embedded -- the package lives inside the .toe. One file
                    to move and nothing to lose track of.
        'shared'    bind to the artifact where it already sits (the palette
                    store). One copy per machine: refreshing the store
                    updates every project that shares it.
        <folder>    copy the artifact into <folder> and bind there. Each
                    project owns its files, so a project can hold a
                    modified package without touching any other.

    Binding is what gives the updater its clean path: updating a bound
    package is a file write plus a reload, not COMP surgery.
    """
    if not bind:
        return ''
    src = step['path']
    if bind == 'shared':
        dest = src
    else:
        folder = bind if os.path.isabs(bind) else RepoPath(bind)
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, step['name'] + '.tox').replace('\\', '/')
        if os.path.normcase(os.path.abspath(dest)) != \
                os.path.normcase(os.path.abspath(src)):
            shutil.copyfile(src, dest)
    comp.par.externaltox = dest
    comp.par.enableexternaltox = True
    # Save Backup of External ON: the user's .toe embeds a backup, so a
    # bound package still loads when its file has vanished (a deleted
    # store, a moved project folder). The OPPOSITE of the dev-side rule --
    # there the flag would smuggle gated bytes into the published root
    # suspect; here the user owns both files and the backup is the
    # self-healing.
    p = getattr(comp.par, 'savebackup', None)
    if p is not None:
        p.val = True
    return dest


def _fileSha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def FamilyWanted(sel, index, companions, root_comp):
    """Whether a selection that holds a family member wants the family
    (the FNS tab in the OP Create dialog) with it.

    The selection's `family` flag decides when it is a bool: the picker's
    switch and the last-install record write it. A selection that does
    not say (a minimal request from an agent, an older selection.json)
    keeps the project as it is: family members already installed without
    the family means someone turned it off, and adding a member must not
    bring the tab back. A project with no member yet gets the family."""
    choice = sel.get('family')
    if isinstance(choice, bool):
        return choice
    if root_comp is None:
        return True
    present = {c.name for c in root_comp.children if c.family == 'COMP'}
    rec_t = root_comp.op(INSTALLED_DAT)
    if rec_t is not None:
        present |= {rec_t[i, 0].val for i in range(1, rec_t.numRows) if rec_t[i, 0].val}
    if any(n in present for n in companions):
        return True
    return not any(index.get(n, {}).get('family') for n in present)


def _releaseFamilies(comp):
    """Unregister every TDFam family `comp` owns (or holds) before it is
    destroyed. TDFam never prunes a destroyed owner, so removing the FNS
    operator family would otherwise leave its tab in the OP Create dialog
    until TouchDesigner restarts. Done here, before the destroy, and never
    from the family's own onDestroyTD: that hook also runs on every
    extension reinit, and a promoted lookup on the owner there deadlocked
    TouchDesigner's main thread (2026-09-17). Never raises."""
    reg = getattr(op, 'FAMREGISTRY', None)
    if reg is None:
        return []
    released = []
    try:
        owners = [o for o in list(reg.RegisteredFams.values())
                  if o is not None and getattr(o, 'valid', False)
                  and (o == comp or o.path.startswith(comp.path + '/'))]
        for owner in owners:
            if reg.UnregisterFamily(owner):
                released.append(owner.path)
    except Exception as e:
        debug('FNS_Installer: could not release the families in %s: %s' % (comp.path, e))
    return released


def RemoveTools(plan):
    """Remove the plan's `to_remove` tools from the project.

    Scope rules, deliberately asymmetric:
      * PROJECT state goes: the COMP, its `installed` row, and a
        project-mode package file -- the file only when its bytes still
        match the published artifact (a modified copy is the user's work
        and stays, with a note).
      * MACHINE state stays: the store cache is other projects' business
        and a reinstall's shortcut; the tool's section in the palette
        config survives so preferences roam across remove/reinstall and
        across the user's other projects.
    """
    if plan.get('locked'):
        return {'removed': [], 'notes': ['REFUSED: ' + plan['locked']]}
    parent_comp = op(plan['target'])
    if parent_comp is None:
        return {'removed': [], 'notes': []}
    by_name = {s['name']: s for s in plan['steps']}
    removed, notes = [], []

    def destroy_and_clean(comp):
        """Destroy an installed COMP; a project-mode package file goes
        with it, but only while its bytes still match the published
        artifact -- a modified copy is the user's work and stays."""
        name = comp.name
        _releaseFamilies(comp)
        bound = ''
        p = getattr(comp.par, 'externaltox', None)
        if p is not None and comp.par.enableexternaltox.eval():
            bound = str(p.eval()).replace('\\', '/')
        comp.destroy()
        if bound:
            full = bound if os.path.isabs(bound) else RepoPath(bound)
            store_dir = os.path.dirname(by_name.get(name, {}).get('path', ''))
            in_store = store_dir and os.path.normcase(
                os.path.dirname(full)) == os.path.normcase(store_dir)
            if in_store:
                pass          # shared binding: the store file is machine-wide
            elif os.path.exists(full):
                want = by_name.get(name, {}).get('sha256', '')
                try:
                    pristine = bool(want) and _fileSha(full) == want
                except Exception:
                    pristine = False
                if pristine:
                    os.remove(full)
                else:
                    notes.append('%s: kept %s (modified)' % (name, full))

    def drop_record(name):
        t = parent_comp.op(INSTALLED_DAT)
        if t is not None:
            for i in range(t.numRows - 1, 0, -1):
                if t[i, 0].val == name:
                    t.deleteRow(i)

    for name in plan.get('to_remove', []):
        comp = parent_comp.op(name)
        if comp is None:
            continue
        destroy_and_clean(comp)
        drop_record(name)
        removed.append(name)
    # `placement: pane` packages: the spawned copies live in the user's
    # networks and are the user's work -- unselecting one clears only the
    # install record, so the picker stops reporting it as installed.
    # EXCEPT on the installer's own doorstep: a spawn sitting right beside
    # the toolkit container (a sibling at the network root, where the
    # no-editor fallback and a `/`-showing pane both land) is removed for
    # real, exactly like a root child.
    home = parent_comp.parent()
    for name in plan.get('to_unrecord', []):
        beside = home.op(name) if home is not None else None
        if beside is not None and beside.family == 'COMP':
            destroy_and_clean(beside)
            notes.append('%s: removed from %s' % (name, home.path))
        else:
            notes.append('%s: forgotten; the copies in your networks '
                         'stay yours' % name)
        drop_record(name)
        removed.append(name)
    return {'removed': removed, 'notes': notes}


def ExposeConsoleHosts(comp):
    """Flip Expose on for every FNS_Console host the landed package carries.

    Artifacts ship with console exposure OFF (packaging/pre_release_common.py
    explains why: a host whose exposure removes a local surface must not
    bootstrap itself in a bare project). Inside the toolkit, contributors
    expose by default -- and this is the ONE place that decides it: the
    install rail, as the package lands. The flag is the tool's own Registry
    page par, which the config registry persists, so a user who later turns
    it off keeps that choice across updates (an update pass never calls
    this; only a fresh install or an explicit Replace does).

    Returns the tool paths it exposed.
    """
    exposed = []
    if comp is None or not getattr(comp, 'valid', False):
        return exposed
    for tool in [comp] + comp.findChildren(type=COMP):
        host = tool.op('FNS_Console') if tool.name != 'FNS_Console' else None
        if host is None:
            continue
        # the tool-page par is the bind MASTER; the host's own par binds to
        # it once the registry's tool page exists, so write the master first
        # and the host only where no master is there yet
        p = getattr(tool.par, 'Csautoregister', None)
        if p is None:
            p = getattr(host.par, 'Autoregister', None)
        if p is None:
            continue
        try:
            if not p.eval():
                p.val = True
            exposed.append(tool.path)
        except Exception as e:
            debug('FNS_Installer: expose %s: %s' % (tool.path, e))
    return exposed


def SetRemember(parent_comp, name, remember):
    """Set an EXISTING row's remember flag, leaving its bytes record alone
    (a skipped install changes whether the tool is part of the setup, not
    what landed). No row, nothing to say."""
    t = parent_comp.op(INSTALLED_DAT) if parent_comp is not None else None
    if t is None or t.numRows < 2 or t[0, 0].val != INSTALLED_COLS[0]:
        return
    while t.numCols < len(INSTALLED_COLS):
        t.appendCol([INSTALLED_COLS[t.numCols]] + [''] * (t.numRows - 1))
    for i in range(1, t.numRows):
        if t[i, 0].val == name:
            t[i, REMEMBER_COL] = '1' if remember else '0'
            return


def RecordInstalled(parent_comp, name, sha256, release='', remember=None):
    """Upsert the install record. Written per package as it lands, so an
    interrupted install still leaves a truthful record of what is in the
    project -- which is the whole basis of the update comparison.

    `remember`: True / False writes the column ('1' / '0'); None leaves an
    existing row's value alone and writes '1' on a new row -- so an update
    pass, which only knows the bytes, never turns a placed tool into part
    of the setup or the other way round."""
    t = parent_comp.op(INSTALLED_DAT)
    if t is None:
        t = parent_comp.create(tableDAT, INSTALLED_DAT)
        t.nodeX, t.nodeY = -800, -400
        t.color = (0.35, 0.45, 0.55)
    # a fresh tableDAT already holds one empty row, so "no rows" is the
    # wrong test for "needs a header"
    if t.numRows == 0 or t[0, 0].val != INSTALLED_COLS[0]:
        t.clear()
        t.appendRow(INSTALLED_COLS)
    # a table written before `remember` existed grows the column; its old
    # rows read empty, which means remembered -- exactly what they were
    while t.numCols < len(INSTALLED_COLS):
        t.appendCol([INSTALLED_COLS[t.numCols]] + [''] * (t.numRows - 1))
    row = [name, sha256, release, time.strftime('%Y-%m-%d %H:%M:%S')]
    for i in range(1, t.numRows):
        if t[i, 0].val == name:
            for c, v in enumerate(row):
                t[i, c] = v
            if remember is not None:
                t[i, REMEMBER_COL] = '1' if remember else '0'
            return
    t.appendRow(row + ['0' if remember is False else '1'])


# Where a registry master promotes its global copy. One container instead of
# seven loose children of TD's own /sys, so anything that needs to know what
# is live -- this installer, the updater, a support dump -- reads one place.
SYS_REGISTRY_HOME = '/sys/FNS_Registries'


# The roaming config the toolkit root's own host (canonical `FNS`) writes
# into on every SaveAll -- its `last_install` state entry is what lets a
# fresh bootstrap offer "Set up like last time". Read here DIRECTLY, because
# a bare root has no registry yet to ask; the path is the registry's own
# default (ConfigRegistryExt.SUBFOLDER / FILE_NAME). A master's Configfile
# override cannot be known on a bare root and is not honoured here.
CONFIG_SUBPATH = 'config/FNStools_config.json'
ROOT_CANONICAL = 'FNS'


def LastInstall(root=None, path=None):
    """The machine's last recorded install -- {'packages', 'project', 'when',
    'bind'?} -- or None. None under project scope (the roaming file is never
    read there; the authored scope record is the root's Configscope, and a
    missing par reads as global), when there is no file, or when the file
    is unreadable or of another schema. Never raises."""
    scope = getattr(root.par, 'Configscope', None) if root is not None else None
    if scope is not None:
        try:
            if str(scope.eval()) == 'project':
                return None
        except Exception:
            pass
    path = path or (_fnsPaletteRoot() + '/' + CONFIG_SUBPATH)
    try:
        with open(path.replace('\\', '/'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get('schema') != 1:
            return None
        rec = data.get('tools', {}).get(ROOT_CANONICAL, {}).get('state', {}).get('last_install')
        if not isinstance(rec, dict) or not rec.get('packages'):
            return None
        return rec
    except Exception:
        return None


def AutoSetupWanted(root=None, path=None):
    """True when this machine asked for every fresh drop to install its
    last recorded setup with no picker: the root's `Setuplikelast`
    toggle, read live, else from the root's own `pars` section of the
    roaming config -- the host that restores that par may not have run
    yet when the welcome asks. Never under project scope (the roaming
    file is never read there), never without a record to install, and
    it never raises."""
    par = getattr(root.par, 'Setuplikelast', None) if root is not None else None
    if par is not None:
        try:
            if par.eval():
                return LastInstall(root, path) is not None
        except Exception:
            pass
    scope = getattr(root.par, 'Configscope', None) if root is not None else None
    if scope is not None:
        try:
            if str(scope.eval()) == 'project':
                return False
        except Exception:
            pass
    path = path or (_fnsPaletteRoot() + '/' + CONFIG_SUBPATH)
    try:
        with open(path.replace('\\', '/'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get('schema') != 1:
            return False
        rec = (data.get('tools', {}).get(ROOT_CANONICAL, {})
               .get('pars', {}).get('Setuplikelast'))
        if not isinstance(rec, dict):
            return False
        on = rec.get('eval', rec.get('val'))
        if not on or str(on).strip().lower() in ('0', 'false', 'off'):
            return False
        return LastInstall(root, path) is not None
    except Exception:
        return False


def PromotedRegistries():
    """The global registries live in this TD process, newest state first-hand.

    /sys is never saved with the .toe: every master re-promotes on open, so
    this is a snapshot of the running process, not of the project file. A
    freshly installed master replaces a lower-versioned global by itself
    (RegistryBase compares versions on init) -- this is how the installer
    REPORTS what happened, not how it makes it happen.
    """
    home = op(SYS_REGISTRY_HOME)
    if home is None:
        return []
    out = []
    for comp in home.children:
        version = ''
        for parname in ('Pkgversion', 'Version'):
            par = getattr(comp.par, parname, None)
            if par is not None:
                version = str(par.eval())
                break
        shortcut = getattr(comp.par, 'opshortcut', None)
        out.append({'name': comp.name,
                    'path': comp.path,
                    'version': version,
                    'shortcut': str(shortcut.eval()) if shortcut is not None else ''})
    return sorted(out, key=lambda r: r['name'])


def InstallPlan(plan, replace=False, only=None, bind=None):
    """Execute a plan from ResolvePlan. `only` limits to named packages,
    which is how a large install is batched under the MCP timeout. `bind`
    decides where the package files live -- see _bindPackage."""
    tgt = plan['target']
    if plan.get('locked'):
        return {'target': tgt, 'installed': [], 'failed': [], 'results': [],
                'locked': plan['locked'], 'registries': PromotedRegistries()}
    parent_comp = op(tgt)
    if parent_comp is None:
        home = op(tgt.rsplit('/', 1)[0] or '/')
        parent_comp = home.create(baseCOMP, tgt.rsplit('/', 1)[1])

    # Resolved ONCE per pass, not per step: every pane-placed package in
    # one install lands in the same network the user is looking at.
    pane_path, pane_note = '', ''
    if any(s.get('placement') == 'pane' for s in plan['steps']):
        pane_path, pane_note = PanePlacement(tgt)

    results = []
    for step in plan['steps']:
        name = step['name']
        if only and name not in only:
            continue
        pane = step.get('placement') == 'pane'
        rooted = step.get('placement') == 'root'
        # 'none': nothing is placed ANYWHERE. An FNS family member is
        # reached from the FNS tab of the OP Create dialog and from the
        # family folder the updater mirrors on disk, which is the whole
        # point of releasing it as a family member -- dropping a copy into
        # the user's network at install was never wanted. The install is
        # the download plus the record; there is nothing to load, nothing
        # to name, nothing to position, and nothing to destroy on removal.
        if step.get('placement') == 'none':
            if not os.path.exists(step['path']):
                results.append({'name': name, 'action': 'FAILED', 'ok': False,
                                'why': 'artifact not downloaded (%s)'
                                       % step['path']})
                continue
            # Nothing is placed, but this IS an install and the record is
            # the only evidence of it -- there is no child to find. Both
            # ResolvePlan's `present` and the updater's Compare() read it,
            # so skipping it left the picker offering the package forever
            # and the updater calling it missing.
            try:
                landed = _fileSha(step['path'])
            except Exception:
                landed = step.get('sha256', '')
            RecordInstalled(parent_comp, name, landed, step.get('release', ''),
                            remember=not step.get('place'))
            results.append({'name': name, 'ok': True,
                            'action': 'available (not placed)'})
            continue
        if pane:
            # presence is the install record (ResolvePlan); the spawned
            # copy lives wherever the user put it, so there is nothing
            # to verify or destroy here
            if step.get('present') and not replace:
                SetRemember(parent_comp, name, not step.get('place'))
                results.append({'name': name, 'ok': True,
                                'action': 'skipped (already spawned)'})
                continue
            dest = op(pane_path) or parent_comp
        elif rooted:
            # the doorstep: beside the toolkit container, a known address
            # the installer owns -- present/replace work like a root child
            home = parent_comp.parent()
            dest = home if home is not None else parent_comp
        else:
            dest = parent_comp
        existing = None if pane else dest.op(name)
        if existing is not None and not replace:
            state = _verify(existing)
            # a skipped package is NOT a failure of this install -- its
            # pre-existing errors are reported, not counted (oscMapper's
            # busy OSC port kept reading as "failed 1" on every re-run)
            state['ok'] = True
            # ticking a tool that was only placed makes it part of the
            # setup without reloading it (and placing a ticked one is a
            # no-op: ResolvePlan never places what the selection ticks)
            SetRemember(parent_comp, name, not step.get('place'))
            results.append({'name': name, 'action': 'skipped (present)',
                            **state})
            continue
        if not os.path.exists(step['path']):
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': 'artifact not downloaded (%s)' % step['path']})
            continue
        if step.get('stale'):
            # never load bytes the plan already knows are not the
            # manifest's; the picker flow re-downloads these before it
            # ever gets here, so this only fires on a manual Install
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': 'stale store copy (sha mismatch) -- '
                                   'Refresh Store in FNS_Updater, then re-Plan'})
            continue
        if existing is not None:
            existing.destroy()
        # loadTox loads the component INTO the given COMP -- it creates the
        # child itself. Pre-creating a container named after the package
        # nests it a level too deep (AutoRes/AutoRes), so load onto the
        # target and identify the new child by diffing.
        before = {c.id for c in dest.children}
        try:
            dest.loadTox(step['path'])
        except Exception as e:
            results.append({'name': name, 'action': 'FAILED', 'ok': False,
                            'why': str(e)[:140]})
            continue
        fresh = [c for c in dest.children if c.id not in before]
        comp = fresh[0] if fresh else dest.op(name)
        if comp is not None and comp.name != name:
            # TD numbers on collision; the manifest name wins -- except in
            # a pane spawn, where a same-named op is the USER'S and keeps
            # its name (the spawn stays numbered)
            if not (pane and dest.op(name) is not None):
                comp.name = name
        if (pane or rooted) and comp is not None:
            # a spawn must not land on top of the user's work: put it just
            # right of everything in the network, and hand it the selection
            try:
                sibs = [c for c in dest.children if c.id != comp.id]
                if sibs:
                    comp.nodeX = max(s.nodeX + s.nodeWidth for s in sibs) + 200
                    comp.nodeY = max(s.nodeY for s in sibs)
                comp.selected = True
                comp.current = True
            except Exception:
                pass
        bound = ''
        if comp is not None:
            try:
                bound = _bindPackage(comp, step, bind)
            except Exception as e:
                results.append({'name': name, 'action': 'installed', 'ok': False,
                                'why': 'bind failed: %s' % str(e)[:120]})
                continue
        # record the hash of the bytes that actually landed, not the
        # manifest's promise -- on a hash_warnings install they differ,
        # and the updater's comparison must start from the truth
        try:
            landed = _fileSha(step['path'])
        except Exception:
            landed = step.get('sha256', '')
        # ALWAYS on the plan target, even for a pane spawn: the record is
        # project state and the updater reads it there
        RecordInstalled(parent_comp, name, landed, step.get('release', ''),
                        remember=not step.get('place'))
        # inside the toolkit, console contributors expose by default --
        # decided here, once, as the package lands (artifacts ship dormant).
        # A pane spawn sits in the user's network, outside the toolkit, so
        # that default does not apply.
        exposed = [] if (pane or rooted) else ExposeConsoleHosts(comp)
        results.append({'name': name, 'action': 'installed', 'bound': bound,
                        'exposed': exposed,
                        'placed': dest.path if (pane or rooted) else '',
                        **_verify(comp)})
    return {'target': tgt,
            'installed': [r['name'] for r in results if r.get('action') == 'installed'],
            'failed': [r['name'] for r in results if not r.get('ok', True)],
            'results': results,
            # non-empty = pane placement fell back to the target, and why
            'pane_note': pane_note,
            'registries': PromotedRegistries()}


# --- COMP extension ---------------------------------------------------

class InstallerExt:
    """Parameter front-end over the helpers above."""

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

    def _par(self, name, default=''):
        p = getattr(self.ownerComp.par, name, None)
        return str(p.eval()).strip() if p is not None else default

    def _status(self, text):
        p = getattr(self.ownerComp.par, 'Status', None)
        if p is not None:
            p.val = text[:400]

    def _writePlan(self, plan):
        t = self.ownerComp.op('plan')
        if t is None:
            return
        t.clear()
        t.appendRow(['package', 'kind', 'state', 'MB', 'artifact'])
        if plan.get('locked'):
            t.appendRow(['(target)', '', 'LOCKED', '', plan['locked']])
        for s in plan['steps']:
            state = ('stale cache -> re-download' if s.get('stale')
                     else 'present' if s['present']
                     else 'to install' if s.get('have') else 'to download')
            t.appendRow([s['name'], s['kind'], state,
                         '%.2f' % (s.get('bytes', 0) / 1048576.0),
                         os.path.basename(s['path'])])
        for n in plan['missing_artifact']:
            t.appendRow([n, '', 'NO ARTIFACT', '', ''])
        for n in plan['unknown_packages']:
            t.appendRow([n, '', 'NOT IN MANIFEST', '', ''])

    def Plan(self):
        """Dry run: fill the plan table, change nothing."""
        selection = self._par('Selectionfile')
        if not selection:
            self._status('Set Selection to a selection.json from the '
                         'configurator first.')
            return None
        try:
            # A hand-written or pasted selection.json reaches the plan here,
            # so the Patreon hold applies to every rail, not only the picker.
            seldoc, held = self._holdPatreonLocked(
                LoadJson(selection, 'selection'))
            plan = ResolvePlan(seldoc,
                               self._par('Manifestfile') or DefaultManifest(),
                               self._par('Target')
                               or DefaultTarget(self.ownerComp))
            if held:
                plan['patreon_held'] = held
        except Exception as e:
            self._status('Plan failed: %s' % e)
            return None
        # a refused package folder locks the plan like a refused target, so
        # every consumer -- Install, the served picker -- sees one answer
        if not plan.get('locked'):
            why = FolderLock(self._bindChoice())
            if why:
                plan['locked'] = why
        self._writePlan(plan)
        if plan.get('locked'):
            self._status('LOCKED -- ' + plan['locked'])
            return plan
        note = ''
        other = op('/' + ROOT_NAME)
        if other is not None and other.path != plan['target'] \
                and not plan['target'].startswith(other.path + '/'):
            note = ' (NOTE: this project already has a toolkit at %s)' % other.path
        if plan.get('stale_store'):
            note += ('; %d stale store cop%s to re-download'
                     % (len(plan['stale_store']),
                        'y' if len(plan['stale_store']) == 1 else 'ies'))
        if plan.get('hash_warnings'):
            note += ('; HASH MISMATCH kept as-is (not the store): '
                     + ', '.join(plan['hash_warnings']))
        self._status('%d package(s) to install into %s%s%s'
                     % (len(plan['steps']), plan['target'],
                        '; MISSING: ' + ', '.join(plan['missing_artifact'])
                        if plan['missing_artifact'] else '', note))
        return plan

    def _bindChoice(self):
        """Where package files go, from the Package Files menu.

        Embedded is the default: one .toe to move, nothing to lose. The two
        bound modes exist because a package that lives in a file can be
        updated by rewriting that file -- no COMP surgery -- and 'project'
        additionally lets one project hold a modified package without
        touching any other install on the machine.
        """
        mode = self._par('Packagefiles', 'embedded') or 'embedded'
        if mode == 'embedded':
            return None
        if mode == 'shared':
            return 'shared'
        folder = self._par('Packagefolder')
        return folder or (project.folder + '/FNStools').replace('\\', '/')

    def Install(self, remove=None):
        """Install everything the plan resolves to; with `remove` (or the
        Remove Unselected toggle) also remove manifest tools the
        selection no longer includes -- the picker's apply semantics."""
        plan = self.Plan()
        if plan is None:
            return None
        if plan.get('locked'):
            self._status('REFUSED -- ' + plan['locked'])
            return None
        replace = bool(getattr(self.ownerComp.par, 'Replace', None)
                       and self.ownerComp.par.Replace.eval())
        if remove is None:
            p = getattr(self.ownerComp.par, 'Removeunselected', None)
            remove = bool(p and p.eval())
        # decided BEFORE installing: afterwards the root holds tools and the
        # picker reads it as an existing install with no seen record, which
        # announces the release line's new tools to a brand-new user
        # (field report 2026-10-06, a fresh machine installing through TDX
        # Launcher Ultra)
        first_manifest = self._firstInstallManifest(plan)
        res = InstallPlan(plan, replace=replace, bind=self._bindChoice())
        if first_manifest is not None:
            try:
                RecordFirstInstall(first_manifest)
            except Exception as e:
                debug('FNS_Installer: recording the first install as seen: %s' % e)
        res['removed'], res['remove_notes'] = [], []
        # to_unrecord alone is a removal too: an unticked record-only
        # package (a family member, a pane component) or an unplaced tool
        # has no child to destroy, and gating on to_remove left its record
        # standing -- the picker kept reporting it installed
        if remove and (plan.get('to_remove') or plan.get('to_unrecord')):
            rm = RemoveTools(plan)
            res['removed'] = rm['removed']
            res['remove_notes'] = rm['notes']
        self._status('installed %d, removed %d, failed %d%s'
                     % (len(res['installed']), len(res['removed']),
                        len(res['failed']),
                        ': ' + ', '.join(res['failed']) if res['failed'] else ''))
        self.rebuildInstallCommands()
        self._afterPasteInstall(res)
        self._keepStore()
        self.SyncFamilyToggle()
        return res

    def _firstInstallManifest(self, plan):
        """The manifest when this install is the target's first run (no
        tool there yet), else None. Never raises."""
        try:
            full = self._manifestPath()
            if full is None:
                return None
            manifest = LoadJson(full, 'manifest')
            core = set(manifest.get('core') or ())
            tools = [p['name'] for p in manifest.get('packages', [])
                     if p.get('name') and p['name'] not in core]
            return manifest if self._isFirstRun(op(plan['target']), tools) else None
        except Exception as e:
            debug('FNS_Installer: first-install check: %s' % e)
            return None

    # The one companion today, for a store with no manifest yet.
    FAMILY_FALLBACK = ('FNS_OpFamily',)
    # The root toggle that mirrors it (build_installer.ROOT_PROJECT_TOGGLES).
    FAMILY_TOGGLE = 'Opfamily'

    def _familyNames(self, full=None):
        """The companion package names: from the store manifest, else the
        fallback."""
        full = full or self._manifestPath()
        if full is not None:
            try:
                names = [p['name'] for p in LoadJson(full, 'manifest')['packages']
                         if p.get('companion') == 'family']
                if names:
                    return names
            except Exception:
                pass
        return list(self.FAMILY_FALLBACK)

    def _familyRoot(self):
        tgt = self._par('Target') or DefaultTarget(self.ownerComp)
        return op(tgt.path if isinstance(tgt, OP) else tgt)

    def SyncFamilyToggle(self):
        """Set the root's FNS Tab in OP Create toggle to what the project
        holds. Only writes on a difference; the toggle's own callback then
        sees nothing to do. Never raises; returns the state or None."""
        try:
            root = self.ownerComp.parent()
            par = getattr(root.par, self.FAMILY_TOGGLE, None)
            tgt = self._familyRoot()
            if par is None or tgt is None:
                return None
            here = any(tgt.op(n) is not None for n in self._familyNames())
            if bool(par.eval()) != here:
                par.val = here
            return here
        except Exception as e:
            debug('FNS_Installer: FNS tab toggle sync: %s' % e)
            return None

    def _familyRefused(self, why):
        self._status('FNS tab: ' + why)
        debug('FNSTools: FNS tab: ' + why)
        self.SyncFamilyToggle()
        return {'ok': False, 'why': why}

    def SetFamily(self, on=True, fetched=False):
        """Turn the FNS tab in the OP Create dialog on or off for this
        project: the root's FNS Tab in OP Create toggle calls this. Off is
        RemoveFamily. On installs the operator family beside the family
        operators already here, downloading it first when the store lacks
        it, and refuses when no family operator is installed (the tab would
        be empty). A refusal puts the toggle back. Returns what happened."""
        if not on:
            res = self.RemoveFamily()
            if not res.get('ok'):
                return self._familyRefused(res.get('why') or 'could not remove it')
            self.SyncFamilyToggle()
            return res
        root = self._familyRoot()
        if root is None:
            return self._familyRefused('no install target')
        locked = SourceLock(root.path)
        if locked:
            return self._familyRefused(locked)
        full = self._manifestPath()
        if full is None:
            return self._familyRefused('the store has no manifest yet; open Pick Tools once')
        manifest = LoadJson(full, 'manifest')
        index = {p['name']: p for p in manifest['packages']}
        names = self._familyNames(full)
        if any(root.op(n) is not None for n in names):
            self.SyncFamilyToggle()
            return {'ok': True, 'installed': [], 'why': 'the FNS operator family is already installed'}
        present = {c.name for c in root.children if c.family == 'COMP'}
        rec_t = root.op(INSTALLED_DAT)
        if rec_t is not None:
            present |= {rec_t[i, 0].val for i in range(1, rec_t.numRows) if rec_t[i, 0].val}
        members = sorted(n for n in present if index.get(n, {}).get('family'))
        if not members:
            return self._familyRefused('install an FNS family operator first '
                                       '(Random, a scene changer, SwitchTools or a sequencer); '
                                       'the tab lists them')
        try:
            plan = ResolvePlan({'schema': 1, 'install': members + names, 'tools': members,
                                'core': [], 'family': True}, full, root, minimal=True)
        except Exception as e:
            return self._familyRefused('plan failed: %s' % str(e)[:160])
        if plan.get('locked'):
            return self._familyRefused(plan['locked'])
        if plan['to_fetch']:
            if fetched:
                return self._familyRefused('did not download: %s' % ', '.join(plan['to_fetch']))
            why = self._fetchSelection(plan['to_fetch'])
            if why:
                return self._familyRefused(why)
            self._status('FNS tab: downloading %s' % ', '.join(plan['to_fetch']))
            run('args[0].valid and args[0].ext.InstallerExt.familyWhenFetched()',
                self.ownerComp, delayFrames=30, delayRef=op.TDResources)
            return {'ok': True, 'fetching': plan['to_fetch']}
        res = InstallPlan(plan, replace=False, bind=self._bindChoice())
        self.SyncFamilyToggle()
        self._status('FNS tab: installed %s' % (', '.join(res['installed']) or 'nothing'))
        return {'ok': not res['failed'], 'installed': res['installed'], 'failed': res['failed']}

    def familyWhenFetched(self, tries=0):
        """Wiring for SetFamily: finish turning the tab on once the store
        job that downloads the family ends (about three minutes at most)."""
        busy = (self._refreshActive() or self._manifestCheckPending()
                or getattr(self, '_pending_fetch', None) is not None)
        if busy and tries < 360:
            run('args[0].valid and args[0].ext.InstallerExt.familyWhenFetched(args[1])',
                self.ownerComp, tries + 1, delayFrames=30, delayRef=op.TDResources)
            return
        self.SetFamily(True, fetched=True)

    def RemoveFamily(self, confirm=True):
        """Take the FNS operator family out of this project: the FNS tab
        leaves the OP Create dialog, the family operators stay installed.
        It stays off: the next picker apply, "Set up like last time" and an
        agent's install all keep a project with members and no family as
        it is (FamilyWanted). Pick Tools turns it back on.

        `confirm=False` only answers what would happen. Never raises;
        returns {'ok', 'removed' | 'would_remove', 'why'?, 'notes'?}."""
        tgt = self._par('Target') or DefaultTarget(self.ownerComp)
        root = op(tgt.path if isinstance(tgt, OP) else tgt)
        if root is None:
            return {'ok': False, 'why': 'no install target'}
        locked = SourceLock(root.path)
        if locked:
            return {'ok': False, 'why': locked}
        names = list(self.FAMILY_FALLBACK)
        full = self._manifestPath()
        if full is not None:
            try:
                names = [p['name'] for p in LoadJson(full, 'manifest')['packages']
                         if p.get('companion') == 'family'] or names
            except Exception:
                pass
        present = [n for n in names
                   if root.op(n) is not None and root.op(n).family == 'COMP']
        if not present:
            return {'ok': True, 'removed': [], 'would_remove': [],
                    'why': 'the FNS operator family is not installed in this project'}
        if not confirm:
            return {'ok': True, 'would_remove': present}
        rm = RemoveTools({'target': root.path, 'steps': [], 'to_remove': present})
        self._status('removed the FNS operator family: %s' % ', '.join(rm['removed']))
        self.SyncFamilyToggle()
        return {'ok': True, 'removed': rm['removed'], 'notes': rm['notes']}

    def _keepStoreWanted(self):
        upd = self._updaterComp()
        p = getattr(upd.par, 'Keepstore', None) if upd is not None else None
        try:
            return bool(p is not None and p.eval() and getattr(upd, 'KeepStore', None))
        except Exception:
            return False

    def _keepStore(self):
        """The rest of the release into the store after an install landed
        (the updater's Keepstore toggle, default on): Pick Tools works
        offline afterwards. Scheduled, like every updater call from here;
        the updater itself refuses while a job runs and never chains a
        refresh after a refresh."""
        if not self._keepStoreWanted():
            return False
        run('args[0].valid and args[0].KeepStore()', self._updaterComp(),
            delayFrames=5, delayRef=op.TDResources)
        return True

    # The paste rail (the site's copied script) stores this flag on the
    # root right after loadTox so the first-run welcome stays out of the
    # way while the selection installs -- build_installer.WELCOME_FLAG;
    # keep the two in step.
    WELCOME_FLAG = 'FNS_welcomed'
    PASTE_HANDOVER_FRAMES = 60

    def _afterPasteInstall(self, res):
        """Hand a pasted install over to the console once it has landed.

        The paste rail suppresses the welcome, and until 2026-09-12 nothing
        opened afterwards: a paste with no tools picked installed core and
        went silent. Now the root's Pick Tools pulse follows -- the
        console's Install & remove tab, in the Hub's Console tab when the
        Hub is installed -- unless Plus picks are waiting, in which case the
        script pulses Configure itself and the installer's own picker with
        its sign-in is the right surface. Once only: the flag moves on.
        """
        root = self.ownerComp.parent()
        if root is None:
            return
        try:
            if root.fetch(self.WELCOME_FLAG, None, search=False) != 'paste':
                return
        except Exception:
            return
        root.store(self.WELCOME_FLAG, 'shown')
        if not res or not res.get('installed'):
            print('FNSTools: nothing installed from the pasted selection -- %s'
                  % (self._par('Status') or 'see the installer\'s Status'))
            return
        if self._pendingPlus():
            print('FNSTools: Patreon picks are waiting; the picker opens for sign-in')
            return
        if getattr(root.par, 'Picktools', None) is None:
            print('FNSTools: this root has no Pick Tools entry point -- open '
                  'the FNS console from the main menu')
            return
        print('FNSTools: %d package(s) installed; opening Install & remove'
              % len(res['installed']))
        # The registries and the Hub come up over the next frames; wait for
        # the console global before pulsing, a bounded number of times, and
        # say so in the Textport either way -- a silent landing is what the
        # first pasted install with nothing picked looked like.
        run(self._handoverScript(root.path, tries=10),
            delayFrames=self.PASTE_HANDOVER_FRAMES, delayRef=op.TDResources)

    @staticmethod
    def _handoverScript(root_path, tries):
        return (
            "r = op(%(root)r)\n"
            "if r is not None and r.valid:\n"
            "    con = getattr(op, 'FNS_CONSOLE', None)\n"
            "    if con is None and %(tries)d > 0:\n"
            "        run(r.op('FNS_Installer').ext.InstallerExt._handoverScript(%(root)r, %(tries)d - 1),\n"
            "            delayFrames=30, delayRef=op.TDResources)\n"
            "    else:\n"
            "        print('FNSTools: console %%s -- opening Install & remove'\n"
            "              %% ('ready' if con is not None else 'not up; opening the picker instead'))\n"
            "        r.par.Picktools.pulse()\n"
            % {'root': root_path, 'tries': tries})

    def _pendingPlus(self):
        """Plus picks the selection wanted but could not install (its
        `tools` minus `install`): the paste rail then opens the picker
        for sign-in itself."""
        try:
            selp = str(self._par('Selectionfile') or '')
            if not (selp and os.path.exists(selp)):
                return False
            with open(selp, 'r', encoding='utf-8') as sf:
                seldoc = json.load(sf)
            return bool(set(seldoc.get('tools') or []) - set(seldoc.get('install') or []))
        except Exception:
            return False

    # --- Always Set Up Like Last Time --------------------------------
    # The root's `Setuplikelast` toggle: a fresh drop installs the
    # machine's last recorded setup with no picker and no window. The
    # rail runs in the Textport: the store manifest, then exactly the
    # artifacts the plan needs, then the install -- each download waited
    # for by a frame-scheduled tick, the way the picker's page polls.
    LAST_SETUP_TICK_FRAMES = 60
    LAST_SETUP_TRIES = 600          # ten minutes of waiting on downloads

    def InstallLastSetup(self, confirm=False):
        """Install the machine's last recorded setup ("Set up like last
        time") with nothing to click: the tools of the project saved last,
        in the Package Files mode it used. DRY RUN unless `confirm`: the
        summary says what would land and what would download.

        Never removes anything. A Patreon tool the account cannot install
        is held aside and named; it waits for sign-in in the picker exactly
        as a ticked one would. Names the current release no longer has
        fall away silently, as the picker's card counts them."""
        root = self.ownerComp.parent()
        rec = LastInstall(root)
        if not rec:
            return {'ok': False, 'why': 'no last install recorded on this '
                    'machine (or this project keeps its settings to itself)'}
        summary = {'ok': True, 'packages': list(rec.get('packages') or []),
                   'project': rec.get('project'), 'when': rec.get('when'),
                   'bind': rec.get('bind'), 'dry_run': not confirm}
        if not confirm:
            full = self._manifestPath()
            if full is None:
                summary['needs_download'] = ['manifest']
                return summary
            sel, held = self._lastSetupSelection(rec, full)
            try:
                plan = ResolvePlan(sel, full,
                                   self._par('Target') or DefaultTarget(self.ownerComp))
            except Exception as e:
                return {'ok': False, 'why': 'plan failed: %s' % str(e)[:160]}
            summary.update({'ok': not plan.get('locked'), 'why': plan.get('locked') or '',
                            'would_install': [s['name'] for s in plan['steps']],
                            'already_present': plan['already_present'],
                            'needs_download': plan['to_fetch'],
                            'not_in_release': plan.get('unknown_packages', []),
                            'held_for_patreon': held})
            return summary
        print('FNSTools: setting up like last time -- %d package(s) from %s (%s)'
              % (len(summary['packages']), rec.get('project') or 'a saved project',
                 rec.get('when') or 'unknown date'))
        summary.update(self._lastSetupStep('plan'))
        return summary

    def _manifestPath(self):
        """The manifest this installer plans from, if it exists yet."""
        path = self._par('Manifestfile') or DefaultManifest()
        full = path if os.path.isabs(path) else RepoPath(path)
        return full if os.path.exists(full) else None

    def _lastSetupSelection(self, rec, full):
        """The selection the picker's card would post: the record's
        names that the release still has, over core, in the recorded bind
        mode. Returns (selection, held) -- held are the Patreon names
        kept wanted but out of `install`."""
        names = sorted(n for n in (rec.get('packages') or []) if n)
        man = LoadJson(full, 'manifest')
        core = list(man.get('core') or [])
        known = {p.get('name') for p in man.get('packages', [])}
        names = [n for n in names if n in known and n not in core]
        sel = {'schema': 1, 'toolkit': (man.get('toolkit') or {}).get('name'),
               'core': core, 'tools': names,
               'install': sorted(set(core) | set(names))}
        if rec.get('bind'):
            sel['bind'] = rec['bind']
        # the FNS tab: a record made before the flag existed says nothing,
        # and ResolvePlan then keeps the project as it is
        if isinstance(rec.get('family'), bool):
            sel['family'] = rec['family']
        return self._holdPatreonLocked(sel)

    def _lastSetupStep(self, stage):
        """One step of the silent rail. `stage` names what the previous
        step started downloading ('manifest', 'artifacts'), so the same
        thing missing twice is a failure and not another download;
        'plan' is the first step."""
        full = self._manifestPath()
        # The store manifest is MACHINE-WIDE and outlives every project, so
        # a store that predates the current release plans the whole install
        # from the old catalog: the right bytes for the wrong release. This
        # rail used to fetch only when the store had NO manifest at all,
        # which meant a machine that had ever installed simply never looked
        # again. Field report 2026-09-19: a clean start on a v3.2.37 store
        # installed all 67 packages at v3.2.37 (the `installed` table wore
        # today's timestamps and that release), and the family members --
        # still `placement: pane` in that catalog -- spawned seven copies
        # into the root network, which is exactly what `none` exists to
        # prevent. The picker has guarded this since v3.2.26 (_checkManifest
        # behind every served store manifest); the silent rail had no such
        # guard. So refresh first, always: one small JSON, and stage
        # 'manifest' then plans on whatever arrived.
        if stage == 'plan' and (full is None or _inStore(full)):
            why = self._refreshStore(names=[])
            if not why:
                self._armLastSetup('manifest')
                return {'ok': True, 'fetching': 'manifest'}
            # no updater to refresh with: a manifest we already have still
            # installs something, nothing at all is the old hard stop
            if full is None:
                return self._lastSetupStop(why)
        if full is None:
            return self._lastSetupStop('the store manifest did not arrive')
        rec = LastInstall(self.ownerComp.parent())
        if not rec:
            return self._lastSetupStop('the last-install record went away')
        sel, held = self._lastSetupSelection(rec, full)
        if held:
            print('FNSTools: waiting for Patreon sign-in before these install: %s'
                  % ', '.join(held))
        sel_dir = _fnsPaletteRoot()
        os.makedirs(sel_dir, exist_ok=True)
        sel_path = sel_dir + '/selection.json'
        with open(sel_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(sel, indent=1) + '\n')
        self.ownerComp.par.Selectionfile = sel_path
        bind = sel.get('bind')
        pf = getattr(self.ownerComp.par, 'Packagefiles', None)
        if bind and pf is not None and bind in pf.menuNames:
            pf.val = bind
        try:
            plan = ResolvePlan(sel_path, full,
                               self._par('Target') or DefaultTarget(self.ownerComp))
        except Exception as e:
            return self._lastSetupStop('plan failed: %s' % str(e)[:160])
        if plan.get('locked'):
            return self._lastSetupStop(plan['locked'])
        if plan['to_fetch']:
            if stage == 'artifacts':
                return self._lastSetupStop('did not arrive: %s'
                                           % ', '.join(plan['to_fetch']))
            why = self._fetchSelection(plan['to_fetch'])
            if why:
                return self._lastSetupStop(why)
            mb = sum(s.get('bytes', 0) for s in plan['steps']
                     if s['name'] in plan['to_fetch']) / 1048576.0
            print('FNSTools: downloading %d package(s), %.1f MB'
                  % (len(plan['to_fetch']), mb))
            self._armLastSetup('artifacts')
            return {'ok': True, 'fetching': 'artifacts',
                    'needs_download': plan['to_fetch']}
        # never a removal: this rail only ever adds the remembered tools
        res = self.Install(remove=False)
        if res is None:
            return self._lastSetupStop(self._par('Status') or 'install failed')
        print('FNSTools: set up like last time -- installed %d%s'
              % (len(res['installed']),
                 ', FAILED ' + ', '.join(res['failed']) if res['failed'] else ''))
        return {'ok': not res['failed'], 'installed': res['installed'],
                'failed': res['failed']}

    def _armLastSetup(self, stage, tries=None):
        tries = self.LAST_SETUP_TRIES if tries is None else tries
        run("args[0].valid and args[0].ext.InstallerExt._lastSetupTick(%r, %d)"
            % (stage, tries), self.ownerComp,
            delayFrames=self.LAST_SETUP_TICK_FRAMES, delayRef=op.TDResources)

    def _lastSetupTick(self, stage, tries):
        # a queued fetch (_fetchSelection) has not started yet: still waiting
        if self._refreshActive() or getattr(self, '_pending_fetch', None) is not None:
            if tries <= 0:
                self._lastSetupStop('gave up waiting for the download')
                return
            self._armLastSetup(stage, tries - 1)
            return
        job = self._refreshJob()
        if job and job.get('stage') == 'failed':
            self._lastSetupStop('download failed: %s'
                                % (job.get('error') or job.get('why') or 'see FNS_Updater'))
            return
        self._lastSetupStep(stage)

    def _lastSetupStop(self, why):
        line = ('FNSTools: set up like last time stopped -- %s. Pick Tools on '
                'the toolkit root continues by hand.' % why)
        print(line)
        self._status(line)
        return {'ok': False, 'why': why}

    def onParPlan(self, _par):
        self.Plan()

    def onParInstall(self, _par):
        self.Install()

    # --- command rail (FNS_CommandRegistry) ---------------------------
    # The installer answers install requests as COMMANDS, so a consumer
    # (the launcher) never places toxes itself. One owner of placement
    # means one install record, one update path, and no duplicates --
    # docs/LauncherToolkitBoundary.md, Option A.

    def FnsCommands(self):
        """Spec list for FNS_CommandRegistry.

        `install` is DRY RUN by default. A request arriving from another
        application is not the same as a user agreeing to it, so the
        default answer is a plan describing what would land; `confirm`
        performs it. Same shape as fns.collect, which consumers already
        know how to render.
        """
        cap = 'fns.install'
        return [
            {'id': 'install', 'label': 'Install an FNS package…',
             'help': 'Plan an install (dry run); pass confirm=True to apply',
             'method': 'CommandInstall',
             'surface': ['session'], 'capability': cap},
            {'id': 'installed', 'label': 'Installed packages',
             'help': 'What this project has, as the install record knows it',
             'method': 'CommandInstalled', 'hidden': True, 'capability': cap},
            {'id': 'available', 'label': 'Available packages',
             'help': 'What the manifest offers, with launcher reach',
             'method': 'CommandAvailable', 'hidden': True, 'capability': cap},
        ] + self._installRows()

    # --- install-<Package> rows (docs/CommandAvailability.md) ----------
    # One command per package this project can install and does not have,
    # so every command surface offers "Install Collect" where Collect's own
    # commands would be. Rebuilt whenever the answer can change: init, an
    # install here, the end of a store job, an entitlement change.

    _INSTALL_ID_RE = __import__('re').compile(r'^[A-Za-z0-9][A-Za-z0-9_\-]{0,47}$')

    def _installRows(self):
        """Specs for every package that is installable and not present.

        Installable: a `tool` in the store manifest, not `nopick`, not an FNS
        operator family member (the FNS tab is their home), and free or
        entitled. Present: in the install record OR a live COMP of that name
        under the target (a hand-placed or dev-tree copy has no record). A
        package whose install is queued or downloading is left out too, so an
        impatient second click has no row to hit. Never raises."""
        try:
            man = LoadJson(self._par('Manifestfile') or DefaultManifest(), 'manifest')
        except Exception:
            return []
        try:
            tgt = op(self._par('Target') or DefaultTarget(self.ownerComp))
        except Exception:
            tgt = None
        recorded = set()
        t = tgt.op(INSTALLED_DAT) if tgt is not None else None
        if t is not None:
            for i in range(1, t.numRows):
                recorded.add(t[i, 0].val)
        busy = set(getattr(self, '_installQueue', None) or {})
        candidates = []
        for pkg in man.get('packages', []):
            name = str(pkg.get('name') or '')
            if not name or pkg.get('kind') != 'tool':
                continue
            if pkg.get('nopick') or pkg.get('family'):
                continue
            if name in recorded or name in busy:
                continue
            if tgt is not None and tgt.op(name) is not None:
                continue
            candidates.append(pkg)
        locked = set(self._patreonLocked([p['name'] for p in candidates]))
        rows = []
        for pkg in candidates:
            name = pkg['name']
            if name in locked:
                continue
            public = name[4:] if name.startswith('FNS_') else name
            cid = 'install-' + public
            if not self._INSTALL_ID_RE.match(cid):
                debug('FNS_Installer: no install command for %s (id %r is not valid)' % (name, cid))
                continue
            rows.append({
                'id': cid,
                'label': 'Install ' + str(pkg.get('title') or public),
                'help': str(pkg.get('description') or 'Install %s into this project' % public),
                'method': 'CommandInstall',
                'kwargs': {'package': name, 'confirm': True},
                'capability': 'fns.install'})
        return rows

    def rebuildInstallCommands(self):
        """Wiring: re-announce the command list (the install rows follow
        what is installed, downloading and entitled). Called by this
        installer after an install and by the sibling FNS_Updater at the end
        of a store job and on an entitlement change."""
        return self._registerLauncherCommands()

    def onInitTD(self):
        # Deferred: a registry may still be promoting its /sys global, and
        # on a fresh bootstrap drop this COMP's own siblings are still
        # arriving. Guarded inside, so no registry is never an error.
        run('args[0]._registerLauncherCommands()', self, delayFrames=60)
        # the root's FNS Tab toggle follows the project (a saved toe can
        # disagree after a hand delete or an older installer)
        run('args[0].SyncFamilyToggle()', self, delayFrames=90)

    def _registerLauncherCommands(self):
        """Announce to a registry if one is present. Guarded: no registry
        is ever guaranteed, and the tag makes one that arrives LATER
        rediscover this COMP by rescan."""
        try:
            self.ownerComp.tags.add('fnscommands')
            # a catalogue owner: one install row per package, over the
            # registry's ordinary 24-per-tool cap (registry >= 1.12.0)
            self.ownerComp.tags.add('fnscatalog')
        except Exception:
            pass
        try:
            reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
            if reg is not None and hasattr(reg, 'Register'):
                return reg.Register(self.ownerComp, self.FnsCommands())
        except Exception:
            pass
        return None

    def CommandInstall(self, package='', confirm=False, source='', _resumed=False):
        """Install ONE package by name, minimally.

        `source` is an optional local artifact path, so a caller holding
        bytes already (a launcher's bundled free artifact) installs from
        them rather than the store -- a real install with a record and an
        update path, not a dropped tox. A supplied file older than the
        manifest installs with a warning and records the sha that landed,
        so the next online Compare() offers the upgrade.
        """
        name = str(package).strip()
        if not name:
            return {'ok': False, 'error': 'no package named'}
        public = name[4:] if name.startswith('FNS_') else name
        queue = getattr(self, '_installQueue', None)
        if queue is None:
            queue = self._installQueue = {}
        if confirm and not _resumed and name in queue:
            return {'ok': True, 'fetching': True, 'package': name,
                    'text': 'Already downloading %s' % public}
        # Refused up front, with or without a local `source`: bytes already
        # on disk are no entitlement, and a fetch the updater will refuse
        # would leave the caller polling "run again when it settles".
        if self._patreonLocked([name]):
            why = '%s needs a Patreon tier this account does not include' % name
            try:
                upd = self._updaterComp()
                auth = upd.ext.ExtAuth if upd is not None else None
                if auth is not None:
                    why = auth.MissingFor(name) or why
            except Exception:
                pass
            return {'ok': False, 'package': name, 'patreon_locked': True,
                    'error': why}
        try:
            plan = ResolvePlan(
                {'schema': 1, 'install': [name], 'tools': [name], 'core': []},
                self._par('Manifestfile') or DefaultManifest(),
                self._par('Target') or DefaultTarget(self.ownerComp),
                minimal=True,
                sources={name: source} if source else None)
        except Exception as e:
            return {'ok': False, 'error': str(e)[:160]}
        if plan.get('unknown_packages'):
            return {'ok': False, 'error': '%s is not in the manifest' % name}
        if plan.get('locked'):
            return {'ok': False, 'error': plan['locked']}
        would = [s['name'] for s in plan['steps']]
        summary = {'ok': True, 'package': name, 'target': plan['target'],
                   'would_install': would,
                   'already_present': plan['already_present'],
                   'needs_download': plan['to_fetch'],
                   'older_than_manifest': plan['hash_warnings']}
        if not confirm:
            summary['dry_run'] = True
            return summary
        if plan['to_fetch']:
            if _resumed:
                # the download ended and the artifact is still missing
                summary.update({'ok': False,
                                'error': 'did not download: %s' % ', '.join(plan['to_fetch'])})
                return summary
            why = self._fetchSelection(plan['to_fetch'])
            if why:
                summary.update({'ok': False, 'fetching': False, 'error': why})
                return summary
            # queued: the install finishes itself once the store job ends,
            # so a palette click never has to be repeated
            queue[name] = source
            self.rebuildInstallCommands()
            run('args[0].valid and args[0].ext.InstallerExt.installWhenFetched(args[1])',
                self.ownerComp, name, delayFrames=30, delayRef=op.TDResources)
            summary.update({'ok': True, 'fetching': True,
                            'text': 'Downloading %s; it installs when the download finishes' % public})
            return summary
        res = InstallPlan(plan, replace=False, bind=self._bindChoice())
        self.SyncFamilyToggle()
        self.rebuildInstallCommands()
        summary.update({'ok': not res['failed'], 'dry_run': False,
                        'installed': res['installed'], 'failed': res['failed']})
        return summary

    def installWhenFetched(self, name, tries=0):
        """Wiring for CommandInstall: finish a queued install once the
        store job that downloads it ends (about three minutes at most, as
        familyWhenFetched). The outcome goes to the status line and log."""
        queue = getattr(self, '_installQueue', None) or {}
        if name not in queue:
            return
        busy = (self._refreshActive() or self._manifestCheckPending()
                or getattr(self, '_pending_fetch', None) is not None)
        if busy and tries < 360:
            run('args[0].valid and args[0].ext.InstallerExt.installWhenFetched(args[1], args[2])',
                self.ownerComp, name, tries + 1, delayFrames=30, delayRef=op.TDResources)
            return
        source = queue.pop(name, '')
        try:
            res = self.CommandInstall(name, confirm=True, source=source, _resumed=True)
        except Exception as e:
            res = {'ok': False, 'error': str(e)[:160]}
        if res.get('ok'):
            self._status('installed %s' % (', '.join(res.get('installed') or []) or name))
        else:
            self._status('install of %s failed: %s' % (name, res.get('error') or 'unknown'))
            debug('FNS_Installer: install of %s failed after download: %s' % (name, res.get('error')))
        self.rebuildInstallCommands()

    def CommandInstalled(self):
        """The install record: what landed here, at which sha and release."""
        tgt = op(self._par('Target') or DefaultTarget(self.ownerComp))
        t = tgt.op(INSTALLED_DAT) if tgt is not None else None
        rows = []
        if t is not None and t.numRows > 1:
            for i in range(1, t.numRows):
                rows.append({c: t[i, n].val for n, c in enumerate(INSTALLED_COLS)})
        return {'ok': True, 'target': tgt.path if tgt else '', 'packages': rows}

    def CommandAvailable(self):
        """What the manifest offers, with the `launcher` block passed
        through so a consumer can show only what reaches its surfaces.

        NOTE the shape difference, confirmed against a live consumer: the
        MANIFEST omits `launcher` for a package that has none
        (presence-style, like `placement`), but this projection always
        emits the key, `null` when absent. That is deliberate here — a
        consumer iterating packages gets a stable shape and can read
        `p['launcher']` without a membership test — but it means "absent"
        and "null" both mean not-launcher-capable, and a consumer must
        tolerate whichever it meets depending on whether it is reading the
        manifest or asking us.
        """
        try:
            man = LoadJson(self._par('Manifestfile') or DefaultManifest(),
                           'manifest')
        except Exception as e:
            return {'ok': False, 'error': str(e)[:160]}
        out = []
        for p in man.get('packages', []):
            out.append({'name': p['name'], 'version': p.get('version', ''),
                        'access': p.get('access', 'free'),
                        'launcher': p.get('launcher') or None})
        return {'ok': True, 'release': man.get('release', ''), 'packages': out}

    # --- the served configurator (bootstrap rail) ---------------------
    #
    # A Web Server DAT inside this COMP serves the picker page and takes
    # the selection back as a POST -- no file leaves the browser, no par
    # has to be pointed anywhere. The page lives in ./configurator_html
    # (embedded at build time); the manifest it shows is whatever
    # DefaultManifest() resolves to, and when neither store nor repo has
    # one yet the sibling FNS_Updater is asked to refresh the store while the
    # page shows "downloading" and polls.

    def _port(self):
        try:
            return int(self._par('Port') or 36760)
        except ValueError:
            return 36760

    # Fifty wide, like the console's block: Windows reserves ~16-port
    # ranges for Hyper-V/WSL at semi-random places, and a narrow scan that
    # starts inside one finds nothing free on an idle machine.
    PORT_SPAN = 50

    def _freePort(self):
        """First free port from Port upward (PORT_SPAN tries). Several
        open projects each carry an installer -- and the FNS console scans
        36710-36759 the same way -- so a fixed port would make the second
        server fail to bind; a bind test picks a live one instead."""
        import socket
        base = self._port()
        for port in range(base, min(base + self.PORT_SPAN, 65535)):
            s = socket.socket()
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
            finally:
                s.close()
        return None

    BIND_ADDRESS = '127.0.0.1'

    def _bindLoopback(self, ws):
        """Pin the picker's Web Server DAT to loopback.

        A BLANK Local Address makes a Web Server DAT listen on EVERY
        interface (Derivative: "When left blank, the Web Server DAT will
        listen on all interfaces"). The bind test in _freePort above uses
        127.0.0.1 and reads like the thing that keeps this private -- it is
        not; that socket is closed again and constrains nothing. Left blank,
        /selection and /install were drivable by anyone on the same network.

        Applied on every Configure(), not once at build time: installers
        already in the field carry the old blank value, and re-asserting is
        the only thing that repairs them. Restart if it was already serving
        -- the DAT reads this at bind time, not per request.
        """
        if ws is None:
            return
        try:
            if str(ws.par.localaddress.eval()) == self.BIND_ADDRESS:
                return
            ws.par.localaddress = self.BIND_ADDRESS
            if ws.par.active.eval():
                ws.par.restart.pulse()
        except Exception as e:
            debug('INSTALLER: could not pin %s to %s (%s) -- it may be '
                  'reachable from the network' % (ws.path, self.BIND_ADDRESS, e))

    def Configure(self):
        """Serve the picker and show it: the sibling webBrowser COMP if
        this installer ships inside the bootstrap root, else the system
        browser."""
        ws = self.ownerComp.op('webserver')
        if ws is None:
            self._status('no webserver DAT -- rebuild the installer')
            return
        self._bindLoopback(ws)
        port = ws.par.port.eval() if ws.par.active.eval() else self._freePort()
        if port is None:
            self._status('no free port in %d-%d -- close another picker or '
                         'change Configurator Port'
                         % (self._port(), self._port() + self.PORT_SPAN - 1))
            return
        if not ws.par.active.eval():
            ws.par.port = int(port)
            ws.par.active = True
        url = 'http://127.0.0.1:%d/' % int(port)
        browser = self._pickerBrowser()
        if browser is not None:
            act = getattr(browser.par, 'Active', None)
            if act is not None and not act.eval():
                act.val = True
            # Declare the serve: an openViewer window satisfies NONE of
            # the browser's visibility watchers (measured -- not winopen,
            # not viewer-active, not a pane), so without the hold the
            # watchers switch the render back off one frame after this
            # method turns it on, and Pick Tools opens a blank panel.
            # Released by _serverOff when the picker server stops.
            if hasattr(browser.par, 'Holdactive'):
                browser.par.Holdactive = True
            browser.par.Address = url
            # what we actually served, for `_pickerOnScreen`: the port
            # parameter drifts, this does not
            self.ownerComp.store('picker_url', url)
            browser.openViewer()
        else:
            import webbrowser
            webbrowser.open(url)
        self._status('configurator at %s' % url)

    def onParConfigure(self, _par):
        self.Configure()

    def _updaterComp(self):
        parent = self.ownerComp.parent()
        return parent.op('FNS_Updater') if parent is not None else None

    def _patreonLocked(self, names):
        """The Patreon names in `names` this account cannot install yet.

        Asked of the updater's own entitlement, the same answer it uses to
        decide what it will fetch, so the installer never plans a download
        the updater is going to refuse. The picker builds its selection from
        the account snapshot the page loaded with, and that can be stale:
        field report 2026-09-16, a Mac planned FNS_PreviewPanel from an old
        sign-in record, the gate refused it, and the install waited on it.
        No updater or no auth beside the installer reads as not entitled,
        because installing paid bytes on an unanswered question is the wrong
        way to fail.
        """
        names = [str(n) for n in (names or []) if n]
        if not names:
            return []
        try:
            man = LoadJson(self._par('Manifestfile') or DefaultManifest(),
                           'manifest')
        except Exception:
            return []
        access = {p.get('name'): str(p.get('access', 'free') or 'free')
                  for p in man.get('packages', [])}
        gated = [n for n in names if access.get(n, 'free') != 'free']
        if not gated:
            return []
        auth = None
        upd = self._updaterComp()
        try:
            auth = upd.ext.ExtAuth if upd is not None else None
        except Exception:
            auth = None
        locked = []
        for n in gated:
            try:
                ok = bool(auth is not None and auth.IsEntitled(n))
            except Exception:
                ok = False
            if not ok:
                locked.append(n)
        return locked

    def _holdPatreonLocked(self, sel):
        """Move locked Patreon names out of `install`, keeping them wanted.

        Returns (selection, held). `tools` keeps every name, so the picker
        still shows the tool ticked and offers sign-in, and it installs once
        the account includes it. ResolvePlan falls back to core + tools when
        `install` is EMPTY, which would pull a held name straight back in, so
        a selection left with nothing to install drops the held names from
        `tools` too.
        """
        if not isinstance(sel, dict):
            return sel, []
        install = list(sel.get('install') or [])
        held = self._patreonLocked(install)
        if not held:
            return sel, []
        sel = dict(sel)
        remaining = [n for n in install if n not in held]
        sel['install'] = remaining
        tools = list(sel.get('tools') or [])
        if remaining:
            sel['tools'] = tools + [n for n in held if n not in tools]
        else:
            sel['tools'] = [n for n in tools if n not in held]
        debug('FNS_Installer: held for Patreon sign-in: %s' % ', '.join(held))
        return sel, held

    def _refreshStore(self, names=None):
        """Kick the sibling FNS_Updater's store refresh; harmless if one is
        already running (it refuses). `names` scopes the fetch ([] is
        manifest-only -- the picker; a list is the selection at install).

        Scheduled via run(), never called inline: this fires from the web
        server's request callback, and the one observed refresh that
        started inside that callback finished 'done' having fetched
        nothing, while the identical call from the textport fetched the
        whole store. Marshaling out of the callback context is the same
        cure the updater itself applies everywhere else."""
        upd = self._updaterComp()
        if upd is None or getattr(upd, 'RefreshStore', None) is None:
            return 'no FNS_Updater next to the installer -- refresh the store yourself'
        run("op(%r).RefreshStore(names=%r)" % (upd.path, names), delayFrames=1)
        return ''

    # A store that holds ANY manifest used to be served as-is forever: the
    # picker only fetched a catalog when the store had none, so a machine
    # whose store predates a release kept offering the old package list
    # (field report, v3.2.26: the new family packages were missing from a
    # fresh FNSTools.tox's picker). Serving a store manifest now also starts
    # a manifest-only refresh -- one small JSON -- at most once a minute, and
    # the page asks /manifest/release whether the release moved.
    MANIFEST_CHECK_SECONDS = 60

    def _checkManifest(self, full):
        """Start a manifest-only store refresh behind a served STORE
        manifest, throttled; remember which release was served and which
        job was current, so /manifest/release can tell a check that has not
        started yet from one that finished. True when a check is pending."""
        if not _inStore(full):
            return False          # a dev Manifestfile, not the machine store
        now = absTime.seconds
        prev = getattr(self, '_manifest_check', None)
        if prev and now - prev.get('started', 0) < self.MANIFEST_CHECK_SECONDS:
            return self._manifestCheckPending()
        try:
            served = str(LoadJson(full, 'manifest').get('release', '') or '')
        except Exception:
            served = ''
        job = self._refreshJob()
        self._manifest_check = {'started': now, 'served': served,
                                'job_before': id(job) if job is not None else None,
                                'kicked': False}
        if self._refreshActive():
            return True           # a running pass rewrites the manifest anyway
        why = self._refreshStore(names=[])
        if why:
            self._manifest_check = None
            return False
        self._manifest_check['kicked'] = True
        return True

    def _manifestCheckPending(self):
        chk = getattr(self, '_manifest_check', None)
        if not chk:
            return False
        if self._refreshActive():
            return True
        job = self._refreshJob()
        not_started = (chk.get('kicked')
                       and (id(job) if job is not None else None) == chk.get('job_before'))
        # run() schedules the refresh a frame out; give it a few seconds to
        # appear before calling the check finished
        return bool(not_started and absTime.seconds - chk.get('started', 0) < 10)

    # The recommendations lane (packaging/recommendations.json: other
    # creators' tools, linked or pinned) is published to the bucket, which
    # sends no Access-Control-Allow-Origin header, so the served page on
    # 127.0.0.1 could never fetch it (measured 2026-09-17: blocked by CORS
    # on every load). The updater already downloads the list into
    # <store>/community/ with TD's own downloader, where CORS does not
    # apply; the installer relays that copy on the page's own origin.
    COMMUNITY_MAX_AGE = 300          # a removal reaches the picker within minutes
    COMMUNITY_RETRY_SECONDS = 60     # a failed or missing list is not re-asked every poll

    def _communityInFlight(self, upd):
        try:
            place = getattr(upd.ext.ExtUpdater, '_place', None)
        except Exception:
            return False
        return bool(place) and place.get('stage') == 'list'

    def _recommendations(self):
        """The curated list for the served picker, from the store copy.
        Starts a refresh when the copy is missing or stale and the updater
        is idle (a store job would abort the download); `retry` asks the page
        to request again while that refresh can still change the answer."""
        upd = self._updaterComp()
        if upd is None or getattr(upd, 'CommunityList', None) is None:
            return {'tools': [], 'retry': False}
        path = '%s/community/recommendations.json' % upd.StoreFolder()
        try:
            age = time.time() - os.path.getmtime(path)
        except OSError:
            age = None
        if self._communityInFlight(upd):
            return {'tools': upd.CommunityList(), 'retry': True}
        stale = age is None or age > self.COMMUNITY_MAX_AGE
        asked = getattr(self, '_community_asked', None)
        recently = asked is not None and absTime.seconds - asked < self.COMMUNITY_RETRY_SECONDS
        retry = False
        if stale and not recently:
            if (self._refreshActive() or self._manifestCheckPending()
                    or getattr(self, '_pending_fetch', None) is not None):
                retry = True          # busy now; the page asks again shortly
            else:
                self._community_asked = absTime.seconds
                # out of the request callback, like every updater call here
                run('args[0].valid and args[0].RefreshCommunity()', upd,
                    delayFrames=1, delayRef=op.TDResources)
                retry = True
        return {'tools': upd.CommunityList(), 'retry': retry}

    def _placeCommunity(self, name):
        """Ask the updater to place one pinned community tool in the
        working network. Answers at once; the placement itself finishes
        frames later and is read back through GET /community/place."""
        upd = self._updaterComp()
        if upd is None or getattr(upd, 'PlaceCommunityTool', None) is None:
            return {'ok': False, 'why': 'this install has no updater to place it with'}
        if not any(str(t.get('name', '')) == name for t in upd.CommunityList()):
            return {'ok': False, 'why': 'unknown community tool %r' % name}
        target, note = PanePlacement('', lock=CommunityLock)
        if not target:
            return {'ok': False, 'why': note if note != 'no network editor open'
                    else 'open a network editor to place it in'}
        # out of the request callback, like every updater call here
        run('args[0].valid and args[0].PlaceCommunityTool(args[1], args[2])',
            upd, name, target, delayFrames=1, delayRef=op.TDResources)
        return {'ok': True, 'target': target}

    def _installCommunity(self, name):
        """Ask the updater to install one tdp highlight and place its tox in
        the working network. A project with no Python environment is told so
        at once (`noenv`), so the page can offer to set one up."""
        upd = self._updaterComp()
        if upd is None or getattr(upd, 'InstallCommunityPackage', None) is None:
            return {'ok': False, 'why': 'this install has no updater that can install Python packages'}
        if not any(str(t.get('name', '')) == name for t in upd.CommunityList()):
            return {'ok': False, 'why': 'unknown community tool %r' % name}
        env = upd.PythonEnvStatus()
        if env.get('state') != 'ready':
            return {'ok': False, 'noenv': True, 'env': env,
                    'why': 'this project has no Python environment yet'}
        target, note = PanePlacement('', lock=CommunityLock)
        if not target:
            return {'ok': False, 'why': note if note != 'no network editor open'
                    else 'open a network editor to place it in'}
        run('args[0].valid and args[0].InstallCommunityPackage(args[1], args[2])',
            upd, name, target, delayFrames=1, delayRef=op.TDResources)
        return {'ok': True, 'target': target}

    def _fetchSelection(self, names):
        """Download an install's selection. The updater runs one store job at
        a time and REFUSES a second, silently from here, so a click on
        Install while another job runs (the picker's own catalog check, the
        Keepstore mirror after an install) used to end in "Download failed:
        unknown". When a job is running the fetch is queued and started the
        moment it ends; /status reports a queued fetch as fetching."""
        if not self._refreshActive() and not self._manifestCheckPending():
            return self._refreshStore(names=names)
        if self._updaterComp() is None:
            return 'no FNS_Updater next to the installer -- refresh the store yourself'
        self._pending_fetch = list(names)
        run('args[0].valid and args[0].ext.InstallerExt.fetchWhenIdle()',
            self.ownerComp, delayFrames=10, delayRef=op.TDResources)
        return ''

    def fetchWhenIdle(self, tries=0):
        """Wiring for _fetchSelection's queue: start the queued fetch once
        the running store job ends; give up after about a minute and a half
        (the page then reports the failure as before)."""
        names = getattr(self, '_pending_fetch', None)
        if names is None:
            return
        if (self._refreshActive() or self._manifestCheckPending()) and tries < 540:
            run('args[0].valid and args[0].ext.InstallerExt.fetchWhenIdle(args[1])',
                self.ownerComp, tries + 1, delayFrames=10, delayRef=op.TDResources)
            return
        upd = self._updaterComp()
        try:
            if upd is not None and not self._refreshActive():
                upd.RefreshStore(names=names)   # already outside the request callback
        finally:
            self._pending_fetch = None

    def _refreshJob(self):
        """The sibling FNS_Updater's current job dict, or None."""
        upd = self._updaterComp()
        try:
            return getattr(upd.ext.ExtUpdater, '_job', None) if upd else None
        except Exception:
            return None

    def _refreshActive(self):
        job = self._refreshJob()
        return bool(job) and job.get('stage') not in ('done', 'failed')

    def _planText(self, plan):
        lines = ['install into %s' % plan['target'], '']
        if plan.get('locked'):
            lines = ['REFUSED -- ' + plan['locked'], ''] + lines
        fetch_bytes = 0
        for s in plan['steps']:
            if s.get('stale'):
                state = ('present, stale cache -> re-download' if s['present']
                         else 'install (stale cache -> re-download)')
                fetch_bytes += s.get('bytes', 0)
            elif s['present']:
                state = 'present, kept'
            elif s.get('have'):
                state = 'install'
            else:
                state = 'install (download)'
                fetch_bytes += s.get('bytes', 0)
            if s.get('variant', 'base') != 'base':
                state += ' (%s build)' % s['variant']
            lines.append('%-26s %-5s %s' % (s['name'], s['kind'], state))
        for n in plan.get('to_remove', []):
            lines.append('%-26s %-5s %s' % (n, 'tool',
                         'REMOVE (settings kept for reinstall)'))
        for n in plan['missing_artifact']:
            lines.append('%-26s %s' % (n, 'NO ARTIFACT'))
        for n in plan['unknown_packages']:
            lines.append('%-26s %s' % (n, 'NOT IN MANIFEST'))
        if fetch_bytes:
            lines.append('')
            lines.append('%.1f MB to download' % (fetch_bytes / 1048576.0))
        return '\n'.join(lines)

    # The bootstrap's own residents: a root holding nothing but these has
    # never been installed into, and the page runs its guided first run.
    RAILS = ('FNS_Installer', 'FNS_Updater', 'webBrowser')

    def _isFirstRun(self, tgt, tools=None):
        """True when the target holds no TOOL yet.

        `tools` is the manifest's tool names (packages minus core); with
        it the test asks the only question that matters -- is any tool in
        this root, as a child or in the install record (pane-placed tools
        are installed without being children). Without a manifest it
        falls back to "no COMP but the rails and the root's own config
        host". Counting every COMP was the bug: the root's `FNS_ConfigHost`
        ships in the bootstrap (2026-08-22), so every root had one
        "package" and no root was ever a first run again -- no welcome, no
        "Set up like last time", on a bare drop or a paste. Core never
        counts either: the paste rail installs core before anything can
        open, and a root with core and no tools is still the user's first
        look at the picker."""
        if tgt is None:
            return False
        if tools is not None:
            # FNS_ConfigHost is ALSO a catalogued package (the standalone
            # host for other people's components), so the root's own host
            # would read as an installed tool by name; the rails likewise
            tools = set(tools) - set(self.RAILS) - {ROOT_HOST}
            if any(c.family == 'COMP' and c.name in tools for c in tgt.children):
                return False
            rec = tgt.op(INSTALLED_DAT)
            if rec is not None and rec.numRows > 1:
                for i in range(1, rec.numRows):
                    if rec[i, 0].val in tools:
                        return False
            return True
        skip = set(self.RAILS) | {ROOT_HOST}
        return not any(c.family == 'COMP' and c.name not in skip
                       for c in tgt.children)

    def _openExternal(self, url):
        """Open a web URL in the system browser; '' on success, else why."""
        u = str(url or '').strip()
        if not (u.startswith('https://') or u.startswith('http://')):
            return 'not a web address'
        # TouchDesigner's own opener: a URL goes to the default browser
        try:
            ui.viewFile(u)
            return ''
        except Exception as e:
            return 'could not open a browser: %s' % e

    def _openSettings(self):
        """Hand the panel over to the FNS console's Settings tab -- the
        root's own Open Settings pulse, so the routing (console, or an
        older registry's forward, in-TD panel or system browser) stays in
        one place. Returns an error string, '' on success."""
        root = self.ownerComp.parent()
        par = getattr(root.par, 'Opensettings', None) if root else None
        if par is None:
            return 'this installer is not inside a toolkit root -- use the ' \
                   'FNS console directly'
        if getattr(op, 'FNS_CONSOLE', None) is None \
                and getattr(op, 'FNS_CONFIGREGISTRY', None) is None:
            return 'no FNS console installed yet'
        # deferred: the pulse navigates the very panel this request came
        # from, and the response must leave first
        run("op(%r).par.Opensettings.pulse()" % root.path, delayFrames=2)
        return ''

    # The page heartbeats /status every 20 s while someone is interacting
    # with it (mouse or keys in the last two minutes), so "idle" means the
    # page is out of sight or abandoned, not merely done installing.
    SERVER_IDLE_SECONDS = 90

    def _serverOff(self, delay_ms):
        """Deactivate the picker server once it has been IDLE for
        `delay_ms` -- and release the browser hold with it: Holdactive
        means "being served", and a stopped server is the definition of
        not being served.

        Idle, not elapsed: the first version stopped on a fixed timer, and
        a user still reading the "Installed" dialog a minute after the
        install found its Close button dead -- the hold had gone, the
        render with it, and a dormant render shows its last frame and
        takes no clicks. Now the page's heartbeat keeps the server up while
        the page is in use, the picker's own open window keeps it up while
        it is on screen at all (`_idleOff`), and the timer only fires when
        both are gone.

        The hold is released only while the browser still shows THIS
        server: once the console has taken the panel over (Open Settings,
        or the Hub's Console tab) the hold is the console's, and clearing
        it from here froze the Hub's tab the same way.
        """
        run("op(%r).ext.InstallerExt._idleOff(%d)" % (self.ownerComp.path, int(delay_ms)),
            delayMilliSeconds=delay_ms, delayRef=op.TDResources)

    def _pickerBrowser(self):
        parent = self.ownerComp.parent()
        return parent.op('webBrowser') if parent is not None else None

    def _pickerOnScreen(self, url):
        """True while the picker's own window is open and still showing
        `url` -- someone is looking at this page right now.

        The browser's three visibility watchers cannot answer this. Its
        Window Owner is the Hub's panel and its Pane Owner is the Hub,
        because the console mirrors this same browser; a viewer opened on
        the browser ITSELF satisfies none of them, and openViewer does not
        raise the node's Viewer Active flag either. Its own panel does
        answer it: `winopen` tracks that floating window (measured
        2026-09-17 -- False before openViewer, True after, False again
        after closeViewer), and nothing else in the component reads it.

        The address test is what keeps this from outliving the picker:
        once Open Settings or the Hub's Console tab has pointed the same
        browser somewhere else, the window on screen is no longer ours.

        That address is the one we SERVED, remembered by `Configure`,
        rather than one rebuilt from the port parameter here -- belt and
        braces, since the parameter is mutable and nothing stops a later
        Configure from moving it while an older page is still on screen.

        It is NOT what went wrong on 2026-09-17, though the first version
        of this docstring said so. The reading that looked like a drifted
        port (window showing :36710, parameter reading :36760) was the
        CONSOLE serving at :36710 after it had taken the panel over. This
        test answered correctly there; what went dark was the render, and
        the fix for that is in the browser's own visibility rule, which
        now counts a viewer opened on itself.
        """
        browser = self._pickerBrowser()
        if browser is None:
            return False
        try:
            served = self.ownerComp.fetch('picker_url', '', search=False)
        except Exception:
            served = ''
        addr = getattr(browser.par, 'Address', None)
        if addr is None or not str(addr.eval()).startswith(served or url):
            return False
        try:
            return bool(browser.panel.winopen)
        except Exception:
            return False

    def _idleOff(self, delay_ms):
        ws = self.ownerComp.op('webserver')
        if ws is None or not ws.par.active.eval():
            return
        url = 'http://127.0.0.1:%d/' % int(ws.par.port.eval())
        quiet_s = absTime.seconds - getattr(self, '_last_request', 0)
        need_s = max(delay_ms / 1000.0, self.SERVER_IDLE_SECONDS)
        # A quiet page is not an abandoned one. The heartbeat only speaks
        # while someone moves a mouse or types, so reading the "Installed"
        # dialog for three minutes without touching anything went quiet,
        # the server stopped, the hold went with it and the render fell
        # dormant -- last frame still on screen, every click ignored, and
        # no way back in, because the wake signal was the input that the
        # dormant render no longer delivered (field report 2026-09-17).
        # An open window outranks silence: while the picker is on screen
        # it stays served, and the timer resumes once it is closed.
        if quiet_s < need_s:
            wait_ms = int((need_s - quiet_s) * 1000) + 500
        elif self._pickerOnScreen(url):
            wait_ms = int(self.SERVER_IDLE_SECONDS * 1000)
        else:
            wait_ms = 0
        if wait_ms:
            run("op(%r).ext.InstallerExt._idleOff(%d)" % (self.ownerComp.path, int(delay_ms)),
                delayMilliSeconds=wait_ms, delayRef=op.TDResources)
            return
        ws.par.active = False
        browser = self._pickerBrowser()
        if browser is not None and hasattr(browser.par, 'Holdactive'):
            addr = getattr(browser.par, 'Address', None)
            if addr is not None and str(addr.eval()).startswith(url):
                browser.par.Holdactive = False

    def _ownedProducts(self):
        """The package names this machine's account is entitled to; empty
        when signed out or when there is no updater beside us."""
        upd = self._updaterComp()
        try:
            a = upd.ext.ExtAuth if upd is not None else None
            rec = a.Account() if a is not None else None
            return set((rec or {}).get('products') or [])
        except Exception:
            return set()

    def _accountGlobal(self):
        """`window.FNS_ACCOUNT = ...;` for the served page, or ''.

        Omitted entirely when there is no updater beside us, so the page
        can tell "no auth rail here" from "signed out" -- the first has
        no sign-in to offer, the second does.

        Derived facts only. The device token and the download token stay
        in the updater: this page is rendered, not trusted.
        """
        upd = self._updaterComp()
        if upd is None:
            return ''
        acct = None
        try:
            a = upd.ext.ExtAuth
            if a is not None:
                rec = a.Account()
                if rec:
                    acct = {'label': rec.get('label') or 'supporter',
                            'products': sorted(rec.get('products') or []),
                            'checked_at': rec.get('checked_at') or 0,
                            # a BOOLEAN on purpose -- whether they hold
                            # any Patreon tier at all decides the button
                            # copy (Upgrade vs Become a supporter); the
                            # ids themselves stay in the keystore
                            'tier': bool(rec.get('tiers')),
                            # False only when the gate said the Patreon
                            # grant is gone: the page then offers Sign in
                            # again rather than a Check again that cannot help
                            'connected': rec.get('connected') is not False}
        except Exception:
            # never let an auth problem stop the picker from being served
            acct = None
        return 'window.FNS_ACCOUNT = %s;\n' % json.dumps(acct)

    def ServeRequest(self, request, response):
        """onHTTPRequest for the embedded Web Server DAT."""
        uri = request.get('uri', '/')
        method = request.get('method', 'GET')
        response['statusCode'], response['statusReason'] = 200, 'OK'
        self._last_request = absTime.seconds     # what _idleOff measures against
        try:
            if method == 'GET' and uri in ('/', '/index.html'):
                page = self.ownerComp.op('configurator_html')
                response['Content-Type'] = 'text/html; charset=utf-8'
                response['data'] = page.text if page else 'configurator_html missing'
            elif method == 'GET' and uri == '/manifest.js':
                response['Content-Type'] = 'text/javascript; charset=utf-8'
                path = self._par('Manifestfile') or DefaultManifest()
                full = path if os.path.isabs(path) else RepoPath(path)
                tgt = op(self._par('Target') or DefaultTarget(self.ownerComp))
                tool_names = None
                if os.path.exists(full):
                    try:
                        mdoc = LoadJson(full, 'manifest')
                        core_set = set(mdoc.get('core') or ())
                        tool_names = [p['name'] for p in mdoc.get('packages', [])
                                      if p.get('name') and p['name'] not in core_set]
                    except Exception:
                        tool_names = None
                firstrun = self._isFirstRun(tgt, tool_names)
                # the picker needs only the MANIFEST -- artifacts download
                # per-selection at install time, so a lightweight drop
                # stays lightweight until the user actually picks
                if os.path.exists(full):
                    # the page pre-checks what THIS PROJECT actually has,
                    # so unchecking an installed tool reads as removal --
                    # the machine-wide selection.json is scratch, not truth
                    installed, locked = [], ''
                    if tgt is not None:
                        # the rails and the root's own config host are the
                        # root's furniture, not installed tools: listing
                        # them here made the page read the host as an
                        # unchecked tool and plan its removal
                        installed = sorted(c.name for c in tgt.children
                                           if c.family == 'COMP'
                                           and c.name != ROOT_HOST
                                           and c.name not in self.RAILS)
                        # pane-placed packages are installed WITHOUT being
                        # root children: their truth is the install record.
                        # Without this they re-arrive unchecked and a
                        # re-apply spawns a second copy.
                        try:
                            man_doc = LoadJson(full, 'manifest')
                            spawn_names = {p['name']
                                           for p in man_doc.get('packages', [])
                                           if p.get('placement') in ('pane', 'root', 'none')}
                            rec_t = tgt.op(INSTALLED_DAT)
                            if rec_t is not None and spawn_names:
                                installed = sorted(set(installed) | {
                                    rec_t[i, 0].val
                                    for i in range(1, rec_t.numRows)
                                    if rec_t[i, 0].val in spawn_names})
                        except Exception:
                            pass
                        # the page disables Apply up front rather than
                        # letting the user pick and then get refused
                        locked = SourceLock(tgt.path)
                    # the machine's last install, for the first run's
                    # "Set up like last time" -- only offered on a bare
                    # root, so only read there
                    last = LastInstall(tgt) if firstrun else None
                    # Plus picks the user WANTED but could not install --
                    # every selection writer records them in `tools` while
                    # keeping them out of `install`. Resurfacing them here
                    # is what makes the wish survive sign-in, instead of
                    # living exactly one Textport line and evaporating.
                    wanted = []
                    try:
                        # Read the file THIS rail installs from -- the
                        # paste points Selectionfile at its own write in
                        # the store, and /selection re-points it at the
                        # palette copy. The machine-wide palette file is
                        # only the fallback: reading it unconditionally
                        # let a stale scratch copy from another session
                        # swallow a fresh paste's Plus picks (seen live:
                        # a wanted FNS_TimelineTools arrived unchecked).
                        selp = str(self._par('Selectionfile') or '')
                        if not (selp and os.path.exists(selp)):
                            selp = '%s/selection.json' % _fnsPaletteRoot()
                        if os.path.exists(selp):
                            with open(selp, 'r', encoding='utf-8') as sf:
                                seldoc = json.load(sf)
                            wanted = sorted(set(seldoc.get('tools') or [])
                                            - set(seldoc.get('install') or [])
                                            - set(installed))
                    except Exception:
                        wanted = []
                    # placed-only tools are in the project but not in the
                    # setup: the page shows them as Placed, never pre-ticks
                    # them (docs/PlaceOnce.md)
                    try:
                        placed = sorted(PlacedOnly(tgt))
                    except Exception:
                        placed = []
                    known_here = sorted(set(installed) | set(placed))
                    installed = sorted(set(installed) - set(placed))
                    checking = self._checkManifest(full)
                    with open(full, 'r', encoding='utf-8') as f:
                        man_text = f.read()
                    # tools this machine has not been shown yet (the
                    # picker's "New since you last looked"); never the
                    # whole catalog on a first run -- see UnseenTools
                    try:
                        unseen = UnseenTools(json.loads(man_text), known_here, firstrun)
                    except Exception as e:
                        debug('INSTALLER: new-tools record unreadable (%s)' % e)
                        unseen = []
                    response['data'] = ('window.FNS_SERVED = true;\n'
                                        'window.FNS_CHECKING = %s;\n'
                                        'window.FNS_FIRSTRUN = %s;\n'
                                        'window.FNS_LAST = %s;\n'
                                        'window.FNS_INSTALLED = %s;\n'
                                        'window.FNS_PLACED = %s;\n'
                                        'window.FNS_WANTED = %s;\n'
                                        'window.FNS_UNSEEN = %s;\n'
                                        'window.FNS_ANNOUNCE = %s;\n'
                                        'window.FNS_LOCKED = %s;\n'
                                        '%s'
                                        'window.FNS_MANIFEST = %s;\n'
                                        % (json.dumps(checking),
                                           json.dumps(firstrun),
                                           json.dumps(last),
                                           json.dumps(installed),
                                           json.dumps(placed),
                                           json.dumps(wanted),
                                           json.dumps(unseen),
                                           json.dumps(AnnounceNewTools()),
                                           json.dumps(locked),
                                           self._accountGlobal(), man_text))
                else:
                    why = '' if self._refreshActive() \
                        else self._refreshStore(names=[])
                    # A refusal used to ride out as a JS COMMENT: the page
                    # then said "this page refreshes itself" while waiting
                    # on a refresh that never began, and the reason was
                    # invisible to everyone (field report 2026-09-18, a
                    # clean install stuck on first run because the updater
                    # had no base URL to fetch from). Say it where the
                    # reader is.
                    response['data'] = ('window.FNS_REFRESHING = true;\n'
                                        'window.FNS_FIRSTRUN = %s;\n'
                                        'window.FNS_REFRESH_ERROR = %s;\n'
                                        % (json.dumps(firstrun),
                                           json.dumps(why or '')))
            elif method == 'GET' and uri == '/recommendations.json':
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(self._recommendations())
            elif method == 'POST' and uri == '/community/place':
                # A pinned tool by another creator, placed in the network
                # the user is working in (docs/CommunityHighlights.md).
                # The updater downloads, checks size and hash, and loads
                # it; the page polls GET /community/place for the answer.
                data = request.get('data', b'')
                if isinstance(data, bytes):
                    data = data.decode('utf-8', 'replace')
                try:
                    name = str((json.loads(data) or {}).get('name') or '')
                except Exception:
                    name = ''
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(self._placeCommunity(name))
            elif method == 'POST' and uri == '/community/install':
                # A tdp highlight: its locked Python packages into the
                # project's venv, then its tox placed like a pinned one.
                data = request.get('data', b'')
                if isinstance(data, bytes):
                    data = data.decode('utf-8', 'replace')
                try:
                    name = str((json.loads(data) or {}).get('name') or '')
                except Exception:
                    name = ''
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(self._installCommunity(name))
            elif uri == '/community/pyenv':
                # GET: can this project take a Python package? POST: set one
                # up with TouchDesigner's own TDPyEnvManager (Derivative's
                # disclaimer asks first).
                upd = self._updaterComp()
                response['Content-Type'] = 'application/json'
                if upd is None or getattr(upd, 'PythonEnvStatus', None) is None:
                    response['data'] = json.dumps({'state': 'unsupported'})
                elif method == 'POST':
                    run('args[0].valid and args[0].SetUpPythonEnv()', upd,
                        delayFrames=1, delayRef=op.TDResources)
                    response['data'] = json.dumps({'ok': True, 'state': 'creating'})
                else:
                    response['data'] = json.dumps(upd.PythonEnvStatus())
            elif method == 'GET' and uri == '/community/place':
                upd = self._updaterComp()
                try:
                    result = upd.ext.ExtUpdater.communityPlaceResult() if upd is not None else None
                except Exception:
                    result = None
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(result or {})
            elif method == 'GET' and uri == '/manifest/release':
                # The picker's catalog check (_checkManifest): is the check
                # still running, and which release does the store hold now?
                response['Content-Type'] = 'application/json'
                chk = getattr(self, '_manifest_check', None) or {}
                path = self._par('Manifestfile') or DefaultManifest()
                full = path if os.path.isabs(path) else RepoPath(path)
                release = ''
                try:
                    if os.path.exists(full):
                        release = str(LoadJson(full, 'manifest').get('release', '') or '')
                except Exception:
                    release = ''
                job = self._refreshJob()
                pending = self._manifestCheckPending()
                failed = (list(job.get('failed', []))[:4]
                          if job and not pending and job.get('stage') == 'failed' else [])
                response['data'] = json.dumps(
                    {'checking': pending, 'release': release,
                     'served': chk.get('served', ''), 'failed': failed})
            elif method == 'POST' and uri == '/auth/recheck':
                # "I just pledged" -- forces the gate past its six-hour
                # entitlement cache. The outcome arrives asynchronously:
                # the page polls /auth/status for the sentence and reloads
                # ITSELF when the products change (it does now -- this
                # comment used to promise that falsely).
                upd = self._updaterComp()
                why = ''
                if upd is None:
                    why = 'no FNS_Updater next to the installer'
                else:
                    try:
                        upd.ext.ExtAuth.Recheck()
                    except Exception as e:
                        why = str(e)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': not why,
                     'text': why or 'Checking with Patreon…'})
            elif method == 'POST' and uri == '/auth/signin':
                # the picker is where someone MEETS a Plus tool, so it is
                # where they will want to sign in. Starting it is all this
                # does: the updater owns the browser round trip, and the
                # page learns the outcome on its next load.
                upd = self._updaterComp()
                why = ''
                if upd is None:
                    why = 'no FNS_Updater next to the installer'
                else:
                    try:
                        upd.ext.ExtAuth.SignIn()
                    except Exception as e:
                        why = str(e)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': not why,
                     'text': why or ('Finish signing in in your browser. '
                                     'This page notices by itself and '
                                     'refreshes; Reload picker below does '
                                     'it now.')})
            elif method == 'POST' and uri == '/auth/redeem':
                # The lifetime-key door, on the same rail as Sign in: the
                # /plus/ page promises keys are redeemed "in the same
                # place as the Patreon connection", and before this route
                # that place was a parameter page the funnel never
                # pointed at. The page sends the PACKAGE name (a buyer
                # knows the tool, not Gumroad's product id); the gate
                # resolves it through its own map. Outcome is async --
                # the page's /auth/status watcher shows it and reloads
                # on product changes, same as sign-in.
                upd = self._updaterComp()
                why = ''
                raw = request.get('data', b'')
                try:
                    doc = json.loads(raw.decode('utf-8')
                                     if isinstance(raw, bytes) else str(raw))
                except Exception:
                    doc = {}
                if upd is None:
                    why = 'no FNS_Updater next to the installer'
                else:
                    try:
                        r = upd.ext.ExtAuth.RedeemKey(
                            key=str(doc.get('key') or ''),
                            package=str(doc.get('package') or ''))
                        if not r.get('ok'):
                            why = r.get('why', 'redeem refused')
                    except Exception as e:
                        why = str(e)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': not why, 'text': why or 'Checking your licence…'})
            elif method == 'GET' and uri == '/auth/status':
                # The sign-in/recheck OUTCOME, readable by the page. The
                # auth extension writes its result to Authstatus
                # asynchronously, and before this route the sentence
                # landed on a par nobody rendered while the dialog said
                # only "reload in a moment" -- a throttled user reloaded,
                # saw an unchanged chip, and concluded it was broken. The
                # page polls this after a recheck/sign-in, shows the
                # sentence, and reloads itself when products changed.
                upd = self._updaterComp()
                status_txt, products, connected = '', None, None
                # the label and the check time as well: a sign-in on an
                # account entitled to nothing changes no products, and the
                # page watching products alone waited forever for a change
                # that was never coming (field report 2026-09-17)
                label, checked_at = '', 0
                if upd is not None:
                    try:
                        p = getattr(upd.par, 'Authstatus', None)
                        status_txt = str(p.eval()) if p is not None else ''
                    except Exception:
                        status_txt = ''
                    try:
                        a = upd.ext.ExtAuth
                        rec = a.Account() if a is not None else None
                        if rec:
                            products = sorted(rec.get('products') or [])
                            connected = rec.get('connected') is not False
                            label = str(rec.get('label') or '')
                            checked_at = float(rec.get('checked_at') or 0)
                    except Exception:
                        products = None
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(
                    {'ok': True, 'status': status_txt, 'products': products,
                     'connected': connected, 'label': label,
                     'checked_at': checked_at})
            elif method == 'POST' and uri == '/open':
                # An external link, opened in the SYSTEM browser. Inside
                # TouchDesigner's Web Render a target=_blank link is a
                # popup, and popups are ignored (Redirect Popups off, and
                # on would navigate the picker away), so every docs link
                # in the served page was dead. Web URLs only; the server
                # listens on the loopback and answers this page alone.
                data = request.get('data', b'')
                if isinstance(data, bytes):
                    data = data.decode('utf-8', 'replace')
                try:
                    url = str((json.loads(data) or {}).get('url') or '')
                except Exception:
                    url = ''
                why = self._openExternal(url)
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps({'ok': not why, 'why': why})
            elif method == 'POST' and uri == '/seen':
                # the picker's "New since you last looked" was answered:
                # these tools have now been shown on this machine
                data = request.get('data', b'')
                if isinstance(data, bytes):
                    data = data.decode('utf-8', 'replace')
                try:
                    doc = json.loads(data) or {}
                    names = [str(n) for n in (doc.get('names') or [])]
                    if names:
                        MarkSeen(names)
                    out = {'ok': True, 'seen': len(names)}
                    # the "show this window when tools are added" preference
                    if isinstance(doc.get('announce'), bool):
                        out['announce'] = SetAnnounceNewTools(doc['announce'])
                except Exception as e:
                    out = {'ok': False, 'why': str(e)[:200]}
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(out)
            elif method == 'GET' and uri == '/newtools.json':
                # the console's badge on Install & remove: how many tools
                # the picker would announce, without rendering the picker.
                # Never records anything: only the picker's first look does.
                out = {'ok': True, 'unseen': []}
                try:
                    full = self._manifestPath()
                    seen = SeenPackages()
                    if full and os.path.exists(full) and seen is not None:
                        with open(full, 'r', encoding='utf-8') as f:
                            man = json.load(f)
                        known = set(seen)
                        # the picker's rule: a Patreon tool this account
                        # cannot get is never counted as news for it
                        owned = self._ownedProducts()
                        access = {str(p.get('name')): str(p.get('access', 'free') or 'free')
                                  for p in man.get('packages', [])}
                        out['unseen'] = sorted(
                            n for n in _pickableTools(man) if n not in known
                            and (access.get(n, 'free') == 'free' or n in owned))
                except Exception as e:
                    out = {'ok': False, 'why': str(e)[:200], 'unseen': []}
                response['Content-Type'] = 'application/json'
                response['data'] = json.dumps(out)
            elif method == 'POST' and uri == '/settings':
                # the page's "Open Settings" after an install: the console
                # takes the panel over, and this server has nothing left
                # to serve
                why = self._openSettings()
                response['Content-Type'] = 'application/json'
                # A real sentence on success: the page falls back to
                # "could not open the console" for EMPTY text, so the old
                # '' success read as a failure in the field.
                response['data'] = json.dumps(
                    {'ok': not why,
                     'text': why or 'Opening the FNS console…'})
                if not why:
                    self._serverOff(1500)
            elif method == 'POST' and uri == '/selection':
                sel_dir = _fnsPaletteRoot()
                os.makedirs(sel_dir, exist_ok=True)
                sel_path = sel_dir + '/selection.json'
                data = request.get('data', '')
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                sel = json.loads(data)    # refuse to write junk
                # the page decided from the account snapshot it loaded
                # with; the updater's entitlement decides what installs
                sel, held = self._holdPatreonLocked(sel)
                if held:
                    data = json.dumps(sel, indent=1) + '\n'
                with open(sel_path, 'w', encoding='utf-8') as f:
                    f.write(data)
                self.ownerComp.par.Selectionfile = sel_path
                # "Set up like last time" carries the bind mode the last
                # install used; an ordinary selection leaves the par alone
                bind = sel.get('bind') if isinstance(sel, dict) else None
                pf = getattr(self.ownerComp.par, 'Packagefiles', None)
                if bind and pf is not None and bind in pf.menuNames:
                    pf.val = bind
                plan = self.Plan()
                response['Content-Type'] = 'application/json'
                if (plan is None or plan.get('locked')
                        or plan['missing_artifact'] or not plan['steps']):
                    text = (self._planText(plan) if plan
                            else self._par('Status') or 'plan failed')
                    response['data'] = json.dumps({'ok': False, 'text': text})
                else:
                    response['data'] = json.dumps({'ok': True,
                                                   'text': self._planText(plan)})
            elif method == 'GET' and uri == '/status':
                # the page's fetch-then-install poll: how far along is the
                # scoped download, and is the selection installable yet?
                response['Content-Type'] = 'application/json'
                job = self._refreshJob()
                fetching = ((bool(job) and job.get('stage') not in ('done', 'failed'))
                            or getattr(self, '_pending_fetch', None) is not None)
                done = len(job.get('fetched', [])) if job else 0
                togo = (len(job.get('queue', [])) + len(job.get('inflight', {}))
                        if job else 0)
                ready, failed = False, []
                # A gated skip is a REFUSAL with a sentence, not a download
                # failure -- and its artifact will never arrive, so `ready`
                # must stop waiting for it or the page reports the refusal
                # as an unknown failure forever (field-confirmed on the
                # first real walk). Stamped reasons (gate unreachable,
                # session expired) speak verbatim; the local entitlement
                # skip falls back to MissingFor.
                gated, gated_why = [], []
                if job:
                    gated = sorted(set(job.get('gated') or []))
                    reasons = job.get('gated_reasons') or {}
                    aut = None
                    try:
                        upd = self._updaterComp()
                        aut = upd.ext.ExtAuth if upd is not None else None
                    except Exception:
                        aut = None
                    for n in gated:
                        gated_why.append(
                            reasons.get(n)
                            or (aut.MissingFor(n) if aut
                                else '%s needs a supporter account.' % n))
                if not fetching:
                    failed = list(job.get('failed', [])) if job else []
                    try:
                        plan = ResolvePlan(self._par('Selectionfile'),
                                           self._par('Manifestfile') or DefaultManifest(),
                                           self._par('Target')
                                           or DefaultTarget(self.ownerComp))
                        ready = not [n for n in plan['to_fetch']
                                     if n not in set(gated)]
                    except Exception:
                        ready = False
                # The updater's own Status par narrates the pass hop by hop
                # ("refresh: authorising...", "fetching 3 artifact(s)...").
                # Relaying it means a wedge NAMES ITS HOP in the page dialog
                # instead of looping a counter that says "Downloading" even
                # while the pass is authorising (0.5's observability half).
                detail = ''
                try:
                    upd2 = self._updaterComp()
                    if upd2 is not None:
                        detail = str(upd2.par.Status.eval())
                except Exception:
                    detail = ''
                response['data'] = json.dumps(
                    {'fetching': fetching, 'fetched': done, 'togo': togo,
                     'ready': ready, 'failed': failed[:4],
                     'gated': gated[:8], 'gated_why': gated_why[:4],
                     'detail': detail[:200]})
            elif method == 'POST' and uri == '/install':
                plan = ResolvePlan(self._par('Selectionfile'),
                                   self._par('Manifestfile') or DefaultManifest(),
                                   self._par('Target')
                                   or DefaultTarget(self.ownerComp))
                if plan.get('locked'):
                    response['Content-Type'] = 'application/json'
                    response['data'] = json.dumps(
                        {'ok': False, 'text': 'REFUSED -- ' + plan['locked']})
                    return response
                if plan['to_fetch']:
                    # download exactly the selection, then the page polls
                    # /status and re-posts /install once it is all here
                    mb = sum(s.get('bytes', 0) for s in plan['steps']
                             if s['name'] in plan['to_fetch']) / 1048576.0
                    why = self._fetchSelection(plan['to_fetch'])
                    response['Content-Type'] = 'application/json'
                    response['data'] = json.dumps(
                        {'ok': not why, 'fetching': True,
                         'text': why or 'downloading %d package(s), %.1f MB...'
                                 % (len(plan['to_fetch']), mb)})
                    return response
                res = self.Install(remove=True)
                response['Content-Type'] = 'application/json'
                if res is None:
                    response['data'] = json.dumps(
                        {'ok': False, 'text': self._par('Status') or 'install failed'})
                else:
                    lines = ['installed %d, removed %d, failed %d'
                             % (len(res['installed']), len(res.get('removed', [])),
                                len(res['failed']))]
                    placed = {r['name']: r.get('placed', '')
                              for r in res.get('results', [])}
                    lines += ['  %s%s' % (n, ' → ' + placed[n]
                                          if placed.get(n) else '')
                              for n in res['installed']]
                    if res.get('pane_note'):
                        lines.append('  (%s -- spawned into the toolkit '
                                     'container instead)' % res['pane_note'])
                    lines += ['  removed %s' % n for n in res.get('removed', [])]
                    lines += ['  %s' % n for n in res.get('remove_notes', [])]
                    lines += ['  FAILED %s' % n for n in res['failed']]
                    if not res['failed'] and self._keepStoreWanted():
                        lines.append('  the rest of the release downloads in the '
                                     'background, for offline use')
                    response['data'] = json.dumps(
                        {'ok': not res['failed'], 'text': '\n'.join(lines)})
                    if not res['failed']:
                        # Done: stop serving, AFTER this response has gone
                        # out. Otherwise the server stays on forever and
                        # gets saved into the .toe still listening. A
                        # minute, not seconds: the page's done step offers
                        # Open Settings (POST /settings), which needs a
                        # server to answer.
                        self._serverOff(60000)
            else:
                response['statusCode'], response['statusReason'] = 404, 'Not Found'
                response['data'] = 'not found'
        except Exception as e:
            response['statusCode'], response['statusReason'] = 500, 'Error'
            response['data'] = 'server error: %s' % e
        return response
