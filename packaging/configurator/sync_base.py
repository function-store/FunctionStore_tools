"""Sync the shared UI base into every shell that inlines it.

packaging/configurator/base.css is the single source for the FNSTools UI
design tokens and shared components, and base.js for the behaviour both
web shells share (tooltips: FNS:UIBASEJS markers, same rules). The shells that consume it must each
stay a single self-contained file (one is embedded into the installer and
served from a Text DAT inside TouchDesigner; one doubles as a
double-clickable standalone), so the base is INLINED into each of them
between markers rather than linked:

    /* FNS:UIBASE:START ... */
    ...the whole of base.css...
    /* FNS:UIBASE:END */

Run from the repo root (or anywhere -- paths resolve from this file):

    python packaging/configurator/sync_base.py           # drift check only
    python packaging/configurator/sync_base.py --write   # push the base out

The bare run exits non-zero on drift, which is what
tests/test_ui_base_sync.py runs, so a stale copy fails the suite instead
of shipping. A shell whose markers are missing is a hard error in both
modes: silently skipping it is how a hand-synced palette rots.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(HERE, 'base.css')
BASE_JS = os.path.join(HERE, 'base.js')

START = '/* FNS:UIBASE:START'
END = '/* FNS:UIBASE:END */'
JS_START = '/* FNS:UIBASEJS:START'
JS_END = '/* FNS:UIBASEJS:END */'

# Every file that inlines the base. Repo-relative, forward slashes.
TARGETS = (
    'packaging/configurator/index.html',
    'modules/suspects/FNSTools/FNS_Console/console_page.html',
    # ColorUI runs standalone in its own Web Render (TitleBridge) as well as
    # framed under /t/ColorUI/, so it cannot rely on the console server's
    # /base.css and inlines its copy like the shells do.
    'modules/suspects/FNSTools/ColorUI/webui.html',
)

START_LINE = ('/* FNS:UIBASE:START -- generated from '
              'packaging/configurator/base.css; edit THERE, then run '
              'python packaging/configurator/sync_base.py --write */')
JS_START_LINE = ('/* FNS:UIBASEJS:START -- generated from '
                 'packaging/configurator/base.js; edit THERE, then run '
                 'python packaging/configurator/sync_base.py --write */')

# base.js: the behaviour both web shells share (tooltips). ColorUI does
# not carry it -- it has no hover text of its own.
JS_TARGETS = (
    'packaging/configurator/index.html',
    'modules/suspects/FNSTools/FNS_Console/console_page.html',
)

# (source file, start marker, end marker, generated start line, targets)
BLOCKS = (
    (BASE, START, END, START_LINE, TARGETS),
    (BASE_JS, JS_START, JS_END, JS_START_LINE, JS_TARGETS),
)


def _read(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read()


def _block(source, start_line, end):
    return '%s\n%s\n%s' % (start_line, _read(source).strip('\n'), end)


def _splice(text, path, source, start, end, start_line):
    a = text.find(start)
    b = text.find(end)
    if a < 0 or b < 0 or b < a:
        raise SystemExit('%s: %s markers missing or malformed -- '
                         'the shell cannot receive the shared base'
                         % (path, start.strip('/* ')))
    return text[:a] + _block(source, start_line, end) + text[b + len(end):]


def Sync(write=False):
    """Returns the list of targets that were (or would be) rewritten."""
    stale = []
    for source, start, end, start_line, targets in BLOCKS:
        for rel in targets:
            path = os.path.join(REPO, *rel.split('/'))
            if not os.path.exists(path):
                raise SystemExit('%s: missing -- a shell listed for %s does '
                                 'not exist' % (rel, os.path.basename(source)))
            text = _read(path)
            fresh = _splice(text, rel, source, start, end, start_line)
            if fresh != text:
                if rel not in stale:
                    stale.append(rel)
                if write:
                    with io.open(path, 'w', encoding='utf-8', newline='') as f:
                        f.write(fresh)
    return stale


if __name__ == '__main__':
    write = '--write' in sys.argv[1:]
    stale = Sync(write=write)
    if write:
        print('synced %d file(s): %s' % (len(stale), ', '.join(stale) or 'none stale'))
    elif stale:
        print('STALE base copies (run with --write): %s' % ', '.join(stale))
        sys.exit(1)
    else:
        print('all %d base copies current'
              % sum(len(t) for _, _, _, _, t in BLOCKS))
