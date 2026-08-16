"""Stamp the FNS publish UI into Private Investigator's lister.

    exec(open('scripts/pi_publish_ui.py').read()); result = Apply()

Run it inside TouchDesigner. Idempotent: run it again after PI reverts,
after an olib update of PI, or after any edit here.

WHY THIS FILE EXISTS. The publish UI was first built live inside PI on
2026-08-14 and never saved back to PI's own `.tox`. PI carries
`enableexternaltox` ON pointing at
`modules/suspects/private_investigator1_withmyhacks.tox`, so the next
project open reloaded PI from that file and the whole feature vanished --
and because PI is not tagged `pi_suspect`, its own lister never showed it
as dirty. `.toe` backups cannot help: an externaltox COMP stores only its
node and parameters there, never its children (verified with `toeexpand`).
So the UI lives here as code, and PI is only ever the place it gets
stamped into. After running this, SAVE PI:

    pi.save(os.path.join(project.folder, pi.par.externaltox.eval()))

WHAT IT ADDS
  * a `Publish` page on PI: Releaselabel, Publishselected, Editnotes,
    Nextlabel (the parameter set recovered from the 2026-08-14 backup);
  * `fns_publish`, a DAT inside PI holding the orchestration -- confirm
    dialogs, version previews, and the call into packaging/release_one.py;
  * a `Pkg` column in the lister (the live `Pkgversion` par, editable and
    validated) and a `Publish` cloud button column beside Save/Reload;
  * the lister callbacks and a parameter-execute DAT that route clicks
    and pulses into `fns_publish`.

Clicking a package's cloud publishes that package; clicking the toolkit
ROOT publishes every hand-bumped package as one drop (with bump=None, so
a misclick cannot mass-release); Publish Selected takes the lister's
selection. Every path confirms first.
"""

import os

CLOUD_GLYPH = 0xF0167          # Material Design Icons cloud-upload
PUBLISH_PAGE = 'Publish'
MODULE_NAME = 'fns_publish'
PAREXEC_NAME = 'parexec_fns_publish'


# --------------------------------------------------------------------------
# the orchestration module that gets written INTO PI
# --------------------------------------------------------------------------

