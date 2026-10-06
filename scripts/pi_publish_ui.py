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
  * a `Publish` page on PI: Guidedrelease, Releaselabel,
    Publishselected, Editnotes, Nextlabel;
  * `Guided Release...`, a PopDialog wizard walking scope -> preflight
    -> notes -> publish, for when remembering the order is the hard
    part. Every step it takes is also its own button;
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


def PublishNames(names, bump='auto', upload=True, ns=None, confirm=True):
\t"""confirm=False skips the modal: the guided flow has already
\tasked, in a dialog that does not block the main thread."""
\tif not names:
\t\tui.messageBox('FNS publish', 'Nothing shippable in that selection.')
\t\treturn None
\tns = ns or _rail()
\tover = str(getattr(_pi().par, 'Releaselabel', None).eval() or '').strip()
\tlabel = over or None
\tversions = _preview(ns, names, bump)
\ttext = ConfirmText(names, versions, over or NextLabel(), upload)
\tif confirm and ui.messageBox('FNS publish', text,
\t\t\t\t\t\t\t\tbuttons=['Cancel', 'Publish']) != 1:
\t\t_log('publish cancelled at the confirm dialog')
\t\treturn None
\tres = ns['ReleaseMany'](names, bump=bump, label=label, upload=upload)
\tif not res.get('ok'):
\t\tui.messageBox('FNS publish', 'Refused: %s' % res.get('why', 'unknown'))
\t\t_log('publish refused: %s' % res.get('why'), level='WARNING')
\t\tRefreshLabel()
\t\treturn res
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
\treturn res


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


# --------------------------------------------------------------------------
# guided release -- the same rails, walked one dialog at a time
# --------------------------------------------------------------------------
# Every step here is reachable from its own button. This exists because
# knowing WHICH buttons, in WHICH order, is the part nobody remembers at
# 2am -- and the skipped steps are the ones with no error to announce
# them: a package never landed still publishes, it just publishes
# yesterday's bytes under a fresh version.
#
# PopDialog, not ui.messageBox: it does not block the main thread, and it
# hands `details` back to the callback, so the wizard's state rides the
# dialog chain instead of living in a module global that a re-stamp or a
# mid-flow error would strand.

# The dialog centres its text and wraps mid-word, so a long line comes
# out as a ragged block (and clipped buttons taught us it is narrow).
# Wrap it ourselves, short, on word boundaries.
def _wrap(text, width=38):
\tout = []
\tfor para in str(text).split('\\n'):
\t\tline = ''
\t\tfor word in para.split():
\t\t\tif line and len(line) + 1 + len(word) > width:
\t\t\t\tout.append(line)
\t\t\t\tline = word
\t\t\telse:
\t\t\t\tline = (line + ' ' + word) if line else word
\t\tout.append(line)
\treturn '\\n'.join(out)

def _ask(state, text, buttons, title=None):
\t"""One step. buttons[0] is always the way out, so Esc lands there."""
\top.TDResources.PopDialog.OpenDefault(
\t\ttext=_wrap(text),
\t\ttitle=title or ('Guided release  --  step %s of 4' % state.get('step', '?')),
\t\tbuttons=buttons,
\t\tcallback=_step,
\t\tdetails=state,
\t\ttextEntry=False,
\t\tescButton=1,
\t\tenterButton=len(buttons),
\t\tescOnClickAway=True)


def _rebuildRails():
\t"""Rebuild the installer + bootstrap artifacts. Stage() hashes these
\tinto the manifest as it goes, so a stale one publishes under a fresh
\thash -- a manifest promising bytes nobody built."""
\tns = {}
\texec(open('packaging/build_installer.py', encoding='utf-8').read(), ns)
\tout = []
\tfor fn, what in (('BuildInstaller', 'installer'), ('BuildBootstrap', 'bootstrap')):
\t\ttry:
\t\t\tr = ns[fn]()
\t\texcept Exception as e:
\t\t\tout.append('%s FAILED: %s' % (what, e))
\t\t\tcontinue
\t\tout.append('%s %s' % (what, 'rebuilt' if r.get('exported')
\t\t\t\t\t\t\t\telse 'FAILED: %s' % r.get('error')))
\treturn out


def _listerSelection():
\t# ui/treeLister, not 'lister' -- PublishSelected had it right and
\t# this did not, so the Selected path silently offered nothing.
\ttry:
\t\tpaths = list(_pi().op('ui/treeLister').ext.TreeListerExt.SelectedPaths)
\t\treturn Candidates(paths)
\texcept Exception:
\t\treturn []


