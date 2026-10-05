---
package: FNS_SearchFix
summary: The network editor's find bar finds what you mean. Any part of a name, case-insensitive, with wildcards, optionally fuzzy and inside child networks, with the bar's arrows and Home toggle kept.
features:
  - name: Searching
    anchor: searching
  - name: The find bar
    anchor: the-find-bar
---

## Searching

TouchDesigner's find bar only finds names that start with exactly what you
typed, in the network you are looking at. SearchFix replaces that search in
every pane's find bar:

- **Any part of a name, any case.** `SimpleScene` finds
  `FNS_SimpleSceneChanger`; `scene` finds it too.
- **Spaces become underscores** as you type, since operator names have
  none. A text that does not match as typed is tried as its parts:
  `scene_chang` finds `FNS_SimpleSceneChanger`, and every part has to hit.
- **Wildcards** work like TouchDesigner's own pattern fields (a Select OP's,
  for example), in any case: `noise*`, `*out?`, `[ab]lur*`. A pattern has to
  match the whole name, and `^` turns it around: `^FNS_*` finds everything
  that does not start with FNS_.
- **Fuzzy**, when you switch it on, also finds the first letters of words
  (`sschg`), a typo or two (`nosie`), or the letters in order. Those hits come
  after every plain one.
- **Best first.** An exact name comes before one that starts with your text,
  then a word inside the name, then anywhere in it, and shallower operators
  before deeper ones.

## The find bar

Open a pane's find bar as usual. The back and forward arrows step through
the results, and the first result is picked as you type, like before. A
picked operator becomes current and selected; with **Home** on, the pane
centres on it. When a **Deep** search finds something inside a child network,
picking it takes the pane into that network, and the arrows keep stepping
through the same results.

Beside Home sit three checkboxes, drawn like Home's own. **Legacy** brings TouchDesigner's own search
back and **Fuzzy** turns loose matching on; they are the tool's parameters,
so every pane's find bar shares them. **Deep** belongs to that pane's bar:
off searches the network you are in, like TouchDesigner; on, a number field
appears beside it and sets how deep the search goes: 1 is the network you
are in, 2 adds the networks inside it, and so on. The field starts at the
tool's Deep Depth, and each pane keeps its own Deep and depth for the
session.

TouchDesigner opens and closes a pane's find bar on Ctrl+F (Cmd+F on macOS)
while you work in the network, but once you are typing in the bar the
shortcut does nothing. With **Shortcut Closes Find Bar** on, it closes the
bar from there too.

Switching SearchFix off leaves every find bar exactly as TouchDesigner made
it.
