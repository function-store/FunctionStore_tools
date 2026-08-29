# Loopback listener for the sign-in redirect.
#
# The gate finishes the Patreon exchange (it holds the client secret) and
# bounces the browser here with a device token. This runs on TD's MAIN
# thread, so it does exactly two things: read the token and hand it to the
# extension. No network call, no disk work, nothing that can block --
# DOTsimulate ran a blocking token exchange in this exact callback and
# froze TouchDesigner for the length of a cold round trip, at the moment
# the user alt-tabbed back expecting to see something happen.

from urllib.parse import urlparse, parse_qs

_PAGE = """<!doctype html><meta charset="utf-8">
<title>FNSTools</title>
<style>
 body{{background:#141311;color:#eae7e2;font:16px/1.6 -apple-system,
      Segoe UI,Roboto,sans-serif;display:grid;place-items:center;
      height:100vh;margin:0;text-align:center}}
 .c{{max-width:32ch}} h1{{font-size:1.3rem;margin:0 0 .5em}}
 .m{{color:#8c8780;font-size:.9rem}}
</style>
<div class="c"><h1>{title}</h1><p class="m">{body}</p></div>
"""


def _page(title, body):
    return _PAGE.format(title=title, body=body)


def onHTTPRequest(webServerDAT, request, response):
    path = urlparse(request.get('uri', '/')).path
    if path not in ('/fns-auth', '/fns-auth/'):
        response['statusCode'] = 404
        response['statusReason'] = 'Not Found'
        response['data'] = _page('Not found', 'Nothing to see here.')
    else:
        q = parse_qs(urlparse(request.get('uri', '')).query)
        token = q.get('token', [''])[0]
        cn = q.get('cn', [''])[0]
        code = q.get('code', [''])[0]
        ok = False
        try:
            ok = bool(parent().ext.ExtAuth.OnAuthCallback(token, cn, code))
        except Exception as e:
            debug('AUTH callback failed: %s' % e)
        response['statusCode'] = 200 if ok else 400
        response['statusReason'] = 'OK' if ok else 'Bad Request'
        response['data'] = (
            _page('Sign-in received', 'You can close this tab -- TouchDesigner '
                  'is finishing sign-in.')
            if ok else
            _page('Sign-in failed', 'Go back to TouchDesigner and try again.'))
    response['content-type'] = 'text/html; charset=utf-8'
    return response


def onWebSocketOpen(webServerDAT, client, uri):
    return


def onWebSocketClose(webServerDAT, client):
    return


def onWebSocketReceiveText(webServerDAT, client, data):
    return


def onWebSocketReceiveBinary(webServerDAT, client, data):
    return


def onServerStart(webServerDAT):
    return


def onServerStop(webServerDAT):
    return
