---
package: FNS_SwitchTools
summary: 'A companion for any Switch, Cross or multi-input operator: index by slider, menu or bind, loop or clamp, colour the live input, cook only the inputs in use and unload the rest, plus reorder, reverse, randomize and align.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Callbacks
    anchor: callbacks
---

## What it is

Drop SwitchTools next to a Switch TOP, Switch CHOP, Cross CHOP, Switch POP or any multi-input operator and point Switch Op at it (or dock it): the tool binds the operator's index to its own Index, so a slider, a menu, a CHOP or a bound parameter drives the switch, looping or clamping at the ends. Every input the switch is not showing stops cooking and, if you ask, unloads from the GPU, so a scene wall of heavy inputs costs only what is on screen. The live input is coloured in the network, and the inputs can be reordered, reversed, randomized or aligned in one click.

## Callbacks

Create Callbacks makes a DAT beside the tool with onCookingChange (which inputs started and stopped cooking) and onSelectionChange (which inputs were selected and unselected); the Callbacks parameter points at it.
