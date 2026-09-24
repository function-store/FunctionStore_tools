---
package: ChopProcess
summary: 'Shapes channels in one node: limit, remap between ranges with an exponent curve, zero at the bottom, lag, and an optional speed mode that turns the result into a running total. An alternative for the Math CHOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Input and output
    anchor: input-and-output
---

## What it is

ChopProcess is the chain you build after almost every controller, in one node. It limits the incoming values to a range, remaps that range onto another through an exponent curve, glides toward new values with a lag, and can treat the result as a speed and output its running total instead. Every channel of the input goes through it, so one node shapes a whole fader bank.

Zero Below makes the bottom of the input range output 0 instead of the bottom of the output range. It's handy when a fader should switch something fully off at its lowest point but start from a useful value as soon as it moves.

It is the alternative for the Math CHOP: create a Math CHOP with the alternatives shortcut held and ChopProcess is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Input and output

- **in1** (CHOP): the channels to process. With nothing connected, the Value parameter is processed instead.
- **out1** (CHOP): the processed channels.
