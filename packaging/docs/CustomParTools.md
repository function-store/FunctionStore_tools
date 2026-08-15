---
package: CustomParTools
summary: This button is a quick way to manipulate Custom Parameters of a parent component.
features:
  - name: CustomPar Tools
    anchor: custompar-tools
    icon: CustomParTools.png
  - name: QuickExt
    anchor: quickext
  - name: CustomParCustomize
    anchor: customparcustomize
  - name: CustomParHelper
    anchor: customparhelper
  - name: NoNode
    anchor: nonode
---

## CustomPar Tools

This button is a quick way to manipulate **Custom Parameters** of a parent component. It is also added for each pane!

- **Drag-and-Drop onto the icon:**
  - **A Parameter:** Promote that **Parameter** to the **Parent Custom Params** and Bind/Reference automatically (always to the currently active/selected page).
     - Hold `Alt/Opt` or `Ctrl` to customize parameter promotion—name it, set min/max values, and tweak clamping.
       - `Label` and `ParName` for **all** params, and for slider-type params: `min`, `max` values, `clamping` tickboxes, and `default` value  
       - **Quickly jump** between text fields by pressing `Tab` and `Shift+Tab`
  - **A Table DAT**: adds a new ParMenu and sets the table as a menu source
  - **A COMP:** Promote all **Custom Parameters** of the dragged **COMP** to the **Parent Custom Params** and Bind/Reference automatically. 
