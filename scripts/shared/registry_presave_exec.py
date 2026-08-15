"""Pre-save heal for the /sys global registries.

Replaces the disabled periodic watch (RegistryBase.REGISTRY_WATCH_ENABLED is
off): stale/renamed entries are pruned and silent autoregister hosts
re-published once, right before the project saves -- a moment where a frame
spike cannot matter. Lives on an Execute DAT at the FNSTools root.
"""


def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass


def healAllRegistries():
	healed = []
	sys_comp = op('/sys')
	if sys_comp is None:
		return healed
	fns = getattr(op, 'FNS', None)
	for comp in sys_comp.children:
		if 'Registry' not in comp.name or not comp.valid:
			continue
		if not comp.extensionsReady:
			continue
		# each registry's in-project master carries the Presaveheal toggle;
		# missing master or missing par means heal (the safe default)
		master = fns.op(comp.name) if fns is not None and fns.valid else None
		if master is not None:
			par = getattr(master.par, 'Presaveheal', None)
			if par is not None and not par.eval():
				continue
		for ext in comp.extensions:
			if ext is not None and hasattr(ext, '_healRegistryEntries'):
				try:
					ext._healRegistryEntries()
					healed.append(comp.name)
				except Exception as e:
					debug('registry pre-save heal %s: %s' % (comp.name, e))
				break
	return healed


def onProjectPreSave():
	healed = healAllRegistries()
	fnsLog('Registries: pre-save heal ran on %d registr%s (%s)'
		   % (len(healed), 'y' if len(healed) == 1 else 'ies', ', '.join(healed)))
	return
