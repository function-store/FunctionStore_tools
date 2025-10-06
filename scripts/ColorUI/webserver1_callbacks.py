# me - this DAT.
# webServerDAT - the connected Web Server DAT
# request - A dictionary of the request fields. The dictionary will always contain the below entries, plus any additional entries dependent on the contents of the request
# 		'method' - The HTTP method of the request (ie. 'GET', 'PUT').
# 		'uri' - The client's requested URI path. If there are parameters in the URI then they will be located under the 'pars' key in the request dictionary.
#		'pars' - The query parameters.
# 		'clientAddress' - The client's address.
# 		'serverAddress' - The server's address.
# 		'data' - The data of the HTTP request.
# response - A dictionary defining the response, to be filled in during the request method. Additional fields not specified below can be added (eg. response['content-type'] = 'application/json').
# 		'statusCode' - A valid HTTP status code integer (ie. 200, 401, 404). Default is 404.
# 		'statusReason' - The reason for the above status code being returned (ie. 'Not Found.').
# 		'data' - The data to send back to the client. If displaying a web-page, any HTML would be put here.

import json

# return the response dictionary
def onHTTPRequest(webServerDAT, request, response):
    response['statusCode'] = 200  # OK
    response['statusReason'] = 'OK'
    response['content-type'] = 'text/plain; charset=utf-8'
    response['Access-Control-Allow-Origin'] = '*'

    uri = request.get('uri', '/')
    pars = request.get('pars', {}) or {}

    def get_ext():
        try:
            return ext.ExtColorUI
        except Exception:
            return None

    # Serve index HTML
    if uri == '/':
        idx = op('index')
        response['content-type'] = 'text/html; charset=utf-8'
        response['data'] = idx.text if idx is not None else '<b>Index DAT not found</b>'
        return response

    # Health
    if uri == '/api/ping':
        response['content-type'] = 'application/json'
        response['data'] = json.dumps({'ok': True})
        return response

    # Search API
    if uri == '/api/search':
        response['content-type'] = 'application/json'
        term = pars.get('term', '') if isinstance(pars, dict) else ''
        if not term:
            response['statusCode'] = 400
            response['statusReason'] = 'Bad Request'
            response['data'] = json.dumps({'error': 'Missing query parameter: term'})
            return response

        ext_color_ui = get_ext()
        if not ext_color_ui:
            response['statusCode'] = 500
            response['statusReason'] = 'Server Error'
            response['data'] = json.dumps({'error': 'ExtColorUI extension not found on parent component'})
            return response

        try:
            results = ext_color_ui.searchColorKeys(term)
            # results is list[(key, color)]
            def to_norm_rgb(c):
                vals = [float(v) for v in c]
                if any(v > 1.0 for v in vals):
                    vals = [max(0.0, min(1.0, v / 255.0)) for v in vals]
                else:
                    vals = [max(0.0, min(1.0, v)) for v in vals]
                return vals

            def to_hex(rgb):
                r, g, b = [int(round(v * 255)) for v in rgb]
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                return '#%02X%02X%02X' % (r, g, b)

            out = []
            for key, color in results:
                rgb = to_norm_rgb(color)
                out.append({'key': key, 'rgb': rgb, 'hex': to_hex(rgb)})
            response['data'] = json.dumps({'term': term, 'count': len(out), 'results': out})
        except Exception as e:
            response['statusCode'] = 500
            response['statusReason'] = 'Server Error'
            response['data'] = json.dumps({'error': 'Search failed', 'detail': str(e)})
        return response

    # Set color API
    if uri == '/api/set':
        # CORS preflight
        if request.get('method', 'GET').upper() == 'OPTIONS':
            response['statusCode'] = 200
            response['statusReason'] = 'OK'
            response['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
            response['Access-Control-Allow-Headers'] = 'content-type'
            response['content-type'] = 'application/json'
            response['data'] = json.dumps({'ok': True})
            return response

        response['content-type'] = 'application/json'

        def to_norm_rgb_from_any(val):
            # Accept [r,g,b] in 0..1 or 0..255
            try:
                vals = [float(v) for v in val]
            except Exception:
                return None
            if any(v > 1.0 for v in vals):
                vals = [max(0.0, min(1.0, v / 255.0)) for v in vals]
            else:
                vals = [max(0.0, min(1.0, v)) for v in vals]
            return vals

        def parse_hex(s):
            try:
                t = s.strip().lstrip('#')
                if len(t) == 3:
                    t = ''.join(ch*2 for ch in t)
                if len(t) != 6:
                    return None
                r = int(t[0:2], 16)
                g = int(t[2:4], 16)
                b = int(t[4:6], 16)
                return to_norm_rgb_from_any([r, g, b])
            except Exception:
                return None

        def to_hex(rgb):
            r, g, b = [int(round(max(0.0, min(1.0, v)) * 255)) for v in rgb]
            return '#%02X%02X%02X' % (r, g, b)

        # Parse body if present
        body = request.get('data')
        body_json = None
        if body is not None:
            try:
                if hasattr(body, 'decode'):
                    body = body.decode('utf-8', errors='ignore')
                body_json = json.loads(body)
            except Exception:
                body_json = None

        ext_color_ui = get_ext()
        if not ext_color_ui:
            response['statusCode'] = 500
            response['statusReason'] = 'Server Error'
            response['data'] = json.dumps({'error': 'ExtColorUI extension not found on parent component'})
            return response

        updates = []
        if isinstance(body_json, dict) and 'updates' in body_json and isinstance(body_json['updates'], list):
            updates = body_json['updates']
        elif isinstance(body_json, dict) and ('key' in body_json or 'uicolor' in body_json):
            updates = [body_json]
        else:
            # fallback to query parameters for GET style: key, hex or rgb
            key = pars.get('key') or pars.get('uicolor')
            if key:
                upd = {'key': key}
                if 'hex' in pars:
                    upd['hex'] = pars.get('hex')
                elif 'rgb' in pars:
                    upd['rgb'] = [v.strip() for v in str(pars.get('rgb')).split(',') if v is not None]
                else:
                    r = pars.get('r'); g = pars.get('g'); b = pars.get('b')
                    if r is not None and g is not None and b is not None:
                        upd['rgb'] = [r, g, b]
                updates = [upd]

        if not updates:
            response['statusCode'] = 400
            response['statusReason'] = 'Bad Request'
            response['data'] = json.dumps({'error': 'No updates provided'})
            return response

        results = []
        for upd in updates:
            key = upd.get('key') or upd.get('uicolor')
            rgb = None
            if key is None:
                results.append({'ok': False, 'error': 'Missing key'})
                continue
            if 'hex' in upd and upd['hex'] is not None:
                rgb = parse_hex(str(upd['hex']))
            if rgb is None and 'rgb' in upd and upd['rgb'] is not None:
                rgb = to_norm_rgb_from_any(upd['rgb'])
            if rgb is None:
                results.append({'ok': False, 'key': key, 'error': 'Missing or invalid color (hex or rgb)'})
                continue

            try:
                ok = ext_color_ui.setColor(key, rgb)
                if ok:
                    results.append({'ok': True, 'key': key, 'rgb': rgb, 'hex': to_hex(rgb)})
                else:
                    results.append({'ok': False, 'key': key, 'error': 'Unknown UI color key'})
            except Exception as e:
                results.append({'ok': False, 'key': key, 'error': str(e)})

        response['data'] = json.dumps({'count': len(results), 'results': results})
        return response

    # 404
    response['statusCode'] = 404
    response['statusReason'] = 'Not Found'
    response['data'] = 'Not Found: ' + uri
    return response

def onWebSocketOpen(webServerDAT, client, uri):
	return

def onWebSocketClose(webServerDAT, client):
	return

def onWebSocketReceiveText(webServerDAT, client, data):
	webServerDAT.webSocketSendText(client, data)
	return

def onWebSocketReceiveBinary(webServerDAT, client, data):
	webServerDAT.webSocketSendBinary(client, data)
	return

def onWebSocketReceivePing(webServerDAT, client, data):
	webServerDAT.webSocketSendPong(client, data=data);
	return

def onWebSocketReceivePong(webServerDAT, client, data):
	return

def onServerStart(webServerDAT):
	return

def onServerStop(webServerDAT):
	return
	