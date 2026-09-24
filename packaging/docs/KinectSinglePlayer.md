---
package: KinectSinglePlayer
summary: 'Picks one player out of a Kinect skeleton stream: whoever stands inside the bounds you set becomes the active player, and their joints ride out as clean channels until they leave.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Outputs
    anchor: outputs
  - name: Parameters
    anchor: parameters
---

## What it is

A Kinect CHOP reports every body it sees, and an installation usually wants exactly one. KinectSinglePlayer watches a chosen joint of every tracked player, keeps the players whose joint sits inside a box you define, and promotes one of them to the active player. That player's channels come out under a stable name, so the rest of the network never has to know which of the six Kinect slots they occupy. When they walk out of the box the next one in range takes over.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Outputs

- **OUT_ACTIVE** (CHOP): whether a player is active right now.
- **OUT_SINGLE_PLAYER** (CHOP): the active player's joints.

## Parameters

### Custom

- **Kinect Data** (CHOP): the Kinect CHOP (or a Null after it) with all players' joints, channels named `p1/head:tx` and so on. Empty by default. Only the joint channels of the tracked player pass through; colour-space and status channels are dropped.
- **Joint** (Str): the joint whose position is tested against the bounds, matched as a whole name (`spine` does not match `spine_mid`); for example `head` or `spine`.
- **Bound X / Y / Z** (Float, two values each): the box a player has to stand in, in metres in Kinect space. Z is the distance in front of the sensor and is always positive; the defaults are X -0.5 to 0.5, Y -1 to 1, Z 1 to 2.5.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