FNS_PUBLISH = '''"""FNS publish orchestration behind Private Investigator's lister.

STAMPED by scripts/pi_publish_ui.py -- edit that file, not this DAT. PI
reloads from its .tox on every project open, so anything typed here is
temporary; the script is the source of truth.
"""

import json
import re

RAIL = 'packaging/release_one.py'
NOTES = 'packaging/release_notes.md'
RELEASE_JSON = 'packaging/release.json'
BUCKET_MANIFEST = 'packaging/publish/manifest.json'


def _log(msg, level='INFO'):
\ttry:
\t\tlg = op.FNS.op('logger') if hasattr(op, 'FNS') else None
\t\tif lg and lg.par.Active.eval():
\t\t\tlg.Log(msg, level=level)
\texcept Exception:
\t\tpass


def _rail():
\t"""release_one.py in its own namespace -- the same rail the Textport
\truns, so the button and the manual flow cannot drift."""
\tns = {}
\texec(open(RAIL, encoding='utf-8').read(), ns)
\treturn ns


def _pi():
\treturn me.parent()


def NextLabel():
\t"""The label the next publish would take if nobody overrides it."""
\ttry:
\t\twith open(RELEASE_JSON, encoding='utf-8') as f:
\t\t\tcur = json.load(f).get('release', 'v0.0.0')
\t\tparts = cur.lstrip('vV').split('.')
\t\tparts[-1] = str(int(parts[-1]) + 1)
\t\treturn 'v' + '.'.join(parts)
\texcept Exception:
\t\treturn '?'


def RefreshLabel():
\tp = getattr(_pi().par, 'Nextlabel', None)
\tif p is not None:
\t\tover = str(getattr(_pi().par, 'Releaselabel', None).eval() or '').strip()
\t\tp.val = over if over else NextLabel()


def RefreshState():
\t"""Re-cook PI's ledger so the Pkg column shows current versions. The
\tDAT ships LOCKED, so this is unlock -> cook -> restore."""
\tst = _pi().op('state')
\tif st is None:
\t\treturn
\twas = bool(st.lock)
\tst.lock = False
\tst.cook(force=True)
\tst.lock = was


def _notesLine():
\t"""First line of the RELEASE-LEVEL prose. Per-tool 'Name: ...' lines
\tare skipped -- one tool's note is a poor summary of the drop."""
\ttry:
\t\twith open(NOTES, encoding='utf-8') as f:
\t\t\tt = re.sub(r'<!--.*?-->', '', f.read(), flags=re.S).strip()
\t\tif not t:
\t\t\treturn '(empty -- the entry will be just the package list)'
\t\tfor line in t.splitlines():
\t\t\ts = line.strip()
\t\t\tif s and not re.match(r'^[-*]?\\s*[A-Za-z_][\\w]*\\s*:', s):
\t\t\t\treturn s[:88]
\t\treturn t.splitlines()[0][:88]
\texcept Exception:
\t\treturn '(unreadable)'


def _packages(ns):
\treturn {c.name: c for c in ns['Packages']()}


def _preview(ns, names, bump):
\t"""Version transitions ReleaseMany would apply, without applying them."""
\tpub = ns['_publishedVersions']()
\tpkgs = _packages(ns)
\tout = {}
\tfor n in names:
\t\tc = pkgs.get(n)
\t\tif c is None:
\t\t\tcontinue
\t\told = str(c.par.Pkgversion.eval()).strip()
\t\tif bump == 'auto':
\t\t\tp = pub.get(n, '')
\t\t\tif p and ns['_verTuple'](old) <= ns['_verTuple'](p):
\t\t\t\tnew = ns['_bumpedVersion'](p, 'patch')
\t\t\telse:
\t\t\t\tnew = old
\t\telif bump:
\t\t\tnew = ns['_bumpedVersion'](old, bump)
\t\telse:
\t\t\tnew = old
\t\tout[n] = old if new == old else '%s -> %s' % (old, new)
\treturn out


def Candidates(paths):
\t"""op paths -> shippable package names, order kept, deduped."""
\tns = _rail()
\tknown = _packages(ns)
\tnames = []
\tfor p in paths:
\t\to = op(p)
\t\tif o is not None and o.name in known and o.name not in names:
\t\t\tnames.append(o.name)
\treturn names


def _bucketVersions(ns):
\t"""What the WORLD has: the staged rolling manifest when one exists,
\telse the local build. The local packaging/manifest.json is only what we
\tare about to ship -- comparing against it would call everything current
\tthe moment somebody re-ran Build()."""
\ttry:
\t\twith open(BUCKET_MANIFEST, encoding='utf-8') as f:
\t\t\treturn {p['name']: p.get('version', '')
\t\t\t\t\tfor p in json.load(f).get('packages', [])}
\texcept Exception:
\t\treturn ns['_publishedVersions']()


def _bumpedOnly(ns):
\t"""Packages whose live Pkgversion is already ahead of the bucket."""
\tpub = _bucketVersions(ns)
\tout = []
\tfor name, c in _packages(ns).items():
\t\tp = getattr(c.par, 'Pkgversion', None)
\t\tif p is None:
\t\t\tcontinue
\t\tif ns['_verTuple'](str(p.eval()).strip()) > ns['_verTuple'](pub.get(name, '')):
\t\t\tout.append(name)
\treturn sorted(out)


def ConfirmText(names, versions, label, upload=True):
\t"""Exactly what the confirm dialog says. Split out so it can be read
\twithout opening a modal."""
\tlines = ['Publish %d package%s as %s' % (len(names),
\t\t\t\t\t\t\t\t\t\t'' if len(names) == 1 else 's', label), '']
\tlines += ['    %s   %s' % (n, versions.get(n, '?')) for n in names]
\tlines += ['', 'Notes: ' + _notesLine()]
\tif not upload:
\t\tlines += ['', 'Staging only -- no upload.']
\treturn '\\n'.join(lines)


_WATCH = {}


def _armUploadWatch(res):
\t"""Upload runs detached, so nothing would ever say whether it worked.
\tPoll the process and finish with a dialog either way."""
\tproc = res.get('_proc')
\tif proc is None:
\t\treturn
\t_WATCH.update({'proc': proc, 'log': res.get('upload_log', ''),
\t\t\t\t'release': res.get('release', '')})
\trun("op('%s').module.PollUpload()" % me.path, delayFrames=180)


def PollUpload():
\tproc = _WATCH.get('proc')
\tif proc is None:
\t\treturn
\tcode = proc.poll()
\tif code is None:
\t\trun("op('%s').module.PollUpload()" % me.path, delayFrames=180)
\t\treturn
\tlog = _WATCH.get('log', '')
\trel = _WATCH.get('release', '')
\t_WATCH.clear()
\ttail = ''
\ttry:
\t\twith open(log, encoding='utf-8') as f:
\t\t\ttail = '\\n'.join(f.read().strip().splitlines()[-6:])
\texcept Exception:
\t\tpass
\tif code == 0:
\t\tui.messageBox('FNS publish', 'Upload finished -- %s is live.\\n\\n%s' % (rel, tail))
\t\t_log('upload finished for %s' % rel)
\telse:
\t\tui.messageBox('FNS publish',
\t\t\t\t\t'Upload FAILED for %s (exit %s).\\n\\n%s\\n\\n'
\t\t\t\t\t'The staged bytes are fine -- retry with:\\n'
\t\t\t\t\t'    python3 packaging/upload.py' % (rel, code, tail))
\t\t_log('upload failed (exit %s) for %s' % (code, rel), level='ERROR')


def PublishNames(names, bump='auto', upload=True, ns=None):
\tif not names:
\t\tui.messageBox('FNS publish', 'Nothing shippable in that selection.')
\t\treturn
\tns = ns or _rail()
\tover = str(getattr(_pi().par, 'Releaselabel', None).eval() or '').strip()
\tlabel = over or None
\tversions = _preview(ns, names, bump)
\ttext = ConfirmText(names, versions, over or NextLabel(), upload)
\tif ui.messageBox('FNS publish', text, buttons=['Cancel', 'Publish']) != 1:
\t\t_log('publish cancelled at the confirm dialog')
\t\treturn
\tres = ns['ReleaseMany'](names, bump=bump, label=label, upload=upload)
\tif not res.get('ok'):
\t\tui.messageBox('FNS publish', 'Refused: %s' % res.get('why', 'unknown'))
\t\t_log('publish refused: %s' % res.get('why'), level='WARNING')
\t\tRefreshLabel()
\t\treturn
\tdone = ['Released %s' % res['release'], '']
\tdone += ['    %s %s' % (k, v) for k, v in sorted(res['packages'].items())]
\tif res.get('uploading'):
\t\tdone += ['', 'Uploading in the background.',
\t\t\t\t'Log: %s' % res.get('upload_log', '')]
\tif res.get('skipped'):
\t\tdone += ['', 'Skipped (not shippable): %s' % ', '.join(res['skipped'])]
\tui.messageBox('FNS publish', '\\n'.join(done))
\t_log('published %s: %s' % (res['release'], ', '.join(sorted(res['packages']))))
\tgetattr(_pi().par, 'Releaselabel').val = ''
\tRefreshLabel()
\tRefreshState()
\t_armUploadWatch(res)


def PublishPath(path):
\t"""One row's cloud button. The toolkit ROOT means 'everything bumped'."""
\to = op(path)
\tif o is None:
\t\treturn
\troot = op.FNS if hasattr(op, 'FNS') else None
\tif root is not None and o is root:
\t\tPublishAll()
\t\treturn
\tPublishNames(Candidates([path]))


def PublishAll():
\t"""Every hand-bumped package as one drop. bump=None on purpose: a
\tmisclick on the root must not mass-release the fleet."""
\tns = _rail()
\tnames = _bumpedOnly(ns)
\tif not names:
\t\tui.messageBox('FNS publish',
\t\t\t\t\t'No package is ahead of the published manifest.\\n\\n'
\t\t\t\t\t'Bump one in the Pkg column first, or publish a single '
\t\t\t\t\t'tool -- that path auto-bumps.')
\t\treturn
\tPublishNames(names, bump=None, ns=ns)


def PublishSelected():
\t"""The lister's current selection."""
\ttry:
\t\tpaths = list(_pi().op('ui/treeLister').ext.TreeListerExt.SelectedPaths)
\texcept Exception as e:
\t\tui.messageBox('FNS publish', 'Could not read the lister selection: %s' % e)
\t\treturn
\tPublishNames(Candidates(paths))


def EditNotes():
\tui.viewFile(NOTES)
'''


