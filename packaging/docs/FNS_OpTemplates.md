---
package: FNS_OpTemplates
summary: Start with this feature as this is probably the most "innovative" and exciting addition to TD.
features:
  - name: OpTemplates
    anchor: optemplates
  - name: Open Templates
    anchor: open-templates
    icon: OpTemplates.png
---

## OpTemplates

Start with this feature as this is probably the most "innovative" and exciting addition to TD. 
This component lets you define default operator states (`templates`) which you may want to use instead of the factory ones, and is found under `FNSTools/OpTemplates` (or in the **Toolbar**)

### Defining a Template

For single operators, just drag and drop the operator with the desired parameter settings onto the icon in the toolbar.

**Saving your templates is done by middle-clicking on the icon.**

Otherwise, in case of OP chains, or snippets:
1. Right-click an operator in the `OP Create Dialog` and click `Edit Templates...`. <br>**Alternatively**, you can manually create a **Base COMP** naming it the desired `OPType` attribute. E.g. for creating one for Trigger CHOP you would name it `triggerCHOP`
1. Place your template operators of the same `OPType` inside this **Base COMP**.
1. *You can also drag-and-drop a single operator to the ![](/docs/assets/icons/OpTemplates.png) icon in the toolbar!*
1. *You can define multiple templates for the same operator type!*
1. *The name of the operator will show up in a menu when choosing from multiple to put down, so name away!*
1. *You can chain additional operators after the template operator!*
1. *You can also define whole Snippets (see next chapter)!*
1. **It is strongly suggested that you bypass / disable cooking of template definitions to avoid performance issues or errors.**

##### Template Snippets

You can define OP snippets for an operator type which will behave the same way as other templates:
1. Create a **Base COMP** inside the Base COMP named after the `OPType` described above.
1. You can create any network inside this Base COMP that will be extracted when placing down a template, allowing you e.g. to summon a full render network with geo, camera, light (and whatever you want) instead of placing down only the Render TOP.
1. Inside this Base COMP you can add another Base COMP, which is the way to substitute an operator with a COMP if your heart desires!
1. In case of adding or inserting a template snippet between two OPs, you can help the script figure out the input and output node, by adding an In/Out OP to your snippet Base COMP. Otherwise it will have to guess and it might be wrong.

### Templates Usage

Creating an operator anywhere in your network using the `OP Create Dialog`, you will see a `>>>` mark show next to the operator type that you defined templates for.

1. Click the operator to start placing it.
2. Hold `Ctrl+Alt` (or `Ctrl+Cmd` on Mac) when actually placing it in your network.
3. If there is only one template defined for the given OP type it will be replaced with the template automatically.
4. If there are multiple defined, you will see a menu pop up to choose which one you want to use (the name of the OP/COMP, followed by `(OpTemplates)`), and is then replaced.

#### Since 3.1: templates are op alternatives

Placing a template is now done by [OpMenuRegistry](/docs/fns-opmenuregistry/#what-tools-contribute),
which watches for new operators, holds the shortcut and does the swap for every
tool that declares an alternative for an operator type. OpTemplates publishes
its library to it. What that means for you:

- **The shortcut lives on the registry.** It is the `Alternatives Shortcut` on
  `FNS_OpMenuRegistry`'s Alternatives page (`Ctrl+Alt`, or `Ctrl+Cmd` on Mac).
  OpTemplates' own `Keys` parameter now mirrors that value and is read-only. If
  you had changed `Keys` before upgrading, your shortcut was carried onto the
  registry the first time the new version started, so it keeps working.
- **Other tools can appear in the same menu.** A tool that offers itself for
  the operator type you are placing is listed beside your templates, and a tool
  you downloaded to your store without installing is listed below a divider. A
  `>>` mark beside a type (instead of `>>>`) means its only alternatives are in
  the store.
- **Both packages are needed.** OpTemplates 3.1 places nothing under an older
  OpMenuRegistry, because the watcher moved out of OpTemplates. OpMenuRegistry
  is a core package, so a normal install or update has both.
- **Your libraries are untouched.** The external `.tox` files in your Palette
  folder, `Edit Templates...` and the four commands all work as before. Where
  a library lives is now the `Library Scope` setting, see Maintaining
  OpTemplates below.

You can simply place the templates, or insert them between connections, which also works with templates of OP chains and templates contained on Base COMPs. 

In case of adding or inserting a template Snippet between two OPs, you can help the script figure out the input and output node, by adding an In/Out OP to your snippet Base COMP. Otherwise it will have to guess and it might be wrong.

If those are not present, or simply inserting an OP Chain, assumptions are made: 
- The operator with the same type and no inputs is taken as the first input of the chain 
- The operator at the end of the chain is taken as the last output of the chain. 
- If there are multiple parallel "dead-end" operators it's more or less random what is chosen to be the output of the chain. This should not affect the majority of use-cases.

### Maintaining OpTemplates

One library is active at a time, and `Library Scope` says where it lives:

- **Global** (the historical default): one `.tox` in your **User Palette** folder (`FNStools_ext/OpTemplates/`), shared by every project on this machine. Saving writes that file.
- **Project**: a component named `OpTemplatesLibrary` at the network root, next to the FNSTools container. It saves with the project file and stays through toolkit updates, because it lives outside the tool.
- **Follow config scope** (the default): global or project, whatever the toolkit's `Config Scope` setting says, so a project-scoped install keeps its templates in the project without a second decision.

A library that does not exist yet is created from the set that is loaded at that moment. The templates that ship with the tool are only that starting point. Switching scope never overwrites anything by itself: it loads what is there, or creates it. Switching from project to global when both a project library and a global file exist asks what to do with the project set: push it to the global file, adopt the global set as it is, or stay on project. `Push To Global` does the same push on demand, asking first when the file exists.

> **IMPORTANT:** Under global scope, **Save** the templates by `Middle-Clicking` on the toolbar icon, or clicking `Save Templates` in the Custom Pars (which you can open by `Right-Clicking` on the toolbar icon). Under project scope, saving the project saves the templates.

The `Templates` parameter shows the library the scope resolved to and is read-only. The former `Advanced` mode, where you pointed the tool at any Base COMP in the project, is retired; a component it pointed at is adopted as the project library on the first start after upgrading.

#### TD2023 Migration

Since workfiles saved in TD2023 cannot be opened in earlier versions, template .toxes are created separately with `_2023` appended to them, and they are only synced to TD2023 project files.

To migrate your current default templates to 2023 on Windows navigate to `%USERPROFILE%\Documents\Derivative\Palette\FNSTools_ext\OpTemplates` and make a copy of `OpTemplates1.tox` and rename it `OpTemplates1_2023.tox`, then restart your project file. The steps are the same for Mac, just locate your `Palette` folder!

##### Known issues

- Creating an OP by typing the operator type fully and hitting enter will **not** give the opportunity to place a template instead.
- Relative operator references in parameters can be broken due to naming conflicts.
- Template libraries saved by versions before 3.1 may carry `TEMPLATE_ROOT`, `TEMPLATE_IN` or `TEMPLATE_OUT` tags on their operators, left behind by earlier placements. They are harmless and are cleaned off as those templates get placed again.

## Open Templates

Opens a floating window of the current `Templates` container of the `OpTemplates` component. **Right-Click** to open custom parameters, **Middle-Click** to save.
