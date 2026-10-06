'''Info Header Start
Name : FamilyCommandsExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
"""Quick-launch commands for the FNS operator family (docs/OperatorFamilyFromStore.md).

TDFam's own Stubs pulses ask before they act and report in modal dialogs,
which is right behind a button and wrong on any path a script, a palette or
an agent can reach. These commands call the same batch methods without a
dialog and return what happened.
"""
from typing import Optional

FNSCommand = next(d for d in me.docked if d.name == 'FNSCommand').module


class FamilyCommandsExt:
	"""Stub, restore, update and resync the FNS family's placed operators."""

	def __init__(self, ownerComp: COMP) -> None:
		self.ownerComp = ownerComp

	def onInitTD(self) -> None:
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)
		# The updater keeps no family folder where the family is not
		# installed, so the family asks for one when it arrives (after the
		# TDFam registry has registered it).
		run('args[0]._syncOnArrival()', self, delayFrames=120, delayRef=op.TDResources)

	def _syncOnArrival(self) -> None:
		upd = getattr(op, 'FNS_UPDATER', None)
		if upd is not None and hasattr(upd, 'SyncFamilyFolder'):
			upd.SyncFamilyFolder()

	def _announceCommands(self) -> None:
		FNSCommand.announce(self.ownerComp)

	# ------------------------------------------------------------------
	# helpers
	# ------------------------------------------------------------------

	def _family(self):
		"""TDFam's installer ext on this COMP, or None before it is built."""
		try:
			return self.ownerComp.ext.OpFamExt
		except Exception:
			return None

	def _scope(self, only_current_network: bool) -> Optional[COMP]:
		if not only_current_network:
			return None
		pane = ui.panes.current
		owner = getattr(pane, 'owner', None) if pane is not None else None
		return owner if owner is not None and owner.isCOMP else None

	def _placed(self, ops_) -> list:
		"""Drop anything inside the toolkit container: masters and doorstep
		copies belong to the FNS updater (the callbacks DAT guards TDFam's own
		pulses the same way)."""
		home = self.ownerComp.parent()
		if home is None or home.path == '/':
			return list(ops_)
		pre = home.path + '/'
		return [o for o in ops_ if not o.path.startswith(pre)]

	def _installer(self) -> Optional[COMP]:
		"""The FNS_Installer beside this family, when it can remove it."""
		home = self.ownerComp.parent()
		inst = home.op('FNS_Installer') if home is not None else None
		return inst if inst is not None and hasattr(inst, 'RemoveFamily') else None

	def _refused(self, why: str) -> dict:
		debug('FNS_OpFamily: ' + why)
		return {'ok': False, 'why': why}

	# ------------------------------------------------------------------
	# commands
	# ------------------------------------------------------------------

	@FNSCommand.fns_command(help='Turn every placed FNS operator into a light stub that keeps its wiring and retained parameters')
	def StubFamilyOperators(self, only_current_network: bool = False) -> dict:
		fam = self._family()
		if fam is None or not getattr(fam, 'fam_registry', None):
			return self._refused('the FNS family is not registered')
		scope = self._scope(only_current_network)
		ops_ = self._placed(fam._find_family_operators(scope=scope, include_stubs=False) or [])
		if not ops_:
			return {'ok': True, 'stubbed': 0, 'why': 'no FNS operators found'}
		stubs = fam._create_stubs_batch(ops_) or []
		return {'ok': True, 'stubbed': len(stubs)}

	@FNSCommand.fns_command(help='Bring every FNS stub back as the full operator from the family folder')
	def ReplaceFamilyStubs(self, only_current_network: bool = False) -> dict:
		fam = self._family()
		if fam is None or not getattr(fam, 'fam_registry', None):
			return self._refused('the FNS family is not registered')
		stubs = self._placed(fam._find_stubs(scope=self._scope(only_current_network)) or [])
		if not stubs:
			return {'ok': True, 'replaced': 0, 'why': 'no FNS stubs found'}
		back = fam._replace_stubs_batch(stubs) or []
		missing = len(stubs) - len(back)
		out = {'ok': missing == 0, 'replaced': len(back)}
		if missing:
			out['why'] = ('%d stub(s) have no operator in the family folder: the store '
						  'does not hold that package on this machine' % missing)
		return out

	@FNSCommand.fns_command(help='Upgrade placed FNS operators to the newest version in the family folder, keeping retained parameters and state')
	def UpdateFamilyOperators(self, only_current_network: bool = False) -> dict:
		fam = self._family()
		if fam is None or not getattr(fam, 'fam_registry', None):
			return self._refused('the FNS family is not registered')
		ops_ = self._placed(fam._find_family_operators(scope=self._scope(only_current_network), include_stubs=False) or [])
		if not ops_:
			return {'ok': True, 'updated': 0, 'why': 'no FNS operators found'}
		analysis = fam._analyze_for_update(ops_) or {}
		todo = analysis.get('updateable') or []
		if not todo:
			return {'ok': True, 'updated': 0, 'why': 'every FNS operator is current',
					'unmatched': len(analysis.get('without_matches') or [])}
		res = fam._update_batch(todo) or {}
		return {'ok': not res.get('errors'), 'updated': len(res.get('updated') or []),
				'skipped': len(res.get('skipped') or []), 'errors': len(res.get('errors') or []),
				'unmatched': len(analysis.get('without_matches') or [])}

	@FNSCommand.fns_command(help='Take the FNS tab out of the OP Create dialog and keep it off; your FNS tools stay installed. Pick Tools turns it back on')
	def RemoveOperatorFamily(self) -> dict:
		inst = self._installer()
		if inst is None:
			return self._refused('no FNS installer beside the family; untick "Add FNS tab to OP Create" in Pick Tools instead')
		check = inst.RemoveFamily(confirm=False)
		if not check.get('ok') or not check.get('would_remove'):
			return check
		# the removal destroys this COMP, so it runs after the command returns
		run('args[0].valid and args[0].RemoveFamily()', inst, delayFrames=1, delayRef=op.TDResources)
		return {'ok': True, 'removing': check['would_remove']}

	@FNSCommand.fns_command(help="Mirror the store's family members into the family folder now")
	def SyncFamilyFromStore(self) -> dict:
		upd = getattr(op, 'FNS_UPDATER', None)
		if upd is None or not hasattr(upd, 'SyncFamilyFolder'):
			return self._refused('FNS_Updater is not in this project; the family folder is kept by the updater')
		return upd.SyncFamilyFolder()
