
'''Info Header Start
Name : QuickmarkStorageExt
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.69.toe
Saveversion : 2025.33070
Info Header End'''
### Code and idea from Alex Guevara
### Modified by Function Store

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
    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        # Stored items for quickmarks
        storedItems = [{'name': f'Quickmark{i}', 'default': None} for i in range(10)]
        self.stored = StorageManager(self, ownerComp, storedItems)
        fnsLog('QuickMarks: init')

    def custom_print(self, message):
        # Prints a message to the status bar and the console
        current_time = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"{current_time} {message}"

        ui.status = formatted_message
        fnsLog(f'QuickMarks: {message}')

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
        self.stored[key] = quickmark_value
        self.custom_print(f"QuickMarks {key} is set to: {quickmark_value}")
    
    def UnstoreQuickmark(self, key):
        # Unstores the quickmark specified by the key
        self.stored[key] = None
        self.custom_print(f"QuickMarks {key} unstored")
    
    def RetrieveQuickmark(self, key):
        # Get the quickmark from the stored dictionary
        quickmark = self.stored.get(key, None)
        if quickmark and 'current_network' in quickmark:
            target = op(quickmark['current_network'])
            if target is None or not target.isCOMP:
                self.custom_print(f"QuickMarks {key}: stored network {quickmark['current_network']} no longer exists")
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

            self.custom_print(f"QuickMarks Jump to {key}")
        return quickmark

    def HandleShortcut(self, shortcutName):
        # Extract the key number from the shortcutName
        key_number = shortcutName.split('.')[-1]
        if shortcutName == 'ctrl.alt.shift.0':
            parent().par.Active = not parent().par.Active
            self.custom_print(f"QuickMarks Active is now set to: {parent().par.Active}")

        elif shortcutName.startswith('ctrl.') and 'alt.' not in shortcutName and 'shift.' not in shortcutName:
            if parent().par.Active:
                quickmark_key = f"Quickmark{key_number}"
                self.RetrieveQuickmark(quickmark_key)
                self.RetrieveQuickmark(quickmark_key) # need to call twice to get the correct position
        
        # For storing the quickmark with 'ctrl.' but not 'ctrl.alt.' or 'ctrl.0'
        elif shortcutName.startswith('ctrl.alt.') and 'shift.' not in shortcutName and key_number in [str(i) for i in range(1, 10)]:
            quickmark_key = f"Quickmark{key_number}"
            self.StoreQuickmark(quickmark_key)
        
        # For unstoring the quickmark with 'ctrl.alt.'
        elif 'ctrl.' in shortcutName and 'alt.shift.' in shortcutName and key_number in [str(i) for i in range(1, 10)]:
            quickmark_key = f"Quickmark{key_number}"
            self.UnstoreQuickmark(quickmark_key)

    ### FNS_CommandRegistry (quick-launch commands) ###

    @FNSCommand.fns_command(label='Go to quickmark')
    def GoToMark(self, slot: int):
        """Jump to the quickmark stored in the given slot."""
        self.RetrieveQuickmark(int(slot))
        return {'ok': True, 'slot': int(slot)}

    @FNSCommand.fns_command(label='Store quickmark')
    def StoreMark(self, slot: int):
        """Store the current network location in the given slot."""
        self.StoreQuickmark(int(slot))
        return {'ok': True, 'slot': int(slot)}

    @FNSCommand.fns_command(label='Clear quickmark')
    def ClearMark(self, slot: int):
        """Clear the quickmark stored in the given slot."""
        self.UnstoreQuickmark(int(slot))
        return {'ok': True, 'slot': int(slot)}

    def onInitTD(self):
        run('args[0]._announceCommands()', self, delayFrames=60)

    def _announceCommands(self):
        FNSCommand.announce(self.ownerComp)

    def onDestroyTD(self):
        try:
            reg = getattr(op, 'FNS_COMMANDREGISTRY', None)
            if reg is not None and hasattr(reg, 'Unregister'):
                reg.Unregister(self.ownerComp.path)
        except Exception:
            pass

    @FNSCommand.fns_command(label='Toggle QuickMarks')
    def ToggleActive(self):
        """Enable or disable QuickMarks."""
        self.ownerComp.par.Active = not self.ownerComp.par.Active.eval()
        return {'ok': True, 'active': bool(self.ownerComp.par.Active.eval())}
