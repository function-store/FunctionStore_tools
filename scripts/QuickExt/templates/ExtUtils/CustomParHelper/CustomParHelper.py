import re

class CustomParHelper:
    """
    Author: Dan Molnar aka Function Store (@function.str dan@functionstore.xyz) 2024

    CustomParHelper is a helper class that provides easy access to custom parameters
    of a COMP and simplifies the implementation of custom parameter callbacks in TouchDesigner extensions.

    ## Features:
    - Access custom parameters as properties
    - Simplified custom parameter callbacks
    - Support for sequence parameters
    - Support for parameter groups (parGroups)
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
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [], enable_stubs: bool = False)
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

    3. Access custom parameters as properties (if enable_properties=True (default)):
       - `self.par<ParamName>`: Access the parameter object
       - `self.eval<ParamName>`: Get the evaluated value of the parameter
       - `self.parGroup<GroupName>`: Access the parameter group object (if enable_parGroups=True (default))
       - `self.evalGroup<GroupName>`: Get the evaluated value of the parameter group (if enable_parGroups=True (default))
    > NOTE: to expose public properties, eg. self.Par<ParamName> instead of self.par<ParamName>, set expose_public=True in the Init function

    4. Implement callbacks (if enable_callbacks=True (default)):
       - For regular parameters:
         ```python
         def onPar<ParamName>(self, _par, _val, _prev):
           # _par and _prev can be omitted if not needed
         ```

       - For pulse parameters:
         ```python
         def onPar<PulseParamName>(self, _par):
           # _par can be omitted if not needed
         ```

       - For sequence blocks:
         ```python
         def onSeq<SeqName>N(self, idx):
         ```

       - For sequence parameters:
         ```python
         def onSeq<SeqName>N<ParName>(self, _par, idx, _val, _prev):
           # _par and _prev can be omitted if not needed
         ```

       - For parameter groups if enable_parGroups=True (default):
         ```python
         def onParGroup<GroupName>(self, _parGroup, _val):
           # _parGroup can be omitted if not needed
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
    EXCEPT_CALLBACKS: list[str] = []
    EXCEPT_SEQUENCES: list[str] = []
    PAR_PROPS: list[str] = ['*']
    PAR_CALLBACKS: list[str] = ['*']
    SEQUENCE_PATTERN: str = r'(\w+?)(\d+)(.+)'
    IS_EXPOSE_PUBLIC: bool = False
    STUBS_ENABLED: bool = False

    @classmethod
    def Init(cls, extension_self, ownerComp: COMP, enable_properties: bool = True, enable_callbacks: bool = True, enable_parGroups: bool = True, enable_seq: bool = True, expose_public: bool = False,
             par_properties: list[str] = ['*'], par_callbacks: list[str] = ['*'], 
             except_properties: list[str] = [], except_sequences: list[str] = [], except_callbacks: list[str] = [], except_pages: list[str] = [],
             enable_stubs: bool = False) -> None:
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
        if cls.STUBS_ENABLED and cls.STUBSER is not None:
            # get class name from extension object
            class_name = cls.EXT_SELF.__class__.__name__
            op_ext = cls.EXT_OWNERCOMP.op(class_name)
            cls.STUBSER.StubifyDat(op_ext)