# --------------------------------------------------------------------------
# lister callbacks appended to PI's treeListerConfig/callbacks
# --------------------------------------------------------------------------

CALLBACK_MARK = '# --- FNS publish (scripts/pi_publish_ui.py) ---'

CALLBACKS = CALLBACK_MARK + '''

def _fnsPublish():
    return parent.pi.op('fns_publish').module


def onClickPublish(info):
    _fnsPublish().PublishPath(getPath(info))


def onEditEndPkg(info):
    import re as _re
    o = op(getPath(info))
    p = getattr(o.par, 'Pkgversion', None) if o is not None else None
    if p is None:
        return
    txt = str(info.get('cellText', '')).strip()
    if not _re.match(r'^\\d+\\.\\d+\\.\\d+$', txt):
        ui.messageBox('FNS publish',
                      'A package version looks like 1.2.3 -- got %r' % txt)
        return
    p.val = txt
    p.default = txt
'''


PAREXEC = '''# Routes the Publish page's pulses into fns_publish.
# Stamped by scripts/pi_publish_ui.py.

def _mod():
	return parent().op('fns_publish').module


def onPulse(par):
	if par.name == 'Publishselected':
		_mod().PublishSelected()
	elif par.name == 'Editnotes':
		_mod().EditNotes()


def onValueChange(par, prev):
	if par.name == 'Releaselabel':
		_mod().RefreshLabel()
'''


