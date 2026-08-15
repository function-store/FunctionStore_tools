

'''Info Header Start
Name : extStubser
Author : root
Saveorigin : FunctionStore_tools_2025_DEV.16.toe
Saveversion : 2025.33070
Info Header End'''
import ast
from pathlib import Path
import re
from stubsTransformer import StubsTransformer

debug = op("logger").Log

class extStubser:
	"""
	A Utility to automaticaly generate stubs for touchdesigner Extensions and modules.
	"""
	def __init__(self, ownerComp:COMP):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	def Stubify(self, input:str, includePrivate:bool = False, includeUnpromoted:bool = True) -> str:
		"""Generate a stubified String of a module, removing all unnecesarry elements of functions."""
		data = ast.parse(input)
		transformedData = StubsTransformer( includePrivate, includeUnpromoted).visit( data )
		
		return ast.unparse(transformedData)
	
	def _parse_td_version(self, path: Path) -> tuple[int, int] | None:
		"""Extract TouchDesigner version from path."""
		td_pattern = re.compile(r'TouchDesigner\.(\d+)\.(\d+)')
		# Check folder name for version
		match = td_pattern.match(path.name)
		if match:
			return (int(match.group(1)), int(match.group(2)))
		return None

	def _is_valid_td_version(self, version: tuple[int, int] | None) -> bool:
		"""Check if version meets minimum requirements (>= 2023.3000)."""
		if version is None:
			return False
		major, minor = version
		if major > 2023:
			return True
		elif major == 2023:
			return minor >= 30000
		return False

	def _find_td_builtins(self) -> Path | None:
		"""Search for valid __builtins__.pyi in the highest version TD installation."""
		# First check current app version
		current_td = Path(app.installFolder)
		version = self._parse_td_version(current_td)
		
		# Always check if current builtins exists
		td_builtins = current_td / 'bin' / '__builtins__.pyi'
		if td_builtins.exists():
			if self._is_valid_td_version(version):
				debug(f"Using current TD builtins in {version[0]}.{version[1]}")
				return td_builtins
			else:
				debug("Current TD version is not valid, but builtins exists")
				# Store current builtins as fallback
				current_builtins = td_builtins
		else:
			current_builtins = None
			debug("Current TD builtins not found")
		
		# If current version is not valid, search for highest version
		td_installations = current_td.parent
		highest_match = None
		highest_version = (0, 0)

		for td_folder in td_installations.iterdir():
			if not td_folder.is_dir():
				continue

			version = self._parse_td_version(td_folder)
			if self._is_valid_td_version(version) and version > highest_version:
				td_builtins = td_folder / 'bin' / '__builtins__.pyi'
				if td_builtins.exists():
					highest_version = version
					highest_match = td_builtins
					debug(f"Found builtins in TD {version[0]}.{version[1]}")

		# Return highest valid version if found, otherwise return current builtins
		return highest_match if highest_match else current_builtins

	def _get_typing_paths(self, name: str) -> tuple[Path, Path]:
		"""Determine paths for builtins and stubs files."""
		if self.ownerComp.par.Tointerpreter.eval():
			# Try to find builtins in highest version TD installation
			td_builtins = self._find_td_builtins()
			if td_builtins:
				builtins_file = td_builtins
			else:
				debug("No valid TD installation (>= 2023.30000) found with __builtins__.pyi")
				# Fallback to local typings
				builtins_file = Path("typings", "__builtins__.pyi")
		else:
			debug("Using local typings directory")
			builtins_file = Path("typings", "__builtins__.pyi")

		# Ensure parent directory exists
		builtins_file.parent.mkdir(exist_ok=True)
		if not builtins_file.exists():
			debug("Creating new __builtins__.pyi file")
			builtins_file.touch()

		# Create custom_typings/QuickExt directory next to __builtins__.pyi
		stubs_dir = builtins_file.parent / "custom_typings" / "QuickExt"
		stubs_dir.mkdir(parents=True, exist_ok=True)
		
		return builtins_file, stubs_dir / f"{name}.pyi"
		
	def _placeTyping(self, stubsString:str, name:str):
		"""Export the stub string and register it in the project __builtins__.pyi.

		typings/__builtins__.pyi re-exports the shipped TD interface library
		(`from tdi import *`) so built-in TD type completion is preserved, then
		adds the helper stubs under custom_typings/QuickExt. Requires TD
		2025.32820+ (which ships the `tdi` package). Paths are anchored to
		project.folder so they resolve on macOS too (where the process CWD is
		not the project folder).
		"""
		debug("Placing Typings", name)
		typingsDir = Path(project.folder) / "typings"

		builtinsFile = typingsDir / "__builtins__.pyi"
		builtinsFile.parent.mkdir(parents=True, exist_ok=True)
		builtinsText = builtinsFile.read_text() if builtinsFile.exists() else ""
		if "from tdi import *" not in builtinsText:
			builtinsText = "from tdi import *\n" + builtinsText
		importLine = f"from custom_typings.QuickExt.{name} import *"
		if importLine not in builtinsText:
			builtinsText = builtinsText.rstrip("\n") + "\n" + importLine + "\n"
		builtinsFile.write_text(builtinsText)

		stubsDir = typingsDir / "custom_typings" / "QuickExt"
		stubsDir.mkdir(parents=True, exist_ok=True)
		(stubsDir / f"{name}.pyi").write_text(stubsString)

	
	def StubifyDat(self, target:textDAT, includePrivate:bool = False, includeUnpromoted:bool = True):
		debug( "Stubifying Dat", target.name)
		self._placeTyping(
			self.Stubify(
				target.text, 
				includePrivate=includePrivate, 
				includeUnpromoted=includeUnpromoted), 
			target.name )

	def StubifyComp(self, target:COMP, depth = 1, tag = "stubser", includePrivate:bool = False, includeUnpromoted:bool = True):
		debug( "Stubifying COMP", target.name )
		for child in target.findChildren( 
				tags=[ tag ], 
				type=textDAT, 
				maxDepth = depth ):
			
			self.StubifyDat( 
				child, 
				includePrivate=includePrivate, 
				includeUnpromoted=includeUnpromoted )
			
	def _findParPage(self, name):
		pagename = name
		owner = self.ownerComp.par.Owner.eval()
		for page in owner.customPages:
			if page.name == pagename:
				return page
		return owner.appendCustomPage( pagename )

	def InitOwner(self):
		page = self._findParPage("Stubser")
		page.appendPulse( 	
			"Deploystubs",
			label 		= "Deploy Stubs",
			replace		= True )
		return
	