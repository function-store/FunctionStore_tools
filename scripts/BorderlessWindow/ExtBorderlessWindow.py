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

# Window states
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3

# SetWindowPos Flags
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040

# Custom RECT structure
class RECT(ctypes.Structure):
	_fields_ = [
		("left", ctypes.c_long),
		("top", ctypes.c_long),
		("right", ctypes.c_long),
		("bottom", ctypes.c_long)
	]

# WINDOWPLACEMENT structure
class WINDOWPLACEMENT(ctypes.Structure):
	_fields_ = [
		("length", ctypes.c_uint),
		("flags", ctypes.c_uint),
		("showCmd", ctypes.c_uint),
		("ptMinPosition", ctypes.c_long * 2),
		("ptMaxPosition", ctypes.c_long * 2),
		("rcNormalPosition", RECT)
	]

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
GetWindowRect = ctypes.windll.user32.GetWindowRect
GetClientRect = ctypes.windll.user32.GetClientRect
GetWindowPlacement = ctypes.windll.user32.GetWindowPlacement

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
		self.default_width_offset = 9
		self.default_height_offset = -9
		self.applied_offsets = False
		

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

	def onStart(self):
		"""Called on component initialization"""
		# Check if we should go fullscreen on start
		if self.evalFixfullscreenonstart or self.evalFullscreen:
			# Get foreground window
			hwnd = GetForegroundWindow()
			if self.is_main_td_window(hwnd):
				# Get work area
				work_left, work_top, work_width, work_height = self.get_work_area(hwnd)
				
				# Make window fullscreen
				SetWindowPos(hwnd, None, work_left, work_top, work_width, work_height, 
							SWP_FRAMECHANGED | SWP_SHOWWINDOW)
				
				# Maximize the window
				self.maximize_window(hwnd)
		# Check if we should also remove borders on start
		if self.evalOnstart:
			# Remove borders
			self.remove_borders()
			self.ownerComp.par.Borderless = True

		if self.evalHidemenubuttons:
			self.onParHidemenubuttons(self.evalHidemenubuttons)
			pass
		
		if self.evalShowprojectname:
			self.displayProjName(self.evalShowprojectname)

	def onParHidemenubuttons(self, _val):
		self.hideMenuButtons(_val)

	def hideMenuButtons(self, _val):
		mainMenu = op('/ui/dialogs/mainmenu')
		op_names_to_hide = ('wiki', 'forum', 'tutorials')
		for op_name in op_names_to_hide:
			_op = mainMenu.op(op_name)
			if _op:
				_op.par.display = not _val
		pass

	def onStartBorderless(self):
		self.onStart()


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
		if self.evalShowprojectname:
			self.displayProjName(value)
		# Update the dependency whenever borderless state changes
		self.IsModifiedAndBorderless.val = self.is_modified and self.is_borderless

	def onParShowprojectname(self, _par, _val):
		if self.is_borderless:
			self.displayProjName(_val)

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

	def is_window_maximized(self, hwnd):
		"""Check if the window is maximized"""
		placement = WINDOWPLACEMENT()
		placement.length = ctypes.sizeof(placement)
		if not GetWindowPlacement(hwnd, ctypes.byref(placement)):
			return False
		return placement.showCmd == SW_SHOWMAXIMIZED

	def remove_borders(self):
		hwnd = GetForegroundWindow()  # Get active window
		# Check if it's main TouchDesigner window
		if not self.is_main_td_window(hwnd):
			return
		
		# Check if window is maximized
		is_maximized = self.is_window_maximized(hwnd)
		
		# Get current window dimensions
		window_rect = RECT()
		GetWindowRect(hwnd, ctypes.byref(window_rect))
		current_left = window_rect.left
		current_top = window_rect.top
		current_width = window_rect.right - window_rect.left
		current_height = window_rect.bottom - window_rect.top
		
		# Get work area for scaling if needed
		work_left, work_top, work_width, work_height = self.get_work_area(hwnd)
		
		# Get window style
		current_style = GetWindowLong(hwnd, GWL_STYLE)

		force_fullscreen = self.ownerComp.par.Fullscreen.eval()

		# Force fullscreen mode if window is maximized
		use_fullscreen = is_maximized or force_fullscreen

		# Check fullscreen parameter
		if use_fullscreen:
			# First set window to full work area size
			SetWindowPos(hwnd, None, work_left, work_top, work_width, work_height, 
						SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		
		# Remove borders
		SetWindowLong(hwnd, GWL_STYLE, (current_style & ~WS_CAPTION & ~WS_THICKFRAME))  # Remove border & title bar
		
		self.IsBorderless = True
		
		# Apply changes and set size
		if use_fullscreen:
			# Scale down if needed
			scale = 1  # 50% of screen size
			width_reduction = int(work_width * (1 - scale))
			height_reduction = int(work_height * (1 - scale))
			
			left = work_left + width_reduction // 2
			top = work_top + height_reduction // 2
			width = work_width - width_reduction
			height = work_height - height_reduction
			
			SetWindowPos(hwnd, None, left, top, width, height, 
						SWP_FRAMECHANGED | SWP_SHOWWINDOW)
		else:
			# Apply user-defined offsets
			width_offset = self.default_width_offset
			height_offset = self.default_height_offset
			
			# Apply offsets to window size
			SetWindowPos(hwnd, None, current_left + width_offset, current_top, 
						current_width - width_offset*2, current_height + height_offset,
						SWP_FRAMECHANGED | SWP_SHOWWINDOW)
			self.applied_offsets = True
						
		self.saved_foreground_window = hwnd

	def restore_borders(self):
		hwnd = GetForegroundWindow()  # Get active window
		
		# Check if it's main TouchDesigner window
		if not self.is_main_td_window(hwnd):
			return
			
		# Get current window rect before restoring borders
		window_rect = RECT()
		GetWindowRect(hwnd, ctypes.byref(window_rect))
		
		# Get window style
		current_style = GetWindowLong(hwnd, GWL_STYLE)
		
		# Restore borders
		SetWindowLong(hwnd, GWL_STYLE, (current_style | WS_CAPTION | WS_THICKFRAME))  # Restore border & title bar
		
		# Get work area
		work_left, work_top, work_width, work_height = self.get_work_area(hwnd)
		
		# Set window size and position
		if not self.applied_offsets:
			# Apply changes with proper flags and restore to full size
			SetWindowPos(hwnd, None, work_left, work_top, work_width, work_height, 
						SWP_FRAMECHANGED | SWP_SHOWWINDOW)
			self.maximize_window(hwnd)
		else:
			# Apply inverse of the user-defined offsets
			width_offset = self.default_width_offset
			height_offset = self.default_height_offset
			
			# Apply inverse offsets to compensate
			new_left = window_rect.left - width_offset
			new_width = window_rect.right - window_rect.left + width_offset * 2
			new_height = window_rect.bottom - window_rect.top - height_offset
			
			# Keep current window dimensions but adjust for added borders
			SetWindowPos(hwnd, None, new_left, window_rect.top, 
						new_width, new_height,
						SWP_FRAMECHANGED | SWP_SHOWWINDOW)
			
		self.IsBorderless = False

	def displayProjName(self, state):
		if not self.is_borderless:
			return
		targets = [self.ownerComp.op('projname'), op('/ui/dialogs/mainmenu/projname')]

		for target in targets:
			if not target:
				continue
		
			target.par.display = state

