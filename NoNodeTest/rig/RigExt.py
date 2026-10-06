"""RigExt -- a minimal NoNode consumer, used only by nonode_harness.

Registers one CHOP exec and one DAT exec and counts every callback it
receives. The harness then renames / moves / copies the watched operators and
asks whether the registrations survived.
"""

NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import


class RigExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.Calls = {}
		NoNode.Init(ownerComp, enable_chopexec=True, enable_datexec=True,
					enable_parexec=True, enable_keyboard_shortcuts=False)
		self.Register()
		self.Harvest = NoNode.HarvestCallbacks(self)
		# BOTH systems live on this COMP, which is the realistic shape and the
		# one that answers "can a decorator coexist with CustomParHelper".
		CustomParHelper.Init(self, ownerComp)

	def Register(self):
		"""Register against whatever currently answers to the watched names."""
		chop = self.ownerComp.op('chop_watched')
		dat = self.ownerComp.op('dat_watched')
		if chop is not None:
			NoNode.RegisterChopExec(NoNode.ChopExecType.ValueChange,
									chop, 'chan1', self.onChopValue)
		if dat is not None:
			NoNode.RegisterDatExec(NoNode.DatExecType.TableChange,
								   dat, self.onDatTable)

	# --- declarative registration -----------------------------------------
	# The decorated half of the rig. Targets are STRINGS resolved at harvest:
	# a class body runs before any COMP exists, so op('chop_deco') here would
	# resolve against nothing. Each decorated method counts under its own key
	# so it cannot be confused with the imperative registrations above.

	@NoNode.onChopExec(NoNode.ChopExecType.ValueChange, 'chop_deco', 'chan1')
	def decoChopValue(self, channel, val):
		self._bump('deco_chop')

	@NoNode.onDatExec(NoNode.DatExecType.TableChange, 'dat_deco')
	def decoDatTable(self, dat):
		self._bump('deco_dat')

	# owner OMITTED -- defaults to the extension's own COMP. This is the case
	# that overlaps CustomParHelper, which watches every custom par already.
	@NoNode.onParExec(NoNode.ParExecType.ValueChange, None, 'Speed')
	def decoOwnPar(self, par, val):
		self._bump('deco_ownpar')

	@NoNode.onParExec(NoNode.ParExecType.ValueChange, 'chop_deco', 'value0')
	def decoParValue(self, par, val):
		self._bump('deco_par')

	# --- CustomParHelper declarative callbacks ----------------------------
	# Freely-named handlers: none of these could be found by the onPar<Name>
	# convention. onParSpeed below stays as the convention's own case, so both
	# styles are exercised on one extension.

	@CustomParHelper.onPar('Gain')
	def gainMoved(self, _par, _val, _prev):
		self._bump('cph_deco_gain')

	@CustomParHelper.onPar('Reset')
	def doTheReset(self, _par):
		self._bump('cph_deco_reset')

	@CustomParHelper.onParGroup('Trans')
	def transMoved(self, _parGroup, _val):
		self._bump('cph_deco_trans')

	def onParSpeed(self, val):
		"""CustomParHelper's NAME convention, on the same parameter that also
		carries an @onParExec decorator. Both must fire, independently."""
		self._bump('cph_speed')

	def _bump(self, key):
		debug(key)
		self.Calls[key] = self.Calls.get(key, 0) + 1

	def onChopValue(self, channel, val):
		self._bump('chop')

	def onDatTable(self, dat):
		self._bump('dat')

	def onParValue(self, par, val):
		self._bump('par')

	def Reset(self):
		self.Calls = {}

	def Counts(self):
		return dict(self.Calls)
