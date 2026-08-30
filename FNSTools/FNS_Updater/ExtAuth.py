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
		# Entitlement as something a PARAMETER EXPRESSION can depend on.
		# A plain attribute cannot serve that: an expression reading it
		# evaluates once and never hears about the change. Reading a
		# tdu.Dependency's .val registers the dependency, so assigning it
		# later invalidates every expression that read it -- which is how
		# a UI can reflect sign-in by REFERENCE instead of being written
		# to by this extension reaching across the network.
		self._plus = tdu.Dependency(False)
		self._refreshPlus()
		fnsLog('AUTH: init')

	# ------------------------------------------------------------------
	# entitlement as a dependency
	# ------------------------------------------------------------------

	@property
	def Plusactive(self):
		"""True when this install holds at least one entitled package.

		Read it from a parameter expression -- e.g. a colour that is
		yellow for a supporter and red otherwise:

			1 if getattr(op.FNS.op('FNS_Updater'), 'Plusactive', 0) else 0

		getattr's default covers both the updater being absent (it is a
		separate rail and may not be installed) and extensions not yet
		initialised, which is the same guard `extensionsReady` gives.
		"""
		return bool(self._plus.val)

	def _refreshPlus(self):
		"""Re-read entitlement into the dependency. Cheap, main-thread.

		Called from _setStatus, which is the single funnel every state
		change already passes through -- sign-in, sign-out, licence
		accepted -- so no caller has to remember this exists.
		"""
		try:
			self._plus.val = bool(self.Entitlements())
		except Exception:
			self._plus.val = False

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

	def _gateRequest(self, wc, url, data='{}', token=None):
		"""POST to the gate. Two measured truths (2026-08-29) live here:

		request() does not write par.url -- after every call it still
		held the DAT's factory default -- and auth_client_callbacks
		routes an arriving response BY that par, so the URL is recorded
		first or every response drops as 'unexpected'.

		And the DAT's auth PARS are ignored by scripted request():
		authtype 'oauth2' + a token par sent NO Authorization header at
		all (captured on a local listener), while the authType/
		oauth2Token KWARGS send the bearer. Auth therefore rides the
		call, never the pars."""
		wc.par.url = url
		kw = {'header': {'content-type': 'application/json'}, 'data': data}
		if token:
			kw['authType'] = 'oauth2'
			kw['oauth2Token'] = token
		wc.request(url, 'POST', **kw)

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
	# the shared machine session (G7 -- TDXLUGateIntegration.md)
	#
	# One sign-in serves every FNS product on this machine. The channel
	# is a small JSON file BESIDE the config (never under store/ -- the
	# store is a wipeable mirror): {schema, device_token, written_by,
	# written_at}. Rules, per the launcher contract's §5: written
	# atomically on every successful sign-in; adopted by a product
	# holding no session; deleted when the gate says signed_out; on
	# sign-out, revoke first and delete only if the file still holds the
	# token that was just revoked (never clobber a newer sign-in).
	# The token here is OPAQUE and REVOCABLE -- weaker at rest than the
	# DPAPI keystore that remains our own copy, and accepted as the
	# interop cost by decision (both products pre-release, 2026-08-30).
	# ------------------------------------------------------------------

	def _sharedSessionPath(self):
		"""ALWAYS the machine's default palette location -- never the
		Storefolder override. Sharing is a machine-level contract: the
		launcher derives <user palette>/FNStools_ext independently, so a
		custom Storefolder here would mean two different files and
		sharing that silently never happens (launcher review, G7)."""
		return ('%s/FNStools_ext/config/gate-session.json'
				% app.userPaletteFolder).replace('\\', '/')

	def _readSharedSession(self):
		"""The shared file's record, or None -- unreadable is absent."""
		try:
			with open(self._sharedSessionPath(), 'r', encoding='utf-8') as f:
				doc = json.load(f)
			tok = str(doc.get('device_token') or '')
			return doc if tok else None
		except Exception:
			return None

	def _publishSharedSession(self, token):
		"""Atomic write on every successful sign-in, so a crash mid-write
		can never leave a half token for another product to adopt."""
		import os
		path = self._sharedSessionPath()
		try:
			os.makedirs(os.path.dirname(path), exist_ok=True)
			tmp = path + '.tmp'
			with open(tmp, 'w', encoding='utf-8') as f:
				json.dump({'schema': 1, 'device_token': token,
						   'written_by': 'FNSTools',
						   'written_at': time.time()}, f, indent=1)
			os.replace(tmp, path)
		except Exception as e:
			fnsLog('AUTH: could not publish the shared session (%s)' % e,
				   level='WARNING')

	def _dropSharedSession(self, only_token=None):
		"""Delete the shared file. With only_token, delete ONLY when the
		file still holds that token -- a newer sign-in by another product
		is not ours to destroy."""
		import os
		try:
			if only_token is not None:
				doc = self._readSharedSession()
				if doc is None or doc.get('device_token') != only_token:
					return
			os.remove(self._sharedSessionPath())
		except FileNotFoundError:
			pass
		except Exception as e:
			fnsLog('AUTH: could not drop the shared session (%s)' % e,
				   level='WARNING')

	def _adoptSharedSession(self):
		"""Holding no session, take the machine's -- once per extension
		lifetime, so the file read does not ride every Account() call.
		Products are unknown at adoption; a deferred token request fills
		them the moment the main loop breathes."""
		self._shared_checked = True
		doc = self._readSharedSession()
		if doc is None:
			return None
		s = self._storage()
		if s is None:
			return None
		try:
			s.Store(self._storageDir(), doc['device_token'],
					products=[], label='supporter')
		except Exception as e:
			fnsLog('AUTH: could not adopt the shared session (%s)' % e,
				   level='WARNING')
			return None
		fnsLog('AUTH: adopted the machine session written by %s'
			   % (doc.get('written_by') or 'unknown'))
		run('args[0].ext.ExtAuth.RequestToken()', self.ownerComp,
			delayFrames=2, delayRef=op.TDResources)
		try:
			return s.Load(self._storageDir())
		except Exception:
			return None

	# ------------------------------------------------------------------
	# what this install is entitled to
	# ------------------------------------------------------------------

	def Account(self):
		"""The stored account record, or None. Reading it is cheap enough
		to do per call and avoids a cache that can disagree with the
		keystore after a Sign Out in another project. Holding nothing,
		it checks the shared machine session once (G7) -- a sign-in from
		the launcher serves this product too."""
		s = self._storage()
		if s is None:
			return None
		try:
			rec = s.Load(self._storageDir())
		except Exception as e:
			fnsLog('AUTH: keystore unreadable (%s)' % e, level='WARNING')
			return None
		if rec is None and not getattr(self, '_shared_checked', False):
			rec = self._adoptSharedSession()
		elif rec is not None and not getattr(self, '_shared_backfilled', False):
			# Backfill (G7): a session signed in BEFORE the shared file
			# existed never published -- publish fires on sign-in/redeem
			# events, so a pre-G7 keystore stays invisible to the machine
			# until the next sign-in. First read with a token in hand and
			# no shared file on disk closes that gap; checked once per
			# extension lifetime, like adoption.
			self._shared_backfilled = True
			if self._readSharedSession() is None:
				self._publishSharedSession(rec['device_token'])
				fnsLog('AUTH: published the held session to the machine '
					   'file (backfill)')
		return rec

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

	def _routesFor(self, package):
		"""(tier_label, key_available) for a gated package, read from the
		store manifest's routes projection (build_manifest ships the tier
		ladder's labels and the key flag). Empty when the manifest
		predates the projection -- the sentence degrades to generic, it
		never breaks."""
		try:
			man = self.ownerComp.ext.ExtUpdater.StoreManifest() or {}
			pkg = next((p for p in man.get('packages', [])
						if p.get('name') == package), {})
			access = str(pkg.get('access', 'free') or 'free')
			label = ''
			for t in (man.get('toolkit') or {}).get('tiers') or []:
				if str(t.get('id')) == access:
					label = str(t.get('label') or '')
					break
			return label, bool(pkg.get('key_available'))
		except Exception:
			return '', False

	def MissingFor(self, package):
		"""What to TELL someone who cannot have this package -- naming
		the ROUTES, not just the refusal: the tier it unlocks at (or
		higher; the ladder grants upward) and, where a Gumroad row
		exists, the lifetime key. The client reads its claim only for
		this."""
		label, key = self._routesFor(package)
		at = (' — it unlocks at the %s tier or higher' % label) if label else ''
		buy = ', or with a lifetime key' if key else ''
		if not self.IsSignedIn():
			return 'Sign in to download %s%s%s.' % (package, at, buy)
		if label:
			return ('Your current tier does not include %s — upgrade to '
					'the %s tier or higher%s.'
					% (package, label,
					   buy.replace(', or', ', or unlock it') if key else ''))
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

	def DropCachedToken(self):
		"""Forget the cached download token. The gate can kill the session
		that minted it mid-window (a sign-out elsewhere on the machine);
		the token then looks valid here while every download it signs
		comes back an error body. The updater calls this on a refused
		gated fetch so the next pass re-requests -- and that request gets
		the honest 401 that updates the session state."""
		self._download_token, self._download_expires = '', 0.0

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
		self._gateRequest(wc, '%s/token/download' % self.GateUrl(),
						  token=acct['device_token'])
		return {'ok': True, 'why': 'requesting (async)'}

	def Recheck(self, callback=None):
		"""Ask the gate to re-read entitlement from Patreon RIGHT NOW.

		The automatic path caches the Patreon call for six hours, which is
		correct for an install that is merely running and wrong for the one
		moment that decides whether someone stays a customer: they have
		just pledged and are waiting to see it. Without this they would be
		told "your tier does not include this" for the rest of the day and
		reasonably conclude it is broken.

		ASYNC -- `callback(ok, message)` on a later frame.
		"""
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
		self._recheck_cb = callback
		self._setStatus('checking your membership...')
		self._gateRequest(wc, '%s/session/recheck' % self.GateUrl(),
						  token=acct['device_token'])
		return {'ok': True, 'why': 'checking (async)'}

	def OnRecheckResponse(self, statusCode, data):
		"""Web Client DAT callback for /session/recheck."""
		cb, self._recheck_cb = getattr(self, '_recheck_cb', None), None
		ok, payload = self._readJson(statusCode, data)
		if not ok:
			self._setStatus(str(payload))
			self._actOnRefusal()
			if cb:
				cb(False, payload)
			return
		products = payload.get('products') or []
		self._rememberProducts(products, tiers=payload.get('tiers'))
		# The answer's structure decides the sentence -- each state has a
		# DIFFERENT remedy, and collapsing them is how "check again"
		# becomes a silent forever-no (the gate now says which it is).
		if payload.get('connected') is False:
			# the grant is dead; rechecking can never see anything again
			msg = str(payload.get('message')
					  or 'your Patreon link is no longer active -- sign in again')
		elif products:
			msg = self.AuthStatus()
		elif payload.get('stale'):
			msg = ('could not reach Patreon just now -- showing the last '
				   'known answer; try again in a minute')
		elif payload.get('tiers'):
			# Patreon says they ARE a patron, but of a tier that grants
			# nothing here. Say which of the two it is: the remedies differ.
			msg = 'membership found, but it does not include any packages yet'
		else:
			msg = 'no active membership found on this Patreon account'
		self._setStatus(msg)
		if cb:
			cb(bool(products), msg)

	def OnTokenResponse(self, statusCode, data):
		"""Web Client DAT callback for /token/download."""
		cb, self._token_cb = getattr(self, '_token_cb', None), None
		ok, payload = self._readJson(statusCode, data)
		if not ok:
			fnsLog('AUTH: token refused (%s)' % payload, level='WARNING')
			self._actOnRefusal()
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
		sentence; anything else must not be shown raw. The parsed body
		and code also land on _last_gate_body/_last_gate_code, because a
		refusal's STRUCTURE is authoritative too -- a 403 carries the
		products truth, a 401 declares the session dead -- and reducing
		it to a message string was how a lapsed supporter's picker said
		N-unlocked forever."""
		self._last_gate_body, self._last_gate_code = {}, 0
		try:
			body = json.loads(data.decode('utf-8') if isinstance(data, bytes) else str(data))
		except Exception:
			return False, 'the gate returned something unreadable'
		code = int((statusCode or {}).get('code', 0) or 0) if isinstance(statusCode, dict) else int(statusCode or 0)
		self._last_gate_body, self._last_gate_code = body, code
		if code == 200 and body.get('ok'):
			return True, body
		return False, str(body.get('message') or 'request failed (%s)' % code)

	def _actOnRefusal(self):
		"""Act on the STRUCTURE of a gate refusal (_readJson stashed it).

		403 no_entitlement deliberately carries the merged products list
		(Patreon + Gumroad, possibly empty) -- remember it, or a lapsed
		supporter's picker claims N-unlocked forever, since a successful
		token response can never arrive for that account again. 401
		means THIS DEVICE TOKEN is dead: clear the local record so every
		surface stops presenting a session that cannot act, instead of
		hiding Sign in behind a stale account."""
		body = getattr(self, '_last_gate_body', {}) or {}
		code = getattr(self, '_last_gate_code', 0)
		if code == 403 and 'products' in body:
			self._rememberProducts(body.get('products') or [])
		elif code == 401:
			self._sessionDied()

	def _sessionDied(self):
		"""The gate answered 401: this device token is revoked, aged out,
		or lost server-side. Local clear only -- no gate revoke, the gate
		just said the token is already dead. The picker's account global
		goes null and its rail re-offers the ways back in; both routes
		are named because both exist, and re-redeeming a held key spends
		no activation by design."""
		acct = self.Account() or {}
		dead = acct.get('device_token')
		s = self._storage()
		if s is not None:
			try:
				s.Clear(self._storageDir())
			except Exception as e:
				fnsLog('AUTH: could not clear the dead session (%s)' % e,
					   level='WARNING')
		# the gate declared THIS token dead: drop the shared file too --
		# but only while it still holds the dead token; a newer sign-in
		# by another product is not ours to destroy (G7)
		if dead:
			self._dropSharedSession(only_token=dead)
		self._shared_checked = True   # do not re-adopt the corpse
		self._download_token, self._download_expires = '', 0.0
		self._setStatus('session expired -- sign in again, or redeem your '
						'licence key again')
		fnsLog('AUTH: gate reported the session dead (401) -- local record '
			   'cleared', level='WARNING')

	def _rememberProducts(self, products, tiers=None):
		"""tiers: pass the response's own list when it carries one -- the
		gate's answer is fresher than the stored copy, and persisting the
		stale local tiers next to fresh products was a quiet drift."""
		if products is None:
			return
		acct = self.Account()
		if acct is None:
			return
		s = self._storage()
		try:
			s.Store(self._storageDir(), acct['device_token'],
					products=products,
					tiers=acct.get('tiers') if tiers is None else tiers,
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
		# Adopt-before-browser (launcher review, G7): adoption is checked
		# once per extension lifetime, so a toolkit that started signed
		# out never noticed a launcher sign-in made LATER in the same TD
		# session. The Sign in click is the moment to look again -- when
		# the machine already holds a session, take it and save the user
		# the whole browser trip. The launcher does the same.
		if self.Account() is None:
			self._shared_checked = False
			if self.Account() is not None:
				self._setStatus(self.AuthStatus())
				fnsLog('AUTH: adopted the machine session instead of a '
					   'browser sign-in')
				return {'ok': True, 'why': 'adopted the machine session'}
		ws = self._ensureServer()
		if ws is None:
			return {'ok': False, 'why': 'could not create the callback listener'}
		# Bind-test, start, then VERIFY the start. The test socket closing
		# opens a race any other process can win, and the Web Server DAT
		# accepts active=True silently while failing to start (measured
		# 2026-08-29: the op carried "Failed to start server" and nothing
		# raised). Without the check, losing the race means a browser
		# pointed at a port nobody serves; with it, one more walk step.
		import socket
		port = None
		for cand in CALLBACK_PORTS:
			probe = socket.socket()
			try:
				probe.bind(('127.0.0.1', cand))
			except OSError:
				continue
			finally:
				probe.close()
			ws.par.active = False
			ws.par.port = cand
			ws.par.active = True
			if not ws.errors():
				port = cand
				break
			ws.par.active = False
		if port is None:
			return {'ok': False, 'why': 'could not start the callback '
					'listener on any port in %s' % (CALLBACK_PORTS,)}
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
			self._gateRequest(wc, '%s/session/claim' % self.GateUrl(),
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
		# every successful sign-in serves the whole machine (G7)
		self._publishSharedSession(token)
		# the rich line, not a bare "signed in": AuthStatus() names the
		# account and counts what it unlocked, which is the only place a
		# supporter can currently SEE that paying did something
		self._setStatus(self.AuthStatus())
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
		mine = (acct or {}).get('device_token')
		if wc is not None and mine:
			try:
				self._gateRequest(wc, '%s/session/revoke' % self.GateUrl(),
								  token=mine)
			except Exception as e:
				fnsLog('AUTH: revoke request failed to start (%s)' % e,
					   level='WARNING')
		s = self._storage()
		if s is not None:
			s.Clear(self._storageDir())
		# Sign-out signs the MACHINE out (G7): revoke-then-delete, and
		# delete only while the shared file still holds the token just
		# revoked -- a newer sign-in by another product survives.
		if mine:
			self._dropSharedSession(only_token=mine)
		self._shared_checked = True   # a deliberate sign-out is not re-adopted
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

	def RedeemKey(self, key=None, product=None, package=None):
		"""Redeem one Gumroad licence key.

		Keys are PER TOOL by decision, so redeeming EXTENDS the account
		rather than replacing it -- five tools means five keys on one
		install, and the gate merges them onto one device token.

		`package` is the buyer-friendly address: they know the TOOL they
		bought, not Gumroad's product id, and the gate resolves the name
		through its own one-to-one map. `product` (the raw id) keeps
		working for the pars and for scripts."""
		key = (key or self._par('Licensekey')).strip()
		product = (product or self._par('Licenseproduct')).strip()
		package = str(package or '').strip()
		if not key:
			return {'ok': False, 'why': 'no licence key given'}
		if not product and not package:
			return {'ok': False, 'why': 'no product id or package name given'}
		wc = self._client()
		if wc is None:
			return {'ok': False, 'why': 'no auth client'}
		acct = self.Account() or {}
		body = {'license_key': key}
		if product:
			body['product_id'] = product
		else:
			body['package'] = package
		if acct.get('device_token'):
			body['device_token'] = acct['device_token']
		self._redeem_pending = True
		self._gateRequest(wc, '%s/gumroad/redeem' % self.GateUrl(),
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
		# a redeem is a sign-in too: the minted/extended token serves the
		# whole machine (G7)
		self._publishSharedSession(payload['device_token'])
		self._download_token, self._download_expires = '', 0.0
		self._setStatus(self.AuthStatus())
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
		# every state change passes through here, so this is the one place
		# entitlement has to be re-read for the dependency to stay true
		self._refreshPlus()
