---
package: FNS_BackupCleaner
summary: 'Every .toe backup under a folder, grouped by the project that made them, with sizes and an estimate of the hours they hold; clean the ones you are done with.'
features:
  - name: Backup Cleaner
    anchor: backup-cleaner
  - name: Reading the list
    anchor: reading-the-list
  - name: Keeping the recent ones
    anchor: keeping-the-recent-ones
  - name: Cleaning
    anchor: cleaning
  - name: What counts as a backup
    anchor: what-counts-as-a-backup
---

## Backup Cleaner

A tab of [Hub](/docs/fns-hub/) (the **FNS** button in the main-menu bar).

TouchDesigner writes a numbered `.toe` into a `Backup` folder every time you
save. They are worth having, and after a year of work there are thousands of
them. This tool finds them under a folder you choose, shows you what they cost
you in disk space, and lets you throw away the ones you are finished with.

Nothing is scanned until you open the tab or press **Scan**, so the tool costs
nothing while you are working.

## Reading the list

Set **Root Folder** to where your projects live and press **Scan**. The list is
a tree: one row per folder that contains backups, with its files underneath.

A folder row totals everything below it, including its sub-folders:

- **Size** in megabytes.
- **Count**, how many backup files.
- **Work Hrs**, an estimate of the time those saves represent. Save timestamps
  are grouped into sessions, a gap of more than an hour starts a new one, and
  the sessions are added up. It is a rough number and it is often the reason
  you decide to keep a folder.

Right-click a row to show that file in your file browser. Click the header of
the size column to re-scan.

## Keeping the recent ones

**Keep Last** protects the newest N backups in every folder. At `0` nothing is
protected and everything found is a candidate. Set it to `5` and the five most
recent saves in each folder drop out of the list, so what remains is only the
history you have clearly moved past.

## Cleaning

The trash icon in the header row cleans everything currently listed. The trash
icon on a row cleans that row, and on a folder row that means every backup
inside it. If you have selected rows, the trash icon cleans the selection.

You are asked before anything happens, and you get two choices:

- **Move to Recycle Bin** (Trash on macOS), which is reversible.
- **Permanent Delete**, which asks a second time and then is not.

Holding **Shift** while clicking a row's trash icon deletes permanently without
the dialog. The list refreshes itself afterwards.

## What counts as a backup

**Regex Pattern** decides. The default, `Backup/.+\..+\.toe`, matches the
numbered files TouchDesigner writes into a `Backup` folder and nothing else,
which is why your working `.toe` files never appear in the list. Change it if
your projects keep their backups somewhere else.

The pattern and Keep Last follow you between projects. The root folder does
not, because it is a path on one machine.
