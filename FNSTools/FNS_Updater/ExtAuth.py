"""Sign-in and entitlement for gated packages.

A SECOND extension on FNS_Updater rather than a package of its own: the
updater is the only thing in TouchDesigner that touches the network
(GatedDeliveryResearch 1), so the credential belongs beside it and nowhere
else. Keeping it in its own DAT keeps ExtUpdater about updating.

WHAT THIS HOLDS is an opaque device token in the OS keystore, and a
short-lived download token in memory only. It never sees a Patreon secret
(the gate holds that -- Patreon's token exchange requires a client secret
and has no PKCE, which is the whole reason a gate exists) and never a
Patreon refresh token.

THE CLIENT NEVER DECIDES ACCESS. It reads its own entitlement list only to
say WHICH tier is missing in a refusal, because "not entitled" tells a
paying customer nothing. Anything it cannot read fails OPEN -- it must
never invent a lockout the gate did not decide. The gate fails closed.

TRANSPORT is TD's Web Client DAT, not urllib on a worker: async by
construction, ships with TD, and cannot block the frame. DOTsimulate ran a
blocking token exchange inline in a Web Server callback and froze TD; that
is the failure this avoids by construction rather than by care.
"""

import json
import secrets
import time

# The one address this component knows. Baked into every shipped copy, so
# it carries the same generation contract as DISCOVERY_PINS: moving the
# gate after a release cannot reach installs already in the field. Swap it
# here, in worker/wrangler.toml, and in the Patreon client's redirect URI
# together -- all three name the same host or sign-in breaks.
DEFAULT_GATE = 'https://gate.functionstore.tools'

# Loopback ports for the sign-in callback. Same range and same reason as
# FNS_ConfigRegistry's settings page: a fixed single port breaks the moment
# a second TouchDesigner is open, which for TD users is most of the time.
CALLBACK_PORTS = tuple(range(9881, 9891))
# A Web Server DAT with a BLANK Local Address listens on EVERY interface, not
# just loopback (Derivative: "When left blank, the Web Server DAT will listen
# on all interfaces"). _freePort below binds 127.0.0.1 only to TEST that a
# port is free and closes it again -- it does not constrain the server. Left
# blank, /fns-auth was reachable from the network, and it hands whatever
# `token` arrives straight to the OS keystore.
BIND_ADDRESS = '127.0.0.1'
# The browser round-trip is a human typing a password. Generous, but not
# unbounded: a listener left open is a port held and a promise unkept.
SIGNIN_TIMEOUT = 300
# Download tokens are minted short by the gate; re-ask a little early so a
# long update pass never dies holding one that expired mid-flight.
TOKEN_EARLY_REFRESH = 60


def fnsLog(*args, level='INFO'):
	try:
		lg = op.FNS.op('logger')
		if lg and lg.par.Active.eval():
			lg.Log(*args, level=level)
	except Exception:
		pass


