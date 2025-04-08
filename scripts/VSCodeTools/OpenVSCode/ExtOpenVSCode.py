import subprocess
import os
import json
from pathlib import Path

class ExtOpenVSCode:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.logger = self.ownerComp.op('logger1')
		run(
			"args[0].postInit() if args[0] "
					"and hasattr(args[0], 'postInit') else None",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)


	@property
	def is_autodetect(self):
		return self.ownerComp.par.Autodetect.eval()
	
	@property
	def is_startup(self):
		return self.ownerComp.par.Startup.eval()

	@property
	def codeexe(self):
		return self.ownerComp.par.Codeexe.eval()
	
	@codeexe.setter
	def codeexe(self, value):
		self.ownerComp.par.Codeexe = value
	
	@property
	def workspace(self):
		return self.ownerComp.par.Workspace.eval()
	
	@property
	def projectname(self):
		return project.name.split('.')[0]
	
	@workspace.setter
	def workspace(self, value):
		self.ownerComp.par.Workspace = value
		

	def postInit(self):
		if self.is_autodetect:
			self.set_codeexe()
			self.set_workspace()

		if self.is_startup:
			self.OpenVSCode()


	def OnAutodetect(self, val):
		if val:
			self.postInit()

	def OnOpen(self):
		if self.is_autodetect:
			self.set_codeexe()
			self.set_workspace()
		self.OpenVSCode()

	def set_codeexe(self):
		code_exe_path = self.codeexe  # Get the current value of Codeexe

		# Step 1 & 2: Check if Codeexe is Set and Verify Existence
		if code_exe_path and Path(code_exe_path).exists():
			self.logger.Log(f"VS Code executable found at: {code_exe_path}")
		else:
			# Step 3: Fallback to Preferences
			fallback_path = ui.preferences['dats.texteditor']
			if fallback_path and Path(fallback_path).exists():
				self.logger.Log(f"Falling back to preference's text editor at: {fallback_path}")
				# Detect MacOS
				if fallback_path.endswith(".app"):
					if 'Cursor.app' in fallback_path:
						fallback_path = f"{fallback_path}/Contents/MacOS/Cursor"
					else:
						fallback_path = f"{fallback_path}/Contents/MacOS/Electron"
				self.codeexe = fallback_path  # Update Codeexe to the fallback path
			else:
				# Step 4: Error Handling
				self.logger.Log("Error: No valid VS Code executable found. Please set the path manually.")


	def set_workspace(self):
		project_folder = Path(project.folder)  # Convert project_folder to a Path object for easier manipulation

		# Step 2: Find or Create Workspace File
		workspace_files = list(project_folder.glob('*.code-workspace'))
		if workspace_files:
			workspace_file = workspace_files[0]
		else:
			workspace_file = project_folder / f"{self.projectname}.code-workspace"

		# Step 3: Convert to Relative Path
		# Ensure the workspace_file path is relative to project_folder
		relative_workspace_file = workspace_file.relative_to(project_folder)

		# Step 4: Handle Path Conversion
		# Update the workspace property to use the relative path
		self.workspace = str(relative_workspace_file)
		self.logger.Log(f"Using workspace file: {relative_workspace_file}")


	def OpenVSCode(self):
		# check if both exist
		missing_exe = not self.codeexe or not Path(self.codeexe).exists()

		# Ensure workspace file exists, create if necessary
		project_folder = Path(project.folder)
		workspace_path = project_folder / self.workspace
		
		# Get the interpreter path
		interpreter_path = self._get_interpreter_path()
		# Check if we're using a valid TD interpreter or falling back to local typings
		interpreter_parent = interpreter_path.parent
		version = self._parse_td_version(interpreter_parent.parent)
		is_valid_td = self._is_valid_td_version(version)

		# Load existing workspace config or create new one
		if workspace_path.exists():
			with workspace_path.open('r') as file:
				workspace_config = json.load(file)
		else:
			workspace_config = {"folders": [{"path": "."}]}
		
		if is_valid_td:
			# Initialize settings if it doesn't exist
			if "settings" not in workspace_config:
				workspace_config["settings"] = {}
		
			# Update Python settings to force workspace interpreter
			python_settings = {
				"python.defaultInterpreterPath": str(interpreter_path),
				"python.terminal.activateEnvironment": True
			}
		
			# Update workspace settings
			workspace_config["settings"].update(python_settings)
		
		# Save the workspace config
		with workspace_path.open('w') as file:
			json.dump(workspace_config, file, indent=4)
		
		if not workspace_path.exists():
			self.logger.Log(f"Created workspace file: {workspace_path}")
		else:
			self.logger.Log(f"Updated interpreter path in workspace file: {workspace_path}")
		
		
		# Only deploy stubs if we're not using a valid TD interpreter
		if not is_valid_td:
			if TDTypings := getattr(op, 'FNS_TDTYPINGS', None):
				self.logger.Log("Deploying stubs because no valid TD interpreter found")
				TDTypings.DeployStubs()
			
		missing_workspace = not self.workspace or not Path(self.workspace).exists()

		if missing_exe or missing_workspace:
			self._popErrorMessage(missing_exe, missing_workspace)
			return
		
		subprocess.Popen([self.codeexe, self.workspace])
		pass

	def _popErrorMessage(self, missing_exe=False, missing_workspace=False):
		missing_components = []
		if missing_exe:
			missing_components.append("VS Code executable")
		if missing_workspace:
			missing_components.append("workspace file")

		if missing_components:
			base_error_msg = "Error: No valid {} found. Please set the path manually and make sure it exists."
			formatted_components = " and ".join(missing_components)
			message = base_error_msg.format(formatted_components)

			if not self.is_autodetect:
				message += '\nOr try turning on Auto-detect!'
			
			ui.messageBox("Error", message, buttons=["OK"])
			self.ownerComp.openParameters()
		pass

	def _parse_td_version(self, path: Path) -> tuple[int, int] | None:
		"""Extract TouchDesigner version from path."""
		td_pattern = re.compile(r'TouchDesigner\.(\d+)\.(\d+)')
		# Check folder name for version
		match = td_pattern.match(path.name)
		if match:
			return (int(match.group(1)), int(match.group(2)))
		return None

	def _is_valid_td_version(self, version: tuple[int, int] | None) -> bool:
		"""Check if version meets minimum requirements (>= 2023.30000)."""
		if version is None:
			return False
		major, minor = version
		if major > 2023:
			return True
		elif major == 2023:
			return minor >= 30000
		return False

	def _find_td_interpreter(self) -> Path | None:
		"""Search for valid python.exe in the highest version TD installation."""
		# First check current app version
		current_td = Path(app.installFolder)
		version = self._parse_td_version(current_td)
		self.logger.Log(f"Current TD version: {version}")
		
		if app.osName != 'Windows': # this will be the norm for windows too in the future
			return Path(app.pythonExecutable)
		
		# Always check if current interpreter exists
		td_interpreter = current_td / 'bin' / 'python.exe'
		if td_interpreter.exists():
			if self._is_valid_td_version(version):
				self.logger.Log(f"Using current TD interpreter in {version[0]}.{version[1]}")
				return td_interpreter
			else:
				self.logger.Log("Current TD version is not valid, but interpreter exists")
				# Store current interpreter as fallback
				current_interpreter = td_interpreter
		else:
			current_interpreter = None
			self.logger.Log("Current TD interpreter not found")
		
		# If current version is not valid, search for highest version
		td_installations = current_td.parent
		highest_match = None
		highest_version = (0, 0)

		for td_folder in td_installations.iterdir():
			if not td_folder.is_dir():
				continue

			version = self._parse_td_version(td_folder)
			if self._is_valid_td_version(version) and version > highest_version:
				td_interpreter = td_folder / 'bin' / 'python.exe'
				if td_interpreter.exists():
					highest_version = version
					highest_match = td_interpreter
					self.logger.Log(f"Found interpreter in TD {version[0]}.{version[1]}")

		# Return highest valid version if found, otherwise return current interpreter
		return highest_match if highest_match else current_interpreter

	def _get_interpreter_path(self) -> Path:
		"""Determine paths for builtins and stubs files."""
		# Try to find builtins in highest version TD installation
		td_interpreter = self._find_td_interpreter()
		if td_interpreter:
			interpreter_file = td_interpreter
		else:
			self.logger.Log("No valid TD installation (>= 2023.30000) found with python.exe")
			# Fallback to local typings
			interpreter_file = Path("typings", "python.exe")

		return interpreter_file
