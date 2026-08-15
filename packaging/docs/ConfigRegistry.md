---
package: ConfigRegistry
summary: 'There are a couple of components whose states/contents you''ll probably want to synchronize between your projects, such as OpTemplates, ExprHotStrings, or Global ResetPLS exceptions.'
features:
  - name: Syncing/Externalizing
    anchor: syncingexternalizing
  - name: Custom Parameters
    anchor: custom-parameters
---

## Syncing/Externalizing

There are a couple of components whose states/contents you'll probably want to synchronize between your projects, such as [OpTemplates](/docs/optemplates/), [ExprHotStrings](/docs/exprhotstrings/#exprhotstrings), or [Global ResetPLS](/docs/resetpls1/#global-resetpls) exceptions. These are saved into a folder inside your **User Palette**, and can be toggled On or Off.

The state of some other components such as MIDI/OSC Maps get saved into your project folder for easy migration and future-proofing for updates.

These can be turned on or off in the Custom Parameters of the toolkit, which you can also access by right-clicking the (![](/docs/assets/icons/Fx.png) button in the toolbar.

The general settings of the tools (the **Custom Parameters**) can also be saved and synced between projects with the `Save/Load All Configs To/From JSON` buttons. You need to explicitly hit save whenever you make some significant change you'll want to synchronize to other projects, however there is a toggle for `Auto-Load`ing the configs after startup. This `json` file is also used for the **Self-Update Feature** in which case the settings are saved and re-loaded automatically.

## Custom Parameters

At the base level of `FunctionStore_tools.tox` you can find some custom parameters that allow you to customize its main functionalities on a broad scale. 

Should you want further customization, it is possible at the component level of each tool, feel free to dive in and customize each!

> You can easily access these main settings by right-clicking the ![](/docs/assets/icons/Fx.png) button in the toolbar.

### Active tab

In this tab you can choose to disable some of the components, that you might find annoying or unwanted. Some other setting are also crammed in there.

### Syncing

Turn On or Off Syncing/Externalizing for individual modules **(On by default)**. See [Syncing/Externalizing](https://github.com/function-store/FunctionStore_tools#syncingexternalizing) for more info.

See [TD2023 Migration guide](/docs/optemplates/#td2023-migration) for OpTemplates.

### UI

By pulsing `Open Toolbar Definition` you can customize the toolbar settings: enable/disable icons and change their orders. This is saved externally to sync with other project files. Note that this does not disable backend functionalities!
In this tab you can also set the default state of UI related mods such as windows title and timeline state, and UI color.
