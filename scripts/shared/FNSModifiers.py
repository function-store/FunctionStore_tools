"""Authoritative modifier-key state, shared by the tools that need it.

WHY THIS EXISTS
---------------
TouchDesigner's Keyboard In CHOP latches. The app loses focus while a
modifier is down, the keyup event is never delivered, and the channel stays
at 1 until that key is pressed and released again. Alt-tabbing is the usual
cause and macOS is markedly worse. The stickiness is in TD's event
integration, so it cannot be fixed at the CHOP layer.

WHAT TD OFFERS INSTEAD (measured 2026-09-01, TD 2025.33070)
-----------------------------------------------------------
Nothing usable for this. `ui` exposes no modifier state at all -- the full
attribute list has rollover/rolloverOp/rolloverPar/rolloverParGroup and
nothing for keys. TD's panel values DO carry `ctrl` / `alt` / `shift` /
`cmd`, but the documented semantics are "1 if the key is down WHEN THE
PANEL IS CLICKED ON": they are latched at click time. That is immune to a
missed keyup, but it cannot answer "is shift held right now" anywhere
except inside a click on that specific panel -- and all three callers read
outside a click (a hotkey handler, a drop handler, and a display refresh).
So panel values are the right idea with the wrong lifetime.

THE SEAM
--------
Callers use `held('shift')`. Everything below it is strategy, kept in ONE
file precisely so it can be changed without touching three tools again.
The alternatives considered were: timeout decay (clear a modifier held
longer than N seconds -- crude, cannot tell a genuinely-held key from a
stuck one) and reconcile-on-next-event (cheap, but does not end the stuck
window, only waits for the user to end it).

FALLBACK IS THE CONTRACT
------------------------
`held()` returns True, False, or **None meaning "cannot tell"** -- an
unsupported platform, a library that will not load, any exception. Callers
treat None as "fall back to whatever you read before", so a platform where
this does not work behaves EXACTLY as it does today. It never fails open
(inventing a held modifier) and never fails shut (denying a real one).

macOS is IMPLEMENTED BUT UNVERIFIED: it was written from the
ApplicationServices API and could not be tested from Windows. If it is
wrong it raises, `held()` returns None, and the Mac keeps its current
behaviour -- which is the whole reason the fallback is shaped this way.
"""

import sys

# Windows virtual-key codes. Left/right variants are folded together: a
# caller asking "is shift held" does not care which shift.
_VK = {
	'shift': (0x10,),
	'ctrl':  (0x11,),
	'alt':   (0x12,),
	'cmd':   (0x5B, 0x5C),   # left/right Win key, the Windows analogue
}

# macOS CGEventFlags bits (ApplicationServices/CoreGraphics).
_CG_FLAG = {
	'shift': 1 << 17,
	'ctrl':  1 << 18,
	'alt':   1 << 19,   # Option
	'cmd':   1 << 20,
}

_NAMES = ('shift', 'ctrl', 'alt', 'cmd')

_mac_source = None       # cached CGEventSourceFlagsState, or False once failed


def _heldWindows(name):
	import ctypes
	codes = _VK.get(name)
	if not codes:
		return None
	gaks = ctypes.windll.user32.GetAsyncKeyState
	# high bit = currently down; the low bit is "pressed since last call"
	# and must NOT be used -- it would report a key the user already released.
	return any(bool(gaks(c) & 0x8000) for c in codes)


def _heldMac(name):
	"""macOS via CGEventSourceFlagsState. UNVERIFIED -- see module docstring."""
	global _mac_source
	bit = _CG_FLAG.get(name)
	if not bit:
		return None
	if _mac_source is False:
		return None
	if _mac_source is None:
		import ctypes, ctypes.util
		path = ctypes.util.find_library('ApplicationServices')
		if not path:
			_mac_source = False
			return None
		lib = ctypes.cdll.LoadLibrary(path)
		fn = lib.CGEventSourceFlagsState
		fn.restype = ctypes.c_uint64
		fn.argtypes = [ctypes.c_uint32]
		_mac_source = fn
	# 1 = kCGEventSourceStateCombinedSessionState
	return bool(_mac_source(1) & bit)


def held(name):
	"""True / False / None for one modifier, asked of the OS right now.

	None means CANNOT TELL, and is the caller's signal to fall back to
	whatever it read before. Never raises.
	"""
	key = str(name or '').strip().lower()
	if key not in _NAMES:
		return None
	try:
		if sys.platform == 'win32':
			return _heldWindows(key)
		if sys.platform == 'darwin':
			return _heldMac(key)
	except Exception:
		return None
	return None


def heldOr(name, fallback):
	"""`held(name)`, or `fallback` when the OS cannot be asked.

	The shape every caller wants: one expression that is authoritative
	where it can be and unchanged where it cannot.
	"""
	value = held(name)
	return bool(fallback) if value is None else value


def state():
	"""All four modifiers at once, for diagnostics. None where unknown."""
	return {n: held(n) for n in _NAMES}


def available():
	"""Whether this platform can answer at all -- for a status readout."""
	return held('shift') is not None
