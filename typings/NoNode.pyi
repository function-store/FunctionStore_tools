import re
import TDStoreTools
from typing import Callable, Dict, Union, List
from enum import Enum, auto

class NoNode:
    """
    ## NoNode

    NoNode is a versatile utility class that centralizes the management of various types of executions and callbacks in TouchDesigner, eliminating the need for dedicated nodes.

    ### Key Features:
    - Keyboard shortcut handling
    - CHOP executions (value changes, on/off states)
    - DAT executions (table, row, or cell changes)
    - Centralized event management
    - Reduced node clutter
    - Visual indication of watched operators

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

    """

    class ChopExecType(Enum):
        OffToOn = auto()
        WhileOn = auto()
        OnToOff = auto()
        WhileOff = auto()
        ValueChange = auto()

    class DatExecType(Enum):
        TableChange = auto()
        RowChange = auto()
        ColChange = auto()
        CellChange = auto()
        SizeChange = auto()

    class ParExecType(Enum):
        ValueChange = auto()
        OnPulse = auto()
    MARK_COLOR = (0.5, 0.05, 0.5)
    CHOP_VALUECHANGE_EXEC: DAT = op('extChopValueChangeExec')
    CHOP_OFFTOON_EXEC: DAT = op('extChopOffToOnExec')
    CHOP_ONTOOFF_EXEC: DAT = op('extChopOnToOffExec')
    CHOP_WHILEON_EXEC: DAT = op('extChopWhileOnExec')
    CHOP_WHILEOFF_EXEC: DAT = op('extChopWhileOffExec')
    DAT_TABLECHANGE_EXEC: DAT = op('extDatTableChangeExec')
    DAT_ROWCHANGE_EXEC: DAT = op('extDatRowChangeExec')
    DAT_COLCHANGE_EXEC: DAT = op('extDatColChangeExec')
    DAT_CELLCHANGE_EXEC: DAT = op('extDatCellChangeExec')
    DAT_SIZECHANGE_EXEC: DAT = op('extDatSizeChangeExec')
    KEYBOARD_EXEC: DAT = op('extKeyboardIn')
    CHOP_EXECS: list[DAT] = [CHOP_VALUECHANGE_EXEC, CHOP_OFFTOON_EXEC, CHOP_ONTOOFF_EXEC, CHOP_WHILEON_EXEC, CHOP_WHILEOFF_EXEC]
    DAT_EXECS: list[DAT] = [DAT_TABLECHANGE_EXEC, DAT_ROWCHANGE_EXEC, DAT_COLCHANGE_EXEC, DAT_CELLCHANGE_EXEC, DAT_SIZECHANGE_EXEC]
    CHOP_EXEC_MAP: Dict[ChopExecType, COMP] = {ChopExecType.ValueChange: CHOP_VALUECHANGE_EXEC, ChopExecType.OffToOn: CHOP_OFFTOON_EXEC, ChopExecType.OnToOff: CHOP_ONTOOFF_EXEC, ChopExecType.WhileOn: CHOP_WHILEON_EXEC, ChopExecType.WhileOff: CHOP_WHILEOFF_EXEC}
    DAT_EXEC_MAP: Dict[DatExecType, COMP] = {DatExecType.TableChange: DAT_TABLECHANGE_EXEC, DatExecType.RowChange: DAT_ROWCHANGE_EXEC, DatExecType.ColChange: DAT_COLCHANGE_EXEC, DatExecType.CellChange: DAT_CELLCHANGE_EXEC, DatExecType.SizeChange: DAT_SIZECHANGE_EXEC}
    CHOPEXEC_CALLBACKS: TDStoreTools.DependDict[ChopExecType, dict[CHOP, dict[str, Callable]]] = TDStoreTools.DependDict()
    DATEXEC_CALLBACKS: TDStoreTools.DependDict[DatExecType, dict[DAT, Callable]] = TDStoreTools.DependDict()
    KEYBOARD_CALLBACKS: TDStoreTools.DependDict[str, Callable] = TDStoreTools.DependDict()
    CHOPEXEC_IS_ENABLED: bool = False
    DATEXEC_IS_ENABLED: bool = False
    KEYBOARD_IS_ENABLED: bool = False
    PAR_VALUECHANGE_EXEC: DAT = op('extParExecNoNodeValueChange')
    PAR_ONPULSE_EXEC: DAT = op('extParExecNoNodeOnPulse')
    PAR_EXECS: list[DAT] = [PAR_VALUECHANGE_EXEC, PAR_ONPULSE_EXEC]
    PAR_EXEC_MAP: Dict[ParExecType, COMP] = {ParExecType.ValueChange: PAR_VALUECHANGE_EXEC, ParExecType.OnPulse: PAR_ONPULSE_EXEC}
    PAREXEC_CALLBACKS: TDStoreTools.DependDict[ParExecType, dict[OP, dict[Union[Par, str], Callable]]] = TDStoreTools.DependDict()
    PAREXEC_IS_ENABLED: bool = False
    ALL_EXECS: list[DAT] = CHOP_EXECS + DAT_EXECS + PAR_EXECS + [KEYBOARD_EXEC]
    EXT_OWNER_COMP: COMP = None

    @classmethod
    def Init(cls, ownerComp, enable_chopexec: bool=True, enable_datexec: bool=True, enable_parexec: bool=True, enable_keyboard_shortcuts: bool=True) -> None:
        """Initialize the NoNode functionality."""
        pass

    @classmethod
    def EnableChopExec(cls) -> None:
        """Enable chopExec handling."""
        pass

    @classmethod
    def EnableDatExec(cls) -> None:
        """Enable datExec handling."""
        pass

    @classmethod
    def DisableChopExec(cls, event_type: ChopExecType=None) -> None:
        """Disable chopExec handling for a specific event type or all event types."""
        pass

    @classmethod
    def DisableDatExec(cls, event_type: DatExecType=None) -> None:
        """Disable datExec handling for a specific event type or all event types."""
        pass

    @classmethod
    def RegisterChopExec(cls, event_type: ChopExecType, chop: CHOP, channels: Union[str, List[str]], callback: Callable) -> None:
        """
        Register a CHOP execute callback.

        Args:
            event_type (ChopExecType): The type of event to listen for.
            chop (CHOP): The CHOP operator to register the callback for.
            channels (Union[str, List[str]]): The channel(s) to listen to. Can be a whitespace and/or comma separated string, or a list. Use '*' for all channels.
            callback (Callable): The callback function to be called on CHOP execution.

        Example:
            def my_callback(event_type, channel, index, value, prev):
                print(f"Event: {event_type}, Channel {channel} at index {index} changed from {prev} to {value}")
            
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), '*', my_callback)
            # Or with multiple channels:
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), ['chan1', 'chan2'], my_callback)
            # Or with comma and/or whitespace separated channels:
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), 'chan1, chan2 chan3,chan4', my_callback)
        """
        pass

    @classmethod
    def RegisterDatExec(cls, event_type: DatExecType, dat: DAT, callback: Callable) -> None:
        """
        Register a DAT execute callback.

        Args:
            event_type (DatExecType): The type of event to listen for.
            dat (DAT): The DAT operator to register the callback for.
            callback (Callable): The callback function to be called on DAT execution.

        Example:
            def my_callback(dat, rows, cols):
                print(f"DAT {dat} changed. New size: {rows}x{cols}")
            
            NoNode.RegisterDatExec(DatExecType.SizeChange, op('table1'), my_callback)
        """
        pass

    @classmethod
    def DeregisterChopExec(cls, event_type: ChopExecType, chop: CHOP=None, channels: Union[str, List[str]]=None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (ChopExecType): The event type to deregister.
            chop (CHOP, optional): The CHOP operator to deregister the callback for. If None, deregisters all CHOPs for the event type.
            channels (Union[str, List[str]], optional): The channel(s) to deregister. Can be a string (single channel, comma/space-separated list, or wildcard pattern) or a list of strings. If None, deregisters all channels for the specified CHOP.
        """
        pass

    @classmethod
    def DeregisterDatExec(cls, event_type: DatExecType, dat: DAT=None) -> None:
        """
        Deregister a datExec callback

        Args:
            event_type (DatExecType): The event type to deregister.
            dat (DAT, optional): The DAT operator to deregister the callback for. If None, deregisters all DATs for the event type.
        """
        pass

    @classmethod
    def OnChopExec(cls, event_type: ChopExecType, channel: Channel, sampleIndex: int, val: float, prev: float) -> None:
        """Handle chopExec events."""
        pass

    @classmethod
    def OnDatExec(cls, event_type: DatExecType, dat: DAT, rows: int=None, cols: int=None, cells: list[Cell]=None, prev=None) -> None:
        """Handle datExec events."""
        pass

    @classmethod
    def EnableKeyboardShortcuts(cls) -> None:
        """Enable keyboard shortcut handling."""
        pass

    @classmethod
    def DisableKeyboardShortcuts(cls) -> None:
        """Disable keyboard shortcut handling."""
        pass

    @classmethod
    def RegisterKeyboardShortcut(cls, shortcut: str, callback: callable) -> None:
        """ Register a keyboard shortcut and its callback.
        Handle keyboard shortcuts (if enable_keyboard_shortcuts=True (default is False)):
       - Enable keyboard shortcuts:
         CustomParHelper.Init(self, ownerComp, enable_keyboard_shortcuts=True)
       - Register a keyboard shortcut and its callback:
         CustomParHelper.RegisterKeyboardShortcut("ctrl.k", self.onKeyboardShortcut)
       - Implement the callback method:
         def onKeyboardShortcut(self):
           # This method will be called when the registered keyboard shortcut is pressed
        """
        pass

    @classmethod
    def DeregisterKeyboardShortcut(cls, shortcut: str) -> None:
        """Unregister a keyboard shortcut."""
        pass

    @classmethod
    def OnKeyboardShortcut(cls, shortcut: str) -> None:
        """Handle keyboard shortcut events."""
        pass

    @classmethod
    def SetMarkColor(cls, color: tuple[float, float, float]) -> None:
        """Set the mark color."""
        pass

    @classmethod
    def EnableParExec(cls) -> None:
        """Enable parameter execute handling."""
        pass

    @classmethod
    def DisableParExec(cls, event_type: ParExecType=None) -> None:
        """Disable parameter execute handling for a specific event type or all event types."""
        pass

    @classmethod
    def RegisterParExec(cls, event_type: ParExecType, owner: OP, parameter: Union[Par, str], callback: Callable) -> None:
        """
        Register a parameter execute callback.

        Args:   
            event_type (ParExecType): The type of event to listen for.
            owner (OP): The operator that owns the parameter.
            parameter (Union[Par, str]): The parameter to watch. Can be a Par object or parameter name.
            callback (Callable): The callback function to be called on parameter execution.

        Example:
            def my_callback(par, prev):
                print(f"Parameter {par} changed from {prev} to {par.eval()}")
            
            # Using Par object from any operator
            NoNode.RegisterParExec(op('base1'), ParExecType.ValueChange, op('base1').par.v, self.my_callback)
        """
        pass

    @classmethod
    def DeregisterParExec(cls, event_type: ParExecType, owner: OP, parameter: Union[Par, str]=None) -> None:
        """
        Deregister a parameter execute callback.

        Args:
            event_type (ParExecType): The event type to deregister. 
            owner (OP): The operator that owns the parameter.
            parameter (Union[Par, str], optional): The parameter to deregister. If None, deregisters all parameters for the owner.
           
        """
        pass

    @classmethod
    def OnParExec(cls, event_type: ParExecType, parameter: Par, value=None, prev=None) -> None:
        """Handle parameter execute events."""
        pass