---
package: FNS_AutoRes
summary: 'When holding Alt (same for Mac) and placing a Generator type TOP this component sets the Output Resolution parameter to ''Parent Panel Size'' if available, otherwise Custom Resolution and the expression'
features:
  - name: AutoRes
    anchor: autores
  - name: Only the operator you dropped
    anchor: only-the-operator-you-dropped
---

## AutoRes

When holding `Alt` (same for Mac) and placing a **Generator** type TOP this component sets the `Output Resolution` parameter to 'Parent Panel Size' if available, otherwise `Custom Resolution` and the expression for the `resolutionw` (and similarly to `resolutionh`): `"tdu.tryExcept(lambda: parent.Project.width, op.AUTO_RES.par.Resolutionw)"`. In a nutshell this means if `parent.Project.width` is defined it will set the resolution to those values, if not it will set the resolution to the value defined by this component's custom parameters. Where available it also sets the `RGB` and `Pixel Format` parameters to this component's defaults.

## Only the operator you dropped

AutoRes acts on the operator that just appeared in the network you are looking at, and on nothing else. Operators that surface deeper down (a package reloading, a replicator, a component loading its contents) are not drops and are left alone, and a batch too large to be a drop is skipped with a note in the Textport. Earlier versions could catch up on such a backlog at your next Alt-drop and rewrite every generator TOP in it.
