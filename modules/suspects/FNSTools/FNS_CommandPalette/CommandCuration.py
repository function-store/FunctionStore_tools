"""CommandCuration -- the command curation file shared with the launcher.

Favourites, hidden/shown overrides and presets for quick-launch commands live
in ONE file per machine, read and written by every consumer: this palette and
the TDXLPP launcher (its tray overlay and its palette tab inside TD). Neither
side owns the file; both follow the same rules, which are the contract in
docs/CommandCuration.md. In short:

  * it sits beside the toolkit's roaming config, under the MACHINE-DEFAULT
    user palette folder (never a relocated store folder);
  * entries key on the curation identity `tool#id`, never on the wire key;
  * every entry carries `updated` (epoch seconds); on read and before every
    write the file is merged per entry and the greater `updated` wins;
  * a removal is a tombstone (`favorite: false` with no `hidden`, or a preset
    with `deleted: true`), pruned after TOMBSTONE_DAYS, so a stale peer can
    never resurrect what the user removed elsewhere;
  * the document carries a `revision` that every write increments; a write
    re-checks the file's (mtime, size) AND revision right before the rename
    and merges again if another consumer wrote in between, so two open
    panels cannot lose each other's updates;
  * the rename itself is retried a few times: on Windows a replace fails
    with a sharing violation while any other process holds the destination
    open (the other consumer mid-read, an antivirus scanner, the indexer);
  * a file that will not parse is parked beside itself and immediately
    replaced from this consumer's merged memory when it has any, so a torn
    write costs at most what changed since the last read. Only a parse
    failure is corruption: a read the OS refuses (another writer holds the
    file open) is FileBusy, and the file is neither parked nor written over;
  * the file itself records who has seeded it (`seeded`), so a consumer whose
    private store comes back from a backup does not seed twice.

Pure Python: nothing here touches an operator. The one TouchDesigner call is
`app.userPaletteFolder`, made at call time.
"""

import json
import math
import os
import time

# --- the toolkit's folder in the user palette ------------------------------
# <user palette>/FNSTools (docs/PaletteFolderContract.md). Until 2026-09-18
# this was FNStools_ext; a legacy folder is renamed into place the first
# time any reader looks. This function is carried verbatim by every FNS
# extension that reads the folder: they ship as separate toxes and cannot
# share a module, and whichever reader gets there first must be able to
# migrate on its own. Master copy: FNS_Updater/ExtUpdater.py.
PALETTE_DIR = 'FNSTools'
LEGACY_PALETTE_DIR = 'FNStools_ext'


def _fnsPaletteRoot():
	"""'<user palette>/FNSTools', migrating a legacy FNStools_ext folder into
	place on first sight; '' when this install has no user palette folder."""
	try:
		base = str(app.userPaletteFolder).replace('\\', '/').rstrip('/')
	except Exception:
		return ''
	if not base:
		return ''
	new = '%s/%s' % (base, PALETTE_DIR)
	legacy = None
	try:
		for fn in os.listdir(base):
			if fn.lower() == LEGACY_PALETTE_DIR.lower() and os.path.isdir('%s/%s' % (base, fn)):
				legacy = '%s/%s' % (base, fn)
				break
	except Exception:
		pass
	if legacy is None:
		return new
	if not os.path.isdir(new):
		try:
			os.rename(legacy, new)
			return new
		except OSError as e:
			# a file held open, most likely; this session keeps using the
			# old folder and the next start tries again
			debug('FNS: could not rename %s to %s (%s)' % (legacy, new, e))
			return legacy
	# both exist (a race, or an older launcher recreated the legacy
	# folder): whatever the legacy folder holds that the new one lacks
	# moves over, and the legacy folder goes once it is empty
	# entry by entry, each on its own: a folder something still watches
	# (TDFam's Folder DAT on the old family tree) refuses to move, and that
	# must not keep the store or the config from moving. A folder both
	# sides hold is merged the same way one level down, because a reader
	# that seeds its file when it is missing (OpTemplates) can have made
	# the new folder before this ran. A FILE both sides hold stays as the
	# new side has it, and the legacy copy is kept aside under
	# FNSTools/legacy_<old name>/ at its old relative path, never deleted:
	# the new side's file is usually the later state, but it can be a seed
	# (OpTemplates writes its default library when its file is missing)
	# while the legacy one is the user's work. OpTemplates looks there
	# before seeding again. Deleting it lost a user's library (2026-09-18).
	left = []

	def merge(src_dir, dst_dir):
		for fn in os.listdir(src_dir):
			src, dst = '%s/%s' % (src_dir, fn), '%s/%s' % (dst_dir, fn)
			try:
				if not os.path.exists(dst):
					os.rename(src, dst)
				elif os.path.isdir(src) and os.path.isdir(dst):
					merge(src, dst)
					if not os.listdir(src):
						os.rmdir(src)
				elif os.path.isfile(src) and os.path.isfile(dst):
					rel = os.path.relpath(src, legacy).replace('\\', '/')
					keep = '%s/legacy_%s/%s' % (new, LEGACY_PALETTE_DIR, rel)
					if os.path.exists(keep):
						os.remove(src)
					else:
						os.makedirs(os.path.dirname(keep), exist_ok=True)
						os.rename(src, keep)
			except OSError as e:
				left.append('%s (%s)' % (fn, e))

	try:
		merge(legacy, new)
		if not os.listdir(legacy):
			os.rmdir(legacy)
	except Exception as e:
		left.append(str(e))
	if left:
		debug('FNS: legacy palette folder %s not fully merged: %s' % (legacy, '; '.join(left)))
	return new