def _preflightText(names, pre):
\tlines = ['Shipping: %s' % ', '.join(names), '']
\t# Each check carries its own advice after ' -- '; on a 38-column
\t# dialog that doubles the text to repeat what the buttons say.
\tclaim = lambda t: t.split(' -- ')[0].strip()
\tfor b in pre['blockers']:
\t\tlines.append('BLOCK  ' + claim(b))
\tfor w in pre['warnings']:
\t\tlines.append('warn   ' + claim(w))
\tif pre['ok'] and not pre['warnings']:
\t\tlines.append('Nothing is being forgotten.')
\tif pre['unlanded']:
\t\tlines += ['', 'Landing is manual: Save those rows in the lister, save '
\t\t\t\t'the project, then start this again.']
\tlines.append('')
\tlines.append('[Rebuild] rebuild the stale rails    [Continue] ship anyway'
\t\t\t\t if pre['stale_rails'] else '[Continue] ship anyway')
\treturn '\\n'.join(lines)


def GuidedRelease():
\t"""The whole release, one dialog at a time.

\tStep 1 scope, 2 preflight (with a Rebuild Rails escape hatch), 3 notes,
\t4 confirm and publish. No new machinery -- the same rails the cloud
\tbuttons drive, in the order that is easy to get wrong."""
\tns = _rail()
\tsel, bumped = _listerSelection(), _bumpedOnly(ns)
\tevery = sorted(c.name for c in ns['Packages']())
\t# Labels stay short: the dialog clips wide ones, and a truncated
\t# button is worse than a terse one. The body carries the meaning.
\ttext = ['What are you shipping?', '',
\t\t\t'[Selected] the rows picked in the lister:',
\t\t\t'    %s' % (', '.join(sel) if sel else '(nothing selected)'),
\t\t\t'',
\t\t\t'[Bumped] already ahead of the bucket:',
\t\t\t'    %s' % (', '.join(bumped) if bumped else '(none)'),
\t\t\t'',
\t\t\t'[All] every package, auto patch-bumped: %d' % len(every)]
\t_ask({'step': 1, 'sel': sel, 'bumped': bumped, 'every': every},
\t\t'\\n'.join(text), ['Cancel', 'Selected', 'Bumped', 'All'])


def _step(info):
\t"""Every dialog in the chain lands here; `details` says which step."""
\tstate = info.get('details') or {}
\tbutton = str(info.get('button') or '')
\tstep = state.get('step')
\tif not step or button in ('Cancel', 'Stop', ''):
\t\tif step:
\t\t\t_log('guided release stopped at step %s' % step)
\t\treturn

\tns = _rail()

\tif step == 1:
\t\tnames = {'Selected': state.get('sel') or [],
\t\t\t\t'Bumped': state.get('bumped') or [],
\t\t\t\t'All': state.get('every') or []}.get(button, [])
\t\tif not names:
\t\t\t_ask({}, 'Nothing to ship in that choice.', ['OK'],
\t\t\t\ttitle='Guided release')
\t\t\treturn
\t\tstate = {'step': 2, 'names': names}
\t\tstep = 2

\tif step == 2 and button == 'Rebuild':
\t\t_ask({'step': 2, 'names': state['names'], 'ack': True},
\t\t\t'\\n'.join(_rebuildRails()), ['Stop', 'Back'],
\t\t\ttitle='Guided release  --  rails')
\t\treturn

\tif step == 2:
\t\tnames = state['names']
\t\tpre = ns['Preflight'](names, quiet=True)
\t\t# entering the step, or coming back from a rebuild: show the checks
\t\tif state.get('ack') or button in ('Selected', 'Bumped', 'All', 'Back'):
\t\t\tif pre['ok'] and not pre['warnings']:
\t\t\t\tstate = {'step': 3, 'names': names}
\t\t\t\tstep = 3
\t\t\telse:
\t\t\t\tbuttons = ['Stop']
\t\t\t\tif pre['stale_rails']:
\t\t\t\t\tbuttons.append('Rebuild')
\t\t\t\tbuttons.append('Continue')
\t\t\t\t_ask({'step': 2, 'names': names, 'checked': True},
\t\t\t\t\t_preflightText(names, pre), buttons)
\t\t\t\treturn
\t\telse:
\t\t\tstate = {'step': 3, 'names': names}
\t\t\tstep = 3