# --------------------------------------------------------------------------
# stamping
# --------------------------------------------------------------------------

def _findPI():
	for c in op('/').children:
		if c.isCOMP and c.op('PrivateInvestigator') is not None:
			return c
	return None


def _page(comp, name):
	for pg in comp.customPages:
		if pg.name == name:
			return pg
	return comp.appendCustomPage(name)


def _par(page, kind, name, label, readOnly=False):
	comp = page.owner
	p = getattr(comp.par, name, None)
	if p is None:
		p = {'Str': page.appendStr, 'Pulse': page.appendPulse}[kind](name, label=label)[0]
	p.label = label
	if readOnly:
		p.readOnly = True
	return p


def _setColumn(colDefine, name, attrs, before='Row'):
	"""Add or update one lister column, addressed by attribute NAME so the
	config's row order is never assumed."""
	header = [c.val for c in colDefine.row(0)]
	attrNames = [colDefine[r, 0].val for r in range(colDefine.numRows)]
	if name in header:
		ci = header.index(name)
	else:
		ci = header.index(before) if before in header else len(header)
		colDefine.insertCol([name] + [attrs.get(a, '') for a in attrNames[1:]], ci)
		return 'added'
	for r in range(1, colDefine.numRows):
		key = attrNames[r]
		if key in attrs:
			colDefine[r, ci] = attrs[key]
	return 'updated'


def _publishTops(cfg):
	"""Publish button art: the Release trio cloned, with a cloud glyph."""
	made = []
	src = cfg.op('ReleaseCOMP')
	base = cfg.op('PublishCOMP')
	if base is None:
		base = cfg.copy(src, name='PublishCOMP')
		base.nodeX, base.nodeY = src.nodeX, src.nodeY - 150
		made.append('PublishCOMP')
	base.par.text.mode = ParMode.EXPRESSION
	base.par.text.expr = 'chr(%s)' % hex(CLOUD_GLYPH).upper().replace('0X', '0x')
	for suffix in ('Roll', 'Press'):
		s = cfg.op('Release' + suffix)
		d = cfg.op('Publish' + suffix)
		if d is None:
			d = cfg.copy(s, name='Publish' + suffix)
			d.nodeX, d.nodeY = s.nodeX, s.nodeY - 150
			made.append('Publish' + suffix)
		if d.inputConnectors and base.outputConnectors:
			try:
				d.inputConnectors[0].connect(base)
			except Exception:
				pass
	return made


def _patchStateTable(pi):
	"""Give the lister's source table a Pkgversion column, so the Pkg
	column is a VIEW of the live par rather than a side table."""
	cb = pi.op('script1_callbacks')
	t = cb.text or ''
	if 'Pkgversion' in t:
		return 'already'
	old_hdr = '[ "Path" ] + entries + [ "Dirty", "Family" ]'
	new_hdr = '[ "Path" ] + entries + [ "Dirty", "Family", "Pkgversion" ]'
	old_row = '\t\tappendData.append( target_operator.family )'
	new_row = ('\t\tappendData.append( target_operator.family )\n'
			'\t\t_pkg = getattr( target_operator.par, "Pkgversion", None )\n'
			'\t\tappendData.append( str(_pkg.eval()).strip() if _pkg is not None else "" )')
	if old_hdr not in t or old_row not in t:
		return 'PATTERN MISSING -- state table not patched'
	cb.text = t.replace(old_hdr, new_hdr).replace(old_row, new_row, 1)
	return 'patched'


def _refreshState(pi):
	"""PI keeps its `state` scriptDAT LOCKED, so a patched callback has no
	effect until the table is re-cooked by hand. Unlock, cook, and put the
	lock back exactly as found -- leaving it unlocked would re-run
	Get_Info over every suspect on any downstream cook."""
	st = pi.op('state')
	if st is None:
		return 'no state DAT'
	was = bool(st.lock)
	st.lock = False
	st.cook(force=True)
	st.lock = was
	return 'cooked (lock restored: %s)' % was


