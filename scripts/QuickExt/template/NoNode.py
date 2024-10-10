import re
import TDStoreTools
from typing import Callable, Dict, List, TypeAlias, Union, overload
from enum import Enum, auto


class NoNode:
    """
    NoNode is a utility class that provides functionality for handling keyboard shortcuts
    and CHOP executions without the need for a specific node in TouchDesigner.
    """

    class ChopExecType(Enum):
        OffToOn = auto()
        WhileOn = auto()
        OnToOff = auto()
        WhileOff = auto()
        ValueChange = auto()
        
    CHOPVALUE_EXEC: COMP = op('extChopValueExec')
    CHOPOFFTOON_EXEC: COMP = op('extChopOffToOnExec')
    CHOPONTOOFF_EXEC: COMP = op('extChopOnToOffExec')
    CHOPWHILEON_EXEC: COMP = op('extChopWhileOnExec')
    CHOPWHILEOFF_EXEC: COMP = op('extChopWhileOffExec')

    CHOP_EXECS: list[COMP] = [CHOPVALUE_EXEC, CHOPOFFTOON_EXEC, CHOPWHILEON_EXEC, CHOPWHILEOFF_EXEC]
    CHOPEXEC_CALLBACKS: TDStoreTools.DependDict[ChopExecType, dict[CHOP, dict[str, Callable]]] = TDStoreTools.DependDict()

    CHOPEXEC_IS_ENABLED: bool = False

    ALL_EXECS: list[COMP] = CHOP_EXECS

    KEYBOARD_SHORTCUTS: dict = {}
    KEYBOARD_IS_ENABLED: bool = False

    CHOP_EXEC_MAP: Dict[ChopExecType, COMP] = {
        ChopExecType.ValueChange: CHOPVALUE_EXEC,
        ChopExecType.OffToOn: CHOPOFFTOON_EXEC,
        ChopExecType.WhileOn: CHOPWHILEON_EXEC,
        ChopExecType.WhileOff: CHOPWHILEOFF_EXEC
    }

    @classmethod
    def Init(cls, enable_chopexec: bool = True, enable_keyboard_shortcuts: bool = True) -> None:
        """Initialize the NoNode functionality."""
        cls.CHOPEXEC_IS_ENABLED = enable_chopexec
        cls.KEYBOARD_IS_ENABLED = enable_keyboard_shortcuts
        cls.CHOPEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.KEYBOARD_SHORTCUTS = {}

        # Disable all CHOP execute operators by default
        for exec in cls.ALL_EXECS:
            exec.par.active = False

        if enable_chopexec:
            cls.EnableChopExec()
        else:
            cls.DisableChopExec()

        if enable_keyboard_shortcuts:
            cls.EnableKeyboardShortcuts()
        else:
            cls.DisableKeyboardShortcuts()

    @classmethod       
    def EnableChopExec(cls) -> None:
        """Enable chopExec handling."""
        cls.CHOPEXEC_IS_ENABLED = True

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
                cls.DisableChopExec()

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
    def EnableKeyboardShortcuts(cls) -> None:
        """Enable keyboard shortcut handling."""
        cls.KEYBOARD_IS_ENABLED = True
        for _docked in me.docked:
            if 'extKeyboardin' in _docked.tags:
                _docked.par.active = True
                cls._UpdateKeyboardShortcuts()

    @classmethod
    def DisableKeyboardShortcuts(cls) -> None:
        """Disable keyboard shortcut handling."""
        cls.KEYBOARD_IS_ENABLED = False
        for _docked in me.docked:
            if 'extKeyboardin' in _docked.tags:
                _docked.par.active = False

    @classmethod
    def RegisterKeyboardShortcut(cls, shortcut: str, callback: callable) -> None:
        """Register a keyboard shortcut and its callback."""
        cls.KEYBOARD_SHORTCUTS[shortcut] = callback
        if cls.KEYBOARD_IS_ENABLED:
            cls._UpdateKeyboardShortcuts()

    @classmethod
    def UnregisterKeyboardShortcut(cls, shortcut: str) -> None:
        """Unregister a keyboard shortcut."""
        cls.KEYBOARD_SHORTCUTS.pop(shortcut, None)
        if cls.KEYBOARD_IS_ENABLED:
            cls._UpdateKeyboardShortcuts()

    @classmethod
    def _UpdateKeyboardShortcuts(cls) -> None:
        """Update the extKeyboardIn operator's shortcuts parameter."""
        for _docked in me.docked:
            if 'extKeyboardin' in _docked.tags:
                _docked.par.shortcuts = ' '.join(cls.KEYBOARD_SHORTCUTS.keys())

    @classmethod
    def OnKeyboardShortcut(cls, shortcut: str) -> None:
        """Handle keyboard shortcut events."""
        if cls.KEYBOARD_IS_ENABLED and shortcut in cls.KEYBOARD_SHORTCUTS:
            cls.KEYBOARD_SHORTCUTS[shortcut]()