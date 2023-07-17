# FunctionStore_tools

*by Daniel Molnar ([Function Store](https://linktr.ee/function.str) @function.str)* **Join my Discord**

---

This is a collection of **TouchDesigner** hacks and tools that can help you improve workflow as well as manipulate the default behavior of TD.
For example, with these tools you will be able to place operators with your preferred default parameters, operator chains, or even full render networks with one click; as well as swap operators, and more. 

The design principle of these tools is to be seamlessly integrated with the user experience of TD, meaning the learning curve and adaptibility of these tools should be easy for any level of TD users.

One main improvement area can be found at the bookmark toolbar. Upon installing additional icons will appear in the UI, giving you easy access to some of the main functions. However there are tools that work in the background and are accessible with simple shortcuts. 

Everything is documented here, so be sure to refer to this document and in general to my [TD Tips & Tricks & Hacks]() blog post. If something is still not clear write an issue here on github, or write me an e-mail or on discord.

Most of the tools are made by Function Store, with notable contributions from `AlphaMoonbase.berlin` and `Yea Chen`.  

While this tool is here for all the community to enjoy, I've spent countless hours on them so subscriptions and donations are welcome to keep the efforts alive!

## Installation

- Minimum TD version of the tool: TouchDesigner.2022.33910 (no guaranteess with older versions)
- Download the latest release `FunctionStore_tools.tox` from the releases sidebar
- Open a new project file
- Drag and drop the downloaded `.tox` to the root (`/`) level of your network
- Save the project file and set it as default startup file in `Preferences->General->Startup File Mode/Custom Startup File`
- Or just drag and drop the `.tox` to an existing project file's root level
- There might be errors shown initially but upon right clicking on the component and clicking `Clear (Children) Script Errors` they should be gone

---

## Table of Contents

- [OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates)
    - [Template Definiton](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#template-definiton)
      - [Template Snippets](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#template-snippets)
    - [Templates Usage](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#templates-usage)
    - [Maintaining OpTemplates](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#maintaining-optemplates)
    - [Known issues](https://github.com/function-store/FunctionStore_tools/wiki/01.-OpTemplates#known-issues)

- [FNS_Toolbar](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar)
    - [tools_ui](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#tools_ui)
    - [op_store](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#op_store)
    - [GlobalOutSelect](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#globaloutselect)
      - [Known Issues](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#known-issues)
    - [ExprHotStrings](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#exprhotstrings)
    - [midiMapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#midimapper)
    - [oscMapper](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#oscmapper)
    - [Olib Browser](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#olib-browser)
    - [Open Templates](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#open-templates)
    - [Perform Window Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#perform-window-tools)
    - [Global Mouse CHOP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#global-mouse-chop)
    - [Global ResetPLS](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#global-resetpls)
      - [Conf](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#conf)
      - [TOP, CHOP, SOP, COMP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#top-chop-sop-comp)
      - [Misc](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#misc)
    - [Swap OPs WIP!](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#swap-ops-wip)
    - [Show/Hide Backdrops](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#showhide-backdrops)
    - [Show/Hide Network Editor Grid](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#showhide-network-editor-grid)
    - [Set Input/Viewer Smoothness](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#set-inputviewer-smoothness)
    - [Global Hog CHOP](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#global-hog-chop)
    - [Mute and Volume](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#mute-and-volume)
    - [CustomPar Tools](https://github.com/function-store/FunctionStore_tools/wiki/02.-FNS_Toolbar#custompar-tools)

- [Miscellaneous](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous)
    - [Hotkeys](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#hotkeys)
    - [TD_SearchPalette](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#td_searchpalette)
    - [AltSelect](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#altselect)
    - [AutoCombine](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#autocombine)
    - [AutoRes](https://github.com/function-store/FunctionStore_tools/wiki/03.-Miscellaneous#autores)

---

## Acknowledgements

**AlphaMoonbase.berlin** with `Olib Browser`, `op_store`, `midiMapper`, `oscMapper` and lots of best practices I've learned from his components.

**Yea Chen** for the ever useful TD_SearchPalette.

**Acrylicode** and **kim0slice** for the early feedback and testing.

# License

Copyright 2023 Daniel Molnar / Function Store

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

