---
package: "FNS_OpMenu"
summary: "This is a table to define custom search keywords for each OpType for the OpMenu / OP Create Dialog."
features:
  - name: "Custom OpMenu Search Keywords"
    anchor: "custom-opmenu-search-keywords"
  - name: "OpMenu Mods"
    anchor: "opmenu-mods"
  - name: "Greg's IO Filters"
    anchor: "gregs-io-filters"
  - name: "Custom Search Keywords"
    anchor: "custom-search-keywords"
  - name: "Dotsimulate's OpType acronyms"
    anchor: "dotsimulates-optype-acronyms"
  - name: "QuickOp"
    anchor: "quickop"
---

## Custom OpMenu Search Keywords

This is a table to define custom search keywords for each OpType for the **OpMenu / OP Create Dialog**. Read more [here](/docs/fns-opmenu/#opmenu-mods).

## OpMenu Mods



## Greg's IO Filters

This OP Create dialog mod by [Greg Hermanovic](https://derivative.ca) installs automatically from `FunctionStore_tools/Gregs_opmenu_mod` and adds filtering options to the OP Create dialog menu to the top right, showing only IO operators (`IO` option), or ops without the IO ones (`-IO`) or all (`All`, default).

IO operators are considered ones that interact with resources outside of TouchDesigner such as sensors or web interfaces. 

## Custom Search Keywords

For each OP Type you can define custom search keywords. For example you can find `Pattern CHOP` by typing `ramp` or `cos`, or you can find `Audio File In` by typing `music` in the OP search field. The definition table is fully customizable through the [custom UI](/docs/fns-opmenu/#custom-opmenu-search-keywords), and is synced across project files.

## Dotsimulate's OpType acronyms

Thanks to [Dotsimulate](https://www.patreon.com/dotsimulate/), you can also list OpTypes based on their acronym. Meaning you can find `Movie File Out` by typing `m f o`, and so on.

## QuickOp

This is an alternative and quicker way of adding new operators, and was suggested by [Greg Hermanovic](https://derivative.ca) to be implemented, which I happily obliged to.
`Ctrl-Dragging` and operator somewhere will pop the OP create dialog, and the selected operator will be placed in the position of the previous drag.
Similarly, `Shift-Dragging` will **Insert** a new operator between two operators.
