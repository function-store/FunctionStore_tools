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

### Parameters:

* **Code.exe**: path to code.exe [this may be auto-filled, see Auto-detect]
* **Workspace**: path to VSCode workspace file (with extension .code-workspace) [his may be auto-filled, see Auto-detect] 
* **Auto-detect**: will attempt to auto-fill the Code.exe and Workspace parameters. (on by default)
    * Code.exe will be auto-filled if it is already set up in TD Preferences (Cursor is also detected and used if set as the Preferences text editor)
    * Workspace will be the name of the project file by default 
* **Auto-open**: will open the VSCode workspace when the project starts
* **Open**: opens workspace, if it didn't exist before, a new one is created and opened in the project root folder


_Sync Settings_

* **Script Sync Base Folder**: folder path relative to project root where scripts will be synced
* **Use Ctrl+Shift+E Shortcut**: hitting this shortcut will externalize selected script or table to the base folder, with the name of the operator. If it already exists a dialog pops up to rename.
    * You can also use Ctrl+Shift+Alt+E if you want to force the dialog to save to another path or with another name.
* **Sync File Selected**: same as Ctrl+Shift+E

> If a to-be-synced script is an Extension script the default folder will include a subfolder with the parent's name (the extension belongs to)

_Clear tab:_

> Explanation: if you ship your project file with synced files in your project, but without supplying the files you will have a bad time.

* **Tags**: this is read-only and should not be changed --- these are the tags that are automatically added if syncing/externalizing with this tool, and checked (all of them need to exist in an operator)
* Clear:
    * **selected DATs**: will only clear sync and tags from the selected DATs
    * **in current pane**: will clear sync and tags from current pane (and not any deeper children)
    * **in current pane and all children**: will clear sync and tags from current pane and all children
    * **all in project**: will clear sync and tags from all of the project


_Stubs:_

This is an integration of [AlphaMoonbaseBerlin's](https://github.com/AlphaMoonbaseBerlin) [Stubser](https://olib.amb-service.net/component/stubser) and [typings](https://github.com/AlphaMoonbaseBerlin/Python_TouchdesignerStubsFromWiki) <3

Python typing stubs can be deployed for selected DATs and COMPs containing extensions as well as built-in TD python typings.

<!-- TODO: screenshot lost (expired GitHub JWT, ~Jul 2024) -- re-capture and add here. -->

* **Stubs tags**: Do not touch :)
* **Private**: Whether methods and attributes starting with `_` should be stubbed
* **Unpromoted**: Whether unpromoted (ie. starting with lowercase) methods and attributes should be stubbed
* **Deploy Stubs**: Deploy stubs for selected DATs or COMPs containing extensions
TD Typings
* **Install**: This will deploy built in TD typings
* **Force**: This will install and update built in TD typings even if they existed before
