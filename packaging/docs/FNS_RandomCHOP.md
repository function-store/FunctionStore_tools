---
package: FNS_RandomCHOP
summary: 'A random-value CHOP: uniform or normal distributions, unique re-rolls with a tolerance and history, a Markov chain mode, weights and a trigger from inputs, generated per channel or per sample.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
---

## What it is

Random is a CHOP that rolls new values when you ask for them. Pulse Generate, or wire a trigger into its first input, and every channel (or every sample) gets a fresh value from the distribution you chose: uniform inside a range, or normal around a mean with spread, skew and kurtosis. Unique mode refuses a value too close to the last N, so a run of rolls never repeats itself; Markov Chain mode makes each roll depend on the previous one, with a reset.

It is the first member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node. It is also the alternative for the Noise CHOP: create a Noise CHOP with the alternatives shortcut held and Random is offered in its place.

## Inputs and output

- **in_trigger** (CHOP): a rising value rolls new values, the same as pulsing Generate.
- **in_weights** (CHOP): weights for the roll, one channel per candidate, when the mode uses them.
- **out1** (CHOP): the rolled values, `Samples` samples of `Channel Name`.
