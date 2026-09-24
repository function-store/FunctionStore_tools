---
package: ChopBank
summary: 'A bank of channel processors: one block per channel, each with its own range, exponent curve, zero-below, lag and speed mode, built from the input with one Snap Input, with gain before and after and every block promoted as a property. An alternative for the Math CHOP and the Constant CHOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Input and output
    anchor: input-and-output
---

## What it is

ChopBank shapes a whole controller in one node. Every block in the Bank is one channel with its own processing: a range to limit and remap it, an exponent curve, Zero Below, a lag, and a speed mode that turns it into a running total. It's the same chain as ChopProcess, set per channel. A fader bank where each fader needs a different range and feel is one node, not eight.

Snap Input builds the bank for you: it makes one block per incoming channel, named after it and holding its current value. A new block starts with the settings of the block before it, so setting up a row of similar faders is quick. With Promote to Property on, each block is also a property on the node, so `op('ChopBank').Fader1` reads and sets that block's Value.

A block takes the input channel it is named after, or the channel at its position when its Name is empty. When no input channel matches, it outputs its own Value instead. That way a bank can also add channels that aren't in the input.

It is an alternative for the Math CHOP and for the Constant CHOP: create either with the alternatives shortcut held and ChopBank is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Input and output

- **in1** (CHOP): the channels to process.
- **out1** (CHOP): one processed channel per block.
