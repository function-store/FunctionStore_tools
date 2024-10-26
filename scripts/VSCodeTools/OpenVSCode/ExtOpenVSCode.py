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
		if not workspace_path.exists():
			with workspace_path.open('w') as file:
				json.dump({"folders": [{"path": "."}]}, file)
			self.logger.Log(f"Created workspace file: {workspace_path}")
			if TDTypings := getattr(op, FNS_TDTYPINGS, None):
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
