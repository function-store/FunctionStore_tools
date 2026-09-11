---
package: FNS_Remote
summary: Control this project from your phone over your own network, with no cloud and no account
features:
  - name: Pair by QR
    anchor: pair-by-qr
  - name: What you can drive
    anchor: what-you-can-drive
  - name: The toolbar button
    anchor: the-toolbar-button
  - name: Expose from the phone
    anchor: expose-from-the-phone
  - name: The client link
    anchor: the-client-link
  - name: Off by default, local by default
    anchor: off-by-default-local-by-default
---

## Pair by QR

Press **Open Pairing** on the component, click the phone button in the
toolbar, or run the Phone Remote command, and a small window opens inside
TouchDesigner with the code. Scan it with the phone. Nothing leaves the
machine to draw it: the code is rendered by the tool itself, there is no
cloud service in the middle, no account, and nothing to sign into. Each
machine mints its own access token the first time it serves, and the link
carries it.

The window shows a code only while **LAN access** is on, because a phone
cannot reach a server that listens on this machine alone. When it is off
the window says so and offers the switch, so pairing is two clicks from
cold: open, allow LAN, scan.

The token is deliberately **not** a parameter. Parameters travel inside
the `.toe`, and a token that travels is a token you gave away, so it
lives beside the toolkit's config on the machine that minted it. **Regenerate
Token** invalidates every link that was handed out before.

## What you can drive

Point it at components and expose their parameter pages, and those become
controls on the phone: sliders, toggles, menus and pulse buttons, in the
Control tab that the page opens on. A parameter group, a position or a
colour, is one row showing its values; tap it and it opens into one slider
per component. A perform window can be exposed in one toggle. Multi-touch,
in the Touch tab, arrives as a CHOP you can wire into anything, with the
touch count you set and optional normalising and Y-flip.

## The toolbar button

A phone icon in the toolbar. Click it to open the pairing window with the
QR code; if the remote is not serving yet, that starts it. The button lights
while the remote is serving.

Drag a component from a network editor onto the button to make it **the**
component the phone controls. Hold **Alt** while dropping to **add** it
to the component list instead, so several components are exposed at once.
A component that is already listed is switched on rather than listed
twice. Dropping a parameter works too and exposes the component it belongs
to. The exposure is the same one the Control page describes, so the page
filters and the per-component switch are there when you want them.

## Expose from the phone

The Control tab ends with **Expose a component**. It opens a browser of
the project, one level at a time: every component with parameters or with
components inside, its parameter count beside it. Tap **Expose** to add
one to the controls, the arrow to look inside it, **Up** to come back. A
cross beside a component's name in the Control tab stops exposing it.
This is the same list the Control page and the toolbar drop maintain, so
the three agree.

## The client link

There are two links, and the pairing window hands out one at a time.
The full link is yours. The **client link** is a second code, minted
beside the first, that opens only the exposed controls: no session
actions, no browsing the project, and the server refuses those routes on
it, so hiding them on the page is not what keeps them shut. Turn on
**Pair the Client Link** and the window, its QR code and Click to open
here switch to the client link; turn it off and they switch back. **Touch
on Client Link** decides whether that link also gets the touch pad, so a
rig can hand out a sliders-only page. **Regenerate Token** renews both
codes at once.

## Off by default, local by default

It serves nothing until you turn it on, and when it does it binds to
loopback until you opt into LAN. That is deliberate: a project that
quietly opened a port on every network it ever joined would be a liability.
