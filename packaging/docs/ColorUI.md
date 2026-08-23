---
package: ColorUI
summary: 'ColorUI: Recolor any TouchDesigner UI element, create presets, import/export, and share!'
features:
  - name: ColorUI
    anchor: colorui
  - name: In the console
    anchor: in-the-console
---

## ColorUI

ColorUI: Recolor any TouchDesigner UI element, create presets, import/export, and share!  
   - Available as the **OpColor** tab of [FNS_Hub](/docs/fns-hub/) (the **FNS** button in the main-menu bar)  
   - Includes recoloring **OP Families** (looking at you, POPs)  
   - Or any UI element by choosing from the dropdown  
   - **Saving colors locally** saves them to the component and can be auto-loaded on startup  
   - **Export to JSON**, and **import** — imported settings take precedence over local  

## In the console

ColorUI is also the first tool to contribute a tab to **FNS_Console**, the
toolkit's web front: the same colour UI, served in the browser alongside
Settings and Install & remove. Turn it on with **Expose** on ColorUI's
`Registry` page and open the console (`FNS_Console`, tab *ColorUI*). While the
console serves the page, ColorUI's own in-TD web render switches off so it is
not rendering the same page twice.
