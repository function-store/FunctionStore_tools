---
package: ExprHotStrings
summary: YouTube breakdown
features:
  - name: ExprHotStrings
    anchor: exprhotstrings
video: 'https://www.youtube.com/watch?v=j43gZ0MB2xo'
---

## ExprHotStrings

[YouTube breakdown](https://www.youtube.com/watch?v=j43gZ0MB2xo)

Define `Abbreviations` in the first column that when used in a parameter expression will expand to the string defined in the `Expands` column.
Forget `absTime.seconds`, use `#AT`! The abbreviations work in-line too, meaing you can type `#AT * 0.2` or even combine them!

There is a special reserved abbreviation, `#@` which will wrap anything valid after it in `op('...')`. So `#@noise1.par.amp` becomes `op('noise1').par.amp` saving you some heavy keystrokes!

Another special abbreviation `#!` will resolve to the closest parent shortcut, as well as `#!!` will also add a .par after it!

   - #!.par.Something -> parent.Project.par.Something (for example)
   - #!!Something -> parent.Project.par.Something (for example)
   - Encouraging even more to use parent shortcuts (which you can easily add by `ctrl+shift-clicking` on the diamond button

> **IMPORTANT**: due to what's available through the TD API, you need to have your mouse over the parameter box when finishing typing (either by clicking away, in which case you need to move the mouse over to the parameter again, or my suggested way of hitting `Enter`).