\t# BEFORE the step-3 block below, which returns on its own and left
\t# this unreachable: clicking Notes just re-showed the same dialog.
\tif step == 3 and button == 'Notes':
\t\tEditNotes()
\t\t_ask({}, 'Write the notes, save the file, then start Guided'
\t\t\t' Release again.', ['OK'], title='Guided release')
\t\treturn

\tif step == 3:
\t\tnames = state['names']
\t\tpre = ns['Preflight'](names, quiet=True)
\t\tif pre['unnoted'] and button != 'Skip':
\t\t\t_ask({'step': 3, 'names': names, 'asked': True},
\t\t\t\t'No release notes for: %s\\n\\n'
\t\t\t\t'Their changelog bullet and in-tool "whatsnew" ship empty.\\n'
\t\t\t\t'A line starting "PackageName:" rides that package.\\n\\n'
\t\t\t\t'[Notes] open the file     [Skip] ship without them'
\t\t\t\t% ', '.join(pre['unnoted']),
\t\t\t\t['Stop', 'Notes', 'Skip'])
\t\t\treturn
\t\tstate = {'step': 4, 'names': names}
\t\tstep = 4

\tif step == 4:
\t\tnames = state['names']
\t\tif button == 'Publish':
\t\t\tres = PublishNames(names, confirm=False)
\t\t\tif res and res.get('ok'):
\t\t\t\t_ask({}, 'Published %s.\\n\\nThe upload runs in the background; '
\t\t\t\t\t'you get a dialog either way.\\n\\nLast step, in git:\\n'
\t\t\t\t\t'    the re-exported .tox files\\n'
\t\t\t\t\t'    packaging/manifest.json\\n'
\t\t\t\t\t'    packaging/CHANGELOG.md' % res.get('release', ''),
\t\t\t\t\t['OK'], title='Guided release  --  done')
\t\t\treturn
\t\tover = str(getattr(_pi().par, 'Releaselabel', None).eval() or '').strip()
\t\tversions = _preview(ns, names, 'auto')
\t\t_ask({'step': 4, 'names': names},
\t\t\tConfirmText(names, versions, over or NextLabel()),
\t\t\t['Cancel', 'Publish'])
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
    if o is None:
        return
    # WRITE the child, never the comp par: the tool's own Pkgversion is a
    # mirror (expression/bind onto FNS_About), and a .val assignment there
    # silently flips it to CONSTANT -- the severed-mirror preflight
    # blocker. Exactly release_one._versionWritePar's rule; the bare
    # comp-level par answers only for packages with no FNS_About child.
    fa = o.op('FNS_About')
    p = getattr(fa.par, 'Pkgversion', None) if fa is not None else None
    if p is None:
        p = getattr(o.par, 'Pkgversion', None)
    if p is None:
        return
    txt = str(info.get('cellText', '')).strip()
    if not _re.match(r'^\\d+\\.\\d+\\.\\d+$', txt):
        # no ui.messageBox here -- it blocks the main thread (td-python.md)
        debug('FNS publish: a package version looks like 1.2.3 -- got %r'
              % txt)
        return
    p.val = txt
    p.default = txt
'''


PAREXEC = '''# Routes the Publish page's pulses into fns_publish.
# Stamped by scripts/pi_publish_ui.py.

def _mod():
	return parent().op('fns_publish').module


def onPulse(par):
	if par.name == 'Guidedrelease':
		_mod().GuidedRelease()
	elif par.name == 'Publishselected':
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
	_par(pg, 'Pulse', 'Guidedrelease', 'Guided Release...')
	_par(pg, 'Str', 'Releaselabel', 'Release Label (blank = auto)')
	_par(pg, 'Pulse', 'Publishselected', 'Publish Selected to Bucket')
	_par(pg, 'Pulse', 'Editnotes', 'Edit Release Notes')
	_par(pg, 'Str', 'Nextlabel', 'Next Release', readOnly=True)
	# append lands at the END of a page that already exists, so the order
	# is asserted rather than assumed -- a PI stamped before the guided
	# button existed would otherwise keep it last forever.
	for i, _n in enumerate(('Guidedrelease', 'Releaselabel',
							'Publishselected', 'Editnotes', 'Nextlabel')):
		_p = getattr(pi.par, _n, None)
		if _p is not None:
			try:
				_p.order = i
			except Exception:
				pass
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
	pe.par.pars = 'Guidedrelease Publishselected Editnotes Releaselabel'
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
