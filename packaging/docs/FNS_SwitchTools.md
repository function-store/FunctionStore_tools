---
package: FNS_SwitchTools
summary: 'A companion for any Switch, Cross or multi-input operator: index by slider, menu or bind, loop or clamp, colour the live input, cook only the inputs in use and unload the rest, plus reorder, reverse, randomize and align.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Parameters
    anchor: parameters
  - name: Callbacks
    anchor: callbacks
---

## What it is

Drop SwitchTools next to a Switch TOP, Switch CHOP, Cross CHOP, Switch POP or any multi-input operator and point Switch Op at it (or dock it): the tool binds the operator's index to its own Index, so a slider, a menu, a CHOP or a bound parameter drives the switch, looping or clamping at the ends. Every input the switch is not showing stops cooking and, if you ask, unloads from the GPU, so a scene wall of heavy inputs costs only what is on screen. The live input is coloured in the network, and the inputs can be reordered, reversed, randomized or aligned in one click.

## Parameters

### Custom

- **Switch OP** (OP)
- **Bind** (Toggle)
- **Index** (Float)
- **Blend** (Toggle)
- **Loop Type** (Menu)
- **Select** (Menu)
- **Current Select** (Menu)
- **Out Index** (Float)
- **Num Inputs** (Int)
- **Control Cook (COMPs)** (Toggle)
- **Unload GPU** (Toggle): When an input stops being used, release its COMP's CPU/GPU memory a few frames later (cancelled if it is selected again first), paced by Unload Method and Unload Budget.
- **Unload Method** (Menu): How an unused input COMP's memory is released. Progressive uses COMP.progressiveUnload() paced by Unload Budget and covers every node type including POPs. Immediate calls unload() on each unlocked TOP in one frame (the previous behaviour).
- **Unload Budget (ms/frame)** (Float): Milliseconds per frame spent releasing an unused input's memory (COMP.progressiveUnload). Spreads the unload over several frames so a heavy input never hitches the frame it stops being used. 0 unloads everything in a single frame.
- **Colorize** (Toggle)
- **On Color** (RGBA)
- **On Color** (RGBA)
- **On Color** (RGBA)
- **Off Color** (RGBA)
- **Off Color** (RGBA)
- **Off Color** (RGBA)
- **Active** (Toggle)
### Inputs

- **Reverse Inputs** (Pulse)
- **Randomize Inputs** (Pulse)
- **Order to NodeY (swap)** (Pulse)
- **NodeY to Order (reconnect)** (Pulse)
- **^(automatic)^** (Toggle)
- **Re-Digitize Inputs (rename)** (Pulse): Change the digits of the inputs to match the select index
- **^1 based index^** (Toggle)
- **Align Inputs (retoggle)** (Toggle): Re-toggle to re-align
- **Alignment Mode** (Menu)
- **Adjust Offset (X, Y, YGap)** (Float)
- **Adjust Offset (X, Y, YGap)** (Float)
- **Adjust Offset (X, Y, YGap)** (Float)
- **Save as Original** (Pulse)
- **Restore Original** (Pulse)
- **Disconnect All Inputs** (Pulse)
- **First == Last** (Toggle)
### Callbacks

- **Callbacks** (DAT)
- **Create Callbacks** (Pulse)

## Callbacks

Create Callbacks makes a DAT beside the tool with onCookingChange (which inputs started and stopped cooking) and onSelectionChange (which inputs were selected and unselected); the Callbacks parameter points at it.