- **LeftClick:** Opens **Parent Parameters**.
- **Shift-LeftClick:** Opens **Selected OP Parameters**.
- **RightClick:** Opens **Parent Component Editor**.
- **Shift-RightClick:** Opens **Selected OP Component Editor**.
- **Alt-LeftClick (Cmd+LeftClick for Mac):** Clears broken parameter expressions/binds of a selected COMP recursively (usually useful after copying a COMP from another project)
- **Ctrl+Alt+Drag** an **OP** (Ctrl+Cmd+Drag on Mac): Promote as `iop` to parent
- **Ctrl+Shift+Click**: Add Parent shortcut
- **Shift+Alt+LeftClick** (Shift+Cmd+LeftClick for Mac): Add [QuickExt](/docs/custompartools/#quickext) to parent for a streamlined python Extension workflow - see [QuickExt](/docs/custompartools/)  
- **MiddleClick:** Promotes **Parent Parameters** further to **_its_** **Parent**.

## QuickExt

See the extensive description of [QuickExt](/docs/custompartools/).


---

## CustomParCustomize

A fast way to customize parameter promotion—name it, set min/max values, and tweak clamping. Related to [CustomParTools](/docs/quicktime/#quicktime)
   - `Label` and `ParName` for **all** params, and for slider-type params: `min`, `max` values, `clamping` tickboxes, and `default` value  
   - **Invoked** by holding `Ctrl` or `Alt`(`Opt`) while drag-and-dropping a parameter onto the `diamond` button or a parent in the path bar  
   - **Quickly jump** between text fields by pressing `Tab` and `Shift+Tab`  

When adding an extension using [CustomParTools](/docs/custompartools/#quickext)![](/docs/assets/icons/CustomParTools.png) **Shift+Alt+LeftClick**, the created default Extension will have the following available:
- Simplified default extension code
- Includes `ExtUtils` which contains [CustomParHelper](/docs/custompartools/#customparhelper) and [NoNode](/docs/custompartools/#nonode), which are also initialized in the default extension code

> You can also add QuickExt to your Base COMP via the `Component Editor->Extension` section by long-clicking on `Add` and selecting `QuickExt`

> It is important that `ExtUtils` stays docked to your extension code!

By leveraging [NoNode] and [CustomParHelper], TouchDesigner developers can create more efficient, organized, and maintainable extensions, ultimately leading to smoother workflow and improved project scalability.

> Pro Tip: Set your IDE's Python interpreter to that of TouchDesigner's to utilize stubs/code suggestion - ExtUtils will deploy its definition automatically!

##### Importing

The default extension code will contain the following - at first sight complicated looking - import statements for the utility packages. You can just ignore them, but don't remove them!

> This might look complicated at first but it's just a fancy import statement to avoid any conflicts when
> having multiple extension classes with ExtUtils attached. 

```python
  CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
  NoNode: NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
```

## CustomParHelper

CustomParHelper simplifies the management of custom parameters in TouchDesigner extensions, providing an intuitive interface for accessing and manipulating parameters, implementing callbacks, and handling parameter groups.

### Key Features:

- Easy parameter access as properties
- Simplified custom parameter callbacks
- Support for sequence parameters and blocks
- Parameter group (parGroups) management
- Flexible configuration for inclusion/exclusion of properties and callbacks
- Optional public/private naming conventions
- Automatic stub generation for improved IDE support

### Usage examples in your extension class:

0. Make sure ExtUtils is docked to your extension

1. Import the CustomParHelper class:
    ```python
    CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
    ```

2. Initialize in your extension's __init__ method as follows:
    ```python
    CustomParHelper.Init(self, ownerComp)
    ```

    Full signature and optional parameters:
    ```python
    CustomParHelper.Init(self, ownerComp, enable_properties: bool = True, enable_callbacks: bool = True, enable_parGroups: bool = True, enable_seq: bool = True, expose_public: bool = False,
          par_properties: list[str] = ['*'], par_callbacks: list[str] = ['*'], 
          except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [], 
          enable_stubs: bool = False, general_callback_enable: bool = True)
    ```

    Additional options:
    - `enable_properties`: If True, creates properties for custom parameters (default: True)
    - `enable_callbacks`: If True, creates callbacks for custom parameters (default: True)
    - `enable_parGroups`: If True, creates properties and methods for parGroups (default: True)
    - `enable_seq`: If True, creates properties and methods for sequence parameters (default: True)
    - `expose_public`: If True, uses capitalized property and method names (e.g., Par, Eval instead of par, eval)
    - `par_properties`: List of parameter names to include in property creation, by default all parameters are included
    - `par_callbacks`: List of parameter names to include in callback handling, by default all parameters are included
    - `except_properties`: List of parameter names to exclude from property creation
    - `except_callbacks`: List of parameter names to exclude from callback handling
    - `except_pages`: List of parameter pages to exclude from property and callback handling
    - `except_sequences`: List of sequence names to exclude from property and callback handling
    - `enable_stubs`: If True, automatically creates and updates stubs for the extension (default: False) (thanks to AlphaMoonbase.berlin for Stubser)
    - `general_callback_enable`: If True, enables general callbacks that catch all parameter changes (default: True)


3. Access and set custom parameters as properties (if enable_properties=True (default)):
    
    There are two ways to access and set parameter values:

    a) Using Eval properties (recommended for simple value setting):
    - `self.eval<ParamName>`: Get/set the evaluated value of the parameter
      ```python
      # Get value
      value = self.evalMyparam
      # Set value (always sets .val regardless of parameter mode)
      self.evalMyparam = 5
      ```
    - `self.evalGroup<GroupName>`: Get/set the evaluated value of the parameter group
      ```python
      # Get values
      values = self.evalGroupXyz
      # Set values (always sets .val for each parameter)
      self.evalGroupXyz = [1, 2, 3]
      ```

    b) Using Par properties (for advanced parameter control):
    - `self.par<ParamName>`: Access/set the parameter object
      ```python
      # Get parameter object for advanced operations
      self.parMyparam.expr = "op('something').par.value"
      self.parMyparam.bindExpr = "op('other').par.value"
      # Set value (only works in CONSTANT or BIND modes)
      self.parMyparam = 5  # Ignored if parameter is in EXPRESSION mode
      ```
    - `self.parGroup<GroupName>`: Access/set the parameter group object
      ```python
      # Get parameter group for advanced operations
      myGroup = self.parGroupXyz
      # Set values (only works for parameters in CONSTANT or BIND modes)
      self.parGroupXyz = [1, 2, 3]  # Only affects non-expression parameters
      ```

    > NOTE: to expose public properties, eg. self.Par<ParamName> instead of self.par<ParamName>, set expose_public=True in the Init function

4. Implement callbacks (if enable_callbacks=True (default)):
    a) Parameter-specific callbacks:
    - For regular parameters:
      ```python
      def onPar<Parname>(self, _par, _val, _prev):
        # _par and _prev can be omitted if not needed
      ```

    - For pulse parameters:
      ```python
      def onPar<PulseParname>(self, _par):
        # _par can be omitted if not needed
      ```

    - For sequence blocks:
      ```python
      def onSeq<SeqName>N(self, idx):
      ```

    - For sequence parameters:
      ```python
      def onSeq<SeqName>N<Parname>(self, _par, idx, _val, _prev):
        # _par and _prev can be omitted if not needed
      ```

    - For parameter groups if enable_parGroups=True (default):
      ```python
      def onParGroup<Groupname>(self, _parGroup, _val):
        # _parGroup can be omitted if not needed
      ```

    b) General callbacks (if general_callback_enable=True (default)):
    These catch all parameter changes that aren't handled by specific callbacks:
    
    - For value changes:
      ```python
      def onValueChange(self, _par, _val, _prev):
        # Called when any parameter value changes that doesn't have a specific callback
        # _val and _prev can be omitted if not needed
      ```

    - For pulse parameters:
      ```python
      def onPulse(self, _par):
        # Called when any pulse parameter is triggered that doesn't have a specific callback
        # _par can be omitted if not needed
      ```

