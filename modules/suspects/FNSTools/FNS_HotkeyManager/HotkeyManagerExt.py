import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
import TDFunctions as TDF

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import
############

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log('HotkeyManager:', *args, level=level)
	except Exception:
		pass

KILL = False

# Modifier vocabulary: l/r variants normalize to their base for conflict grouping.
MODIFIER_ALIASES = {
	'lalt': 'alt', 'ralt': 'alt', 'alt': 'alt',
	'lctrl': 'ctrl', 'rctrl': 'ctrl', 'ctrl': 'ctrl',
	'lshift': 'shift', 'rshift': 'shift', 'shift': 'shift',
	'lcmd': 'cmd', 'rcmd': 'cmd', 'cmd': 'cmd',
}
MODIFIER_ORDER = ['ctrl', 'alt', 'shift', 'cmd']

TABLE_HEADERS = [
	"path", "par", "type", "_COMP_",
	"custom_val", "custom_expr",
	"_CHOP_",
	"chop_keys_val", "chop_keys_expr",
	"chop_modifiers_val", "chop_modifiers_expr",
	"_DAT_",
	"dat_keys_val", "dat_keys_expr",
	"dat_shortcuts_val", "dat_shortcuts_expr"
]

UI_HEADERS = ["Tool", "Path", "Par", "Hotkey", "Default", "Persist", "Status"]

DEFAULT_HINT = "click a Hotkey cell to rebind - right-click resets to default"


@dataclass
class HotkeyRecord:
	"""One hotkey-bearing parameter found in the project."""
	owner: 'OP'
	par_name: str
	kind: str  # 'COMP' | 'CHOP' | 'DAT'
	val: str = ""   # constant/bind value ("" when expression-driven)
	expr: str = ""  # externalizable os-switch expression ("" otherwise)

	@property
	def par(self) -> Optional['Par']:
		return getattr(self.owner.par, self.par_name, None)

	@property
	def current(self) -> str:
		"""Evaluated runtime value (what the binding IS right now)."""
		_par = self.par
		if _par is None:
			return ""
		try:
			return str(_par.eval())
		except Exception:
			return ""


