"""The shared command-usage file (docs/CommandUsage.md), palette side.

Owner, 2026-09-23: frequently used commands rank higher, optionally, shared
with the TDXLU launcher. The contract pins the math so both sides can prove
they agree; this runs its test vectors against FNS_CommandPalette's
CommandCuration module, then walks the file rules against a scratch palette
with a fake `app` and `debug`: a run is applied to the file as it is now
(another TD's increment survives), the other consumer's block is never
touched, a higher schema is left alone, an unreadable file is parked, stale
entries prune, and Clear drops only our block.

    python tests/test_command_usage.py
"""
import io
import json
import os
import shutil
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_CommandPalette', 'CommandCuration.py')
FAILS = []
DAY = 86400.0


def check(label, cond, detail=''):
	if cond:
		print('  PASS  %s' % label)
	else:
		FAILS.append(label)
		print('  FAIL  %s   %s' % (label, detail))


def load(palette_dir):
	mod = types.ModuleType('CommandCuration')
	mod.app = types.SimpleNamespace(userPaletteFolder=palette_dir)
	mod.debug = lambda *a: None
	exec(compile(io.open(MODULE, encoding='utf-8').read(), MODULE, 'exec'), mod.__dict__)
	return mod


def main():
	scratch = tempfile.mkdtemp(prefix='fns_usage_')
	try:
		m = load(scratch)
		print('test vectors (docs/CommandUsage.md)')
		r4 = lambda x: round(x, 4)
		check('never used -> 0.0', m.usage_bonus(0) == 0.0)
		check('v=1 -> 1.8214', r4(m.usage_bonus(1)) == 1.8214, m.usage_bonus(1))
		v = 1 * m.decay(1209600)
		check('one run 14 days ago: v=0.5 -> 1.0654', v == 0.5 and r4(m.usage_bonus(v)) == 1.0654)
		e = m.record_run({'score': 4.0, 'last': 0.0, 'count': 4}, 1209600.0)
		check('score 4, one half-life, then a run -> 3.0', e['score'] == 3.0 and e['count'] == 5, e)
		doc = {'consumers': {'fnstools': {'A#a': {'score': 3.0, 'last': 100.0}},
							 'tdxlu': {'A#a': {'score': 2.0, 'last': 100.0}}}}
		v = m.usage_values(doc, 100.0)['A#a']
		check('summed across consumers: v=5 -> 4.7082', v == 5.0 and r4(m.usage_bonus(v)) == 4.7082)
		check('saturated: v=20 and v=100 -> 8.0', m.usage_bonus(20) == 8.0 and m.usage_bonus(100) == 8.0)
		v = 101 * m.decay(365 * DAY)
		check('old heavy use fades: 101 a year ago -> 0.0000', r4(m.usage_bonus(v)) == 0.0 and v < 2e-06, v)
		check('a last in the future does not grow', m.decay(-5 * DAY) == 1.0)

		print('file rules')
		path = m.usage_path()
		check('path beside the curation file',
			  path == scratch.replace('\\', '/') + '/FNSTools/config/command-usage.json', path)
		uf = m.UsageFile(log=lambda *a: None)
		t0 = 1788000000.0
		uf.record('Tool#a', now=t0)
		# another TD writes a run and a launcher block in between
		with open(path, encoding='utf-8') as f:
			data = json.load(f)
		data['consumers']['fnstools']['Tool#b'] = {'score': 1.0, 'last': t0, 'count': 1}
		data['consumers']['tdxlu'] = {'Tool#a': {'score': 2.0, 'last': t0, 'count': 2}}
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f)
		uf.record('Tool#a', now=t0)
		with open(path, encoding='utf-8') as f:
			data = json.load(f)
		mine = data['consumers']['fnstools']
		check('a run applies to the file as re-read (another TD survives)', 'Tool#b' in mine)
		check('the run landed: score 2.0, count 2', mine['Tool#a']['score'] == 2.0 and mine['Tool#a']['count'] == 2)
		check('the launcher block is untouched', data['consumers']['tdxlu'] == {'Tool#a': {'score': 2.0, 'last': t0, 'count': 2}})
		check('schema written', data['schema'] == 1)
		check('bonuses sum both blocks (v=4)', r4(uf.bonuses(now=t0)['Tool#a']) == r4(m.usage_bonus(4.0)))

		uf.record('Tool#c', now=t0 + 120 * DAY)
		with open(path, encoding='utf-8') as f:
			mine = json.load(f)['consumers']['fnstools']
		check('entries decayed below 0.01 prune on write', set(mine) == {'Tool#c'}, sorted(mine))

		check('clear drops our block only', uf.clear())
		with open(path, encoding='utf-8') as f:
			data = json.load(f)
		check('  ...launcher block still there', 'fnstools' not in data['consumers'] and 'tdxlu' in data['consumers'])

		newer = {'schema': 2, 'consumers': {'tdxlu': {'X#y': {'score': 1.0, 'last': t0}}}}
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(newer, f)
		before = open(path, 'rb').read()
		check('a higher schema records nothing', uf.record('Tool#a', now=t0) is False)
		check('  ...and leaves the file untouched', open(path, 'rb').read() == before)
		check('  ...and reads as no bonus', m.UsageFile().bonuses(now=t0) == {})

		with open(path, 'w', encoding='utf-8') as f:
			f.write('{torn')
		check('an unreadable file still records', uf.record('Tool#a', now=t0))
		folder = os.path.dirname(path)
		parked = [f for f in os.listdir(folder) if f.startswith('command-usage.json.corrupt-')]
		check('  ...after parking it', len(parked) == 1, os.listdir(folder))
		with open(path, encoding='utf-8') as f:
			data = json.load(f)
		check('  ...into a fresh document holding just that key',
			  list(data['consumers']) == ['fnstools'] and list(data['consumers']['fnstools']) == ['Tool#a'])
		check('no temp file left behind', not [f for f in os.listdir(folder) if f.endswith('.tmp')])

		# a read refused because another writer holds the file open is not corruption
		before = open(path, 'rb').read()
		real_open = open

		def held_open(p, *a, **k):
			if str(p).replace('\\', '/') == path and 'w' not in (a[0] if a else k.get('mode', 'r')):
				raise PermissionError(13, 'sharing violation', p)
			return real_open(p, *a, **k)
		m.open = held_open
		try:
			check('a file held open skips the write', uf.record('Tool#z', now=t0) is False)
		finally:
			del m.open
		check('  ...and is neither parked nor changed',
			  open(path, 'rb').read() == before and len([f for f in os.listdir(folder) if '.corrupt-' in f]) == 1)
	finally:
		shutil.rmtree(scratch, ignore_errors=True)
	print()
	print('%d failed' % len(FAILS) if FAILS else 'all passed')
	return 1 if FAILS else 0


if __name__ == '__main__':
	raise SystemExit(main())
