---
package: paste_from_clipboard
summary: Copy an image to your clipboard and paste it directly in TD with alt+v shortcut
features:
  - name: Clipboard Image Paste
    anchor: clipboard-image-paste
platforms:
  - windows
credit:
  name: DotSimulate
  url: 'https://www.patreon.com/dotsimulate'
---

## Clipboard Image Paste

> Windows only! Implemented by [Dotsimulate](https://www.patreon.com/c/dotsimulate), integrated by Function Store

Copy an image to your clipboard and paste it directly in TD with `alt+v` shortcut  
   - You will be met with three options (hotkeys **1,2,3**): 🟢 Paste as **Movie File In**, 🔵 Paste as **locked Script TOP**, 🟠 Paste as **Annotate**  
   - When pasting as Movie File, the image also gets saved in the folder specified by toolkit settings (default: `Assets/clipboard_images`) 📂  
   - The other two options will produce a locked TOP which increases your `.toe` file size but avoids external dependencies  
   - ❗ **WINDOWS ONLY** — if anyone knows of a native Mac solution (not using external Python libs), let us know!  
