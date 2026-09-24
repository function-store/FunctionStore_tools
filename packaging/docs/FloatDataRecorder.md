---
package: FloatDataRecorder
summary: 'Records a float texture such as a depth point cloud, a colour texture and a CHOP to files in sync, then plays the three back together against the timeline with a frame offset.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Parameters
    anchor: parameters
---

## What it is

FloatDataRecorder captures a take from a sensor and plays it back later as if the sensor were still there. It records three streams at once: a float texture such as a Kinect or depth camera point cloud, a colour texture, and a CHOP such as skeleton data. Turn Rec on and all three write to files; turn it off and the CHOP is saved to its own file. On the Play side, open the three files and they play in step with the timeline, with an offset in frames to line them up, so you can build and test a whole installation without the hardware plugged in.

The CHOP player stays off until its file exists, so a fresh node shows no error before you have recorded anything.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (TOP): the float texture to record, such as a point cloud.
- **in2** (CHOP): the channels to record.
- **in3** (TOP): the colour texture to record.
- **out_pointcloud** (TOP), **out_color** (TOP): the played-back textures.
- **out2** (CHOP): the played-back channels.

## Parameters

### Record

- **Texture File**, **Color Texture File** (File): the movies the two textures are written to.
- **CHOP File** (File): where the channels are saved when recording stops; a name with no extension gets `.bclip`.
- **Rec** (Toggle): record while on.

### Play

- **Texture File**, **Color Texture File**, **CHOP File** (File): the recordings to play back.
- **Play Offset Frames** (Int): shift the playback against the timeline.
- **Reload** (Pulse): reload the three files, and look again for a CHOP file that was missing.
- **Sync Timeline** (Pulse): set the timeline's length to the recording's.
- **Play** (Toggle): output the recordings. Off, and always while recording, the outputs pass the live inputs through.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
