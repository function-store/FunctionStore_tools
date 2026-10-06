---
package: FNS_AutoCombine
summary: Hold Alt while placing a generator TOP to set its combine, operation and format defaults.
features:
  - name: AutoCombine
    anchor: autocombine
  - name: Only the operator you dropped
    anchor: only-the-operator-you-dropped
---

## AutoCombine

When holding `Alt` (same for Mac) and placing a **Generator** type TOP (e.g. noise, circle, rectangle) this component sets the default `Combine with Input`, `Operation`, `Pixel Format` as well as `RGB` (in case of Noise) parameters. The defaults can be set at the component parameters.

## Only the operator you dropped

AutoCombine acts on the operator that just appeared in the network you are looking at, and on nothing else. Operators that surface deeper down (a package reloading, a replicator, a component loading its contents) are not drops and are left alone, and a batch too large to be a drop is skipped with a note in the Textport. Earlier versions could catch up on such a backlog at your next Alt-drop and rewrite every TOP with inputs in it.
