---
package: FNS_OpFamily
summary: 'The FNS tab in the OP Create dialog: an operator family whose members are FNS tools placed from the store as one node each, with stubs for projects that travel and in-place updates. Built with TDFam.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Where the operators come from
    anchor: where-the-operators-come-from
  - name: Stubs and updates
    anchor: stubs-and-updates
  - name: Credits
    anchor: credits
---

## What it is

Open the OP Create dialog and there is an **FNS** tab beside COMP, TOP, CHOP and the rest. Every entry on it is an FNS tool that reads as one operator: inputs on the left, outputs on the right, its own parameters, placed into the network you are working in like any stock type. Random, SimpleSceneChanger, ProSceneChanger, SwitchTools, MixSequencer, OpSequencer and CamSequencer are the first members.

You never pick it on its own. The installer adds it when you install one of its operators and removes it when the last of them goes, so a project without FNS operators has no FNS tab and no family registry, and the machine keeps no family folder for it.

The tab is optional. When you tick a family operator in Pick Tools, the selection bar shows **Add FNS tab to OP Create**. Untick it to keep the operators in your palette only. To turn the tab off later, untick **FNS Tab in OP Create** on the FNSTools page of the toolkit's parameters, untick the same switch in Pick Tools, or run the **Remove Operator Family** quick-launch command. The toggle turns it back on too, as long as at least one family operator is installed. Your FNS tools stay installed either way, and the choice sticks: installing another family operator, or setting up a new project like the last one, keeps the tab off until you tick the switch again.

The family is the same component wherever it runs: this package is a TDFam family named `FNS`, colour black, installed on project start, and its registry promotes itself to `/sys` the way TDFam designs it.

## Where the operators come from

Members are not embedded in this package. They are the packages you already know, mirrored from the machine's store into the family's operator folder (`FNSTools/FNS/` in your palette folder), one tox per member under its plain name with a manifest beside it. The same folder shows up in TouchDesigner's own Palette as `FNSTools > FNS`. The FNS updater keeps that folder in step with the store: every install and update pass that leaves the store complete runs the sync, so the FNS tab lists every member the machine holds, and only those.

Because the store only holds the packages your account is entitled to, a Pro-tier member appears on the tab for Pro members and not for Base members, with no extra gate anywhere. A member you never installed is still on the tab once the store holds it, since the store is complete by default (see the updater's Keep the Whole Release in the Store toggle).

A member can also be an operator alternative: create a Noise CHOP with the alternatives shortcut held and Random is offered. Two doors, one tox.

## Stubs and updates

Two things a pane package could not do before:

- **Stubs.** Before a project travels to a machine without the toolkit, stub the FNS operators: each placed member becomes a light placeholder that keeps its wiring, position, retained parameters and retained state. On a machine with the family, replace the stubs and the real operators come back. Both are commands on this package.
- **Updates in place.** A placed member is frozen at its spawn version. Update Family Operators upgrades every placed member to the newest version in the family folder, applying each member's retained parameters and state.

Which parameters and which state survive a stub or an update is declared per member in its manifest.

The same three actions, plus a resync of the family folder, are quick-launch commands: **Stub Family Operators**, **Replace Family Stubs**, **Update Family Operators** and **Sync Family From Store**. A fifth, **Remove Operator Family**, takes the tab away (see above). They act without dialogs and report what they did, and each can be limited to the network you are looking at. The toolkit's own copies of the members are never stubbed or updated this way, by these commands or by the pulses below: those copies belong to the FNS updater.

## Credits

Built with [TDFam](https://github.com/dotsimulate/TDFam) by Lyell Hintz (dotsimulate) and Dan Molnar (Function Store), Apache-2.0. The licence and notice ship inside the package.
