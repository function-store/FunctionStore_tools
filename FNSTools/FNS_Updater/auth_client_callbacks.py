# Web Client DAT callbacks for the gate's JSON API.
#
# Dispatch is by the URL that was requested, because one client serves both
# /token/download and /gumroad/redeem and the arriving response is the only
# thing that says which it was.

UNREACHABLE = b'{"message":"could not reach the gate"}'


def _ext():
    return parent().ext.ExtAuth


def _route(webClientDAT, statusCode, data):
    """Hand a payload to the handler for the request that produced it.

    One client serves both endpoints, so the requested URL is the only
    thing that says which handler owns an arriving response. Returns False
    when nothing matched, so each caller can log in its own words.
    """
    url = str(webClientDAT.par.url.eval())
    if url.endswith('/token/download'):
        _ext().OnTokenResponse(statusCode, data)
    elif url.endswith('/gumroad/redeem'):
        _ext().OnRedeemResponse(statusCode, data)
    elif url.endswith('/session/revoke'):
        _ext().OnRevokeResponse(statusCode, data)
    elif url.endswith('/session/claim'):
        _ext().OnClaimResponse(statusCode, data)
    else:
        return False
    return True


def onConnect(webClientDAT, statusCode, headerDict, data, id):
    return


def onResponse(webClientDAT, statusCode, headerDict, data, id):
    try:
        if not _route(webClientDAT, statusCode, data):
            debug('AUTH: unexpected response from %s' % webClientDAT.par.url.eval())
    except Exception as e:
        debug('AUTH: response handler failed (%s)' % e)
    return


def onError(webClientDAT, statusCode, headerDict, data, id):
    # A transport failure is NOT a refusal: reaching nobody must never be
    # reported as "you are not entitled". Both handlers already read this
    # shape as a plain refusal carrying a human sentence.
    #
    # ROUTED, not hardcoded to the token handler. Sending every failure to
    # OnTokenResponse meant an unreachable gate during a licence redemption
    # reported through the wrong path and never cleared _redeem_pending --
    # so the tool believed a check was still in flight for the rest of the
    # session, and a retry looked like it did nothing.
    try:
        if not _route(webClientDAT, statusCode, UNREACHABLE):
            debug('AUTH: transport error from %s' % webClientDAT.par.url.eval())
    except Exception as e:
        debug('AUTH: error handler failed (%s)' % e)
    return
