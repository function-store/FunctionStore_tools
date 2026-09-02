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

Clicking this icon will open this Wiki page. If the border of this icon is yellow it means one or more of your installed packages have an update available. Clicking it in that state will prompt you for an update.

## Self-Update Feature

If there is an update available for any package installed in your project, the `?` icon in the toolbar will have a yellow border. Clicking the icon will prompt you for an update, you can say `No` in which case it will take you to the Wiki as usual, otherwise the following is going to happen:
- Save all configs (custom parameters of tools) to a `json` file
- Fetch only the packages that actually changed from the store (verifying each download's hash), and replace just those; a package you never installed stays uninstalled
- Reload each replaced tool's saved configs

This way we can ensure that your settings are retained between updates, alongside the externally retained data, outlined in the next chapter.
