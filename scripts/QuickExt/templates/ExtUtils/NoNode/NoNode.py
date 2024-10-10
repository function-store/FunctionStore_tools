import re
import TDStoreTools
from typing import Callable, Dict, List, TypeAlias, Union, overload
from enum import Enum, auto


class NoNode:
    """
    NoNode is a versatile utility class designed to enhance TouchDesigner workflows by providing a centralized system for managing various types of executions and callbacks without requiring dedicated nodes.

    Key features include:
    1. Keyboard shortcut handling: Easily define and manage custom keyboard shortcuts.
    2. CHOP executions: Handle different types of CHOP events (e.g., value changes, on/off states).
    3. DAT executions: Manage various DAT-related events (e.g., table, row, or cell changes).

    This class simplifies the process of setting up complex interactions and automations within TouchDesigner projects, 
    reducing clutter and improving organization. It's particularly useful for larger projects or when working with 
    multiple extensions that need to respond to similar events.

    Usage examples:
    0. Initialize the NoNode system in your extension:
       NoNode.Init(enable_chopexec=True, enable_datexec=True, enable_keyboard_shortcuts=True)

    1. CHOP executions:
       - Register a callback for CHOP value changes:
         NoNode.RegisterChopExec(NoNode.ChopExecType.ValueChange, chop_op, channel_name, callback_function)
         # callback signature: def on_value_change_function(channel: Channel, sampleIndex: int, val: float, prev: float):
         # can omit parameters from the right side of the signature if not needed
       - Handle CHOP state changes:
         NoNode.RegisterChopExec(NoNode.ChopExecType.OffToOn, chop_op, channel_name, on_activate_function)
         # callback signature: def on_activate_function(channel: Channel, sampleIndex: int, val: float, prev: float):
         # can omit parameters from the right side of the signature if not needed

    2. DAT executions:
       - React to table changes in a DAT:
         NoNode.RegisterDatExec(NoNode.DatExecType.TableChange, dat_op, on_table_change_function)
         # callback signature depends on the event type, eg.: def on_table_change_function(dat: DAT):
       - Handle cell value changes:
         NoNode.RegisterDatExec(NoNode.DatExecType.CellChange, dat_op, on_cell_change_function)
         # callback signature depends on the event type, eg.: def on_cell_change_function(dat: DAT, cells: list[Cell], prev: Cell):

    3. Keyboard shortcuts:
       - Register a keyboard shortcut:
         NoNode.RegisterKeyboardShortcut('ctrl.k', onKeyboardShortcut)
         # callback signature: def onKeyboardShortcut():

    These examples demonstrate how NoNode can be used to centralize and simplify event handling in TouchDesigner projects.
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

    ALL_EXECS: list[DAT] = CHOP_EXECS + DAT_EXECS + [KEYBOARD_EXEC]

    @classmethod
    def Init(cls, enable_chopexec: bool = True, enable_datexec: bool = True, enable_keyboard_shortcuts: bool = True) -> None:
        """Initialize the NoNode functionality."""
        cls.CHOPEXEC_IS_ENABLED = enable_chopexec
        cls.DATEXEC_IS_ENABLED = enable_datexec
        cls.KEYBOARD_IS_ENABLED = enable_keyboard_shortcuts
        cls.CHOPEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.DATEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.KEYBOARD_CALLBACKS = TDStoreTools.DependDict()

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
    def RegisterChopExec(cls, event_type: ChopExecType, chop: CHOP, channels: str, callback: Callable) -> None:
        """
        Register a CHOP execute callback.

        Args:
            event_type (ChopExecType): The type of event to listen for.
            chop (CHOP): The CHOP operator to register the callback for.
            channels (str): The channel(s) to listen to. Use '*' for all channels.
            callback (Callable): The callback function to be called on CHOP execution.

        Example:
            def my_callback(event_type, channel, index, value, prev):
                print(f"Event: {event_type}, Channel {channel} at index {index} changed from {prev} to {value}")
            
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), '*', my_callback)
        """
        if event_type not in cls.CHOPEXEC_CALLBACKS.getRaw():
            cls.CHOPEXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.CHOPEXEC_CALLBACKS.getDependency(event_type)
        if chop not in current_callbacks.val:
            current_callbacks.val[chop] = {}
        current_callbacks.val[chop][channels] = callback
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
        current_callbacks.val[dat] = callback
        cls.DATEXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Enable the appropriate docked operator based on the event type
        if event_type in cls.DAT_EXEC_MAP:
            cls.DAT_EXEC_MAP[event_type].par.active = True

    @classmethod
    def DeregisterChopExec(cls, event_type: ChopExecType, chop: CHOP = None, channels: str = None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (ChopExecType): The event type to deregister.
            chop (CHOP, optional): The CHOP operator to deregister the callback for. If None, deregisters all CHOPs for the event type.
            channels (str, optional): The channel(s) to deregister. If None, deregisters all channels for the specified CHOP.
        """
        if event_type in cls.CHOPEXEC_CALLBACKS:
            if chop is None:
                del cls.CHOPEXEC_CALLBACKS[event_type]
            elif chop in cls.CHOPEXEC_CALLBACKS[event_type]:
                if channels is None:
                    del cls.CHOPEXEC_CALLBACKS[event_type][chop]
                else:
                    cls.CHOPEXEC_CALLBACKS[event_type][chop].pop(channels, None)
                
                if not cls.CHOPEXEC_CALLBACKS[event_type][chop]:
                    del cls.CHOPEXEC_CALLBACKS[event_type][chop]
            
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
                del cls.DATEXEC_CALLBACKS[event_type]
            elif dat in cls.DATEXEC_CALLBACKS[event_type]:
                del cls.DATEXEC_CALLBACKS[event_type][dat]
            
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
        if event_type in cls.CHOPEXEC_CALLBACKS:
            callbacks = cls.CHOPEXEC_CALLBACKS[event_type].get(chop, {})
            for ch, callback in callbacks.items():
                if ch == '*' or channel.name == ch:
                    execute_callback(callback)

    @classmethod
    def OnDatExec(cls, event_type: DatExecType, dat: DAT, rows: int = None, cols: int = None, cells: list[Cell] = None, prev = None) -> None:
        """Handle datExec events."""
        debug('hejj')
        debug(cls.DATEXEC_IS_ENABLED)
        if not cls.DATEXEC_IS_ENABLED:
            return

        if event_type in cls.DATEXEC_CALLBACKS and dat in cls.DATEXEC_CALLBACKS[event_type]:
            callback = cls.DATEXEC_CALLBACKS[event_type][dat]
            arg_count = callback.__code__.co_argcount
            debug(f'wouldcall {callback} with {arg_count} args')
            if arg_count == 1:
                callback()
            elif arg_count == 2:
                callback(dat)
            elif arg_count == 3:
                if event_type == DatExecType.RowChange:
                    callback(dat, rows)
                elif event_type == DatExecType.ColumnChange:
                    callback(dat, cols)
                elif event_type == DatExecType.CellChange:
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