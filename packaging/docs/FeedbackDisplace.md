---
package: FeedbackDisplace
summary: 'A feedback loop with a displace stage inside it: opacity, crossfade, filter size, displacement driven by a built-in noise or a second input, a per-pass transform, reset and a dry/wet mix. The alternative for the Feedback TOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

A Feedback TOP on its own gives you the loop and nothing else; the rest is always the same handful of operators around it. FeedbackDisplace is that handful in one node: the loop, a composite with an opacity, a blur, a displace stage that warps every pass by an animated noise or by whatever you wire into the second input, a transform applied per pass for drift, zoom and spin, a reset, and a dry/wet mix against the input. Trails, smears, liquid echoes and infinite zooms come from the parameters instead of from rebuilding the chain.

It is the alternative for the Feedback TOP: create a Feedback TOP with the alternatives shortcut held and FeedbackDisplace is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and output

- **in1** (TOP): the image fed into the loop.
- **in_displace** (TOP): optional; a displacement map that replaces the built-in noise.
- **out1** (TOP): the loop's output, mixed with the input by Dry / Wet Mix.
