CustomParHelper: CustomParHelper = mod(next((d.name for d in me.docked if 'CustomParHelper' in d.tags)))
import re
import TDStoreTools
from typing import Callable, Dict, List, TypeAlias, Union, overload

class CustomParHelper:
    """
    Author: Dan Molnar aka Function Store (@function.str dan@functionstore.xyz) 2024

    CustomParHelper is a helper class that provides easy access to custom parameters
    of a COMP and simplifies the implementation of custom parameter callbacks in TouchDesigner extensions.

    Features:
    - Access custom parameters as properties
    - Simplified custom parameter callbacks
    - Support for sequence parameters
    - Support for parameter groups (parGroups)
    - Keyboard shortcuts handling
    - Configurable inclusion for properties and callbacks (by default all parameters are included)
    - Configurable exceptions for pages, properties, callbacks, and sequences

    Usage in your extension class:
    1. Import the CustomParHelper class:
       from utils import CustomParHelper
    
    2. Initialize in your extension's __init__ method as follows:
       CustomParHelper.Init(self, ownerComp)

       Full signature and optional parameters:
       CustomParHelper.Init(self, ownerComp, enable_properties: bool = True, enable_callbacks: bool = True, enable_parGroups: bool = True, expose_public: bool = False,
             par_properties: list[str] = ['*'], par_callbacks: list[str] = ['*'], 
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [], 
             enable_keyboard_shortcuts=False, enable_stubs: bool = False)

        Additional options:
            - enable_parGroups: If True, creates properties and methods for parGroups (default: True)
            - expose_public: If True, uses capitalized property and method names (e.g., Par, Eval instead of par, eval)
            - par_properties: List of parameter names to include in property creation, by default all parameters are included
            - par_callbacks: List of parameter names to include in callback handling, by default all parameters are included
            - except_properties: List of parameter names to exclude from property creation
            - except_callbacks: List of parameter names to exclude from callback handling
            - except_pages: List of parameter pages to exclude from property and callback handling
            - except_sequences: List of sequence names to exclude from property and callback handling
            - enable_keyboard_shortcuts: If True, enables keyboard shortcut handling with callbacks (default: False)
            - enable_stubs: If True, automatically creates and updates stubs for the extension (default: False) (thanks to AlphaMoonbase.berlin for Stubser)

    3. Access custom parameters as properties (if enable_properties=True (default)):
       - self.par<ParamName>: Access the parameter object
       - self.eval<ParamName>: Get the evaluated value of the parameter
       - self.parGroup<GroupName>: Access the parameter group object (if enable_parGroups=True (default))
       - self.evalGroup<GroupName>: Get the evaluated value of the parameter group (if enable_parGroups=True (default))
    > NOTE: to expose public properties, eg. self.Par<ParamName> instead of self.par<ParamName>, set expose_public=True in the Init function

    4. Implement callbacks (if enable_callbacks=True (default)):
       - For regular parameters:
         def onPar<ParamName>(self, _par, _val, _prev):
           # _par and _prev can be omitted if not needed

       - For pulse parameters:
         def onPar<PulseParamName>(self, _par):
           # _par can be omitted if not needed

       - For sequence blocks:
         def onSeq<SeqName>N(self, idx):

       - For sequence parameters:
         def onSeq<SeqName>N<ParName>(self, _par, idx, _val, _prev):
           # _par and _prev can be omitted if not needed

       - For parameter groups if enable_parGroups=True (default):
         def onParGroup<GroupName>(self, _parGroup, _val):
           # _parGroup can be omitted if not needed

    5. Handle keyboard shortcuts (if enable_keyboard_shortcuts=True (default is False)):
       - Enable keyboard shortcuts:
         CustomParHelper.Init(self, ownerComp, enable_keyboard_shortcuts=True)
       - Register a keyboard shortcut and its callback:
         CustomParHelper.RegisterKeyboardShortcut("ctrl.k", self.onKeyboardShortcut)
       - Implement the callback method:
         def onKeyboardShortcut(self):
           # This method will be called when the registered keyboard shortcut is pressed

    > NOTE: This class only works docked to an extension with the tag 'extTemplate' and 
      with the docked helper operators, which create the interface to the TouchDesigner environment.
      Note that the docked helpers are hidden by default.
    > NOTE: The reason this is implemented with static methods, is to omit the need to instantiate the class, providing a simpler interface (arguably).
    """
    EXCEPT_PAGES_STATIC: list[str] = ['Version Ctrl', 'About', 'Info']
    EXCEPT_PAGES: list[str] = EXCEPT_PAGES_STATIC
    EXCEPT_PROPS: list[str] = []
    EXCEPT_CALLBACKS: list[str] = []
    EXCEPT_SEQUENCES: list[str] = []
    PAR_PROPS: list[str] = ['*']
    PAR_CALLBACKS: list[str] = ['*']
    SEQUENCE_PATTERN: str = '(\\w+?)(\\d+)(.+)'
    IS_EXPOSE_PUBLIC: bool = False
    EXT_SELF = None
    STUBS_ENABLED: bool = False

    @classmethod
    def Init(cls, extension_self, ownerComp: COMP, enable_properties: bool=True, enable_callbacks: bool=True, enable_parGroups: bool=True, expose_public: bool=False, par_properties: list[str]=['*'], par_callbacks: list[str]=['*'], except_properties: list[str]=[], except_sequences: list[str]=[], except_callbacks: list[str]=[], except_pages: list[str]=[], enable_stubs: bool=False) -> None:
        """Initialize the CustomParHelper."""
        pass

    @classmethod
    def CustomParsAsProperties(cls, extension_self, ownerComp: COMP, enable_parGroups: bool=True) -> None:
        """Create properties for custom parameters."""
        pass

    @classmethod
    def EnableCallbacks(cls, enable_parGroups: bool=True) -> None:
        """Enable callbacks for custom parameters."""
        pass

    @classmethod
    def DisableCallbacks(cls) -> None:
        """Disable callbacks for custom parameters."""
        pass

    @classmethod
    def OnValueChange(cls, comp: COMP, par: Par, prev: Par) -> None:
        """Handle value change events for custom parameters."""
        pass

    @classmethod
    def OnPulse(cls, comp: COMP, par: Par) -> None:
        """Handle pulse events for custom parameters."""
        pass

    @classmethod
    def OnValuesChanged(cls, changes: list[tuple[Par, Par]]) -> None:
        """Handle value change events for ParGroups."""
        pass

    @classmethod
    def OnSeqValuesChanged(cls, changes: list[tuple[Par, Par]]) -> None:
        """Handle value change events for Sequence blocks."""
        pass

    @classmethod
    def EnableStubs(cls) -> None:
        """Enable stubs for the extension."""
        pass

    @classmethod
    def DisableStubs(cls) -> None:
        """Disable stubs for the extension."""
        pass

    @classmethod
    def UpdateStubs(cls) -> None:
        """Update the stubs for the extension."""
        pass

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
    def Init(cls, enable_chopexec: bool=True, enable_keyboard_shortcuts: bool=True) -> None:
        """Initialize the NoNode functionality."""
        pass

    @classmethod
    def EnableChopExec(cls) -> None:
        """Enable chopExec handling."""
        pass

    @classmethod
    def DisableChopExec(cls) -> None:
        """Disable chopExec handling."""
        pass

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
        pass

    @classmethod
    def DeregisterChopExec(cls, event_type: str, chop: CHOP=None, channels: str=None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (str): The event type to deregister ('OffToOn', 'WhileOn', 'WhileOff', 'ValueChange').
            chop (CHOP, optional): The CHOP operator to deregister the callback for. If None, deregisters all CHOPs for the event type.
            channels (str, optional): The channel(s) to deregister. If None, deregisters all channels for the specified CHOP.
        """
        pass

    @classmethod
    def OnChopExec(cls, event_type: str, channel: Channel, sampleIndex: int, val: float, prev: float) -> None:
        """Handle chopExec events."""
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
        """Register a keyboard shortcut and its callback."""
        pass

    @classmethod
    def UnregisterKeyboardShortcut(cls, shortcut: str) -> None:
        """Unregister a keyboard shortcut."""
        pass

    @classmethod
    def OnKeyboardShortcut(cls, shortcut: str) -> None:
        """Handle keyboard shortcut events."""
        pass