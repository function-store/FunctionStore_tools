---
package: ConstantCHOP
summary: 'A Constant CHOP with typed values: numbers, toggles, tuples, text, paths or operator references, each promoted as a property you can read and set from Python, and a snap from its input. An alternative for the Constant CHOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Input and outputs
    anchor: input-and-outputs
---

## What it is

ConstantCHOP holds a list of named values, like the Constant CHOP, but the values don't have to be plain numbers. Pick a Type and every constant becomes a float, an integer, a toggle, a four-value tuple such as XYZW or RGBA, a string, a file or folder path, or a reference to an operator. Numbers, toggles and tuples come out as channels; text, paths and references come out as a table.

With Promote to Property on, each constant is also a property on the node: `op('ConstantCHOP').Speed` reads and sets the constant named `speed`, and `Speed_out` reads what the node outputs. A prefix keeps those names clear of anything else on the COMP.

Snap Input takes whatever is wired in and turns it into constants, one per channel, named and valued from it. Switching Type keeps each value wherever it converts.

It is the alternative for the Constant CHOP: create a Constant CHOP with the alternatives shortcut held and ConstantCHOP is offered in its place. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Input and outputs

- **in1** (CHOP): optional; the channels Snap Input copies from.
- **out1** (CHOP): the numeric constants as channels.
- **out2** (DAT): every constant as a table of names and values.