class ExtAuth:
	"""Entitlement state for this install."""

	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self._download_token = ''
		self._download_expires = 0.0
		self._signin = None          # in-flight sign-in, or None
		fnsLog('AUTH: init')

	# ------------------------------------------------------------------
	# where things live
	# ------------------------------------------------------------------

	def _par(self, name, default=''):
		p = getattr(self.ownerComp.par, name, None)
		if p is None:
			return default
		return str(p.eval()).strip() or default

	def GateUrl(self):
		return self._par('Gateurl', DEFAULT_GATE).rstrip('/')

	def _storageDir(self):
		"""Machine-local, beside the package store. Only the macOS backend
		ignores it; on Windows this is where the DPAPI blob sits."""
		v = self._par('Storefolder')
		if not v:
			v = '%s/FNStools_ext' % app.userPaletteFolder
		return v.replace('\\', '/').rstrip('/')

	def _storage(self):
		d = self.ownerComp.op('secure_storage')
		return d.module if d is not None else None

	# ------------------------------------------------------------------
	# what this install is entitled to
	# ------------------------------------------------------------------

	def Account(self):
		"""The stored account record, or None. Reading it is cheap enough
		to do per call and avoids a cache that can disagree with the
		keystore after a Sign Out in another project."""
		s = self._storage()
		if s is None:
			return None
		try:
			return s.Load(self._storageDir())
		except Exception as e:
			fnsLog('AUTH: keystore unreadable (%s)' % e, level='WARNING')
			return None

	def IsSignedIn(self):
		return self.Account() is not None

	def Entitlements(self):
		"""Package names this install may download. Empty when signed out
		-- and empty is NOT a refusal to show them, only a refusal to
		fetch: a locked package still appears in the picker."""
		acct = self.Account() or {}
		return list(acct.get('products') or [])

	def IsEntitled(self, package):
		return package in self.Entitlements()

	def MissingFor(self, package):
		"""What to TELL someone who cannot have this package. The client
		reads its claim only for this."""
		if not self.IsSignedIn():
			return 'Sign in to download %s.' % package
		return ('Your current tier does not include %s.' % package)

	def AuthStatus(self):
		acct = self.Account()
		if acct is None:
			return 'signed out'
		n = len(acct.get('products') or [])
		label = acct.get('label') or 'supporter'
		return '%s -- %d package%s' % (label, n, '' if n == 1 else 's')

	# ------------------------------------------------------------------
	# the download token (short-lived, in memory only)
	# ------------------------------------------------------------------

	def CachedToken(self):
		"""A still-valid download token, or ''. Never written to disk: it
		lives minutes and a copy on disk would outlive its usefulness while
		remaining a credential."""
		if self._download_token and time.time() < self._download_expires - TOKEN_EARLY_REFRESH:
			return self._download_token
		return ''

	def RequestToken(self, callback=None):
		"""Ask the gate for a download token. ASYNC -- `callback` is called
		with (ok, token_or_reason) on a later frame.

		Returns a dict describing what it started, never the token: a
		synchronous return would mean a blocking request, which is the one
		thing this must not do."""
		cached = self.CachedToken()
		if cached:
			if callback:
				callback(True, cached)
			return {'ok': True, 'why': 'cached'}
		acct = self.Account()
		if acct is None:
			if callback:
				callback(False, 'signed out')
			return {'ok': False, 'why': 'signed out'}
		wc = self._client()
		if wc is None:
			if callback:
				callback(False, 'no auth client')
			return {'ok': False, 'why': 'no auth client'}
		self._token_cb = callback
		wc.par.authtype = 'oauth2'
		wc.par.token = acct['device_token']
		wc.request('%s/token/download' % self.GateUrl(), 'POST',
				   header={'content-type': 'application/json'}, data='{}')
		return {'ok': True, 'why': 'requesting (async)'}

	def OnTokenResponse(self, statusCode, data):
		"""Web Client DAT callback for /token/download."""
		cb, self._token_cb = getattr(self, '_token_cb', None), None
		ok, payload = self._readJson(statusCode, data)
		if not ok:
			fnsLog('AUTH: token refused (%s)' % payload, level='WARNING')
			if cb:
				cb(False, payload)
			return
		self._download_token = str(payload.get('token', ''))
		self._download_expires = time.time() + float(payload.get('expires_in', 0) or 0)
		# The gate is authoritative about entitlement, so a token response
		# is also the freshest product list we will ever see -- record it,
		# or the picker keeps showing a tier the user has since changed.
		self._rememberProducts(payload.get('products'))
		if cb:
			cb(bool(self._download_token), self._download_token or 'empty token')

	def _readJson(self, statusCode, data):
		"""(ok, payload-or-message). A gate refusal carries a human
		sentence; anything else must not be shown raw."""
		try:
			body = json.loads(data.decode('utf-8') if isinstance(data, bytes) else str(data))
		except Exception:
			return False, 'the gate returned something unreadable'
		code = int((statusCode or {}).get('code', 0) or 0) if isinstance(statusCode, dict) else int(statusCode or 0)
		if code == 200 and body.get('ok'):
			return True, body
		return False, str(body.get('message') or 'request failed (%s)' % code)

	def _rememberProducts(self, products):
		if products is None:
			return
		acct = self.Account()
		if acct is None:
			return
		s = self._storage()
		try:
			s.Store(self._storageDir(), acct['device_token'],
					products=products, tiers=acct.get('tiers'),
					label=acct.get('label', ''))
		except Exception as e:
			fnsLog('AUTH: could not update entitlements (%s)' % e, level='WARNING')

	# ------------------------------------------------------------------
	# sign in / out
	# ------------------------------------------------------------------

	def SignIn(self):
		"""Open the browser and listen on loopback for the gate to hand
		back a device token.

		The redirect registered with Patreon is the GATE's, not ours -- only
		the gate may hold the client secret. It bounces back here with the
		port it was given, so nothing about this flow needs a fixed port."""
		if self._signin is not None:
			return {'ok': False, 'why': 'a sign-in is already in progress'}
		ws = self._ensureServer()
		if ws is None:
			return {'ok': False, 'why': 'could not create the callback listener'}
		port = self._freePort()
		if port is None:
			return {'ok': False, 'why': 'no free loopback port in %s' % (CALLBACK_PORTS,)}
		ws.par.port = port
		ws.par.active = True
		# The nonce rides to the gate, through the OAuth exchange, and back
		# to the loopback listener -- which accepts a token only when it
		# returns matching. The gate's own `state` nonce protects the gate;
		# this one protects the LISTENER (see OnAuthCallback).
		nonce = secrets.token_urlsafe(24)
		self._signin = {'port': port, 'at': absTime.seconds, 'nonce': nonce}
		url = '%s/patreon/start?port=%d&cn=%s' % (self.GateUrl(), port, nonce)
		import webbrowser
		webbrowser.open(url)
		self._setStatus('waiting for the browser...')
		run('args[0].ext.ExtAuth._signinTimeout(%d)' % port, self.ownerComp,
			delayFrames=60, delayRef=op.TDResources)
		return {'ok': True, 'url': url, 'port': port}

	def OnAuthCallback(self, token, cn='', code=''):
		"""The gate redirected back to loopback.

		Accepted only when the callback carries the nonce THIS sign-in
		minted: the gate echoes it back, and nothing else that finds the
		port can know it. Loopback-only (BIND_ADDRESS) is the first
		boundary; this is the second, and it also covers a browser being
		scripted into hitting the listener. A mismatch refuses WITHOUT
		tearing down the pending sign-in -- the real redirect may still be
		on its way, and a stray request must not be able to cancel it.

		The redirect normally carries a one-time `code`, not the device
		token -- a token in a URL lands in browser history. The code is
		exchanged async via POST /session/claim (OnClaimResponse stores the
		result). A bare `token` is still honoured for an older gate."""
		expected = (self._signin or {}).get('nonce', '')
		if expected and cn != expected:
			fnsLog('AUTH: callback nonce mismatch -- refused', level='ERROR')
			return False
		self._closeServer()
		self._signin = None
		if code:
			wc = self._client()
			if wc is None:
				self._setStatus('sign-in failed (no auth client)')
				return False
			wc.par.authtype = 'none'
			wc.request('%s/session/claim' % self.GateUrl(), 'POST',
					   header={'content-type': 'application/json'},
					   data=json.dumps({'code': code}))
			self._setStatus('finishing sign-in...')
			return True
		if not token:
			self._setStatus('sign-in failed')
			return False
		return self._storeDeviceToken(token)

	def OnClaimResponse(self, statusCode, data):
		"""Web Client DAT callback for /session/claim."""
		ok, payload = self._readJson(statusCode, data)
		if not ok:
			self._setStatus(str(payload))
			fnsLog('AUTH: sign-in claim refused (%s)' % payload, level='WARNING')
			return
		self._storeDeviceToken(str(payload.get('device_token', '')))

	def _storeDeviceToken(self, token):
		if not token:
			self._setStatus('sign-in failed')
			return False
		s = self._storage()
		if s is None or not s.available():
			self._setStatus('no keystore on this platform')
			fnsLog('AUTH: no OS keystore; cannot stay signed in', level='ERROR')
			return False
		s.Store(self._storageDir(), token)
		self._setStatus('signed in')
		fnsLog('AUTH: signed in')
		# Entitlements arrive with the first token request, not here.
		self.RequestToken()
		return True

	def SignOut(self):
		# Revoke AT THE GATE before forgetting locally: a sign-out that
		# only clears the keystore leaves the device token valid forever,
		# which is a promise the button's label makes and must keep
		# (docs/EntitlementLifecycle.md 4). Best-effort and async -- an
		# offline sign-out still signs out locally, and the session row's
		# TTL bounds what a missed revoke costs.
		acct = self.Account()
		wc = self._client()
		if wc is not None and acct and acct.get('device_token'):
			try:
				wc.par.authtype = 'oauth2'
				wc.par.token = acct['device_token']
				wc.request('%s/session/revoke' % self.GateUrl(), 'POST',
						   header={'content-type': 'application/json'}, data='{}')
			except Exception as e:
				fnsLog('AUTH: revoke request failed to start (%s)' % e,
					   level='WARNING')
		s = self._storage()
		if s is not None:
			s.Clear(self._storageDir())
		self._download_token, self._download_expires = '', 0.0
		self._closeServer()
		self._setStatus('signed out')
		fnsLog('AUTH: signed out')
		return {'ok': True}

	def OnRevokeResponse(self, statusCode, data):
		"""Web Client DAT callback for /session/revoke. The local copy is
		gone by the time this arrives, so the outcome is only worth a log
		line -- a revoke that never landed is bounded by the row's TTL."""
		ok, why = self._readJson(statusCode, data)
		fnsLog('AUTH: gate revoke %s' % ('confirmed' if ok else 'not confirmed (%s)' % why),
			   level='INFO' if ok else 'WARNING')

	def RedeemKey(self, key=None, product=None):
		"""Redeem one Gumroad licence key.

		Keys are PER TOOL by decision, so redeeming EXTENDS the account
		rather than replacing it -- five tools means five keys on one
		install, and the gate merges them onto one device token."""
		key = (key or self._par('Licensekey')).strip()
		product = (product or self._par('Licenseproduct')).strip()
		if not key:
			return {'ok': False, 'why': 'no licence key given'}
		if not product:
			return {'ok': False, 'why': 'no product id given'}
		wc = self._client()
		if wc is None:
			return {'ok': False, 'why': 'no auth client'}
		acct = self.Account() or {}
		wc.par.authtype = 'none'
		body = {'license_key': key, 'product_id': product}
		if acct.get('device_token'):
			body['device_token'] = acct['device_token']
		self._redeem_pending = True
		wc.request('%s/gumroad/redeem' % self.GateUrl(), 'POST',
				   header={'content-type': 'application/json'},
				   data=json.dumps(body))
		self._setStatus('checking licence...')
		return {'ok': True, 'why': 'checking (async)'}

	def OnRedeemResponse(self, statusCode, data):
		self._redeem_pending = False
		ok, payload = self._readJson(statusCode, data)
		if not ok:
			self._setStatus(str(payload))
			fnsLog('AUTH: licence refused (%s)' % payload, level='WARNING')
			return
		s = self._storage()
		if s is None:
			return
		# Store() defaults tiers and label to EMPTY, and a key EXTENDS an
		# account rather than replacing it (the gate merges both onto one
		# device token) -- so writing only `products` here silently dropped
		# the Patreon half of a mixed account: a patron who redeemed a key
		# lost their tier list and their display label. Carry them across,
		# the same way _rememberProducts already does.
		prior = self.Account() or {}
		if prior.get('device_token') not in (None, '', payload['device_token']):
			prior = {}      # the gate handed back a DIFFERENT session; its
							# tiers and label are not this account's
		s.Store(self._storageDir(), payload['device_token'],
				products=payload.get('products'),
				tiers=prior.get('tiers'), label=prior.get('label', ''))
		self._download_token, self._download_expires = '', 0.0
		self._setStatus('licence accepted')
		fnsLog('AUTH: licence redeemed (%d package(s))'
			   % len(payload.get('products') or []))

	# ------------------------------------------------------------------
	# parameter callbacks
	#
	# extensionParExec dispatches onPulse(par) to a promoted method named
	# EXACTLY like the parameter, so these thin wrappers exist to keep the
	# real API intent-named (SignIn) while the par stays TD-cased (Signin).
	# ------------------------------------------------------------------

	def Signin(self, par):
		self.SignIn()

	def Signout(self, par):
		self.SignOut()

	def Redeemlicense(self, par):
		self.RedeemKey()

	# ------------------------------------------------------------------
	# the loopback listener
	# ------------------------------------------------------------------

	def _client(self):
		return self.ownerComp.op('auth_client')

	def _ensureServer(self):
		comp = self.ownerComp
		ws = comp.op('auth_server')
		if ws is None:
			ws = comp.create(webserverDAT, 'auth_server')
			ws.par.active = False
			# create() spawns its own empty callbacks DAT named for the
			# server; left alone it squats where ours belongs and the
			# server answers nothing.
			auto = ws.par.callbacks.eval()
			if auto is not None and auto.name.startswith('auth_server_callbacks'):
				try:
					auto.destroy()
				except Exception:
					pass
			src = comp.op('auth_callbacks')
			if src is not None:
				ws.par.callbacks = src
			ws.nodeX, ws.nodeY = 400, -400
		# Unconditional, not just on the create branch: a server already in
		# the .toe or in a .tox published before this line carries the old
		# blank value, and only re-asserting repairs those. See BIND_ADDRESS.
		try:
			if str(ws.par.localaddress.eval()) != BIND_ADDRESS:
				ws.par.localaddress = BIND_ADDRESS
		except Exception as e:
			fnsLog('AUTH: could not pin %s to %s (%s) -- it may be reachable '
				   'from the network' % (ws.path, BIND_ADDRESS, e), level='ERROR')
		return ws

	def _closeServer(self):
		ws = self.ownerComp.op('auth_server')
		if ws is not None:
			ws.par.active = False

	def _freePort(self):
		import socket
		for port in CALLBACK_PORTS:
			s = socket.socket()
			try:
				s.bind(('127.0.0.1', port))
				s.close()
				return port
			except OSError:
				s.close()
		return None

	def _signinTimeout(self, port):
		"""Never leave a listener open. A browser tab the user abandoned
		must not hold a port for the rest of the session."""
		job = self._signin
		if job is None or job.get('port') != port:
			return
		if absTime.seconds - job['at'] < SIGNIN_TIMEOUT:
			run('args[0].ext.ExtAuth._signinTimeout(%d)' % port, self.ownerComp,
				delayFrames=60, delayRef=op.TDResources)
			return
		self._signin = None
		self._closeServer()
		self._setStatus('sign-in timed out')
		fnsLog('AUTH: sign-in timed out after %ds' % SIGNIN_TIMEOUT, level='WARNING')

	def _setStatus(self, text):
		p = getattr(self.ownerComp.par, 'Authstatus', None)
		if p is not None:
			p.val = text
