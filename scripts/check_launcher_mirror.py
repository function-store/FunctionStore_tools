"""check_launcher_mirror -- the launcher's copies of our registries must not drift.

TDXLPP (the launcher) carries FNSTools' PUBLISHED registry packages verbatim
(FNS_CommandRegistry: registry + built-in commands + FNS_About in one
artifact; FNS_MainMenuRegistry since v3.1.3) and a verbatim copy of the
FNSCommand module for its own tools. Each artifact's identity is recorded in
packaging/launcher_mirror.json at release time and the launcher's copy is
checked against that record. Run from either repo before shipping.

    python scripts/check_launcher_mirror.py            # TDXLPP beside this repo
    python scripts/check_launcher_mirror.py C:/path/to/TDXLPP

Exit 0 when everything agrees, 1 with a list of what differs.
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RECORD = os.path.join(REPO, 'packaging', 'launcher_mirror.json')

# (ours, theirs) -- module files that must stay byte-identical (BOM and line endings normalised)
MIRRORED_FILES = [
    ('modules/suspects/FNSTools/CustomParTools/QuickExt/ExtUtils/FNSCommand.py',
     'utility/TDXLauncherUtility/ExtUtils/FNSCommand.py'),
]

# the old mirror shape: a hand-copied registry extension and a fork of the built-ins.
# Their presence means the launcher has not switched to the artifact yet.
OLD_SHAPE = [
    'utility/TDXLauncherUtility/FNS_CommandRegistry/FNSCommandRegistryExt.py',
    'utility/TDXLauncherUtility/TDX_BuiltinCommands',
]


def normalised(path):
    raw = io.open(path, 'rb').read()
    return raw.decode('utf-8-sig').replace('\r\n', '\n')


def text_digest(path):
    return hashlib.sha256(normalised(path).encode('utf-8')).hexdigest()


def byte_digest(path):
    return hashlib.sha256(io.open(path, 'rb').read()).hexdigest()


def records(doc):
    """The per-package entries: schema 2 carries a `packages` list; the
    original record was one package at the top level."""
    if isinstance(doc, dict) and isinstance(doc.get('packages'), list):
        return list(doc['packages'])
    return [doc] if isinstance(doc, dict) and doc.get('package') else []


def main(argv):
    launcher = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.join(os.path.dirname(REPO), 'TDXLPP')
    problems, notes = [], []
    if not os.path.isdir(launcher):
        print('launcher checkout not found at %s' % launcher)
        return 1
    if not os.path.exists(RECORD):
        problems.append('no release record at packaging/launcher_mirror.json -- release the registries first')
        entries = []
    else:
        entries = records(json.load(io.open(RECORD, encoding='utf-8')))
        if not entries:
            problems.append('packaging/launcher_mirror.json carries no package entries')

    for ours, theirs in MIRRORED_FILES:
        a, b = os.path.join(REPO, ours), os.path.join(launcher, theirs)
        if not os.path.exists(b):
            problems.append('missing in launcher: %s' % theirs)
        elif text_digest(a) != text_digest(b):
            problems.append('DRIFT: %s differs from %s' % (theirs, ours))

    for rec in entries:
        copy = os.path.join(launcher, rec['launcher_copy'])
        if not os.path.exists(copy):
            problems.append('launcher has no artifact copy at %s' % rec['launcher_copy'])
        else:
            got = byte_digest(copy)
            if got != rec['sha256']:
                problems.append('DRIFT: %s is not the released %s %s (sha256 %s..., expected %s...)'
                                % (rec['launcher_copy'], rec['package'], rec['pkgversion'],
                                   got[:12], rec['sha256'][:12]))
        ours = os.path.join(REPO, rec['artifact'])
        if os.path.exists(ours) and byte_digest(ours) != rec['sha256']:
            notes.append('%s on disk is not the recorded published build -- publish, then rewrite '
                         'packaging/launcher_mirror.json to the published entry and hand the launcher the '
                         'new artifact' % rec['artifact'])

    for rel in OLD_SHAPE:
        if os.path.exists(os.path.join(launcher, rel)):
            problems.append('old mirror shape still present: %s (the artifact carries this now; remove it)' % rel)

    for n in notes:
        print('note: ' + n)
    if problems:
        print('launcher mirror: %d problem(s)' % len(problems))
        for p in problems:
            print('  - ' + p)
        return 1
    print('launcher mirror OK: FNSCommand.py identical, %s'
          % ', '.join('%s %s matches the release record' % (r['package'], r['pkgversion']) for r in entries))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
