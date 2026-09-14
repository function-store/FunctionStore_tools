---
package: FNS_OpToClipboard
summary: 'Pressing Ctrl(Cmd)+Shift+C will copy the currently selected OP name to the clipboard, so you can easily paste OP references to expressions.'
features:
  - name: OpToClipboard
    anchor: optoclipboard
---

## OpToClipboard

Pressing `Ctrl(Cmd)+Shift+C` will copy the currently selected OP name to the clipboard, so you can easily paste OP references to expressions.

This works relative from any OP to any parameter expression with a small caveat:

Since there's no telling from TD API where the pasting is happening, the pasted text will have an `@` identifier after it, that will automatically resolve to the full relative/shortcut path to the copied OP reference. The base mechanism is the same as [ExprHotStrings](/docs/fns-exprhotstrings/#exprhotstrings) in the end. 

Long story short, just ignore the `@` that is pasted after and keep typing your expression. It should in the end resolve.

### Copying a parameter reference

Press the same shortcut while the mouse is over a parameter to copy a reference to that parameter instead of the operator. Over a single field, such as `tx`, you get `op('geo1')@.par.tx`. Over the name of a parameter row with several fields, such as Translate, you get the whole group: `op('geo1')@.parGroup.t`.

The `@` resolves the same way as for an operator, and the `.par` or `.parGroup` part stays behind it, so the finished expression reads `op('geo1').par.tx` (with the path adjusted to wherever the expression lives).
