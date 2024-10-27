import re
import TDStoreTools
from typing import Callable, Dict, Union, List
from enum import Enum, auto


class NoNode:
    '''
    # NoNode

    NoNode is a versatile utility class designed to enhance TouchDesigner workflows by providing a centralized system for managing various types of executions and callbacks without requiring dedicated nodes.

    ## Key Features

    1. Keyboard shortcut handling: Easily define and manage custom keyboard shortcuts.
    2. CHOP executions: Handle different types of CHOP events (e.g., value changes, on/off states).
    3. DAT executions: Manage various DAT-related events (e.g., table, row, or cell changes).

    This class simplifies the process of setting up complex interactions and automations within TouchDesigner projects, 
    reducing clutter and improving organization. It's particularly useful for larger projects or when working with 
    multiple extensions that need to respond to similar events.

    ## Usage Examples

    ### 0. Initialize the NoNode system in your extension:
       NoNode.Init(enable_chopexec=True, enable_datexec=True, enable_keyboard_shortcuts=True)

    ### 1. CHOP executions:
       - Register a callback for CHOP value changes:
         NoNode.RegisterChopExec(NoNode.ChopExecType.ValueChange, chop_op, channel_name, callback_function)
         # callback signature: def on_value_change_function(channel: Channel, sampleIndex: int, val: float, prev: float):
         # can omit parameters from the right side of the signature if not needed
       - Handle CHOP state changes:
         NoNode.RegisterChopExec(NoNode.ChopExecType.OffToOn, chop_op, channel_name, on_activate_function)
         # callback signature: def on_activate_function(channel: Channel, sampleIndex: int, val: float, prev: float):
         # can omit parameters from the right side of the signature if not needed

    ### 2. DAT executions:
       - React to table changes in a DAT:
         NoNode.RegisterDatExec(NoNode.DatExecType.TableChange, dat_op, on_table_change_function)
         # callback signature depends on the event type, eg.: def on_table_change_function(dat: DAT):
       - Handle cell value changes:
         NoNode.RegisterDatExec(NoNode.DatExecType.CellChange, dat_op, on_cell_change_function)
         # callback signature depends on the event type, eg.: def on_cell_change_function(dat: DAT, cells: list[Cell], prev: Cell):

    ### 3. Keyboard shortcuts:
       - Register a keyboard shortcut:
         NoNode.RegisterKeyboardShortcut('ctrl.k', onKeyboardShortcut)
         # callback signature: def onKeyboardShortcut():

    > Note: relevant operators are marked with a color to make them easier to identify.

    These examples demonstrate how NoNode can be used to centralize and simplify event handling in TouchDesigner projects.
    '''

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
    
    CHOP_EXEC_MAP: Dict[ChopExecType, COMP] = {
        ChopExecType.ValueChange: CHOP_VALUECHANGE_EXEC,
        ChopExecType.OffToOn: CHOP_OFFTOON_EXEC,
        ChopExecType.OnToOff: CHOP_ONTOOFF_EXEC,
        ChopExecType.WhileOn: CHOP_WHILEON_EXEC,
        ChopExecType.WhileOff: CHOP_WHILEOFF_EXEC
    }

    DAT_EXEC_MAP: Dict[DatExecType, COMP] = {
        DatExecType.TableChange: DAT_TABLECHANGE_EXEC,
        DatExecType.RowChange: DAT_ROWCHANGE_EXEC,
        DatExecType.ColChange: DAT_COLCHANGE_EXEC,
        DatExecType.CellChange: DAT_CELLCHANGE_EXEC,
        DatExecType.SizeChange: DAT_SIZECHANGE_EXEC
    }

    CHOPEXEC_CALLBACKS: TDStoreTools.DependDict[ChopExecType, dict[CHOP, dict[str, Callable]]] = TDStoreTools.DependDict()
    DATEXEC_CALLBACKS: TDStoreTools.DependDict[DatExecType, dict[DAT, Callable]] = TDStoreTools.DependDict()
    KEYBOARD_CALLBACKS: TDStoreTools.DependDict[str, Callable] = TDStoreTools.DependDict()
    CHOPEXEC_IS_ENABLED: bool = False
    DATEXEC_IS_ENABLED: bool = False
    KEYBOARD_IS_ENABLED: bool = False

    # Add these class variables after other similar declarations
    PAR_VALUECHANGE_EXEC: DAT = op('extParExecNoNodeValueChange')
    PAR_VALUESCHANGED_EXEC: DAT = op('extParExecNoNodeValuesChanged')
    PAR_ONPULSE_EXEC: DAT = op('extParExecNoNodeOnPulse')

    PAR_EXECS: list[DAT] = [PAR_VALUECHANGE_EXEC, PAR_VALUESCHANGED_EXEC, PAR_ONPULSE_EXEC]

    PAR_EXEC_MAP: Dict[ParExecType, COMP] = {
        ParExecType.ValueChange: PAR_VALUECHANGE_EXEC,
        ParExecType.OnPulse: PAR_ONPULSE_EXEC
    }

    PAREXEC_CALLBACKS: TDStoreTools.DependDict[ParExecType, dict[Union[Par, str], Callable]] = TDStoreTools.DependDict()
    PAREXEC_IS_ENABLED: bool = False

    # Update ALL_EXECS to include PAR_EXECS
    ALL_EXECS: list[DAT] = CHOP_EXECS + DAT_EXECS + PAR_EXECS + [KEYBOARD_EXEC]
    EXT_OWNER_COMP: COMP = None

    @classmethod
    def Init(cls, ownerComp, enable_chopexec: bool = True, enable_datexec: bool = True, 
             enable_keyboard_shortcuts: bool = True, enable_parexec: bool = True) -> None:
        """Initialize the NoNode functionality."""
        cls.EXT_OWNER_COMP = ownerComp
        cls.CHOPEXEC_IS_ENABLED = enable_chopexec
        cls.DATEXEC_IS_ENABLED = enable_datexec
        cls.KEYBOARD_IS_ENABLED = enable_keyboard_shortcuts
        cls.CHOPEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.DATEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.KEYBOARD_CALLBACKS = TDStoreTools.DependDict()
        cls.PAREXEC_IS_ENABLED = enable_parexec
        cls.PAREXEC_CALLBACKS = TDStoreTools.DependDict()
        
        cls.__setOwnerCompToDocked(ownerComp)

        # Disable all execute operators by default
        for exec in cls.ALL_EXECS:
            if exec is not None:
                exec.par.active = False

        if enable_chopexec:
            cls.EnableChopExec()
        else:
            cls.DisableChopExec()

        if enable_datexec:
            cls.EnableDatExec()
        else:
            cls.DisableDatExec()

        if enable_keyboard_shortcuts:
            cls.EnableKeyboardShortcuts()
        else:
            cls.DisableKeyboardShortcuts()

        if enable_parexec:
            cls.EnableParExec()
        else:
            cls.DisableParExec()

    @classmethod
    def __setOwnerCompToDocked(cls, ownerComp: COMP) -> None:
        for _op in me.docked:
            if hasattr(_op.par, 'ops'):
                _op.par.ops.val = ownerComp
            if hasattr(_op.par, 'op'):
                _op.par.op.val = ownerComp

    ### CHOP and DAT Exec ###

    @classmethod       
    def EnableChopExec(cls) -> None:
        """Enable chopExec handling."""
        cls.CHOPEXEC_IS_ENABLED = True

    @classmethod
    def EnableDatExec(cls) -> None:
        """Enable datExec handling."""
        cls.DATEXEC_IS_ENABLED = True

    @classmethod
    def DisableChopExec(cls, event_type: ChopExecType = None) -> None:
        """Disable chopExec handling for a specific event type or all event types."""
        if event_type is None:
            # disable all active operators
            for chop_exec in cls.CHOP_EXECS:
                chop_exec.par.active = False
        elif event_type in cls.CHOP_EXEC_MAP:
            cls.CHOP_EXEC_MAP[event_type].par.active = False

    @classmethod
    def DisableDatExec(cls, event_type: DatExecType = None) -> None:
        """Disable datExec handling for a specific event type or all event types."""
        if event_type is None:
            # disable all active operators
            for dat_exec in cls.DAT_EXECS:
                dat_exec.par.active = False
        elif event_type in cls.DAT_EXEC_MAP:
            cls.DAT_EXEC_MAP[event_type].par.active = False

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
        if event_type not in cls.CHOPEXEC_CALLBACKS.getRaw():
            cls.CHOPEXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.CHOPEXEC_CALLBACKS.getDependency(event_type)
        if chop not in current_callbacks.val:
            current_callbacks.val[chop] = {}
            cls.__markOperatorAsWatched(chop)

        if isinstance(channels, str):
            channels = re.split(r'[,\s]+', channels.strip())
        for channel in channels:
            current_callbacks.val[chop][channel] = callback
        cls.CHOPEXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Enable the appropriate docked operator based on the event type
        if event_type in cls.CHOP_EXEC_MAP:
            cls.CHOP_EXEC_MAP[event_type].par.active = True

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
        if event_type not in cls.DATEXEC_CALLBACKS.getRaw():
            cls.DATEXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.DATEXEC_CALLBACKS.getDependency(event_type)
        if dat not in current_callbacks.val:
            current_callbacks.val[dat] = callback
            cls.__markOperatorAsWatched(dat)
        cls.DATEXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Enable the appropriate docked operator based on the event type
        if event_type in cls.DAT_EXEC_MAP:
            cls.DAT_EXEC_MAP[event_type].par.active = True

    @classmethod
    def DeregisterChopExec(cls, event_type: ChopExecType, chop: CHOP = None, channels: Union[str, List[str]] = None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (ChopExecType): The event type to deregister.
            chop (CHOP, optional): The CHOP operator to deregister the callback for. If None, deregisters all CHOPs for the event type.
            channels (Union[str, List[str]], optional): The channel(s) to deregister. Can be a string (single channel, comma/space-separated list, or wildcard pattern) or a list of strings. If None, deregisters all channels for the specified CHOP.
        """
        if event_type in cls.CHOPEXEC_CALLBACKS:
            if chop is None:
                for registered_chop in cls.CHOPEXEC_CALLBACKS[event_type]:
                    cls.__checkAndResetOperatorColor(registered_chop)
                del cls.CHOPEXEC_CALLBACKS[event_type]
            elif chop in cls.CHOPEXEC_CALLBACKS[event_type]:
                if channels is None:
                    del cls.CHOPEXEC_CALLBACKS[event_type][chop]
                    cls.__checkAndResetOperatorColor(chop)
                else:
                    if isinstance(channels, str):
                        channels = re.split(r'[,\s]+', channels.strip())
                    for channel in channels:
                        for registered_channel in list(cls.CHOPEXEC_CALLBACKS[event_type][chop].keys()):
                            if channel == '*' or tdu.match(channel, [registered_channel]):
                                del cls.CHOPEXEC_CALLBACKS[event_type][chop][registered_channel]
                
                if not cls.CHOPEXEC_CALLBACKS[event_type][chop]:
                    del cls.CHOPEXEC_CALLBACKS[event_type][chop]
                    cls.__checkAndResetOperatorColor(chop)
            
            if not cls.CHOPEXEC_CALLBACKS[event_type]:
                del cls.CHOPEXEC_CALLBACKS[event_type]
            # check if there are any callbacks left for this event type if not disable the operator
            if event_type in cls.CHOPEXEC_CALLBACKS:
                for chop in cls.CHOPEXEC_CALLBACKS[event_type]:
                    if cls.CHOPEXEC_CALLBACKS[event_type][chop]:
                        return
                cls.DisableChopExec(event_type)

    @classmethod
    def DeregisterDatExec(cls, event_type: DatExecType, dat: DAT = None) -> None:
        """
        Deregister a datExec callback

        Args:
            event_type (DatExecType): The event type to deregister.
            dat (DAT, optional): The DAT operator to deregister the callback for. If None, deregisters all DATs for the event type.
        """
        if event_type in cls.DATEXEC_CALLBACKS:
            if dat is None:
                for registered_dat in cls.DATEXEC_CALLBACKS[event_type]:
                    cls.__checkAndResetOperatorColor(registered_dat)
                del cls.DATEXEC_CALLBACKS[event_type]
            elif dat in cls.DATEXEC_CALLBACKS[event_type]:
                del cls.DATEXEC_CALLBACKS[event_type][dat]
                cls.__checkAndResetOperatorColor(dat)
            
            if not cls.DATEXEC_CALLBACKS[event_type]:
                del cls.DATEXEC_CALLBACKS[event_type]
                cls.DisableDatExec(event_type)

    @classmethod
    def OnChopExec(cls, event_type: ChopExecType, channel: Channel, sampleIndex: int, val: float, prev: float) -> None:
        """Handle chopExec events."""
        if not cls.CHOPEXEC_IS_ENABLED:
            return

        def execute_callback(callback):
            arg_count = callback.__code__.co_argcount
            if arg_count == 1:
                callback()
            elif arg_count == 2:
                callback(val)
            elif arg_count == 3:
                callback(channel, val)
            elif arg_count == 4:
                callback(channel, sampleIndex, val)
            elif arg_count == 5:
                callback(channel, sampleIndex, val, prev)
        chop = channel.owner

        # execute the callback for the channel if it matches the event type
        if event_type in cls.CHOPEXEC_CALLBACKS:
            callbacks = cls.CHOPEXEC_CALLBACKS[event_type].get(chop, {})
            executed_callbacks = set() # to avoid executing the same callback multiple times for the same channel
            for ch, callback in callbacks.items():
                channel_names = ch.split() if ch != '*' else ['*']
                for channel_name in channel_names:
                    if (channel_name == '*' or tdu.match(channel_name, [channel.name])) and (channel.name, callback) not in executed_callbacks:
                        execute_callback(callback)
                        executed_callbacks.add((channel.name, callback))
                        break  # Exit the inner loop after executing the callback

    @classmethod
    def OnDatExec(cls, event_type: DatExecType, dat: DAT, rows: int = None, cols: int = None, cells: list[Cell] = None, prev = None) -> None:
        """Handle datExec events."""
        if not cls.DATEXEC_IS_ENABLED:
            return

        if event_type in cls.DATEXEC_CALLBACKS and dat in cls.DATEXEC_CALLBACKS[event_type]:
            callback = cls.DATEXEC_CALLBACKS[event_type][dat]
            arg_count = callback.__code__.co_argcount
            if arg_count == 1:
                callback()
            elif arg_count == 2:
                callback(dat)
            elif arg_count == 3:
                if event_type == cls.DatExecType.RowChange:
                    callback(dat, rows)
                elif event_type == cls.DatExecType.ColChange:
                    callback(dat, cols)
                elif event_type == cls.DatExecType.CellChange:
                    callback(dat, cells)
            elif arg_count == 4:
                callback(dat, cells, prev)


    ### Keyboard Shortcuts ###

    @classmethod
    def EnableKeyboardShortcuts(cls) -> None:
        """Enable keyboard shortcut handling."""
        cls.KEYBOARD_IS_ENABLED = True
        cls.KEYBOARD_EXEC.par.active = True

    @classmethod
    def DisableKeyboardShortcuts(cls) -> None:
        """Disable keyboard shortcut handling."""
        cls.KEYBOARD_IS_ENABLED = False
        cls.KEYBOARD_EXEC.par.active = False

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
        cls.KEYBOARD_CALLBACKS[shortcut] = callback

    @classmethod
    def UnregisterKeyboardShortcut(cls, shortcut: str) -> None:
        """Unregister a keyboard shortcut."""
        cls.KEYBOARD_CALLBACKS.pop(shortcut, None)


    @classmethod
    def OnKeyboardShortcut(cls, shortcut: str) -> None:
        """Handle keyboard shortcut events."""
        if cls.KEYBOARD_IS_ENABLED and shortcut in cls.KEYBOARD_CALLBACKS:
            cls.KEYBOARD_CALLBACKS[shortcut]()

    @classmethod
    def __markOperatorAsWatched(cls, _op: OP) -> None:
        """Mark an operator as watched by changing its color."""
        _op.color = cls.MARK_COLOR

    @classmethod
    def __resetOperatorColor(cls, _op: OP) -> None:
        """Reset an operator's color to the default."""
        _op.color = (0.55, 0.55, 0.55) # td default color, probably available somewhere in the TD API/vars

    @classmethod
    def __checkAndResetOperatorColor(cls, _op: OP) -> None:
        """Check if an operator is still registered for any event type, and reset its color if not."""
        for event_type in cls.CHOPEXEC_CALLBACKS.getRaw().keys() | cls.DATEXEC_CALLBACKS.getRaw().keys():
            if _op in cls.CHOPEXEC_CALLBACKS.getRaw().get(event_type, {}) or _op in cls.DATEXEC_CALLBACKS.getRaw().get(event_type, {}):
                return
        cls.__resetOperatorColor(_op)

    @classmethod
    def SetMarkColor(cls, color: tuple[float, float, float]) -> None:
        """Set the mark color."""
        cls.MARK_COLOR = color
        # list all registered operators (chops and dats) and update their color
        for event_type in cls.CHOPEXEC_CALLBACKS.getRaw().keys() | cls.DATEXEC_CALLBACKS.getRaw().keys():
            for _op in cls.CHOPEXEC_CALLBACKS.getRaw().get(event_type, {}).keys() | cls.DATEXEC_CALLBACKS.getRaw().get(event_type, {}).keys():
                _op.color = cls.MARK_COLOR

    ### Parameter Exec ###

    @classmethod
    def EnableParExec(cls) -> None:
        """Enable parameter execute handling."""
        cls.PAREXEC_IS_ENABLED = True

    @classmethod
    def DisableParExec(cls, event_type: ParExecType = None) -> None:
        """Disable parameter execute handling for a specific event type or all event types."""
        if event_type is None:
            for par_exec in cls.PAR_EXECS:
                par_exec.par.active = False
        elif event_type in cls.PAR_EXEC_MAP:
            cls.PAR_EXEC_MAP[event_type].par.active = False

    @classmethod
    def RegisterParExec(cls, event_type: ParExecType, parameter: Union[Par, str], callback: Callable) -> None:
        """
        Register a parameter execute callback.

        Args:
            event_type (ParExecType): The type of event to listen for.
            parameter (Union[Par, str]): The parameter to watch. Can be a Par object or a string in format 'op/parameter'.
            callback (Callable): The callback function to be called on parameter execution.

        Example:
            def my_callback(par, prev):
                print(f"Parameter {par} changed from {prev} to {par.eval()}")
            
            # Using Par object
            NoNode.RegisterParExec(ParExecType.ValueChange, op('base1').par.v, my_callback)
            # Using string reference
            NoNode.RegisterParExec(ParExecType.ValueChange, 'base1/v', my_callback)
        """
        if event_type not in cls.PAREXEC_CALLBACKS.getRaw():
            cls.PAREXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.PAREXEC_CALLBACKS.getDependency(event_type)
        
        # convert string parameter reference to Par object
        if isinstance(parameter, str):
            if not hasattr(cls.EXT_OWNER_COMP.par, parameter):
                return
            parameter = cls.EXT_OWNER_COMP.par[parameter]
            
        # mark the operator
        #cls.__markOperatorAsWatched(parameter.owner)

        current_callbacks.val[parameter] = callback
        cls.PAREXEC_CALLBACKS.setItem(event_type, current_callbacks)

        if event_type in cls.PAR_EXEC_MAP:
            cls.PAR_EXEC_MAP[event_type].par.active = True

    @classmethod
    def DeregisterParExec(cls, event_type: ParExecType, parameter: Union[Par, str] = None) -> None:
        """
        Deregister a parameter execute callback.

        Args:
            event_type (ParExecType): The event type to deregister.
            parameter (Union[Par, str], optional): The parameter to deregister. If None, deregisters all parameters for the event type.
        """
        if event_type not in cls.PAREXEC_CALLBACKS.getRaw():
            return

        current_callbacks = cls.PAREXEC_CALLBACKS.getDependency(event_type)

        if parameter is None:
            # Deregister all callbacks for this event type
            cls.PAREXEC_CALLBACKS.setItem(event_type, {}, raw=True)
            cls.DisableParExec(event_type)
            return

        # Convert string parameter reference to Par object if needed
        if isinstance(parameter, str):
            if not hasattr(cls.EXT_OWNER_COMP.par, parameter):
                return
            parameter = cls.EXT_OWNER_COMP.par[parameter]

        if parameter in current_callbacks.val:
            del current_callbacks.val[parameter]
            cls.PAREXEC_CALLBACKS.setItem(event_type, current_callbacks)

            # Disable exec if no more callbacks
            if not current_callbacks.val:
                cls.DisableParExec(event_type)

    @classmethod
    def OnParExec(cls, event_type: ParExecType, parameter: Par, value = None, prev = None) -> None:
        """Handle parameter execute events."""

        if not cls.PAREXEC_IS_ENABLED:
            return

        if event_type not in cls.PAREXEC_CALLBACKS.getRaw():
            return

        # Create parameter string reference for matching
        par_str = parameter.name
        
        # Check both Par object and string reference
        callback = cls.PAREXEC_CALLBACKS[event_type].get(parameter) or \
                  cls.PAREXEC_CALLBACKS[event_type].get(par_str)
        
        if callback:
            arg_count = callback.__code__.co_argcount
            if arg_count == 1:
                callback()
            elif arg_count == 2:
                callback(value if event_type == cls.ParExecType.ValueChange else parameter)
            elif arg_count == 3:
                callback(parameter, value)
            elif arg_count == 4:
                callback(parameter, value, prev)
                    
