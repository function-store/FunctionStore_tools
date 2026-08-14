"""onHTTPRequest for the ConfigRegistry settings server (settings_server).

Dumb dispatcher: resolve the registry extension, call its Ui* methods,
serialize. The page ships in the sibling `settings_page` DAT; no state and
no tool knowledge live here. The server itself is ephemeral -- see
OpenSettingsUI in ConfigRegistryExt.
"""

import json


def _ext(webServerDAT):
	# the global /sys registry is the API owner; fall back to our own comp
	# (its Ui* methods delegate to the global anyway)
	reg = getattr(op, 'CONFIGREGISTRY', None)
	if reg is None or not reg.valid:
		reg = webServerDAT.parent()
	return reg.ext.ConfigRegistryExt


def _json(response, payload, code=200):
	response['statusCode'] = code
	response['statusReason'] = 'OK' if code == 200 else 'Error'
	response['Content-Type'] = 'application/json'
	response['data'] = json.dumps(payload)


def onHTTPRequest(webServerDAT, request, response):
	uri = request.get('uri', '/')
	try:
		ext = _ext(webServerDAT)
		ext._touchSettingsServer()
		if uri == '/':
			page = webServerDAT.parent().op('settings_page')
			response['statusCode'] = 200
			response['statusReason'] = 'OK'
			response['Content-Type'] = 'text/html'
			response['data'] = page.text if page else 'settings_page missing'
		elif uri == '/api/state':
			_json(response, ext.UiState())
		elif uri == '/api/set' and request.get('method') == 'POST':
			body = json.loads(request.get('data') or '{}')
			_json(response, ext.UiSet(body.get('tool'), body.get('par'),
									  body.get('value')))
		else:
			_json(response, {'ok': False, 'why': 'not found: ' + uri}, 404)
	except Exception as e:
		_json(response, {'ok': False, 'why': str(e)}, 500)
	return response
