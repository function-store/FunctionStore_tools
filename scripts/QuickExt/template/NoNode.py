import re
import TDStoreTools
from typing import Callable, Dict, List, TypeAlias, Union, overload


class NoNode:
    """
    NoNode is a utility class that provides functionality for handling keyboard shortcuts
    and CHOP executions without the need for a specific node in TouchDesigner.
    """

    CHOPEXEC_CALLBACKS: TDStoreTools.DependDict[str, dict[CHOP, dict[str, Callable]]] = TDStoreTools.DependDict()
    KEYBOARD_SHORTCUTS: dict = {}
    
    KEYBOARD_IS_ENABLED: bool = False
    CHOPEXEC_IS_ENABLED: bool = False

    @classmethod
    def Init(cls, enable_chopexec: bool = True, enable_keyboard_shortcuts: bool = True) -> None:
        """Initialize the NoNode functionality."""
        cls.CHOPEXEC_IS_ENABLED = enable_chopexec
        cls.KEYBOARD_IS_ENABLED = enable_keyboard_shortcuts
        cls.CHOPEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.KEYBOARD_SHORTCUTS = {}

        # Disable all CHOP execute operators by default
        for _docked in me.docked:
            if any(tag in _docked.tags for tag in ['extChopValueExec', 'extChopOffToOnExec', 'extChopWhileOnExec', 'extChopWhileOffExec']):
                _docked.par.active = False

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
        # Note: We don't enable any specific operators here anymore

    @classmethod
    def DisableChopExec(cls) -> None:
        """Disable chopExec handling."""
        cls.CHOPEXEC_IS_ENABLED = False
        for _docked in me.docked:
            if any(tag in _docked.tags for tag in ['extChopValueExec', 'extChopOffToOnExec', 'extChopWhileOnExec', 'extChopWhileOffExec']):
                _docked.par.active = False

    @classmethod
    def RegisterChopExec(cls, event_type: str, chop: COMP, channels: str, callback: Callable) -> None:
        """
        Register a CHOP execute callback.

        Args:
            event_type (str): The type of event to listen for ('OffToOn', 'WhileOn', 'WhileOff', 'ValueChange').
            chop (CHOP): The CHOP operator to register the callback for.
            channels (str): The channel(s) to listen to. Use '*' for all channels.
            callback (Callable): The callback function to be called on CHOP execution.

        Example:
            def my_callback(event_type, channel, index, value, prev):
                print(f"Event: {event_type}, Channel {channel} at index {index} changed from {prev} to {value}")
            
            NoNode.RegisterChopExec('ValueChange', op('constant1'), '*', my_callback)
        """
        if event_type not in cls.CHOPEXEC_CALLBACKS.getRaw():
            cls.CHOPEXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.CHOPEXEC_CALLBACKS.getDependency(event_type)
        if chop not in current_callbacks.val:
            current_callbacks.val[chop] = {}
        current_callbacks.val[chop][channels] = callback
        cls.CHOPEXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Enable the appropriate docked operator based on the event type
        for _docked in me.docked:
            if 'extChopValueExec' in _docked.tags:
                if event_type == 'ValueChange':
                    _docked.par.active = True
            elif 'extChopOffToOnExec' in _docked.tags:
                if event_type == 'OffToOn':
                    _docked.par.active = True
            elif 'extChopWhileOnExec' in _docked.tags:
                if event_type == 'WhileOn':
                    _docked.par.active = True
            elif 'extChopWhileOffExec' in _docked.tags:
                if event_type == 'WhileOff':
                    _docked.par.active = True

    @classmethod
    def DeregisterChopExec(cls, event_type: str, chop: CHOP = None, channels: str = None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (str): The event type to deregister ('OffToOn', 'WhileOn', 'WhileOff', 'ValueChange').
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

    @classmethod
    def OnChopExec(cls, event_type: str, channel: Channel, sampleIndex: int, val: float, prev: float) -> None:
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