# FunctionStore_tools

*by Daniel Molnar ([Function Store](https://functionstore.xyz)). 
**Watch the InSession [stream](https://www.youtube.com/watch?v=hnpC5uh-GTs) with the TouchDesigner team covering the tools in depth!***

[![Download TOE](https://img.shields.io/badge/Download_.toe_%E2%86%93-blank?style=for-the-badge)](https://github.com/function-store/FunctionStore_tools/releases/latest/download/FNS_TDDefault_2023.toe) [![Download TOX](https://img.shields.io/badge/Download_.TOX_%E2%86%93-blank?style=for-the-badge)](https://github.com/function-store/FunctionStore_tools/releases/latest/download/FunctionStore_tools_2023.tox)
[![Total Downloads](https://img.shields.io/github/downloads/function-store/FunctionStore_tools/total?style=for-the-badge&label=Total%20Downloads)](https://github.com/function-store/FunctionStore_tools/releases/latest/download/FunctionStore_tools_2023.tox)

---
![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/main.png)

This is a collection of [**TouchDesigner**](https://derivative.ca) hacks and tools that can help you improve workflow as well as manipulate the default behavior of TD.
For example, with these tools you will be able to place operators with your preferred default parameters, operator chains, or even full render networks with one click; as well as swap operators, and more. 

The design principle of these tools is to be seamlessly integrated with the user experience of TD, meaning the learning curve and adaptability of these tools should be easy for any level of TD users.

One main improvement area can be found at the [bookmark toolbar]([url](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar)), the [nav/pathbar]([url](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#navbar-mods)) and the [op create dialog]([url](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#opmenu-mods)). However there are tools that work in the background and are accessible with simple shortcuts. 

Everything is documented here, so be sure to refer to the [Wiki](https://github.com/function-store/FunctionStore_tools/wiki) and in general to my [TD Tips & Tricks & Hacks]() (TBA) blog post. 

Please help by reporting any [issues](https://github.com/function-store/FunctionStore_tools/issues) here on GitHub or use the **Troubleshoot** channel on my [Discord](https://discord.gg/b4CaCP3g3K).

A lot of the tools are made by [Function Store](https://functionstore.xyz), with notable contributions from [AlphaMoonbase.berlin](https://alphamoonbase.de/), [DotSimulate](https://www.patreon.com/c/dotsimulate), [Alex Guevara](https://alex-guevara.com) [Yea Chen](https://www.instagram.com/yeataro) and [Greg Hermanovic](https://derivative.ca), please support them <3

While these tools are here for all the community to enjoy, [Patreon](https://patreon.com/function_store) follows are appreciated!

## Installation

1. Ensure that you have minimum **TouchDesigner.2023.11880** version installed (no guaranteess with older versions)
2. Download the latest release `FunctionStore_tools_2023.tox` from the [releases](https://github.com/function-store/FunctionStore_tools/releases/latest) sidebar
3. Open a new project file
4. Drag and drop the downloaded `.tox` to the root (`/`) level of your network, or drag and drop the `.tox` to an existing project file's root level
6. (Strongly Suggested) Save the project file and set it as default startup file in `Preferences->General->Startup File Mode/Custom Startup File` so that it is used in every project from then on!
7. (Alternative Strong Suggestion) There is a `FNS_TDDefault_2023.toe` file which already has the toolkit inside, feel free to use that as a Custom Startup File!
8. Bonus: `Alt-RightClick` (or `Alt-MiddleClick`) on any of the newly added toolbar icons to open the relevant wiki in a browser! (`Option-Right/MiddleClick` for Mac users)
 
> **Note:** There might be errors shown initially but upon right clicking on the component and clicking `Clear (Children) Script Errors` they should be gone, or they can be ignored.

## Mac Compatibility

While 99% of the features work identically for Mac, users should pay attention to the following:
- Olib Browser does not work on Mac
- It is very hard to stay consisten with hotkeys on Mac ,so **When referring to hotkeys in the Wiki `Alt` refers to `Cmd`**
    - With a lot of exceptions, but those will be clearly documented. Let me know if something is missing!

## Self-Update Feature

If the toolkit (v2.4.0+) is installed in your project and there is an update, the `?` icon in the toolbar will have a yellow border. Clicking the icon will prompt you for an update, you can say `No` in which case it will take you to the Wiki as usual, otherwise the following is going to happen:
- Save all configs (custom parameters of tools) to a `json` file
- Download the new version of the toolkit `.tox` into the user palette, and replace the existing one with it
- Load all the saved configs from the previously saved `json` file

This way we can ensure that your settings are retained between updates, alongside the externally retained data, outlined in the next chapter.

## Syncing/Externalizing

There are a couple of components whose states/contents you'll probably want to synchronize between your projects, such as [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates), [ExprHotStrings](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#exprhotstrings), or [Global ResetPLS](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#global-resetpls) exceptions. These are saved into a folder inside your **User Palette**, and can be toggled On or Off.

The state of some other components such as MIDI/OSC Maps get saved into your project folder for easy migration and future-proofing for updates.

These can be turned on or off in the Custom Parameters of the toolkit, which you can also access by right-clicking the (![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Fx.png) button in the toolbar.

The general settings of the tools (the **Custom Parameters**) can also be saved and synced between projects with the `Save/Load All Configs To/From JSON` buttons. You need to explicitly hit save whenever you make some significant change you'll want to synchronize to other projects, however there is a toggle for `Auto-Load`ing the configs after startup. This `json` file is also used for the **Self-Update Feature** in which case the settings are saved and re-loaded automatically.

## Custom Parameters

At the base level of `FunctionStore_tools.tox` you can find some custom parameters that allow you to customize its main functionalities on a broad scale. 

Should you want further customization, it is possible at the component level of each tool, feel free to dive in and customize each!

> You can easily access these main settings by right-clicking the ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Fx.png) button in the toolbar.


### Active tab

In this tab you can choose to disable some of the components, that you might find annoying or unwanted. Some other setting are also crammed in there.

### Syncing

Turn On or Off Syncing/Externalizing for individual modules **(On by default)**. See [Syncing/Externalizing](https://github.com/function-store/FunctionStore_tools#syncingexternalizing) for more info.

See [TD2023 Migration guide](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#td2023-migration) for OpTemplates.

### UI

By pulsing `Open Toolbar Definition` you can customize the toolbar settings: enable/disable icons and change their orders. This is saved externally to sync with other project files. Note that this does not disable backend functionalities!
In this tab you can also set the default state of UI related mods such as windows title and timeline state, and UI color.

## Repo Structure

The monolithic `FunctionStore_tools_2023.tox` can be found in [modules/release](https://github.com/function-store/FunctionStore_tools/tree/main/modules/release). This is what you should be using in your project files.

Individual `.tox` files can be found in the [modules/suspects/FunctionStore_tools](https://github.com/function-store/FunctionStore_tools/tree/main/modules/suspects/FunctionStore_tools) folder. Please note that some modules expect the presence of others in order to work, but many of these should work individually also.

There is a `FNS_TDDefault_2023.toe` project file for you to quickly test the tools, or use as a default startup project file!

---

## [Read the Wiki](https://github.com/function-store/FunctionStore_tools/wiki)
`Alt-RightClick` (or `Alt-MiddleClick`) on any of the newly added toolbar icons to open the relevant wiki in a browser! (`Option-Right/MiddleClick` for Mac users)

- [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/OpTemplates.png)
    - [Template Definiton](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#template-definiton)
      - [Template Snippets](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#template-snippets)
    - [Templates Usage](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#templates-usage)
    - [Maintaining OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#maintaining-optemplates)
    - [Known issues](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#known-issues)

- [FNS_Toolbar](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/main.png)
    - [wiki](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-wiki) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Wiki.png)
    - [tools_ui](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-tools_ui) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Fx.png)
      - [op_store](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#op_store) 
      - [GlobalOutSelect](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#globaloutselect)
      - [ExprHotStrings](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#exprhotstrings)
      - [midiMapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#midimapper)
      - [oscMapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#oscmapper)
      - [Custom OpMenu Search Keywords](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#custom-opmenu-search-keywords)
    - [Olib Browser](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-olib-browser) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Olib.png)
    - [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-open-templates) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/OpTemplates.png)
    - [Perform Window Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-perform-window-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/PerformTools.png)
    - [VSCode Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-vscode-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/VSCodeTools.png)
    - [Global ResetPLS](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-global-resetpls) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/ResetPLS.png)
    - [Swap OPs](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-swap-ops) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/SwapOPs.png)
    - [Set Input/Viewer Smoothness](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-set-inputviewer-smoothness) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Set%20Smoothness.png)
    - [ParRandomizer](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-parrandomizer) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Random.png)
    - [Toggle Backdrops](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-showhide-backdrops) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/ToggleBackdrop.png)
    - [Toggle Network Editor Grid](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-showhide-network-editor-grid) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Toggle%20Grid.png)
    - [Global Hog CHOP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-global-hog-chop) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/HogCHOP.png)
    - [Global Mouse CHOP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-global-mouse-chop) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/QuickMouse.png)
    - [QuickTime](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-custompar-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/QuickTime.png)
    - [Mute and Volume](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-mute-and-volume) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/GlobalVol.png)
    - [Mapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-mapper) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Mapper.png)
    - [ParOpDrop](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-paropdrop) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/ParOpDrop.png)
    - [CustomPar Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-custompar-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/CustomParTools.png)

- [Miscellaneous](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous)
    - [OpMenu/OP Create Dialog Mods](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#opmenu-mod)
    - [NavBar Mods](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#navbar-mods)
    - [Hotkeys](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#hotkeys)
    - [TD_SearchPalette](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#td_searchpalette)
    - [AltSelect](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#altselect)
    - [AutoCombine](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#autocombine)
    - [AutoRes](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#autores)
    - [QuickOp](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickop)
    - [QuickPane](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickpane)
    - [SwitchOPs](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#switchops)
    - [OpToClipboard](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#optoclipboard)
    - [OpenExt](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#openext)
    - [QuickCollapse](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickcollapse)  
    - [Clipboard Image Paste](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#clipboard-image-paste)  
    - [QuickMarks](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickmarks)  
    - [CustomParCustomize](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#customparcustomize)  
    - [BorderlessTD](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#borderlesstd)  
    - [ColorUI](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#colorui)  
    - [ResetMIDIPls](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#resetmidipls)
    - [HotkeyManager](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#hotkeymanager)
    - [QuickParCustom](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickparcustom)

- [QuickExt](https://github.com/function-store/FunctionStore_tools/wiki/04.-QuickExt)
    - [CustomParHelper](https://github.com/function-store/FunctionStore_tools/wiki/04.-QuickExt#customparhelper)
    - [NoNode](https://github.com/function-store/FunctionStore_tools/wiki/04.-QuickExt#nonode)

---

## Acknowledgements

Huge thanks to the contributors:

- [AlphaMoonbase.berlin](https://alphamoonbase.de/) with `Olib Browser`, `op_store`, `midiMapper`, `oscMapper` and lots of best practices I've learned from his components.

- [Yea Chen](https://www.instagram.com/yeataro) for the ever useful TD_SearchPalette.

- [Greg Hermanovic](https://derivative.ca) for the IO filters for the OP Create dialog, and **TouchDesigner**.

- [Dotsimulate](https://www.patreon.com/dotsimulate) for Clipboard Image Paste, and OP Create Dialog OpType Acronyms mod
 
- [Alex Guevara](https://alex-guevara.com) for QuickMarks

- [Acrylicode](https://acrylicode.com/) and [kim0slice](https://www.instagram.com/kim0slice) for the early feedback and testing.

## Notable Mentions
Here are some links of mostly free tools/resources:
- [Olib](https://td-olib.org/) by Wieland Hilker (Alphamoonbase.berlin): the de-facto free TD .tox marketplace
- [TD-Launcher](https://github.com/EnviralDesign/TD-Launcher/) by Lucas Morgan: if you're using multiple TD version installs this is a must have

# License

Copyright 2024 Daniel Molnar / Function Store

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
