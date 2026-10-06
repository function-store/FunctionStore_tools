
'''Info Header Start
Name : QuickmarkStorageExt
Author : Dan@DAN-4090
Saveorigin : FNSTools_PRIV.toe
Saveversion : 2025.33070
Info Header End'''
### Code and idea from Alex Guevara
### Modified by Function Store

import json
from datetime import datetime
from TDStoreTools import StorageManager

TDF = op.TDModules.mod.TDFunctions

def fnsLog(*args, level='INFO'):
    """Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
    the logger is absent (standalone installs) or its Active par is off."""
    try:
        _logger = op.FNS.op('logger')
        if _logger and _logger.par.Active.eval():
            _logger.Log(*args, level=level)
    except Exception:
        pass




FNSCommand = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('FNSCommand') # import

class QuickmarkStorageExt:
    """Quickmarks, stored on a custom parameter sequence.

    The store used to be a StorageManager, which had two costs: storage does
    not roam with the toolkit's config and is not visible or editable in the
    UI, so a mark could never carry a NAME the user could read or change. The
    sequence fixes both -- custom parameters travel with the project, roam
    through the config host's pars rail, and each block's Name is free text.

    Block N is the slot reached by ctrl+N, so the first ten line up with the
    hotkeys. The sequence may hold more; those are reachable by command.

    The legacy storage is still declared and is read once by the migration,
    then left alone as a backup. Nothing reads it afterwards.
    """

    SLOTS = 10

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        # legacy store -- migration source only, see _migrateFromStorage
        storedItems = [{'name': f'Quickmark{i}', 'default': None} for i in range(self.SLOTS)]
        self.stored = StorageManager(self, ownerComp, storedItems)

        self._migrateFromStorage()
        fnsLog('QuickMarks: init')

    def onInitTD(self):
        # The slim ExtUtils carries no announcer, so this tool registers its
        # quick-launch commands itself: deferred past the registry's /sys
        # promotion and this module's own compile.
        run('args[0]._announceCommands()', self, delayFrames=60, delayRef=op.TDResources)

    def _announceCommands(self):
        FNSCommand.announce(self.ownerComp)

    def custom_print(self, message):
        # Prints a message to the status bar and the console
        current_time = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"{current_time} {message}"

        ui.status = formatted_message
        fnsLog(f'QuickMarks: {message}')

    ### slot addressing ###

    def _slotIndex(self, slot):
        """Slot index from any of 3, '3' or 'Quickmark3'.

        The hotkey path builds 'Quickmark3' while the registered commands pass
        a bare int; before this they addressed different keys entirely, so a
        mark set by hotkey was invisible to GoToMark.
        """
        text = str(slot).strip()
        if text.startswith('Quickmark'):
            text = text[len('Quickmark'):]
        try:
            return max(0, int(text))
        except ValueError:
            return 0

    def _block(self, slot):
        """Sequence block for a slot, growing the sequence to reach it."""
        index = self._slotIndex(slot)
        seq = self.ownerComp.seq.Mark
        if index >= seq.numBlocks:
            seq.numBlocks = index + 1
        return seq[index]

    def _defaultName(self, network_path):
        """A readable label for a freshly stored mark: the shortest trailing
        piece of its path that no OTHER stored mark's network also ends with,
        so three nested base1 networks come out as base1, base1/base1 and
        base7/base1/base1 instead of the same word three times."""
        if not network_path:
            return ''
        parts = [x for x in network_path.strip('/').split('/') if x]
        if not parts:
            return '/'
        others = []
        for mark in self.Marks():
            net = (mark.get('network') or '').strip('/')
            if net and net != network_path.strip('/'):
                others.append(net.split('/'))
        for k in range(1, len(parts) + 1):
            suffix = parts[-k:]
            if not any(o[-k:] == suffix for o in others):
                return '/'.join(suffix)
        return '/'.join(parts)

    ### store / retrieve ###

    def StoreQuickmark(self, key):
        # Get current pane details and store it
        current_pane = ui.panes.current
        # Workaround to get precise position and zoom of the network
        quickmark_value = {
            'current_network': current_pane.owner.path,
            'current_child': current_pane.owner.currentChild.path if current_pane.owner.currentChild else None,
            'x': current_pane.x,
            'y': current_pane.y,
            'zoom': current_pane.zoom
        }
        block = self._block(key)
        block.par.Data = json.dumps(quickmark_value)
        # only auto-name an unnamed slot -- never overwrite the user's label
        if not str(block.par.Name.eval()).strip():
            block.par.Name = self._defaultName(quickmark_value['current_network'])
        self.custom_print(f"QuickMarks {self._label(key)} is set to: {quickmark_value['current_network']}")

    def UnstoreQuickmark(self, key):
        # Unstores the quickmark specified by the key
        block = self._block(key)
        label = self._label(key)
        block.par.Data = ''
        block.par.Name = ''
        self.custom_print(f"QuickMarks {label} unstored")

    def RetrieveQuickmark(self, key):
        # Get the quickmark from the sequence block
        quickmark = self.GetQuickmark(key)
        if quickmark and 'current_network' in quickmark:
            target = op(quickmark['current_network'])
            if target is None or not target.isCOMP:
                self.custom_print(f"QuickMarks {self._label(key)}: stored network {quickmark['current_network']} no longer exists")
                return quickmark
            ui.panes.current.owner = target
            if 'current_child' in quickmark:
                child_op = op(quickmark['current_child'])
                if child_op:
                    child_op.current = True
                    child_op.selected = True

            ui.panes.current.x = quickmark.get('x', 0)
            ui.panes.current.y = quickmark.get('y', 0)
            ui.panes.current.zoom = quickmark.get('zoom', 1)

            self.custom_print(f"QuickMarks Jump to {self._label(key)}")
        return quickmark

    def GetQuickmark(self, key):
        """The stored dict for a slot, or None. Never navigates."""
        raw = str(self._block(key).par.Data.eval()).strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except ValueError:
            fnsLog(f'QuickMarks: slot {self._slotIndex(key)} holds unreadable data',
                   level='WARNING')
            return None

    def GetName(self, key):
        """The user's label for a slot, empty when unset."""
        return str(self._block(key).par.Name.eval()).strip()

    def SetName(self, key, name):
        """Rename a slot. Does not touch where it points."""
        self._block(key).par.Name = str(name)
        self.custom_print(f"QuickMarks slot {self._slotIndex(key)} named '{name}'")

    def _label(self, key):
        """'3' or '3 (my label)' -- for status messages."""
        index = self._slotIndex(key)
        name = self.GetName(key)
        return f'{index} ({name})' if name else str(index)

    def Marks(self):
        """Every populated slot as {index, name, network}."""
        out = []
        seq = self.ownerComp.seq.Mark
        for i in range(seq.numBlocks):
            data = self.GetQuickmark(i)
            if data:
                out.append({'index': i, 'name': self.GetName(i),
                            'network': data.get('current_network')})
        return out

    ### migration ###

    def _migrateFromStorage(self):
        """Copy legacy StorageManager slots into the sequence, once.

        Guarded by the Migrated par so it cannot run twice, and it never
        overwrites a block that already holds data. The old storage is left
        untouched afterwards as a backup.
        """
        try:
            if self.ownerComp.par.Migrated.eval():
                return
        except AttributeError:
            return          # sequence/par set not present yet
        moved = 0
        for i in range(self.SLOTS):
            old = self.stored.get(f'Quickmark{i}', None)
            if not old or 'current_network' not in old:
                continue
            block = self._block(i)
            if str(block.par.Data.eval()).strip():
                continue    # never clobber a mark already on the sequence
            block.par.Data = json.dumps(old)
            if not str(block.par.Name.eval()).strip():
                block.par.Name = self._defaultName(old.get('current_network'))
            moved += 1
        self.ownerComp.par.Migrated = True
        fnsLog(f'QuickMarks: migrated {moved} mark(s) from storage to the Mark sequence')

    ### hotkeys ###

    def HandleShortcut(self, shortcutName):
        # Extract the key number from the shortcutName
        key_number = shortcutName.split('.')[-1]
        if shortcutName == 'ctrl.alt.shift.0':
            parent().par.Active = not parent().par.Active
            self.custom_print(f"QuickMarks Active is now set to: {parent().par.Active}")

        elif shortcutName.startswith('ctrl.') and 'alt.' not in shortcutName and 'shift.' not in shortcutName:
            if parent().par.Active:
                # Once. The doubled call this carried was never explained; measured
                # on 2025.33070, a pane keeps x/y/zoom set in the same call as its
                # owner switch (unchanged two frames later), so one call is right.
                self.RetrieveQuickmark(key_number)

        # For storing the quickmark with 'ctrl.' but not 'ctrl.alt.' or 'ctrl.0'
        elif shortcutName.startswith('ctrl.alt.') and 'shift.' not in shortcutName and key_number in [str(i) for i in range(1, 10)]:
            self.StoreQuickmark(key_number)

        # For unstoring the quickmark with 'ctrl.alt.'
        elif 'ctrl.' in shortcutName and 'alt.shift.' in shortcutName and key_number in [str(i) for i in range(1, 10)]:
            self.UnstoreQuickmark(key_number)

    ### FNS_CommandRegistry (quick-launch commands) ###

    @FNSCommand.fns_command(label='Go to quickmark')
    def GoToMark(self, slot: int):
        """Jump to the quickmark stored in the given slot."""
        self.RetrieveQuickmark(slot)
        return {'ok': True, 'slot': self._slotIndex(slot), 'name': self.GetName(slot)}

    @FNSCommand.fns_command(label='Store quickmark', context='network')
    def StoreMark(self, slot: int):
        """Store the current network location in the given slot."""
        self.StoreQuickmark(slot)
        return {'ok': True, 'slot': self._slotIndex(slot), 'name': self.GetName(slot)}

    @FNSCommand.fns_command(label='Clear quickmark')
    def ClearMark(self, slot: int):
        """Clear the quickmark stored in the given slot."""
        self.UnstoreQuickmark(slot)
        return {'ok': True, 'slot': self._slotIndex(slot)}

    @FNSCommand.fns_command(label='Name quickmark')
    def NameMark(self, slot: int, name: str = ''):
        """Set the label shown for a quickmark slot."""
        self.SetName(slot, name)
        return {'ok': True, 'slot': self._slotIndex(slot), 'name': self.GetName(slot)}

    @FNSCommand.fns_command(label='List quickmarks')
    def ListMarks(self):
        """List every populated quickmark slot with its name and network."""
        return {'ok': True, 'marks': self.Marks()}

    @FNSCommand.fns_command(label='Toggle QuickMarks', state='Active')
    def ToggleActive(self):
        """Enable or disable QuickMarks."""
        self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
        return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