import uuid

SCHEMA = 1
FILENAME = 'command-curation.json'
WRITTEN_BY = 'fnstools'
TOMBSTONE_DAYS = 30
WRITE_ATTEMPTS = 3          # read-merge-write rounds when another consumer keeps writing
RENAME_ATTEMPTS = 5         # os.replace tries when the destination is momentarily held open
RENAME_PAUSE_S = 0.02


class FileBusy(Exception):
	"""The file exists but the OS refused the read -- on Windows, a sharing
	violation while another writer (the launcher, a scanner) holds it open.
	Not corruption: nothing is parked and nothing is written over it."""


def curation_path() -> str:
	"""`<machine-default user palette>/FNSTools/config/command-curation.json`."""
	return os.path.join(_fnsPaletteRoot(), 'config', FILENAME).replace('\\', '/')


def empty() -> dict:
	return {'schema': SCHEMA, 'revision': 0, 'seeded': {}, 'commands': {}, 'presets': {}}


def _updated(entry) -> float:
	try:
		return float((entry or {}).get('updated') or 0)
	except (TypeError, ValueError):
		return 0.0


def _int(value) -> int:
	try:
		return int(value or 0)
	except (TypeError, ValueError):
		return 0


def normalize(data) -> dict:
	"""Whatever came off disk, as a well-formed document: the revision, the
	seeded map and two dict sections holding dict entries. Anything else is
	dropped rather than trusted."""
	out = empty()
	if not isinstance(data, dict):
		return out
	out['revision'] = _int(data.get('revision'))
	seeded = data.get('seeded')
	if isinstance(seeded, dict):
		for k, v in seeded.items():
			try:
				out['seeded'][str(k)] = float(v)
			except (TypeError, ValueError):
				pass
	for section in ('commands', 'presets'):
		src = data.get(section)
		if isinstance(src, dict):
			out[section] = dict((str(k), dict(v)) for k, v in src.items() if isinstance(v, dict))
	return out


def merge(mine: dict, theirs: dict) -> dict:
	"""Per entry, the greater `updated` wins; a tie keeps `theirs` (the file).
	The seeded map is a union keeping the later stamp per consumer; the
	revision is the greater of the two."""
	out = empty()
	for section in ('commands', 'presets'):
		a, b = mine.get(section) or {}, theirs.get(section) or {}
		for key in set(a) | set(b):
			ea, eb = a.get(key), b.get(key)
			if ea is None:
				out[section][key] = eb
			elif eb is None:
				out[section][key] = ea
			else:
				out[section][key] = ea if _updated(ea) > _updated(eb) else eb
	sa, sb = mine.get('seeded') or {}, theirs.get('seeded') or {}
	for key in set(sa) | set(sb):
		out['seeded'][key] = max(float(sa.get(key, 0) or 0), float(sb.get(key, 0) or 0))
	out['revision'] = max(_int(mine.get('revision')), _int(theirs.get('revision')))
	return out


