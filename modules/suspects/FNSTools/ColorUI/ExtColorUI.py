'''Info Header Start
Name : ExtColorUI
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
Saveversion : 2025.33070
Info Header End'''


CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

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

	# ------------------------------------------------------------ exposure
	# When the FNS_Console host exposes this tool, the console serves the
	# page and switches the local Web Render off itself (the host's Local
	# Browser par names it) -- that policy lives in the console so every
	# contributor gets it. What is ColorUI's own: exposed = the console IS
	# the UI, so Open UI goes there, and nothing is pushed at or kicked on a
	# renderer that is off.

	def _exposed(self):
		p = getattr(self.ownerComp.par, 'Csautoregister', None)
		if p is None:
			return False   # no console host on this tool: local is all there is
		try:
			return bool(p.eval())
		except Exception:
			return False

	def _localActivePar(self):
		wb = self.ownerComp.op('webBrowser')
		return getattr(wb.par, 'Active', None) if wb is not None else None

	def _localActive(self):
		p = self._localActivePar()
		try:
			return bool(p.eval()) if p is not None else False
		except Exception:
			return False

	def _js(self, code):
		if not self._localActive():
			return   # exposed: the console page polls; there is nothing to push at
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
		if self._gotReady or tries <= 0 or not self._localActive():
			return
		wr = self._wr
		if wr is not None:
			try:
				wr.par.reloadsrc.pulse()
			except Exception:
				pass
		run(f"op('{self.ownerComp.path}').ext.ExtColorUI._Kick({tries - 1})",
			delayFrames=180, fromOP=self.ownerComp)

	def _statePayload(self):
		"""Everything the page renders from, one dict -- pushed into the
		in-TD browser by SendState, handed back over HTTP by ConsoleState."""
		if not self.defaults:
			# ext was reinitialized mid-session; treat the live palette as baseline
			self._snapshotDefaults()
		rnd = lambda v: [round(float(c), 4) for c in v[:3]]
		return {
			'families': self.families,
			'colors': {k: rnd(ui.colors[k]) for k in ui.colors},
			'defaults': {k: rnd(v) for k, v in self.defaults.items()},
			'overrides': sorted(self.Overrides),
			'autoload': bool(self.evalAutoload),
			'groupby': self.evalGroupby,
			'randomized': self._randomized,
			'version': self.ownerComp.par.Pkgversion.eval(),
		}

	def SendState(self):
		self._sendCall('setState', self._statePayload())

	def Toast(self, text):
		# a console request in flight collects its toasts for the HTTP answer;
		# the in-TD browser gets them regardless
		sink = getattr(self, '_toast_sink', None)
		if sink is not None:
			sink.append(str(text))
		self._js('window.FNS && FNS.toast(' + json.dumps(str(text)) + ')')

	# --------------------------------------------------------- console tab
	# The same webui.html, served by FNS_Console under /t/ColorUI/, talks
	# over HTTP instead of the title/executeJavaScript bridge: commands POST
	# here and get the fresh state back; a light poll keeps it current when
	# the in-TD panel (or TD itself) changes colors.

	def ConsoleState(self):
		return {'ok': True, 'state': self._statePayload()}

	def ConsoleCommand(self, msg):
		"""One page->TD message, same vocabulary as the title bridge
		(_dispatch), answered with the resulting state plus any toasts the
		command raised."""
		if not isinstance(msg, dict):
			return {'ok': False, 'why': 'command must be a JSON object'}
		self._toast_sink = []
		try:
			self._dispatch(msg)
		except Exception as e:
			toasts, self._toast_sink = self._toast_sink, None
			return {'ok': False, 'why': str(e), 'toasts': toasts}
		toasts, self._toast_sink = self._toast_sink, None
		return {'ok': True, 'state': self._statePayload(), 'toasts': toasts}

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
		"""Exposed: the console is the UI, open its ColorUI tab. Local (or
		no console to go to): the in-TD panel, renderer on."""
		if self._exposed():
			con = getattr(op, 'FNS_CONSOLE', None)
			if con is not None and con.valid:
				res = con.Open(tab='ColorUI')
				if isinstance(res, dict) and res.get('ok'):
					return
				fnsLog(f'ColorUI: console did not open ({res}); falling back to the panel',
					   level='WARNING')
			else:
				fnsLog('ColorUI: exposed but no FNS_Console -- opening the panel', level='WARNING')
			p = self._localActivePar()
			if p is not None and not p.eval():
				p.val = True
				self._gotReady = False
				self._Kick(4)
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

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Open color UI')
	def OpenColorUI(self):
		"""Open the TouchDesigner UI color editor."""
		self.OpenUI()
		return {'ok': True}

	@FNSCommand.fns_command(label='Randomize colors')
	def RandomizeColors(self):
		"""Randomize the UI colors."""
		self.Randomize()
		return {'ok': True}

	@FNSCommand.fns_command(label='Undo randomize')
	def UndoRandomize(self):
		"""Undo the last color randomization."""
		self.UndoRandom()
		return {'ok': True}

	@FNSCommand.fns_command(label='Reset all colors', hidden=True)
	def ResetAllColors(self):
		"""Reset every UI color to its default."""
		self.ResetAll()
		return {'ok': True}

	@FNSCommand.fns_command(label='Import color palette', hidden=True)
	def ImportPalette(self):
		"""Import a UI color palette from file."""
		self.DoImport()
		return {'ok': True}

	@FNSCommand.fns_command(label='Export color palette', hidden=True)
	def ExportPalette(self):
		"""Export the current UI colors to file."""
		self.DoExport()
		return {'ok': True}
