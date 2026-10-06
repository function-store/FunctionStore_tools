---
package: QuickMarks
summary: Save up to ten spots in your project and jump straight back to them with Ctrl+number.
features:
  - name: QuickMarks
    anchor: quickmarks
---

## QuickMarks

Ten numbered bookmarks for places in your project. Park one on the network you
keep coming back to and you are one keystroke away from it, from anywhere.

- **Save** a mark: `Ctrl+Alt+{number}` (`Ctrl+Option+{number}` on macOS)
- **Recall** it: `Ctrl+{number}`
- **Remove** it: `Ctrl+Alt+Shift+{number}` (`Option` instead of `Alt` on macOS)

`{number}` is `0` through `9`, so there are ten slots.

> **QuickMarks ships turned off.** Its **Active** parameter defaults to *off*, so
> the number keys do nothing until you switch it on. The shortcuts overlap keys
> a lot of people already use, so the tool leaves that decision to you.

The marks are stored on the component itself, which means they are saved **in
your project file** and are waiting for you the next time you open it. They are
per-project by design: a mark points at a network path, and the same path means
something different in a different `.toe`. Turning **Active** off later hides the
shortcuts and keeps the marks; nothing is thrown away.
