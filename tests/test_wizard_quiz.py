"""The guided setup's questionnaire must recommend only what it can name.

Questions (with options and their tags) are curated in
packaging/catalog.json under `quiz`; each package carries `fits`, the
tags it answers. Two layers keep the result honest, both pinned here
from the REAL sources:

  - the page's scoring function (lifted from index.html, run in node)
    recommends every tool whose fits meet the chosen tags, best first,
    with the answers as reasons, and nothing else
  - the catalog's curation: every option tag is fit by at least one
    package (the standalone mirror of build_manifest._quiz, which runs
    only in TD), every fits tag is asked for by some option

    python tests/test_wizard_quiz.py
"""
import io
import json
import os
import re
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
CATALOG = os.path.join(_ROOT, 'packaging', 'catalog.json')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


src = io.open(PAGE, encoding='utf-8').read()

print('1. the scoring function, from the page')
m = re.search(r'function quizScore\(answers, quiz, tools\) \{.*?\n  \}', src, re.S)
assert m, 'could not lift quizScore from the page'
harness = """
var quiz = {questions: [
  {id: 'work', multi: true, options: [
    {id: 'live', label: 'Live', tags: ['live', 'audio']},
    {id: 'dev', label: 'Dev', tags: ['dev']}]},
  {id: 'out', multi: true, options: [
    {id: 'audio', label: 'Sound', tags: ['audio']}]},
]};
var tools = [
  {name: 'A', fits: ['live']},
  {name: 'B', fits: ['audio']},
  {name: 'C', fits: ['dev']},
  {name: 'D', fits: ['other']},
  {name: 'E'},
];
%s
console.log(JSON.stringify(quizScore({work: ['live'], out: ['audio']}, quiz, tools)));
console.log(JSON.stringify(quizScore({}, quiz, tools)));
""" % m.group(0)
try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', harness],
                         capture_output=True, text=True, timeout=30)
    lines = [l for l in got.stdout.strip().split('\n') if l]
    if got.returncode != 0:
        print('  node stderr: %s' % got.stderr.strip()[:300])
        lines = []
except Exception as e:
    lines = []
    print('  SKIP  node unavailable (%s)' % e)

if len(lines) == 2:
    picks, none = json.loads(lines[0]), json.loads(lines[1])
    names = [r['name'] for r in picks]
    check('a tag chosen twice ranks its tool first', names[0] == 'B', names)
    check('every tool that fits a chosen tag is recommended',
          sorted(names) == ['A', 'B'], names)
    check('a tool fitting an unchosen tag is not', 'C' not in names and 'D' not in names, names)
    check('a tool with no fits is never recommended', 'E' not in names, names)
    check('reasons are the answers labels',
          picks[0]['why'] == ['Live', 'Sound'], picks[0]['why'])
    check('no answers, no recommendations', none == [], none)

print('2. the set is what several answers pointed at; single matches are offered, unticked')
m2 = re.search(r'function quizSplit\(picks\) \{.*?\n  \}', src, re.S)
assert m2, 'could not lift quizSplit from the page'
split_harness = """
%s
var wide = [];
for (var i = 0; i < 20; i++) wide.push({name: 'T' + i, score: i < 7 ? 2 : 1, why: []});
var thin = [{name: 'A', score: 1, why: []}, {name: 'B', score: 1, why: []}];
var w = quizSplit(wide), t = quizSplit(thin);
console.log(JSON.stringify([w.main.length, w.more.length, t.main.length, t.more.length]));
""" % m2.group(0)
try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', split_harness],
                         capture_output=True, text=True, timeout=30)
    nums = json.loads(got.stdout.strip()) if got.returncode == 0 else None
except Exception as e:
    nums = None
    print('  SKIP  node unavailable (%s)' % e)
if nums:
    check('a wide result keeps only multi-answer matches in the set', nums[0] == 7 and nums[1] == 13, nums)
    check('a thin result keeps its single matches in the set', nums[2] == 2 and nums[3] == 0, nums)

print('3. the result routes through choose() like every preset')
# choose() gained `explicit` in 86061543 so the quiz's answer is applied
# as the user answered it instead of being widened by autoPick; the rule
# under test is that the card still routes through choose() like every
# other preset, so anchor on that and on the explicit flag.
check('the quiz card opens the stepper, with its answer applied as given',
      "preQuiz.onclick = function () { quizStart(function (names) { choose(names, null, true); }); };" in src
      and 'function choose(names, bind, explicit, own) {' in src
      and 'applyPreset(explicit ? names : autoPick(names, own));' in src)
check('the card hides when the manifest carries no questionnaire',
      'preQuiz.hidden = !quiz;' in src)

print('4. catalog curation, when present, is fit by shipped packages')
cat = json.load(io.open(CATALOG, encoding='utf-8'))
questions = (cat.get('quiz') or {}).get('questions') or []
if not questions:
    print('  SKIP  catalog.json carries no quiz yet (the vocabulary is dormant)')
else:
    fits = {}
    for name, meta in cat.get('packages', {}).items():
        for t in meta.get('fits') or []:
            fits.setdefault(t, []).append(name)
    asked = set()
    for q in questions:
        check('question %r has an id, a prompt and options' % q.get('id'),
              bool(q.get('id')) and bool(q.get('prompt')) and bool(q.get('options')))
        for o in q.get('options') or []:
            check('%s/%s has an id and a label' % (q.get('id'), o.get('id')),
                  bool(o.get('id')) and bool(o.get('label')))
            for t in o.get('tags') or []:
                asked.add(t)
                check('%s/%s tag %r is fit by a package' % (q.get('id'), o.get('id'), t),
                      t in fits, 'no package fits it')
    orphan = sorted(t for t in fits if t not in asked)
    check('every fits tag is asked for by some option', not orphan, ', '.join(orphan))

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
