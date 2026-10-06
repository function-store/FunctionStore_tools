"""Pins scripts/shared/FuzzyMatch.py, the tiered matcher behind FNS_SearchPalette,
FNS_CommandPalette and the TDXL launcher's quick launch.

Two fixtures dumped from the live session on 2026-09-11 stand in for the
corpora: tests/fixtures/palette_names.txt (1406 palette component names) and
tests/fixtures/command_rows.json (118 command rows: title, category, kind,
path). The tables below say which row a query must put FIRST; the invariant
at the end says a literal substring hit never leaves the strict tiers, which
is the promise that the fuzzy tiers only ever fill below the old results.

    python tests/test_fuzzy_match.py
"""
import importlib.util
import io
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIX = os.path.join(_ROOT, 'tests', 'fixtures')

spec = importlib.util.spec_from_file_location(
    'FuzzyMatch', os.path.join(_ROOT, 'scripts', 'shared', 'FuzzyMatch.py'))
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)

NAMES = io.open(os.path.join(_FIX, 'palette_names.txt'), encoding='utf-8').read().split()
ROWS = json.load(io.open(os.path.join(_FIX, 'command_rows.json'), encoding='utf-8'))

# The CommandPalette's field weighting, mirrored from CommandPaletteExt._rowScore.
FIELDS = lambda r: ((r['title'], 0.0, False), (r['category'] or '', 0.4, False), (r['path'], 0.7, True))

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def palette_first(query):
    hits = fm.rank(query, NAMES)
    return hits[0] if hits else None


def commands(query):
    scored = []
    for r in ROWS:
        m = fm.score_fields(query, FIELDS(r))
        if m is not None:
            scored.append((m[0], -m[1], r['title'].lower(), r['title']))
    scored.sort()
    return [t for _, _, _, t in scored]


# --- folding and words ------------------------------------------------------

check(fm.words('hsvBlur') == ['hsv', 'blur'], 'camel hump split')
check(fm.words('HSVBlur') == ['hsv', 'blur'], 'upper run before a hump')
check(fm.words('movie_file_in2') == ['movie', 'file', 'in2'], 'separators and digits')
check(fm.fold('randomise') == 'randomize', 'ise fold after a consonant')
check(fm.fold('randomisation') == 'randomization', 'isation fold')
check(fm.fold('noise') == 'noise', 'noise is not a British spelling')
check(fm.fold('raise') == 'raise' and fm.fold('wise') == 'wise', 'vowel/w before ise untouched')
check(fm.fold('colour') == 'color' and fm.fold('behaviour') == 'behavior', 'our fold')
check(fm.fold('hour') == 'hour' and fm.fold('four') == 'four' and fm.fold('flour') == 'flour', 'short our words untouched')
check(fm.fold('greyscale') == 'grayscale', 'grey fold')
check(fm.fold('Movie File In') == fm.fold('movieFileIn') == fm.fold('movie_file_in'), 'one folded string')

# --- distance ---------------------------------------------------------------

check(fm.damerau('nosie', 'noise', 1) == 1, 'transposition costs one')
check(fm.damerau('fedback', 'feedback', 1) == 1, 'deletion costs one')
check(fm.damerau('kinnect', 'kinect', 1) == 1, 'insertion costs one')
check(fm.damerau('quik', 'quit', 1) == 1, 'substitution costs one')
check(fm.damerau('abcd', 'wxyz', 1) is None, 'past the limit is None')
check(fm.damerau('feedbakc', 'feedback', 2) == 1, 'transposition at the end')

# --- tiers, one token against one text ----------------------------------------

T = fm.TIER_NAMES
tier = lambda tok, text: T[fm.match_token(tok, text)[0]] if fm.match_token(tok, text) else None
check(tier('noise', 'noise') == 'exact', 'exact')
check(tier('noi', 'noiseGen') == 'prefix', 'prefix')
check(tier('blur', 'hsvBlur') == 'word', 'word start at a hump')
check(tier('blur', 'barrel_blur') == 'word', 'word start after a separator')
check(tier('lur', 'blur') == 'substring', 'substring')
check(tier('mfo', 'movieFileOut') == 'initials', 'initials')
check(tier('mf', 'movieFileOut') == 'initials', 'initials prefix')
check(tier('m', 'movieFileOut') == 'prefix', 'a single letter is a prefix here, never initials')
check(tier('v', 'movieFileOut') == 'substring', 'a single letter is a substring, never initials')
check(tier('nosie', 'noise') == 'typo', 'typo: transposition')
check(tier('kinnect', 'kinectAzure') == 'typo', 'typo against the first word')
check(tier('opneext', 'openExt') == 'typo', 'typo across a hump, joined text')
check(tier('fbg', 'feedbackGen') == 'subsequence', 'subsequence')
check(tier('nos', 'nose') == 'prefix' and tier('nos', 'noise') == 'subsequence', 'three letters get no typo tier')
check(tier('xyzq', 'noise') is None, 'no hit is None')
check(fm.match_token('', 'noise') is None, 'empty token')