def Apply():
	report = {'ok': False}
	pi = _findPI()
	if pi is None:
		report['error'] = 'Private Investigator not found under /'
		return report
	report['pi'] = pi.path

	# 1. the Publish parameter page
	pg = _page(pi, PUBLISH_PAGE)
	_par(pg, 'Str', 'Releaselabel', 'Release Label (blank = auto)')
	_par(pg, 'Pulse', 'Publishselected', 'Publish Selected to Bucket')
	_par(pg, 'Pulse', 'Editnotes', 'Edit Release Notes')
	_par(pg, 'Str', 'Nextlabel', 'Next Release', readOnly=True)
	report['page'] = PUBLISH_PAGE

	# 2. the orchestration module
	mod = pi.op(MODULE_NAME)
	if mod is None:
		mod = pi.create(textDAT, MODULE_NAME)
		st = pi.op('state')
		mod.nodeX, mod.nodeY = (st.nodeX, st.nodeY - 200) if st else (0, 0)
	mod.text = FNS_PUBLISH
	report['module'] = mod.path

	# 3. pulse routing
	pe = pi.op(PAREXEC_NAME)
	if pe is None:
		pe = pi.create(parameterexecuteDAT, PAREXEC_NAME)
		pe.nodeX, pe.nodeY = mod.nodeX + 200, mod.nodeY
	pe.par.op = pi
	pe.par.pars = 'Publishselected Editnotes Releaselabel'
	pe.par.custom = True
	pe.par.builtin = False
	pe.par.valuechange = True
	pe.par.onpulse = True
	pe.text = PAREXEC
	report['parexec'] = pe.path

	# 4. lister columns
	cfg = pi.op('ui/treeListerConfig')
	report['tops'] = _publishTops(cfg)
	colDefine = cfg.op('colDefine')
	report['col_pkg'] = _setColumn(colDefine, 'Pkg', {
		'columnLabel': '*', 'sourceData': 'Pkgversion', 'sourceDataMode': 'string',
		'cellLook': '', 'topFill': 'BEST', 'help': 'Package version -- double-click to edit',
		'width': '58', 'sizable': '0', 'stretch': '0', 'editable': '1',
		'justify': 'CENTER', 'draggable': '0', 'selectRow': '1', 'clickOnDrag': '0',
	})
	report['col_publish'] = _setColumn(colDefine, 'Publish', {
		'columnLabel': '', 'sourceData': 'Family', 'sourceDataMode': 'blank',
		'cellLook': 'button', 'topFill': 'BEST', 'topPath': 'Publish*',
		'help': 'Publish to the bucket', 'width': '22', 'sizable': '0',
		'stretch': '0', 'editable': '', 'justify': '', 'draggable': '',
		'selectRow': '', 'clickOnDrag': '',
	})

	# 5. lister callbacks
	cb = cfg.op('callbacks')
	if CALLBACK_MARK in (cb.text or ''):
		head = cb.text.split(CALLBACK_MARK)[0]
		cb.text = head.rstrip() + '\n\n\n' + CALLBACKS
		report['callbacks'] = 'replaced'
	else:
		cb.text = (cb.text or '').rstrip() + '\n\n\n' + CALLBACKS
		report['callbacks'] = 'appended'

	# 6. the source table gains Pkgversion
	report['state_table'] = _patchStateTable(pi)
	report['state_refresh'] = _refreshState(pi)

	# 7. refresh what the UI shows
	try:
		mod.module.RefreshLabel()
	except Exception as e:
		report['label_refresh'] = str(e)
	try:
		pi.op('ui/treeLister').ext.TreeListerExt.Refresh()
	except Exception as e:
		report['lister_refresh'] = str(e)

	report['ok'] = True
	report['reminder'] = ('now land PI: pi.save(os.path.join(project.folder, '
						'pi.par.externaltox.eval())) -- otherwise the next '
						'project open reverts all of this')
	return report


def Save():
	"""Land PI to its own .tox. Without this the stamp does not survive."""
	pi = _findPI()
	if pi is None:
		return {'ok': False, 'error': 'PI not found'}
	rel = str(pi.par.externaltox.eval()).replace('\\', '/')
	if not rel:
		return {'ok': False, 'error': 'PI has no externaltox path'}
	path = rel if os.path.isabs(rel) else os.path.join(project.folder, rel)
	pi.save(path)
	return {'ok': True, 'saved': rel}
