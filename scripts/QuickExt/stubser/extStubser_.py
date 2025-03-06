'''Info Header Start
Name : extStubser
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2023.334.toe
Saveversion : 2023.11600
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
		return version is not None and version >= (2023, 3000)

	def _find_td_builtins(self) -> Path | None:
		"""Search for valid __builtins__.pyi in the highest version TD installation."""
		# Start from current TD installation folder
		current_td = Path(app.binFolder).parent
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

		return highest_match

	def _get_typing_paths(self, name: str) -> tuple[Path, Path]:
		"""Determine paths for builtins and stubs files."""
		if self.ownerComp.par.Tointerpreter.eval():
			# Try to find builtins in highest version TD installation
			td_builtins = self._find_td_builtins()
			if td_builtins:
				builtins_file = td_builtins
			else:
				debug("No valid TD installation (>= 2023.3000) found with __builtins__.pyi")
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

	def _placeTyping(self, stubsString: str, name: str):
		# TODO: factor out custom_typings.QuickExt. as optional subfolders to stubify to
		"""Export the given stubs string into a file and add it as a builtin."""
		debug("Placing Typings", name)
		
		builtinsFile, stubsFile = self._get_typing_paths(name)
		
		debug("Placing Typings", name)
		debug("Typings File", stubsFile)
		debug("Builtins File", builtinsFile)	

		currentBuiltinsText = builtinsFile.read_text()
		if not re.search(f"from custom_typings.QuickExt.{name} import *", currentBuiltinsText): 
			with builtinsFile.open("t+a") as builtinsFileHandler:
				builtinsFileHandler.write(f"\nfrom custom_typings.QuickExt.{name} import *")
		
		
		stubsFile.touch( exist_ok=True)
		stubsFile.write_text( stubsString )

	
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
	