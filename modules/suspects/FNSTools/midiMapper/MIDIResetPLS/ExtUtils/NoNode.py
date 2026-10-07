

'''Info Header Start
Name : NoNode
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
import re
import TDStoreTools
from typing import Callable, Dict, Union, List
from enum import Enum, auto


class NoNode:
    '''
    ## NoNode

    NoNode is a versatile utility class that centralizes the management of various types of executions and callbacks in TouchDesigner, eliminating the need for dedicated nodes.

    ### Key Features:
    - Keyboard shortcut handling
    - CHOP executions (value changes, on/off states)
    - DAT executions (table, row, or cell changes)
    - Centralized event management
    - Reduced node clutter
    - Visual indication of watched operators

    ### Usage examples:
    1. Make sure ExtUtils is docked to your extension

    2. Import the NoNode class:
    ```python
    NoNode: NoNode = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('NoNode').NoNode # import
    ```

    3. Initialize the NoNode system in your extension:
    ```python
    NoNode.Init(enable_chopexec=True, enable_datexec=True, enable_parexec=True, enable_keyboard_shortcuts=True)
    ```

    4. CHOP executions:
    - Register a callback for CHOP value changes:
        ```python
        NoNode.RegisterChopExec(NoNode.ChopExecType.ValueChange, chop_op, channel_name(s), self.on_value_change_function)
        # callback signature: def on_value_change_function(self, channel: Channel, sampleIndex: int, val: float, prev: float):
        # can omit parameters from the right side of the signature if not needed
        ```
    - Handle CHOP state changes:
        ```python
        NoNode.RegisterChopExec(NoNode.ChopExecType.OffToOn, chop_op, channel_name(s), self.on_activate_function)
        # callback signature: def on_activate_function(self, channel: Channel, sampleIndex: int, val: float, prev: float):
        # can omit parameters from the right side of the signature if not needed
        ```

    5. DAT executions:
    - React to table changes in a DAT:
        ```python
        NoNode.RegisterDatExec(NoNode.DatExecType.TableChange, dat_op, self.on_table_change_function)
        # callback signature depends on the event type, eg.: def on_table_change_function(self, dat: DAT):
        ```
    - Handle cell value changes:
        ```python
        NoNode.RegisterDatExec(NoNode.DatExecType.CellChange, dat_op, self.on_cell_change_function)
        # callback signature depends on the event type, eg.: def on_cell_change_function(self, dat: DAT, cells: list[Cell], prev: Cell):
        ```

    6. Parameter executions:
    - Register a callback for parameter value changes:
        ```python
        NoNode.RegisterParExec(NoNode.ParExecType.ValueChange, par_op, par_name, self.on_value_change_function)
        # callback signature depends on the event type, eg.: def on_value_change_function(self, par: Par, val: float, prev: float):
        # can omit prev, or use val only
        ```
    - Handle pulse parameters:
        ```python
        NoNode.RegisterParExec(NoNode.ParExecType.OnPulse, par_op, par_name, self.on_pulse_function)
        # callback signature: def on_pulse_function(self,par: Par):
        # can omit par if not needed
        ```

    7. Keyboard shortcuts:
    - Register a keyboard shortcut:
        ```python
        NoNode.RegisterKeyboardShortcut('ctrl.k', self.onKeyboardShortcut)
        # callback signature: def onKeyboardShortcut(self):
        ```

    7. Deregister callbacks:
    - Deregister a CHOP execution:
        ```python
        NoNode.DeregisterChopExec(NoNode.ChopExecType.ValueChange, chop_op, channel_name(s))
        ```
    - Deregister a DAT execution:
        ```python
        NoNode.DeregisterDatExec(NoNode.DatExecType.TableChange, dat_op)
        ```
    - Deregister a parameter execution:
        ```python
        NoNode.DeregisterParExec(NoNode.ParExecType.ValueChange, par_op, par_name)
        ```  
    - Deregister a keyboard shortcut:
        ```python
        NoNode.DeregisterKeyboardShortcut('ctrl.k')
        ```

    8. Visual indication:
    - Operators with registered callbacks are marked with a color for easy identification
    - Customize the mark color:
        ```python
        NoNode.SetMarkColor((r, g, b))
        ```

    '''

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

    class ParExecType(Enum):
        ValueChange = auto()
        OnPulse = auto()

    MARK_COLOR = (0.5, 0.05, 0.5)

    CHOP_VALUECHANGE_EXEC: DAT = op('extChopValueChangeExec')
    CHOP_OFFTOON_EXEC: DAT = op('extChopOffToOnExec')
    CHOP_ONTOOFF_EXEC: DAT = op('extChopOnToOffExec')
    CHOP_WHILEON_EXEC: DAT = op('extChopWhileOnExec')
    CHOP_WHILEOFF_EXEC: DAT = op('extChopWhileOffExec')

    DAT_TABLECHANGE_EXEC: DAT = op('extDatTableChangeExec')
    DAT_ROWCHANGE_EXEC: DAT = op('extDatRowChangeExec')
    DAT_COLCHANGE_EXEC: DAT = op('extDatColChangeExec')
    DAT_CELLCHANGE_EXEC: DAT = op('extDatCellChangeExec')
    DAT_SIZECHANGE_EXEC: DAT = op('extDatSizeChangeExec')

    KEYBOARD_EXEC: DAT = op('extKeyboardIn')

    CHOP_EXECS: list[DAT] = [CHOP_VALUECHANGE_EXEC, CHOP_OFFTOON_EXEC, CHOP_ONTOOFF_EXEC, CHOP_WHILEON_EXEC, CHOP_WHILEOFF_EXEC]
    DAT_EXECS: list[DAT] = [DAT_TABLECHANGE_EXEC, DAT_ROWCHANGE_EXEC, DAT_COLCHANGE_EXEC, DAT_CELLCHANGE_EXEC, DAT_SIZECHANGE_EXEC]
    
    CHOP_EXEC_MAP: Dict[ChopExecType, COMP] = {
        ChopExecType.ValueChange: CHOP_VALUECHANGE_EXEC,
        ChopExecType.OffToOn: CHOP_OFFTOON_EXEC,
        ChopExecType.OnToOff: CHOP_ONTOOFF_EXEC,
        ChopExecType.WhileOn: CHOP_WHILEON_EXEC,
        ChopExecType.WhileOff: CHOP_WHILEOFF_EXEC
    }

    DAT_EXEC_MAP: Dict[DatExecType, COMP] = {
        DatExecType.TableChange: DAT_TABLECHANGE_EXEC,
        DatExecType.RowChange: DAT_ROWCHANGE_EXEC,
        DatExecType.ColChange: DAT_COLCHANGE_EXEC,
        DatExecType.CellChange: DAT_CELLCHANGE_EXEC,
        DatExecType.SizeChange: DAT_SIZECHANGE_EXEC
    }

    CHOPEXEC_CALLBACKS: TDStoreTools.DependDict[ChopExecType, dict[CHOP, dict[str, Callable]]] = TDStoreTools.DependDict()
    DATEXEC_CALLBACKS: TDStoreTools.DependDict[DatExecType, dict[DAT, Callable]] = TDStoreTools.DependDict()
    KEYBOARD_CALLBACKS: TDStoreTools.DependDict[str, Callable] = TDStoreTools.DependDict()
    CHOPEXEC_IS_ENABLED: bool = False
    DATEXEC_IS_ENABLED: bool = False
    KEYBOARD_IS_ENABLED: bool = False

    # Add these class variables after other similar declarations
    PAR_VALUECHANGE_EXEC: DAT = op('extParExecNoNodeValueChange')
    PAR_ONPULSE_EXEC: DAT = op('extParExecNoNodeOnPulse')

    PAR_EXECS: list[DAT] = [PAR_VALUECHANGE_EXEC, PAR_ONPULSE_EXEC]

    PAR_EXEC_MAP: Dict[ParExecType, COMP] = {
        ParExecType.ValueChange: PAR_VALUECHANGE_EXEC,
        ParExecType.OnPulse: PAR_ONPULSE_EXEC
    }

    PAREXEC_CALLBACKS: TDStoreTools.DependDict[ParExecType, dict[OP, dict[Union[Par, str], Callable]]] = TDStoreTools.DependDict()
    PAREXEC_IS_ENABLED: bool = False

    # Update ALL_EXECS to include PAR_EXECS
    ALL_EXECS: list[DAT] = CHOP_EXECS + DAT_EXECS + PAR_EXECS + [KEYBOARD_EXEC]
    EXT_OWNER_COMP: COMP = None

    # --- operator identity across network edits ------------------------------
    # An OP's hash follows its PATH. Renaming an operator -- or ANY of its
    # ancestors -- therefore changes the hash of a key already stored in a
    # dict, stranding the entry in the wrong bucket: still present, still
    # EQUAL to the key, simply unreachable by lookup. Every registry below is
    # keyed by live OPs (the exec DATs' target parameters are literally
    # `list(<registry>.keys())`), so the shapes are kept exactly as they are
    # and the LOOKUPS are made tolerant instead.
    #
    # A MOVE is a different failure: TD destroys the operator and creates a
    # new one, so neither the reference nor the id survives, and the exec DAT
    # stops watching anything. Tags DO travel with a move, so a token stamped
    # at registration is the only durable handle back. See Heal().
    NONODE_TAG_PREFIX = 'nonode:'
    WATCH_TOKENS: dict = {}

    @classmethod
    def Init(cls, ownerComp, enable_chopexec: bool = True, enable_datexec: bool = True, enable_parexec: bool = True, 
             enable_keyboard_shortcuts: bool = True) -> None:
        """Initialize the NoNode functionality."""
        cls.EXT_OWNER_COMP = ownerComp
        cls.CHOPEXEC_IS_ENABLED = enable_chopexec
        cls.DATEXEC_IS_ENABLED = enable_datexec
        cls.KEYBOARD_IS_ENABLED = enable_keyboard_shortcuts
        cls.CHOPEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.DATEXEC_CALLBACKS = TDStoreTools.DependDict()
        cls.KEYBOARD_CALLBACKS = TDStoreTools.DependDict()
        cls.PAREXEC_IS_ENABLED = enable_parexec
        cls.PAREXEC_CALLBACKS = TDStoreTools.DependDict()
        
        #cls.__setOwnerCompToDocked(ownerComp)

        # Disable all execute operators by default
        for exec in cls.ALL_EXECS:
            if exec is not None:
                exec.par.active = False

        if enable_chopexec:
            cls.EnableChopExec()
        else:
            cls.DisableChopExec()

        if enable_datexec:
            cls.EnableDatExec()
        else:
            cls.DisableDatExec()

        if enable_keyboard_shortcuts:
            cls.EnableKeyboardShortcuts()
        else:
            cls.DisableKeyboardShortcuts()

        if enable_parexec:
            cls.EnableParExec()
        else:
            cls.DisableParExec()

    @classmethod
    def __setOwnerCompToDocked(cls, ownerComp: COMP) -> None:
        for _op in me.docked:
            if hasattr(_op.par, 'ops'):
                _op.par.ops.val = ownerComp
            if hasattr(_op.par, 'op'):
                _op.par.op.val = ownerComp

    ### CHOP and DAT Exec ###

    @classmethod       
    def EnableChopExec(cls) -> None:
        """Enable chopExec handling."""
        cls.CHOPEXEC_IS_ENABLED = True

    @classmethod
    def EnableDatExec(cls) -> None:
        """Enable datExec handling."""
        cls.DATEXEC_IS_ENABLED = True

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
    def DisableDatExec(cls, event_type: DatExecType = None) -> None:
        """Disable datExec handling for a specific event type or all event types."""
        if event_type is None:
            # disable all active operators
            for dat_exec in cls.DAT_EXECS:
                dat_exec.par.active = False
        elif event_type in cls.DAT_EXEC_MAP:
            cls.DAT_EXEC_MAP[event_type].par.active = False

    @classmethod
    def RegisterChopExec(cls, event_type: ChopExecType, chop: CHOP, channels: Union[str, List[str]], callback: Callable) -> None:
        """
        Register a CHOP execute callback.

        Args:
            event_type (ChopExecType): The type of event to listen for.
            chop (CHOP): The CHOP operator to register the callback for.
            channels (Union[str, List[str]]): The channel(s) to listen to. Can be a whitespace and/or comma separated string, or a list. Use '*' for all channels.
            callback (Callable): The callback function to be called on CHOP execution.

        Example:
            def my_callback(event_type, channel, index, value, prev):
                print(f"Event: {event_type}, Channel {channel} at index {index} changed from {prev} to {value}")
            
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), '*', my_callback)
            # Or with multiple channels:
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), ['chan1', 'chan2'], my_callback)
            # Or with comma and/or whitespace separated channels:
            NoNode.RegisterChopExec(ChopExecType.VALUE_CHANGE, op('constant1'), 'chan1, chan2 chan3,chan4', my_callback)
        """
        cls.Heal()
        if event_type not in cls.CHOPEXEC_CALLBACKS.getRaw():
            cls.CHOPEXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.CHOPEXEC_CALLBACKS.getDependency(event_type)
        # reach a stranded entry rather than adding a second key for the same
        # operator -- two keys would make the exec DAT watch it twice
        entry = cls._entryFor(current_callbacks.val, chop)
        if entry is None:
            entry = {}
            current_callbacks.val[chop] = entry
            cls.__markOperatorAsWatched(chop)

        if isinstance(channels, str):
            channels = re.split(r'[,\s]+', channels.strip())
        for channel in channels:
            entry[channel] = callback
        cls.CHOPEXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Enable the appropriate docked operator based on the event type
        if event_type in cls.CHOP_EXEC_MAP:
            cls.CHOP_EXEC_MAP[event_type].par.active = True

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
        cls.Heal()
        if event_type not in cls.DATEXEC_CALLBACKS.getRaw():
            cls.DATEXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.DATEXEC_CALLBACKS.getDependency(event_type)
        if cls._entryFor(current_callbacks.val, dat) is None:
            current_callbacks.val[dat] = callback
            cls.__markOperatorAsWatched(dat)
        cls.DATEXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Enable the appropriate docked operator based on the event type
        if event_type in cls.DAT_EXEC_MAP:
            cls.DAT_EXEC_MAP[event_type].par.active = True

    @classmethod
    def DeregisterChopExec(cls, event_type: ChopExecType, chop: CHOP = None, channels: Union[str, List[str]] = None) -> None:
        """
        Deregister a chopExec callback

        Args:
            event_type (ChopExecType): The event type to deregister.
            chop (CHOP, optional): The CHOP operator to deregister the callback for. If None, deregisters all CHOPs for the event type.
            channels (Union[str, List[str]], optional): The channel(s) to deregister. Can be a string (single channel, comma/space-separated list, or wildcard pattern) or a list of strings. If None, deregisters all channels for the specified CHOP.
        """
        if event_type not in cls.CHOPEXEC_CALLBACKS.getRaw():
            return
        inner = cls._raw(cls.CHOPEXEC_CALLBACKS.getRaw()[event_type])

        if chop is None:
            for registered_chop in list(inner.keys()):
                cls.__checkAndResetOperatorColor(registered_chop)
            del cls.CHOPEXEC_CALLBACKS[event_type]
        else:
            entry = cls._entryFor(inner, chop)
            if entry is not None:
                if channels is None:
                    entry.clear()
                else:
                    if isinstance(channels, str):
                        channels = re.split(r'[,\s]+', channels.strip())
                    for channel in channels:
                        for registered_channel in list(entry.keys()):
                            if channel == '*' or tdu.match(channel, [registered_channel]):
                                del entry[registered_channel]
                if not entry:
                    cls.CHOPEXEC_CALLBACKS.setItem(event_type,
                                                   cls._withoutKey(inner, chop))
                    cls.__checkAndResetOperatorColor(chop)

        raw = cls.CHOPEXEC_CALLBACKS.getRaw()
        if event_type in raw and not raw[event_type]:
            del cls.CHOPEXEC_CALLBACKS[event_type]
        # nothing left registered for this event type -> stop the exec DAT
        raw = cls.CHOPEXEC_CALLBACKS.getRaw()
        if event_type in raw:
            for registered in raw[event_type].values():
                if registered:
                    return
        cls.DisableChopExec(event_type)

    @classmethod
    def DeregisterDatExec(cls, event_type: DatExecType, dat: DAT = None) -> None:
        """
        Deregister a datExec callback

        Args:
            event_type (DatExecType): The event type to deregister.
            dat (DAT, optional): The DAT operator to deregister the callback for. If None, deregisters all DATs for the event type.
        """
        if event_type not in cls.DATEXEC_CALLBACKS.getRaw():
            return
        inner = cls._raw(cls.DATEXEC_CALLBACKS.getRaw()[event_type])

        if dat is None:
            for registered_dat in list(inner.keys()):
                cls.__checkAndResetOperatorColor(registered_dat)
            del cls.DATEXEC_CALLBACKS[event_type]
        elif cls._entryFor(inner, dat) is not None:
            cls.DATEXEC_CALLBACKS.setItem(event_type, cls._withoutKey(inner, dat))
            cls.__checkAndResetOperatorColor(dat)

        raw = cls.DATEXEC_CALLBACKS.getRaw()
        if event_type in raw and not raw[event_type]:
            del cls.DATEXEC_CALLBACKS[event_type]
        if not cls.DATEXEC_CALLBACKS.getRaw().get(event_type):
            cls.DisableDatExec(event_type)

    @classmethod
    def OnChopExec(cls, event_type: ChopExecType, channel: Channel, sampleIndex: int, val: float, prev: float) -> None:
        """Handle chopExec events."""
        if not cls.CHOPEXEC_IS_ENABLED:
            return
        cls.Heal()

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

        # execute the callback for the channel if it matches the event type
        if event_type in cls.CHOPEXEC_CALLBACKS:
            callbacks = cls._entryFor(cls.CHOPEXEC_CALLBACKS[event_type], chop) or {}
            executed_callbacks = set() # to avoid executing the same callback multiple times for the same channel
            for ch, callback in callbacks.items():
                channel_names = ch.split() if ch != '*' else ['*']
                for channel_name in channel_names:
                    if (channel_name == '*' or tdu.match(channel_name, [channel.name])) and (channel.name, callback) not in executed_callbacks:
                        execute_callback(callback)
                        executed_callbacks.add((channel.name, callback))
                        break  # Exit the inner loop after executing the callback

    @classmethod
    def OnDatExec(cls, event_type: DatExecType, dat: DAT, rows: int = None, cols: int = None, cells: list[Cell] = None, prev = None) -> None:
        """Handle datExec events."""
        if not cls.DATEXEC_IS_ENABLED:
            return
        cls.Heal()

        callback = None
        if event_type in cls.DATEXEC_CALLBACKS:
            callback = cls._entryFor(cls.DATEXEC_CALLBACKS[event_type], dat)
        if callback:
            arg_count = callback.__code__.co_argcount
            if arg_count == 1:
                callback()
            elif arg_count == 2:
                callback(dat)
            elif arg_count == 3:
                if event_type == cls.DatExecType.RowChange:
                    callback(dat, rows)
                elif event_type == cls.DatExecType.ColChange:
                    callback(dat, cols)
                elif event_type == cls.DatExecType.CellChange:
                    callback(dat, cells)
            elif arg_count == 4:
                callback(dat, cells, prev)


    ### Keyboard Shortcuts ###

    @classmethod
    def EnableKeyboardShortcuts(cls) -> None:
        """Enable keyboard shortcut handling."""
        cls.KEYBOARD_IS_ENABLED = True
        cls.KEYBOARD_EXEC.par.active = True

    @classmethod
    def DisableKeyboardShortcuts(cls) -> None:
        """Disable keyboard shortcut handling."""
        cls.KEYBOARD_IS_ENABLED = False
        cls.KEYBOARD_EXEC.par.active = False

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
        cls.KEYBOARD_CALLBACKS[shortcut] = callback

    @classmethod
    def DeregisterKeyboardShortcut(cls, shortcut: str) -> None:
        """Unregister a keyboard shortcut."""
        cls.KEYBOARD_CALLBACKS.pop(shortcut, None)


    @classmethod
    def OnKeyboardShortcut(cls, shortcut: str) -> None:
        """Handle keyboard shortcut events."""
        if cls.KEYBOARD_IS_ENABLED and shortcut in cls.KEYBOARD_CALLBACKS:
            cls.KEYBOARD_CALLBACKS[shortcut]()

    @classmethod
    def _entryFor(cls, inner, _op):
        """`inner[_op]`, tolerating a key stranded by a rename.

        The scan runs only when the hash lookup misses, and only over the
        handful of operators one extension watches, so it costs nothing in
        the normal case. Identity is checked first because TD hands back the
        same wrapper object for a given node; the id comparison covers the
        rest.
        """
        if not inner:
            return None
        # A DependDict's Mapping.items() walks through its __getitem__, which
        # raises KeyError on precisely the stranded keys this is here to find.
        # Normalise to the plain dict before touching it.
        inner = cls._raw(inner)
        try:
            hit = inner.get(_op)
        except Exception:
            hit = None
        if hit is not None:
            return hit
        for k, v in inner.items():
            try:
                if k is _op or (k.valid and _op is not None and k.id == _op.id):
                    return v
            except Exception:
                continue
        return None

    @classmethod
    def _raw(cls, d):
        """The plain dict behind a DependDict (or d itself)."""
        try:
            return d.getRaw() if hasattr(d, 'getRaw') else d
        except Exception:
            return d

    @classmethod
    def _parEntryFor(cls, params, parameter):
        """`params[parameter]`, tolerating a Par key stranded by a rename.

        A Par's hash follows its owner's path, so it stands the same way.
        Within one owner a parameter name is unique, which makes the name the
        reliable identity once the hash is untrustworthy.
        """
        if not params:
            return None
        try:
            hit = params.get(parameter)
        except Exception:
            hit = None
        if hit is not None:
            return hit
        try:
            name = parameter.name
        except Exception:
            return None
        for k, v in params.items():
            try:
                if (k.name if hasattr(k, 'name') else k) == name:
                    return v
            except Exception:
                continue
        return None

    @classmethod
    def _withoutKey(cls, inner, _op):
        """`inner` minus _op's entry, tolerating a key stranded by a rename.

        `del inner[_op]` is a hash lookup too, so it cannot reach a stranded
        entry any more than a read can -- it either raises KeyError or misses
        silently, leaving the callback live. Rebuilding is the only way to
        drop one.
        """
        out, dropped = {}, False
        for k, v in inner.items():
            try:
                same = (k is _op) or (k.valid and _op is not None and k.id == _op.id)
            except Exception:
                same = False
            if same and not dropped:
                dropped = True
                continue
            out[k] = v
        return out

    @classmethod
    def _withoutParKey(cls, params, parameter):
        """`params` minus parameter's entry, matched by NAME.

        Par keys strand exactly like OP keys, so deletion has the same
        problem; within one owner the name is unique and reliable.
        """
        nm = parameter.name if hasattr(parameter, 'name') else parameter
        out = {}
        for k, v in params.items():
            try:
                if (k.name if hasattr(k, 'name') else k) == nm:
                    continue
            except Exception:
                pass
            out[k] = v
        return out

    @classmethod
    def _tokenFor(cls, _op) -> str:
        """The operator's nonode: tag, stamped if it does not have one yet."""
        for t in _op.tags:
            if t.startswith(cls.NONODE_TAG_PREFIX):
                return t
        token = '%s%d' % (cls.NONODE_TAG_PREFIX, _op.id)
        _op.tags.add(token)
        return token

    # --- declarative registration ------------------------------------------
    #
    # A decorator records WHAT a method listens to, next to the method, instead
    # of the caller wiring it up elsewhere with Register*(). It buys four things
    # the imperative form cannot: the binding is visible at the callback, the
    # method name is free, a target that does not resolve is REPORTED at harvest
    # instead of silently never firing, and -- because harvest rebuilds the
    # registry from the class every time -- there is nothing left stale to
    # deregister, which is the defect class behind items 2d and 2e.
    #
    # THE MARKER ATTRIBUTE IS THE CONTRACT, exactly as FNSCommand does it: the
    # decorator records a spec and RETURNS THE FUNCTION UNTOUCHED. Wrapping
    # would break arity inference (co_argcount would describe the wrapper, not
    # the callback) and would make a vendored copy version-dependent.
    #
    # Targets are given as STRINGS and resolved at HARVEST, never at decoration:
    # a class body runs before any COMP exists, so op('null_hk') there resolves
    # against nothing. The same constraint the parameter fields ran into.

    CALLBACK_ATTR = '_nonode_callbacks'

    @classmethod
    def _markCallback(cls, spec):
        """Attach one listen-spec to a method and hand it back unchanged."""
        def mark(fn):
            specs = list(getattr(fn, cls.CALLBACK_ATTR, ()))
            specs.append(spec)
            setattr(fn, cls.CALLBACK_ATTR, specs)
            return fn                      # UNTOUCHED -- see the note above
        return mark

    @classmethod
    def onParExec(cls, event_type, owner=None, parameter=None):
        """Listen to a parameter. `owner` defaults to the extension's own COMP.

        @NoNode.onParExec(NoNode.ParExecType.VALUECHANGE, 'null_hk', 'shift')
        def shiftChanged(self, par, prev):
            ...
        """
        return cls._markCallback({'kind': 'par', 'event': event_type,
                                  'target': owner, 'detail': parameter})

    @classmethod
    def onChopExec(cls, event_type, chop, channels='*'):
        """Listen to CHOP channels.

        @NoNode.onChopExec(NoNode.ChopExecType.VALUECHANGE, 'null_mod', '*')
        def modChanged(self, channel, sampleIndex, val, prev):
            ...
        """
        return cls._markCallback({'kind': 'chop', 'event': event_type,
                                  'target': chop, 'detail': channels})

    @classmethod
    def onDatExec(cls, event_type, dat):
        """Listen to a DAT."""
        return cls._markCallback({'kind': 'dat', 'event': event_type,
                                  'target': dat, 'detail': None})

    @classmethod
    def onKeyboardShortcut(cls, shortcut):
        """Listen to a keyboard shortcut, e.g. 'ctrl.k'."""
        return cls._markCallback({'kind': 'key', 'event': None,
                                  'target': None, 'detail': shortcut})

    @classmethod
    def _resolveTarget(cls, ownerComp, target):
        """A decorator's target -> an OP. Strings resolve from ownerComp."""
        if target is None:
            return ownerComp
        if isinstance(target, str):
            return (ownerComp.op(target) if ownerComp else None) or op(target)
        return target

    @classmethod
    def _decoratedCallbacks(cls, extension_self):
        """Every marked method on the extension, base class first."""
        found, seen = [], set()
        for klass in reversed(type(extension_self).__mro__):
            for name, value in vars(klass).items():
                specs = getattr(value, cls.CALLBACK_ATTR, None)
                if not specs or name in seen:
                    continue
                seen.add(name)
                found.append((name, getattr(extension_self, name), specs))
        return found

    @classmethod
    def HarvestCallbacks(cls, extension_self, ownerComp=None) -> dict:
        """Register every decorated method on `extension_self`.

        Call AFTER NoNode.Init: Init clears the callback stores, so harvesting
        after it means the registry is REBUILT from the class rather than added
        to, and a callback deleted from the code disappears with it. That is the
        property the imperative Register/Deregister pair could not give.

        Needs nothing from CustomParHelper -- a tool that wants only callbacks
        can use NoNode.Init + HarvestCallbacks and never touch the rest.

        Returns {'registered': int, 'problems': [str]}. A target that does not
        resolve is REPORTED, not raised: one bad spec should not stop a tool
        loading, but it must not vanish silently either, which is exactly what
        a mistyped onParSpeeed does today.
        """
        comp = ownerComp if ownerComp is not None else (
            getattr(extension_self, 'ownerComp', None) or cls.EXT_OWNER_COMP)
        registered, problems = 0, []
        for name, bound, specs in cls._decoratedCallbacks(extension_self):
            for spec in specs:
                kind, event = spec['kind'], spec['event']
                try:
                    if kind == 'key':
                        cls.RegisterKeyboardShortcut(spec['detail'], bound)
                        registered += 1
                        continue
                    target = cls._resolveTarget(comp, spec['target'])
                    if target is None or not target.valid:
                        problems.append(
                            '%s: %r does not resolve from %s'
                            % (name, spec['target'],
                               comp.path if comp else '(no ownerComp)'))
                        continue
                    if kind == 'par':
                        par = spec['detail']
                        if isinstance(par, str) and not hasattr(target.par, par):
                            problems.append(
                                '%s: %s has no parameter %r -- this callback '
                                'would never fire' % (name, target.path, par))
                            continue
                        cls.RegisterParExec(event, target, par, bound)
                    elif kind == 'chop':
                        cls.RegisterChopExec(event, target, spec['detail'], bound)
                    elif kind == 'dat':
                        cls.RegisterDatExec(event, target, bound)
                    else:
                        problems.append('%s: unknown callback kind %r' % (name, kind))
                        continue
                    registered += 1
                except Exception as e:
                    problems.append('%s: %s: %s' % (name, type(e).__name__, e))
        for problem in problems:
            try:
                debug('NoNode.HarvestCallbacks: ' + problem)
            except Exception:
                pass
        return {'registered': registered, 'problems': problems}

    @classmethod
    def Heal(cls) -> dict:
        """Re-seat registrations whose operator was MOVED.

        A move destroys the operator and creates a new one, so the stored key
        goes invalid and the exec DAT -- whose target parameter IS the key
        list -- stops watching. Dispatch can therefore never heal a move on
        its own; something has to notice out of band, which is what this is.

        The nonode: tag travels with the move, so the replacement can be
        found and the entry rebound. The project-wide tag search is paid for
        ONLY when a dead key actually exists; the common case is a cheap scan
        that writes nothing. Renames need no repair here -- `_entryFor`
        already tolerates them.

        Called at the top of every Register*; safe to call by hand.
        """
        summary = {'checked': 0, 'rebound': 0, 'pruned': 0}
        stores = (cls.CHOPEXEC_CALLBACKS, cls.DATEXEC_CALLBACKS,
                  cls.PAREXEC_CALLBACKS)

        dead_tokens = set()
        for store in stores:
            for inner in store.getRaw().values():
                for k in list(inner.keys()):
                    summary['checked'] += 1
                    try:
                        if not k.valid:
                            tok = cls.WATCH_TOKENS.get(k.id)
                            if tok:
                                dead_tokens.add(tok)
                    except Exception:
                        pass
        if not dead_tokens:
            return summary

        found = {}
        for tok in dead_tokens:
            try:
                hits = op('/').findChildren(tags=[tok])
            except Exception:
                hits = []
            found[tok] = hits[0] if hits else None

        for store in stores:
            for event_type, inner in list(store.getRaw().items()):
                rebuilt, changed = {}, False
                for k, v in inner.items():
                    try:
                        alive = k.valid
                    except Exception:
                        alive = False
                    if alive:
                        rebuilt[k] = v
                        continue
                    changed = True
                    tok = cls.WATCH_TOKENS.pop(k.id, None)
                    new_op = found.get(tok) if tok else None
                    if new_op is None:
                        summary['pruned'] += 1
                        continue
                    # a moved owner's Par keys died with it -- re-seat them by
                    # name against the operator that replaced it
                    if isinstance(v, dict):
                        remapped = {}
                        for pk, pv in v.items():
                            nm = pk.name if hasattr(pk, 'name') else pk
                            np = getattr(new_op.par, nm, None) if isinstance(nm, str) else None
                            remapped[np if np is not None else pk] = pv
                        v = remapped
                    rebuilt[new_op] = v
                    cls.WATCH_TOKENS[new_op.id] = tok
                    summary['rebound'] += 1
                if changed:
                    store.setItem(event_type, rebuilt)
        return summary

    @classmethod
    def __markOperatorAsWatched(cls, _op: OP) -> None:
        """Colour the operator, and stamp the token a MOVE cannot destroy."""
        if _op is None or not _op.valid:
            return
        _op.color = cls.MARK_COLOR
        try:
            cls.WATCH_TOKENS[_op.id] = cls._tokenFor(_op)
        except Exception:
            pass

    @classmethod
    def __resetOperatorColor(cls, _op: OP) -> None:
        """Reset an operator's color to the default, and drop its token."""
        if _op is None or not _op.valid:
            return
        _op.color = (0.55, 0.55, 0.55) # td default color, probably available somewhere in the TD API/vars
        try:
            for t in list(_op.tags):
                if t.startswith(cls.NONODE_TAG_PREFIX):
                    _op.tags.remove(t)
            cls.WATCH_TOKENS.pop(_op.id, None)
        except Exception:
            pass

    @classmethod
    def __checkAndResetOperatorColor(cls, _op: OP) -> None:
        """Check if an operator is still registered for any event type, and reset its color if not."""
        for event_type in cls.CHOPEXEC_CALLBACKS.getRaw().keys() | cls.DATEXEC_CALLBACKS.getRaw().keys():
            if (cls._entryFor(cls.CHOPEXEC_CALLBACKS.getRaw().get(event_type, {}), _op) is not None
                    or cls._entryFor(cls.DATEXEC_CALLBACKS.getRaw().get(event_type, {}), _op) is not None):
                return
        cls.__resetOperatorColor(_op)

    @classmethod
    def SetMarkColor(cls, color: tuple[float, float, float]) -> None:
        """Set the mark color."""
        cls.MARK_COLOR = color
        # list all registered operators (chops and dats) and update their color
        for event_type in cls.CHOPEXEC_CALLBACKS.getRaw().keys() | cls.DATEXEC_CALLBACKS.getRaw().keys():
            for _op in cls.CHOPEXEC_CALLBACKS.getRaw().get(event_type, {}).keys() | cls.DATEXEC_CALLBACKS.getRaw().get(event_type, {}).keys():
                if _op is not None and _op.valid:
                    _op.color = cls.MARK_COLOR

    ### Parameter Exec ###

    @classmethod
    def EnableParExec(cls) -> None:
        """Enable parameter execute handling."""
        cls.PAREXEC_IS_ENABLED = True

    @classmethod
    def DisableParExec(cls, event_type: ParExecType = None) -> None:
        """Disable parameter execute handling for a specific event type or all event types."""
        if event_type is None:
            for par_exec in cls.PAR_EXECS:
                par_exec.par.active = False
        elif event_type in cls.PAR_EXEC_MAP:
            cls.PAR_EXEC_MAP[event_type].par.active = False

    @classmethod
    def RegisterParExec(cls, event_type: ParExecType, owner: OP, parameter: Union[Par, str], callback: Callable) -> None:
        """
        Register a parameter execute callback.

        Args:   
            event_type (ParExecType): The type of event to listen for.
            owner (OP): The operator that owns the parameter.
            parameter (Union[Par, str]): The parameter to watch. Can be a Par object or parameter name.
            callback (Callable): The callback function to be called on parameter execution.

        Example:
            def my_callback(par, prev):
                print(f"Parameter {par} changed from {prev} to {par.eval()}")
            
            # Using Par object from any operator
            NoNode.RegisterParExec(op('base1'), ParExecType.ValueChange, op('base1').par.v, self.my_callback)
        """
        cls.Heal()
        if event_type not in cls.PAREXEC_CALLBACKS.getRaw():
            cls.PAREXEC_CALLBACKS.setItem(event_type, {}, raw=True)

        current_callbacks = cls.PAREXEC_CALLBACKS.getDependency(event_type)

        # Handle owner resolution
        owner = owner or cls.EXT_OWNER_COMP
        entry = cls._entryFor(current_callbacks.val, owner)
        if entry is None:
            entry = {}
            current_callbacks.val[owner] = entry

        # Convert string parameter reference to Par object if needed
        if isinstance(parameter, str):
            if not hasattr(owner.par, parameter):
                return
            parameter = owner.par[parameter]

        # Mark the operator
        if owner is not cls.EXT_OWNER_COMP:
            cls.__markOperatorAsWatched(owner)

        entry[parameter] = callback
        cls.PAREXEC_CALLBACKS.setItem(event_type, current_callbacks)

        if event_type in cls.PAR_EXEC_MAP:
            cls.PAR_EXEC_MAP[event_type].par.active = True

    @classmethod
    def DeregisterParExec(cls, event_type: ParExecType, owner: OP, parameter: Union[Par, str] = None) -> None:
        """
        Deregister a parameter execute callback.

        Args:
            event_type (ParExecType): The event type to deregister. 
            owner (OP): The operator that owns the parameter.
            parameter (Union[Par, str], optional): The parameter to deregister. If None, deregisters all parameters for the owner.
           
        """
        if event_type not in cls.PAREXEC_CALLBACKS.getRaw():
            return

        current_callbacks = cls.PAREXEC_CALLBACKS.getDependency(event_type)
        
        # Handle owner resolution
        owner = owner or cls.EXT_OWNER_COMP

        if parameter is None:
            if cls._entryFor(current_callbacks.val, owner) is not None:
                current_callbacks.val = cls._withoutKey(current_callbacks.val, owner)
                cls.__checkAndResetOperatorColor(owner)
        else:
            # Convert string parameter reference to Par object if needed
            if isinstance(parameter, str):
                if not hasattr(owner.par, parameter):
                    return
                parameter = owner.par[parameter]

            params = cls._entryFor(cls._raw(current_callbacks.val), owner)
            if params is not None and cls._parEntryFor(params, parameter) is not None:
                remaining = cls._withoutParKey(params, parameter)
                if remaining:
                    # rebuild the outer map too: the owner key may itself be
                    # stranded, so it cannot be reassigned by subscript
                    rebuilt = {}
                    for k, v in current_callbacks.val.items():
                        try:
                            same = (k is owner) or (k.valid and k.id == owner.id)
                        except Exception:
                            same = False
                        rebuilt[k] = remaining if same else v
                    current_callbacks.val = rebuilt
                else:
                    current_callbacks.val = cls._withoutKey(current_callbacks.val, owner)
                    cls.__checkAndResetOperatorColor(owner)

        # Update callbacks
        cls.PAREXEC_CALLBACKS.setItem(event_type, current_callbacks)

        # Disable exec if no more callbacks
        if not current_callbacks.val:
            cls.DisableParExec(event_type)

    @classmethod
    def OnParExec(cls, event_type: ParExecType, parameter: Par, value = None, prev = None) -> None:
        """Handle parameter execute events."""

        if not cls.PAREXEC_IS_ENABLED:
            return
        cls.Heal()

        if event_type not in cls.PAREXEC_CALLBACKS.getRaw():
            return

        owner = parameter.owner
        params = cls._entryFor(cls.PAREXEC_CALLBACKS.getRaw()[event_type], owner)
        if not params:
            return

        callback = cls._parEntryFor(params, parameter)

        if callback:
            arg_count = callback.__code__.co_argcount
            if arg_count == 1:
                callback()
            elif arg_count == 2:
                callback(value if event_type == cls.ParExecType.ValueChange else parameter)
            elif arg_count == 3:
                callback(parameter, value)
            elif arg_count == 4:
                callback(parameter, value, prev)
