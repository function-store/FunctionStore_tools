---
package: QuickCollapse
summary: Collapse the selected nodes into a Base COMP with one keystroke.
features:
  - name: QuickCollapse
    anchor: quickcollapse
    hotkeys:
      - keys: Ctrl+W
        does: Collapse the selection into a `Base COMP` straight away
      - keys: Ctrl+Shift+W
        does: Collapse, but ask for the COMP's name and parent shortcut first
---

## QuickCollapse

Select some nodes and press `Ctrl+W`: they move inside a new **Base COMP**,
wired exactly as they were. It runs TouchDesigner's own *Collapse Selected*
underneath, so the result is the operator you would have got from the right-click
menu. This puts it on a key and skips the menu.

The whole thing is one undo step, and undoing it also returns you to the network
you collapsed from, so you are never left inside a COMP that no longer exists.

`Ctrl+Shift+W` does the same thing but asks first, with a small dialog for the new
COMP's **name** and its **parent shortcut**. Worth the extra key whenever the
result is something you will refer to later, because naming it at creation time
is cheaper than renaming it and fixing up references afterwards.

This is the tidying pass that keeps a patch readable: build flat and fast while
you are figuring it out, then sweep a working section into a component once it
has earned a name.
