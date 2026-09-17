---
package: FNS_RandomCHOP
summary: 'A random-value CHOP: uniform or normal distributions, unique re-rolls with a tolerance and history, a Markov chain mode, weights and a trigger from inputs, generated per channel or per sample.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and output
    anchor: inputs-and-output
  - name: Parameters
    anchor: parameters
---

## What it is

Random is a CHOP that rolls new values when you ask for them. Pulse Generate, or wire a trigger into its first input, and every channel (or every sample) gets a fresh value from the distribution you chose: uniform inside a range, or normal around a mean with spread, skew and kurtosis. Unique mode refuses a value too close to the last N, so a run of rolls never repeats itself; Markov Chain mode makes each roll depend on the previous one, with a reset.

It is the first member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node. It is also the alternative for the Noise CHOP: create a Noise CHOP with the alternatives shortcut held and Random is offered in its place.

## Inputs and output

- **in_trigger** (CHOP): a rising value rolls new values, the same as pulsing Generate.
- **in_weights** (CHOP): weights for the roll, one channel per candidate, when the mode uses them.
- **out1** (CHOP): the rolled values, `Samples` samples of `Channel Name`.

## Parameters

### Random

- **Samples** (Int): how many samples the output holds.
- **Channel Name** (Str): the output channel name.
- **Per Channel / Per Sample** (Toggle): roll one value per channel, or one per sample.
- **Int / Float** (Toggle): integers or floats.
- **Seed** (Float): the seed of the generator; the same seed gives the same run.
- **Uniform Dist** (Toggle) and **Range**: every value inside the range is equally likely.
- **Unique** (Toggle), **Tolerance**, **Prev N Check**: a new value must differ by more than the tolerance from each of the last N values.
- **Normal Dist** (Toggle), **Use Range**, **Range**, **Mean**, **Spread**, **Skew**, **Kurtosis**: a normal distribution, clamped to the range when Use Range is on.
- **Markov Chain** (Toggle) and **Reset Chain** (Pulse): each roll depends on the previous one; reset starts the chain over.
- **Generate** (Pulse): roll now.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