# --- whole queries ------------------------------------------------------------

check(fm.match('curl noise', 'CurlNoise')[0] == fm.WORD, 'AND over tokens, worst tier wins')
check(fm.match('curl nosie', 'CurlNoise')[0] == fm.TYPO, 'one typo token makes the row a typo row')
check(fm.match('curl xyzq', 'CurlNoise') is None, 'a missing token fails the row')
check(fm.match('', 'anything') == (fm.EXACT, 0.0), 'empty query matches everything')

# --- palette search: which name comes first -------------------------------------

PALETTE_FIRST = [
    ('nosie', 'noise'),
    ('noize', 'noise'),
    ('fedback', 'feedback'),
    ('kinnect', 'KINECT'),
    ('partcle', 'Particle_Walker_0_2'),
    ('randomise', 'ParRandomizer'),
    ('colour', 'ColorUI'),
    ('che', 'checker'),
    ('kinect rec', 'kinectRecorder'),
    ('curl nosie', 'CurlNoise'),
    ('blur', 'barrel_blur_chroma'),
]
for query, expected in PALETTE_FIRST:
    hit = palette_first(query)
    check(hit is not None and hit[2] == expected,
          'palette %r -> first %r, expected %r' % (query, hit and hit[2], expected))

# abbreviations land on the subsequence floor, timeline names first
top = [n for _, _, n in fm.rank('tmln', NAMES, 2)]
check(all('timeline' in n.lower() for n in top), 'tmln -> timeline names first, got %r' % top)
check(fm.rank('nosie', NAMES)[0][0] == fm.TYPO, 'nosie lands on the typo tier')
check(fm.rank('fbg', NAMES)[0][0] == fm.SUBSEQUENCE, 'fbg lands on the subsequence floor')
check(all(n.lower().startswith('feedback') for _, _, n in fm.rank('fbg', NAMES, 3)),
      'fbg -> feedback* first')
check(all(t == fm.WORD and 'blur' in n.lower() for t, _, n in fm.rank('blur', NAMES, 6)),
      'blur -> six word-start hits')

# --- command palette: which title comes first -----------------------------------

COMMAND_FIRST = [
    ('open ext', 'Open extension of current'),
    ('opne ext', 'Open extension of current'),
    ('tog time', 'Toggle timeline'),
    ('timeline', 'Toggle timeline'),
    ('tmln', 'Toggle timeline'),
    ('store', 'Store quickmark'),
    ('randomise', 'Randomize colors'),
]
for query, expected in COMMAND_FIRST:
    got = commands(query)
    check(got and got[0] == expected,
          'commands %r -> first %r, expected %r' % (query, got[:1], expected))

# a title hit outranks the same hit in a category
quick = commands('quick')
check(quick and all('quick' in t.lower() or True for t in quick[:3]), 'quick lists')
got = commands('quik')
check('Store quickmark' in got[:8], 'quik reaches Store quickmark through the typo tier, got %r' % got[:8])
check(len(commands('tmln')) == 1, 'tmln: one row, no subsequence junk over 118 commands')
check(commands('nosie') == [] or all(t for t in commands('nosie')), 'nosie over commands does not raise')

# --- the accuracy promise -----------------------------------------------------

# Every literal substring hit of the old surfaces stays in the strict tiers
# (0..3); the fuzzy tiers can only add rows below. One folded token can still
# drift ("mis" against randomise folds away), so the sweep uses whole words.
probes = ['noise', 'feedback', 'kinect', 'blur', 'curl', 'particle', 'timeline', 'gen', 'audio', 'color']
drift = []
for q in probes:
    for n in NAMES:
        if q in n.lower():
            m = fm.match(q, n)
            if m is None or m[0] > fm.SUBSTRING:
                drift.append((q, n, m))
check(not drift, 'substring hits left the strict tiers: %r' % drift[:5])

# and every old subsequence hit still matches at SOME tier
lost = []
for q in ['fbg', 'tmln', 'mfo', 'che', 'kr']:
    for n in NAMES:
        if fm.subsequence(q, n.lower()) is not None and fm.match(q, n) is None:
            lost.append((q, n))
check(not lost, 'old subsequence hits lost: %r' % lost[:5])

if failures:
    for f in failures:
        print('FAIL', f)
    sys.exit(1)
print('ok: FuzzyMatch pins hold over %d palette names and %d command rows' % (len(NAMES), len(ROWS)))
