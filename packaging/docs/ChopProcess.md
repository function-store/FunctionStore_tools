---
package: ChopProcess
summary: 'Shapes channels in one node: limit, remap between ranges with an exponent curve, zero at the bottom, lag, and an optional speed mode that turns the result into a running total. An alternative for the Math CHOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Input and output
    anchor: input-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

ChopProcess is the chain you build after almost every controller, in one node. It limits the incoming values to a range, remaps that range onto another through an exponent curve, glides toward new values with a lag, and can treat the result as a speed and output its running total instead. Every channel of the input goes through it, so one node shapes a whole fader bank.

Zero Below makes the bottom of the input range output 0 instead of the bottom of the output range. It's handy when a fader should switch something fully off at its lowest point but start from a useful value as soon as it moves.

It is the alternative for the Math CHOP: create a Math CHOP with the alternatives shortcut held and ChopProcess is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Input and output

- **in1** (CHOP): the channels to process. With nothing connected, the Value parameter is processed instead.
- **out1** (CHOP): the processed channels.

## Parameters

### Custom

- **Value** (Float): the value to process when nothing is wired into the input.
- **Name** (Str): rename the output channels, with names separated by spaces or a pattern like `chan[1-4]`. Empty keeps the input's names.
- **Type** (Menu): what happens outside the From Range: off, clamp, loop or zigzag.
- **From Range**, **To Range** (Float, two values each): the input range and the output range it maps onto.
- **Zero Below** (Toggle): output 0 at the bottom of the From Range. Only with Type set to clamp.
- **Exponent Value** (Float): the curve between the ranges. 1 is linear, above 1 eases in, and below 1 eases out.
- **Lag** (Float, two values): seconds to glide up and down toward a new value.
- **Is Speed** (Toggle): output the running total of the processed value, so a held input keeps moving.
- **Limit Type**, **Minimum**, **Maximum** (Menu, Float): what the running total does at its limits.
- **Reset Value** (Float), **Reset** (Toggle), **Reset Pulse** (Pulse): hold or return the running total to the Reset Value.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
