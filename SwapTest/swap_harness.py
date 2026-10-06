"""swap_harness -- index-aware regression tests for SwapOps.

Why this exists
---------------
SwapOps rebuilds wiring from ``op.inputs`` / ``op.outputs``, which are
index-ERASED OP lists: they say WHAT is connected, never TO WHICH CONNECTOR.
Restoring through ``connector.connect(someOP)`` therefore lands on the
destination's first FREE slot rather than the original one. Every failure
this harness reports is a symptom of that one lossy step -- plus the two
COMP connector sets (``inputCOMPConnectors`` / ``outputCOMPConnectors``)
that SwapOps never touches at all.

Running
-------
    op('/SwapTest/swap_harness').module.RunAll()
    op('/SwapTest/swap_harness').module.RunAll('multi_in_order')   # one case

The oracle
----------
Each case builds a throwaway network under ``./fixtures``, snapshots the full
index-aware topology, swaps the named operators through SwapOps' OWN code,
then compares against the only correct answer: the BEFORE snapshot with those
operators' names exchanged. If swapping A and B does not yield exactly "A's
wiring on B and B's wiring on A", it is wrong. No hand-written per-case
expectations, so the expectations cannot themselves be buggy.
"""

FIXTURES = 'fixtures'


# --------------------------------------------------------------------------
# topology capture + oracle
# --------------------------------------------------------------------------

def snapshot(comp):
	"""Index-aware topology of every child of comp.

	{name: {'in': [(myIdx, farName, farIdx)], 'out': [...],
	        'cin': [...], 'cout': [...]}}

	Connector.connections yields the FAR-SIDE Connector, so both ends of every
	wire keep their index. That is the whole point -- op.inputs/op.outputs
	throw exactly this away.
	"""
	out = {}
	for o in comp.children:
		rec = {
			'in': sorted((c.index, f.owner.name, f.index)
						 for c in o.inputConnectors for f in c.connections),
			'out': sorted((c.index, f.owner.name, f.index)
						  for c in o.outputConnectors for f in c.connections),
		}
		if o.isCOMP:
			rec['cin'] = sorted((c.index, f.owner.name, f.index)
								for c in o.inputCOMPConnectors for f in c.connections)
			rec['cout'] = sorted((c.index, f.owner.name, f.index)
								 for c in o.outputCOMPConnectors for f in c.connections)
		out[o.name] = rec
	return out


def exchange(snap, a, b):
	"""Return snap with operators a and b exchanged -- names AND references."""
	def nm(n):
		return b if n == a else (a if n == b else n)
	out = {}
	for name, rec in snap.items():
		out[nm(name)] = dict(
			(k, sorted((i, nm(fn), fi) for (i, fn, fi) in v))
			for k, v in rec.items()
		)
	return out


def capacity(o):
	"""How many input connections o can physically hold.

	A COMP's connectors come from the In ops inside it, so its capacity is
	the connector count. maxInputs 9999 means one connector that grows.
	"""
	if o.isCOMP:
		return len(o.inputConnectors)
	return 9999 if o.maxInputs >= 9999 else o.maxInputs


def _byslot(entries):
	d = {}
	for (idx, fn, fi) in entries:
		d.setdefault(idx, []).append((fn, fi))
	return d


def _flat(d):
	return sorted((idx, fn, fi) for idx, v in d.items() for (fn, fi) in v)


