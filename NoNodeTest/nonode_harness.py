"""nonode_harness -- regression tests for NoNode's operator identity.

Why this exists
---------------
An OP's hash follows its PATH. Renaming an operator -- or ANY of its
ancestors -- therefore changes the hash of a key already living in a dict,
stranding the entry in the wrong bucket: still present, still EQUAL to the
key, simply unreachable by lookup. Every NoNode registry is keyed by live
OPs, so a rename silently stops callbacks firing while the exec DAT keeps
firing perfectly well.

A MOVE is a different failure. TD destroys the operator and creates a new
one, so neither the reference nor the id survives, and the exec DAT -- whose
target parameter IS `list(registry.keys())` -- stops watching anything at
all. Dispatch can never heal that on its own, which is what NoNode.Heal()
is for.

Running
-------
    op('/NoNodeTest/nonode_harness').module.RunAll()
    op('/NoNodeTest/nonode_harness').module.RunAll('dispatch_after_rename')

Dispatch is exercised by calling NoNode's own OnChopExec / OnDatExec /
OnParExec with a real Channel / DAT / Par, which is exactly what the exec
DATs do. That keeps every case synchronous -- no waiting on frames -- while
still going through the real code path rather than poking at internals.
"""

KEEP = ('RigExt', 'ExtUtils')
RIG_TAG = 'nonode_rig'


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------

def _rig():
	"""Find the rig wherever it lives, by TAG.

	This used to be `me.parent().op('rig')`, which was the same path-identity
	mistake the harness exists to catch. The owner cut and pasted the rig out
	to the root; the harness crashed with AttributeError and it read as
	"NoNode broke on move" when NoNode had in fact self-healed a frame later.
	A tag survives both rename and move, so the harness now follows the rig
	instead of assuming where it sits.
	"""
	hits = op('/').findChildren(tags=[RIG_TAG], maxDepth=4)
	if not hits:
		hits = op('/').findChildren(tags=[RIG_TAG])
	return hits[0] if hits else None


def _nn():
	return _rig().op('ExtUtils').mod('NoNode').NoNode


def _ext():
	return _rig().ext.RigExt


def _reset():
	"""Return the rig to a known state and re-register from scratch."""
	rig = _rig()
	holder = _holder(create=False)
	if holder:
		holder.destroy()
	for c in list(rig.children):
		if c.name not in KEEP:
			c.destroy()
	chop = rig.create(constantCHOP, 'chop_watched')
	chop.nodeX, chop.nodeY = 400, 0
	chop.par.name0 = 'chan1'
	chop.par.value0 = 0
	dat = rig.create(tableDAT, 'dat_watched')
	dat.nodeX, dat.nodeY = 400, -200
	# the targets the DECORATED callbacks name -- they must exist before the
	# reinit below, because harvest resolves target strings at __init__ time
	deco = rig.create(constantCHOP, 'chop_deco')
	deco.nodeX, deco.nodeY = 400, -400
	deco.par.name0 = 'chan1'
	deco.par.value0 = 0
	ddat = rig.create(tableDAT, 'dat_deco')
	ddat.nodeX, ddat.nodeY = 400, -600
	# each par guarded on ITSELF -- gating the whole block on one of them
	# means a later addition is silently never created
	page = None
	for name, append in (('Speed', 'appendFloat'), ('Gain', 'appendFloat'),
						 ('Reset', 'appendPulse'), ('Trans', 'appendXYZ')):
		if hasattr(rig.par, name) or hasattr(rig.parGroup, name):
			continue
		if page is None:
			page = next((pg for pg in rig.customPages if pg.name == 'Rig'), None) 				   or rig.appendCustomPage('Rig')
		getattr(page, append)(name, label=name)
	rig.par.reinitextensions.pulse()
	return rig


def _holder(create=True):
	"""Somewhere to move a watched operator TO -- beside the rig, wherever
	the rig currently is."""
	parent = _rig().parent()
	h = parent.op('moved')
	if h is None and create:
		h = parent.create(baseCOMP, 'moved')
		h.nodeX, h.nodeY = 0, -400
	return h


def _move(o, holder):
	"""A TD move: copy to the new parent, destroy the original."""
	moved = holder.copyOPs([o])[0]
	moved.nodeX, moved.nodeY = 0, 0
	o.destroy()
	return moved


