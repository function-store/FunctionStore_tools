---
package: "AutoRes"
summary: "When holding Alt (same for Mac) and placing a Generator type TOP this component sets the Output Resolution parameter to 'Parent Panel Size' if available, otherwise Custom Resolution and the expression"
features:
  - name: "AutoRes"
    anchor: "autores"
---

## AutoRes

When holding `Alt` (same for Mac) and placing a **Generator** type TOP this component sets the `Output Resolution` parameter to 'Parent Panel Size' if available, otherwise `Custom Resolution` and the expression for the `resolutionh` (and similarly to `resolutionw`): `"tdu.tryExcept(lambda: parent.Project.width, op.AUTO_RES.par.Resolutionw)"`. In a nutshell this means if `parent.Project.width` is defined it will set the resolution to those values, if not it will set the resolution to the value defined by this component's custom parameters.
