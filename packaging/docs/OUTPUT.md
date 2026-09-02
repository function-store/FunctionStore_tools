---
package: OUTPUT
summary: Drag and drop an operator to set it as the Window Operator of the /perform Window.
features:
  - name: Perform Window Tools
    anchor: perform-window-tools
    icon: PerformTools.png
---

## Perform Window Tools

Drag and drop an operator onto the toolbar button to make it the **Window
Operator** of the `/perform` Window, with no trip into the Window COMP's
parameters. **Left-click** opens the perform window, and closes it again if it
is open. **Right-click** opens the configuration popup, which also has the
switches for streaming that same window out over **NDI** and **Spout**
(Syphon on macOS); both ship switched on, under the sender names on the
component's parameters.

Which window it drives is the **Perform** parameter of the button itself
(`button_perform`, parent shortcut `Main`). That is what the drop writes
through, so pointing it at another Window COMP takes effect on the next drop
with nothing to re-install.