class HotkeyManagerExt:
	"""Gathers, persists, restores and (via the HotkeyUI lister) edits every
	hotkey-bearing parameter under the FNS tools root. Discovery is a single
	routine shared by the watcher wiring, the externalize table and the UI."""

	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self._allHotkeys = tdu.Dependency([[None, None]])
		if KILL or not self.evalActive:
			return

		self.ownerComp = ownerComp

		self.keyboardin_chop_pars = ['keys', 'modifiers']
		self.keyboardin_dat_pars = ['keys', 'shortcuts']
		self.comp_pars_substrings = ['key', 'shortcut', 'hotkey']
		self.comp_pars_exceptions = ['opshortcut', 'parentshortcut', 'arrowkeys', 'savehotkeys', 'loadhotkeys', 'shortcutactive', 'deletekey']
		self.comp_except = ['popMenu', 'popDialog', 'KeyModifiers', 'FNS_HotkeyManager']
		# DAT `keys` values consisting only of these are modifier-listen setups, not hotkeys
		self.ignored_keys = ['ctrl', 'alt', 'shift', 'cmd', 'esc', 'enter', 'tab']

		# the toolkit container this package is installed in -- never the
		# dev root by name/shortcut, so a bare install resolves too
		self.searchRoot = self.ownerComp.parent()
		self.hotkeyTable: 'tableDAT' = self.ownerComp.op('table_gathered_hotkeys')
		self.defaultTable: 'tableDAT' = self.ownerComp.op('table_gathered_hotkeys1')
		self.supressWatch = False

		self._records: List[HotkeyRecord] = []
		self._conflicts = {}          # combo -> [HotkeyRecord]
		self._pendingChanges = {}     # (path_display, par_name) -> (prev, new)
		self._capture = None          # None or {'path':..., 'par':...} while rebinding
		self._jumpState = None        # cycles through conflict partners on repeated Status clicks

		# retired debug machinery from the old dual-discovery comparison
		for _key in ('propertyPaths', 'gatheredPaths', 'allHotkeyParsDebug', 'gatherParamsDebug'):
			self.ownerComp.unstore(_key)

		fnsLog("HotkeyManagerExt initialized")

	# ------------------------------------------------------------------
	# Discovery (single source of truth)
	# ------------------------------------------------------------------

	def _isModifierOnlyKeys(self, value: str) -> bool:
		"""True when a DAT `keys` value contains only modifier/ignored keys."""
		pattern = r'^(?:\s*(?:' + '|'.join(self.ignored_keys) + r')(?:\s+|$))*$'
		return re.match(pattern, value.lower()) is not None

	def _recordFromPar(self, _op: 'OP', par_name: str, kind: str) -> Optional[HotkeyRecord]:
		"""Capture one parameter as a HotkeyRecord, or None if it holds nothing
		externalizable. Constant/bind values are taken as-is; expressions only
		count when they follow the os-switch convention ('app.osName' in expr)."""
		_par = getattr(_op.par, par_name, None)
		if _par is None:
			return None
		if _par.mode in (ParMode.CONSTANT, ParMode.BIND):
			_raw = _par.eval()
			if not _raw:  # falsy RAW value (empty string, False, 0) is not a binding
				return None
			_val = str(_raw)
			if kind == 'DAT' and par_name == 'keys' and self._isModifierOnlyKeys(_val):
				return None
			return HotkeyRecord(_op, par_name, kind, val=_val)
		if _par.mode == ParMode.EXPRESSION and _par.expr and 'app.osName' in _par.expr:
			return HotkeyRecord(_op, par_name, kind, expr=_par.expr)
		return None

	def _isExcepted(self, _op: 'OP') -> bool:
		return any(_sub in _op.path for _sub in self.comp_except)

	def _isPanelScoped(self, _op: 'OP') -> bool:
		"""A keyboardin with a Panels filter only fires while those panels have
		focus -- that is a local control scheme, not a global hotkey."""
		p = getattr(_op.par, 'panels', None)
		if p is None:
			return False
		return bool((p.expr or '').strip() if p.mode == ParMode.EXPRESSION else str(p.val).strip())

	def _scanRoots(self) -> List['COMP']:
		"""Every top-level COMP under '/' except the Excluderoots names --
		hotkeys can conflict project-wide, so discovery is project-wide."""
		par = getattr(self.ownerComp.par, 'Excluderoots', None)
		excluded = set(str(par.eval()).split()) if par is not None else {'ui', 'sys', 'local'}
		roots = []
		for child in op('/').children:
			if not child.isCOMP or child.type == 'annotate':
				continue
			if child.name in excluded:
				continue
			roots.append(child)
		return roots

	def Discover(self) -> List[HotkeyRecord]:
		"""Scan every top-level COMP (minus excluded roots) for hotkey-bearing
		parameters. The tools root's CHILDREN are tools; other roots are each
		a tool themselves (their own custom pars are scanned too)."""
		records: List[HotkeyRecord] = []

		def scanComp(_comp: 'COMP'):
			for _par in _comp.customPars:
				if _par.style not in ('Str', 'StrMenu', 'Menu'):
					continue  # bindings live in string-valued pars; toggles like Enablekeyboardshortcuts are not bindings
				name_l = _par.name.lower()
				if any(_sub in name_l for _sub in self.comp_pars_exceptions):
					continue
				if not any(_sub in name_l for _sub in self.comp_pars_substrings):
					continue
				rec = self._recordFromPar(_comp, _par.name, 'COMP')
				if rec:
					records.append(rec)

		def scanTree(root: 'COMP', include_root: bool):
			for _op in root.findChildren(type=keyboardinCHOP):
				if self._isExcepted(_op) or self._isPanelScoped(_op):
					continue
				for par_name in self.keyboardin_chop_pars:
					rec = self._recordFromPar(_op, par_name, 'CHOP')
					if rec:
						records.append(rec)
			for _op in root.findChildren(type=keyboardinDAT):
				if self._isExcepted(_op) or self._isPanelScoped(_op):
					continue
				for par_name in self.keyboardin_dat_pars:
					rec = self._recordFromPar(_op, par_name, 'DAT')
					if rec:
						records.append(rec)
			if include_root and not self._isExcepted(root):
				scanComp(root)
			for _comp in root.findChildren(type=COMP):
				if self._isExcepted(_comp):
					continue
				scanComp(_comp)

		for root in self._scanRoots():
			scanTree(root, include_root=(root != self.searchRoot))

		# Bind followers mirror their master; list only the master (the editable
		# one). Followers whose master is NOT itself discovered are kept, so no
		# binding silently disappears from the list.
		discovered_keys = {(r.owner.path, r.par_name) for r in records}
		deduped = []
		for r in records:
			_par = r.par
			if _par is not None and _par.mode == ParMode.BIND:
				bm = getattr(_par, 'bindMaster', None)
				if bm is not None and hasattr(bm, 'owner') and hasattr(bm, 'name') \
						and (bm.owner.path, bm.name) in discovered_keys:
					continue
			deduped.append(r)
		records = deduped

		self._records = records
		fnsLog(f"Discover: {len(records)} hotkey parameters "
						f"({sum(1 for r in records if r.kind == 'CHOP')} CHOP, "
						f"{sum(1 for r in records if r.kind == 'DAT')} DAT, "
						f"{sum(1 for r in records if r.kind == 'COMP')} COMP)")
		return records

	def AllHotkeyPars(self) -> List[tuple]:
		"""(operator, parameter_name) tuples for the parexec watcher."""
		result = [(rec.owner, rec.par_name) for rec in self.Discover()]
		self._allHotkeys.val = result
		self.ownerComp.op('parexec1').cook(force=True)
		return result

	# ------------------------------------------------------------------
	# Path helpers (no eval)
	# ------------------------------------------------------------------

	def _getPathFromOP(self, _op: 'OP') -> str:
		p = _op.path
		root_p = self.searchRoot.path
		if p == root_p or p.startswith(root_p + '/'):
			return TDF.getShortcutPath(self.searchRoot, _op)  # compact legacy form for the tools package
		return p  # outside the tools package the full path is the unambiguous generic form

	def _displayFromStored(self, path_str: str) -> str:
		"""Normalize any stored path form to the UI display form:
		"op('./Tool/kb')" -> 'Tool/kb'; "op.Embody.op('x')" -> 'Embody/x'."""
		s = path_str.strip()
		if s.startswith('/'):
			return s[1:]
		m = re.fullmatch(r"op\(\s*['\"](.+?)['\"]\s*\)", s)
		if m:
			rel = m.group(1)
			return rel[2:] if rel.startswith('./') else rel
		m = re.fullmatch(r"op\.(\w+)(?:\.op\(\s*['\"](.+?)['\"]\s*\))?", s)
		if m:
			return m.group(1) + ('/' + m.group(2) if m.group(2) else '')
		return s

	def _resolveOP(self, path_str: str) -> Optional['OP']:
		"""Resolve a stored or display path -- root-relative forms against the
		search root, "op.Name..." forms via global shortcuts -- no eval."""
		s = path_str.strip()
		if s.startswith('/'):
			_op = op(s)
		else:
			m = re.fullmatch(r"op\.(\w+)(?:\.op\(\s*['\"](.+?)['\"]\s*\))?", s)
			if m:
				base = getattr(op, m.group(1), None)
				_op = base.op(m.group(2)) if (base is not None and m.group(2)) else base
			else:
				m = re.fullmatch(r"op\(\s*['\"](.+?)['\"]\s*\)", s)
				rel = m.group(1) if m else s
				_op = self.searchRoot.op(rel)
				if _op is None:
					# display form: try as a root-level path, then a global shortcut
					_op = op('/' + rel)
				if _op is None:
					seg, _, rest = rel.partition('/')
					base = getattr(op, seg, None)
					if base is not None:
						_op = base.op(rest) if rest else base
		if _op is None:
			fnsLog(f"Could not resolve operator for path {path_str}")
		return _op

	def _displayPath(self, _op: 'OP') -> str:
		"""Root-relative path for UI display: './MY_HOTKEYS/kb' -> 'MY_HOTKEYS/kb'."""
		return self._displayFromStored(self._getPathFromOP(_op))

	def _toolName(self, _op: 'OP') -> str:
		"""Grouping name for the UI: inside the tools package, the tool is the
		direct child of the package root; anywhere else it is the top-level
		COMP under '/' that contains the op."""
		node = _op
		while node.parent() is not None and node.parent() != self.searchRoot:
			if node.parent().path == '/':
				return node.name  # top-level COMP outside the tools package
			node = node.parent()
		return node.name if node.parent() == self.searchRoot else _op.name

	# ------------------------------------------------------------------
	# Conflict detection
	# ------------------------------------------------------------------

	def _combosFromRecord(self, rec: HotkeyRecord) -> set:
		"""Normalized key combos a record currently binds. Modifier-only values
		(hold-style bindings like 'alt') yield no combos -- they are shared by
		design and would drown real conflicts. Character classes like
		'ctrl.[0-9]' expand so overlaps with literal digits are caught."""
		value = rec.current
		if not value:
			return set()
		# CHOP keys pair with the op's modifiers menu par
		prefix_mods = []
		if rec.kind == 'CHOP':
			if rec.par_name == 'modifiers':
				return set()  # handled as prefix of the keys record
			mod_par = getattr(rec.owner.par, 'modifiers', None)
			if mod_par is not None:
				mod_val = str(mod_par.eval()).lower()
				if mod_val in MODIFIER_ALIASES:
					prefix_mods = [MODIFIER_ALIASES[mod_val]]
		combos = set()
		for token in value.split():
			parts = [p for p in re.split(r'[.+]', token) if p]  # '.' and '+' (Embody) separators
			mods = set(prefix_mods)
			keys = []
			for p in parts:
				p_l = p.lower()
				if p_l in MODIFIER_ALIASES:
					mods.add(MODIFIER_ALIASES[p_l])
				else:
					keys.append(p_l)
			if not keys:
				continue  # modifier-hold binding
			mod_part = [m for m in MODIFIER_ORDER if m in mods]
			for key in keys:
				try:
					expanded = tdu.expand(key) if ('[' in key and ']' in key) else [key]
				except Exception:
					expanded = [key]
				if len(expanded) > 20:
					expanded = [key]
				for k in expanded:
					combos.add('.'.join(mod_part + [k]))
		return combos

	def ComputeConflicts(self) -> dict:
		"""combo -> [records] for every combo bound by more than one tool."""
		by_combo = {}
		for rec in self._records:
			for combo in self._combosFromRecord(rec):
				by_combo.setdefault(combo, []).append(rec)
		self._conflicts = {
			combo: recs for combo, recs in by_combo.items()
			if len({self._toolName(r.owner) for r in recs}) > 1
		}
		if self._conflicts:
			for combo, recs in self._conflicts.items():
				owners = ', '.join(f"{self._displayPath(r.owner)}:{r.par_name}" for r in recs)
				fnsLog(f"CONFLICT {combo}: {owners}")
		return self._conflicts

	def _conflictComboFor(self, rec: HotkeyRecord) -> str:
		for combo, recs in self._conflicts.items():
			if rec in recs:
				return combo
		return ""

	def _comboOwners(self, combo: str) -> List[HotkeyRecord]:
		"""Every record currently binding this exact combo."""
		return [rec for rec in self._records if combo in self._combosFromRecord(rec)]

	def ShowConflictPartners(self, display_path: str, par_name: str):
		"""Surface who else binds this row's conflicted combo in the hint bar."""
		rec = next((r for r in self._records
					if self._displayPath(r.owner) == display_path and r.par_name == par_name), None)
		if rec is None:
			return
		combo = self._conflictComboFor(rec)
		if not combo:
			self._setHint()
			return
		partners = [f"{self._displayPath(r.owner)}:{r.par_name}"
					for r in self._conflicts.get(combo, []) if r is not rec]
		self._setHint(f"'{combo}' also bound by: " + ', '.join(partners))

	def JumpToConflictPartner(self, display_path: str, par_name: str):
		"""Select and scroll to the partner row of this row's conflicted combo;
		repeated clicks cycle through partners when there are several."""
		rec = next((r for r in self._records
					if self._displayPath(r.owner) == display_path and r.par_name == par_name), None)
		if rec is None:
			return
		combo = self._conflictComboFor(rec)
		if not combo:
			self._setHint()
			return
		partners = [r for r in self._conflicts.get(combo, []) if r is not rec]
		if not partners:
			return
		key = (display_path, par_name, combo)
		idx = 0
		if self._jumpState and self._jumpState.get('key') == key:
			idx = (self._jumpState['idx'] + 1) % len(partners)
		self._jumpState = {'key': key, 'idx': idx}
		target = partners[idx]
		t_path, t_par = self._displayPath(target.owner), target.par_name

		table = self.ownerComp.op('HotkeyUI/table_ui_hotkeys')
		lst = self.ownerComp.op('HotkeyUI/lister')
		if table is None or lst is None or not lst.extensions:
			return
		row = None
		for i in range(1, table.numRows):
			if table[i, 'Path'].val == t_path and table[i, 'Par'].val == t_par:
				row = i
				break
		if row is None:
			return
		le = lst.extensions[0]
		try:
			le.SelectRow(row)
		except Exception as e:
			fnsLog(f"SelectRow failed: {e}")
		try:
			lst.scroll(row, 0)
		except Exception:
			pass  # selection alone still highlights the partner
		suffix = f" ({idx + 1}/{len(partners)})" if len(partners) > 1 else ""
		self._setHint(f"'{combo}' partner{suffix}: {t_path}:{t_par}")

	# ------------------------------------------------------------------
	# Lifecycle / parameter callbacks
	# ------------------------------------------------------------------

	def onStart(self):
		self.AllHotkeys = self.AllHotkeyPars()
		fnsLog("Starting hotkeys initialization...")
		self.setAllHotkeys()
		self.ComputeConflicts()
		self.RefreshUI()
		fnsLog("Hotkey initialization complete")

	def onParSavehotkeys(self):
		self.SaveHotkeys()

	def onParLoadhotkeys(self):
		fnsLog("Loading hotkeys...")
		self._loadWithWatchSuppressed(default=False)

	def onParLoaddefault(self):
		fnsLog("Loading default hotkeys...")
		self._loadWithWatchSuppressed(default=True)
		self.hotkeyTable.clear()
		self.hotkeyTable.copy(self.defaultTable)

	def onParForcedefault(self, val):
		if val:
			self.onParLoaddefault()

	def _loadWithWatchSuppressed(self, default: bool):
		self.supressWatch = True
		self.setAllHotkeys(default=default)
		run(
			"args[0].supressWatch = False",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)
		self._pendingChanges = {}
		self.ComputeConflicts()
		self.RefreshUI()

	def onShortcutChanged(self, _par: 'Par', prev=None):
		"""Non-modal change watcher: log it, mark the row unsaved in the UI.
		Externalizing happens through Save (UI button or Savehotkeys pulse)."""
		if self.supressWatch:
			return
		try:
			new_val = str(_par.eval())
		except Exception:
			new_val = ""
		key = (self._displayPath(_par.owner), _par.name)
		self._pendingChanges[key] = (str(prev), new_val)
		fnsLog(
			f"Shortcut '{_par.owner.path}:{_par.name}' changed "
			f"from '{prev}' to '{new_val}' -- unsaved (Save externalizes it)")
		self.ComputeConflicts()
		self.RefreshUI()

	# ------------------------------------------------------------------
	# Externalize / restore
	# ------------------------------------------------------------------

	def SaveHotkeys(self):
		"""Externalize the current live bindings into the gathered table."""
		fnsLog("Saving hotkeys...")
		self.gatherAllHotkeys()
		self._pendingChanges = {}
		self.RefreshUI()

	def gatherAllHotkeys(self):
		"""Write the discovery result into table_gathered_hotkeys (legacy
		16-column schema, one row per CHOP/DAT op, one row per COMP par)."""
		table: 'tableDAT' = self.hotkeyTable
		table.clear()
		table.appendRow(TABLE_HEADERS)

		records = self.Discover()

		# group CHOP/DAT records per owner so keys+modifiers / keys+shortcuts share a row
		grouped = {}
		order = []
		for rec in records:
			gkey = (rec.owner, rec.kind) if rec.kind in ('CHOP', 'DAT') else (rec.owner, rec.kind, rec.par_name)
			if gkey not in grouped:
				grouped[gkey] = []
				order.append(gkey)
			grouped[gkey].append(rec)

		for gkey in order:
			recs = grouped[gkey]
			kind = recs[0].kind
			row = {h: "" for h in TABLE_HEADERS}
			row["path"] = self._getPathFromOP(recs[0].owner)
			row["type"] = kind
			if kind == 'COMP':
				row["par"] = recs[0].par_name
				row["custom_val"] = recs[0].val
				row["custom_expr"] = recs[0].expr
			elif kind == 'CHOP':
				row["par"] = ', '.join(self.keyboardin_chop_pars)
				for rec in recs:
					row[f"chop_{rec.par_name}_val"] = rec.val
					row[f"chop_{rec.par_name}_expr"] = rec.expr
			elif kind == 'DAT':
				row["par"] = ', '.join(self.keyboardin_dat_pars)
				for rec in recs:
					row[f"dat_{rec.par_name}_val"] = rec.val
					row[f"dat_{rec.par_name}_expr"] = rec.expr
			table.appendRow([row[h] for h in TABLE_HEADERS])

		fnsLog(f"Externalized {table.numRows - 1} hotkey rows")
		return table

	def setAllHotkeys(self, default=False):
		"""Restore bindings from the gathered (or default) table onto the ops."""
		fnsLog("Setting all hotkeys...")
		hotkeyTable = self.hotkeyTable if not (self.evalForcedefault or default) else self.defaultTable
		headers = [h.val for h in hotkeyTable.row(0)]
		success = 0

		for row_idx in range(1, hotkeyTable.numRows):
			_data = dict(zip(headers, [c.val for c in hotkeyTable.row(row_idx)]))
			_op = self._resolveOP(_data.get('path', ''))
			if _op is None:
				continue

			_type = _data.get('type', '')
			applied = 0
			for _par_name in _data.get('par', '').split(', '):
				_par = getattr(_op.par, _par_name, None)
				if _par is None:
					fnsLog(f"No parameter '{_par_name}' found on operator {_op}")
					continue
				if _type == "COMP":
					col_prefix = "custom"
				else:
					col_prefix = f"{_type.lower()}_{_par_name}"
				_val = _data.get(f"{col_prefix}_val", '')
				_expr = _data.get(f"{col_prefix}_expr", '')
				if _expr:
					_par.expr = _expr
					applied += 1
				elif _val:
					_par.val = _val
					applied += 1
			if applied:
				success += 1

		fnsLog(f"Successfully loaded {success} hotkeys")

	# ------------------------------------------------------------------
	# Config persistence (ConfigRegistry pilot)
	# ------------------------------------------------------------------

	# Explicit declaration tag: a keyboardin CHOP/DAT or a COMP carrying it
	# (or living inside a COMP carrying it) opts its hotkeys into the
	# user-level config file even when it sits outside the FNS tools package.
	CONFIG_TAG = 'FNS_hotkeys'

	def _isPackageSource(self, _op) -> bool:
		"""Inside the FNS tools package: ALWAYS persisted, not user-toggleable
		-- tool hotkeys surviving updates is the whole point."""
		if _op is None:
			return False
		root_p = self.searchRoot.path
		return _op.path == root_p or _op.path.startswith(root_p + '/')

	def _tagCarrier(self, _op):
		"""The op whose CONFIG_TAG declares this source (itself or the nearest
		tagged ancestor), or None when undeclared."""
		node = _op
		while node is not None and node.path != '/':
			if self.CONFIG_TAG in node.tags:
				return node
			node = node.parent()
		return None

	def _isDeclaredSource(self, _op) -> bool:
		"""Rows persisted to the config file: anything under the tools root
		(implicitly declared), or anything carrying/inside the CONFIG_TAG.
		Project-local bindings (an untagged /project1 keyboardin) never
		persist -- the same path means something else in every project."""
		if _op is None:
			return False
		if self._isPackageSource(_op):
			return True
		return self._tagCarrier(_op) is not None

	def TogglePersist(self, display_path: str, par_name: str) -> bool:
		"""Persist-column click: flip the CONFIG_TAG on the row's source op.
		FNS-package rows are refused -- tool hotkeys always persist. Returns
		the new declared state."""
		_op = self._resolveOP(display_path)
		if _op is None:
			return False
		if self._isPackageSource(_op):
			self._setHint(f'{display_path}: FNS tool hotkeys always persist')
			return True
		carrier = self._tagCarrier(_op)
		if carrier is None:
			_op.tags.add(self.CONFIG_TAG)
			self._setHint(f"{display_path}: hotkeys now persist to the config file "
						  f"('{self.CONFIG_TAG}' tag added)")
			declared = True
		elif carrier is _op:
			_op.tags.remove(self.CONFIG_TAG)
			still = self._tagCarrier(_op)
			if still is not None:
				self._setHint(f'{display_path}: still persisted -- {still.path} '
							  f"carries '{self.CONFIG_TAG}'")
				declared = True
			else:
				self._setHint(f'{display_path}: hotkeys are project-local again')
				declared = False
		else:
			# declared through an ancestor's tag: removing it here would change
			# every sibling under that ancestor -- make the user do that at the
			# carrier, deliberately
			self._setHint(f"{display_path}: persisted via '{self.CONFIG_TAG}' on "
						  f'{carrier.path} -- remove the tag there to opt out')
			declared = True
		fnsLog(f'TogglePersist {display_path}: declared={declared}')
		self.RefreshUI()
		return declared

	def ConfigSaveRows(self) -> dict:
		"""Declared rows of the gathered table, for config_callbacks
		onConfigSave. Rows that arrived from the config file but never
		resolved in THIS project ride along unchanged, so switching projects
		cannot silently drop another project's declared bindings."""
		table = self.hotkeyTable
		if table is None or table.numRows < 1:
			return {}
		headers = [h.val for h in table.row(0)]
		rows = []
		for row_idx in range(1, table.numRows):
			vals = [c.val for c in table.row(row_idx)]
			_data = dict(zip(headers, vals))
			_op = self._resolveOP(_data.get('path', ''))
			if _op is not None and self._isDeclaredSource(_op):
				rows.append(vals)
		try:
			path_col, par_col = headers.index('path'), headers.index('par')
		except ValueError:
			return {}
		known = {(r[path_col], r[par_col]) for r in rows}
		for key, vals in getattr(self, '_config_orphan_rows', {}).items():
			if key not in known and len(vals) == len(headers):
				rows.append(list(vals))
		if not rows:
			return {}
		return {'headers': headers, 'rows': rows}

	def ConfigLoadRows(self, data) -> int:
		"""Merge config rows into the gathered table -- update by path+par,
		insert unknown, remember unresolvable rows as orphans, leave every
		project-local row untouched -- then apply through the standard load
		path (watch suppressed)."""
		headers_in = list(data.get('headers') or [])
		rows = data.get('rows') or []
		if not rows:
			return 0
		if headers_in != TABLE_HEADERS:
			fnsLog('Config hotkey rows ignored: table schema mismatch')
			return 0
		table = self.hotkeyTable
		if table.numRows < 1:
			table.appendRow(TABLE_HEADERS)
		path_col, par_col = TABLE_HEADERS.index('path'), TABLE_HEADERS.index('par')
		existing = {}
		for row_idx in range(1, table.numRows):
			vals = [c.val for c in table.row(row_idx)]
			existing[(vals[path_col], vals[par_col])] = row_idx
		self._config_orphan_rows = {}
		merged = 0
		for vals in rows:
			if len(vals) != len(TABLE_HEADERS):
				continue
			vals = [str(v) for v in vals]
			key = (vals[path_col], vals[par_col])
			_op = self._resolveOP(vals[path_col])
			if _op is None:
				# not present in this project: keep for the next save, skip apply
				self._config_orphan_rows[key] = vals
				continue
			row_idx = existing.get(key)
			if row_idx is None:
				table.appendRow(vals)
			else:
				for col, v in enumerate(vals):
					table[row_idx, col] = v
			merged += 1
		if merged:
			fnsLog(f'Config: merged {merged} declared hotkey row(s), '
							f'{len(self._config_orphan_rows)} kept unresolved')
			self._loadWithWatchSuppressed(default=False)
		return merged

	# ------------------------------------------------------------------
	# Defaults
	# ------------------------------------------------------------------

	def _parDefault(self, par: 'Par') -> str:
		"""A custom par's OWN shipped default, as a display string.

		Custom pars carry their default with them (Par.default / .defaultExpr /
		.defaultBindExpr, selected by .defaultMode), so the default survives the
		op being renamed or reparented -- which a path-keyed table row does not.
		Returns "" for built-in pars, whose factory default is empty/'ignore'
		and would UNBIND the hotkey rather than restore it."""
		if par is None or not par.isCustom:
			return ""
		try:
			mode = par.defaultMode
			if mode == ParMode.BIND:
				return par.defaultBindExpr or ""
			if mode == ParMode.EXPRESSION:
				return par.defaultExpr or ""
			return str(par.default or "")
		except Exception:
			return ""

	def _defaultsMap(self) -> dict:
		"""(display_path, par_name) -> default display value, from the default table."""
		defaults = {}
		if self.defaultTable is None or self.defaultTable.numRows < 2:
			return defaults
		headers = [h.val for h in self.defaultTable.row(0)]
		for row_idx in range(1, self.defaultTable.numRows):
			_data = dict(zip(headers, [c.val for c in self.defaultTable.row(row_idx)]))
			rel = self._displayFromStored(_data.get('path', ''))
			_type = _data.get('type', '')
			for _par_name in _data.get('par', '').split(', '):
				col_prefix = "custom" if _type == "COMP" else f"{_type.lower()}_{_par_name}"
				_val = _data.get(f"{col_prefix}_val", '')
				_expr = _data.get(f"{col_prefix}_expr", '')
				defaults[(rel, _par_name)] = _val or _expr
			# whole-row lookup for reset
			defaults[(rel, '__row__')] = _data
		return defaults

	def ResetToDefault(self, display_path: str, par_name: str) -> bool:
		"""Restore one binding to its default.

		A custom par owns its default, so Par.reset() restores value, expression,
		bind expression and mode as a unit -- and keeps working after the op is
		renamed or moved. The default table is the fallback for keyboardin
		built-ins, which cannot carry an authored default."""
		_op = self._resolveOP(display_path)
		_par = getattr(_op.par, par_name, None) if _op is not None else None
		if _par is not None and self._parDefault(_par):
			_par.reset()
			fnsLog(f"Reset {display_path}:{par_name} to its Par default")
			return True

		defaults = self._defaultsMap()
		row = defaults.get((display_path, '__row__'))
		if row is None:
			fnsLog(f"No default recorded for {display_path}")
			return False
		_op = self._resolveOP(row.get('path', ''))
		if _op is None:
			return False
		_par = getattr(_op.par, par_name, None)
		if _par is None:
			return False
		_type = row.get('type', '')
		col_prefix = "custom" if _type == "COMP" else f"{_type.lower()}_{par_name}"
		_val = row.get(f"{col_prefix}_val", '')
		_expr = row.get(f"{col_prefix}_expr", '')
		if _expr:
			_par.expr = _expr
		elif _val:
			_par.val = _val
		else:
			return False
		fnsLog(f"Reset {display_path}:{par_name} to default")
		return True

	# ------------------------------------------------------------------
	# Rebind capture
	# ------------------------------------------------------------------

	def _setHint(self, msg: Optional[str] = None):
		hint = self.ownerComp.op('HotkeyUI/txt_hint')
		if hint is not None:
			hint.par.text = msg or DEFAULT_HINT

	def BeginCapture(self, display_path: str, par_name: str):
		"""Arm the capture keyboardin; next non-modifier keypress becomes the binding."""
		kb = self.ownerComp.op('HotkeyUI/keyboardin_capture')
		if kb is None:
			fnsLog("No capture keyboardin found")
			return
		self._capture = {'path': display_path, 'par': par_name}
		kb.par.active = True
		self._setHint(f"press keys for {display_path}:{par_name} (Esc cancels)")
		fnsLog(f"Capturing new binding for {display_path}:{par_name} "
						"(press keys, Esc cancels)")
		self.RefreshUI()

	def CancelCapture(self):
		kb = self.ownerComp.op('HotkeyUI/keyboardin_capture')
		if kb is not None:
			kb.par.active = False
		self._capture = None
		self._setHint()
		self.RefreshUI()

	def OnCaptureKey(self, key, character, alt, ctrl, shift, state, cmd=False):
		"""Called by the capture keyboardin's onKey callback. If the captured
		combo is already bound elsewhere, hold the capture open and require the
		same combo a second time to force it (Esc cancels)."""
		if self._capture is None or not state:
			return
		k = str(key)
		if k.lower() in MODIFIER_ALIASES:
			return  # keep waiting for the trigger key
		if k.lower() == 'esc':
			self.CancelCapture()
			return
		mods = [m for m, on in (('ctrl', ctrl), ('alt', alt), ('shift', shift), ('cmd', cmd)) if on]
		combo = '.'.join(mods + [k.lower() if len(k) == 1 else k])
		target = self._capture

		others = [r for r in self._comboOwners(combo)
				  if not (self._displayPath(r.owner) == target['path'] and r.par_name == target['par'])]
		if others and target.get('force_combo') != combo:
			target['force_combo'] = combo
			owners = ', '.join(sorted({f"{self._displayPath(r.owner)}:{r.par_name}" for r in others}))
			self._setHint(f"'{combo}' taken by {owners} -- same keys again to force, Esc cancels")
			fnsLog(f"Capture: '{combo}' already bound by {owners}; awaiting confirm")
			self.RefreshUI()
			return

		self._capture = None
		kb = self.ownerComp.op('HotkeyUI/keyboardin_capture')
		if kb is not None:
			kb.par.active = False
		self._setHint()
		self.ApplyBinding(target['path'], target['par'], combo)

	def ApplyBinding(self, display_path: str, par_name: str, combo: str) -> bool:
		"""Write a new combo onto a binding. Expression-driven os-switch bindings
		keep their structure (Windows half = combo, mac half swaps ctrl->cmd);
		everything else becomes a constant value."""
		_op = self._resolveOP(display_path)
		if _op is None:
			return False
		_par = getattr(_op.par, par_name, None)
		if _par is None:
			fnsLog(f"No parameter '{par_name}' on {display_path}")
			return False
		if _par.mode == ParMode.EXPRESSION and _par.expr and 'app.osName' in _par.expr:
			win = combo
			mac = combo.replace('ctrl', 'cmd')
			_par.expr = f"'{win}' if app.osName == 'Windows' else '{mac}'"
		else:
			if _par.mode == ParMode.BIND:
				fnsLog(f"NOTE: {display_path}:{par_name} was bind-mode; now constant")
			# preserve the par's separator convention (Embody uses 'cmd+shift+o')
			current = str(_par.eval())
			if '+' in current and '.' not in current:
				combo = combo.replace('.', '+')
			if _par.style == 'Menu' and combo not in _par.menuNames:
				self._setHint(f"{display_path}:{par_name} is a menu par -- valid: {' '.join(_par.menuNames)}")
				fnsLog(f"Declined: '{combo}' not a menu option of {display_path}:{par_name}")
				return False
			_par.val = combo
		fnsLog(f"Bound {display_path}:{par_name} = {combo}")
		# watcher marks it pending; recompute + refresh happen there unless suppressed
		if self.supressWatch:
			self.ComputeConflicts()
			self.RefreshUI()
		return True

	# ------------------------------------------------------------------
	# UI
	# ------------------------------------------------------------------

	def OpenUI(self):
		ui_comp = self.ownerComp.op('HotkeyUI')
		if ui_comp is None:
			fnsLog("HotkeyUI not built yet")
			return
		self.Discover()
		self.ComputeConflicts()
		self.RefreshUI()
		ui_comp.openViewer(unique=True, borders=True)

	def onParOpenui(self):
		self.OpenUI()

	def _displayValue(self, value: str) -> str:
		"""Compact display form: os-switch expressions show their Windows branch."""
		if 'app.osName' in value:
			m = re.match(r"^\s*['\"](.+?)['\"]\s+if\s+app\.osName", value)
			if m:
				return m.group(1)
		return value

	def RefreshUI(self):
		"""Rebuild the UI table the lister displays. Safe no-op when absent."""
		table = self.ownerComp.op('HotkeyUI/table_ui_hotkeys')
		if table is None:
			return
		defaults = self._defaultsMap()
		table.clear()
		table.appendRow(UI_HEADERS)
		cap = self._capture
		for rec in sorted(self._records, key=lambda r: (self._toolName(r.owner).lower(), r.par_name)):
			if rec.kind == 'CHOP' and rec.par_name == 'modifiers':
				continue  # folded into the keys row's combo display
			path_d = self._displayPath(rec.owner)
			# a custom par's own default wins -- it follows the op through renames
			# and moves, where the path-keyed table row goes stale
			default_v = self._displayValue(
				self._parDefault(rec.par) or defaults.get((path_d, rec.par_name), ""))
			status = ""
			if cap and cap['path'] == path_d and cap['par'] == rec.par_name:
				if cap.get('force_combo'):
					status = f"'{cap['force_combo']}' taken -- again to force"
				else:
					status = "press keys... (Esc cancels)"
			else:
				combo = self._conflictComboFor(rec)
				if combo:
					status = f"CONFLICT ({combo})"
				if (path_d, rec.par_name) in self._pendingChanges:
					status = (status + " " if status else "") + "unsaved"
			if self._isPackageSource(rec.owner):
				persist_v = "always"
			else:
				persist_v = "yes" if self._isDeclaredSource(rec.owner) else "no"
			table.appendRow([
				self._toolName(rec.owner),
				path_d,
				rec.par_name,
				rec.current,
				default_v,
				persist_v,
				status,
			])

	def RefreshAll(self):
		"""Full re-scan + UI rebuild (UI Refresh button)."""
		self.AllHotkeyPars()
		self.ComputeConflicts()
		self.RefreshUI()

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Open hotkey UI')
	def OpenHotkeyUI(self):
		"""Open the hotkey manager lister."""
		self.OpenUI()
		return {'ok': True}

	@FNSCommand.fns_command(label='Save hotkeys')
	def SaveHotkeysCmd(self):
		"""Save the current hotkey bindings."""
		self.ownerComp.par.Savehotkeys.pulse()
		return {'ok': True}

	@FNSCommand.fns_command(label='Load hotkeys')
	def LoadHotkeysCmd(self):
		"""Load the saved hotkey bindings."""
		self.ownerComp.par.Loadhotkeys.pulse()
		return {'ok': True}