def is_command_tombstone(entry) -> bool:
	return not entry.get('favorite') and 'hidden' not in entry


def prune(data: dict, now: float = None) -> None:
	"""Drop tombstones older than TOMBSTONE_DAYS, in place."""
	cutoff = (now or time.time()) - TOMBSTONE_DAYS * 86400
	commands = data['commands']
	for key in list(commands):
		if is_command_tombstone(commands[key]) and _updated(commands[key]) < cutoff:
			del commands[key]
	presets = data['presets']
	for key in list(presets):
		if presets[key].get('deleted') and _updated(presets[key]) < cutoff:
			del presets[key]


def replace_with_retry(src: str, dst: str, log=None) -> None:
	"""os.replace, retried a few times: Windows refuses to replace a file any
	other process has open at that instant (a reader, an antivirus scanner,
	the indexer, a sync client), and reports it as a plain OSError."""
	for attempt in range(RENAME_ATTEMPTS):
		try:
			os.replace(src, dst)
			return
		except OSError as e:
			if attempt == RENAME_ATTEMPTS - 1:
				raise
			if log:
				log('curation file: rename refused (%s), retrying' % e)
			time.sleep(RENAME_PAUSE_S)


class CurationFile:
	"""The shared file as seen from one consumer: a merged in-memory copy that
	re-reads when the file changes on disk and writes through on every change.

	`seed` is a zero-argument callable returning a document-shaped dict of
	entries this consumer kept BEFORE the shared file existed. It is asked
	once per MACHINE, not once per consumer install: the file's `seeded` map
	records that this consumer has seeded, so a private store restored from a
	backup cannot seed again and resurrect removals whose tombstones were
	pruned. Seeded entries are adopted wherever the file has no entry for that
	key (a union, never an overwrite)."""

	def __init__(self, seed=None, log=None):
		self._data = empty()
		self._seen = None               # (mtime, size) of the file as last read or written
		self._seed = seed
		self._log = log or (lambda *a: None)
		self._loaded = False

	# --- file access ----------------------------------------------------------

	@property
	def path(self) -> str:
		return curation_path()

	def _stat(self):
		"""(mtime, size) of the file, or None when absent. Both, because mtime
		alone can stay equal across two writes inside one timestamp tick."""
		try:
			st = os.stat(self.path)
		except OSError:
			return None
		return (st.st_mtime, st.st_size)

	def _hasEntries(self) -> bool:
		return bool(self._data['commands'] or self._data['presets'])

	def _readFile(self):
		"""The document on disk, or None. A file that exists but will not
		parse is parked beside itself (`<file>.corrupt-<epoch>`, recoverable
		by hand) so nothing stale is trusted and nothing is overwritten in
		place; the caller then replaces it from memory when it can. A read
		the OS refuses raises FileBusy instead: only a parse failure is
		corruption, and parking a healthy file another writer holds open
		would throw away its latest entries."""
		path = self.path
		try:
			with open(path, encoding='utf-8') as f:
				return normalize(json.load(f))
		except FileNotFoundError:
			return None
		except OSError as e:
			raise FileBusy(str(e))
		except ValueError as e:
			if os.path.exists(path):
				parked = '%s.corrupt-%d' % (path, int(time.time()))
				try:
					os.replace(path, parked)
					self._log('curation file unreadable (%s); parked as %s' % (e, parked))
				except OSError:
					self._log('curation file unreadable (%s) and could not be parked' % e)
			return None

	def _diskRevision(self):
		"""The revision the file carries right now, without touching memory;
		None when the file is absent or unreadable."""
		try:
			with open(self.path, encoding='utf-8') as f:
				return _int(json.load(f).get('revision'))
		except (OSError, ValueError, AttributeError):
			return None

	def _write(self) -> None:
		data = normalize(self._data)
		prune(data)
		data['revision'] = data['revision'] + 1
		data['schema'] = SCHEMA
		data['written_by'] = WRITTEN_BY          # diagnostic only: never merged on
		data['written_at'] = time.time()
		path = self.path
		os.makedirs(os.path.dirname(path), exist_ok=True)
		tmp = '%s.%d.tmp' % (path, os.getpid())   # per process: two TDs never share one
		with open(tmp, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=1, sort_keys=True)
		replace_with_retry(tmp, path, self._log)
		self._data = data
		self._seen = self._stat()

	def load(self) -> dict:
		"""Memory brought up to date with the file: re-read and merged per
		entry when (mtime, size) moved. A file that was parked as unreadable,
		or that vanished, is replaced from memory as soon as this consumer
		holds loaded state with entries in it. The first load seeds this
		consumer's legacy entries unless the file says it already has."""
		seen = self._stat()
		if seen is not None and seen != self._seen:
			try:
				disk = self._readFile()
			except FileBusy as e:
				# held open by another writer: keep working from memory and
				# read it next time; never park it, never write over it
				self._log('curation file busy (%s); using memory for now' % e)
				return self._data
			if disk is not None:
				self._data = merge(self._data, disk)
				self._seen = seen
			elif self._loaded and self._hasEntries():
				self._write()               # parked as unreadable: our merged copy replaces it
				self._log('curation file: rewritten from memory after parking the unreadable one')
		elif seen is None and self._loaded and self._hasEntries():
			self._write()                   # vanished under us: put our merged copy back
			self._log('curation file: rewritten from memory after it vanished')
		if not self._loaded:
			self._loaded = True
			if self._seed is not None and WRITTEN_BY not in self._data['seeded']:
				self._adopt(self._seed())
		return self._data

	def _adopt(self, legacy) -> None:
		"""Union this consumer's legacy entries into the file and stamp the
		file as seeded by this consumer -- always written, even when nothing
		was adopted, so the stamp is on the machine and not in a config that
		can be restored from backup."""
		legacy = normalize(legacy)
		added = 0
		for section in ('commands', 'presets'):
			for key, entry in legacy[section].items():
				if key not in self._data[section]:
					entry = dict(entry)
					entry.setdefault('updated', time.time())
					self._data[section][key] = entry
					added += 1
		self._data['seeded'][WRITTEN_BY] = time.time()
		self._write()
		self._log('curation file: seeded by %s, %d legacy entries adopted' % (WRITTEN_BY, added))

	def _unchangedSinceRead(self) -> bool:
		"""Nobody wrote between our read and now: same (mtime, size) AND the
		same revision. The revision closes the one hole stat leaves (two
		same-size writes inside one timestamp tick)."""
		if self._stat() != self._seen:
			return False
		rev = self._diskRevision()
		return rev is None or rev == self._data['revision']

	def _commit(self, mutate) -> None:
		"""Read-merge, apply, write -- re-checking that nobody wrote between
		our read and our rename. Two consumers that both read before either
		wrote would otherwise silently drop one change; the re-check and retry
		close that window without a lock file. The mutation is re-applied on
		every attempt, so it must be idempotent (every one here is)."""
		for attempt in range(WRITE_ATTEMPTS):
			self.load()
			mutate(self._data)
			if self._busy():
				time.sleep(RENAME_PAUSE_S)
				continue
			if self._unchangedSinceRead():
				self._write()
				return
			self._log('curation file: moved between read and write, merging again (%d)' % (attempt + 1))
		self.load()                         # take whatever is there now, then ours on top
		mutate(self._data)
		if self._busy():
			# still held open: the change stays in memory with its `updated`
			# stamp, wins the next merge and is written by the next change
			self._log('curation file busy; change kept in memory, written with the next one')
			return
		self._write()
		self._log('curation file: wrote after %d retries; another writer kept moving it' % WRITE_ATTEMPTS)

	def _busy(self) -> bool:
		"""The file exists and the last load could not read it: writing now
		would put a document built from memory over entries we never saw."""
		seen = self._stat()
		return seen is not None and seen != self._seen

	# --- what the palette reads -----------------------------------------------

	def favourites(self) -> set:
		return set(k for k, e in self.load()['commands'].items() if e.get('favorite'))

	def overrides(self) -> dict:
		"""identity -> True (hidden) / False (shown); absent = the tool's default."""
		return dict((k, bool(e['hidden'])) for k, e in self.load()['commands'].items() if 'hidden' in e)

	def presets(self) -> list:
		"""Live presets as the palette shapes them: `{id, label, ident, args}`."""
		out = []
		for pid, e in self.load()['presets'].items():
			if e.get('deleted') or not e.get('target'):
				continue
			out.append({'id': pid, 'label': str(e.get('label') or e.get('target')),
						'ident': str(e['target']), 'args': dict(e.get('kwargs') or {})})
		out.sort(key=lambda p: (p['label'].lower(), p['id']))
		return out

	# --- what the palette writes ----------------------------------------------

	def set_favourite(self, ident: str, on: bool) -> None:
		def mutate(d):
			e = d['commands'].setdefault(ident, {})
			e['favorite'] = bool(on)
			e['updated'] = time.time()
		self._commit(mutate)

	def set_hidden(self, ident: str, value) -> None:
		"""True hides, False shows, None drops the override (back to the tool's default)."""
		def mutate(d):
			e = d['commands'].setdefault(ident, {})
			if value is None:
				e.pop('hidden', None)
			else:
				e['hidden'] = bool(value)
			e['updated'] = time.time()
		self._commit(mutate)

	def add_preset(self, label: str, target: str, kwargs: dict, preset_id: str = None) -> dict:
		pid = preset_id or uuid.uuid4().hex[:8]
		def mutate(d):
			d['presets'][pid] = {'label': str(label).strip() or target, 'target': target,
								 'kwargs': dict(kwargs or {}), 'updated': time.time()}
		self._commit(mutate)
		return {'id': pid, 'label': str(label).strip() or target, 'ident': target, 'args': dict(kwargs or {})}

	def delete_preset(self, preset_id: str) -> bool:
		live = self.load()['presets'].get(preset_id)
		if live is None or live.get('deleted'):
			return False
		def mutate(d):
			e = d['presets'].get(preset_id)
			if e is not None:
				e['deleted'] = True
				e['updated'] = time.time()
		self._commit(mutate)
		return True


