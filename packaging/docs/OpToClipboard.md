---
package: OpToClipboard
summary: 'Pressing Ctrl(Cmd)+Shift+C will copy the currently selected OP name to the clipboard, so you can easily paste OP references to expressions.'
features:
  - name: OpToClipboard
    anchor: optoclipboard
---

## OpToClipboard

Pressing `Ctrl(Cmd)+Shift+C` will copy the currently selected OP name to the clipboard, so you can easily paste OP references to expressions.

This works relative from any OP to any parameter expression with a small caveat:

Since there's no telling from TD API where the pasting is happening, the pasted text will have an `@` identifier after it, that will automatically resolve to the full relative/shortcut path to the copied OP reference. The base mechanism is the same as [ExprHotSprings](/docs/exprhotstrings/#exprhotstrings) in the end. 

Long story short, just ignore the `@` that is pasted after and keep typing your expression. It should in the end resolve.
