import re

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
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [])

        Additional options:
            - enable_parGroups: If True, creates properties and methods for parGroups (default: True)
            - expose_public: If True, uses capitalized property and method names (e.g., Par, Eval instead of par, eval)
            - par_properties: List of parameter names to include in property creation, by default all parameters are included
            - par_callbacks: List of parameter names to include in callback handling, by default all parameters are included
            - except_properties: List of parameter names to exclude from property creation
            - except_callbacks: List of parameter names to exclude from callback handling
            - except_pages: List of parameter pages to exclude from property and callback handling
            - except_sequences: List of sequence names to exclude from property and callback handling

    > NOTE: this class should only be attached to one extension, otherwise it will cause conflicts    

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
    
    > NOTE: This class only works with the docked helper ParExec DATs, which also perform filtering of parameters in a lot of cases.
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
    
    @staticmethod
    def Init(extension_self, ownerComp: COMP, enable_properties: bool = True, enable_callbacks: bool = True, enable_parGroups: bool = True, expose_public: bool = False,
             par_properties: list[str] = ['*'], par_callbacks: list[str] = ['*'], 
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = []) -> None:
        """Initialize the CustomParHelper."""
        CustomParHelper.EXT_SELF = extension_self
        CustomParHelper.IS_EXPOSE_PUBLIC = expose_public
        CustomParHelper.PAR_PROPS = par_properties
        CustomParHelper.PAR_CALLBACKS = par_callbacks
        CustomParHelper.EXCEPT_PAGES = CustomParHelper.EXCEPT_PAGES_STATIC + except_pages
        CustomParHelper.EXCEPT_PROPS = except_properties
        CustomParHelper.EXCEPT_CALLBACKS = except_callbacks
        CustomParHelper.EXCEPT_SEQUENCES = except_sequences

        me_me: textDAT = me # just to have autocomplete on this
        for _docked in me_me.docked:
            if 'extDatExec' in _docked.tags:
                _docked.par.active = enable_properties

        if enable_properties:
            CustomParHelper.CustomParsAsProperties(extension_self, ownerComp, enable_parGroups=enable_parGroups)

        if enable_callbacks:
            CustomParHelper.EnableCallbacks(enable_parGroups)
        else:
            CustomParHelper.DisableCallbacks()


    @staticmethod
    def CustomParsAsProperties(extension_self, ownerComp: COMP, enable_parGroups: bool = True) -> None:
        """Create properties for custom parameters."""
        for _par in ownerComp.customPars:
            if (not tdu.match(' '.join(CustomParHelper.PAR_PROPS), [_par.name]) or
                tdu.match(' '.join(CustomParHelper.EXCEPT_PAGES), [_par.page.name]) or
                tdu.match(' '.join(CustomParHelper.EXCEPT_PROPS), [_par.name])):
                continue
            # Check if the parameter belongs to an excepted sequence
            sequence_match = re.match(CustomParHelper.SEQUENCE_PATTERN, _par.name)
            if sequence_match and sequence_match.group(1) in CustomParHelper.EXCEPT_SEQUENCES:
                continue

            CustomParHelper._create_propertyEval(extension_self, ownerComp, _par.name, enable_parGroups=enable_parGroups)
            CustomParHelper._create_propertyPar(extension_self, ownerComp, _par.name, enable_parGroups=enable_parGroups)


    @staticmethod
    def _create_propertyEval(extension_self, owner_comp: COMP, Parname: str, enable_parGroups: bool = True) -> None:
        """Create a property for the evaluated value of a parameter."""
        def getter(instance):
            return getattr(owner_comp.par, Parname).eval()
        def getter_group(instance):
            return getattr(owner_comp.parGroup, Parname[:-1]).eval()

        property_name = f'{"Eval" if CustomParHelper.IS_EXPOSE_PUBLIC else "eval"}{Parname}'
        setattr(extension_self.__class__, property_name, property(getter))
        
        if enable_parGroups and CustomParHelper.__isParGroup(getattr(owner_comp.par, Parname)):
            setattr(extension_self.__class__, f'{"EvalGroup" if CustomParHelper.IS_EXPOSE_PUBLIC else "evalGroup"}{Parname[:-1]}', property(getter_group))
        

    @staticmethod
    def _create_propertyPar(extension_self, owner_comp: COMP, Parname: str, enable_parGroups: bool = True) -> None:
        """Create a property for the parameter object."""
        def getter(instance):
            return getattr(owner_comp.par, Parname)
        def getter_group(instance):
            return getattr(owner_comp.parGroup, Parname[:-1])

        property_name = f'{"Par" if CustomParHelper.IS_EXPOSE_PUBLIC else "par"}{Parname}'
        setattr(extension_self.__class__, property_name, property(getter))
        
        if enable_parGroups and CustomParHelper.__isParGroup(getattr(owner_comp.par, Parname)):
            setattr(extension_self.__class__, f'{"ParGroup" if CustomParHelper.IS_EXPOSE_PUBLIC else "parGroup"}{Parname[:-1]}', property(getter_group))


    @staticmethod
    def EnableCallbacks(enable_parGroups: bool = True) -> None:
        """Enable callbacks for custom parameters."""
        for _docked in me.docked:
            if 'extParExec' in _docked.tags or ('extParGroupExec' in _docked.tags and enable_parGroups):
                _docked.par.active = True


    @staticmethod
    def DisableCallbacks() -> None:
        """Disable callbacks for custom parameters."""
        for _docked in me.docked:
            if 'extParExec' in _docked.tags or 'extParGroupExec' in _docked.tags:
                _docked.par.active = False


    @staticmethod
    def OnValueChange(comp: COMP, par: Par, prev: Par) -> None:
        """Handle value change events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters

        comp = CustomParHelper.EXT_SELF # a bit hacky to be able to call non-exposed methods too

        # check if we are a sequence parameter first
        match = re.match(CustomParHelper.SEQUENCE_PATTERN, par.name)
        if match:
            sequence_name, sequence_index, parameter_name = match.groups()
            sequence_index = int(sequence_index)
            if sequence_name in CustomParHelper.EXCEPT_SEQUENCES:
                return
            method_name = f'{"OnSeq" if CustomParHelper.IS_EXPOSE_PUBLIC else "onSeq"}{sequence_name}N{parameter_name}'
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
        elif hasattr(comp, f'{"OnPar" if CustomParHelper.IS_EXPOSE_PUBLIC else "onPar"}{par.name}'):
            method = getattr(comp, f'{"OnPar" if CustomParHelper.IS_EXPOSE_PUBLIC else "onPar"}{par.name}')
            arg_count = method.__code__.co_argcount  # Total number of arguments
            if arg_count == 2:
                method(par.eval())
            elif arg_count == 3:
                method(par, par.eval())
            elif arg_count == 4:
                method(par, par.eval(), prev)
                

    @staticmethod
    def OnPulse(comp: COMP, par: Par) -> None:
        """Handle pulse events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters
        
        comp = CustomParHelper.EXT_SELF # a bit hacky to be able to call non-exposed methods too

        # check if we are a sequence parameter first
        match = re.match(CustomParHelper.SEQUENCE_PATTERN, par.name)
        if match:
            sequence_name, sequence_index, parameter_name = match.groups()
            sequence_index = int(sequence_index)
            if sequence_name in CustomParHelper.EXCEPT_SEQUENCES:
                return
            method_name = f'{"OnSeq" if CustomParHelper.IS_EXPOSE_PUBLIC else "onSeq"}{sequence_name}N{parameter_name}'
            if hasattr(comp, method_name):
                method = getattr(comp, method_name)
                arg_count = method.__code__.co_argcount
                if arg_count == 2:
                    method(sequence_index)
                elif arg_count == 3:
                    method(sequence_index, par)
        elif hasattr(comp, f'{"OnPar" if CustomParHelper.IS_EXPOSE_PUBLIC else "onPar"}{par.name}'):
            method = getattr(comp, f'{"OnPar" if CustomParHelper.IS_EXPOSE_PUBLIC else "onPar"}{par.name}')
            arg_count = method.__code__.co_argcount  # Total number of arguments
            if arg_count == 1:
                method()
            elif arg_count == 2:
                method(par)


    @staticmethod
    def OnValuesChanged(changes: list[tuple[Par, Par]]) -> None:
        """Handle value change events for ParGroups."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters
        parGroupsCalled = []
        for change in changes:
            _par = change[0]
            # _prev = change[1]
            # _comp = _par.owner
            _comp = CustomParHelper.EXT_SELF # a bit hacky to be able to call non-exposed methods too
            # handle sequence exceptions
            # check if we are a sequence parameter first
            match = re.match(CustomParHelper.SEQUENCE_PATTERN, _par.name)
            if match:
                sequence_name, sequence_index, parameter_name = match.groups()
                sequence_index = int(sequence_index)
                if sequence_name in CustomParHelper.EXCEPT_SEQUENCES:
                    continue
            if CustomParHelper.__isParGroup(_par):
                if _par.name[:-1] not in parGroupsCalled: # prevent calling parGroups multiple times
                    parGroupsCalled.append(_par.name[:-1])
                else:
                    continue
                # fetch the parGroup and ParName if it's a parGroup
                match = re.match(r'(\w+)(.)', _par.name)
                if match:
                    ParGroup, ParName = match.groups()
                    _par = _comp.ownerComp.parGroup[ParGroup] 
                    method_name = f'{"OnParGroup" if CustomParHelper.IS_EXPOSE_PUBLIC else "onParGroup"}{ParGroup}'
                    if hasattr(_comp, method_name):
                        method = getattr(_comp, method_name)
                        arg_count = method.__code__.co_argcount
                        if arg_count == 2:
                            method(_par.eval())
                        elif arg_count == 3:
                            method(_par, _par.eval())

    @staticmethod
    def OnSeqValuesChanged(changes: list[tuple[Par, Par]]) -> None:
        """Handle value change events for Sequence blocks."""
        seqsCalled = []
        for change in changes:
            _par = change[0]
            # _prev = change[1]
            # _comp = _par.owner
            _comp = CustomParHelper.EXT_SELF # a bit hacky to be able to call non-exposed methods too
            # handle sequence exceptions
            # check if we are a sequence parameter first
            match = re.match(CustomParHelper.SEQUENCE_PATTERN, _par.name)
            if match:
                sequence_name, sequence_index, parameter_name = match.groups()
                sequence_index = int(sequence_index)
                if sequence_name in CustomParHelper.EXCEPT_SEQUENCES:
                    return
                if f'{sequence_name}{sequence_index}' not in seqsCalled:
                    seqsCalled.append(f'{sequence_name}{sequence_index}')
                else:
                    continue
                method_name = f'{"OnSeq" if CustomParHelper.IS_EXPOSE_PUBLIC else "onSeq"}{sequence_name}N'
                if hasattr(_comp, method_name):
                    method = getattr(_comp, method_name)
                    arg_count = method.__code__.co_argcount
                    if arg_count == 2:
                        method(sequence_index)
                        
    @staticmethod
    def __isParGroup(par: Par) -> bool:
        """Check if a parameter is a ParGroup. Is there no better way?"""
        par_name = par.name[:-1]
        try:
            pg = par.owner.parGroup[par_name]
            return len(pg) > 1
        except:
            return False

