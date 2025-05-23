import re

class CustomParHelper:
    """
    Author: Dan Molnar aka Function Store (@function.str dan@functionstore.xyz) 2024

    CustomParHelper is a helper class that provides easy access to custom parameters
    of a COMP and simplifies the implementation of custom parameter callbacks in TouchDesigner extensions.

    ## Features:
    - Access custom parameters as properties
    - Set parameter values through properties
    - Simplified custom parameter callbacks
    - Support for sequence parameters
    - Support for parameter groups (parGroups)
    - Support for general callbacks that catch all parameter changes
    - Configurable inclusion for properties and callbacks (by default all parameters are included)
    - Configurable exceptions for pages, properties, callbacks, and sequences

    ## Usage in your extension class:
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
         value = self.evalMyParam
         # Set value (always sets .val regardless of parameter mode)
         self.evalMyParam = 5
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
         self.parMyParam.expr = "op('something').par.value"
         self.parMyParam.bindExpr = "op('other').par.value"
         # Set value (only works in CONSTANT or BIND modes)
         self.parMyParam = 5  # Ignored if parameter is in EXPRESSION mode
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

    > NOTE: This class is part of the extUtils package, and is designed to work with the QuickExt framework.
    > NOTE: The reason this is implemented with static methods, is to omit the need to instantiate the class, providing a simpler interface (arguably).
    """
    
    EXT_SELF = None
    EXT_OWNERCOMP = None

    PAR_EXEC = op('extParExec')
    DAT_EXEC = op('extParPropDatExec')
    PAR_GROUP_EXEC = op('extParGroupExec')
    SEQ_EXEC = op('extSeqParExec')
    STUBSER = op('extStubser')

    EXCEPT_PAGES_STATIC: list[str]  = ['Version Ctrl', 'About', 'Info']
    EXCEPT_PAGES: list[str] = EXCEPT_PAGES_STATIC
    EXCEPT_PROPS: list[str] = []
    EXCEPT_CALLBACKS: list[str] = [] # handled outside in extParExec DAT
    EXCEPT_SEQUENCES: list[str] = [] # handled outside in extSeqParExec DAT
    PAR_PROPS: list[str] = ['*']
    PAR_CALLBACKS: list[str] = ['*'] # handled outside in extParExec DAT
    SEQUENCE_PATTERN: str = r'(\w+?)(\d+)(.+)'
    IS_EXPOSE_PUBLIC: bool = False
    STUBS_ENABLED: bool = False
    GENERAL_CALLBACK_ENABLE: bool = True


    @classmethod
    def Init(cls, extension_self, ownerComp: COMP, enable_properties: bool = True, enable_callbacks: bool = True, enable_parGroups: bool = True, enable_seq: bool = True, expose_public: bool = False,
             par_properties: list[str] = ['*'], par_callbacks: list[str] = ['*'], 
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [],
             enable_stubs: bool = False, general_callback_enable: bool = True) -> None:
        """Initialize the CustomParHelper."""
        cls.EXT_SELF = extension_self
        cls.EXT_OWNERCOMP = ownerComp
        cls.IS_EXPOSE_PUBLIC = expose_public
        cls.PAR_PROPS = par_properties
        cls.PAR_CALLBACKS = par_callbacks
        cls.EXCEPT_PAGES = cls.EXCEPT_PAGES_STATIC + except_pages
        cls.EXCEPT_PROPS = except_properties
        cls.EXCEPT_CALLBACKS = except_callbacks
        cls.EXCEPT_SEQUENCES = except_sequences
        cls.GENERAL_CALLBACK_ENABLE = general_callback_enable

        cls.__setOwnerCompToDocked(ownerComp)

        cls.DAT_EXEC.par.active = enable_properties

        if enable_properties:
            cls.CustomParsAsProperties(extension_self, ownerComp, enable_parGroups=enable_parGroups)

        if enable_callbacks:
            cls.EnableCallbacks(enable_parGroups, enable_seq)
        else:
            cls.DisableCallbacks(not enable_parGroups, not enable_seq)

        if enable_stubs:
            cls.EnableStubs()
        else:
            cls.DisableStubs()


    @classmethod
    def __setOwnerCompToDocked(cls, ownerComp: COMP) -> None:
        for _op in me.docked:
            if hasattr(_op.par, 'ops'):
                _op.par.ops.val = ownerComp
            if hasattr(_op.par, 'op'):
                _op.par.op.val = ownerComp


    @classmethod
    def CustomParsAsProperties(cls, extension_self, ownerComp: COMP, enable_parGroups: bool = True) -> None:
        """Create properties for custom parameters."""
        if ownerComp is None:
            return
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
    def UpdateCustomParsAsProperties(cls) -> None:
        """Update the properties for custom parameters."""
        cls.CustomParsAsProperties(cls.EXT_SELF, cls.EXT_OWNERCOMP)

    @classmethod
    def _create_propertyEval(cls, extension_self, owner_comp: COMP, Parname: str, enable_parGroups: bool = True) -> None:
        """Create a property for the evaluated value of a parameter."""
        def getter(instance):
            return getattr(owner_comp.par, Parname).eval()
        def setter(instance, value):
            getattr(owner_comp.par, Parname).val = value
        def getter_group(instance):
            return getattr(owner_comp.parGroup, Parname[:-1]).eval()
        def setter_group(instance, value):
            for i, val in enumerate(value):
                getattr(owner_comp.parGroup, Parname[:-1])[i].val = val

        property_name = f'{"Eval" if cls.IS_EXPOSE_PUBLIC else "eval"}{Parname}'
        setattr(extension_self.__class__, property_name, property(getter, setter))
        
        if enable_parGroups and cls.__isParGroup(getattr(owner_comp.par, Parname)):
            setattr(extension_self.__class__, f'{"EvalGroup" if cls.IS_EXPOSE_PUBLIC else "evalGroup"}{Parname[:-1]}', property(getter_group, setter_group))
        

    @classmethod
    def _create_propertyPar(cls, extension_self, owner_comp: COMP, Parname: str, enable_parGroups: bool = True) -> None:
        """Create a property for the parameter object."""
        def getter(instance):
            return getattr(owner_comp.par, Parname)
        def setter(instance, value):
            par = getattr(owner_comp.par, Parname)
            if par.mode in [ParMode.BIND, ParMode.CONSTANT]:
                par.val = value
        def getter_group(instance):
            return getattr(owner_comp.parGroup, Parname[:-1])
        def setter_group(instance, value):
            pargroup = getattr(owner_comp.parGroup, Parname[:-1])
            for i, val in enumerate(value):
                if pargroup[i].mode in [ParMode.BIND, ParMode.CONSTANT]:
                    pargroup[i].val = val

        property_name = f'{"Par" if cls.IS_EXPOSE_PUBLIC else "par"}{Parname}'
        setattr(extension_self.__class__, property_name, property(getter, setter))
        
        if enable_parGroups and cls.__isParGroup(getattr(owner_comp.par, Parname)):
            setattr(extension_self.__class__, f'{"ParGroup" if cls.IS_EXPOSE_PUBLIC else "parGroup"}{Parname[:-1]}', property(getter_group, setter_group))


    @classmethod
    def EnableCallbacks(cls, enable_parGroups: bool = True, enable_seq: bool = True) -> None:
        """Enable callbacks for custom parameters."""
        cls.PAR_EXEC.par.active = True
        if enable_parGroups:
            cls.PAR_GROUP_EXEC.par.active = True
        if enable_seq:
            cls.SEQ_EXEC.par.active = True


    @classmethod
    def DisableCallbacks(cls, disable_parGroups: bool = True, disable_seq: bool = True) -> None:
        """Disable callbacks for custom parameters."""
        cls.PAR_EXEC.par.active = False
        if disable_parGroups:
            cls.PAR_GROUP_EXEC.par.active = False
        if disable_seq:
            cls.SEQ_EXEC.par.active = False


    @classmethod
    def OnValueChange(cls, comp: COMP, _par: Par, prev: Par) -> None:
        """Handle value change events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters

        comp = cls.EXT_SELF # a bit hacky to be able to call non-exposed methods too

        # check if we are a sequence parameter first
        match = None
        if _par.sequence is not None:
            match = re.match(cls.SEQUENCE_PATTERN, _par.name)
        if match:
            sequence_name, sequence_index, parameter_name = match.groups()
            parameter_name = parameter_name.capitalize()
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
                    method(sequence_index, _par.eval())
                elif arg_count == 4:
                    method(_par, sequence_index, _par.eval())
                elif arg_count == 5:
                    method(_par, sequence_index, _par.eval(), prev)
        elif hasattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{_par.name}'):
            method = getattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{_par.name}')
            arg_count = method.__code__.co_argcount  # Total number of arguments
            if arg_count == 2:
                method(_par.eval())
            elif arg_count == 3:
                method(_par, _par.eval())
            elif arg_count == 4:
                method(_par, _par.eval(), prev)
        elif cls.GENERAL_CALLBACK_ENABLE:
            # if not caught by any other callbacks, check if there is a general callback
            method_check = f'{"OnValueChange" if cls.IS_EXPOSE_PUBLIC else "onValueChange"}'
            if hasattr(comp, method_check):
                method = getattr(comp, method_check)
                arg_count = method.__code__.co_argcount
                if arg_count == 2:
                    method(_par)
                elif arg_count == 3:
                    method(_par, _par.eval())
                elif arg_count == 4:
                    method(_par, _par.eval(), prev)


    @classmethod
    def OnPulse(cls, comp: COMP, _par: Par) -> None:
        """Handle pulse events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters
        
        comp = cls.EXT_SELF # a bit hacky to be able to call non-exposed methods too

        # check if we are a sequence parameter first
        match = None
        if _par.sequence is not None:
            match = re.match(cls.SEQUENCE_PATTERN, _par.name)
        if match:
            sequence_name, sequence_index, parameter_name = match.groups()
            parameter_name = parameter_name.capitalize()
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
                    method(sequence_index, _par)
        elif hasattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{_par.name}'):
            method = getattr(comp, f'{"OnPar" if cls.IS_EXPOSE_PUBLIC else "onPar"}{_par.name}')
            arg_count = method.__code__.co_argcount  # Total number of arguments
            if arg_count == 1:
                method()
            elif arg_count == 2:
                method(_par)
        elif cls.GENERAL_CALLBACK_ENABLE:
            # if not caught by any other callbacks, check if there is a general callback
            method_check = f'{"OnPulse" if cls.IS_EXPOSE_PUBLIC else "onPulse"}'
            if hasattr(comp, method_check):
                method = getattr(comp, method_check)
                arg_count = method.__code__.co_argcount
                if arg_count == 1:
                    method()
                elif arg_count == 2:
                    method(_par)


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
            match = None
            if _par.sequence is not None:
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
    def __isParGroup(cls, _par: Par) -> bool:
        """Check if a parameter is a ParGroup. Is there no better way?"""
        return len(_par.parGroup) > 1

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
        if cls.STUBS_ENABLED and cls.STUBSER is not None:
            # get class name from extension object
            class_name = cls.EXT_SELF.__class__.__name__
            op_ext = cls.EXT_OWNERCOMP.op(class_name)
            cls.STUBSER.StubifyDat(op_ext)
