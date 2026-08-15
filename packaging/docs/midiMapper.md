---
package: midiMapper
summary: Simple MIDI mapping tool by AlphaMoonbase.berlin.
features:
  - name: midiMapper
    anchor: midimapper
  - name: ResetMIDIPls
    anchor: resetmidipls
  - name: Mapper
    anchor: mapper
    icon: Mapper.png
credit:
  name: AlphaMoonbase.berlin
  url: 'https://alphamoonbase.de/'
---

## midiMapper

Simple MIDI mapping tool by AlphaMoonbase.berlin. Drag and drop parameters onto the UI, learn, and move a fader/knob to assign. You can also modify the min/max range.
Right click on the folder tab to configure.

## ResetMIDIPls

Bypass and un-bypass MIDI operators to unstick them (requested by Jacopo)  
   - Built into `midiMapper` and its button on the toolbar  
   - 🎛️ In `midiMapper`, a **new button** resets the selected `Device ID`  
   - 🖱️ **Middle-click** the `midiMapper` toolbar button to reset **all**  
   - Can be set to **auto-reset all on startup**  

If enabled in the `FunctionStore_tools` base custom parameters, the contents of the table will be externalized to the project folder.

## Mapper

Allows quick MIDI/OSC Mapping by **DragDropping** a **Parameter** onto this button, using Galileo [MIDI](/docs/midimapper/#midimapper)/[OSC](/docs/oscmapper/#oscmapper) Mapper. 

* **LeftClick:** MIDI Mapper
* **Alt(/Cmd)+LeftClick:** OSC Mapper
* **Alt(/Cmd)+RightClick:** (OSC)MIDI Mapper Settings
* **DragDrop par:** auto-learn MIDI
* **Alt(/Cmd)+DragDrop par:** auto-learn OSC

**Move knob to auto-learn.**
