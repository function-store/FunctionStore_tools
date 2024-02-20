# FunctionStore_tools

*by Daniel Molnar ([Function Store](https://functionstore.xyz)). 
**Watch the InSession [stream](https://www.youtube.com/watch?v=hnpC5uh-GTs) with the TouchDesigner team covering the tools in depth!***

**Important: This toolkit has been developed under TD2022, while there is a 2023 variant available in the releases it may have bugs. Please report if you see any, thanks! See [TD2023 Migration guide](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#td2023-migration) for OpTemplates.**

---
![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/main.png)

This is a collection of [**TouchDesigner**](https://derivative.ca) hacks and tools that can help you improve workflow as well as manipulate the default behavior of TD.
For example, with these tools you will be able to place operators with your preferred default parameters, operator chains, or even full render networks with one click; as well as swap operators, and more. 

The design principle of these tools is to be seamlessly integrated with the user experience of TD, meaning the learning curve and adaptibility of these tools should be easy for any level of TD users.

One main improvement area can be found at the bookmark toolbar. Upon installing additional icons will appear in the UI, giving you easy access to some of the main functions. However there are tools that work in the background and are accessible with simple shortcuts. 

Everything is documented here, so be sure to refer to the [Wiki](https://github.com/function-store/FunctionStore_tools/wiki) and in general to my [TD Tips & Tricks & Hacks]() (TBA) blog post. 

Please help by reporting any [issues](https://github.com/function-store/FunctionStore_tools/issues) here on GitHub or use the **Troubleshoot** channel on my [Discord](https://discord.gg/b4CaCP3g3K).

A lot of the tools are made by [Function Store](https://functionstore.xyz), with notable contributions from [AlphaMoonbase.berlin](https://alphamoonbase.de/), [Yea Chen](https://www.instagram.com/yeataro) and [Greg Hermanovic](https://derivative.ca), please support them <3

While these tools are here for all the community to enjoy, [Patreon](https://patreon.com/function_store) follows are appreciated!

## Installation

1. Ensure that you have minimum TouchDesigner.2022.33910 version installed (no guaranteess with older versions)
2. Download the latest release `FunctionStore_tools.tox` from the [releases](https://github.com/function-store/FunctionStore_tools/releases/latest) sidebar
3. Open a new project file
4. Drag and drop the downloaded `.tox` to the root (`/`) level of your network, or drag and drop the `.tox` to an existing project file's root level
6. (Strongly Suggested) Save the project file and set it as default startup file in `Preferences->General->Startup File Mode/Custom Startup File` so that it is used in every project from then on!
7. (Alternative Strong Suggestion) There is a `FNS_TDDefault.toe` file which already has the toolkit inside, feel free to use that as a Custom Startup File!
 
> **Note:** There might be errors shown initially but upon right clicking on the component and clicking `Clear (Children) Script Errors` they should be gone.

## Syncing/Externalizing

There are a couple of components whose states/contents you'll probably want to synchronize between your projects, such as [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates), [ExprHotStrings](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#exprhotstrings), or [Global ResetPLS](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#global-resetpls) exceptions. These are saved into a folder inside your **User Palette**, and can be toggled On or Off.

The state of some other components such as MIDI/OSC Maps get saved into your project folder for easy migration and future-proofing for updates.

These can be turned on or off in the Custom Parameters of the toolkit, which you can also access by right-clicking the (![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Fx.png) button in the toolbar.

## Custom Parameters

At the base level of `FunctionStore_tools.tox` you can find some custom parameters that allow you to customize its functionalities on a broad scale. Should you want further customization, it is possible at the component level of each tool.

> You can easily access these settings by right-clicking the ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Fx.png) button in the toolbar.


### Active tab

In this tab you can choose to disable some of the components, that you might find annoying or unwanted. I only added the ones I personally might want turned off occasionally. I also crammed in `ParPromoter Ref/Bind` which is explained here: [CustomPar Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#custompar-tools)

### Syncing

Turn On or Off Syncing/Externalizing for individual modules **(On by default)**. See [Syncing/Externalizing](https://github.com/function-store/FunctionStore_tools#syncingexternalizing) for more info.

See [TD2023 Migration guide](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#td2023-migration) for OpTemplates.

## Repo Structure

The monolithic `FunctionStore_tools.tox` can be found in [modules/release](https://github.com/function-store/FunctionStore_tools/tree/main/modules/release). This is what you should be using in your project files.

Individual `.tox` files can be found in the [modules/suspects/FunctionStore_tools](https://github.com/function-store/FunctionStore_tools/tree/main/modules/suspects/FunctionStore_tools) folder. Please note that some modules expect the presence of others in order to work, but many of these should work individually also.

There is a `FNS_TDDefault.toe` project file for you to quickly test the tools, or use as a default startup project file.

---

## [Read the Wiki](https://github.com/function-store/FunctionStore_tools/wiki)

- [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/OpTemplates.png)
    - [Template Definiton](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#template-definiton)
      - [Template Snippets](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#template-snippets)
    - [Templates Usage](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#templates-usage)
    - [Maintaining OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#maintaining-optemplates)
    - [Known issues](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#known-issues)

- [FNS_Toolbar](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/main.png)
    - [tools_ui](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-tools_ui) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Fx.png)
      - [op_store](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#op_store) 
      - [GlobalOutSelect](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#globaloutselect)
      - [ExprHotStrings](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#exprhotstrings)
      - [midiMapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#midimapper)
      - [oscMapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#oscmapper)
    - [Olib Browser](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-olib-browser) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Olib.png)
    - [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-open-templates) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/OpTemplates.png)
    - [Perform Window Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-perform-window-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/PerformTools.png)
    - [Global Mouse CHOP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-global-mouse-chop) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/QuickMouse.png)
    - [Global ResetPLS](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-global-resetpls) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/ResetPLS.png)
    - [Swap OPs](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-swap-ops) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/SwapOPs.png)
    - [Toggle Backdrops](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-showhide-backdrops) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/ToggleBackdrop.png)
    - [Toggle Network Editor Grid](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-showhide-network-editor-grid) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Toggle%20Grid.png)
    - [Set Input/Viewer Smoothness](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-set-inputviewer-smoothness) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/Set%20Smoothness.png)
    - [Global Hog CHOP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-global-hog-chop) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/HogCHOP.png)
    - [QuickTime](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-custompar-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/QuickTime.png)
    - [Mute and Volume](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-mute-and-volume) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/GlobalVol.png)
    - [CustomPar Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#-custompar-tools) ![](https://github.com/function-store/FunctionStore_tools/blob/main/icons/CustomParTools.png)

- [Miscellaneous](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous)
    - [Greg's OP Create IO Filter Mod](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#gregs-op-create-io-filter-mod)
    - [ParentHierarchy](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#parenthierarchy)
    - [Hotkeys](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#hotkeys)
    - [TD_SearchPalette](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#td_searchpalette)
    - [AltSelect](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#altselect)
    - [AutoCombine](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#autocombine)
    - [AutoRes](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#autores)
    - [QuickOp](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickop)
    - [QuickPane](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#quickpane)

---

## Acknowledgements

Huge thanks to the contributors:

- [AlphaMoonbase.berlin](https://alphamoonbase.de/) with `Olib Browser`, `op_store`, `midiMapper`, `oscMapper` and lots of best practices I've learned from his components.

- [Yea Chen](https://www.instagram.com/yeataro) for the ever useful TD_SearchPalette.

- [Greg Hermanovic](https://derivative.ca) for the IO filters for the OP Create dialog, and **TouchDesigner**.

- [Acrylicode](https://acrylicode.com/) and [kim0slice](https://www.instagram.com/kim0slice) for the early feedback and testing.

# License

Copyright 2023 Daniel Molnar / Function Store

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
