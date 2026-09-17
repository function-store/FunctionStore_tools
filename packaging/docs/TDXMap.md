---
package: TDXMap
summary: 'MIDI controller mapping with a live web UI: multiple devices, banks, Smart Learn, button actions, 14-bit controls. Its own product with its own licence, a 14-day trial then Base or Pro, installable from the picker.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Installing from the toolkit
    anchor: installing-from-the-toolkit
  - name: Updates and licensing
    anchor: updates-and-licensing
---

## What it is

TDXMap maps MIDI controllers to TouchDesigner parameters through a web UI
served from inside your project: drag a parameter onto a knob, fader or
button, switch banks per device, and let Smart Learn work out what the
hardware sends. The full manual, guides and changelog live on its own
site: [tdxmap.functionstore.xyz](https://tdxmap.functionstore.xyz).

TDXMap is a **family product**, not a toolkit tool. The toolkit mirrors its
released build so you can install it from the same picker as everything
else, but the tool itself, its updates and its licensing are its own.

## Installing from the toolkit

Tick **TDXMap** in the installer picker. It lands at your network root,
beside the toolkit container, so `op.TDXMap` resolves from anywhere in the
project, the address its own documentation assumes.

Once installed, it does not depend on any toolkit registry and works with
the toolkit removed.

## Updates and licensing

TDXMap keeps itself current. The toolkit's Updates view lists it as
**updates itself** and never touches it: check for updates from the
TDXMap preferences footer, which downloads the new build and reloads it
in place.

TDXMap is not free. A 14-day trial of Pro runs once per computer; after
it the mapping editor needs a Function Store Patreon membership at the
Base or Pro tier, or a Gumroad lifetime key. Live MIDI to parameters
keeps working without one, and your mappings are kept. See
[licensing](https://tdxmap.functionstore.xyz/license/) on the product
site.
