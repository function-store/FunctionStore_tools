---
package: TopToMidi
summary: 'Samples an image at points you define and turns the pixel values into MIDI notes in a musical scale: index or value mapping, trigger gating and retrigger control, custom and MIDI-learned scales, output to a MIDI Out or Audio VST CHOP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Setup
    anchor: setup
  - name: Inputs and outputs
    anchor: inputs-and-outputs
  - name: Processing while idle
    anchor: processing-while-idle
---

## What it is

TopToMidi plays your visuals. A sampler (a SOP's points, or a TOP's pixels) says where the input image is read; each sample point becomes a note. In Index mode a point triggers its own note whenever its pixel passes the threshold, so a pattern sweeping across the picture plays an arpeggio. In Value mode the pixel's brightness picks the note, quantised to Steps. The notes are mapped into a scale from a root note and octave, with custom scales you type in, or a scale learned live from a MIDI keyboard so you can duet with the picture. Trigger gating keeps busy scenes from spraying notes.

The notes go out to a MIDI Out CHOP, an Audio VST CHOP, or both, and ride out as a CHOP for anything else.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Setup

Every scale except MIDI Scale is computed with the Python package mingus, which TouchDesigner does not bundle. The tool ships its own pip requirements file (the `requirements` DAT inside it) and installs it through TouchDesigner's Python Environment Manager. The Setup page's Status says whether mingus is available. When it is missing:

- With a Python vEnv or Conda environment linked through the Python Environment Manager, press Install mingus. The tool writes `TopToMidi.requirements.txt` beside your .toe and hands it to the environment manager, which installs it into the linked environment in the background; Status reports the result. When the project has an environment context file, the requirements file is also registered in it, so a machine that opens the project with Auto Setup On Startup installs it on its own.
- With no environment, create one in the Python Environment Manager (palette: tdPyEnvManager), then press Install mingus.

Nothing blocks TouchDesigner while this happens, and the tool never installs anything without the pulse.

## Inputs and outputs

- **in2** (TOP): the image to sample.
- **out_viz** (TOP): the sampling points drawn over the input.
- **out_sampled** (TOP) and **out_sampled_CHOP** (CHOP): the sampled values.
- **out_notes** (CHOP): the generated notes.

## Processing while idle

Note processing runs only while a MIDI Out or VST CHOP is configured or the outputs are wired. MIDI learning runs only while a MIDI In CHOP is set. Steps follows the number of sample points while note processing runs.