def swap_pair(comp, snap, a, b):
	"""Exchange a and b, leaving inputs that will not fit where they are.

	Operators of different input capacity cannot exchange every wire: a
	1-input null has nowhere to put a merge's second source. Dropping the
	surplus would cost the user a connection they never asked to remove, so
	only the first min(capacity) slots change hands and the rest keep their
	existing connections. Swapping a merge fed by (a, other) with the null it
	feeds moves the two past each other and leaves `other` on the merge.
	"""
	oa, ob = comp.op(a), comp.op(b)
	upto = min(capacity(oa), capacity(ob))
	comp_upto = (min(len(oa.inputCOMPConnectors), len(ob.inputCOMPConnectors))
				 if (oa.isCOMP and ob.isCOMP) else 0)

	def nm(x):
		return b if x == a else (a if x == b else x)

	def merged(own, theirs, limit):
		out = {}
		for i, v in theirs.items():
			if i < limit:
				out[i] = [(nm(fn), fi) for (fn, fi) in v]
		for i, v in own.items():
			if i >= limit:
				out[i] = list(v)          # surplus: untouched at both ends
		return out

	out = {}
	for name, rec in snap.items():
		new = dict(rec)
		for key, limit in (('in', upto), ('cin', comp_upto)):
			if key not in rec:
				continue
			if name in (a, b):
				other = b if name == a else a
				own = _byslot(rec.get(key, []))
				theirs = _byslot(snap[other].get(key, []))
				new[key] = _flat(merged(own, theirs, limit))
			else:
				new[key] = sorted((i, nm(fn), fi) for (i, fn, fi) in rec.get(key, []))
		out[name] = new
	return out


def derive_outputs(snap):
	"""Rebuild every 'out'/'cout' from the 'in'/'cin' records.

	A connection is ONE edge recorded at both ends, so inputs are the source
	of truth and the far end is derivable. Deriving it is what stops a
	dropped wire from lingering on the operator that fed it.
	"""
	for rec in snap.values():
		rec['out'] = []
		if 'cout' in rec:
			rec['cout'] = []
	for name, rec in snap.items():
		for key, far_key in (('in', 'out'), ('cin', 'cout')):
			for (idx, fn, fi) in rec.get(key, []):
				far = snap.get(fn)
				if far is not None:
					far.setdefault(far_key, []).append((fi, name, idx))
	for rec in snap.values():
		for k in ('out', 'cout'):
			if k in rec:
				rec[k] = sorted(rec[k])
	return snap


