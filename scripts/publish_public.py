"""Generate the PUBLIC mirror from this private repo.

The public repo (function-store/FunctionStore_tools) used to be a plain
push of this tree: `public/dev25` is an ANCESTOR of this history, which
is exactly why a stray `git push public HEAD:dev25` would fast-forward
and publish paid source. This script replaces that with a GENERATED
mirror -- a filtered copy of one commit, committed into a checkout of
the public repo. After the first run the two histories diverge, so git
itself rejects the stray push before any hook has to.

What is withheld, and why each rule exists:

  toe       Every *.toe. FunctionStore_tools_2025_DEV.toe fully embeds
            /TDXLauncherUtility (a DIFFERENT product: externaltox points
            at ../TDXLPP/release/, enableexternaltox is OFF and
            savebackup is ON, so its contents live in the binary), plus
            tox_updater, TDAsyncIO, and a drift of scratch. Keeping a
            hand-pruned .toe publishable is a chore repeated every
            publish, and the publish that forgets it is the one that
            leaks TDXL. Nobody consuming FNSTools needs the dev project
            -- the toolkit ships as toxes through the installer.
  gated     Everything that IS a package catalog.json marks non-free.
            Derived from the catalog, never a hand-kept list, so gating
            a tool tomorrow updates this with no code edit.
  declared  A few paths the derivation cannot see -- design docs whose
            names do not carry the package name. Deliberately explicit,
            and the path sweep below refuses to run when a NEW one
            appears unclassified.

Mentioning a gated tool is not leaking it: catalog.json, manifest.json,
packaging/docs/<Name>.md and the design docs that reference the gate all
publish normally. Only paths that ARE the tool are withheld.

One leak no path rule can catch: the root suspect tox publishes, and it
EMBEDS every child whose enableexternaltox is off. EmbeddedGated() reads
each gated package's carrier off the manifest and refuses the run (every
mode, the pre-push hook included) while any gated package is root-carried
or unknown to the manifest.

    python scripts/publish_public.py                   # dry run (default)
    python scripts/publish_public.py --target ../DIR   # explicit checkout
    python scripts/publish_public.py --local           # commit locally only
    python scripts/publish_public.py --push            # commit and publish

Dry run is the default and prints every exclusion with the rule that
produced it. Nothing is written without --push.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import tarfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(REPO, 'packaging', 'catalog.json')

DEFAULT_TARGET = os.path.normpath(
    os.path.join(REPO, '..', 'FNSTools_PUB'))
BRANCH = 'dev25'
# The mirror's identity. A target whose origin does not match this is
# refused: publishing into the wrong checkout is unrecoverable.
PUBLIC_SLUG = 'function-store/FunctionStore_tools'

# Paths that belong to a gated package but carry no package name, so no
# derivation can find them. Each one is a deliberate decision; the sweep
# in _unclassified() refuses the run when a new candidate appears.
DECLARED_PRIVATE = (
    'docs/TimelineToolsContract.md',
    'docs/MarkersToolContract.md',
    'docs/TimelineBackgroundContract.md',
    'docs/WaveformToolContract.md',
    # Sample EDL/CSV/XML marker files -- fixtures for the gated tool's
    # importer. No published test reads them.
    'tests/fixtures/markers/README.md',
    'tests/fixtures/markers/audacity_labels.txt',
    'tests/fixtures/markers/cue_sheet.txt',
    'tests/fixtures/markers/fcpxml_markers.fcpxml',
    'tests/fixtures/markers/premiere_legacy.xml',
    'tests/fixtures/markers/premiere_markers.csv',
    'tests/fixtures/markers/premiere_markers_tabbed.csv',
    'tests/fixtures/markers/resolve_dropframe.edl',
    'tests/fixtures/markers/resolve_markers.edl',
)

# Whole private subtrees. DECLARED_PRIVATE is exact paths on purpose (a
# doc is one file); these are CONTAINERS whose future contents must stay
# withheld without anyone re-listing them file by file. PreviewPanel25 is
# a root-level dev container (the network FNS_PaneTypeRegistry was
# authored in) -- _packageish() only recognises package shapes under
# FNSTools/ and modules/suspects/FNSTools/, so root-level suspects like
# this passed the fail-closed sweep unexamined and published by accident.
DECLARED_PRIVATE_PREFIXES = (
    'PreviewPanel25/',
    'modules/suspects/PreviewPanel25.tox',
    'modules/suspects/PreviewPanel25/',
    # PI's portable release exports. The root one embeds EVERY tool --
    # the gated package included at full 323-op strength, which is how
    # 9MB of FNS_TimelineTools reached the mirror in Release v3.0.12
    # (2026-08-30). Untracked + gitignored in the private repo since
    # 65c758e; withheld here so a stray re-track can never publish, and
    # so the next publish DELETES the copies the mirror already carries.
    'modules/release/',
)

# Paths that legitimately carry a gated package's name and still publish:
# the public catalogue and the tool's own user-facing doc page (the site
# build hard-fails without it, and a Plus tool having a docs page is the
# point).
def _nameAllowed(path, name):
    return path in (
        'packaging/catalog.json',
        'packaging/manifest.json',
        'packaging/release.json',
        'packaging/docs/%s.md' % name,
    )


# Package-shaped paths that predate the catalog: legacy registry names,
# rails, and odds and ends that already publish today. Seeded once from
# what the mirror carried on 2026-08-29 -- NOT a place to add new work.
# A new tool belongs in catalog.json, where its access flag lives.
GRANDFATHERED = (
    'tools_ui',
    'ConfigRegistry', 'ExternalTables', 'FNS_Config', 'FNS_Installer',
    'FNS_UISkin', 'MainMenuRegistry', 'NavbarRegistry', 'Olib_Browser1',
    'OpMenuRegistry', 'PaneTypeRegistry', 'ToolbarRegistry', 'UPDATER',
    'op_store_mod',
)


def _packageish(path):
    """The package name a path belongs to, or None if it is not one.

    Two shapes carry package source: the externalized python under
    FNSTools/<Name>/, and the suspect tox (plus its sub-tox folder) under
    modules/suspects/FNSTools/.
    """
    parts = path.split('/')
    if len(parts) > 2 and parts[0] == 'FNSTools':
        return parts[1]
    if len(parts) > 3 and parts[:3] == ['modules', 'suspects', 'FNSTools']:
        tail = parts[3]
        if tail.lower().endswith('.tox'):
            return tail[:-4]
        # A bare folder here is a package's SUB-COMPONENT (the merged
        # CustomParTools tools live this way), not a package -- unless a
        # sibling tox of the same name says otherwise. A gated package's
        # sub-folder is already covered by the gated rule above.
        if os.path.exists(os.path.join(
                REPO, 'modules', 'suspects', 'FNSTools', tail + '.tox')):
            return tail
    return None


def _git(*args, **kw):
    """Run git in REPO (or kw['cwd']) and return stdout text."""
    return subprocess.check_output(
        ('git',) + args, cwd=kw.get('cwd', REPO)).decode('utf-8', 'replace')


def GatedPackages():
    """Package names catalog.json marks non-free. The single source."""
    cat = json.load(io.open(CATALOG, encoding='utf-8'))
    pk = cat.get('packages', cat)
    out = []
    for name, meta in sorted(pk.items()):
        access = str((meta or {}).get('access', 'free') or 'free')
        if access != 'free':
            out.append(name)
    return out


def KnownPackages():
    """Every name catalog.json knows, free or gated."""
    cat = json.load(io.open(CATALOG, encoding='utf-8'))
    return set(cat.get('packages', cat))


def EmbeddedGated():
    """Gated packages whose bytes would ride INSIDE a published tox.

    The path rules withhold a gated package's OWN files, but the root
    suspect (modules/suspects/FNSTools.tox) publishes -- and it EMBEDS
    every child whose `enableexternaltox` is off ('carried by the ROOT
    toolkit tox'). A gated package in that state leaks through a file no
    path rule can withhold, so the publish must refuse instead. The
    manifest records each package's carrier (`tox_carrier`: 'root' =
    embedded, 'own' = the root holds only a reference).

    A second flag does the same thing more quietly: `savebackup` (Save
    Backup of External, TD default ON) embeds a full backup copy on every
    parent save EVEN WITH the external binding intact. The manifest
    carries it as `save_backup` (presence-style).

    Returns (embedded, unknown): gated names whose bytes the root tox
    would carry (root-carried, or backup-embedding), and gated names the
    manifest does not know (undecidable -- also refused, fail closed).
    """
    gated = GatedPackages()
    if not gated:
        return [], []
    try:
        man = json.load(io.open(
            os.path.join(REPO, 'packaging', 'manifest.json'),
            encoding='utf-8'))
        carriers = {p['name']: str(p.get('tox_carrier', ''))
                    for p in man.get('packages', [])}
        backups = {p['name'] for p in man.get('packages', [])
                   if p.get('save_backup')}
    except Exception:
        return [], sorted(gated)
    embedded = sorted({n for n in gated if carriers.get(n) == 'root'}
                      | (set(gated) & backups))
    return embedded, sorted(n for n in gated if n not in carriers)


def _gatedPrefixes(name):
    """The standard on-disk layout of one package."""
    return (
        'FNSTools/%s/' % name,
        'modules/suspects/FNSTools/%s/' % name,
    ), (
        'modules/suspects/FNSTools/%s.tox' % name,
    )


def Rule(path, gated):
    """Which rule withholds this path, or None to publish it."""
    if path.lower().endswith('.toe'):
        return 'toe'
    if path in DECLARED_PRIVATE:
        return 'declared'
    if any(path == p.rstrip('/') or path.startswith(p)
           for p in DECLARED_PRIVATE_PREFIXES):
        return 'declared'
    for name in gated:
        prefixes, exacts = _gatedPrefixes(name)
        if path in exacts or any(path.startswith(p) for p in prefixes):
            return 'gated:%s' % name
    # Fail closed: package-shaped and undeclared means nobody has decided
    # whether it is free. Withhold until catalog.json says.
    pkg = _packageish(path)
    if pkg and pkg not in GRANDFATHERED and pkg not in KnownPackages():
        return 'undeclared:%s' % pkg
    return None


def _tokens(name):
    """Name fragments that mark a path as belonging to a gated package.

    The package name, the same without the FNS_ prefix, and every
    sub-component the package's own suspect folder declares -- so a
    gated tool's internals are recognised by their own names too.
    """
    out = {name}
    if name.startswith('FNS_'):
        out.add(name[4:])
    sub = os.path.join(REPO, 'modules', 'suspects', 'FNSTools', name)
    if os.path.isdir(sub):
        for f in os.listdir(sub):
            if f.lower().endswith('.tox'):
                stem = f[:-4]
                out.add(stem)
                if stem.startswith('FNS_'):
                    out.add(stem[4:])
    return sorted(out)


def _unclassified(published, gated):
    """Published paths whose NAME says they may belong to a gated tool.

    This is the guard against a future gated package whose files do not
    sit in the standard layout. It looks at paths only -- a doc that
    merely mentions a Plus tool is not a leak and must keep publishing.
    """
    hits = []
    for name in gated:
        toks = _tokens(name)
        for path in published:
            if _nameAllowed(path, name):
                continue
            low = path.lower()
            if any(t.lower() in low for t in toks):
                hits.append((path, name))
    return hits


def Plan(rev='HEAD'):
    """What one publish would contain, withhold, and flag."""
    gated = GatedPackages()
    tracked = [p for p in _git('ls-tree', '-r', '--name-only', rev).split('\n')
               if p.strip()]
    published, withheld = [], []
    for path in tracked:
        rule = Rule(path, gated)
        (withheld if rule else published).append(
            (path, rule) if rule else path)
    return {
        'rev': _git('rev-parse', rev).strip(),
        'gated': gated,
        'published': published,
        'withheld': withheld,
        'unclassified': _unclassified(published, gated),
    }


def _shas(args, cwd, sha_index):
    """path -> blob sha, from `git ls-tree -r` or `git ls-files -s`.

    Both print `<fields...> <TAB> <path>`; splitting on whitespace with a
    maxsplit keeps a path with spaces intact.
    """
    out = {}
    for line in _git(*args, cwd=cwd).splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 3)
        if len(parts) == 4:
            out[parts[3]] = parts[sha_index]
    return out


def Diff(plan, target):
    """What one publish would change in the mirror checkout.

    Compares git blob shas -- the same content hash on both sides, so a
    byte-identical file never shows up as a change.
    """
    want = _shas(('ls-tree', '-r', plan['rev']), REPO, 2)
    want = {k: v for k, v in want.items() if k in set(plan['published'])}
    have = _shas(('ls-files', '-s'), target, 1)
    return {
        'added': sorted(p for p in want if p not in have),
        'changed': sorted(p for p in want if p in have and have[p] != want[p]),
        'removed': sorted(p for p in have if p not in want),
    }


def _targetOk(target):
    if not os.path.isdir(os.path.join(target, '.git')):
        return 'not a git checkout: %s' % target
    try:
        url = _git('remote', 'get-url', 'origin', cwd=target).strip()
    except subprocess.CalledProcessError:
        return 'no origin remote in %s' % target
    if PUBLIC_SLUG.lower() not in url.lower():
        return 'origin is %s -- expected the public mirror (%s)' % (
            url, PUBLIC_SLUG)
    branch = _git('rev-parse', '--abbrev-ref', 'HEAD', cwd=target).strip()
    if branch != BRANCH:
        return 'target is on %r -- check out %r first' % (branch, BRANCH)
    return None


def _materialize(rev, published, target):
    """Write the published set into target, and delete what left it."""
    keep = set(published)
    tar = subprocess.Popen(('git', 'archive', '--format=tar', rev),
                           cwd=REPO, stdout=subprocess.PIPE)
    written = 0
    with tarfile.open(fileobj=tar.stdout, mode='r|') as tf:
        for m in tf:
            if not m.isfile() or m.name not in keep:
                continue
            dest = os.path.join(target, m.name.replace('/', os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            src = tf.extractfile(m)
            with open(dest, 'wb') as fh:
                fh.write(src.read())
            written += 1
    tar.stdout.close()
    tar.wait()

    removed = []
    for path in _git('ls-files', cwd=target).split('\n'):
        path = path.strip()
        if path and path not in keep:
            full = os.path.join(target, path.replace('/', os.sep))
            if os.path.exists(full):
                os.remove(full)
            removed.append(path)
    return written, removed


def _assertClean(target, gated):
    """Refuse to leave a withheld path sitting in the mirror."""
    bad = []
    for path in _git('ls-files', cwd=target).split('\n'):
        path = path.strip()
        if path and Rule(path, gated):
            bad.append(path)
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--target', default=DEFAULT_TARGET,
                    help='checkout of the public repo (default: %(default)s)')
    ap.add_argument('--rev', default='HEAD',
                    help='commit to publish (default: HEAD -- committed '
                         'state only, never the dirty working tree)')
    ap.add_argument('--push', action='store_true',
                    help='write, commit AND push. Without it: dry run.')
    ap.add_argument('--local', action='store_true',
                    help='write and commit into the mirror checkout, but do '
                         'NOT push -- so the commit can be inspected before '
                         'it reaches the world. Push it yourself afterwards.')
    ap.add_argument('--check-rev', metavar='REV',
                    help='exit non-zero when the tree at REV holds ANY '
                         'withheld path. This is what the pre-push hook '
                         'calls, so hook and publisher cannot drift apart.')
    args = ap.parse_args(argv)

    # The embedding guard runs in EVERY mode, the hook's included: a
    # root-carried gated package taints modules/suspects/FNSTools.tox
    # itself, which no per-path rule can withhold.
    embedded, unknown = EmbeddedGated()
    if embedded or unknown:
        if embedded:
            print('REFUSED -- gated package(s) whose bytes ride the '
                  'published root tox: %s' % ', '.join(embedded))
            print('Root-carried (tox_carrier "root") or backup-embedding '
                  '(Save Backup of External on). Turn enableexternaltox ON '
                  'and savebackup OFF, PI-save the package and the root, '
                  'rebuild the manifest, then re-run.')
        if unknown:
            print('REFUSED -- gated package(s) the manifest does not know: '
                  '%s' % ', '.join(unknown))
            print('Their carrier is undecidable, so whether the root tox '
                  'embeds them is too. Rebuild the manifest first.')
        return 2

    if args.check_rev:
        plan = Plan(args.check_rev)
        if not plan['withheld']:
            return 0
        print('REFUSED: %s carries %d withheld path(s), including:'
              % (args.check_rev[:12], len(plan['withheld'])))
        for path, rule in sorted(plan['withheld'],
                                 key=lambda r: (r[1], r[0]))[:8]:
            print('  %-14s %s' % (rule, path))
        print('The public mirror is GENERATED -- publish with '
              'scripts/publish_public.py, never by pushing this history.')
        return 2

    plan = Plan(args.rev)
    gated = plan['gated']

    print('publishing %s' % plan['rev'][:12])
    print('gated packages (from catalog.json): %s'
          % (', '.join(gated) or 'none'))
    print()
    print('WITHHELD (%d):' % len(plan['withheld']))
    for path, rule in sorted(plan['withheld'], key=lambda r: (r[1], r[0])):
        print('  %-14s %s' % (rule, path))
    print()
    print('PUBLISHED: %d files' % len(plan['published']))

    if plan['unclassified']:
        print()
        print('REFUSED -- these published paths carry a gated package name '
              'and are not classified:')
        for path, name in plan['unclassified']:
            print('  %s   (matches %s)' % (path, name))
        print('Add each to DECLARED_PRIVATE (it belongs to the tool) or to '
              '_nameAllowed (it merely mentions it), then re-run.')
        return 2

    problem = _targetOk(args.target)
    writing = args.push or args.local

    if not writing:
        print()
        if problem:
            print('target not ready (%s)' % problem)
            print('-- filter shown above; clone the mirror to see the '
                  'file-by-file diff.')
        else:
            d = Diff(plan, args.target)
            print('AGAINST %s' % args.target)
            print('  added %d / changed %d / removed %d'
                  % (len(d['added']), len(d['changed']), len(d['removed'])))
            for label in ('removed', 'added'):
                for path in d[label][:20]:
                    print('    %-8s %s' % (label, path))
                if len(d[label]) > 20:
                    print('    %-8s ... and %d more'
                          % (label, len(d[label]) - 20))
        print()
        print('dry run -- nothing written. --local to commit into the '
              'mirror, --push to commit and publish.')
        return 0

    if problem:
        print('\nREFUSED -- %s' % problem)
        return 2

    # The mirror can move without us -- a merged PR, a publish from
    # another machine. Catch that BEFORE rewriting files, not at push
    # time when the working tree is already replaced.
    try:
        _git('pull', '--ff-only', 'origin', BRANCH, cwd=args.target)
    except subprocess.CalledProcessError:
        print('\nREFUSED -- %s/%s has moved and this checkout cannot '
              'fast-forward to it.' % (args.target, BRANCH))
        print('Someone merged into the mirror, or it was published from '
              'elsewhere. Reconcile that checkout (or re-clone) first --'
              ' publishing over it would silently revert their change.')
        return 2

    written, removed = _materialize(args.rev, plan['published'], args.target)
    # Stage FIRST: `git ls-files` reads the INDEX, so a file deleted from
    # the working tree still lists until that deletion is staged.
    # Asserting before this reports every correct removal as a leak.
    _git('add', '-A', cwd=args.target)
    bad = _assertClean(args.target, gated)
    if bad:
        print('\nREFUSED -- withheld paths reached the mirror: %s' % bad)
        return 2

    status = _git('status', '--porcelain', cwd=args.target).strip()
    if not status:
        print('\nmirror already matches %s -- nothing to commit'
              % plan['rev'][:12])
        return 0
    # A message a public-repo reader can use. Built ONLY from material
    # that publishes anyway -- the mirror's own diff and the manifest's
    # release label -- never the private commit's subject, which may
    # describe withheld work. The source hash stays as a trailer for
    # traceability.
    changed = []
    for line in status.splitlines():
        p = line[3:].strip().strip('"')
        if ' -> ' in p:
            p = p.split(' -> ', 1)[1]
        changed.append(p)
    areas = sorted({p.split('/', 1)[0] if '/' in p else p for p in changed})
    new_rel = old_rel = None
    try:
        with open(os.path.join(args.target, 'packaging', 'manifest.json'),
                  encoding='utf-8') as f:
            new_rel = json.load(f).get('release')
    except Exception:
        pass
    try:
        old_rel = json.loads(_git('show', 'HEAD:packaging/manifest.json',
                                  cwd=args.target)).get('release')
    except Exception:
        pass
    if new_rel and new_rel != old_rel:
        subject = 'Release %s' % new_rel
    else:
        shown = ', '.join(areas[:4]) + (', ...' if len(areas) > 4 else '')
        subject = 'Update %s' % shown
    msg = ('%s\n\n%d file(s) changed across %s.\n\n'
           'Generated by scripts/publish_public.py from private commit '
           '%s.\nWithheld: %d paths (the script carries the rules).\n'
           % (subject, len(changed), ', '.join(areas),
              plan['rev'][:12], len(plan['withheld'])))
    _git('commit', '-m', msg, cwd=args.target)
    if not args.push:
        sha = _git('rev-parse', '--short', 'HEAD', cwd=args.target).strip()
        print('\ncommitted LOCALLY as %s: %d files written, %d removed. '
              'Nothing has left this machine.' % (sha, written, len(removed)))
        print('Inspect:  git -C %s show --stat' % args.target)
        print('Publish:  git -C %s push origin %s' % (args.target, BRANCH))
        return 0
    _git('push', 'origin', BRANCH, cwd=args.target)
    print('\npublished: %d files written, %d removed, pushed to %s/%s'
          % (written, len(removed), PUBLIC_SLUG, BRANCH))
    return 0


if __name__ == '__main__':
    sys.exit(main())
