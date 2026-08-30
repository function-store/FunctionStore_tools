---
package: VSCodeTools
summary: Youtube Breakdown
features:
  - name: VSCode Tools
    anchor: vscode-tools
    icon: VSCodeTools.png
---

## VSCode Tools

[Youtube Breakdown](https://youtu.be/aZtraQ2N4Oc)

VSCodeTools helps creating/opening/managing VSCode workspaces and synced (externalized) scripts or tables. The file extension is detected from the DAT's declared language or content (`.py, .vert, .frag, .tsv`, plus `.json, .yaml, .xml, .html` and others).
The only requirement is code.exe set up as the default text editor in TD Preferences.

The component is a button with the following interactions (and more, check the parameters below to get a full picture of what it does!!!)

* **LeftClick**: Open VSCode workspace (if set up, see below)
* **RightClick**: Set up VSCode workspace
* **Shift+LeftClick**: Sync to file selected script
* **Alt+LeftClick**: Clear Sync of selected
* **Ctrl+Shift+Alt+LeftClick**: Force sync to file dialog

The component's own controls are listed under **Parameters** below, straight
from the tool itself. What follows is the reasoning the parameter tooltips do
not have room for.

### Sync settings

> If a to-be-synced script is an Extension script the default folder will include a subfolder with the parent's name (the extension belongs to)

You can also use `Ctrl+Shift+Alt+E` to force the rename dialog and save to
another path or under another name.

### Clearing a sync before you ship

> If you ship your project file with synced files in your project, but without supplying the files, you will have a bad time.

The **Clear** page is how you avoid that: it drops the sync and this tool's
tags so the content lives in the `.toe` again, at whatever scope you pick.

### Stubs

This is an integration of [AlphaMoonbaseBerlin's](https://github.com/AlphaMoonbaseBerlin) [Stubser](https://olib.amb-service.net/component/stubser) and [typings](https://github.com/AlphaMoonbaseBerlin/Python_TouchdesignerStubsFromWiki) <3

Python typing stubs can be deployed for selected DATs and COMPs containing extensions as well as built-in TD python typings.

<!-- TODO: screenshot lost (expired GitHub JWT, ~Jul 2024) -- re-capture and add here. -->

The **Stubs** page deploys them: for your own extensions, and for
TouchDesigner's own built-in typings.
