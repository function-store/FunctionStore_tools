'''Info Header Start
Name : ExtColorUI
Author : root
Saveorigin : FunctionStore_tools_2025_DEV.65.toe
Saveversion : 2025.33070
Info Header End'''


CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import

###

import json
import random

# Families are ordinary ui.colors keys; this fixed order is just for display.
FAMILY_ORDER = ('COMP', 'TOP', 'CHOP', 'SOP', 'DAT', 'MAT', 'POP', 'CUSTOM')

# Page -> TD messages ride document.title (watched via the webrender info DAT):
#   FNSCUI:<nonce>:<json>              single message
#   FNSCUI#<nonce>:<i>/<n>:<part>      chunked message, each part acked
# TD -> page is webrender.executeJavaScript into the FNS global.

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

class ExtColorUI:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)

		self.defaults: dict = {}   # factory colors, snapshotted at OnStart
		self._rx = {}              # chunk reassembly: nonce -> [total, {idx: part}]
		self._lastNonce = None
		self._gotReady = False
		self._randomized = False
		fnsLog('ColorUI: init')

	# ------------------------------------------------------------------ state

	@property
	def Overrides(self) -> dict:
		return self.ownerComp.fetch('colors', {}, search=False)

	def _storeOverrides(self, d: dict):
		self.ownerComp.store('colors', d)

	@property
	def families(self):
		return [f for f in FAMILY_ORDER if f in ui.colors]

	def _snapshotDefaults(self):
		self.defaults = {k: tuple(ui.colors[k]) for k in ui.colors}

	def OnStart(self):
		"""Project start (execute1 onStart/onCreate). Idempotent: snapshots the
		factory palette off a clean reset, then reapplies saved overrides."""
		fnsLog('ColorUI: OnStart')
		ui.colors.resetToDefaults()
		self._snapshotDefaults()
		self._randomized = False

		# migrate legacy split storage from the old par-sequence UI, and prune
		# junk keys it left behind (empty sequence rows, renamed elements)
		merged = dict(self.Overrides)
		legacy = self.ownerComp.fetch('fam_colors', None, search=False)
		if legacy:
			merged.update(legacy)
			try:
				self.ownerComp.unstore('fam_colors')
			except Exception:
				pass
		self._storeOverrides({k: v for k, v in merged.items() if k in ui.colors})

		if self.evalAutoload:
			self.ApplyOverrides()

		self._gotReady = False
		self._lastNonce = None
		self._rx = {}
		self._Kick(4)

	def ApplyOverrides(self):
		for el, rgb in self.Overrides.items():
			if el in ui.colors:
				ui.colors[el] = rgb

	# -------------------------------------------------------------- TD -> page

	@property
	def _wr(self):
		return self.ownerComp.op('webBrowser/webrender1')

	def _js(self, code):
		try:
			self._wr.executeJavaScript(code)
		except Exception as e:
			fnsLog(f'ColorUI: executeJavaScript failed: {e}', level='WARNING')

	def _sendCall(self, fn, payload: dict):
		"""Call FNS.<fn>(payload) in the page. executeJavaScript rejects
		scripts over ~8k chars AND drops rapid back-to-back calls (shared IPC
		queue), so big payloads stream through a page-side buffer paced a few
		frames apart. A new stream simply replaces any in-flight one â€” the
		leading _rxopen resets the page buffer."""
		data = json.dumps(payload)
		single = f'window.FNS && FNS.{fn}({data})'
		if len(single) <= 6000:
			self._js(single)
			return
		CH = 4000
		codes = ['window.FNS && FNS._rxopen()']
		for i in range(0, len(data), CH):
			codes.append('window.FNS && FNS._rxpart(' + json.dumps(data[i:i + CH]) + ')')
		codes.append('window.FNS && FNS._rxdone(' + json.dumps(fn) + ')')
		self._txq = codes
		self._PumpTx()

	def _PumpTx(self):
		q = getattr(self, '_txq', None)
		if not q:
			return
		self._js(q.pop(0))
		if q:
			run(f"op('{self.ownerComp.path}').ext.ExtColorUI._PumpTx()",
				delayFrames=2, fromOP=self.ownerComp)

	def _Kick(self, tries):
		"""Reload the page source until it phones home with 'ready'."""
		if self._gotReady or tries <= 0:
			return
		wr = self._wr
		if wr is not None:
			try:
				wr.par.reloadsrc.pulse()
			except Exception:
				pass
		run(f"op('{self.ownerComp.path}').ext.ExtColorUI._Kick({tries - 1})",
			delayFrames=180, fromOP=self.ownerComp)

	def SendState(self):
		if not self.defaults:
			# ext was reinitialized mid-session; treat the live palette as baseline
			self._snapshotDefaults()
		rnd = lambda v: [round(float(c), 4) for c in v[:3]]
		payload = {
			'families': self.families,
			'colors': {k: rnd(ui.colors[k]) for k in ui.colors},
			'defaults': {k: rnd(v) for k, v in self.defaults.items()},
			'overrides': sorted(self.Overrides),
			'autoload': bool(self.evalAutoload),
			'groupby': self.evalGroupby,
			'randomized': self._randomized,
			'version': self.ownerComp.par.Pkgversion.eval(),
		}
		self._sendCall('setState', payload)

	def Toast(self, text):
		self._js('window.FNS && FNS.toast(' + json.dumps(str(text)) + ')')

	# -------------------------------------------------------------- page -> TD

	def OnBrowserTitle(self, raw):
		"""Called by watch_browser when the page rewrites document.title."""
		raw = str(raw)
		try:
			if raw.startswith('FNSCUI:'):
				_, nonce, payload = raw.split(':', 2)
				self._js(f'window.FNS && FNS._ack({json.dumps(nonce)})')
				if nonce == self._lastNonce:
					return
				self._lastNonce = nonce
				self._dispatch(json.loads(payload))
			elif raw.startswith('FNSCUI#'):
				head, idx, part = raw.split(':', 2)
				nonce = head[len('FNSCUI#'):]
				i, n = (int(x) for x in idx.split('/'))
				self._js(f'window.FNS && FNS._ack({json.dumps(nonce)}, {i})')
				buf = self._rx.setdefault(nonce, [n, {}])
				buf[1][i] = part
				if len(buf[1]) == buf[0]:
					del self._rx[nonce]
					if nonce == self._lastNonce:
						return
					self._lastNonce = nonce
					whole = ''.join(buf[1][k] for k in range(buf[0]))
					self._dispatch(json.loads(whole))
		except Exception as e:
			fnsLog(f'ColorUI: bad browser message {raw[:80]!r}: {e}', level='WARNING')

	def _dispatch(self, msg: dict):
		cmd = msg.get('cmd')
		if cmd == 'ready':
			self._gotReady = True
			fnsLog('ColorUI: web UI ready')
			self.SendState()
		elif cmd == 'set':
			self._apply(msg.get('colors') or {}, record=True)
		elif cmd == 'preview':
			self._apply(msg.get('colors') or {}, record=False)
		elif cmd == 'resetAll':
			self.ResetAll()
		elif cmd == 'randomize':
			self.Randomize()
		elif cmd == 'undoRandom':
			self.UndoRandom()
		elif cmd == 'import':
			self.DoImport(dialog=True)
		elif cmd == 'export':
			self.DoExport(dialog=True)
		elif cmd == 'autoload':
			self.ownerComp.par.Autoload = bool(msg.get('value'))
		elif cmd == 'groupby':
			v = msg.get('value')
			if v in ('prefix', 'role'):
				self.ownerComp.par.Groupby = v
		elif cmd == 'refresh':
			self.SendState()
		else:
			fnsLog(f'ColorUI: unknown web command {cmd!r}', level='WARNING')

	def _apply(self, colors: dict, record: bool):
		if not self.defaults:
			self._snapshotDefaults()
		ov = dict(self.Overrides) if record else None
		for el, rgb in colors.items():
			if el not in ui.colors or not isinstance(rgb, (list, tuple)) or len(rgb) < 3:
				continue
			try:
				rgb = [max(0.0, min(1.0, float(c))) for c in rgb[:3]]
			except (TypeError, ValueError):
				continue
			ui.colors[el] = rgb
			if record:
				d = self.defaults.get(el)
				if d is not None and all(abs(a - b) < 1e-3 for a, b in zip(d, rgb)):
					ov.pop(el, None)   # back at default -> not an override
				else:
					ov[el] = tuple(rgb)
		if record:
			self._storeOverrides(ov)

	# ----------------------------------------------------------------- actions

	def ResetAll(self):
		fnsLog('ColorUI: resetting all UI colors to defaults')
		ui.colors.resetToDefaults()
		self._snapshotDefaults()
		self._storeOverrides({})
		self._randomized = False
		self.SendState()

	def Randomize(self):
		fnsLog('ColorUI: randomizing all UI colors')
		for el in ui.colors:
			ui.colors[el] = [random.uniform(0, 1) for _ in range(3)]
		self._randomized = True
		self.SendState()

	def UndoRandom(self):
		ui.colors.resetToDefaults()
		self.ApplyOverrides()
		self._randomized = False
		self.SendState()

	def DoImport(self, dialog=False):
		path = self.evalFile
		if dialog or not path:
			path = ui.chooseFile(load=True, start=path or None,
								 fileTypes=['json'], title='Import UI colors')
			if not path:
				return
			self.evalFile = path
		try:
			with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			if not isinstance(data, dict):
				raise ValueError('not a {element: [r,g,b]} dictionary')
		except Exception as e:
			fnsLog(f'ColorUI: import failed: {e}', level='ERROR')
			self.Toast(f'Import failed: {e}')
			return
		valid = {k: v for k, v in data.items() if k in ui.colors}
		self._apply(valid, record=True)
		skipped = len(data) - len(valid)
		fnsLog(f'ColorUI: imported {len(valid)} colors from {path}'
			   + (f' ({skipped} unknown keys skipped)' if skipped else ''))
		self.Toast(f'Imported {len(valid)} colors'
				   + (f' · {skipped} unknown skipped' if skipped else ''))
		self.SendState()

	def DoExport(self, dialog=False):
		path = self.evalFile
		if dialog or not path:
			path = ui.chooseFile(load=False, start=path or None,
								 fileTypes=['json'], title='Export UI colors')
			if not path:
				return
		if not path.endswith('.json'):
			path += '.json'
		self.evalFile = path
		ov = self.Overrides
		try:
			with open(path, 'w', encoding='utf-8') as f:
				json.dump({k: list(v) for k, v in ov.items()}, f, indent=1)
		except Exception as e:
			fnsLog(f'ColorUI: export failed: {e}', level='ERROR')
			self.Toast(f'Export failed: {e}')
			return
		fnsLog(f'ColorUI: exported {len(ov)} colors to {path}')
		self.Toast(f'Exported {len(ov)} changed colors')

	def OpenUI(self):
		self.ownerComp.openViewer()

	# ------------------------------------------------------------ par callbacks

	def onParImport(self):
		self.DoImport()

	def onParExport(self):
		self.DoExport()

	def onParOpenui(self):
		self.OpenUI()

	def onParAutoload(self, _val):
		# keep the page checkbox in sync however the par was flipped
		self._js('window.FNS && FNS.setAutoload(' + ('true' if _val else 'false') + ')')

	def onParGroupby(self, _val):
		self._js('window.FNS && FNS.setGroupby(' + json.dumps(str(_val)) + ')')

	def onParFile(self, _file):
		if _file and not _file.endswith('.json'):
			self.evalFile = _file + '.json'
