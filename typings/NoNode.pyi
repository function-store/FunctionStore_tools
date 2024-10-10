import re
import TDStoreTools
from typing import Callable, Dict, List, TypeAlias, Union, overload
from enum import Enum, auto

class NoNode:
    """
    NoNode is a utility class that provides functionality for handling keyboard shortcuts,
    CHOP executions, and DAT executions without the need for a specific node in TouchDesigner.
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
    CHOP_VALUECHANGE_EXEC: COMP = op('extChopValueChangeExec')
    CHOP_OFFTOON_EXEC: COMP = op('extChopOffToOnExec')
    CHOP_ONTOOFF_EXEC: COMP = op('extChopOnToOffExec')
    CHOP_WHILEON_EXEC: COMP = op('extChopWhileOnExec')
    CHOP_WHILEOFF_EXEC: COMP = op('extChopWhileOffExec')
    DAT_TABLECHANGE_EXEC: COMP = op('extDatTableChangeExec')
    DAT_ROWCHANGE_EXEC: COMP = op('extDatRowChangeExec')
    DAT_COLCHANGE_EXEC: COMP = op('extDatColChangeExec')
    DAT_CELLCHANGE_EXEC: COMP = op('extDatCellChangeExec')
    DAT_SIZECHANGE_EXEC: COMP = op('extDatSizeChangeExec')
    KEYBOARD_EXEC: COMP = op('extKeyboardIn')
    CHOP_EXECS: list[COMP] = [CHOP_VALUECHANGE_EXEC, CHOP_OFFTOON_EXEC, CHOP_ONTOOFF_EXEC, CHOP_WHILEON_EXEC, CHOP_WHILEOFF_EXEC]
    DAT_EXECS: list[COMP] = [DAT_TABLECHANGE_EXEC, DAT_ROWCHANGE_EXEC, DAT_COLCHANGE_EXEC, DAT_CELLCHANGE_EXEC, DAT_SIZECHANGE_EXEC]
    CHOP_EXEC_MAP: Dict[ChopExecType, COMP] = {ChopExecType.ValueChange: CHOP_VALUECHANGE_EXEC, ChopExecType.OffToOn: CHOP_OFFTOON_EXEC, ChopExecType.WhileOn: CHOP_WHILEON_EXEC, ChopExecType.WhileOff: CHOP_WHILEOFF_EXEC}
    DAT_EXEC_MAP: Dict[DatExecType, COMP] = {DatExecType.TableChange: DAT_TABLECHANGE_EXEC, DatExecType.RowChange: DAT_ROWCHANGE_EXEC, DatExecType.ColChange: DAT_COLCHANGE_EXEC, DatExecType.CellChange: DAT_CELLCHANGE_EXEC, DatExecType.SizeChange: DAT_SIZECHANGE_EXEC}
    CHOPEXEC_CALLBACKS: TDStoreTools.DependDict[ChopExecType, dict[CHOP, dict[str, Callable]]] = TDStoreTools.DependDict()
    DATEXEC_CALLBACKS: TDStoreTools.DependDict[DatExecType, dict[DAT, Callable]] = TDStoreTools.DependDict()
    KEYBOARD_CALLBACKS: TDStoreTools.DependDict[str, Callable] = TDStoreTools.DependDict()
    CHOPEXEC_IS_ENABLED: bool = False
    DATEXEC_IS_ENABLED: bool = False
    KEYBOARD_IS_ENABLED: bool = False
    ALL_EXECS: list[COMP] = CHOP_EXECS + DAT_EXECS + [KEYBOARD_EXEC]

    @classmethod
    def Init(cls, enable_chopexec: bool=True, enable_datexec: bool=True, enable_keyboard_shortcuts: bool=True) -> None:
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
    def RegisterChopExec(cls, event_type: ChopExecType, chop: COMP, channels: str, callback: Callable) -> None:
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
    def DeregisterChopExec(cls, event_type: ChopExecType, chop: CHOP=None, channels: str=None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (ChopExecType): The event type to deregister.
            chop (CHOP, optional): The CHOP operator to deregister the callback for. If None, deregisters all CHOPs for the event type.
            channels (str, optional): The channel(s) to deregister. If None, deregisters all channels for the specified CHOP.
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
    def UnregisterKeyboardShortcut(cls, shortcut: str) -> None:
        """Unregister a keyboard shortcut."""
        pass

    @classmethod
    def OnKeyboardShortcut(cls, shortcut: str) -> None:
        """Handle keyboard shortcut events."""
        pass