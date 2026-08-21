"""onHTTPRequest for the ConfigRegistry settings server (settings_server).

Dumb dispatcher: resolve the registry extension, call its Ui* methods,
serialize. The page ships in the sibling `settings_page` DAT; no state and
no tool knowledge live here. The server itself is ephemeral -- see
OpenSettingsUI in ConfigRegistryExt.

The console also fronts the FNS_Installer picker when the project ships
one: /tools serves the installer's own configurator page, and the picker's
endpoints (/manifest.js, /selection, /status, /install) forward to
InstallerExt.ServeRequest unchanged -- one origin, one port, zero
duplicated picker logic. Without an installer those routes answer with a
plain explanation instead of a broken tab.
"""

import json


def _ext(webServerDAT):
	# the global /sys registry is the API owner; fall back to our own comp
	# (its Ui* methods delegate to the global anyway)
	reg = getattr(op, 'FNS_CONFIGREGISTRY', None)
	if reg is None or not reg.valid:
		reg = webServerDAT.parent()
	return reg.ext.ConfigRegistryExt


def _json(response, payload, code=200):
	response['statusCode'] = code
	response['statusReason'] = 'OK' if code == 200 else 'Error'
	response['Content-Type'] = 'application/json'
	response['data'] = json.dumps(payload)


def _html(response, text):
	response['statusCode'] = 200
	response['statusReason'] = 'OK'
	response['Content-Type'] = 'text/html'
	response['data'] = text


def _body(request):
	data = request.get('data') or '{}'
	if isinstance(data, bytes):
		data = data.decode('utf-8')
	return json.loads(data)


def _installer(ext):
	comp = ext._installerComp()
	if comp is None:
		return None
	try:
		return comp.ext.InstallerExt
	except Exception:
		return None


# picker endpoints owned by InstallerExt.ServeRequest, forwarded verbatim
PICKER_URIS = ('/manifest.js', '/selection', '/status', '/install')

NO_INSTALLER_HTML = (
	'<!doctype html><body style="background:#191b1e;color:#8a8f98;'
	'font:14px/1.6 sans-serif;padding:40px;max-width:60ch">'
	'<h3 style="color:#d6d9de">No installer in this project</h3>'
	'This project has no <code>FNS_Installer</code> COMP, so tools cannot '
	'be added or removed from here. Drop the FNSTools bootstrap (or the '
	'bare <code>FNS_Installer.tox</code>) into the project and reload this '
	'tab. Settings on the other tab keep working either way.</body>')


def onHTTPRequest(webServerDAT, request, response):
	uri = request.get('uri', '/')
	method = request.get('method', 'GET')
	try:
		ext = _ext(webServerDAT)
		ext._touchSettingsServer()
		if uri == '/':
			page = webServerDAT.parent().op('settings_page')
			_html(response, page.text if page else 'settings_page missing')
		elif uri == '/api/state':
			_json(response, ext.UiState())
		elif uri == '/api/set' and method == 'POST':
			body = _body(request)
			_json(response, ext.UiSet(body.get('tool'), body.get('par'),
									  body.get('value')))
		elif uri == '/api/export':
			_json(response, ext.UiExport())
		elif uri == '/api/import' and method == 'POST':
			_json(response, ext.UiImport(_body(request)))
		elif uri == '/api/scope':
			if method == 'POST':
				body = _body(request)
				_json(response, ext.UiScope(body.get('value'), body.get('mode')))
			else:
				_json(response, ext.UiScope())
		elif uri == '/tools' or uri in PICKER_URIS:
			inst = _installer(ext)
			if inst is None:
				if uri == '/tools':
					_html(response, NO_INSTALLER_HTML)
				else:
					_json(response, {'ok': False,
									 'why': 'no FNS_Installer in this project'},
						  404)
			else:
				fwd = dict(request)
				if uri == '/tools':
					fwd['uri'] = '/'
				return inst.ServeRequest(fwd, response)
		else:
			_json(response, {'ok': False, 'why': 'not found: ' + uri}, 404)
	except Exception as e:
		_json(response, {'ok': False, 'why': str(e)}, 500)
	return response
