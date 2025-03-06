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
#
class ExtBorderlessWindow:#
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.current_pid = os.getpid()  # Store current process ID
		self.saved_foreground_window = GetForegroundWindow()
		self.is_borderless = False  # Track borderless state
		self.IsModifiedAndBorderless = tdu.Dependency(False)
		self.ui_mod_bg_top = self.ownerComp.op('constant1')
		self.modify_ui(self.evalModifyui)

	def modify_ui(self, state):
		target_op = op('/ui/dialogs/mainmenu/emptypanel')
		if not target_op:
			return
		if state:
			target_op.par.top = self.ui_mod_bg_top
		else:
			target_op.par.top = None

	def onParModifyui(self, val):
		self.modify_ui(val)

	@property
	def TdProjectIsModified(self):
		return self.td_project_is_modified(self.saved_foreground_window)

	def UpdateModified(self):
		if self.IsBorderless:
			if self.td_project_is_modified(self.saved_foreground_window):
				self.ui_mod_bg_top.par.alpha = 0.15
				return
			
		self.ui_mod_bg_top.par.alpha = 0.0

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

	def onParMakeborderless(self):
		self.MakeBorderless()

	def onParRestoreborders(self):
		self.UndoBorderless()

	def MakeBorderless(self):
		if self.IsBorderless:
			self.restore_borders()
		else:
			self.remove_borders()

	def UndoBorderless(self):
		self.restore_borders()

	@property
	def IsBorderless(self):
		return self.is_borderless
	
	@IsBorderless.setter
	def IsBorderless(self, value):
		self.is_borderless = value
		self.displayProjName(value)

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
