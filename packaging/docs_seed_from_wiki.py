"""ONE-SHOT migration: GitHub wiki -> packaging/docs/<Package>.md.

This is a migration, not a pipeline. Run it once, review the output, commit
it, then freeze the wiki. Nothing regenerates from the wiki afterwards --
`packaging/docs/` becomes the source of truth, the same way `catalog.json`
is already the source of truth for category and description.

The wiki is organised by *where a tool appears in the UI* (toolbar, op
menu, nav bar); the catalog is organised by *what ships as a package*.
Those two shapes do not line up, so the mapping is the explicit ROUTES
table below rather than anything inferred. Every routing decision in it
was checked by hand against `modules/suspects/FunctionStore_tools_2025/`
-- e.g. QuickExt and CustomParCustomize land in CustomParTools because
`CustomParTools.tox` is what actually carries them, and ResetMIDIPls
lands in midiMapper because `midiMapper/MIDIResetPLS.tox` does.

Sections with no sensible package, and packages with no wiki content, are
both REPORTED rather than guessed at. Stubs are written for the latter so
every catalog package has a file; they carry a TODO and the catalog
description, and are meant to be written by hand.

Usage:
    python3 packaging/docs_seed_from_wiki.py [--wiki PATH] [--force]

Without --wiki the wiki is cloned to a temp dir. --force overwrites
existing files in packaging/docs/ (default: refuses, so a second run
cannot clobber hand-edits).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOCS_DIR = os.path.join(HERE, 'docs')
CATALOG = os.path.join(HERE, 'catalog.json')
WIKI_URL = 'https://github.com/function-store/FunctionStore_tools.wiki.git'

# Wiki page order, and the order sections are concatenated per package.
PAGES = ['01.-OpTemplates.md', '02.-FNS_Toolbar.md', '03.-Miscellaneous.md',
         '04.-QuickExt.md', 'Home.md']

# (page, normalised heading text) -> package name.
#
# Normalised means: inline icon image stripped, whitespace collapsed,
# lowercased. A heading routes its own prose plus every subsection under
# it, unless a subsection has its own entry here (then it splits off).
ROUTES = {
    # ---- 01. OpTemplates: the whole page is one package ----
    ('01.-OpTemplates.md', 'optemplates'): 'OpTemplates',

    # ---- 02. FNS_Toolbar ----
    # The page preamble (how the bar installs, ToolbarDef ordering) is the
    # FNS_Toolbar package itself; the buttons on it are other packages.
    ('02.-FNS_Toolbar.md', '__preamble__'): 'FNS_Toolbar',
    ('02.-FNS_Toolbar.md', 'wiki'): 'FNS_Updater',
    ('02.-FNS_Toolbar.md', 'tools_ui'): 'tools_ui',
    ('02.-FNS_Toolbar.md', 'op_store'): 'tools_ui',
    ('02.-FNS_Toolbar.md', 'globaloutselect'): 'GlobalOutSelect',
    ('02.-FNS_Toolbar.md', 'exprhotstrings'): 'ExprHotStrings',
    ('02.-FNS_Toolbar.md', 'midimapper'): 'midiMapper',
    ('02.-FNS_Toolbar.md', 'resetmidipls'): 'midiMapper',
    ('02.-FNS_Toolbar.md', 'oscmapper'): 'oscMapper',
    ('02.-FNS_Toolbar.md', 'custom opmenu search keywords'): 'FNS_OpMenu',
    ('02.-FNS_Toolbar.md', 'colorui'): 'ColorUI',
    # Olib_Browser1.tox ships inside the tools_ui panel, not standalone.
    ('02.-FNS_Toolbar.md', 'olib browser'): 'tools_ui',
    ('02.-FNS_Toolbar.md', 'open templates'): 'OpTemplates',
    ('02.-FNS_Toolbar.md', 'perform window tools'): 'OUTPUT',
    ('02.-FNS_Toolbar.md', 'vscode tools'): 'VSCodeTools',
    ('02.-FNS_Toolbar.md', 'global resetpls'): 'ResetPLS1',
    ('02.-FNS_Toolbar.md', 'swap ops'): 'SwapOps',
    ('02.-FNS_Toolbar.md', 'set input/viewer smoothness'): 'SetSmoothness',
    ('02.-FNS_Toolbar.md', 'parrandomizer'): 'ParRandomizer',
    # catalog: "Assorted small utilities that ship together (hog CHOP,
    # mouse input and friends)" -- the friends are these four.
    ('02.-FNS_Toolbar.md', 'show/hide backdrops'): 'MISC',
    ('02.-FNS_Toolbar.md', 'show/hide network editor grid'): 'MISC',
    ('02.-FNS_Toolbar.md', 'global hog chop'): 'MISC',
    ('02.-FNS_Toolbar.md', 'global mouse chop'): 'MISC',
    ('02.-FNS_Toolbar.md', 'quicktime'): 'QuickTime',
    ('02.-FNS_Toolbar.md', 'mute and volume'): 'GlobalVolControl',
    # The Mapper button drives both mappers; midiMapper is the primary and
    # cross-links to oscMapper.
    ('02.-FNS_Toolbar.md', 'mapper'): 'midiMapper',
    ('02.-FNS_Toolbar.md', 'paropdrop'): 'ParOPDrop',
    ('02.-FNS_Toolbar.md', 'custompar tools'): 'CustomParTools',
    ('02.-FNS_Toolbar.md', 'hydrohomie'): 'HydroHomie',
    ('02.-FNS_Toolbar.md', 'quickext'): 'CustomParTools',

    # ---- 03. Miscellaneous ----
    ('03.-Miscellaneous.md', 'opmenu mods'): 'FNS_OpMenu',
    ('03.-Miscellaneous.md', 'optemplates'): 'OpTemplates',
    ("03.-Miscellaneous.md", "greg's io filters"): 'FNS_OpMenu',
    ('03.-Miscellaneous.md', 'custom search keywords'): 'FNS_OpMenu',
    ("03.-Miscellaneous.md", "dotsimulate's optype acronyms"): 'FNS_OpMenu',
    # No QuickOp package exists in the 2025 tree; the behaviour is a mod of
    # the OP Create dialog, which is what FNS_OpMenu ships.
    ('03.-Miscellaneous.md', 'quickop'): 'FNS_OpMenu',
    ('03.-Miscellaneous.md', 'navbar mods'): 'FNS_Navbar',
    ('03.-Miscellaneous.md', 'path bar mods'): 'FNS_Navbar',
    ('03.-Miscellaneous.md', 'parent hierarchy'): 'FNS_Navbar',
    ('03.-Miscellaneous.md', 'hotkeys'): 'MY_HOTKEYS',
    ('03.-Miscellaneous.md', 'td_searchpalette'): 'MY_HOTKEYS',
    ('03.-Miscellaneous.md', 'altselect'): 'AltSelect',
    ('03.-Miscellaneous.md', 'autocombine'): 'AutoCombine',
    ('03.-Miscellaneous.md', 'autores'): 'AutoRes',
    ('03.-Miscellaneous.md', 'quickpane'): 'QuickPane',
    ('03.-Miscellaneous.md', 'switchops'): 'SwitchOPs',
    ('03.-Miscellaneous.md', 'optoclipboard'): 'OpToClipboard',
    ('03.-Miscellaneous.md', 'openext'): 'OpenExt',
    ('03.-Miscellaneous.md', 'quickcollapse'): 'QuickCollapse',
    ('03.-Miscellaneous.md', 'clipboard image paste'): 'paste_from_clipboard',
    ('03.-Miscellaneous.md', 'quickmarks'): 'QuickMarks',
    ('03.-Miscellaneous.md', 'customparcustomize'): 'CustomParTools',
    ('03.-Miscellaneous.md', 'borderlesstd'): 'BorderlessTD',
    ('03.-Miscellaneous.md', 'colorui'): 'ColorUI',
    ('03.-Miscellaneous.md', 'resetmidipls'): 'midiMapper',
    ('03.-Miscellaneous.md', 'hotkeymanager'): 'FNS_HotkeyManager',
    ('03.-Miscellaneous.md', 'quickparcustom'): 'QuickParCustom',

    # ---- 04. QuickExt: ships inside CustomParTools.tox ----
    ('04.-QuickExt.md', 'quickext'): 'CustomParTools',
    ('04.-QuickExt.md', '__preamble__'): 'CustomParTools',
    ('04.-QuickExt.md', 'customparhelper'): 'CustomParTools',
    ('04.-QuickExt.md', 'nonode'): 'CustomParTools',

    # ---- Home: mostly landing-page material, two real tool sections ----
    ('Home.md', 'self-update feature'): 'FNS_Updater',
    ('Home.md', 'syncing/externalizing'): 'ConfigRegistry',
    ('Home.md', 'custom parameters'): 'ConfigRegistry',
}

# Home sections that are landing-page copy, not tool docs. Listed so the
# report can distinguish "deliberately not routed" from "forgotten".
LANDING_ONLY = {
    ('Home.md', '__preamble__'), ('Home.md', 'installation'),
    ('Home.md', 'mac compatibility'), ('Home.md', 'repo structure'),
    ('Home.md', 'acknowledgements'), ('Home.md', 'functionstore_tools'),
    ('Home.md', 'notable mentions'), ('Home.md', 'license'),
    ('Home.md', '[read the wiki](https://github.com/function-store/'
                'functionstore_tools/wiki)'),
    ('03.-Miscellaneous.md', '__preamble__'),
}

# Per-package extras that cannot be derived from the wiki text.
CREDITS = {
    'tools_ui': ('AlphaMoonbase.berlin', 'https://alphamoonbase.de/'),
    'midiMapper': ('AlphaMoonbase.berlin', 'https://alphamoonbase.de/'),
    'oscMapper': ('AlphaMoonbase.berlin', 'https://alphamoonbase.de/'),
    'QuickMarks': ('Alex Guevara', 'https://alex-guevara.com'),
    'paste_from_clipboard': ('DotSimulate', 'https://www.patreon.com/dotsimulate'),
}
VIDEOS = {
    'ExprHotStrings': 'https://www.youtube.com/watch?v=j43gZ0MB2xo',
}
# Everything ships on both unless listed here. Olib Browser (inside
# tools_ui) and Clipboard Image Paste are Windows-only per the wiki.
PLATFORMS = {
    'paste_from_clipboard': ['windows'],
}

# The wiki embeds this with an expired JWT (exp ~Jul 2024); it is already
# a dead link on github.com. Dropped, with a TODO left in the body.
DEAD_IMAGE = 'private-user-images.githubusercontent.com'

ICON_RE = re.compile(
    r'!\[[^\]]*\]\(https://github\.com/function-store/FunctionStore_tools/'
    r'blob/main/icons/([^)]+)\)')
BLOB_IMG_RE = re.compile(
    r'(!\[[^\]]*\]\()https://github\.com/function-store/FunctionStore_tools/'
    r'blob/main/([^)]+)(\))')
WIKI_LINK_RE = re.compile(
    r'\(https://github\.com/function-store/FunctionStore_tools/wiki/'
    r'([0-9A-Za-z._-]+)(#[^)\s]*)?\)')
# The wiki's own broken anchors, fixed on the way through. Left-hand side
# is what Home.md links to; right-hand side is the heading that exists.
ANCHOR_FIXES = {
    '#-custompar-tools': '#quicktime',      # Home links QuickTime here
    '#global-resetpls': '#global-resetpls',
    '#opmenu-mod': '#opmenu-mods',
}
# Hotkey bullets: "- `Ctrl+0`: reset everything" / "* `Alt+V` - paste".
HOTKEY_RE = re.compile(r'^\s*[-*]\s+`([^`]{2,40})`\s*[:–—-]\s+(.+)$')


def slugify(text):
    """Anchor slug. Must stay identical to slugify() in build-site.mjs."""
    text = ICON_RE.sub('', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)     # any other image
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)  # link -> its text
    text = text.replace('`', '').lower().strip()
    text = re.sub(r'[^a-z0-9\s_-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-{2,}', '-', text).strip('-')


def package_slug(name):
    """URL slug for a package. Must match _helpUrl() in build_manifest.py."""
    return name.lower().replace('_', '-')


def clone_wiki(dest):
    subprocess.run(['git', 'clone', '--depth', '1', WIKI_URL, dest],
                   check=True, capture_output=True)
    return dest


class Section(object):
    def __init__(self, page, level, heading, line):
        self.page = page
        self.level = level
        self.heading = heading          # raw, icon still attached
        self.line = line
        self.body = []
        self.children = []
        # Level of the ancestor that owns this section's routing decision.
        # Sections split off at different wiki depths (midiMapper was an
        # h3 under tools_ui, Mapper an h2) but each becomes an h2 here.
        self.root_level = level

    @property
    def title(self):
        return ICON_RE.sub('', self.heading).strip()

    @property
    def key(self):
        return (self.page, ' '.join(self.title.lower().split()))

    @property
    def icon(self):
        m = ICON_RE.search(self.heading)
        return m.group(1).replace('%20', ' ') if m else None


def parse_page(page, text):
    """Flat list of top-level sections; subsections nest under them."""
    root = Section(page, 0, '__preamble__', 0)
    stack = [root]
    out = [root]
    for i, line in enumerate(text.splitlines()):
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if not m:
            stack[-1].body.append(line)
            continue
        level, heading = len(m.group(1)), m.group(2).strip()
        sec = Section(page, level, heading, i + 1)
        while len(stack) > 1 and stack[-1].level >= level:
            stack.pop()
        stack[-1].children.append(sec)
        stack.append(sec)
        out.append(sec)
    return root, out


def route(sec):
    """Package for a section, or None. Inherited from the nearest routed
    ancestor unless the section has its own entry."""
    return ROUTES.get(sec.key)


def collect(root, page, assigned, unrouted):
    """Walk the tree, assigning each section to a package. A subsection
    with its own ROUTES entry splits off from its parent."""
    def walk(sec, inherited, root_level):
        own = route(sec)
        pkg = own or inherited
        if own is not None:
            root_level = sec.level
        sec.root_level = root_level
        if pkg:
            assigned.setdefault(pkg, []).append(sec)
        elif sec.key not in LANDING_ONLY and (sec.body or sec.children):
            if any(ln.strip() for ln in sec.body):
                unrouted.append(sec)
        for child in sec.children:
            walk(child, pkg, root_level)
    walk(root, None, 1)


def clean_body(lines, page, pkg_of_page_section):
    """Fix the four known content defects on the way through."""
    out, notes = [], []
    for line in lines:
        if DEAD_IMAGE in line:
            notes.append('dead-image')
            out.append('<!-- TODO: screenshot lost (expired GitHub JWT, '
                       '~Jul 2024) -- re-capture and add here. -->')
            continue
        # /blob/ image URLs only render on github.com; point at local assets.
        line = BLOB_IMG_RE.sub(
            lambda m: m.group(1) + '/docs/assets/' + m.group(2) + m.group(3),
            line)

        def _wikilink(m):
            target, anchor = m.group(1), m.group(2) or ''
            anchor = ANCHOR_FIXES.get(anchor, anchor)
            if anchor:
                anchor = '#' + slugify(anchor[1:])
            pkg = pkg_of_page_section(target + '.md', anchor)
            return '(%s%s)' % (pkg, anchor) if pkg else '(%s)' % (anchor or '/docs/')
        line = WIKI_LINK_RE.sub(_wikilink, line)
        out.append(line)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out, notes


def extract_hotkeys(lines):
    keys = []
    for line in lines:
        m = HOTKEY_RE.match(line)
        if not m:
            continue
        combo, does = m.group(1).strip(), m.group(2).strip()
        # Only accept things that actually look like key combos.
        if not re.search(r'(?i)\b(ctrl|alt|shift|cmd|option|f\d|tab|enter)\b',
                         combo):
            continue
        does = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', does)
        does = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', does).strip()
        keys.append({'keys': combo, 'does': does[:120]})
    return keys


def first_sentence(lines):
    for line in lines:
        s = line.strip()
        if not s or s.startswith(('#', '>', '-', '*', '!', '|', '<', '```')):
            continue
        s = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', s)
        s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
        s = re.sub(r'[*_`]', '', s).strip()
        if len(s) < 15:
            continue
        m = re.match(r'^(.{15,200}?[.!?])(\s|$)', s)
        return (m.group(1) if m else s[:200]).strip()
    return ''


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def dedupe(sections):
    """The wiki documents a few tools twice (ResetMIDIPls appears under
    both midiMapper and Miscellaneous). Same slug within one package =
    same tool; keep whichever copy carries more prose."""
    best, order = {}, []
    for sec in sections:
        if sec.heading == '__preamble__':
            order.append(sec)
            continue
        slug = slugify(sec.title)
        weight = sum(len(ln.strip()) for ln in sec.body)
        if slug not in best:
            best[slug] = (weight, sec)
            order.append(sec)
        elif weight > best[slug][0]:
            prev = best[slug][1]
            order[order.index(prev)] = sec
            best[slug] = (weight, sec)
    return order


def render(pkg, meta, sections, page_index, pkg_of_page_section):
    features, body, notes = [], [], []
    sections = dedupe(sections)
    for sec in sections:
        if sec.heading == '__preamble__':
            lines, n = clean_body(sec.body, sec.page, pkg_of_page_section)
            notes += n
            if lines:
                body.append('\n'.join(lines))
            continue
        title, anchor = sec.title, slugify(sec.title)
        depth = max(2, min(2 + sec.level - sec.root_level, 5))
        lines, n = clean_body(sec.body, sec.page, pkg_of_page_section)
        notes += n
        body.append('%s %s\n\n%s' % ('#' * depth, title, '\n'.join(lines)))
        if depth == 2:
            entry = {'name': title, 'anchor': anchor}
            if sec.icon:
                entry['icon'] = sec.icon
            hk = extract_hotkeys(sec.body)
            if hk:
                entry['hotkeys'] = hk
            features.append(entry)

    summary = first_sentence(sum([s.body for s in sections], []))
    fm = ['---', 'package: %s' % yaml_str(pkg)]
    fm.append('summary: %s' % yaml_str(summary or meta.get('description', '')))
    if features:
        fm.append('features:')
        for f in features:
            fm.append('  - name: %s' % yaml_str(f['name']))
            fm.append('    anchor: %s' % yaml_str(f['anchor']))
            if 'icon' in f:
                fm.append('    icon: %s' % yaml_str(f['icon']))
            if f.get('hotkeys'):
                fm.append('    hotkeys:')
                for hk in f['hotkeys']:
                    fm.append('      - {keys: %s, does: %s}'
                              % (yaml_str(hk['keys']), yaml_str(hk['does'])))
    if pkg in PLATFORMS:
        fm.append('platforms: [%s]' % ', '.join(PLATFORMS[pkg]))
    if pkg in CREDITS:
        name, url = CREDITS[pkg]
        fm.append('credit: {name: %s, url: %s}' % (yaml_str(name), yaml_str(url)))
    if pkg in VIDEOS:
        fm.append('video: %s' % yaml_str(VIDEOS[pkg]))
    fm.append('---')
    return '\n'.join(fm) + '\n\n' + '\n\n'.join(b for b in body if b.strip()) + '\n', notes


def render_stub(pkg, meta):
    return ('---\n'
            'package: %s\n'
            'summary: %s\n'
            '---\n\n'
            '<!-- TODO: no wiki content existed for this package. Written\n'
            '     from the catalog description only -- please expand. -->\n\n'
            '%s\n' % (yaml_str(pkg), yaml_str(meta.get('description', '')),
                      meta.get('description', '')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wiki', help='existing wiki checkout (else cloned)')
    ap.add_argument('--force', action='store_true',
                    help='overwrite packaging/docs/ (default: refuse)')
    args = ap.parse_args()

    with open(CATALOG, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    packages = catalog['packages']

    if os.path.isdir(DOCS_DIR) and os.listdir(DOCS_DIR) and not args.force:
        sys.exit('packaging/docs/ is not empty. This is a one-shot seeder; '
                 'pass --force only if you mean to discard hand-edits.')

    tmp = None
    wiki = args.wiki
    if not wiki:
        tmp = tempfile.mkdtemp(prefix='fnstools-wiki-')
        wiki = clone_wiki(os.path.join(tmp, 'wiki'))

    try:
        assigned, unrouted, page_index = {}, [], {}
        for page in PAGES:
            path = os.path.join(wiki, page)
            if not os.path.exists(path):
                sys.exit('missing wiki page: %s' % page)
            with open(path, 'r', encoding='utf-8') as f:
                root, flat = parse_page(page, f.read())
            page_index[page] = flat
            collect(root, page, assigned, unrouted)

        # page+anchor -> "/docs/<slug>/#anchor", for rewriting wiki links.
        anchor_owner = {}
        for pkg, secs in assigned.items():
            for sec in secs:
                anchor_owner[(sec.page, '#' + slugify(sec.title))] = pkg
                anchor_owner.setdefault((sec.page, ''), pkg)

        def pkg_of_page_section(page, anchor):
            pkg = anchor_owner.get((page, anchor)) or anchor_owner.get((page, ''))
            return '/docs/%s/' % package_slug(pkg) if pkg else None

        os.makedirs(DOCS_DIR, exist_ok=True)
        written, stubs, all_notes = [], [], {}
        for pkg in sorted(packages, key=str.lower):
            meta = packages[pkg]
            path = os.path.join(DOCS_DIR, '%s.md' % pkg)
            if pkg in assigned:
                text, notes = render(pkg, meta, assigned[pkg], page_index,
                                     pkg_of_page_section)
                if notes:
                    all_notes[pkg] = notes
                written.append(pkg)
            else:
                text = render_stub(pkg, meta)
                stubs.append(pkg)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)

        bad = sorted(set(assigned) - set(packages))

        print('seeded %d/%d packages from the wiki, %d stubs written'
              % (len(written), len(packages), len(stubs)))
        if bad:
            print('\nROUTED TO UNKNOWN PACKAGES (fix ROUTES):')
            for p in bad:
                print('  %s' % p)
        if stubs:
            print('\nSTUBS -- no wiki content existed, need writing by hand:')
            for p in stubs:
                print('  %-20s %s' % (p, packages[p]['category']))
        if unrouted:
            print('\nUNROUTED wiki sections (not landing-page copy):')
            for s in unrouted:
                print('  %-22s %s:%d  %s' % (s.page.replace('.md', ''),
                                             '', s.line, s.title))
        if all_notes:
            print('\nCONTENT FIXES APPLIED:')
            for p, n in sorted(all_notes.items()):
                print('  %-20s %s' % (p, ', '.join(sorted(set(n)))))
        print('\nNow review packaging/docs/*.md by hand -- the wiki register '
              'is casual reference prose and some catalog descriptions '
              'disagree with it.')
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