# --- command usage: rank frequently used commands higher --------------------
# A second shared file beside the curation file, contract in
# docs/CommandUsage.md. Kept apart on purpose: curation rule 7 lets nothing
# else ride along, and a counter written on every run must not churn the
# favourites file. Each consumer writes only its own block; every TD running
# FNSTools writes the `fnstools` block, so a run is applied to the value
# re-read from disk, never to a block held in memory. Two TDs recording in
# the same instant can lose one increment; usage is a tie-breaker, so that is
# accepted.

USAGE_SCHEMA = 1
USAGE_FILENAME = 'command-usage.json'
HALF_LIFE = 1209600.0       # 14 days, in seconds
V_SAT = 20.0                # decayed uses at which the bonus saturates
BONUS_MAX = 8.0             # below FAVOURITE_BONUS (12), so a favourite always wins alone
PRUNE_BELOW = 0.01          # a single use falls under this after ~93 days


def usage_path() -> str:
	"""`<machine-default user palette>/FNSTools/config/command-usage.json`."""
	return os.path.join(_fnsPaletteRoot(), 'config', USAGE_FILENAME).replace('\\', '/')


def decay(dt: float) -> float:
	return 0.5 ** (max(0.0, float(dt)) / HALF_LIFE)


def usage_bonus(v: float) -> float:
	"""The ranking bonus for a summed decayed usage value, in [0, BONUS_MAX]."""
	if v <= 0:
		return 0.0
	return min(BONUS_MAX, BONUS_MAX * math.log1p(v) / math.log1p(V_SAT))


