"""The shared command curation file (docs/CommandCuration.md), palette side.

Favourites, hidden overrides and presets live in one file shared with the
TDXLU launcher. This walks CommandCuration.CurationFile against a scratch
palette with a fake `app` and `debug`: two consumers merge per entry, an
unreadable file is parked and replaced from memory, and a file another writer
holds open (a Windows sharing violation) is NOT corruption -- it is neither
parked nor written over, and a change made meanwhile stays in memory until
the next write carries it.

    python tests/test_command_curation.py
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
	mod.RENAME_PAUSE_S = 0.0
	return mod


def hold_open(mod, path):
	"""Make every read of `path` in the module fail as a sharing violation."""
	real_open = open

	def fake(p, *a, **k):
		mode = a[0] if a else k.get('mode', 'r')
		if str(p).replace('\\', '/') == path and 'w' not in mode:
			raise PermissionError(13, 'sharing violation', p)
		return real_open(p, *a, **k)
	mod.open = fake


def release(mod):
	del mod.open


def corrupt_count(folder):
	return len([f for f in os.listdir(folder) if '.corrupt-' in f])


def main():
	scratch = tempfile.mkdtemp(prefix='fns_curation_')
	try:
		m = load(scratch)
		path = m.curation_path()
		folder = os.path.dirname(path)
		a = m.CurationFile(seed=lambda: {})
		b = m.CurationFile()

		print('merge between two consumers')
		a.set_favourite('Tool#a', True)
		b.set_favourite('Tool#b', True)
		check('each sees both favourites', a.favourites() == {'Tool#a', 'Tool#b'} == b.favourites(),
			  (a.favourites(), b.favourites()))
		check('the file carries the seeded stamp', 'fnstools' in json.load(open(path))['seeded'])
		check('no temp file left behind', not [f for f in os.listdir(folder) if f.endswith('.tmp')])

		print('a file held open is busy, not corrupt')
		before = open(path, 'rb').read()
		os.utime(path, None)                    # the other writer touched it
		os.utime(path, (os.stat(path).st_atime, os.stat(path).st_mtime + 5))
		hold_open(m, path)
		try:
			favs = a.favourites()
			check('a read keeps working from memory', favs == {'Tool#a', 'Tool#b'}, favs)
			a.set_favourite('Tool#c', True)
			check('a change while busy is not written over the file', open(path, 'rb').read() == before)
			check('  ...and nothing is parked', corrupt_count(folder) == 0, os.listdir(folder))
			check('  ...and the change is held in memory', 'Tool#c' in a.favourites())
		finally:
			release(m)
		a.set_favourite('Tool#d', True)
		on_disk = json.load(open(path))['commands']
		check('the next write carries the held change',
			  on_disk.get('Tool#c', {}).get('favorite') is True and on_disk.get('Tool#d', {}).get('favorite') is True,
			  sorted(on_disk))
		check('  ...without losing the other consumer\'s entry', on_disk.get('Tool#b', {}).get('favorite') is True)

		print('a fresh consumer meeting a busy file')
		c = m.CurationFile()
		hold_open(m, path)
		try:
			before = open(path, 'rb').read()
			check('reads as empty', c.favourites() == set())
			check('  ...leaves the file alone', open(path, 'rb').read() == before and corrupt_count(folder) == 0)
		finally:
			release(m)
		check('  ...and reads it once it is free', 'Tool#b' in c.favourites())

		print('a file that will not parse is still parked')
		with open(path, 'w', encoding='utf-8') as f:
			f.write('{torn')
		favs = a.favourites()
		check('parked beside itself', corrupt_count(folder) == 1, os.listdir(folder))
		check('replaced from memory', 'Tool#b' in json.load(open(path))['commands'] and 'Tool#b' in favs)
	finally:
		shutil.rmtree(scratch, ignore_errors=True)
	print()
	print('%d failed' % len(FAILS) if FAILS else 'all passed')
	return 1 if FAILS else 0


if __name__ == '__main__':
	raise SystemExit(main())
