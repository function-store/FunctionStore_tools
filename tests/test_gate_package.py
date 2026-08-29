"""Offline test of the gate_package authoring command.

Runs against a TEMP copy of the two files it edits -- catalog.json and
wrangler.toml -- and asserts the whole authoring contract: both files
move together, placeholder scaffolding is dropped as real values land,
display names are refused where an ID belongs, and the result is exactly
what publish.Stage()'s entitlement guard will accept.

    python tests/test_gate_package.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        print('  FAIL  %s %s' % (label, detail))
        FAILS.append(label)


tmp = tempfile.mkdtemp(prefix='fns_gate_')
cat_path = os.path.join(tmp, 'catalog.json')
toml_path = os.path.join(tmp, 'wrangler.toml')
with open(cat_path, 'w', encoding='utf-8') as f:
    json.dump({'packages': {
        'PaidTool': {'category': 'X', 'description': 'd',
                     'access': 'PLACEHOLDER_TIER', 'license': '', 'seats': None},
        'FreeTool': {'category': 'X', 'description': 'd'},
    }}, f)
with open(toml_path, 'w', encoding='utf-8') as f:
    f.write('name = "gate"\n\nTIERS = """\n'
            '{\n  "REPLACE_WITH_TIER_ID": ["PaidTool"]\n}\n"""\n\n'
            'GUMROAD_PRODUCTS = """\n'
            '{\n  "REPLACE_WITH_GUMROAD_PRODUCT_ID": "PaidTool"\n}\n"""\n')

spec = importlib.util.spec_from_file_location(
    'gate_package', os.path.join(_ROOT, 'packaging', 'gate_package.py'))
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)
gp.CATALOG, gp.WRANGLER = cat_path, toml_path

print('1. placeholder state is reported as not authorizable')
check('status exits 1 on placeholders', gp.Status() == 1)

print('2. a display name where the ID belongs is refused')
try:
    gp.Gate('PaidTool', tier='Supporter Tier')
    check('name refused', False, '(accepted a display name)')
except SystemExit as e:
    check('name refused, message teaches the ID rule',
          'NUMERIC' in str(e), str(e)[:90])

print('3. gating by ID writes BOTH files and drops the scaffolding')
rc = gp.Gate('PaidTool', tier='9999')
cat = json.load(open(cat_path, encoding='utf-8'))
toml = open(toml_path, encoding='utf-8').read()
tiers = json.loads(toml.split('TIERS = """')[1].split('"""')[0])
gum = json.loads(toml.split('GUMROAD_PRODUCTS = """')[1].split('"""')[0])
check('catalog access = the id', cat['packages']['PaidTool']['access'] == '9999')
check('TIERS grants it', tiers.get('9999') == ['PaidTool'], tiers)
check('placeholder tier row dropped', 'REPLACE_WITH_TIER_ID' not in tiers)
check('placeholder gumroad row dropped', not gum, gum)
check('status now clean (Stage would accept)', rc == 0)

print('4. adding a Gumroad key keeps the tier grant')
gp.Gate('PaidTool', tier='9999', gumroad_id='prod_abc')
toml = open(toml_path, encoding='utf-8').read()
gum = json.loads(toml.split('GUMROAD_PRODUCTS = """')[1].split('"""')[0])
tiers = json.loads(toml.split('TIERS = """')[1].split('"""')[0])
check('gumroad row written', gum.get('prod_abc') == 'PaidTool', gum)
check('tier grant intact, not duplicated', tiers.get('9999') == ['PaidTool'])

print('5. --free removes every grant and the access field')
gp.Free('PaidTool')
cat = json.load(open(cat_path, encoding='utf-8'))
toml = open(toml_path, encoding='utf-8').read()
tiers = json.loads(toml.split('TIERS = """')[1].split('"""')[0])
gum = json.loads(toml.split('GUMROAD_PRODUCTS = """')[1].split('"""')[0])
check('access removed', 'access' not in cat['packages']['PaidTool'])
check('license/seats untouched (hand-curated)',
      cat['packages']['PaidTool'].get('license') == ''
      and cat['packages']['PaidTool'].get('seats') is None)
check('no grants left', not tiers and not gum, (tiers, gum))

print('6. --tier is the ENTRY tier: every tier above it is granted too')
base, pro, coach = (t for t, _ in gp.TIER_LADDER)
check('ladder expands upward from Base', gp.LadderFrom(base) == [base, pro, coach],
      gp.LadderFrom(base))
check('  from Pro, Base is NOT included', gp.LadderFrom(pro) == [pro, coach],
      gp.LadderFrom(pro))
check('  the top tier grants only itself', gp.LadderFrom(coach) == [coach],
      gp.LadderFrom(coach))
check('  an id outside the ladder grants only itself',
      gp.LadderFrom('55555') == ['55555'])

gp.Gate('PaidTool', tier=pro)
cat = json.load(open(cat_path, encoding='utf-8'))
toml = open(toml_path, encoding='utf-8').read()
tiers = json.loads(toml.split('TIERS = \"\"\"')[1].split('\"\"\"')[0])
check('access records the ENTRY tier, not the expansion',
      cat['packages']['PaidTool'].get('access') == pro,
      cat['packages']['PaidTool'].get('access'))
check('Pro grants it', 'PaidTool' in tiers.get(pro, []), tiers)
check('Coaching grants it too -- nobody pays more for less',
      'PaidTool' in tiers.get(coach, []), tiers)
check('Base does NOT grant it', 'PaidTool' not in tiers.get(base, []), tiers)

gp.Free('PaidTool')
tiers = json.loads(open(toml_path, encoding='utf-8').read()
                   .split('TIERS = \"\"\"')[1].split('\"\"\"')[0])
check('ungating clears EVERY tier in the expansion, not just the entry',
      not any('PaidTool' in v for v in tiers.values()), tiers)

shutil.rmtree(tmp, ignore_errors=True)
print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
