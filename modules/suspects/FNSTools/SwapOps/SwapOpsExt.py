

'''Info Header Start
Name : SwapOpsExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass




FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class SwapOpsExt:
	"""
	SwapOpsExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		fnsLog('SwapOps: init')

	def onInitTD(self):
		# The slim ExtUtils carries no announcer, so this tool registers its
		# quick-launch commands itself: deferred past the registry's /sys
		# promotion and this module's own compile.
		run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

	def _announceCommands(self):
		FNSCommand.announce(self.ownerComp)

	def OnSwap(self):
		selected = ui.panes.current.owner.selectedChildren
		selected = sorted(selected, key=lambda x: x.nodeCenterX)
		num_selected = len(selected)
		fnsLog(f'SwapOps: swapping {num_selected} selected ops in {ui.panes.current.owner.path}')

		ui.undo.startBlock("Swap selected OPs")
		# reversed effect: middle-out order
		for i in reversed(range(int(num_selected/2))):
			op_a = selected[i]
			op_b = selected[num_selected-i-1]
			self.swapPosition(op_a, op_b)
			self.swapConnectorsMult(op_a, op_b)
		ui.undo.endBlock()
		
	def swapPosition(self, op1: OP, op2: OP):
		# Save the current positions of the operators
		x1, y1 = op1.nodeCenterX , op1.nodeCenterY 
		x2, y2 = op2.nodeCenterX , op2.nodeCenterY
		op1.nodeCenterX, op1.nodeCenterY = x2, y2
		op2.nodeCenterX, op2.nodeCenterY = x1, y1

	def swapConnectorsMult(self, op1: OP, op2: OP):
		"""Exchange every connection between op1 and op2, indices intact.

		Both ends of a wire carry an index, and TD exposes them through
		Connector.connections -- the FAR-SIDE Connector, with .owner and
		.index. op.inputs / op.outputs throw that away, which is why
		restoring through them lands on whatever slot happens to be free.

		Every edge touching op1 or op2 is some operator's INPUT, so the
		whole swap reduces to: capture the input wiring of op1, op2 and
		every operator they feed; then rebuild each from its counterpart's.
		Rebuilding the DESTINATIONS too is what keeps a growing multi-input's
		slot ORDER intact -- reconnecting one wire into a compacted merge
		cannot otherwise land where it started.

		SURPLUS INPUTS STAY WHERE THEY ARE. Two operators of different input
		capacity cannot exchange every wire -- a 1-input null has nowhere to
		put a merge's second source -- so only the first min(capacity) slots
		change hands and the rest keep their existing connections. Swapping
		a merge fed by (a, other) with the null it feeds therefore moves the
		merge and the null past each other and leaves `other` on the merge,
		instead of silently costing the user that wire.

		Handles all four connector sets: the horizontal data connectors and,
		for COMPs, the vertical inputCOMPConnectors / outputCOMPConnectors.
		"""
		def exchanged(o):
			# identity, never a dict -- an OP's hash follows its path
			if o is op1:
				return op2
			if o is op2:
				return op1
			return o

		def bySlot(o, comp_side=False):
			conns = o.inputCOMPConnectors if comp_side else o.inputConnectors
			return [[(f.owner, f.index) for f in c.connections] for c in conns]

		def isGrowing(o):
			# maxInputs 9999 == ONE connector that grows (merge, composite,
			# switch). isMultiInputs is inverted from its name, so it is not
			# the test. A COMP's connectors come from the In/Out ops inside
			# it and are always positional.
			return (not o.isCOMP) and o.maxInputs >= 9999

		def capacity(o):
			if o.isCOMP:
				return len(o.inputConnectors)
			return 9999 if o.maxInputs >= 9999 else o.maxInputs

		# how many slots actually change hands, per connector set
		swap_upto = min(capacity(op1), capacity(op2))
		comp_upto = (min(len(op1.inputCOMPConnectors), len(op2.inputCOMPConnectors))
					 if (op1.isCOMP and op2.isCOMP) else 0)

		def wiringFor(t, comp_side=False):
			"""The input wiring t should end up with."""
			own = bySlot(t, comp_side)
			src = exchanged(t)
			if src is t:
				# a destination: it keeps its own wiring, but whichever of
				# the pair feeds it has changed identity
				return [[(exchanged(fo), fi) for (fo, fi) in slot]
						for slot in own]
			if comp_side and not src.isCOMP:
				# swapping a COMP with a non-COMP: only a COMP has vertical
				# connectors, so this wiring has nowhere to go and stays put
				return own
			theirs = bySlot(src, comp_side)
			limit = comp_upto if comp_side else swap_upto
			out = []
			for i in range(max(len(own), len(theirs))):
				if i < limit:
					taken = theirs[i] if i < len(theirs) else []
					out.append([(exchanged(fo), fi) for (fo, fi) in taken])
				else:
					# surplus: untouched, so its far ends are untouched too
					out.append(list(own[i]) if i < len(own) else [])
			return out

		# 1. every operator whose input wiring this swap can disturb.
		#    Keyed by TD id, so nothing depends on an OP hashing stably.
		touched = {}
		for o in (op1, op2):
			touched[o.id] = o
			for c in o.outputConnectors:
				for f in c.connections:
					touched[f.owner.id] = f.owner
			if o.isCOMP:
				for c in o.outputCOMPConnectors:
					for f in c.connections:
						touched[f.owner.id] = f.owner

		# 2. the desired post-swap wiring, captured BEFORE anything is cut
		plan = {}
		for oid, t in touched.items():
			rec = {'in': wiringFor(t)}
			if t.isCOMP:
				rec['cin'] = wiringFor(t, True)
			plan[oid] = rec

		# 3. cut every affected input
		for t in touched.values():
			for comp_side in ((False, True) if t.isCOMP else (False,)):
				while True:
					conns = (t.inputCOMPConnectors if comp_side
							 else t.inputConnectors)
					live = [c for c in conns if c.connections]
					if not live:
						break
					live[0].disconnect()

		# 4. rebuild ascending; re-read the connector list every time because
		#    a growing multi-input gains a spare slot with each connection
		dropped = []
		for oid, rec in plan.items():
			t = touched[oid]
			for key, comp_side in (('in', False), ('cin', True)):
				slots = rec.get(key)
				if not slots:
					continue
				grow = isGrowing(t) and not comp_side
				nxt = 0
				for idx, sources in enumerate(slots):
					for (src_op, src_idx) in sources:
						conns = (t.inputCOMPConnectors if comp_side
								 else t.inputConnectors)
						src_conns = (src_op.outputCOMPConnectors if comp_side
									 else src_op.outputConnectors)
						use = nxt if grow else idx
						if use >= len(conns) or src_idx >= len(src_conns):
							dropped.append('%s[%d] <- %s[%d]'
										   % (t.name, use, src_op.name, src_idx))
							continue
						src_conns[src_idx].connect(conns[use])
						nxt += 1

		# Surplus retention means a wire should never be lost now; this is the
		# backstop for a shape that still cannot be rebuilt, and it must be
		# visible. The log is not where a user looks after pressing a button,
		# and ui.messageBox would block the main thread -- the status bar is
		# the non-blocking channel, and the swap sits inside an undo block.
		if dropped:
			fnsLog('SwapOps: %d connection(s) could not be restored: %s'
				   % (len(dropped), ', '.join(dropped)), level='WARNING')
			try:
				ui.status = ('SwapOps: %d connection(s) could not be restored'
							 % len(dropped))
			except Exception:
				pass
		return dropped

	### FNS_CommandRegistry (quick-launch commands) ###

	@FNSCommand.fns_command(label='Swap selected ops', context='selected')
	def SwapSelected(self):
		"""Swap the connections of the selected operators."""
		self.OnSwap()
		return {'ok': True}
