"""Released artifacts carry no Private Investigator markers.

A published tox is a COPY. A copy that still carries `pi_suspect`,
`FNS_externalized` or `Vcoriginal` True is a user's placed tool that PI
treats as a tracked dev original (measured 2026-09-17: eight store
artifacts carried them, root and 2-25 inner operators each). The publish
rail exports through Embody, which strips only Embody's own tags, so
build_manifest.ExportPackage scrubs the written artifact: load it into a
cooking-disabled holder, strip, save it back. The live master is never
touched (stripping and restoring on the master marked it modified).

Runs outside TouchDesigner: build_manifest.py is exec'd with the TD
builtins it touches replaced by small fakes.

    python tests/test_release_markers.py
"""
import io
import os
import shutil
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_GEN = os.path.join(_ROOT, 'packaging', 'build_manifest.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


class Par(object):
    def __init__(self, val):
        self.val = val

    def eval(self):
        return self.val


class FakeOp(object):
    def __init__(self, name, parent=None, tags=(), is_comp=True, vcoriginal=None):
        self.name = name
        self.path = (parent.path.rstrip('/') + '/' + name) if parent else '/' + name
        self.tags = set(tags)
        self.isCOMP = is_comp
        self.par = types.SimpleNamespace()
        if vcoriginal is not None:
            self.par.Vcoriginal = Par(vcoriginal)
        self.children = []
        self.allowCooking = True
        self.saved_to = []
        if parent is not None:
            parent.children.append(self)

    def findChildren(self):
        out = []
        for c in self.children:
            out.append(c)
            out.extend(c.findChildren())
        return out

    def save(self, path):
        self.saved_to.append(path)


class Holder(FakeOp):
    """The /sys/quiet holder: loadTox builds whatever tree the test queued."""
    def __init__(self, quiet, tree):
        FakeOp.__init__(self, 'fns_release_scrub', parent=quiet)
        self.quiet = quiet
        self.tree = tree
        self.destroyed = False
        self.loaded_from = None

    def loadTox(self, path):
        self.loaded_from = path
        if isinstance(self.tree, Exception):
            raise self.tree
        return self.tree

    def destroy(self):
        self.destroyed = True
        self.quiet.children.remove(self)


class Quiet(FakeOp):
    def __init__(self):
        FakeOp.__init__(self, 'quiet')
        self.next_tree = None
        self.holders = []

    def create(self, kind, name):
        h = Holder(self, self.next_tree)
        self.holders.append(h)
        return h


def load_build_manifest(repo, quiet, embody):
    mod = types.ModuleType('build_manifest_under_test')

    class OpShim(object):
        Embody = embody

        def __call__(self, path):
            return quiet if path in ('/sys/quiet', '/sys') else None

    mod.__dict__['project'] = types.SimpleNamespace(folder=repo, name='t')
    mod.__dict__['app'] = types.SimpleNamespace(build='2025.33070')
    mod.__dict__['op'] = OpShim()
    mod.__dict__['debug'] = lambda *a, **k: None
    mod.__dict__['baseCOMP'] = object()
    code = io.open(MANIFEST_GEN, encoding='utf-8').read()
    exec(compile(code, MANIFEST_GEN, 'exec'), mod.__dict__)
    return mod


def marked_tree():
    root = FakeOp('FNS_Foo', tags=('pi_suspect', 'fnscommands'), vcoriginal=True)
    ext = FakeOp('FooExt', parent=root, tags=('pi_suspect', 'TDExtension'), is_comp=False)
    about = FakeOp('FNS_About', parent=root, vcoriginal=True)
    FakeOp('CustomParHelper', parent=about, tags=('FNS_externalized', 'pi_suspect', 'extPackage'), is_comp=False)
    FakeOp('Plain', parent=root, vcoriginal=False)
    return root


class Embody(object):
    def __init__(self):
        self.result = True
        self.calls = []

    def ExportPortableTox(self, target=None, save_path=None):
        self.calls.append((target, save_path))
        if self.result:
            with open(save_path, 'wb') as f:
                f.write(b'tox bytes %d' % len(self.calls))
        return self.result


repo = tempfile.mkdtemp(prefix='fns_release_markers_')
try:
    quiet = Quiet()
    embody = Embody()
    bm = load_build_manifest(repo, quiet, embody)

    # ------------------------------------------------------------ 1
    print('1. StripReleaseMarkers clears PI markers on a copy, nothing else')
    tree = marked_tree()
    changed = bm.StripReleaseMarkers(tree)
    everything = [tree] + tree.findChildren()
    check('no operator keeps pi_suspect or FNS_externalized',
          not [o.path for o in everything if o.tags & {'pi_suspect', 'FNS_externalized'}])
    check('other tags stay (fnscommands, TDExtension, extPackage)',
          'fnscommands' in tree.tags and 'TDExtension' in tree.children[0].tags
          and 'extPackage' in tree.children[1].children[0].tags)
    check('Vcoriginal True becomes False on every COMP carrying it',
          tree.par.Vcoriginal.val is False and tree.children[1].par.Vcoriginal.val is False)
    check('a DAT is never asked for Vcoriginal, and an already-False one is not counted',
          '/FNS_Foo/Plain' not in changed)
    check('it reports the four operators it changed',
          sorted(changed) == sorted(['/FNS_Foo', '/FNS_Foo/FooExt', '/FNS_Foo/FNS_About',
                                     '/FNS_Foo/FNS_About/CustomParHelper']), changed)
    check('PI_RELEASE_TAGS names both tags PI\'s own release scrub removes',
          set(bm.PI_RELEASE_TAGS) == {'pi_suspect', 'FNS_externalized'})

    # ------------------------------------------------------------ 2
    print('2. ScrubArtifact loads, strips, saves back, always cleans up')
    art = os.path.join(repo, 'a.tox')
    quiet.next_tree = marked_tree()
    n = bm.ScrubArtifact(art)
    h = quiet.holders[-1]
    check('the artifact is loaded into a holder in /sys/quiet', h.loaded_from == art)
    check('cooking is off on the holder, and left alone on the loaded copy (it would be saved)',
          h.allowCooking is False and quiet.next_tree.allowCooking is True)
    check('the stripped copy is saved back over the artifact', quiet.next_tree.saved_to == [art])
    check('it returns how many operators changed', n == 4, n)
    check('the holder is destroyed', h.destroyed and h not in quiet.children)

    clean = FakeOp('FNS_Clean', tags=('fnscommands',))
    quiet.next_tree = clean
    check('an artifact with nothing to strip is not re-saved (bytes stay identical)',
          bm.ScrubArtifact(art) == 0 and clean.saved_to == [])

    quiet.next_tree = RuntimeError('not a tox')
    try:
        bm.ScrubArtifact(art)
        raised = False
    except RuntimeError:
        raised = True
    check('a load failure raises, and the holder is still destroyed',
          raised and quiet.holders[-1].destroyed)

    # ------------------------------------------------------------ 3
    print('3. ExportPackage scrubs the artifact and never touches the live master')
    scrubbed = []
    bm.__dict__['ScrubArtifact'] = lambda path: scrubbed.append(path) or 3
    live = marked_tree()
    before = [(o.path, sorted(o.tags), getattr(o.par, 'Vcoriginal', Par(None)).val)
              for o in [live] + live.findChildren()]
    res = bm.ExportPackage(live)
    after = [(o.path, sorted(o.tags), getattr(o.par, 'Vcoriginal', Par(None)).val)
             for o in [live] + live.findChildren()]
    dest = bm._repo(bm.DIST_DIR, 'FNS_Foo.tox')
    check('Embody exports the live master to dist', embody.calls[-1] == (live, dest))
    check('the written artifact is scrubbed', scrubbed == [dest], scrubbed)
    check('the live master keeps every tag and its Vcoriginal', before == after)
    check('the result hashes the scrubbed file',
          res is not None and res['path'] == 'packaging/dist/FNS_Foo.tox' and len(res['sha256']) == 64)

    def failing_scrub(path):
        raise RuntimeError('save refused')
    bm.__dict__['ScrubArtifact'] = failing_scrub
    check('a failed scrub fails the export (no hash for a marked artifact)',
          bm.ExportPackage(marked_tree()) is None)

    bm.__dict__['ScrubArtifact'] = lambda path: scrubbed.append(path) or 0
    scrubbed[:] = []
    embody.result = False
    check('a failed export returns None and is not scrubbed',
          bm.ExportPackage(marked_tree()) is None and scrubbed == [])
    embody.result = True

    src = io.open(MANIFEST_GEN, encoding='utf-8').read()
    body = src[src.index('def ExportPackage('):]
    body = body[:body.index('\ndef ', 1)]
    check('ExportPackage never calls StripReleaseMarkers on the live comp',
          'StripReleaseMarkers' not in body)
finally:
    shutil.rmtree(repo, ignore_errors=True)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all release-marker checks pass')
