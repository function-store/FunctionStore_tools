---
package: SeqMod
summary: 'Watches a sequence of parameters on any COMP and tells you when blocks come and go: name the target and the sequence, and the block parameters are published as one list, with a callback per added or removed block.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Callbacks
    anchor: callbacks
---

## What it is

Sequence parameters (the `Items0name`, `Items1name`, ... blocks TouchDesigner grows and shrinks) are awkward to drive from outside: the names change with the count, and nothing tells you when a block appears. SeqMod sits beside the COMP that owns the sequence, keeps the list of block parameters current, publishes them as `Par Names` and as a table on `out1`, and fires a callback for every block added or removed. Wire it to a replicator, a UI builder or your own script and the sequence becomes something you can react to.

Point `COMP` at the target, set `Seq Name` to the sequence's name, and the tool follows the count from there. References resolve from SeqMod itself: a bare name is a sibling of SeqMod, `..` (the default) is the network SeqMod sits in, and something inside SeqMod needs `./name`. The same rule applies to the Callbacks DAT.

It is a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Callbacks

`Create Callbacks` makes a DAT with two hooks, called once per block:

- `OnAddBlock(seqBlock)`: a block was added; `seqBlock` is the new block.
- `OnRemoveBlock(seqBlock_idx)`: a block was removed; the index it had.

Retargeting the tool to another COMP or sequence does not fire them. Errors raised inside a callback are reported on SeqMod itself.
