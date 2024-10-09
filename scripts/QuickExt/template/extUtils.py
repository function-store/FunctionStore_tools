import re
import TDStoreTools
from typing import Callable, Dict, List, TypeAlias, Union, overload

class CustomParHelper:
    '''
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
    '''
    
    EXCEPT_PAGES_STATIC: list[str]  = ['Version Ctrl', 'About', 'Info']
    EXCEPT_PAGES: list[str] = EXCEPT_PAGES_STATIC
    EXCEPT_PROPS: list[str] = []
    EXCEPT_CALLBACKS: list[str] = []
    EXCEPT_SEQUENCES: list[str] = []
    PAR_PROPS: list[str] = ['*']
    PAR_CALLBACKS: list[str] = ['*']
    SEQUENCE_PATTERN: str = r'(\w+?)(\d+)(.+)'
    IS_EXPOSE_PUBLIC: bool = False
    EXT_SELF = None
    STUBS_ENABLED: bool = False

    @classmethod
    def Init(cls, extension_self, ownerComp: COMP, enable_properties: bool = True, enable_callbacks: bool = True, enable_parGroups: bool = True, expose_public: bool = False,
             par_properties: list[str] = ['*'], par_callbacks: list[str] = ['*'], 
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [],
             enable_stubs: bool = False) -> None:
        """Initialize the CustomParHelper."""
        cls.EXT_SELF = extension_self
        cls.IS_EXPOSE_PUBLIC = expose_public
        cls.PAR_PROPS = par_properties
        cls.PAR_CALLBACKS = par_callbacks
        cls.EXCEPT_PAGES = cls.EXCEPT_PAGES_STATIC + except_pages
        cls.EXCEPT_PROPS = except_properties
        cls.EXCEPT_CALLBACKS = except_callbacks
        cls.EXCEPT_SEQUENCES = except_sequences

        me_me: textDAT = me # just to have autocomplete on this
        for _docked in me_me.docked:
            if 'extDatExec' in _docked.tags:
                _docked.par.active = enable_properties

        if enable_properties:
            cls.CustomParsAsProperties(extension_self, ownerComp, enable_parGroups=enable_parGroups)

        if enable_callbacks:
            cls.EnableCallbacks(enable_parGroups)
        else:
            cls.DisableCallbacks()

        if enable_stubs:
            cls.EnableStubs()
        else:
            cls.DisableStubs()

    @classmethod
    def CustomParsAsProperties(cls, extension_self, ownerComp: COMP, enable_parGroups: bool = True) -> None:
        """Create properties for custom parameters."""
        for _par in ownerComp.customPars:
            if (not tdu.match(' '.join(cls.PAR_PROPS), [_par.name]) or
                tdu.match(' '.join(cls.EXCEPT_PAGES), [_par.page.name]) or
                tdu.match(' '.join(cls.EXCEPT_PROPS), [_par.name])):
                continue
            # Check if the parameter belongs to an excepted sequence
            sequence_match = re.match(cls.SEQUENCE_PATTERN, _par.name)
            if sequence_match and sequence_match.group(1) in cls.EXCEPT_SEQUENCES:
                continue

            cls._create_propertyEval(extension_self, ownerComp, _par.name, enable_parGroups=enable_parGroups)
            cls._create_propertyPar(extension_self, ownerComp, _par.name, enable_parGroups=enable_parGroups)


    @classmethod
    def _create_propertyEval(cls, extension_self, owner_comp: COMP, Parname: str, enable_parGroups: bool = True) -> None:
        """Create a property for the evaluated value of a parameter."""
        def getter(instance):
            return getattr(owner_comp.par, Parname).eval()
        def getter_group(instance):
            return getattr(owner_comp.parGroup, Parname[:-1]).eval()

        property_name = f'{"Eval" if cls.IS_EXPOSE_PUBLIC else "eval"}{Parname}'
        setattr(extension_self.__class__, property_name, property(getter))
        
        if enable_parGroups and cls.__isParGroup(getattr(owner_comp.par, Parname)):
            setattr(extension_self.__class__, f'{"EvalGroup" if cls.IS_EXPOSE_PUBLIC else "evalGroup"}{Parname[:-1]}', property(getter_group))
        

    @classmethod
    def _create_propertyPar(cls, extension_self, owner_comp: COMP, Parname: str, enable_parGroups: bool = True) -> None:
        """Create a property for the parameter object."""
        def getter(instance):
            return getattr(owner_comp.par, Parname)
        def getter_group(instance):
            return getattr(owner_comp.parGroup, Parname[:-1])

        property_name = f'{"Par" if cls.IS_EXPOSE_PUBLIC else "par"}{Parname}'
        setattr(extension_self.__class__, property_name, property(getter))
        
        if enable_parGroups and cls.__isParGroup(getattr(owner_comp.par, Parname)):
            setattr(extension_self.__class__, f'{"ParGroup" if cls.IS_EXPOSE_PUBLIC else "parGroup"}{Parname[:-1]}', property(getter_group))


    @classmethod
    def EnableCallbacks(cls, enable_parGroups: bool = True) -> None:
        """Enable callbacks for custom parameters."""
        for _docked in me.docked:
            if 'extParExec' in _docked.tags or ('extParGroupExec' in _docked.tags and enable_parGroups):
                _docked.par.active = True


    @classmethod
    def DisableCallbacks(cls) -> None:
        """Disable callbacks for custom parameters."""
        for _docked in me.docked:
            if 'extParExec' in _docked.tags or 'extParGroupExec' in _docked.tags:
                _docked.par.active = False


    @classmethod
    def OnValueChange(cls, comp: COMP, par: Par, prev: Par) -> None:
        """Handle value change events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters

        comp = cls.EXT_SELF # a bit hacky to be able to call non-exposed methods too

        # check if we are a sequence parameter first
        match = re.match(cls.SEQUENCE_PATTERN, par.name)
        if match:
            sequence_name, sequence_index, parameter_name = match.groups()
            sequence_index = int(sequence_index)
            if sequence_name in cls.EXCEPT_SEQUENCES:
                return
            method_name = f'{"OnSeq" if cls.IS_EXPOSE_PUBLIC else "onSeq"}{sequence_name}N{parameter_name}'
            if hasattr(comp, method_name):
                method = getattr(comp, method_name)
                arg_count = method.__code__.co_argcount
                if arg_count == 2:
                    method(sequence_index)
                if arg_count == 3:
                    method(sequence_index, par.eval())
                elif arg_count == 4:
                    method(par, sequence_index, par.eval())
                elif arg_count == 5:
                    method(par, sequence_index, par.eval(), prev)
        elif hasattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{par.name}'):
            method = getattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{par.name}')
            arg_count = method.__code__.co_argcount  # Total number of arguments
            if arg_count == 2:
                method(par.eval())
            elif arg_count == 3:
                method(par, par.eval())
            elif arg_count == 4:
                method(par, par.eval(), prev)
                

    @classmethod
    def OnPulse(cls, comp: COMP, par: Par) -> None:
        """Handle pulse events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters
        
        comp = cls.EXT_SELF # a bit hacky to be able to call non-exposed methods too

        # check if we are a sequence parameter first
        match = re.match(cls.SEQUENCE_PATTERN, par.name)
        if match:
            sequence_name, sequence_index, parameter_name = match.groups()
            sequence_index = int(sequence_index)
            if sequence_name in cls.EXCEPT_SEQUENCES:
                return
            method_name = f'{"OnSeq" if cls.IS_EXPOSE_PUBLIC else "onSeq"}{sequence_name}N{parameter_name}'
            if hasattr(comp, method_name):
                method = getattr(comp, method_name)
                arg_count = method.__code__.co_argcount
                if arg_count == 2:
                    method(sequence_index)
                elif arg_count == 3:
                    method(sequence_index, par)
        elif hasattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{par.name}'):
            method = getattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{par.name}')
            arg_count = method.__code__.co_argcount  # Total number of arguments
            if arg_count == 1:
                method()
            elif arg_count == 2:
                method(par)


    @classmethod
    def OnValuesChanged(cls, changes: list[tuple[Par, Par]]) -> None:
        """Handle value change events for ParGroups."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters
        parGroupsCalled = []
        for change in changes:
            _par = change[0]
            # _prev = change[1]
            # _comp = _par.owner
            _comp = cls.EXT_SELF # a bit hacky to be able to call non-exposed methods too
            # handle sequence exceptions
            # check if we are a sequence parameter first
            match = re.match(cls.SEQUENCE_PATTERN, _par.name)
            if match:
                sequence_name, sequence_index, parameter_name = match.groups()
                sequence_index = int(sequence_index)
                if sequence_name in cls.EXCEPT_SEQUENCES:
                    continue
            if cls.__isParGroup(_par):
                if _par.name[:-1] not in parGroupsCalled: # prevent calling parGroups multiple times
                    parGroupsCalled.append(_par.name[:-1])
                else:
                    continue
                # fetch the parGroup and ParName if it's a parGroup
                match = re.match(r'(\w+)(.)', _par.name)
                if match:
                    ParGroup, ParName = match.groups()
                    _par = _comp.ownerComp.parGroup[ParGroup] 
                    method_name = f'{"OnParGroup" if cls.IS_EXPOSE_PUBLIC else "onParGroup"}{ParGroup}'
                    if hasattr(_comp, method_name):
                        method = getattr(_comp, method_name)
                        arg_count = method.__code__.co_argcount
                        if arg_count == 2:
                            method(_par.eval())
                        elif arg_count == 3:
                            method(_par, _par.eval())

    @classmethod
    def OnSeqValuesChanged(cls, changes: list[tuple[Par, Par]]) -> None:
        """Handle value change events for Sequence blocks."""
        seqsCalled = []
        for change in changes:
            _par = change[0]
            # _prev = change[1]
            # _comp = _par.owner
            _comp = cls.EXT_SELF # a bit hacky to be able to call non-exposed methods too
            # handle sequence exceptions
            # check if we are a sequence parameter first
            match = re.match(cls.SEQUENCE_PATTERN, _par.name)
            if match:
                sequence_name, sequence_index, parameter_name = match.groups()
                sequence_index = int(sequence_index)
                if sequence_name in cls.EXCEPT_SEQUENCES:
                    return
                if f'{sequence_name}{sequence_index}' not in seqsCalled:
                    seqsCalled.append(f'{sequence_name}{sequence_index}')
                else:
                    continue
                method_name = f'{"OnSeq" if cls.IS_EXPOSE_PUBLIC else "onSeq"}{sequence_name}N'
                if hasattr(_comp, method_name):
                    method = getattr(_comp, method_name)
                    arg_count = method.__code__.co_argcount
                    if arg_count == 2:
                        method(sequence_index)
                        
    @classmethod
    def __isParGroup(cls, par: Par) -> bool:
        """Check if a parameter is a ParGroup. Is there no better way?"""
        par_name = par.name[:-1]
        try:
            pg = par.owner.parGroup[par_name]
            return len(pg) > 1
        except:
            return False

    @classmethod
    def EnableStubs(cls) -> None:
        """Enable stubs for the extension."""
        cls.STUBS_ENABLED = True
        cls.UpdateStubs()

    @classmethod
    def DisableStubs(cls) -> None:
        """Disable stubs for the extension."""
        cls.STUBS_ENABLED = False

    @classmethod
    def UpdateStubs(cls) -> None:
        """Update the stubs for the extension."""
        if cls.STUBS_ENABLED:
            for _docked in me.docked:
                if 'extStubser' in _docked.tags:
                    # get class name from extension object
                    class_name = cls.EXT_SELF.__class__.__name__
                    op_ext = op(class_name)
                    _docked.StubifyDat(op_ext)



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