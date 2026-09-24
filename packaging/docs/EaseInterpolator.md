---
package: EaseInterpolator
summary: 'Crossfades between two CHOPs through an easing curve: thirty classic easings from sine to bounce, or a custom curve from a third input, all driven by one Select value.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

EaseInterpolator blends every channel of one CHOP into the matching channel of another, and the blend follows an easing curve instead of a straight line. Select runs from 0, all of the first input, to 1, all of the second. Pick Linear for a plain crossfade, or one of the sine, quad, cubic, quart, quint, expo, circ, back, elastic and bounce curves in their In, Out and In-Out forms. Custom Ease reads the curve from a third input, so any shape you can draw in a CHOP becomes the transition.

Drive Select from a timer, a slider or an LFO and two presets become a move with character: a camera that settles, a value that overshoots and springs back.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (CHOP): the channels at Select 0.
- **in2** (CHOP): the channels at Select 1.
- **in_custom_ease** (CHOP): optional; the curve used when Easing is Custom Ease.
- **out1** (CHOP): the eased blend of the two inputs.
