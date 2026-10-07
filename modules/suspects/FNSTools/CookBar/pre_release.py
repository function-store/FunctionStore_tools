# Embody/PI pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/table edits only). args[0] = resolved save path.
exec(open('packaging/pre_release_common.py').read())

# Cook Bar ships switched off, holding nothing from the network it last drew
# in. Keys are stored as None rather than unstored: its scripts fetch them
# with no default, and fetch() raises on a missing key.
_c0.par.Active.val = False
_c0.par.Active.enable = True
_c0.comment = ''
for _k in ('targetCOMP', 'winWidth', 'winHeight'):
    _c0.store(_k, None)
# The view geometry stays NUMERIC: glsl_cook_bar's resolution and uniforms
# read it by expression, and float(None) is an error the moment it cooks.
for _k, _v in (('netX', 0.0), ('netY', 0.0), ('netZoom', 1.0),
               ('netWidth', 640.0), ('netHeight', 360.0), ('netRatio', 1.0)):
    _c0.store(_k, _v)
_c0.store('active', False)
_c0.store('hiddenDisplay', [])
_c0.store('dimmedAnnotations', [])
_p = _c0.par['Annotationalpha']
if _p is not None:
    _p.val = 0.2
_p = _c0.par['Maxops']
if _p is not None:
    _p.val = 100

# The Global Hog CHOP (toolbar right-click) exists to eat frame time on
# purpose; it ships switched off.
_hog = _c0.op('hog_global')
if _hog is not None:
    _hog.par.active.val = False

# The background TOP is renamed while the bar is on; ship its idle name.
_bg = _c0.op('null_cook_bar_bg')
if _bg is not None:
    _bg.name = 'null_cook_bar_bg__deactivated'

# Its own background ops, if a pane was inside the tool while it was on.
for _n in ('select_cook_bar_bg', 'text_cook_bar_suicide'):
    _o = _c0.op(_n)
    if _o is not None:
        _o.destroy()

# The last frame's measurements of the network it was drawing.
_t = _c0.op('table_op_info')
if _t is not None:
    _t.text = '\t'.join(('name', 'x', 'y', 'width', 'height', 'border', 'isCOMP',
                         'cooking', 'cookTime', 'childrenCooking',
                         'childrenCookTime', 'gpuMemory', 'childrenGpuMemory'))