def expected_for(comp, snap, names):
	"""Apply SwapOps' middle-out pairing to a snapshot to get the oracle."""
	n = len(names)
	out = snap
	for i in reversed(range(n // 2)):
		out = swap_pair(comp, out, names[i], names[n - 1 - i])
	return derive_outputs(out)


def diff(expected, actual):
	"""Human-readable difference between two snapshots."""
	problems = []
	for name in sorted(set(expected) | set(actual)):
		e, a = expected.get(name), actual.get(name)
		if e is None:
			problems.append('  %s: unexpected operator in result' % name)
			continue
		if a is None:
			problems.append('  %s: operator missing from result' % name)
			continue
		for key in sorted(set(e) | set(a)):
			ev, av = e.get(key, []), a.get(key, [])
			if ev != av:
				problems.append('  %s.%s\n      expected %s\n      actual   %s'
								% (name, key, ev, av))
	return problems


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------

def _swapops():
	"""SwapOps, without hardcoding an absolute path."""
	s = getattr(op, 'SwapOps', None)
	if s is None:
		found = op('/').findChildren(name='SwapOps', maxDepth=3)
		s = found[0] if found else None
	return s


def _swap(ops):
	"""Run SwapOps' own swap over ops, mirroring OnSwap's middle-out pairing."""
	s = _swapops()
	if s is None:
		raise RuntimeError('SwapOps not found in this project')
	ext = s.ext.SwapOpsExt
	ordered = sorted(ops, key=lambda x: x.nodeCenterX)
	n = len(ordered)
	for i in reversed(range(n // 2)):
		a, b = ordered[i], ordered[n - 1 - i]
		ext.swapPosition(a, b)
		ext.swapConnectorsMult(a, b)


def _fixtures():
	f = me.parent().op(FIXTURES)
	if f is None:
		f = me.parent().create(baseCOMP, FIXTURES)
		f.nodeX, f.nodeY = 0, -400
	return f


def _fresh(name):
	"""An empty, correctly-placed fixture container for one case."""
	f = _fixtures()
	old = f.op(name)
	if old:
		old.destroy()
	c = f.create(baseCOMP, name)
	# These fixtures are wiring skeletons -- chain heads have no source, so
	# cooking them only sprays "Not enough sources specified" across the
	# project. Topology is read from connectors, never from cooked output.
	c.allowCooking = False
	existing = [x for x in f.children if x is not c]
	c.nodeX = 0
	c.nodeY = (min([x.nodeY for x in existing]) - 400) if existing else 0
	return c


def _row(comp, *names_types):
	"""Create ops left-to-right on the grid. Returns them in order."""
	made = []
	x = 0
	for nm, ty in names_types:
		o = comp.create(ty, nm)
		o.nodeX, o.nodeY = x, 0
		x += max(o.nodeWidth, 160) + 40
		made.append(o)
	return made


# --------------------------------------------------------------------------
# cases -- each returns {'comp': COMP, 'swap': [names]}
# --------------------------------------------------------------------------

def case_chain_simple():
	"""src -> a -> b -> dst, all single fixed inputs."""
	c = _fresh('chain_simple')
	src, a, b, dst = _row(c, ('src', nullCHOP), ('a', nullCHOP),
						  ('b', nullCHOP), ('dst', nullCHOP))
	src.outputConnectors[0].connect(a.inputConnectors[0])
	a.outputConnectors[0].connect(b.inputConnectors[0])
	b.outputConnectors[0].connect(dst.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_adjacent():
	"""a -> b and nothing else -- the pair is directly connected."""
	c = _fresh('adjacent')
	a, b = _row(c, ('a', nullCHOP), ('b', nullCHOP))
	a.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_middle_op():
	"""a -> m -> b: the 'annoying edge case' the current code special-cases."""
	c = _fresh('middle_op')
	a, m, b = _row(c, ('a', nullCHOP), ('m', nullCHOP), ('b', nullCHOP))
	a.outputConnectors[0].connect(m.inputConnectors[0])
	m.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_middle_op_multi():
	"""a -> m(multi, 2 ins) -> b, where m's input ORDER must survive."""
	c = _fresh('middle_op_multi')
	a, other, m, b = _row(c, ('a', nullCHOP), ('other', nullCHOP),
						  ('m', mergeCHOP), ('b', nullCHOP))
	a.outputConnectors[0].connect(m.inputConnectors[0])
	other.outputConnectors[0].connect(m.inputConnectors[1])
	m.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_multi_surplus_adjacent():
	"""Owner's case (2026-09-01): swap a multi-input with the op it FEEDS.

	m(merge) <- a, other; m -> b(null). b cannot hold two inputs, so `other`
	has nowhere to go. It must therefore STAY on m rather than be dropped:
	expected is a -> b -> m with other -> m still attached.
	"""
	c = _fresh('multi_surplus_adjacent')
	a, other, m, b = _row(c, ('a', nullCHOP), ('other', nullCHOP),
						  ('m', mergeCHOP), ('b', nullCHOP))
	a.outputConnectors[0].connect(m.inputConnectors[0])
	other.outputConnectors[0].connect(m.inputConnectors[1])
	m.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['m', 'b']}


def case_multi_surplus_apart():
	"""Same capacity mismatch, but the pair is NOT adjacent."""
	c = _fresh('multi_surplus_apart')
	s1, s2, s3, m, b = _row(c, ('s1', nullCHOP), ('s2', nullCHOP),
							('s3', nullCHOP), ('m', mergeCHOP), ('b', nullCHOP))
	s1.outputConnectors[0].connect(m.inputConnectors[0])
	s2.outputConnectors[0].connect(m.inputConnectors[1])
	s3.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['m', 'b']}


def case_fixed_two_in():
	"""Two fixed 2-input ops (overTOP), both inputs wired on each."""
	c = _fresh('fixed_two_in')
	s1, s2, s3, s4, a, b = _row(c, ('s1', nullTOP), ('s2', nullTOP),
								('s3', nullTOP), ('s4', nullTOP),
								('a', overTOP), ('b', overTOP))
	s1.outputConnectors[0].connect(a.inputConnectors[0])
	s2.outputConnectors[0].connect(a.inputConnectors[1])
	s3.outputConnectors[0].connect(b.inputConnectors[0])
	s4.outputConnectors[0].connect(b.inputConnectors[1])
	return {'comp': c, 'swap': ['a', 'b']}


def case_sparse_fixed():
	"""a uses ONLY input 1 (input 0 empty); b uses only input 0.

	The killer case for index-erased restore: op.inputs reports one OP for
	each, losing which slot it occupied.
	"""
	c = _fresh('sparse_fixed')
	s1, s2, a, b = _row(c, ('s1', nullTOP), ('s2', nullTOP),
						('a', overTOP), ('b', overTOP))
	s1.outputConnectors[0].connect(a.inputConnectors[1])
	s2.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_multi_in_order():
	"""Two growing multi-input ops with 3 ordered inputs each."""
	c = _fresh('multi_in_order')
	made = _row(c, ('s1', nullCHOP), ('s2', nullCHOP), ('s3', nullCHOP),
				('t1', nullCHOP), ('t2', nullCHOP), ('t3', nullCHOP),
				('a', mergeCHOP), ('b', mergeCHOP))
	s1, s2, s3, t1, t2, t3, a, b = made
	for i, s in enumerate((s1, s2, s3)):
		s.outputConnectors[0].connect(a.inputConnectors[i])
	for i, t in enumerate((t1, t2, t3)):
		t.outputConnectors[0].connect(b.inputConnectors[i])
	return {'comp': c, 'swap': ['a', 'b']}


def case_fixed_to_multi():
	"""a is fixed 1-in, b is a growing multi-in with 2 inputs."""
	c = _fresh('fixed_to_multi')
	s1, t1, t2, a, b = _row(c, ('s1', nullCHOP), ('t1', nullCHOP),
							('t2', nullCHOP), ('a', nullCHOP), ('b', mergeCHOP))
	s1.outputConnectors[0].connect(a.inputConnectors[0])
	t1.outputConnectors[0].connect(b.inputConnectors[0])
	t2.outputConnectors[0].connect(b.inputConnectors[1])
	return {'comp': c, 'swap': ['a', 'b']}


def case_multi_to_fixed():
	"""Mirror of fixed_to_multi -- a is multi, b is fixed."""
	c = _fresh('multi_to_fixed')
	s1, s2, t1, a, b = _row(c, ('s1', nullCHOP), ('s2', nullCHOP),
							('t1', nullCHOP), ('a', mergeCHOP), ('b', nullCHOP))
	s1.outputConnectors[0].connect(a.inputConnectors[0])
	s2.outputConnectors[0].connect(a.inputConnectors[1])
	t1.outputConnectors[0].connect(b.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_fan_out():
	"""a feeds three destinations at specific input indices; b feeds one."""
	c = _fresh('fan_out')
	made = _row(c, ('a', nullCHOP), ('b', nullCHOP), ('d1', mergeCHOP),
				('d2', mergeCHOP), ('d3', nullCHOP))
	a, b, d1, d2, d3 = made
	# a -> d1 slot 1, a -> d2 slot 0, a -> d3 slot 0
	filler = c.create(nullCHOP, 'filler')
	filler.nodeX, filler.nodeY = 0, -200
	filler.outputConnectors[0].connect(d1.inputConnectors[0])
	a.outputConnectors[0].connect(d1.inputConnectors[1])
	a.outputConnectors[0].connect(d2.inputConnectors[0])
	a.outputConnectors[0].connect(d3.inputConnectors[0])
	b.outputConnectors[0].connect(d2.inputConnectors[1])
	return {'comp': c, 'swap': ['a', 'b']}


def case_comp_horizontal():
	"""Two COMPs whose horizontal connectors come from inner In/Out ops."""
	c = _fresh('comp_horizontal')
	s1, s2, a, b, dst = _row(c, ('s1', nullCHOP), ('s2', nullCHOP),
							 ('a', baseCOMP), ('b', baseCOMP), ('dst', mergeCHOP))
	for comp in (a, b):
		i = comp.create(inCHOP, 'in1')
		o = comp.create(outCHOP, 'out1')
		i.nodeX, i.nodeY = 0, 0
		o.nodeX, o.nodeY = 200, 0
		i.outputConnectors[0].connect(o.inputConnectors[0])
	s1.outputConnectors[0].connect(a.inputConnectors[0])
	s2.outputConnectors[0].connect(b.inputConnectors[0])
	a.outputConnectors[0].connect(dst.inputConnectors[0])
	b.outputConnectors[0].connect(dst.inputConnectors[1])
	return {'comp': c, 'swap': ['a', 'b']}


def case_comp_vertical():
	"""Two object COMPs wired through the VERTICAL COMP connectors.

	SwapOps touches only inputConnectors/outputConnectors, so this wiring is
	expected to be dropped entirely.
	"""
	c = _fresh('comp_vertical')
	a, b, hub_a, hub_b = _row(c, ('a', geometryCOMP), ('b', geometryCOMP),
							  ('hub_a', geometryCOMP), ('hub_b', geometryCOMP))
	a.outputCOMPConnectors[0].connect(hub_a.inputCOMPConnectors[0])
	b.outputCOMPConnectors[0].connect(hub_b.inputCOMPConnectors[0])
	return {'comp': c, 'swap': ['a', 'b']}


def case_comp_vs_top():
	"""A COMP swapped against a plain TOP -- unequal connector shapes."""
	c = _fresh('comp_vs_top')
	s1, s2, a, b, dst = _row(c, ('s1', nullTOP), ('s2', nullTOP),
							 ('a', baseCOMP), ('b', nullTOP), ('dst', compositeTOP))
	i = a.create(inTOP, 'in1')
	o = a.create(outTOP, 'out1')
	i.nodeX, i.nodeY = 0, 0
	o.nodeX, o.nodeY = 200, 0
	i.outputConnectors[0].connect(o.inputConnectors[0])
	s1.outputConnectors[0].connect(a.inputConnectors[0])
	s2.outputConnectors[0].connect(b.inputConnectors[0])
	a.outputConnectors[0].connect(dst.inputConnectors[0])
	b.outputConnectors[0].connect(dst.inputConnectors[1])
	return {'comp': c, 'swap': ['a', 'b']}


def case_three_way():
	"""Three selected ops -- exercises OnSwap's middle-out loop (swaps 0 and 2)."""
	c = _fresh('three_way')
	src, a, m, b, dst = _row(c, ('src', nullCHOP), ('a', nullCHOP),
							 ('m', nullCHOP), ('b', nullCHOP), ('dst', nullCHOP))
	src.outputConnectors[0].connect(a.inputConnectors[0])
	a.outputConnectors[0].connect(m.inputConnectors[0])
	m.outputConnectors[0].connect(b.inputConnectors[0])
	b.outputConnectors[0].connect(dst.inputConnectors[0])
	return {'comp': c, 'swap': ['a', 'm', 'b']}


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def cases():
	"""All case builders, in declaration order."""
	import types
	g = globals()
	names = [n for n in g if n.startswith('case_')
			 and isinstance(g[n], types.FunctionType)]
	# declaration order via code object line numbers
	names.sort(key=lambda n: g[n].__code__.co_firstlineno)
	return [(n[5:], g[n]) for n in names]


def RunAll(only=None):
	"""Build, swap and verify every case. Returns a report dict."""
	results = []
	for name, builder in cases():
		if only and name != only:
			continue
		rec = {'case': name}
		try:
			fx = builder()
			comp, swap_names = fx['comp'], fx['swap']
			before = snapshot(comp)
			expected = expected_for(comp, before, swap_names)
			_swap([comp.op(n) for n in swap_names])
			after = snapshot(comp)
			problems = diff(expected, after)
			rec['pass'] = not problems
			rec['problems'] = problems
			rec['swapped'] = swap_names
		except Exception as e:
			import traceback
			rec['pass'] = False
			rec['problems'] = ['  EXCEPTION: ' + traceback.format_exc()]
		results.append(rec)

	passed = [r for r in results if r['pass']]
	failed = [r for r in results if not r['pass']]
	lines = ['SwapOps harness: %d/%d passed' % (len(passed), len(results)), '']
	for r in results:
		lines.append('%s  %s' % ('PASS' if r['pass'] else 'FAIL', r['case']))
		for p in r.get('problems', []):
			lines.append(p)
	text = '\n'.join(lines)
	rep = me.parent().op('report')
	if rep is not None:
		rep.text = text
	return {'passed': len(passed), 'failed': len(failed),
			'total': len(results),
			'failing': [r['case'] for r in failed], 'text': text}