## NoNode

NoNode is a versatile utility class that centralizes the management of various types of executions and callbacks in TouchDesigner, eliminating the need for dedicated nodes.

### Usage examples:

1. Make sure ExtUtils is docked to your extension

2. Import the NoNode class:
   ```python
   NoNode: NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
   ```

3. Initialize the NoNode system in your extension:
   ```python
   NoNode.Init(enable_chopexec=True, enable_datexec=True, enable_parexec=True, enable_keyboard_shortcuts=True)
   ```

4. CHOP executions:
   - Register a callback for CHOP value changes:
     ```python
     NoNode.RegisterChopExec(NoNode.ChopExecType.ValueChange, chop_op, channel_name(s), self.on_value_change_function)
     # callback signature: def on_value_change_function(self, channel: Channel, sampleIndex: int, val: float, prev: float):
     # can omit parameters from the right side of the signature if not needed
     ```
   - Handle CHOP state changes:
     ```python
     NoNode.RegisterChopExec(NoNode.ChopExecType.OffToOn, chop_op, channel_name(s), self.on_activate_function)
     # callback signature: def on_activate_function(self, channel: Channel, sampleIndex: int, val: float, prev: float):
     # can omit parameters from the right side of the signature if not needed
     ```

5. DAT executions:
   - React to table changes in a DAT:
     ```python
     NoNode.RegisterDatExec(NoNode.DatExecType.TableChange, dat_op, self.on_table_change_function)
     # callback signature depends on the event type, eg.: def on_table_change_function(self, dat: DAT):
     ```
   - Handle cell value changes:
     ```python
     NoNode.RegisterDatExec(NoNode.DatExecType.CellChange, dat_op, self.on_cell_change_function)
     # callback signature depends on the event type, eg.: def on_cell_change_function(self, dat: DAT, cells: list[Cell], prev: Cell):
     ```

6. Parameter executions:
   - Register a callback for parameter value changes:
     ```python
     NoNode.RegisterParExec(NoNode.ParExecType.ValueChange, par_op, par_name, self.on_value_change_function)
     # callback signature depends on the event type, eg.: def on_value_change_function(self, par: Par, val: float, prev: float):
     # can omit prev, or use val only
     ```
   - Handle pulse parameters:
     ```python
     NoNode.RegisterParExec(NoNode.ParExecType.OnPulse, par_op, par_name, self.on_pulse_function)
     # callback signature: def on_pulse_function(self,par: Par):
     # can omit par if not needed
     ```

7. Keyboard shortcuts:
   - Register a keyboard shortcut:
     ```python
     NoNode.RegisterKeyboardShortcut('ctrl.k', self.onKeyboardShortcut)
     # callback signature: def onKeyboardShortcut(self):
     ```

7. Deregister callbacks:
   - Deregister a CHOP execution:
     ```python
     NoNode.DeregisterChopExec(NoNode.ChopExecType.ValueChange, chop_op, channel_name(s))
     ```
   - Deregister a DAT execution:
     ```python
     NoNode.DeregisterDatExec(NoNode.DatExecType.TableChange, dat_op)
     ```
   - Deregister a parameter execution:
     ```python
     NoNode.DeregisterParExec(NoNode.ParExecType.ValueChange, par_op, par_name)
     ```  
   - Deregister a keyboard shortcut:
     ```python
     NoNode.DeregisterKeyboardShortcut('ctrl.k')
     ```

8. Visual indication:
   - Operators with registered callbacks are marked with a color for easy identification
   - Customize the mark color:
     ```python
     NoNode.SetMarkColor((r, g, b))
     ```


To demo all the features you can download [QuickExtTest.tox](https://github.com/function-store/FunctionStore_tools/blob/main/modules/suspects/FunctionStore_tools_2023/QuickExtTest.tox) and run it or just check its [extension code](https://github.com/function-store/FunctionStore_tools/blob/main/scripts/QuickExt/templates/ExtUtils/ExtTest.py).
