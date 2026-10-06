---
package: KinectSinglePlayer
summary: 'Picks one player out of a Kinect skeleton stream: whoever stands inside the bounds you set becomes the active player, and their joints ride out as clean channels until they leave.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Outputs
    anchor: outputs
---

## What it is

A Kinect CHOP reports every body it sees, and an installation usually wants exactly one. KinectSinglePlayer watches a chosen joint of every tracked player, keeps the players whose joint sits inside a box you define, and promotes one of them to the active player. That player's channels come out under a stable name, so the rest of the network never has to know which of the six Kinect slots they occupy. When they walk out of the box the next one in range takes over.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Outputs

- **OUT_ACTIVE** (CHOP): whether a player is active right now.
- **OUT_SINGLE_PLAYER** (CHOP): the active player's joints.