def _float(value) -> float:
	try:
		return float(value or 0)
	except (TypeError, ValueError):
		return 0.0


def record_run(entry, now: float) -> dict:
	"""One entry after one more run at `now`: the stored score decays to now, plus one."""
	entry = entry if isinstance(entry, dict) else {}
	score = _float(entry.get('score'))
	last = _float(entry.get('last'))
	return {'score': (score * decay(now - last) if score else 0.0) + 1.0,
			'last': float(now), 'count': int(_float(entry.get('count'))) + 1}


def usage_values(data, now: float) -> dict:
	"""tool#id -> decayed usage summed over every consumer's block."""
	out = {}
	consumers = data.get('consumers') if isinstance(data, dict) else None
	if not isinstance(consumers, dict):
		return out
	for block in consumers.values():
		if not isinstance(block, dict):
			continue
		for key, e in block.items():
			if isinstance(e, dict):
				out[key] = out.get(key, 0.0) + _float(e.get('score')) * decay(now - _float(e.get('last')))
	return out


class UsageFile:
	"""The shared usage file as one consumer sees it: bonuses read (cached by
	the file's (mtime, size)), runs recorded straight to disk."""

	def __init__(self, consumer: str = WRITTEN_BY, log=None):
		self._consumer = consumer
		self._log = log or (lambda *a: None)
		self._seen = None
		self._data = {}

	@property
	def path(self) -> str:
		return usage_path()

	def _stat(self):
		try:
			st = os.stat(self.path)
		except OSError:
			return None
		return (st.st_mtime, st.st_size)

	def _read(self):
		"""(document, ok_to_write). A higher schema is left alone and read as
		empty; an unreadable file is parked and read as empty (usage is not
		worth rebuilding from memory)."""
		path = self.path
		try:
			with open(path, encoding='utf-8') as f:
				data = json.load(f)
			if not isinstance(data, dict):
				raise ValueError('not a JSON object')
		except FileNotFoundError:
			return {}, True
		except OSError as e:
			# held open by another writer (a Windows sharing violation) is not
			# corruption: skip this write rather than park a good file
			self._log('usage file not readable right now (%s); skipped' % e)
			return {}, False
		except ValueError as e:
			if os.path.exists(path):
				parked = '%s.corrupt-%d' % (path, int(time.time()))
				try:
					os.replace(path, parked)
					self._log('usage file unreadable (%s); parked as %s' % (e, parked))
				except OSError:
					self._log('usage file unreadable (%s) and could not be parked' % e)
					return {}, False
			return {}, True
		if _int(data.get('schema')) > USAGE_SCHEMA:
			return {}, False
		return data, True

	def values(self, now: float = None) -> dict:
		"""tool#id -> summed decayed usage, re-read only when the file moved."""
		seen = self._stat()
		if seen != self._seen:
			self._data = self._read()[0] if seen is not None else {}
			self._seen = seen
		return usage_values(self._data, time.time() if now is None else now)

	def bonuses(self, now: float = None) -> dict:
		return dict((k, usage_bonus(v)) for k, v in self.values(now).items())

	def record(self, ident: str, now: float = None) -> bool:
		"""One successful run of `ident`, applied to the file as it is now."""
		if not ident:
			return False
		now = time.time() if now is None else now
		data, ok = self._read()
		if not ok:
			return False
		consumers = data.get('consumers') if isinstance(data.get('consumers'), dict) else {}
		mine = consumers.get(self._consumer) if isinstance(consumers.get(self._consumer), dict) else {}
		mine[ident] = record_run(mine.get(ident), now)
		for key in list(mine):
			e = mine[key]
			if not isinstance(e, dict) or _float(e.get('score')) * decay(now - _float(e.get('last'))) < PRUNE_BELOW:
				del mine[key]
		consumers[self._consumer] = mine
		data['consumers'] = consumers
		data['schema'] = USAGE_SCHEMA
		self._writeDoc(data)
		return True

	def clear(self) -> bool:
		"""Drop this consumer's block only; the other consumer's history still counts."""
		data, ok = self._read()
		if not ok:
			return False
		consumers = data.get('consumers') if isinstance(data.get('consumers'), dict) else {}
		if self._consumer not in consumers:
			return True
		del consumers[self._consumer]
		data['consumers'] = consumers
		data['schema'] = USAGE_SCHEMA
		self._writeDoc(data)
		return True

	def _writeDoc(self, data) -> None:
		path = self.path
		os.makedirs(os.path.dirname(path), exist_ok=True)
		tmp = '%s.%d.tmp' % (path, os.getpid())
		with open(tmp, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=1, sort_keys=True)
		replace_with_retry(tmp, path, self._log)
		self._data = data
		self._seen = self._stat()
