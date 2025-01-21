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
    EXCEPT_PAGES_STATIC: list[str] = ['Version Ctrl', 'About', 'Info']
    EXCEPT_PAGES: list[str] = EXCEPT_PAGES_STATIC
    EXCEPT_PROPS: list[str] = []
    EXCEPT_CALLBACKS: list[str] = []
    EXCEPT_SEQUENCES: list[str] = []
    PAR_PROPS: list[str] = ['*']
    PAR_CALLBACKS: list[str] = ['*']
    SEQUENCE_PATTERN: str = '(\\w+?)(\\d+)(.+)'
    IS_EXPOSE_PUBLIC: bool = False
    STUBS_ENABLED: bool = False

    @classmethod
    def Init(cls, extension_self, ownerComp: COMP, enable_properties: bool=True, enable_callbacks: bool=True, enable_parGroups: bool=True, enable_seq: bool=True, expose_public: bool=False, par_properties: list[str]=['*'], par_callbacks: list[str]=['*'], except_properties: list[str]=[], except_sequences: list[str]=[], except_callbacks: list[str]=[], except_pages: list[str]=[], enable_stubs: bool=False) -> None:
        """Initialize the CustomParHelper."""
        pass

    @classmethod
    def CustomParsAsProperties(cls, extension_self, ownerComp: COMP, enable_parGroups: bool=True) -> None:
        """Create properties for custom parameters."""
        pass

    @classmethod
    def UpdateCustomParsAsProperties(cls) -> None:
        """Update the properties for custom parameters."""
        pass

    @classmethod
    def EnableCallbacks(cls, enable_parGroups: bool=True, enable_seq: bool=True) -> None:
        """Enable callbacks for custom parameters."""
        pass

    @classmethod
    def DisableCallbacks(cls, disable_parGroups: bool=True, disable_seq: bool=True) -> None:
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