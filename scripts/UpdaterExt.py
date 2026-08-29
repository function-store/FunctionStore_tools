"""
UpdaterExt -- Embody self-update from GitHub releases.

Hosted on the 'updater' baseCOMP inside the Embody COMP (Embody's four root
extension slots are occupied). Reaches the host via a CONTEXT-FREE reference
(self.ownerComp.parent.Embody) -- NOT the bare `parent.Embody` global, which
resolves from the current execution context. This matters because the
post-reload entry points (VerifyUpdate / VerifyRollback / _rollback) are
invoked by string-form run() whose scheduling op was destroyed, so they run
with ROOT as context where `parent` finds no Embody ancestor and raises. Every
host access here is bound to self.ownerComp (a stored reference), matching the
house precedent (WindowHeaderExt uses self.ownerComp.parent.Embody).

Swap mechanism (probe-verified 2026-07-21 on TD 2025.33070):
    The update is applied with an IN-PLACE external-tox reload -- set
    par.externaltox to the downloaded release .tox, reloadcustom/reloadbuiltin
    OFF, then pulse enableexternaltoxpulse. The host COMP survives (global
    shortcut, wires, position), children are rebuilt from the new tox, live
    custom-par VALUES are preserved while NEW par definitions land, the old
    extension instances get onDestroyTD (Envoy shuts down cleanly), and the
    reloaded execute DAT's onCreate runs Embody's normal boot chain.

    Consequences honored here:
    - Preserved par values mean par.Version still reads the OLD version after
      the reload; VerifyUpdate() stamps the About pars from the manifest --
      but ONLY after confirming a real reload happened (the EmbodyExt DAT's
      op id changes when children are recreated; a no-op reload keeps the old
      id, and stamping then would make par.Version lie).
    - externaltox is left pointing at the download; VerifyUpdate() clears it
      (same hazard _validateTrackedOperators clears for drag-ins).
    - The pulse destroys THIS extension's own host child mid-call, so the
      pulse is the LAST TD-touching statement of the apply path; the undo
      block is opened AND closed before the pulse, and everything after the
      reload runs from string-form run() callbacks that resolve the fresh
      instance via op('<embody>').op('updater') and are guarded against a
      missing child (a run() with delayRef=<destroyed op> never fires, so
      delayRef is never used here).

Failure surfacing:
    - CHECK-stage failures (no network, unverifiable/absent manifest, TD-build
      floor) are quiet on the automatic startup path (log + Update Status) and
      loud on the manual path (dialog). Nobody wants a dialog every launch
      because GitHub was briefly unreachable.
    - INSTALL-stage failures (backup export, reload, verify, rollback) ALWAYS
      dialog, on every path -- once the live component is being touched, a
      silent failure would leave the user unknowingly on a half-broken or
      wrong-version install. Silent success, loud failure.

Network layer follows the house pattern (EmbodyExt._checkMCPUpdate /
EnvoyExt._beginAsyncBootstrap): a daemon worker thread doing pure-Python
urllib with ZERO TD access publishes a generation-tagged result to a plain
attribute; a bounded main-thread run() poll chain (with a stale-instance
guard) drains it. urllib follows GitHub's 302 asset redirects and carries our
User-Agent (GitHub rejects UA-less requests with 403).

TD-2025 facts baked in: there is no project.dirty (the manual path offers a
save; the startup path runs when the just-opened .toe IS the recovery point),
and an older TD build loading a newer-build tox returns None/empty SILENTLY --
hence the manifest min_td_build gate BEFORE download and the reload-token
check AFTER.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path


def _verified_tls_context():
    """A VERIFYING SSL context that works on TD's bundled Python.

    Windows resolves CAs from the OS certificate store, so bare urlopen
    always worked there. macOS's bundled Python has NO default CA path:
    every HTTPS call from TD failed with CERTIFICATE_VERIFY_FAILED --
    the field 'Update check failed' on every Mac. certifi ships inside
    TouchDesigner (a requests dependency); load its bundle IN ADDITION
    to any system defaults, so both platforms verify. Verification is
    never disabled or downgraded: this context feeds the SELF-UPDATER,
    and an unverified download would be a supply-chain hole.

    WORKER-SAFE: pure Python, importable and callable off the main
    thread with zero TD access.
    """
    import ssl
    context = ssl.create_default_context()
    try:
        import certifi
        context.load_verify_locations(cafile=certifi.where())
    except Exception:
        pass  # the OS store may already suffice (Windows)
    return context


class UpdaterExt:
    """Self-updater for the Embody component (check / download / apply)."""

    GITHUB_OWNER = 'dylanroscover'
    GITHUB_REPO = 'Embody'
    USER_AGENT = 'Embody-Updater'
    MANIFEST_ASSET = 'embody-release.json'
    # A release tox is ~700KB; cap well above that but below anything that
    # could exhaust memory when buffered (GitHub allows 2GB assets).
    MAX_ASSET_BYTES = 50_000_000
    # A backup must look like a plausible portable tox, not a truncated stub.
    MIN_BACKUP_BYTES = 100_000
    ASSET_RE = re.compile(r'^[A-Za-z0-9._-]+\.tox$')

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        # Worker handoff slots (plain attributes -- never TD objects).
        # None = in flight; dict (with '_gen') = published result.
        self._check_result = None
        self._download_result = None
        self._check_gen = 0
        self._download_gen = 0
        self._busy = False
        self._pending = None  # release info between check -> apply
        self._rearmed = False  # one-shot: StartupCheck's verifier re-arm

    # ==================================================================
    # Host access (CONTEXT-FREE) + logging / dialogs (main thread only)
    # ==================================================================

    @property
    def _embody(self):
        # Bound to self.ownerComp, so it resolves correctly even from the
        # root execution context of a surviving string-form run().
        return self.ownerComp.parent.Embody

    def _log(self, msg, level='INFO'):
        try:
            self._embody.Log(f'Updater: {msg}', level)
        except Exception:
            debug(f'[Updater/{level}] {msg}')

    def _dialog(self, title, message, buttons):
        """Route through Embody's auto-response-aware messageBox.

        Returns the button index, or -1 when the dialog is suppressed (test
        runner active / save window / unseeded). Callers MUST treat -1 (and
        any non-affirmative value) as 'no' -- never as a default action.
        """
        return self._embody.ext.Embody._messageBox(title, message, buttons)

    @staticmethod
    def _posix(path):
        return str(path).replace('\\', '/')

    def _setPar(self, par, value):
        """Assign through the readOnly dance (About/status pars are locked)."""
        was = par.readOnly
        par.readOnly = False
        par.val = value
        par.readOnly = was

    def _status(self, text):
        p = getattr(self._embody.par, 'Updatestatus', None)
        if p is not None:
            self._setPar(p, str(text)[:160])

    # ==================================================================
    # Pure helpers (static -- unit-testable outside TD)
    # ==================================================================

    @staticmethod
    def parseVersion(tag):
        """'v6.0.141' / '6.0.141' -> (6, 0, 141); None if not X.Y.Z."""
        m = re.match(r'^v?(\d+)\.(\d+)\.(\d+)$', str(tag).strip())
        return tuple(int(g) for g in m.groups()) if m else None

    @staticmethod
    def parseBuild(build):
        """'2025.33070' -> (2025, 33070); None if malformed."""
        m = re.match(r'^(\d+)\.(\d+)$', str(build).strip())
        return tuple(int(g) for g in m.groups()) if m else None

    @staticmethod
    def validateManifest(data):
        """Return error string for a bad manifest dict, or None if usable.

        This is a security gate as much as a schema check: `asset` flows into
        a filesystem path and must be a bare .tox filename (no traversal, no
        absolute path); `size` must be sane before we buffer a download.
        """
        if not isinstance(data, dict):
            return 'manifest is not a JSON object'
        for key in ('version', 'asset', 'size', 'sha256', 'min_td_build'):
            if key not in data:
                return f'manifest missing required key: {key}'
        if UpdaterExt.parseVersion(data['version']) is None:
            return f'manifest version not X.Y.Z: {data["version"]!r}'
        if UpdaterExt.parseBuild(data['min_td_build']) is None:
            return f'manifest min_td_build malformed: {data["min_td_build"]!r}'
        if not isinstance(data['size'], int) or data['size'] <= 0:
            return 'manifest size must be a positive integer'
        if data['size'] > UpdaterExt.MAX_ASSET_BYTES:
            return (f'manifest size {data["size"]} exceeds the '
                    f'{UpdaterExt.MAX_ASSET_BYTES}-byte cap')
        if not re.match(r'^[0-9a-f]{64}$', str(data['sha256'])):
            return 'manifest sha256 is not a 64-char lowercase hex digest'
        if not UpdaterExt.ASSET_RE.match(str(data['asset'])):
            return (f'manifest asset must be a bare .tox filename, got '
                    f'{data["asset"]!r}')
        # The two OPTIONAL keys with the largest blast radius, type-checked
        # because both drive destructive reconciliation and the manifest is a
        # mutable, unhashed release asset. A `custom_pars` that arrived as the
        # STRING "Version" would set()-iterate into single characters, leaving
        # every real par 'undeclared' -- the prune would then destroy every
        # setting on the component. A non-dict `builtin_pars` raises inside
        # VerifyUpdate, orphaning the sentinel and externaltox.
        pars = data.get('custom_pars')
        if pars is not None:
            if (not isinstance(pars, (list, tuple))
                    or not all(isinstance(n, str) for n in pars)):
                return 'manifest custom_pars must be a list of names'
        builtins = data.get('builtin_pars')
        if builtins is not None and not isinstance(builtins, dict):
            return 'manifest builtin_pars must be an object'
        return None

    @staticmethod
    def apiLatestUrl(owner, repo):
        return f'https://api.github.com/repos/{owner}/{repo}/releases/latest'

    # ==================================================================
    # Paths and state files
    # ==================================================================

    def _updatesDir(self, create=False):
        root = self._embody.ext.Embody._findProjectRoot()
        d = Path(root) / '.embody' / 'updates'
        if create:
            d.mkdir(parents=True, exist_ok=True)
        return d

    def _sentinelPath(self):
        return self._updatesDir(create=False) / 'pending.json'

    def _withinUpdates(self, path):
        """True only if `path` really lives inside .embody/updates/.

        pending.json is attacker-writable local state; the recovery path must
        never reload a backup pointed anywhere else on disk.
        """
        try:
            base = os.path.realpath(str(self._updatesDir(create=False)))
            target = os.path.realpath(str(path))
            return target == base or target.startswith(base + os.sep)
        except Exception:
            return False

    def _writeSentinel(self, data):
        self._updatesDir(create=True)
        path = self._sentinelPath()
        tmp = Path(str(path) + '.tmp')
        tmp.write_text(json.dumps(data, indent=1), encoding='utf-8')
        os.replace(str(tmp), str(path))

    def _readSentinel(self):
        path = self._sentinelPath()
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            return None

    def _clearSentinel(self):
        try:
            self._sentinelPath().unlink(missing_ok=True)
        except OSError:
            pass

    # ---- sentinel ownership: 'in flight' vs 'interrupted' ----------------
    #
    # The sentinel is a CRASH artifact: it exists from just before the swap
    # until VerifyUpdate confirms it, and StartupCheck offers to roll back
    # anything it finds. But an in-place tox reload does NOT restart
    # TouchDesigner -- the new component boots inside the same process and
    # runs the same startup chain, so it meets the live sentinel of the very
    # update it IS. Without an owner stamp that reads as 'a previous update
    # never completed', and the user is asked to roll back a healthy install
    # seconds before it succeeds (field report, v6.0.246).

    @staticmethod
    def _sessionMark():
        """Identity of the TD PROCESS applying an update.

        pid alone would be ambiguous after a crash that recycled it, so it is
        paired with the process's wall-clock start time, derived from
        absTime.seconds ('total seconds played since the application started'
        -- docs.derivative.ca/AbsTime_Class). Both are plain data, safe in
        JSON, and meaningless to any other process.
        """
        try:
            started = int(time.time() - float(absTime.seconds))
        except Exception:
            started = 0
        return {'pid': os.getpid(), 'started': started}

    def _sameSession(self, sentinel):
        """True when THIS TD process is the one that started this update."""
        owner = sentinel.get('session')
        if not isinstance(owner, dict):
            return False  # pre-6.0.247 sentinel: no ownership was recorded
        try:
            if int(owner.get('pid')) != os.getpid():
                return False
        except (TypeError, ValueError):
            return False
        mine = self._sessionMark().get('started', 0)
        try:
            # Both readings estimate the same instant; a couple of seconds of
            # drift is the sampling jitter, a restart is minutes apart.
            return abs(int(owner.get('started')) - int(mine)) <= 5
        except (TypeError, ValueError):
            return False

    def _swapStillPointed(self, sentinel):
        """True while the component is still pointed at the tox being applied.

        A second, writer-independent witness. _applyPhase2 sets externaltox to
        the download and only VerifyUpdate clears it, so a match means the
        swap has not finished being verified -- by definition unfinished, not
        interrupted. This one needs nothing from the build that WROTE the
        sentinel, which is what makes the first update to ship this fix (whose
        sentinel came from the older build) behave correctly.
        """
        want = str(sentinel.get('tox_path') or '').replace('\\', '/')
        if not want:
            return False
        try:
            current = str(self._embody.par.externaltox.eval() or '')
        except Exception:
            return False
        # Separator- and case-insensitive, because both filesystems this ships
        # on are case-insensitive and the par round-trips through TD. Kept to
        # exactly that: any looser match (a basename, a directory) would risk
        # a FALSE positive, and a false positive here SUPPRESSES a genuine
        # crash-recovery prompt -- the one direction that must not happen.
        return current.replace('\\', '/').lower() == want.lower()

    def _updateInFlight(self, sentinel):
        """True when this sentinel describes a swap that is still running."""
        return self._sameSession(sentinel) or self._swapStillPointed(sentinel)

    @staticmethod
    def _sha256File(path):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        return h.hexdigest()

    # ==================================================================
    # Guards / status helpers
    # ==================================================================

    def isDevCheckout(self):
        """True when Embody's own DATs are file-synced (the git dev tree).

        ExportPortableTox strips every relative file reference from release
        toxes, so a non-empty file par on EmbodyExt only exists in the dev
        checkout -- where the repo, not a downloaded tox, is source of truth.
        """
        dat = self._embody.op('EmbodyExt')
        return bool(dat is not None and dat.par.file.eval())

    def _refuse(self, why, interactive):
        """Pre-commit refusal (nothing on disk touched). Quiet unless asked."""
        self._log(f'update refused: {why}', 'WARNING')
        self._status(why)
        if interactive:
            self._dialog('Embody Update', why, ['OK'])
        return {'error': why}

    def _fail(self, why, loud=True):
        """Install-stage failure -- the live component was being touched.

        ALWAYS dialogs when loud (the default): a silent failure here leaves
        the user unknowingly on a broken/wrong install.
        """
        self._log(f'update FAILED: {why}', 'ERROR')
        self._status(why)
        if loud:
            self._dialog('Embody Update', why, ['OK'])
        return {'error': why}

    # ==================================================================
    # CHECK (promoted): worker thread + bounded main-thread poll
    # ==================================================================

    def CheckForUpdate(self, interactive=True, auto_install=False):
        """Query GitHub for a newer release. Prompts when interactive."""
        if self._readSentinel():
            return self._refuse(
                'An update is already in progress. Restart TouchDesigner if '
                'this persists.', interactive)
        if self._busy:
            return self._refuse('An update operation is already running.',
                                interactive)
        if self.isDevCheckout():
            return self._refuse(
                'This is the Embody dev checkout -- update via git, '
                'not self-update.', interactive)
        local = self.parseVersion(self._embody.par.Version.eval())
        if local is None:
            return self._refuse('Local Version parameter is not X.Y.Z.',
                                interactive)

        self._busy = True
        self._check_result = None
        self._check_gen += 1
        gen = self._check_gen
        self._status('Checking for updates...')
        self._log(f'checking {self.GITHUB_OWNER}/{self.GITHUB_REPO} '
                  f'(local v{".".join(map(str, local))})')

        # Resolve EVERYTHING the worker needs on the main thread first.
        url = self.apiLatestUrl(self.GITHUB_OWNER, self.GITHUB_REPO)
        ua = self.USER_AGENT
        manifest_name = self.MANIFEST_ASSET

        def _worker():
            # ZERO TD access in here -- pure Python only.
            out = {'_gen': gen}
            try:
                import urllib.request
                tls = _verified_tls_context()
                req = urllib.request.Request(url, headers={
                    'User-Agent': ua,
                    'Accept': 'application/vnd.github+json',
                })
                with urllib.request.urlopen(req, timeout=10,
                                            context=tls) as resp:
                    release = json.loads(resp.read())
                out['tag'] = release.get('tag_name', '')
                out['notes'] = (release.get('body') or '')[:4000]
                assets = release.get('assets') or []
                out['assets'] = {
                    a.get('name'): {
                        'url': a.get('browser_download_url'),
                        'size': a.get('size'),
                    } for a in assets
                }
                mf = out['assets'].get(manifest_name)
                if mf and mf.get('url'):
                    req2 = urllib.request.Request(
                        mf['url'], headers={'User-Agent': ua})
                    with urllib.request.urlopen(req2, timeout=10,
                                                context=tls) as resp2:
                        out['manifest'] = json.loads(resp2.read())
            except Exception as e:  # network errors are expected, not fatal
                out['error'] = f'{type(e).__name__}: {e}'
            self._check_result = out

        import threading
        threading.Thread(target=_worker, daemon=True).start()
        # Budget >= 3x the worker's worst case (two sequential 10s requests
        # plus unbounded DNS): 100 x 15 frames ~= 25s at 60fps.
        run('args[0]._pollCheck(args[1], args[2], args[3], args[4])',
            self, interactive, auto_install, gen, 0, delayFrames=15)
        return {'status': 'checking'}

    def _staleInstance(self):
        try:
            return self.ownerComp.ext.UpdaterExt is not self
        except Exception:
            return True

    def _pollCheck(self, interactive, auto_install, gen, attempts):
        if self._staleInstance():
            return
        result = self._check_result
        # Only accept the result from THIS check's worker generation.
        if result is None or result.get('_gen') != gen:
            if attempts < 100:
                run('args[0]._pollCheck(args[1], args[2], args[3], args[4])',
                    self, interactive, auto_install, gen, attempts + 1,
                    delayFrames=15)
            else:
                self._busy = False
                self._refuse('Update check timed out.', interactive)
            return
        self._check_result = None
        self._busy = False
        self._finishCheck(result, interactive, auto_install)

    def _finishCheck(self, result, interactive, auto_install):
        if 'error' in result:
            msg = (f'Update check failed (no internet or GitHub '
                   f'unreachable): {result["error"]}')
            self._log(msg, 'WARNING')
            self._status('Update check failed (network error)')
            if interactive:
                self._dialog('Embody Update', msg, ['OK'])
            return

        local = self.parseVersion(self._embody.par.Version.eval())
        remote = self.parseVersion(result.get('tag', ''))
        if remote is None:
            self._refuse(f'Release tag is not vX.Y.Z: '
                         f'{result.get("tag")!r}', interactive)
            return
        # releases/latest is commit-date ordered, NOT semver -- only a
        # strictly greater remote version is an update.
        if remote <= local:
            self._status(f'Up to date (v{".".join(map(str, local))})')
            self._log('up to date')
            if interactive:
                self._dialog('Embody Update',
                             'Embody is up to date '
                             f'(v{".".join(map(str, local))}).', ['OK'])
            return

        tag = result['tag']
        manifest = result.get('manifest')
        err = self.validateManifest(manifest) if manifest is not None else (
            'release has no embody-release.json manifest')
        if err:
            self._refuse(
                f'Update v{".".join(map(str, remote))} found, but it cannot '
                f'be verified: {err}. Update manually from GitHub.',
                interactive)
            return

        min_build = self.parseBuild(manifest['min_td_build'])
        this_build = self.parseBuild(app.build)
        if this_build is None or min_build is None or this_build < min_build:
            self._refuse(
                f'Update {tag} requires TouchDesigner build '
                f'{manifest["min_td_build"]}+ (this is {app.build}). '
                f'Update TouchDesigner first.', interactive)
            return

        asset = result['assets'].get(manifest['asset'])
        if not asset or not asset.get('url'):
            self._refuse(f'Release {tag} is missing its asset '
                         f'{manifest["asset"]!r}.', interactive)
            return

        self._pending = {
            'tag': tag,
            'version': manifest['version'],
            'asset_url': asset['url'],
            'manifest': manifest,
            'notes': result.get('notes', ''),
        }
        self._status(f'{tag} available')
        self._log(f'update available: {tag}')

        if auto_install:
            self._startDownload(interactive=False, apply_after=True)
            return
        if interactive:
            # Keep this a DECISION, not a reading assignment: version pair +
            # a link. Release-notes bodies (project intro, changelog bullets)
            # overwhelmed the dialog; anyone who wants them has the URL.
            choice = self._dialog(
                'Embody Update',
                f'Update available: {tag} (installed: '
                f'v{".".join(map(str, local))}).\n\n'
                f'Release notes: https://github.com/{self.GITHUB_OWNER}/'
                f'{self.GITHUB_REPO}/releases/tag/{tag}\n\n'
                'Download and install now?',
                ['Install', 'Not Now'])
            if choice == 0:  # affirmative only; -1/1/None => do nothing
                self._startDownload(interactive=True, apply_after=True)

    # ==================================================================
    # DOWNLOAD: worker thread writes + hashes the asset, poll drains
    # ==================================================================

    def _startDownload(self, interactive, apply_after):
        if self._busy:
            return self._refuse('An update operation is already running.',
                                interactive)
        pending = self._pending
        if not pending:
            return self._refuse('No pending update to download.', interactive)

        self._busy = True
        self._download_result = None
        self._download_gen += 1
        gen = self._download_gen
        self._status(f'Downloading {pending["tag"]}...')

        url = pending['asset_url']
        ua = self.USER_AGENT
        expect_size = pending['manifest']['size']
        expect_sha = pending['manifest']['sha256']
        # asset is validated as a bare .tox filename -> safe to join.
        dest = self._posix(self._updatesDir(create=True)
                           / pending['manifest']['asset'])

        def _worker():
            # ZERO TD access. urllib follows the 302 to
            # objects.githubusercontent.com natively.
            out = {'_gen': gen}
            try:
                import urllib.request
                req = urllib.request.Request(
                    url, headers={'User-Agent': ua})
                with urllib.request.urlopen(req, timeout=60,
                                            context=_verified_tls_context()
                                            ) as resp:
                    # Cap the read at the manifest size (+1 to detect
                    # overrun) so a hostile server can't stream unbounded
                    # bytes into memory.
                    payload = resp.read(expect_size + 1)
                if len(payload) != expect_size:
                    raise ValueError(
                        f'size mismatch: got {len(payload)}, '
                        f'manifest says {expect_size}')
                digest = hashlib.sha256(payload).hexdigest()
                if digest != expect_sha:
                    raise ValueError('sha256 mismatch: download does not '
                                     'match the release manifest')
                tmp = dest + '.tmp'
                with open(tmp, 'wb') as f:
                    f.write(payload)
                os.replace(tmp, dest)
                out['path'] = dest
            except Exception as e:
                out['error'] = f'{type(e).__name__}: {e}'
            self._download_result = out

        import threading
        threading.Thread(target=_worker, daemon=True).start()
        run('args[0]._pollDownload(args[1], args[2], args[3], args[4])',
            self, interactive, apply_after, gen, 0, delayFrames=15)
        return {'status': 'downloading'}

    def _pollDownload(self, interactive, apply_after, gen, attempts):
        if self._staleInstance():
            return
        result = self._download_result
        if result is None or result.get('_gen') != gen:
            if attempts < 800:  # ~200s at 60fps; covers a slow trickle
                run('args[0]._pollDownload(args[1], args[2], args[3], args[4])',
                    self, interactive, apply_after, gen, attempts + 1,
                    delayFrames=15)
            else:
                self._busy = False
                self._refuse('Download timed out.', interactive)
            return
        self._download_result = None
        self._busy = False
        if 'error' in result:
            self._refuse(f'Download failed: {result["error"]}', interactive)
            return
        self._pending['tox_path'] = result['path']
        self._log(f'downloaded and verified {result["path"]}')
        if apply_after:
            self.ApplyUpdate(interactive=interactive)

    # ==================================================================
    # APPLY (promoted): pre-flight, backup, then the in-place reload
    # ==================================================================

    def ApplyUpdate(self, interactive=True):
        pending = self._pending
        if not pending or not pending.get('tox_path'):
            return self._refuse('No verified download to apply. Run '
                                'CheckForUpdate first.', interactive)
        if self._readSentinel():
            return self._refuse('An update is already in progress.',
                                interactive)
        if self._busy:
            return self._refuse('An update operation is already running.',
                                interactive)
        if self.isDevCheckout():
            return self._refuse('Dev checkout -- refusing self-update.',
                                interactive)
        if not os.path.isfile(pending['tox_path']):
            return self._refuse('Downloaded file vanished; re-run the check.',
                                interactive)
        # Re-gate the TD-build floor (cheap; app.build is constant in-session,
        # but this keeps apply self-contained and honest).
        min_build = self.parseBuild(pending['manifest']['min_td_build'])
        this_build = self.parseBuild(app.build)
        if this_build is None or min_build is None or this_build < min_build:
            return self._refuse(
                f'Update {pending["tag"]} requires TouchDesigner build '
                f'{pending["manifest"]["min_td_build"]}+.', interactive)

        # There is no project.dirty on TD 2025 -- offer the recovery point
        # explicitly. Whitelist affirmatives: -1 (suppressed) / None / any
        # unexpected value must CANCEL, never install.
        if interactive:
            choice = self._dialog(
                'Embody Update',
                f'Install {pending["tag"]} now?\n\n'
                'Saving the project first gives you a clean recovery '
                'point in case anything goes wrong.',
                ['Save and Install', 'Install Without Saving', 'Cancel'])
            if choice not in (0, 1):
                self._status(f'{pending["tag"]} available')
                return {'status': 'cancelled'}
            if choice == 0:
                project.save()

        self._busy = True
        self._status(f'Installing {pending["tag"]}...')
        # Delay past the post-save dialog-suppression window (~120 frames)
        # AND the Envoy socket-release window, so backup-failure dialogs in
        # phase 2 are not swallowed.
        run('args[0]._applyPhase2(args[1])', self, interactive,
            delayFrames=150)
        return {'status': 'applying'}

    def _applyPhase2(self, interactive):
        if self._staleInstance():
            return
        pending = self._pending
        embody = self._embody

        # Stop Envoy cleanly so the port is free and its registry entry is
        # removed (onDestroyTD alone does not remove the envoy.json entry).
        # Gate on Envoyenable, not the status string (which reads
        # 'Running on port N' / 'Restarting after save...').
        try:
            if embody.par.Envoyenable.eval():
                embody.ext.Envoy.Stop()
                self._log('Envoy stopped for update')
        except Exception as e:
            self._log(f'Envoy stop skipped: {e!r}', 'WARNING')

        # Rollback artifact FIRST, verified before anything is touched.
        old_version = embody.par.Version.eval()
        backup = self._posix(self._updatesDir(create=True)
                            / f'backup-v{old_version}.tox')
        try:
            # run_hooks=False: this backup is update machinery, not an
            # authored release. Embody-self exports always run in LIVE
            # hook mode (never copy-staged), so hook DATs authored in the
            # DEV project ship inside the released Embody tox -- and
            # would execute here, inside an end user's project, or abort
            # the backup. Suppress them.
            ok = embody.ext.Embody.ExportPortableTox(target=embody,
                                                     save_path=backup,
                                                     run_hooks=False)
        except Exception as e:
            self._busy = False
            self._fail(f'Backup export failed -- update aborted: {e!r}')
            return
        if not ok:
            # ExportPortableTox reports failures via its return value
            # (export errors are exception-contained) -- without this
            # gate a STALE backup from a prior attempt could pass the
            # isfile/size checks below and become the rollback artifact.
            self._busy = False
            self._fail('Backup export reported failure -- update aborted.')
            return
        if (not os.path.isfile(backup)
                or os.path.getsize(backup) < self.MIN_BACKUP_BYTES):
            self._busy = False
            self._fail('Backup tox missing or implausibly small -- '
                       'update aborted.')
            return
        # Everything from here to the reload is guarded as one unit: a raise
        # in this region (a Windows file lock on the just-exported backup, a
        # read-only .embody/updates) used to escape the run() callback with
        # NO dialog, the status stuck on 'Installing ...' and _busy latched
        # True -- so every later check answered 'An update operation is
        # already running' for the rest of the session. Install-stage
        # failures ALWAYS dialog (see the module docstring); nothing here has
        # touched the live component yet, so the refusal is clean.
        try:
            backup_sha = self._sha256File(backup)

            # Reload token: the EmbodyExt DAT's op id changes when children
            # are recreated by a REAL reload. A no-op/failed reload keeps the
            # old id, and VerifyUpdate refuses to stamp success in that case
            # (so par.Version can never lie about an install that didn't
            # happen).
            try:
                reload_token = embody.op('EmbodyExt').id
            except Exception:
                reload_token = None

            # Crash sentinel: if TD dies mid-swap, the next open finds this
            # and offers the (integrity-checked) backup. `session` stamps the
            # process applying it, so the reloaded component -- which boots in
            # THIS process while the swap is still being verified -- can tell
            # its own update in flight from one a crash interrupted.
            self._writeSentinel({
                'from_version': old_version,
                'to_version': pending['version'],
                'tag': pending['tag'],
                'tox_path': pending['tox_path'],
                'backup_path': backup,
                'backup_sha256': backup_sha,
                'reload_token': reload_token,
                'manifest': pending['manifest'],
                'interactive': bool(interactive),
                'session': self._sessionMark(),
                'phase': 'reloading',
            })
            self._log(f'applying {pending["tag"]}: in-place reload from '
                      f'{pending["tox_path"]} (backup: {backup})')

            # Post-reload verifier: STRING form, resolves the FRESH instance
            # via the surviving host COMP, guarded against a missing 'updater'
            # child, no delayRef, generous delay for the new version's boot
            # chain. This run survives destruction of this extension's own
            # host child.
            ep = embody.path
            verify = (f"op('{ep}').op('updater').ext.UpdaterExt"
                      f".VerifyUpdate(0) "
                      f"if op('{ep}') and op('{ep}').op('updater') else None")
            run(verify, delayFrames=300)
        except Exception as e:
            self._busy = False
            self._clearSentinel()
            self._fail(f'Update could not be started -- nothing was '
                       f'changed: {e!r}')
            return

        # ---- The reload. The undo block is opened AND closed here, so the
        # pulse is the LAST TD-touching statement (its own host dies with it).
        p = embody.par.externaltox
        ui.undo.startBlock('Embody self-update', enable=False)
        was = p.readOnly
        p.readOnly = False
        p.val = pending['tox_path']
        p.readOnly = was
        embody.par.reloadcustom = False
        embody.par.reloadbuiltin = False
        embody.par.enableexternaltox = True
        ui.undo.endBlock()
        embody.par.enableexternaltoxpulse.pulse()

    # ==================================================================
    # VERIFY (promoted): runs in the NEW extension instance post-reload
    # ==================================================================

    def VerifyUpdate(self, attempts=0):
        """Confirm the reload booted; stamp About pars; clean up or roll back."""
        sentinel = self._readSentinel()
        if not sentinel:
            # Benign since 6.0.247: StartupCheck re-arms verification for a
            # live-but-unowned swap, so two passes can be scheduled and the
            # loser finds the work already done.
            self._log('VerifyUpdate: no pending sentinel -- already verified',
                      'DEBUG')
            return
        embody = self._embody
        ext_dat = embody.op('EmbodyExt')
        # A REAL reload recreated the children, so EmbodyExt has a new op id.
        reloaded = (ext_dat is not None
                    and ext_dat.id != sentinel.get('reload_token'))
        booted = (reloaded
                  and embody.op('execute') is not None
                  and embody.extensionsReady)
        if not booted:
            if attempts < 10:
                ep = embody.path
                run(f"op('{ep}').op('updater').ext.UpdaterExt"
                    f".VerifyUpdate({attempts + 1}) "
                    f"if op('{ep}') and op('{ep}').op('updater') else None",
                    delayFrames=120)
                return
            self._rollback(sentinel, 'new version never finished booting')
            return

        # NOTHING BELOW MAY BLOCK UNTIL THE SENTINEL IS GONE. ui.messageBox is
        # modal to the caller but NOT to TouchDesigner: run() callbacks keep
        # firing while it is open. The retired-settings dialog used to be
        # raised from inside this sequence, five statements short of
        # _clearSentinel -- so the reloaded component's own startup sweep read
        # a live sentinel and offered to roll back the update that was busy
        # succeeding (field report, v6.0.246). Every mutation completes first;
        # reporting happens at the end, when there is no half-applied state
        # left for a concurrent caller to act on.
        manifest = sentinel['manifest']
        self._stampAboutPars(manifest)
        # The reload preserves live par values. That is right for the user's
        # settings and wrong for pars the BUILD owns, so re-assert those, then
        # retire settings this version no longer declares.
        self._applyBuildOwnedPars(manifest)
        retired = self._pruneRetiredPars(manifest)
        self._clearExternalTox()
        self._cleanupFiles(sentinel, keep_backup=True)
        self._clearSentinel()
        self._status(f'Updated to {sentinel["tag"]}')
        self._log(f'update to {sentinel["tag"]} verified '
                  f'(from v{sentinel["from_version"]})', 'SUCCESS')
        # ---- critical section over; dialogs are safe from here ----
        if sentinel.get('interactive'):
            message = (f'Embody was updated to {sentinel["tag"]}.\n\n'
                       'Settings and externalizations were preserved.')
            if retired:
                # ONE dialog, not two. These are removals the user did not ask
                # for, so they are reported -- but as part of the update's own
                # result, not as a separate alarm that lands before the update
                # has even announced itself.
                message += ('\n\nThese settings no longer exist in this '
                            'version and were removed:\n' + ', '.join(retired))
            self._dialog('Embody Update', message, ['OK'])

    def _stampAboutPars(self, manifest):
        """Preserved par values keep the OLD About info -- stamp the new."""
        embody = self._embody
        stamps = {
            'Version': manifest.get('version'),
            'Touchbuild': manifest.get('td_build'),
            'Build': manifest.get('build'),
            'Date': manifest.get('date'),
        }
        for name, value in stamps.items():
            if value is None:
                continue
            par = getattr(embody.par, name, None)
            if par is not None:
                self._setPar(par, value)

    def _applyBuildOwnedPars(self, manifest):
        """Re-assert every built-in par the NEW build declares.

        The reload preserves live par values: right for the user's settings,
        wrong for the component's own wiring, because a build that changes one
        could otherwise never make it take effect on an existing install. The
        set is not hand-picked here -- the exporter records every built-in this
        build sets away from its TD default (`builtin_pars`), so a par added in
        a future version is carried automatically.

        Why the whole set matters, not just the obvious one: v6.0.233 shipped
        the status readout, and BOTH `nodeview` and `opviewer` had to move for
        the node to display it. Fixing only `opviewer` left it inert and the
        update still looked like a no-op (v6.0.245 shipped exactly that
        mistake). The same hole would silently drop a newly added extension,
        since ext*object/ext*name/ext*promote are built-in pars too.

        Mode travels with the value: w/h are BIND, and assigning .val to a
        bound par switches it to CONSTANT (rules/parameters.md). Custom pars
        are never touched -- those are the user's settings.
        """
        declared = manifest.get('builtin_pars')
        if not declared:
            return  # pre-6.0.246 manifest -- nothing declared, assert nothing
        embody = self._embody
        applied, skipped = [], []
        for name, spec in declared.items():
            par = getattr(embody.par, name, None)
            if par is None:
                continue
            try:
                mode = (spec or {}).get('mode', 'CONSTANT')
                value = (spec or {}).get('value', '')
                # Never point an op reference at something this build lacks.
                if (mode == 'CONSTANT' and isinstance(value, str)
                        and value.startswith('./')):
                    if embody.op(value[2:]) is None:
                        skipped.append(name)
                        continue
                if self._parMatches(par, mode, value):
                    continue
                self._setParMode(par, mode, value)
                applied.append(name)
            except Exception as e:
                self._log(f'could not assert built-in par {name}: {e}',
                          'WARNING')
        if applied:
            self._log(f'asserted {len(applied)} build-owned par(s) the reload '
                      f'preserved: {", ".join(sorted(applied))}')
        if skipped:
            self._log(f'left {", ".join(sorted(skipped))} as-is (target not '
                      f'present in this build)', 'DEBUG')

    @staticmethod
    def _parMatches(par, mode, value):
        """True when the live par already carries the declared mode+value."""
        if par.mode.name != mode:
            return False
        if mode == 'EXPRESSION':
            return par.expr == value
        if mode == 'BIND':
            return par.bindExpr == value
        return str(par.val) == str(value)

    def _setParMode(self, par, mode, value):
        """Assign honouring MODE -- .val on a bound/expression par would drop
        it to CONSTANT and silently break the binding."""
        # ParMode is a DAT-namespace global and absent from the td module, so
        # the enum is taken off the live par -- no namespace dependency.
        par_mode = getattr(type(par.mode), mode, None)
        was = par.readOnly
        par.readOnly = False
        try:
            if mode == 'EXPRESSION':
                par.expr = value
            elif mode == 'BIND':
                par.bindExpr = value
            else:
                par.val = value
            if par_mode is not None:
                par.mode = par_mode
        finally:
            par.readOnly = was

    @staticmethod
    def _isSequenceBlockPar(par):
        """True for a par that lives inside a custom SEQUENCE block.

        Sequence blocks are a RUNTIME projection, never a setting: ConvoyExt
        sizes the Convoy Nodes sequence to this machine's live Convoy mesh
        (`seq.numBlocks = len(rows)`), so the block count differs on every
        install and drifts within a session. The sequence HEADER par is
        authored and static, so it is NOT a block par and stays prunable
        like any other declaration.

        Verified on docs.derivative.ca/Par_Class: `Par.sequence` is the
        Sequence a par belongs to (None when it belongs to none), and
        `Par.isSequence` is True for the header. Access is defended because
        Embody's own sequence code carries build-portability fallbacks
        (ConvoyExt._sequenceBlockPar); an unreadable attribute is treated as
        'a block', i.e. keep it -- never destroy on a guess.
        """
        try:
            if getattr(par, 'isSequence', False):
                return False
            return getattr(par, 'sequence', None) is not None
        except Exception:
            return True

    def _pruneRetiredPars(self, manifest):
        """Remove custom pars this build no longer declares; return the names.

        The reload preserves live custom-par VALUES (they are the user's
        settings, and an update must never rewrite them) -- but that also
        strands pars a newer build removed, leaving dead settings on the
        component forever. The manifest's `custom_pars` is the build's own
        declaration of what exists; anything else is retired.

        Silent on manifests that predate the field, and it only ever removes
        pars the OLD build had: a par the new build declares is untouched, and
        new ones arrive with the reload.

        SEQUENCE BLOCK PARS ARE NEVER TOUCHED, whatever the manifest says.
        v6.0.245 and v6.0.246 shipped manifests that declared the developer's
        own Convoy node blocks, so a user with a bigger mesh had the surplus
        rows destroyed and was told four status cells were 'settings that no
        longer exist'. Two further reasons this guard is not merely cosmetic:
        `Par.destroy()` on a sequential par destroys its ENTIRE block and
        renumbers the survivors, so the by-name re-lookup below would retarget
        live blocks; and the manifests already published cannot be un-shipped,
        so the CONSUMER is the only place that can protect those users.

        Returns the list of removed names -- it does not dialog. Reporting is
        the caller's, deliberately: a modal opened from here would park inside
        VerifyUpdate's critical section with the sentinel still on disk, which
        is exactly what let StartupCheck offer to roll back a healthy update.
        """
        declared = manifest.get('custom_pars')
        if not declared:
            return []  # pre-6.0.245 manifest -- no source of truth, prune none
        embody = self._embody
        declared = set(declared)
        # Names first: destroying a Par invalidates the OTHER Par objects held
        # in a snapshot, so each removal is re-looked-up by name.
        candidates = [p.name for p in embody.customPars
                      if p.name not in declared
                      and not self._isSequenceBlockPar(p)]
        # Pages that were ALREADY empty before this prune. Anything in here is
        # not ours to remove -- see the sweep below.
        try:
            was_empty = {page.name for page in embody.customPages
                         if not page.pars}
        except Exception:
            was_empty = None
        retired = []
        for name in candidates:
            par = getattr(embody.par, name, None)
            if par is None:
                continue
            try:
                par.destroy()
                retired.append(name)
            except Exception as e:
                self._log(f'could not remove retired par {name}: {e}',
                          'WARNING')
        if retired and was_empty is not None:
            # ONLY pages THIS PRUNE emptied. The sweep used to run over every
            # custom page whenever anything at all was retired, so a page whose
            # remaining content is a sequence (Page.pars is not documented to
            # include sequence members) could read as empty and be destroyed
            # outright -- taking the sequence definition with it, unrecoverable
            # without another tox reload.
            try:
                for page in list(embody.customPages):
                    if page.name not in was_empty and not page.pars:
                        page.destroy()
            except Exception:
                pass
        if retired:
            self._log(f'removed {len(retired)} setting(s) retired in this '
                      f'version: {", ".join(sorted(retired))}', 'WARNING')
        return sorted(retired)

    def _clearExternalTox(self):
        """Detach from the downloaded file so a later save can't clobber it."""
        embody = self._embody
        p = embody.par.externaltox
        was = p.readOnly
        p.readOnly = False
        p.val = ''
        p.readOnly = was
        embody.par.enableexternaltox = False

    def _cleanupFiles(self, sentinel, keep_backup=True):
        """Remove the applied download; keep only the most recent backup."""
        try:
            tox = sentinel.get('tox_path')
            if tox and os.path.isfile(tox) and self._withinUpdates(tox):
                os.unlink(tox)
        except OSError:
            pass
        if keep_backup:
            return
        try:
            b = sentinel.get('backup_path')
            if b and os.path.isfile(b) and self._withinUpdates(b):
                os.unlink(b)
        except OSError:
            pass

    # ==================================================================
    # ROLLBACK
    # ==================================================================

    def _validBackup(self, sentinel):
        """The backup must be inside updates/ and match its recorded hash."""
        backup = sentinel.get('backup_path')
        if not backup or not os.path.isfile(backup):
            return None, 'backup file is missing'
        if not self._withinUpdates(backup):
            return None, 'backup path is outside .embody/updates'
        want = sentinel.get('backup_sha256')
        if want and self._sha256File(backup) != want:
            return None, 'backup failed its integrity check'
        return backup, None

    def _rollback(self, sentinel, why):
        self._log(f'update FAILED ({why}) -- rolling back to '
                  f'v{sentinel.get("from_version")}', 'ERROR')
        backup, berr = self._validBackup(sentinel)
        if backup is None:
            self._status('Update FAILED; backup unusable -- reopen saved .toe')
            sentinel['phase'] = 'rollback_failed'
            self._writeSentinel(sentinel)
            self._dialog(
                'Embody Update FAILED',
                f'The update failed ({why}) and the backup is unusable '
                f'({berr}). Close WITHOUT saving and reopen the project to '
                'recover.', ['OK'])
            return
        sentinel['phase'] = 'rolling_back'
        self._writeSentinel(sentinel)
        embody = self._embody
        ep = embody.path
        try:
            reload_token = embody.op('EmbodyExt').id
        except Exception:
            reload_token = None
        sentinel['rollback_token'] = reload_token
        self._writeSentinel(sentinel)
        run(f"op('{ep}').op('updater').ext.UpdaterExt.VerifyRollback(0) "
            f"if op('{ep}') and op('{ep}').op('updater') else None",
            delayFrames=300)
        p = embody.par.externaltox
        ui.undo.startBlock('Embody update rollback', enable=False)
        was = p.readOnly
        p.readOnly = False
        p.val = backup
        p.readOnly = was
        embody.par.reloadcustom = False
        embody.par.reloadbuiltin = False
        embody.par.enableexternaltox = True
        ui.undo.endBlock()
        embody.par.enableexternaltoxpulse.pulse()

    def VerifyRollback(self, attempts=0):
        sentinel = self._readSentinel()
        embody = self._embody
        ext_dat = embody.op('EmbodyExt')
        reloaded = (ext_dat is not None and sentinel is not None
                    and ext_dat.id != sentinel.get('rollback_token'))
        booted = reloaded and embody.extensionsReady
        if not booted and attempts < 10:
            ep = embody.path
            run(f"op('{ep}').op('updater').ext.UpdaterExt"
                f".VerifyRollback({attempts + 1}) "
                f"if op('{ep}') and op('{ep}').op('updater') else None",
                delayFrames=120)
            return
        self._clearExternalTox()
        if booted:
            self._clearSentinel()
            self._status('Update failed -- previous version restored')
            self._dialog(
                'Embody Update',
                'The update failed and the previous version was restored '
                'from backup. Details are in the Embody log.', ['OK'])
        else:
            # Rollback itself failed -- KEEP the sentinel so the next open
            # can re-offer recovery. This is exactly when it matters most.
            if sentinel is not None:
                sentinel['phase'] = 'rollback_failed'
                self._writeSentinel(sentinel)
            self._status('Update AND rollback failed -- reopen saved .toe')
            self._dialog(
                'Embody Update FAILED',
                'The update and the automatic rollback both failed. Close '
                'WITHOUT saving and reopen the project to recover the last '
                'saved state.', ['OK'])

    def _resumeVerifyIfOrphaned(self, sentinel):
        """Arm verification for a live swap this process did not schedule.

        _applyPhase2 arms VerifyUpdate in the same breath as the reload, so
        the session that started the update needs nothing here -- re-arming
        there would just race its own verifier.

        A swap found LIVE in a different process is the case that needs it:
        the component is already pointed at the new tox (so the update
        effectively applied) but nothing is left to stamp the About pars,
        re-assert build-owned pars, clear externaltox or clean up. Suppressing
        the recovery prompt without this would trade a wrong dialog for a
        silent half-applied install. Once only, so a verifier that keeps
        failing cannot loop.
        """
        if self._sameSession(sentinel) or getattr(self, '_rearmed', False):
            return
        self._rearmed = True
        ep = self._embody.path
        self._log('startup sweep: re-arming verification for an update left '
                  'unverified by a previous session', 'INFO')
        run(f"op('{ep}').op('updater').ext.UpdaterExt.VerifyUpdate(0) "
            f"if op('{ep}') and op('{ep}').op('updater') else None",
            delayFrames=120)

    # ==================================================================
    # STARTUP (promoted): called from execute.py at ~frame 150
    # ==================================================================

    def StartupCheck(self):
        """Crash-recovery sweep, then the Autoupdate-gated auto check."""
        if self._staleInstance():
            return
        sentinel = self._readSentinel()
        if sentinel:
            if self._updateInFlight(sentinel):
                # NOT an interrupted update -- one that is still finishing.
                # An in-place reload keeps the same TD process, and the
                # reloaded component runs this very sweep (execute.py's
                # onCreate) at the same frame budget VerifyUpdate uses, so
                # without this gate a successful self-update offers to roll
                # itself back. Answering 'Keep Current State' was the worse
                # outcome: it deletes the sentinel out from under
                # VerifyUpdate, which then stamps nothing -- par.Version
                # keeps naming the OLD release, build-owned pars are never
                # re-asserted, and externaltox is left pointing into
                # .embody/updates, so the component breaks the moment that
                # file is cleaned up or the project moves.
                self._log(f'startup sweep: the update to '
                          f'{sentinel.get("tag")} is still being verified '
                          f'-- no recovery prompt', 'DEBUG')
                self._resumeVerifyIfOrphaned(sentinel)
                return
            # A previous update never completed (TD crashed or was closed
            # mid-swap). Surface it regardless of the Autoupdate setting.
            backup, berr = self._validBackup(sentinel)
            if backup is None:
                self._log(f'interrupted update found but backup unusable '
                          f'({berr}); clearing sentinel', 'WARNING')
                self._dialog(
                    'Embody Update',
                    f'A previous update to {sentinel.get("tag")} did not '
                    f'complete and its backup is unusable ({berr}). No '
                    'automatic recovery is possible.', ['OK'])
                self._clearSentinel()
                return
            choice = self._dialog(
                'Embody Update Recovery',
                f'An update to {sentinel.get("tag")} did not complete. '
                'Restore the pre-update backup?',
                ['Restore Backup', 'Keep Current State'])
            if choice == 0:
                self._rollback(sentinel, 'recovering interrupted update')
            elif choice == 1:
                # Explicit "keep" only -- a suppressed/dismissed dialog (-1)
                # leaves the sentinel so the next open re-offers recovery.
                self._clearSentinel()
            return

        mode = 'off'
        p = getattr(self._embody.par, 'Autoupdate', None)
        if p is not None:
            mode = str(p.eval())
        if mode == 'off':
            # Truthful resting state, never a blank: an empty read-only
            # status field looks broken on a fresh install, and 'Disabled'
            # also replaces a stale result left by a session that had
            # checks enabled.
            self._status('Disabled')
            return
        if self.isDevCheckout():
            # Say WHY on the status readout, once: a silent return left
            # the release scrub's bare 'Disabled' on the panel for the
            # whole session, which the readout rendered as if the USER
            # had switched updates off while Autoupdate said notify.
            self._status('Disabled -- dev checkout (update via git)')
            return
        # notify: check + status/log only. install: check + full apply.
        # CHECK-stage failures stay quiet on this auto path; INSTALL-stage
        # failures (backup/reload/verify/rollback) always dialog via _fail.
        self.CheckForUpdate(interactive=False,
                            auto_install=(mode == 'install'))
