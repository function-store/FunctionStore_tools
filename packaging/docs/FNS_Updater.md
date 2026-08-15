---
package: FNS_Updater
summary: Clicking this icon will open this Wiki page.
features:
  - name: Wiki
    anchor: wiki
    icon: Wiki.png
  - name: Self-Update Feature
    anchor: self-update-feature
---

## Wiki

Clicking this icon will open this Wiki page. If the border of this icon is yellow it means there's an update available to the toolkit. Clicking it in that state will prompt you for an update, that will also replace the current .tox with the new one!

## Self-Update Feature

If the toolkit (v2.4.0+) is installed in your project and there is an update, the `?` icon in the toolbar will have a yellow border. Clicking the icon will prompt you for an update, you can say `No` in which case it will take you to the Wiki as usual, otherwise the following is going to happen:
- Save all configs (custom parameters of tools) to a `json` file
- Download the new version of the toolkit `.tox` into the user palette, and replace the existing one with it
- Load all the saved configs from the previously saved `json` file

This way we can ensure that your settings are retained between updates, alongside the externally retained data, outlined in the next chapter.
