
'''Info Header Start
Name : text2
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
Saveversion : 2025.33070
Info Header End'''
"""
GLSL Vector Parameter Promoter for TouchDesigner
=================================================

This script promotes GLSL uniform vectors from glsl1 (sibling operator) 
to custom parameters on the parent base. This allows you to control 
shader uniforms from the base's parameter panel.

Usage:
1. Place this script inside the base alongside glsl1
2. Run this script
3. Enter comma-separated uniform names to exclude when prompted
4. The script will create vec4 custom parameters on the parent
5. GLSL TOP parameters will be bound to reference the parent's parameters

Notes:
- The GLSL TOP must be named 'glsl1' (sibling to this DAT)
- Parameters are created on the 'Custom' page of the parent base
- Default exclusions: uTime, uResolution
- Parameter names are converted to TD format (e.g., uArcEnd -> UArcEnd1/2/3/4)
- Existing parameter values are preserved during promotion
"""

# Promote used Vectors from glsl1 to parent's custom pars as vec4

# Popup to get excluded uniforms
def onSelect(info):
    print('Dialog info:', info)  # Debug
    # Button 2 is OK (second button in the list)
    if info['buttonNum'] == 2:
        exclude_text = info['enteredText']
        # Parse comma-separated list, strip whitespace
        skip_uniforms = [u.strip() for u in exclude_text.split(',') if u.strip()]
        print('Excluding:', skip_uniforms)
        runPromote(skip_uniforms)
    else:
        print('Cancelled')

def runPromote(skip_uniforms):
    print('runPromote called, excluding:', skip_uniforms)
    base_comp = parent()
    glsl_top = op('glsl1')
    
    print('base_comp:', base_comp)
    print('glsl_top:', glsl_top)
    
    if base_comp is None:
        ui.messageBox('Error', 'Parent not found')
        return
    if glsl_top is None:
        ui.messageBox('Error', 'glsl1 not found as sibling')
        return
    
    # Get the existing Custom page or create one
    page = None
    for pg in base_comp.customPages:
        if pg.name == 'Custom':
            page = pg
            break
    if page is None:
        page = base_comp.appendCustomPage('Custom')
    
    # Find which vector slots are in use and not skipped
    # Get existing vec*name parameters to avoid expanding unused slots
    import re
    vec_name_pars = [p for p in glsl_top.pars() if re.match(r'vec\d+name$', p.name)]
    
    for name_par in vec_name_pars:
        if name_par.eval() == '':
            continue
        uniform_name = name_par.eval()
        
        # Extract the index from parameter name (e.g., 'vec0name' -> '0')
        idx = re.search(r'vec(\d+)name', name_par.name).group(1)
        
        # Skip excluded uniforms
        if uniform_name in skip_uniforms:
            print('Skipping:', uniform_name)
            continue
        
        # Convert to valid TD par name: Capitalize first letter, preserve rest
        par_name = uniform_name[0].upper() + uniform_name[1:]
        
        # Get current XYZW values
        src_x = getattr(glsl_top.par, 'vec{}valuex'.format(idx))
        src_y = getattr(glsl_top.par, 'vec{}valuey'.format(idx))
        src_z = getattr(glsl_top.par, 'vec{}valuez'.format(idx))
        src_w = getattr(glsl_top.par, 'vec{}valuew'.format(idx))
        
        # Set to constant to read values
        for src in [src_x, src_y, src_z, src_w]:
            src.mode = ParMode.CONSTANT
        
        val_x = src_x.eval()
        val_y = src_y.eval()
        val_z = src_z.eval()
        val_w = src_w.eval()
        
        # Create vec4 par if it doesn't exist (size=4 creates pars with 1,2,3,4 suffixes)
        if not hasattr(base_comp.par, par_name + '1'):
            new_pars = page.appendFloat(par_name, label=uniform_name, size=4)
            print('Created vec4:', par_name)
            # new_pars is a tuple of the 4 created parameters
            new_pars[0].val = val_x
            new_pars[1].val = val_y
            new_pars[2].val = val_z
            new_pars[3].val = val_w
        else:
            # Par already exists, set values directly
            base_comp.par[par_name + '1'].val = val_x
            base_comp.par[par_name + '2'].val = val_y
            base_comp.par[par_name + '3'].val = val_z
            base_comp.par[par_name + '4'].val = val_w
        print('  Set values:', val_x, val_y, val_z, val_w)
        
        # Bind glsl1 pars to parent (using 1,2,3,4 suffixes)
        src_x.expr = 'parent().par.' + par_name + '1'
        src_y.expr = 'parent().par.' + par_name + '2'
        src_z.expr = 'parent().par.' + par_name + '3'
        src_w.expr = 'parent().par.' + par_name + '4'
        src_x.mode = ParMode.EXPRESSION
        src_y.mode = ParMode.EXPRESSION
        src_z.mode = ParMode.EXPRESSION
        src_w.mode = ParMode.EXPRESSION
        print('  Bound to parent')
    print('Done! Promoted vectors to', base_comp.path)

# Show the input dialog
op.TDResources.PopDialog.Open(
    text='Enter comma-separated uniforms to exclude:',
    title='Promote GLSL Vectors',
    buttons=['Cancel', 'OK'],
    enterButton=2,
    escButton=1,
    escOnClickAway=True,
    textEntry='uTime, uResolution',
    callback=onSelect
)