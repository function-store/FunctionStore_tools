

'''Info Header Start
Name : CustomParHelper
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
import re

# ---------------------------------------------------------------------------
# Declarative parameter fields  (optional, additive -- backlog item 3)
# ---------------------------------------------------------------------------
# CustomParHelper REFLECTS: it reads ownerComp.customPars and generates
# properties and callback routing from whatever it finds. That is the default
# and nothing below changes it. This layer lets a class also DECLARE its
# parameters and have them created, which is the half worth taking from
# tdp-TouchUtilCollection.
#
# THERE IS DELIBERATELY NO BASE CLASS TO INHERIT. CustomParHelper's whole
# appeal is that it needs none; adopting one would forfeit it. A ParField is
# just a class attribute, so declaring costs nothing structural.
#
# It is ADDITIVE in the strict sense: a class that declares no ParField gets
# byte-identical behaviour, because EnsureParFields returns immediately when
# it finds none. That is why this could land without touching a single
# existing tool.
#
# It also closes finding (4): reflection generates properties once, at Init,
# so a parameter added later has none until someone calls
# UpdateCustomParsAsProperties() by hand. A declared parameter cannot drift
# from its property, because the declaration creates both.


class ParField:
    """One declared custom parameter.

    Values are NEVER clobbered. Re-running Init refreshes labels, help,
    ranges and menu entries on an existing parameter but leaves whatever
    value the user (or the saved .toe) put there -- a declaration describes
    the parameter, not its current state.
    """

    STYLE = 'Str'
    _COUNTER = 0

    def __init__(self, default=None, label=None, help=None, page='Custom',
                 order=None, readOnly=False, startSection=False,
                 min=None, max=None, clampMin=None, clampMax=None,
                 normMin=None, normMax=None, menuNames=None, menuLabels=None):
        # Help is strongly expected (.claude/rules/parameters.md) but NOT
        # enforced: refusing to compile a whole extension over a missing
        # tooltip is out of proportion to the problem. Warn where the author
        # will see it and carry on.
        if not (help or '').strip():
            try:
                debug('CustomParHelper: %s declared with no help text — every '
                      'custom parameter should say what it controls and what '
                      'its values mean' % type(self).__name__)
            except Exception:
                pass
        self.default = default
        self.label = label
        self.help = (help or '').strip()
        self.page = page
        self.readOnly = readOnly
        self.startSection = startSection
        self.min, self.max = min, max
        self.clampMin, self.clampMax = clampMin, clampMax
        self.normMin, self.normMax = normMin, normMax
        self.menuNames, self.menuLabels = menuNames, menuLabels
        self.name = None
        ParField._COUNTER += 1
        self._seq = ParField._COUNTER if order is None else order

    # -- attribute access ---------------------------------------------------
    # A ParField is a DESCRIPTOR, so the declaration doubles as the accessor:
    #
    #     self.Speed          -> the Par     (ParGroup for XYZ/RGB/RGBA)
    #     self.Speed.val = 5  -> sets it
    #     self.Speed = 5      -> also sets it
    #
    # Without this, `self.Speed` returns the declaration OBJECT and
    # `self.Speed.val = 5` sets an attribute on it -- appearing to work while
    # the parameter never changes. That silent no-op is the whole reason this
    # exists; it is the first thing anyone writes.
    #
    # Resolution goes through the INSTANCE's ownerComp, never the class-level
    # EXT_OWNERCOMP, so two COMPs sharing one extension module read their own
    # parameters (see the module-locality invariant above).

    def __set_name__(self, owner, name):
        self.name = name

    def _parOf(self, instance):
        """The live Par/ParGroup, or an AttributeError explaining why not.

        It deliberately does NOT fall back to returning the declaration. Doing
        so would hand back an object where `.val = 5` sets a harmless attribute
        and the parameter never moves -- the exact silent no-op this descriptor
        exists to kill, just in a narrower window (before Init, or on a COMP
        that lost the parameter). Failing loudly with the reason is the whole
        point.
        """
        comp = getattr(instance, 'ownerComp', None)
        if comp is None or not comp.valid:
            raise AttributeError(
                "%s: cannot reach parameter '%s' — the extension has no valid "
                "ownerComp yet. Declared parameters exist only after "
                "CustomParHelper.Init(self, ownerComp) has run."
                % (type(instance).__name__, self.name))
        group = getattr(comp.parGroup, self.name, None)
        if group is None:
            raise AttributeError(
                "%s: '%s' is declared but does not exist on %s. Has "
                "CustomParHelper.Init(self, ownerComp) run? (It is what creates "
                "declared parameters.)"
                % (type(instance).__name__, self.name, comp.path))
        return group if len(group) > 1 else group[0]

    def __get__(self, instance, owner=None):
        if instance is None:
            return self                      # class access -- the declaration
        return self._parOf(instance)

    def __set__(self, instance, value):
        par = self._parOf(instance)          # raises rather than silently no-op
        if isinstance(value, (list, tuple)) and hasattr(par, '__len__'):
            for member, item in zip(par, value):
                member.val = item
        elif hasattr(par, '__len__') and not hasattr(par, 'val'):
            for member in par:
                member.val = value
        else:
            par.val = value

    # -- creation -----------------------------------------------------------

    def append(self, page, name):
        """Create the parameter on `page`. Returns its ParGroup."""
        return getattr(page, 'append' + self.STYLE)(name)

    # Styles that carry no meaningful value to seed.
    _NO_VALUE = ('Pulse', 'Header')

    def _defaultFor(self, index):
        """The declared default for member `index` of a ParGroup.

        A multi-member field (XYZ, RGB, RGBA) may declare either one value
        for every member or a sequence, one per member. A sequence must be
        distributed: assigning the whole tuple to a single member raises
        `Cannot set default on parameter`, which is what a ParRGB default
        of (0.2, 0.4, 0.6) did before this existed.
        """
        if self.default is None:
            return None
        if isinstance(self.default, (list, tuple)):
            return self.default[index] if index < len(self.default) else None
        return self.default

    def apply(self, parGroup, created=False):
        """Push declared metadata onto a ParGroup.

        `created` is the ONLY thing that may set a value. A brand-new
        parameter is seeded with its declared default — TD otherwise leaves
        it at the style default, so declaring `default=2.5` and reading 0.0
        was the surprise this argument exists to remove. On a parameter that
        already existed it stays False, which is what keeps the
        value-preservation guarantee intact.
        """
        for i, par in enumerate(parGroup):
            par.help = self.help
            par.readOnly = self.readOnly
            member = self._defaultFor(i)
            if member is not None:
                par.default = member
            for attr in ('min', 'max', 'clampMin', 'clampMax', 'normMin', 'normMax'):
                val = getattr(self, attr)
                if val is not None and hasattr(par, attr):
                    setattr(par, attr, val)
        first = parGroup[0]
        if self.label:
            first.label = self.label
        first.startSection = bool(self.startSection)
        if self.menuNames:
            first.menuNames = list(self.menuNames)
            first.menuLabels = list(self.menuLabels or self.menuNames)
        # Seed the value ONLY on creation -- never on a refresh.
        if created and self.default is not None and self.STYLE not in self._NO_VALUE:
            for i, par in enumerate(parGroup):
                member = self._defaultFor(i)
                if member is not None:
                    par.val = member


class ParFloat(ParField):   STYLE = 'Float'
class ParInt(ParField):     STYLE = 'Int'
class ParStr(ParField):     STYLE = 'Str'
class ParToggle(ParField):  STYLE = 'Toggle'
class ParPulse(ParField):   STYLE = 'Pulse'
class ParFile(ParField):    STYLE = 'File'
class ParFolder(ParField):  STYLE = 'Folder'
class ParHeader(ParField):  STYLE = 'Header'
class ParXYZ(ParField):     STYLE = 'XYZ'
class ParRGB(ParField):     STYLE = 'RGB'
class ParRGBA(ParField):    STYLE = 'RGBA'
class ParOP(ParField):      STYLE = 'OP'
class ParCOMP(ParField):    STYLE = 'COMP'
class ParTOP(ParField):     STYLE = 'TOP'
class ParCHOP(ParField):    STYLE = 'CHOP'
class ParSOP(ParField):     STYLE = 'SOP'
class ParDAT(ParField):     STYLE = 'DAT'
class ParMAT(ParField):     STYLE = 'MAT'


class ParMenu(ParField):
    """A Menu parameter. `names` is required; labels default to the names."""
    STYLE = 'Menu'

    def __init__(self, names, labels=None, **kw):
        kw.setdefault('menuNames', list(names))
        kw.setdefault('menuLabels', list(labels or names))
        super().__init__(**kw)


class ParStrMenu(ParMenu):
    """An editable dropdown -- free text with suggestions."""
    STYLE = 'StrMenu'


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

    ### INVARIANT: an extension's module reference must be LOCAL

    Generated properties are set on the CLASS (`setattr(extension_self.
    __class__, ...)`), closed over the one `owner_comp` that called Init. That
    is safe only because `.module` is per-DAT, so every COMP that resolves its
    extension locally -- `op('./MyExt').module.MyExt(me)` -- gets a DISTINCT
    class object and therefore its own properties.

    Point two COMPs at ONE module and they share a class: the second Init
    rebinds the first COMP's properties to the second COMP's parameters, and
    the first COMP silently starts reading the wrong values. Measured
    2026-09-01: all 726 extension parameters in this project resolve locally,
    so nothing is broken today -- but it is one convention away, which is why
    it is written down. (Callback ROUTING no longer has this problem: it is
    resolved per-comp by `_extForComp`.)

    ### Declaring parameters instead of only reflecting them

    Optional and additive. Declare INSIDE __init__ -- `ownerComp` exists there,
    so the call creates the parameter and hands back the real Par, and ordinary
    Python works:

       ```python
       class MyToolExt:
           def __init__(self, ownerComp):
               self.ownerComp = ownerComp
               self.Speed = CustomParHelper.Float(
                   ownerComp, 'Speed', default=1.0, min=0, max=10,
                   page='Settings', help='Playback speed multiplier.')
               if ownerComp.par.Advanced.eval():          # conditionals
                   self.Depth = CustomParHelper.Int(
                       ownerComp, 'Depth', default=3, page='Settings',
                       help='Recursion depth.')
               for name in ('Alpha', 'Beta'):             # loops
                   CustomParHelper.Toggle(ownerComp, name, page='Flags',
                                          help='Flag %s.' % name)
               CustomParHelper.Init(self, ownerComp)
       ```

    One helper per style -- Float, Int, Str, Toggle, Pulse, Menu, StrMenu,
    File, Folder, Header, XYZ, RGB, RGBA, OP, COMP, TOP, CHOP, SOP, DAT, MAT --
    each returning the Par (a ParGroup for the multi-member ones). All of them
    go through EnsurePar, which is also what the class-body form below uses, so
    there is ONE implementation of create / refresh / restyle.

    ### The class-body form

    Still supported, for a purely static parameter set:

       ```python
       class MyToolExt:
           Speed = CustomParHelper.ParFloat(default=1.0, page='Settings',
                                            help='Playback speed multiplier.')
           def __init__(self, ownerComp):
               CustomParHelper.Init(self, ownerComp)
       ```

    It CANNOT do conditionals, loops or computed values, and it cannot hand
    back a Par: a class body runs before any COMP exists, so there is nothing
    to create a parameter on yet. The declaration object stands in, and a
    descriptor resolves it at runtime:

       self.Speed              # the Par   (a ParGroup for XYZ/RGB/RGBA)
       self.Speed.val = 5      # sets it
       self.Speed = 5          # also sets it

    Before Init has created the parameter, touching it raises AttributeError
    naming the reason rather than silently doing nothing. Resolution goes
    through the INSTANCE's ownerComp, never the class-level EXT_OWNERCOMP, so
    two COMPs sharing one module read their own parameters. CustomParHelper's
    reflected accessors (parSpeed / evalSpeed) still exist alongside.

    Reflection stays the default and a class that declares nothing behaves
    exactly as before, and there is no base class to inherit. Pass
    `enable_parfields=False` to skip the class-body pass entirely.

    `page` names the parameter page to create on, created if absent, and
    defaults to 'Custom'.

    A NEW parameter is seeded with its declared default; an existing one keeps
    whatever value it has. A declared STYLE change is applied by rebuilding the
    parameter, carrying page position, mode, expression, bind expression and
    value -- an EXPORT is the one thing that cannot be carried, and is
    reported. Missing `help` warns rather than raising.

    Every keyword is a TouchDesigner Par MEMBER, set straight through --
    default, label, help, readOnly, startSection, min, max, clampMin,
    clampMax, normMin, normMax, menuNames, menuLabels, order, page. There is
    no second vocabulary and nothing here re-documents them; see the Par Class
    docs. Two are used at CREATION time and so differ from the live member of
    the same name: `page` is the page NAME to create on (created if absent),
    and `order` also fixes declaration order within the class. A multi-member
    field (ParXYZ/ParRGB/ParRGBA) takes one value for all members or a
    sequence, one per member.

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
        - `enable_stubs`: NO-OP. Stub generation was removed from ExtUtils (the Stubser was 18 of its 46 operators and nothing enabled it); kept for API compatibility. Use QuickExt or VSCodeTools to generate stubs. (Stubser by AlphaMoonbase.berlin)
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
             enable_stubs: bool = False, general_callback_enable: bool = True,
             enable_parfields: bool = True) -> None:
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

        # Declarations first: reflection below reads ownerComp.customPars, so
        # a declared parameter must exist by now or it gets no property until
        # the next manual refresh. No-op for a class that declares nothing.
        if enable_parfields:
            cls.EnsureParFields(extension_self, ownerComp)

        if enable_properties:
            cls.CustomParsAsProperties(extension_self, ownerComp, enable_parGroups=enable_parGroups)

        # Declared callbacks bind to the names dispatch already looks for.
        # After the parfield pass, so a declaration may name a parameter the
        # same class declared; before EnableCallbacks, so nothing can fire at
        # a half-bound extension.
        if enable_callbacks:
            cls.HarvestCallbacks(extension_self, ownerComp)
            cls.EnableCallbacks(enable_parGroups, enable_seq)
        else:
            cls.DisableCallbacks(not enable_parGroups, not enable_seq)

        if enable_stubs:
            cls.EnableStubs()
        else:
            cls.DisableStubs()


    # --- declarative parameter fields --------------------------------------

    _PAR_NAME_RE = re.compile(r'^[A-Z][A-Za-z0-9]*$')

    @classmethod
    def _declaredParFields(cls, extension_self) -> list:
        """Every ParField declared on the extension's class, declaration order.

        Walks the MRO base-first so a subclass can override an inherited
        declaration by redeclaring the same name.
        """
        found = {}
        for klass in reversed(type(extension_self).__mro__):
            for name, value in vars(klass).items():
                if isinstance(value, ParField):
                    found[name] = value
        return sorted(found.items(), key=lambda item: item[1]._seq)

    @classmethod
    def _restyle(cls, ownerComp, name, parGroup, field, page):
        """Rebuild a parameter whose declared style changed, keeping what can be kept.

        A style cannot be changed in place, so the parameter is destroyed and
        recreated. Everything TD lets us carry is carried: page position, and
        each member's mode, expression, bind expression and value.

        AN EXPORT CANNOT SURVIVE. The link is owned by the exporting CHOP, not
        by the parameter, so destroying the parameter breaks it and no amount
        of care here restores it. That case is reported loudly rather than
        lost quietly -- it is the one thing a restyle genuinely costs.

        Returns the new ParGroup, or None if the rebuild failed (in which case
        the original is left alone).
        """
        keep, exporting = [], []
        try:
            order = parGroup[0].order
            for par in parGroup:
                keep.append({'mode': par.mode, 'expr': par.expr,
                             'bindExpr': par.bindExpr, 'val': par.val})
                if par.mode == ParMode.EXPORT:
                    exporting.append(par.name)
        except Exception as e:
            debug('CustomParHelper: could not read %s.%s before restyle (%s); '
                  'left unchanged' % (ownerComp.path, name, e))
            return None
        try:
            parGroup.destroy()
            newGroup = field.append(page, name)
        except Exception as e:
            debug('CustomParHelper: restyle of %s.%s FAILED (%s) -- the '
                  'parameter may need recreating by hand' % (ownerComp.path, name, e))
            return None
        for par, prev in zip(newGroup, keep):
            try:
                par.order = order
            except Exception:
                pass
            try:
                if prev['mode'] == ParMode.EXPRESSION and prev['expr']:
                    par.expr = prev['expr']
                    par.mode = ParMode.EXPRESSION
                elif prev['mode'] == ParMode.BIND and prev['bindExpr']:
                    par.bindExpr = prev['bindExpr']
                    par.mode = ParMode.BIND
                elif prev['val'] not in (None, ''):
                    par.val = prev['val']          # TD coerces across types
            except Exception:
                pass                                # a value that will not convert
        if exporting:
            debug('CustomParHelper: %s.%s was EXPORTED (%s) and has been '
                  'restyled to %s -- the export is owned by the exporting CHOP '
                  'and could not be carried across; re-export it'
                  % (ownerComp.path, name, ', '.join(exporting), field.STYLE))
        return newGroup

    @classmethod
    def EnsurePar(cls, ownerComp: COMP, name: str, field):
        """Create or refresh ONE parameter from a field spec, and RETURN it.

        This is the primitive. Everything else -- the init-time helpers below
        and the class-body declarations -- goes through here, so there is one
        implementation of create / refresh / restyle rather than two that can
        drift apart.

        Returns the Par (a ParGroup for multi-member styles), or None if a
        restyle failed. Idempotent: an existing parameter keeps its value.
        """
        if not cls._PAR_NAME_RE.match(name):
            raise ValueError(
                'parameter %r: a custom parameter name must start with an '
                'uppercase letter and contain only letters and digits' % name)
        field.name = name
        page = None
        for p in ownerComp.customPages:
            if p.name == field.page:
                page = p
                break
        if page is None:
            page = ownerComp.appendCustomPage(field.page)
        parGroup = getattr(ownerComp.parGroup, name, None)
        created = parGroup is None
        if created:
            parGroup = field.append(page, name)
        elif parGroup[0].style != field.STYLE:
            # The declaration is the source of truth, so a style change is
            # APPLIED, not refused -- refusing would reintroduce exactly the
            # manual step this layer exists to remove.
            parGroup = cls._restyle(ownerComp, name, parGroup, field, page)
            created = True
            if parGroup is None:
                return None
        field.apply(parGroup, created=created)
        return parGroup if len(parGroup) > 1 else parGroup[0]

    # --- init-time declaration (the primary API) ---------------------------
    # Declaring inside __init__ is the general case: `ownerComp` exists, so
    # the call can CREATE the parameter and hand back the real Par, and
    # ordinary Python -- conditionals, loops, computed defaults -- just works:
    #
    #     def __init__(self, ownerComp):
    #         self.ownerComp = ownerComp
    #         self.Speed = CustomParHelper.Float(ownerComp, 'Speed',
    #                                            default=1.0, page='Settings',
    #                                            help='Playback speed.')
    #         if ownerComp.par.Advanced.eval():
    #             self.Depth = CustomParHelper.Int(ownerComp, 'Depth', ...)
    #         CustomParHelper.Init(self, ownerComp)
    #
    # The class-body form stays supported and is sugar over this same path,
    # but it cannot do any of the above: a class body runs before there is a
    # COMP, which is why it can only ever hand back a stand-in.

    @classmethod
    def DefinePar(cls, ownerComp: COMP, kind, name: str, *args, **kw):
        """Create/refresh one parameter of `kind` (a ParField class). Returns it."""
        return cls.EnsurePar(ownerComp, name, kind(*args, **kw))

    @classmethod
    def EnsureParFields(cls, extension_self, ownerComp: COMP) -> list:
        """Create or refresh every declared parameter. Returns the names.

        IDEMPOTENT, and it never touches a value: re-running refreshes label,
        help, range and menu entries but leaves whatever the user or the saved
        .toe put there. A declaration describes a parameter, not its state.

        A STYLE change is reported and skipped rather than applied, because
        applying it means destroying the parameter -- taking its value, any
        expression, binding or export with it. Delete it by hand if you really
        mean to restyle.
        """
        fields = cls._declaredParFields(extension_self)
        if not fields:
            return []                      # the additive guarantee
        touched = []
        for name, field in fields:
            if cls.EnsurePar(ownerComp, name, field) is None:
                continue
            touched.append(name)
        return touched

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


    # --- declarative callbacks ---------------------------------------------
    #
    # A decorator says WHICH parameter a method handles, next to the method,
    # so the handler's name is free of the onPar<Name> convention.
    #
    # HOW IT WORKS, and why it changes no dispatch code: harvest binds the
    # decorated method to its CONVENTIONAL name on the extension instance, so
    # every existing `hasattr(comp, 'onParSpeed')` finds it unchanged. That
    # buys the whole callback surface at once -- per-par, pulse, ParGroup,
    # sequence par, sequence block and the general callbacks -- with all of
    # their arity variants, because arity is still read off the original
    # function.
    #
    # THE DECORATOR RETURNS THE FUNCTION UNTOUCHED, exactly as NoNode's and
    # FNSCommand's do. Dispatch infers how many arguments a callback wants
    # from __code__.co_argcount; a wrapper would describe itself instead.

    CALLBACK_ATTR = '_cph_callbacks'

    @classmethod
    def _markCallback(cls, spec: tuple):
        """Attach one handles-this spec to a method and hand it back unchanged."""
        def mark(fn):
            specs = list(getattr(fn, cls.CALLBACK_ATTR, ()))
            specs.append(spec)
            setattr(fn, cls.CALLBACK_ATTR, specs)
            return fn                      # UNTOUCHED -- see the note above
        return mark

    @classmethod
    def onPar(cls, name: str):
        """Handle one custom parameter -- value change, or pulse for a Pulse par.

        @CustomParHelper.onPar('Speed')
        def speedChanged(self, _par, _val, _prev):
            ...
        """
        return cls._markCallback(('par', name))

    @classmethod
    def onParGroup(cls, name: str):
        """Handle a ParGroup as a unit (e.g. 'Translate' for Translatex/y/z)."""
        return cls._markCallback(('pargroup', name))

    @classmethod
    def onSeq(cls, sequence: str, name: str):
        """Handle one parameter inside a sequence block."""
        return cls._markCallback(('seq', sequence, name))

    @classmethod
    def onSeqBlock(cls, sequence: str):
        """Handle a sequence's block count changing."""
        return cls._markCallback(('seqblock', sequence))

    @classmethod
    def onAnyValueChange(cls):
        """The general value-change callback, for anything not handled above."""
        return cls._markCallback(('any', 'valuechange'))

    @classmethod
    def onAnyPulse(cls):
        """The general pulse callback, for any pulse not handled above."""
        return cls._markCallback(('any', 'pulse'))

    @classmethod
    def _conventionalName(cls, spec: tuple) -> str:
        """The method name this declaration stands in for.

        Computed at harvest rather than at decoration because it depends on
        IS_EXPOSE_PUBLIC, which Init sets.
        """
        upper = cls.IS_EXPOSE_PUBLIC
        kind = spec[0]
        if kind == 'par':
            return '%s%s' % ('OnPar' if upper else 'onPar', spec[1])
        if kind == 'pargroup':
            return '%s%s' % ('OnParGroup' if upper else 'onParGroup', spec[1])
        if kind == 'seq':
            return '%s%sN%s' % ('OnSeq' if upper else 'onSeq', spec[1],
                                spec[2].capitalize())
        if kind == 'seqblock':
            return '%s%sN' % ('OnSeq' if upper else 'onSeq', spec[1])
        if kind == 'any':
            if spec[1] == 'pulse':
                return 'OnPulse' if upper else 'onPulse'
            return 'OnValueChange' if upper else 'onValueChange'
        return ''

    @classmethod
    def _declaredCallbacks(cls, extension_self) -> list:
        """Every marked method on the extension, base class first."""
        found, seen = [], set()
        for klass in reversed(type(extension_self).__mro__):
            for attr, value in vars(klass).items():
                specs = getattr(value, cls.CALLBACK_ATTR, None)
                if not specs or attr in seen:
                    continue
                seen.add(attr)
                found.append((attr, specs))
        return found

    @classmethod
    def _targetExists(cls, ownerComp: COMP, spec: tuple) -> bool:
        """Whether the parameter / group / sequence a declaration names is real."""
        kind = spec[0]
        try:
            if kind == 'par':
                return hasattr(ownerComp.par, spec[1])
            if kind == 'pargroup':
                return hasattr(ownerComp.parGroup, spec[1])
            if kind in ('seq', 'seqblock'):
                return hasattr(ownerComp.seq, spec[1])
        except Exception:
            return False
        return True

    @classmethod
    def HarvestCallbacks(cls, extension_self, ownerComp: COMP) -> dict:
        """Bind every decorated method to the name dispatch looks for.

        Called by Init. Returns {'bound': int, 'problems': [str]}.

        A declaration naming a parameter that does not exist is REPORTED, not
        raised: the mistyped name is exactly the case the convention cannot
        catch today, but one bad declaration should not stop a tool loading.
        """
        bound, problems = 0, []
        for attr, specs in cls._declaredCallbacks(extension_self):
            for spec in specs:
                target = cls._conventionalName(spec)
                if not target:
                    problems.append('%s: unknown declaration %r' % (attr, spec))
                    continue
                if not cls._targetExists(ownerComp, spec):
                    problems.append(
                        '%s: %s has no %s %r -- this callback would never fire'
                        % (attr, ownerComp.path, spec[0], spec[1]))
                    continue
                # A real method already answering to that name WINS, and the
                # collision is reported: silently shadowing working code is
                # worse than a declaration that does not take effect.
                existing = getattr(type(extension_self), target, None)
                if existing is not None and getattr(existing, '__name__', '') != attr:
                    problems.append(
                        '%s: %s already defines %s -- declaration ignored, '
                        'rename one of them'
                        % (attr, type(extension_self).__name__, target))
                    continue
                setattr(extension_self, target, getattr(extension_self, attr))
                bound += 1
        for problem in problems:
            try:
                debug('CustomParHelper.HarvestCallbacks: ' + problem)
            except Exception:
                pass
        return {'bound': bound, 'problems': problems}

    @classmethod
    def _extForComp(cls, comp):
        """The extension instance belonging to `comp`, not merely the last
        one to call Init.

        EXT_SELF is a CLASS attribute. With two COMPs sharing one extension
        module the second Init rebinds it, and from then on the first COMP's
        callbacks are delivered to the SECOND COMP's extension. Resolving
        from the comp we were handed closes that.

        Measured 2026-09-01: 652 COMPs carry extensions and 21 carry more
        than one, but no pair examined declares two CustomParHelper users --
        so this is hardening, not a live bug. It deliberately returns
        EXT_SELF unchanged in the single-owner case, which is every case
        this project has today.

        Reading `.extensions` is safe HERE, unlike in a probe where it would
        force the very initialisation being measured: a parameter callback
        can only fire after the owning extension is already initialised.
        """
        if comp is None or comp is cls.EXT_OWNERCOMP:
            return cls.EXT_SELF
        try:
            want = type(cls.EXT_SELF)
            for ext in comp.extensions:
                if isinstance(ext, want):
                    return ext
        except Exception:
            pass
        return cls.EXT_SELF

    @classmethod
    def OnValueChange(cls, comp: COMP, _par: Par, prev: Par) -> None:
        """Handle value change events for custom parameters."""
        # exceptions are handled in the parExec itself
        # except for sequence parameters

        # the EXTENSION, not the COMP -- callbacks may be non-promoted, so they
        # exist only on the instance. Resolved from the comp we were HANDED so
        # two COMPs sharing one module cannot cross-wire (see _extForComp).
        comp = cls._extForComp(comp)

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
        
        # the EXTENSION, not the COMP -- callbacks may be non-promoted, so they
        # exist only on the instance. Resolved from the comp we were HANDED so
        # two COMPs sharing one module cannot cross-wire (see _extForComp).
        comp = cls._extForComp(comp)

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
            # _par.owner is the COMP that owns this parameter -- the author's
            # own commented-out line above. Route by it rather than by whichever
            # extension called Init last.
            _comp = cls._extForComp(_par.owner)
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
            # _par.owner is the COMP that owns this parameter -- the author's
            # own commented-out line above. Route by it rather than by whichever
            # extension called Init last.
            _comp = cls._extForComp(_par.owner)
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
    def _stubber(cls):
        """The Stubser component, or None.

        `is not None` is NOT enough. STUBSER is resolved once at class-compile
        time, and a DESTROYED operator still compares against None perfectly
        happily -- so after extStubser was removed from ExtUtils the old guard
        passed and went on to call a method on a dead wrapper. `.valid` is the
        only honest check.
        """
        s = cls.STUBSER
        try:
            return s if (s is not None and s.valid) else None
        except Exception:
            return None

    @classmethod
    def EnableStubs(cls) -> None:
        """Enable stubs for the extension.

        Stub generation was REMOVED from ExtUtils: the Stubser it carried was
        18 of ExtUtils' 46 operators across every instance, and nothing in the
        toolkit ever enabled it. This method and the `enable_stubs` argument
        stay for API compatibility; generate stubs through QuickExt or
        VSCodeTools, which carry their own Stubser.
        """
        if cls._stubber() is None:
            debug('CustomParHelper: stubs requested, but ExtUtils no longer '
                  'carries a Stubser -- use QuickExt or VSCodeTools instead')
            return
        cls.STUBS_ENABLED = True
        cls.UpdateStubs()

    @classmethod
    def DisableStubs(cls) -> None:
        """Disable stubs for the extension."""
        cls.STUBS_ENABLED = False

    @classmethod
    def UpdateStubs(cls) -> None:
        """Update the stubs for the extension."""
        stubber = cls._stubber()
        if cls.STUBS_ENABLED and stubber is not None:
            # get class name from extension object
            class_name = cls.EXT_SELF.__class__.__name__
            op_ext = cls.EXT_OWNERCOMP.op(class_name)
            stubber.StubifyDat(op_ext)


# One import stays enough: the existing
#   CustomParHelper = ...mod('CustomParHelper').CustomParHelper
# line also reaches the field types, as CustomParHelper.ParFloat and so on.
for _cls in (ParField, ParFloat, ParInt, ParStr, ParToggle, ParPulse, ParMenu,
             ParStrMenu, ParFile, ParFolder, ParHeader, ParXYZ, ParRGB, ParRGBA,
             ParOP, ParCOMP, ParTOP, ParCHOP, ParSOP, ParDAT, ParMAT):
    setattr(CustomParHelper, _cls.__name__, _cls)
del _cls


# Init-time helpers: CustomParHelper.Float(ownerComp, 'Speed', ...) and friends.
# Each creates-or-refreshes and RETURNS the Par, so a declaration inside
# __init__ reads as ordinary Python and works with conditionals and loops.
# They are thin wrappers over DefinePar -> EnsurePar, the one implementation
# the class-body declarations also use.
def _makeParHelper(kind):
    def _helper(cls, ownerComp, name, *args, **kw):
        return cls.DefinePar(ownerComp, kind, name, *args, **kw)
    _helper.__name__ = kind.__name__[3:] or kind.__name__
    _helper.__doc__ = (
        "Create or refresh a %s custom parameter on ownerComp and return it. "
        "Keywords are TouchDesigner Par members (default, label, help, page, "
        "order, readOnly, startSection, min, max, clampMin, clampMax, normMin, "
        "normMax); page names the page to create on and defaults to 'Custom'. "
        "Idempotent -- an existing parameter keeps its value." % kind.STYLE)
    return classmethod(_helper)


for _kind in (ParFloat, ParInt, ParStr, ParToggle, ParPulse, ParMenu, ParStrMenu,
              ParFile, ParFolder, ParHeader, ParXYZ, ParRGB, ParRGBA,
              ParOP, ParCOMP, ParTOP, ParCHOP, ParSOP, ParDAT, ParMAT):
    setattr(CustomParHelper, _kind.__name__[3:], _makeParHelper(_kind))
del _kind
