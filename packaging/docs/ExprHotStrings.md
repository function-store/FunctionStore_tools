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
Forget `absTime.seconds`, use `#AT`! With `Replace inline` enabled on the component (off by default; without it an abbreviation only expands when it is the *entire* expression) the abbreviations work in-line too, meaning you can type `#AT * 0.2` or even combine them!

> Most of the behaviors below live behind their own toggle on the component, and only `CustomPar Promote Enable` is on by default: `#@op Wrap Enable` gates `#@`, `#! Parent Shortcut Enable` gates `#!`/`#!!`.

There is a special reserved abbreviation, `#@` which will wrap anything valid after it in `op('...')`. So `#@noise1.par.amp` becomes `op('noise1').par.amp` saving you some heavy keystrokes!

Another special abbreviation `#!` will resolve to the closest parent shortcut, as well as `#!!` will also add a .par after it!

   - #!.par.Something -> parent.Project.par.Something (for example)
   - #!!Something -> parent.Project.par.Something (for example)
   - Encouraging even more to use parent shortcuts (which you can easily add by `ctrl+shift-clicking` on the diamond button

Two more abbreviations promote the parameter you're typing in straight to its parent (via [CustomParTools](/docs/custompartools/#custompar-tools), if installed) and replace themselves with the resulting shortcut path:
   - `#@!` promotes with a **Bind** reference
   - `#@~` promotes with an **Expression** reference
   - Leave off a name to reuse the parameter's own name, or supply one, e.g. `#@!MyName`

> **IMPORTANT**: due to what's available through the TD API, you need to have your mouse over the parameter box when finishing typing (either by clicking away, in which case you need to move the mouse over to the parameter again, or my suggested way of hitting `Enter`).
