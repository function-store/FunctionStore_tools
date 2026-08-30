"""onHTTPRequest for the FNS console server (console_server, on the /sys global).

Dumb dispatcher: resolve the console extension, hand each request to the
subsystem that owns it, serialize. No state and no tool knowledge live
here. The server itself is ephemeral -- see Open() in ConsoleRegistryExt.

Routes:
  /                         the console page (console_page DAT)
  /base.css                 the shared UI base (the page's FNS:UIBASE block),
                            linkable by contributed tabs served under /t/
  /api/tabs                 built-in + contributed tabs
  /api/state /api/set       FNS_ConfigRegistry Ui* -- the paths are the
  /api/export /api/import   registry's original ones on purpose: TDXLPP's
  /api/scope                launcher reads /api/state and /api/set
  /api/updates              FNS_Updater fronted by the console's UiUpdates*:
  /api/updates/check        Compare rows + release notes (GET), kick a cheap
  /api/updates/apply        manifest check, apply updates, and the live
  /api/updates/status       pass's stage/results for the page's poll
  /tools + /manifest.js /selection /status /install /auth/*
                            FNS_Installer.ServeRequest, forwarded verbatim
  /t/<tab>/                 a contributed tab's page (served as-is)
  /t/<tab>/api/<action>     its api DAT's onConsoleRequest(action, method, body)
"""

import json


def _ext(webServerDAT):
	# the global /sys console is the API owner; fall back to our own comp
	con = getattr(op, 'FNS_CONSOLE', None)
	if con is None or not con.valid:
		con = webServerDAT.parent()
	return con.ext.ConsoleRegistryExt


def _json(response, payload, code=200):
	response['statusCode'] = code
	response['statusReason'] = 'OK' if code == 200 else 'Error'
	response['Content-Type'] = 'application/json'
	response['data'] = json.dumps(payload)


def _html(response, text, code=200):
	response['statusCode'] = code
	response['statusReason'] = 'OK' if code == 200 else 'Error'
	response['Content-Type'] = 'text/html'
	response['data'] = text


def _body(request):
	data = request.get('data') or '{}'
	if isinstance(data, bytes):
		data = data.decode('utf-8')
	return json.loads(data)


# /auth/* and /settings ride along so the FRAMED picker's account rail
# (sign in / recheck / redeem / the done step's Open Settings) works when
# the console serves it -- without them those posts 404 against this
# server while the same page served by the installer answers.
PICKER_URIS = ('/manifest.js', '/selection', '/status', '/install',
			   '/auth/signin', '/auth/recheck', '/auth/redeem', '/auth/status',
			   '/settings')
CONFIG_URIS = ('/api/state', '/api/set', '/api/export', '/api/import', '/api/scope')

NO_CONFIG = {'ok': False,
			 'why': 'FNS_ConfigRegistry is not installed -- settings need the config package'}

NO_INSTALLER_HTML = (
	'<!doctype html><body style="background:#0a0a0a;color:#a3a3a3;'
	'font:14px/1.6 sans-serif;padding:40px;max-width:60ch">'
	'<h3 style="color:#f5f5f5">No installer in this project</h3>'
	'This project has no <code>FNS_Installer</code> COMP, so tools cannot '
	'be added or removed from here. Drop the FNSTools bootstrap (or the '
	'bare <code>FNS_Installer.tox</code>) into the project and reload this '
	'tab. Settings on the other tab keep working either way.</body>')


def _serveConfig(ext, uri, method, request, response):
	cfg = ext._configRegistry()
	if cfg is None:
		_json(response, NO_CONFIG, 404)
		return
	if uri == '/api/state':
		_json(response, cfg.UiState())
	elif uri == '/api/set' and method == 'POST':
		b = _body(request)
		_json(response, cfg.UiSet(b.get('tool'), b.get('par'), b.get('value')))
	elif uri == '/api/export':
		_json(response, cfg.UiExport())
	elif uri == '/api/import' and method == 'POST':
		_json(response, cfg.UiImport(_body(request)))
	elif uri == '/api/scope':
		if method == 'POST':
			b = _body(request)
			_json(response, cfg.UiScope(b.get('value'), b.get('mode')))
		else:
			_json(response, cfg.UiScope())
	else:
		_json(response, {'ok': False, 'why': 'method not allowed: ' + uri}, 405)


def _servePicker(ext, uri, request, response):
	inst = ext._installerExt()
	if inst is None:
		if uri == '/tools':
			_html(response, NO_INSTALLER_HTML)
		else:
			_json(response, {'ok': False, 'why': 'no FNS_Installer in this project'}, 404)
		return response
	fwd = dict(request)
	if uri == '/tools':
		fwd['uri'] = '/'
	return inst.ServeRequest(fwd, response)


def onHTTPRequest(webServerDAT, request, response):
	uri = request.get('uri', '/')
	method = request.get('method', 'GET')
	try:
		ext = _ext(webServerDAT)
		ext._touchServer()
		if uri == '/':
			page = webServerDAT.parent().op(ext.PAGE_NAME)
			_html(response, page.text if page else 'console_page missing')
		elif uri == '/base.css':
			# the shared UI base for contributed tabs: link it from a tab
			# page served under /t/<name>/ to inherit the family palette
			# instead of re-declaring it (a tab that also runs outside the
			# console inlines its own synced copy -- see ColorUI)
			response['statusCode'], response['statusReason'] = 200, 'OK'
			response['Content-Type'] = 'text/css; charset=utf-8'
			response['data'] = ext.UiBaseCss()
		elif uri == '/api/tabs':
			# everything, hidden included: the page's bar shows what is
			# displayed, its tab manager lists the rest
			_json(response, {'ok': True, 'tabs': ext.Tabs(include_hidden=True)})
		elif uri == '/api/tabs/display' and method == 'POST':
			b = _body(request)
			_json(response, ext.SetTabDisplayed(b.get('name'), b.get('displayed')))
		elif uri == '/api/updates':
			_json(response, ext.UiUpdates())
		elif uri == '/api/updates/check' and method == 'POST':
			_json(response, ext.UiUpdatesCheck())
		elif uri == '/api/updates/apply' and method == 'POST':
			b = _body(request)
			_json(response, ext.UiUpdatesApply(b.get('names')))
		elif uri == '/api/updates/status':
			_json(response, ext.UiUpdatesStatus())
		elif uri in CONFIG_URIS:
			_serveConfig(ext, uri, method, request, response)
		elif uri == '/tools' or uri in PICKER_URIS:
			return _servePicker(ext, uri, request, response)
		elif uri.startswith('/t/'):
			canonical, _, sub = uri[3:].partition('/')
			res = ext.ServeTab(canonical, sub, method,
							   _body(request) if method == 'POST' else None)
			if 'html' in res:
				_html(response, res['html'], res.get('status', 200))
			else:
				_json(response, res.get('json'), res.get('status', 200))
		else:
			_json(response, {'ok': False, 'why': 'not found: ' + uri}, 404)
	except Exception as e:
		_json(response, {'ok': False, 'why': str(e)}, 500)
	return response
