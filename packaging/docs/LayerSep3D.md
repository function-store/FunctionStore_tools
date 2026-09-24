---
package: LayerSep3D
summary: 'Slices an image into depth layers by a channel threshold and instances them as a stack in 3D: per layer threshold, softness, mix, colour, position, scale and rotation, each driven by a curve or a CHOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Parameters
    anchor: parameters
---

## What it is

LayerSep3D is a Geometry COMP that turns one image into a stack of planes. Each of the Layers slices the input by a threshold on the channel you pick, so the bright parts land on one plane and the dark parts on another, with a soft edge between. The planes are instanced along Z, and every per layer value (threshold, softness, mix, offset, scale, rotation) is a curve over the layer index with an offset, amplitude, power and phase, or a CHOP you wire in. Point a camera at it and a flat picture gets depth.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in_mask** (TOP): the image that is sliced.
- **in_color** (TOP): the colour drawn on the layers, when different from the mask.
- **in_threshold**, **in_softness**, **in_mix** (CHOP): optional per layer curves that override the parameter curves.
- **out_layers** (TOP): the layer stack as a 2D texture array or 3D texture, for your own instancing.

## Parameters

### Custom

- **Layers** (Int): how many slices, at least 2. The range is divided into that many bands, so every layer receives part of the image.
- **Reverse Layer Order** (Toggle): mirror the slice order along Z.
- **Open** (Pulse): open the internal control panel.
- **Mode** (Menu): the channel sliced: Luminance, Red, Green, Blue, Alpha, RGB or RGBA Avg, Max, Min.
- **Threshold** group (Threshold Offset, Amplitude, Range, Power, Phase, and a Threshold CHOP): the per layer threshold curve, or a CHOP that overrides it.
- **Softness** group (Softness Offset, Amplitude, Power, Phase, and a Softness CHOP): the per layer edge softness; edge j between layers j-1 and j uses softness j-1.
- **Mix** group (Mix Amplitude, Offset, Power, Phase, and a Mix CHOP): how much of the colour input each layer shows.
- **Texture Index** group (Invert, Phase, Exponent, Period, Randomize, Single, Select): how the layer index maps to the curves, with a single layer pick.

### Transform

- **Z**, **Scale**, **Rotation** groups (offset, amplitude, power, phase, invert): the per layer instance transform. These can be overridden in the instancing.

### Common

- **Type** (Menu): 2D Texture Array or 3D Texture for the layer output.
- **Instancetexfilter** (Menu): the texture filter used on the instances.

### About

- **Package Version** (Str): the package version the FNS updater compares against the release manifest.
