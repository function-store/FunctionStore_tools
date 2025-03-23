import ctypes
import time
import os

# Windows API Constants
GWL_STYLE = -16
WS_BORDER = 0x00800000
WS_CAPTION = 0x00C00000  # Title bar
WS_THICKFRAME = 0x00040000  # Resizable border
WS_POPUP = 0x80000000  # Borderless
SW_MAXIMIZE = 3
SW_RESTORE = 9
MONITOR_DEFAULTTONEAREST = 2

# SetWindowPos Flags
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040

# Windows API Functions
GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
GetWindowLong = ctypes.windll.user32.GetWindowLongW
SetWindowLong = ctypes.windll.user32.SetWindowLongW
SetWindowPos = ctypes.windll.user32.SetWindowPos
ShowWindow = ctypes.windll.user32.ShowWindow
MonitorFromWindow = ctypes.windll.user32.MonitorFromWindow
GetMonitorInfo = ctypes.windll.user32.GetMonitorInfoW
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
GetWindowTextW = ctypes.windll.user32.GetWindowTextW

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class MONITORINFO(ctypes.Structure):
	_fields_ = [
		("cbSize", ctypes.c_ulong),
		("rcMonitor", ctypes.c_long * 4),  # Full monitor size
		("rcWork", ctypes.c_long * 4),  # Work area (excluding taskbar)
		("dwFlags", ctypes.c_ulong)
	]
###
class ExtBorderlessWindow:#
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.current_pid = os.getpid()  # Store current process ID
		self.saved_foreground_window = GetForegroundWindow()
		self.is_borderless = self.ownerComp.par.Borderless.eval() # Track borderless state
		self.is_modified = False  # Track modified state
		self.IsModifiedAndBorderless = tdu.Dependency(False)
		self.saveStateScriptOp = self.ownerComp.op('saveStateScriptOp')
		self.__injectUI()

	def __injectUI(self):
		nodetable = op('/ui/dialogs/mainmenu/menu')
		target_op = nodetable.op('in1')
		inject_op = self.saveStateScriptOp

		if _op := nodetable.op(inject_op.name):
			out_conns = _op.inputConnectors[0].connections
			_op.destroy()
		else:
			out_conns = target_op.inputConnectors[0].connections

		_op = nodetable.copy(inject_op)
		_op.nodeX = target_op.nodeX + 150
		_op.nodeY = target_op.nodeY
		_op.docked[0].nodeX = _op.nodeX
		_op.docked[0].nodeY = _op.nodeY - 100

		for out_conn in out_conns:
			_op.inputConnectors[0].connect(out_conn.owner)

		_op.outputConnectors[0].connect(target_op)
		_op.bypass = False
		pass


	@property
	def TdProjectIsModified(self):
		return self.td_project_is_modified(self.saved_foreground_window)

	def UpdateModified(self, force=None):
		if force is None:
			is_modified = self.td_project_is_modified(self.saved_foreground_window)
		else:
			is_modified = force

		# Only update if the modified state has changed
		if is_modified != self.is_modified:
			self.is_modified = is_modified
			# Update the dependency
			self.IsModifiedAndBorderless.val = self.is_modified and self.is_borderless
			

	def onParBorderless(self, _par, _val):#
		if _val:
			self.remove_borders()
		else:
			self.restore_borders()
		
		# Update the dependency whenever borderless state changes
		self.IsModifiedAndBorderless.val = self.is_modified and self.is_borderless

	def get_window_title(self, hwnd):
		# Get the length of the title
		length = GetWindowTextLengthW(hwnd) + 1
		title = ctypes.create_unicode_buffer(length)
		GetWindowTextW(hwnd, title, length)
		return title.value

	def is_main_td_window(self, hwnd):
		# First check if it's our process
		process_id = ctypes.c_ulong()
		GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
		if process_id.value != self.current_pid:
			return False
			
		# Then check the window title
		title = self.get_window_title(hwnd)
		# Main window usually has a title ending with "TouchDesigner", ".toe", or "TouchDesigner *", ".toe *"
		return title and (
			title.endswith('.toe') or 
			title.endswith('.toe*')
		)
	
	def td_project_is_modified(self, hwnd):
		title = self.get_window_title(hwnd)
		if title:
			return title.endswith('*')
		return False # if we couldn't get the title, assume it's not modified

	def MakeBorderless(self):
		self.ownerComp.par.Borderless.val = not self.evalBorderless

	def UndoBorderless(self):
		self.ownerComp.par.Borderless.val = False

	@property
	def IsBorderless(self):
		return self.is_borderless
	
	@IsBorderless.setter
	def IsBorderless(self, value):
		self.is_borderless = value
		self.displayProjName(value)
		# Update the dependency whenever borderless state changes
		self.IsModifiedAndBorderless.val = self.is_modified and self.is_borderless

	def get_work_area(self, hwnd):
		monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
		monitor_info = MONITORINFO()
		monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
		GetMonitorInfo(monitor, ctypes.byref(monitor_info))

		# Extract the work area (excluding taskbar)
		left, top, right, bottom = monitor_info.rcWork
		width = right - left
		height = bottom - top
		return left, top, width, height

	def maximize_window(self, hwnd):
		ShowWindow(hwnd, SW_MAXIMIZE)

	def remove_borders(self):
		hwnd = GetForegroundWindow()  # Get active window
		# Check if it's main TouchDesigner window
		if not self.is_main_td_window(hwnd):
			return
		
		# Get work area before modifying window
		left, top, width, height = self.get_work_area(hwnd)
		
		# First set window to full work area size
		SetWindowPos(hwnd, None, left, top, width, height, 
					SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		
		# Then remove borders
		current_style = GetWindowLong(hwnd, GWL_STYLE)
		SetWindowLong(hwnd, GWL_STYLE, (current_style & ~WS_CAPTION & ~WS_THICKFRAME))  # Remove border & title bar
		
		# Make window smaller than screen
		scale = 1  # 50% of screen size
		width_reduction = int(width * (1 - scale))
		height_reduction = int(height * (1 - scale))
		
		left += width_reduction // 2
		top += height_reduction // 2
		width -= width_reduction
		height -= height_reduction
		
		self.IsBorderless = True

		# Move & resize window to final size with proper flags
		SetWindowPos(hwnd, None, left, top, width, height, 
					SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		
		self.saved_foreground_window = hwnd

	def restore_borders(self):
		hwnd = GetForegroundWindow()  # Get active window
		
		# Check if it's main TouchDesigner window
		if not self.is_main_td_window(hwnd):
			return
			
		current_style = GetWindowLong(hwnd, GWL_STYLE)
		SetWindowLong(hwnd, GWL_STYLE, (current_style | WS_CAPTION | WS_THICKFRAME))  # Restore border & title bar
		
		# Get work area
		left, top, width, height = self.get_work_area(hwnd)
		
		# Apply changes with proper flags and restore to full size
		SetWindowPos(hwnd, None, left, top, width, height, 
					SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		self.maximize_window(hwnd)  
		self.IsBorderless = False

	def displayProjName(self, state):
		targets = [self.ownerComp.op('projname'), op('/ui/dialogs/mainmenu/projname')]

		for target in targets:
			if not target:
				continue
		
			target.par.display = state

