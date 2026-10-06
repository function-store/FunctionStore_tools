---
package: LinkOPs
summary: 'Links the parameters of several operators so a change on one lands on all of them: name the operators by pattern, leave some out, leave some parameters out, keep the list current automatically, and optionally link constants only.'
features:
  - name: What it is
    anchor: what-it-is
---

## What it is

Drop LinkOPs into a network, name the operators to link (`noise*`, `level1 level2`) and from then on a parameter changed on any one of them is written to the same parameter on the others: values, and by default expressions and modes too. Except leaves operators out even when they match, Par Except leaves parameters out (`t? seed` keeps transforms and seeds independent), and Constant Only restricts the link to parameters that are in constant mode on both sides, so an expression on one operator is never overwritten.

The search happens in the network LinkOPs sits in. With Auto on the list follows operators as they are added, renamed or removed; with Auto off, Sync rescans on demand. Changes are propagated once per frame from the full list of what changed, so when two linked operators change the same parameter in one frame the last change wins.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.
