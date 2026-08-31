---
package: FNS_Remote
summary: Control this project from your phone over your own network, with no cloud and no account
features:
  - name: Pair by QR
    anchor: pair-by-qr
  - name: What you can drive
    anchor: what-you-can-drive
  - name: Off by default, local by default
    anchor: off-by-default-local-by-default
---

## Pair by QR

Turn it on and scan the code. The page is served by the project itself,
so there is no cloud service in the middle, no account, and nothing to
sign into. Each machine mints its own access token the first time it
serves, and the link carries it.

The token is deliberately **not** a parameter. Parameters travel inside
the `.toe`, and a token that travels is a token you gave away — so it
lives beside the toolkit's config on the machine that minted it. **Regenerate
Token** invalidates every link that was handed out before.

## What you can drive

Point it at components and expose their parameter pages, and those become
controls on the phone. A perform window can be exposed in one toggle.
Multi-touch arrives as a CHOP you can wire into anything, with the touch
count you set and optional normalising and Y-flip.

## Off by default, local by default

It serves nothing until you turn it on, and when it does it binds to
loopback until you opt into LAN. That is deliberate: a project that
quietly opened a port on every network it ever joined would be a liability
rather than a feature.