def _fireChop(chop):
	nn = _nn()
	nn.OnChopExec(nn.ChopExecType.ValueChange, chop['chan1'], 0, 1.0, 0.0)


def _fireDat(dat):
	nn = _nn()
	nn.OnDatExec(nn.DatExecType.TableChange, dat)


def _firePar(par):
	nn = _nn()
	nn.OnParExec(nn.ParExecType.ValueChange, par, 1.0, 0.0)


def _chopTarget():
	ex = _rig().op('ExtUtils/extChopValueChangeExec')
	return str(ex.par.chops.eval())


# --------------------------------------------------------------------------
# cases -- each returns {'ok': bool, 'detail': ...}
# --------------------------------------------------------------------------

def case_dispatch_baseline_chop():
	"""Sanity: an untouched registration dispatches."""
	rig = _reset()
	_ext().Reset()
	_fireChop(rig.op('chop_watched'))
	return {'ok': _ext().Calls.get('chop') == 1, 'detail': _ext().Counts()}


def case_dispatch_baseline_dat():
	rig = _reset()
	_ext().Reset()
	_fireDat(rig.op('dat_watched'))
	return {'ok': _ext().Calls.get('dat') == 1, 'detail': _ext().Counts()}


TRIALS = 12


def _renameTrials(rename_target):
	"""Register, rename, fire -- TRIALS times. Returns (fired, TRIALS).

	The bug is INTERMITTENT, so one trial proves nothing. A stranded entry is
	still reachable whenever the new hash's probe sequence happens to land on
	its slot, because CPython compares the probed key by IDENTITY before it
	compares hashes. Measured 2026-09-01: a renamed single-entry dict stayed
	reachable 9 times in 60, a 5-entry dict 28 times in 100. A single trial
	would therefore pass on luck roughly one run in four to one in six.

	rename_target: 'op' renames the watched CHOP, 'ancestor' renames the COMP
	holding it (which carries no extension, so nothing reinitialises).
	"""
	rig = _reset()
	nn = _nn()
	fired = 0
	for i in range(TRIALS):
		nest = rig.create(baseCOMP, 'n%d' % i)
		nest.nodeX, nest.nodeY = 800 + (i % 4) * 200, -(i // 4) * 200
		c = nest.create(constantCHOP, 'c')
		c.nodeX, c.nodeY = 0, 0
		c.par.name0 = 'chan1'
		nn.RegisterChopExec(nn.ChopExecType.ValueChange, c, 'chan1',
							_ext().onChopValue)
		if rename_target == 'op':
			c.name = 'c_renamed'
		else:
			nest.name = 'n%d_renamed' % i
		_ext().Reset()
		_fireChop(nest.op(c.name))
		if _ext().Calls.get('chop') == 1:
			fired += 1
	return fired


def case_dispatch_after_rename():
	"""THE bug: rename the watched operator, dispatch must still find it."""
	fired = _renameTrials('op')
	return {'ok': fired == TRIALS, 'detail': '%d/%d dispatched' % (fired, TRIALS)}


def case_dispatch_after_dat_rename():
	rig = _reset()
	rig.op('dat_watched').name = 'dat_renamed'
	_ext().Reset()
	_fireDat(rig.op('dat_renamed'))
	return {'ok': _ext().Calls.get('dat') == 1, 'detail': _ext().Counts()}


def case_dispatch_after_ancestor_rename():
	"""Rename an ancestor that carries NO extension.

	Renaming the extension's OWN comp is not the interesting case, and an
	earlier version of this test got that wrong. Measured 2026-09-01: TD
	reinitialises the extension on that rename -- it even re-imports NoNode,
	handing back a fresh class with empty registries -- and the extension's
	own __init__ re-registers from scratch. The whole registry is rebuilt, so
	it self-heals no matter what NoNode does. The test only ever "failed"
	because it read the counters in the same frame, racing a reinit that had
	not landed yet.

	The real exposure is an ancestor with no extension on it: nothing
	reinitialises, the entry keeps its old hash, and the stranded key is the
	only thing between the event and the callback.
	"""
	fired = _renameTrials('ancestor')
	return {'ok': fired == TRIALS, 'detail': '%d/%d dispatched' % (fired, TRIALS)}


def case_target_after_rename():
	"""Targeting is NOT the broken half -- this should pass either way."""
	rig = _reset()
	rig.op('chop_watched').name = 'chop_renamed'
	val = _chopTarget()
	return {'ok': 'chop_renamed' in val, 'detail': val}


def case_target_after_move():
	"""A move kills targeting outright; Heal() must rebind it."""
	rig = _reset()
	moved = _move(rig.op('chop_watched'), _holder())
	before = _chopTarget()
	_nn().Heal()
	after = _chopTarget()
	return {'ok': moved.path in after,
			'detail': {'before_heal': before, 'after_heal': after}}


def case_dispatch_after_move():
	rig = _reset()
	moved = _move(rig.op('chop_watched'), _holder())
	_nn().Heal()
	_ext().Reset()
	_fireChop(moved)
	return {'ok': _ext().Calls.get('chop') == 1, 'detail': _ext().Counts()}


def case_move_prunes_when_gone():
	"""A watched operator that is DELETED, not moved, must leave no corpse."""
	rig = _reset()
	rig.op('chop_watched').destroy()
	summary = _nn().Heal()
	keys = list(_nn().CHOPEXEC_CALLBACKS.getRaw()
				.get(_nn().ChopExecType.ValueChange, {}).keys())
	# "no corpse" is every SURVIVING key still resolving -- not an empty
	# registry. The rig also carries a decorated registration that is
	# legitimately untouched here, so pruning must be surgical, not a sweep.
	return {'ok': summary.get('pruned', 0) == 1 and all(k.valid for k in keys),
			'detail': {'summary': summary,
					   'left': [(k.name, k.valid) for k in keys]}}


def case_no_duplicate_key_on_reregister():
	"""Re-registering a renamed operator must reuse its stranded entry."""
	rig = _reset()
	nn = _nn()
	rig.op('chop_watched').name = 'chop_renamed'
	chop = rig.op('chop_renamed')
	nn.RegisterChopExec(nn.ChopExecType.ValueChange, chop, 'chan1',
						_ext().onChopValue)
	keys = list(nn.CHOPEXEC_CALLBACKS.getRaw()
				.get(nn.ChopExecType.ValueChange, {}).keys())
	# scoped to the operator under test: other registrations on the rig are
	# none of this case's business, only that THIS one did not double up
	mine = [k for k in keys if k.name == 'chop_renamed']
	return {'ok': len(mine) == 1, 'detail': [(k.name, k.id) for k in keys]}


def case_par_dispatch_after_owner_rename():
	"""Par keys hash off their owner's path, so they strand the same way."""
	rig = _reset()
	nn = _nn()
	target = rig.op('chop_watched')
	nn.RegisterParExec(nn.ParExecType.ValueChange, target, 'value0',
					   _ext().onParValue)
	target.name = 'chop_renamed'
	_ext().Reset()
	_firePar(rig.op('chop_renamed').par.value0)
	return {'ok': _ext().Calls.get('par') == 1, 'detail': _ext().Counts()}


def case_deregister_after_rename_chop():
	"""Deregistering a RENAMED operator must actually deregister it.

	`del d[key]` is a hash lookup too, so it cannot reach a stranded entry
	either -- the guard in front of it (`chop in ...`) just skips, silently,
	and the callback stays live. Repeated, because the stranding is
	probabilistic.
	"""
	rig = _reset()
	nn = _nn()
	leaked = 0
	for i in range(TRIALS):
		nest = rig.create(baseCOMP, 'n%d' % i)
		nest.nodeX, nest.nodeY = 800 + (i % 4) * 200, -(i // 4) * 200
		c = nest.create(constantCHOP, 'c')
		c.nodeX, c.nodeY = 0, 0
		c.par.name0 = 'chan1'
		nn.RegisterChopExec(nn.ChopExecType.ValueChange, c, 'chan1',
							_ext().onChopValue)
		c.name = 'c_renamed'
		nn.DeregisterChopExec(nn.ChopExecType.ValueChange, nest.op('c_renamed'))
		_ext().Reset()
		_fireChop(nest.op('c_renamed'))
		if _ext().Calls.get('chop'):
			leaked += 1
	return {'ok': leaked == 0, 'detail': '%d/%d still fired after deregister'
			% (leaked, TRIALS)}


def case_deregister_after_rename_dat():
	rig = _reset()
	nn = _nn()
	leaked = 0
	for i in range(TRIALS):
		nest = rig.create(baseCOMP, 'd%d' % i)
		nest.nodeX, nest.nodeY = 800 + (i % 4) * 200, -(i // 4) * 200
		d = nest.create(tableDAT, 'd')
		d.nodeX, d.nodeY = 0, 0
		nn.RegisterDatExec(nn.DatExecType.TableChange, d, _ext().onDatTable)
		d.name = 'd_renamed'
		nn.DeregisterDatExec(nn.DatExecType.TableChange, nest.op('d_renamed'))
		_ext().Reset()
		_fireDat(nest.op('d_renamed'))
		if _ext().Calls.get('dat'):
			leaked += 1
	return {'ok': leaked == 0, 'detail': '%d/%d still fired after deregister'
			% (leaked, TRIALS)}


def case_deregister_after_rename_par():
	rig = _reset()
	nn = _nn()
	leaked = 0
	for i in range(TRIALS):
		nest = rig.create(baseCOMP, 'p%d' % i)
		nest.nodeX, nest.nodeY = 800 + (i % 4) * 200, -(i // 4) * 200
		c = nest.create(constantCHOP, 'c')
		c.nodeX, c.nodeY = 0, 0
		nn.RegisterParExec(nn.ParExecType.ValueChange, c, 'value0',
						   _ext().onParValue)
		c.name = 'c_renamed'
		nn.DeregisterParExec(nn.ParExecType.ValueChange,
							 nest.op('c_renamed'), 'value0')
		_ext().Reset()
		_firePar(nest.op('c_renamed').par.value0)
		if _ext().Calls.get('par'):
			leaked += 1
	return {'ok': leaked == 0, 'detail': '%d/%d still fired after deregister'
			% (leaked, TRIALS)}


def case_foreign_move_heals_without_explicit_heal():
	"""A watched op OUTSIDE the extension's COMP, moved, with NO Heal() call.

	Nothing reinitialises for a foreign op, so this is the one move case that
	has no self-healing trigger. The rig keeps a second live registration
	(chop_watched), which is the realistic shape: some other event is still
	firing and can carry the repair.
	"""
	rig = _reset()
	nn = _nn()
	outside = rig.parent().op('outside') or rig.parent().create(baseCOMP, 'outside')
	outside.nodeX, outside.nodeY = 800, 0
	for c in list(outside.children):
		c.destroy()
	f = outside.create(constantCHOP, 'foreign')
	f.nodeX, f.nodeY = 0, 0
	f.par.name0 = 'chan1'
	nn.RegisterChopExec(nn.ChopExecType.ValueChange, f, 'chan1',
						_ext().onChopValue)
	moved = _move(f, _holder())
	_ext().Reset()
	_fireChop(moved)                      # deliberately NO Heal() first
	return {'ok': _ext().Calls.get('chop') == 1, 'detail': _ext().Counts()}


def case_deco_dispatch_chop():
	"""A method carrying @onChopExec is registered by harvest and dispatches."""
	rig = _reset()
	_ext().Reset()
	_fireChop(rig.op('chop_deco'))
	return {'ok': _ext().Calls.get('deco_chop') == 1, 'detail': _ext().Counts()}


def case_deco_dispatch_dat():
	rig = _reset()
	_ext().Reset()
	_fireDat(rig.op('dat_deco'))
	return {'ok': _ext().Calls.get('deco_dat') == 1, 'detail': _ext().Counts()}


def case_deco_dispatch_par():
	rig = _reset()
	_ext().Reset()
	_firePar(rig.op('chop_deco').par.value0)
	return {'ok': _ext().Calls.get('deco_par') == 1, 'detail': _ext().Counts()}


def case_deco_does_not_disturb_imperative():
	"""Decorated and Register()-ed callbacks coexist on one extension."""
	rig = _reset()
	_ext().Reset()
	_fireChop(rig.op('chop_watched'))
	_fireChop(rig.op('chop_deco'))
	c = _ext().Counts()
	return {'ok': c.get('chop') == 1 and c.get('deco_chop') == 1, 'detail': c}


def case_deco_arms_exec_dat():
	"""Registration must also POINT the exec DAT at the target.

	Every other case fires dispatch DIRECTLY, which proves routing but not
	that anything would ever call it. Each exec DAT's target parameter is an
	expression over the registry, so registering arms it implicitly -- this
	is the case that notices if that stops being true.
	"""
	rig = _reset()
	ex = rig.op('ExtUtils/extChopValueChangeExec')
	armed = str(ex.par.chops.eval() or '')
	return {'ok': rig.op('chop_deco').path in armed and bool(ex.par.active.eval()),
			'detail': 'active=%s chops=%r' % (ex.par.active.eval(), armed)}


def case_deco_reports_bad_target():
	"""A target that cannot resolve is REPORTED, never silently dropped.

	The whole reason to prefer this over Register() calls: a mistyped
	parameter name currently produces a callback that simply never fires.
	"""
	rig = _reset()
	nn = _nn()

	class Probe:
		def __init__(self):
			self.ownerComp = rig

		def onTypo(self, par, val):
			pass

	# the @ form, applied by hand -- the class body cannot see `nn`
	Probe.onTypo = nn.onParExec(nn.ParExecType.ValueChange,
								'chop_deco', 'Speeed')(Probe.onTypo)
	report = nn.HarvestCallbacks(Probe())
	return {'ok': report['registered'] == 0 and len(report['problems']) == 1,
			'detail': report}


def case_deco_rebuild_is_not_cumulative():
	"""Harvesting twice rebuilds the registry rather than appending to it."""
	rig = _reset()
	nn = _nn()
	first = nn.HarvestCallbacks(_ext())
	second = nn.HarvestCallbacks(_ext())
	_ext().Reset()
	_fireChop(rig.op('chop_deco'))
	return {'ok': _ext().Calls.get('deco_chop') == 1,
			'detail': 'harvested %s then %s; counts %s'
					  % (first['registered'], second['registered'],
						 _ext().Counts())}


def case_deco_arity_is_preserved():
	"""The decorator must return the function UNTOUCHED.

	Dispatch infers arity from __code__.co_argcount, so a decorator that
	wrapped its function would hand the dispatcher the wrapper's signature
	and mis-call every decorated callback.
	"""
	fn = type(_ext()).decoChopValue
	return {'ok': fn.__code__.co_argcount == 3 and fn.__name__ == 'decoChopValue',
			'detail': '%s/%d args' % (fn.__name__, fn.__code__.co_argcount)}


def case_deco_dispatch_own_par():
	"""owner omitted -- the extension's OWN custom parameter.

	The case that overlaps CustomParHelper: it already watches every custom
	par on the COMP through its own exec DATs. This asks whether NoNode's
	registry ALSO carries it, which is what the decorator relies on.
	"""
	rig = _reset()
	_ext().Reset()
	_firePar(rig.par.Speed)
	return {'ok': _ext().Calls.get('deco_ownpar') == 1, 'detail': _ext().Counts()}


def case_deco_own_par_arms_exec_dat():
	"""...and whether the par exec DAT is actually pointed at the COMP."""
	rig = _reset()
	ex = rig.op('ExtUtils/extParExecNoNodeValueChange')
	armed = str(ex.par.ops.eval() or '')
	pars = str(ex.par.pars.eval() or '')
	return {'ok': rig.path in armed and 'Speed' in pars,
			'detail': 'active=%s ops=%r pars=%r'
					  % (ex.par.active.eval(), armed, pars)}


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def cases():
	import types
	g = globals()
	names = [n for n in g if n.startswith('case_')
			 and isinstance(g[n], types.FunctionType)]
	names.sort(key=lambda n: g[n].__code__.co_firstlineno)
	return [(n[5:], g[n]) for n in names]


def RunAll(only=None):
	results = []
	for name, fn in cases():
		if only and name != only:
			continue
		try:
			out = fn()
			results.append({'case': name, 'pass': bool(out.get('ok')),
							'detail': out.get('detail')})
		except Exception:
			import traceback
			results.append({'case': name, 'pass': False,
							'detail': traceback.format_exc()})
	_reset()
	passed = [r for r in results if r['pass']]
	lines = ['NoNode harness: %d/%d passed' % (len(passed), len(results)), '']
	for r in results:
		lines.append('%s  %s' % ('PASS' if r['pass'] else 'FAIL', r['case']))
		if not r['pass']:
			lines.append('      %s' % (r['detail'],))
	text = '\n'.join(lines)
	rep = me.parent().op('report')
	if rep is not None:
		rep.text = text
	return {'passed': len(passed), 'total': len(results),
			'failing': [r['case'] for r in results if not r['pass']],
			'text': text}
