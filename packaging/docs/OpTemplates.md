---
package: OpTemplates
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
This component lets you define default operator states (`templates`) which you may want to use instead of the factory ones, and is found under `FunctionStore_tools/OpTemplates` (or in the **Toolbar**)

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
4. If there are multiple defined, you will see a menu pop up to choose which one you want to use (the name of the OP/COMP), and is then replaced.

You can simply place the templates, or insert them between connections, which also works with templates of OP chains and templates contained on Base COMPs. 

In case of adding or inserting a template Snippet between two OPs, you can help the script figure out the input and output node, by adding an In/Out OP to your snippet Base COMP. Otherwise it will have to guess and it might be wrong.

If those are not present, or simply inserting an OP Chain, assumptions are made: 
- The operator with the same type and no inputs is taken as the first input of the chain 
- The operator at the end of the chain is taken as the last output of the chain. 
- If there are multiple parallel "dead-end" operators it's more or less random what is chosen to be the output of the chain. This should not affect the majority of use-cases.

### Maintaining OpTemplates

OpTemplate definitions are by default synced across your projects by externalizing and syncing to the **User Palette** folder. This can be turned off in the OpTemplate settings (`External Templates Sync`).

> **IMPORTANT:** The only thing to make sure of is to **Save** the templates by `Middle-Clicking` on the toolbar icon, or clicking `Save Templates` in the Custom Pars (which you can open by `Right-Clicking` on the toolbar icon).

Turning on `Advanced` will let you create and define a `Templates` Base COMP anywhere in your project. This way you can have different versions of template definitions, defined by the name of the `Templates` Base COMP.

> While the option is there, I suggest keeping `Advanced` **Off**.

#### TD2023 Migration

Since workfiles saved in TD2023 cannot be opened in earlier versions, template .toxes are created separately with `_2023` appended to them, and they are only synced to TD2023 project files.

To migrate your current default templates to 2023 on Windows navigate to `%USERPROFILE%\Documents\Derivative\Palette\FNSTools_ext\OpTemplates` and make a copy of `OpTemplates1.tox` and rename it `OpTemplates1_2023.tox`, then restart your project file. The steps are the same for Mac, just locate your `Palette` folder!

##### Known issues

- Creating an OP by typing the operator type fully and hitting enter will **not** give the opportunity to place a template instead.
- Relative operator references in parameters can be broken due to naming conflicts.

## Open Templates

Opens a floating window of the current `Templates` container of the `OpTemplates` component. **Right-Click** to open custom parameters, **Middle-Click** to save.
