# Embody/PI pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/table edits only). args[0] = resolved save path.
exec(open('packaging/pre_release_common.py').read())

# A shipped SearchFix starts Active with TouchDesigner's defaults for the rest:
# whatever the author had switched on while working does not ride along.
for _name, _val in (('Active', True), ('Legacy', False), ('Fuzzy', False), ('Depth', 3), ('Maxresults', 500), ('Togglefindbar', True)):
    _p = _c0.par[_name]
    if _p is not None:
        _p.val = _val
