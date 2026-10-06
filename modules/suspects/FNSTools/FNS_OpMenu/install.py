
'''Info Header Start
Name : install
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''

# Surface installation for TD's Insert Operator dialog.
#
# Almost everything this script used to do is owned by OpMenuRegistry now,
# which injects and heals the dialog from whatever tools have registered:
#   - the node-table script node and the right-click menu (registry's own)
#   - the I/O filter chain stage and its radio panel (published BY IOFilter,
#     through its own OpMenuRegistry host + opmenu_callbacks)
#
# What is left is the one thing that is not an entry: a one-shot patch to
# TD's own operator-compatibility table.

op('menu_op_compatible_mod').run()
