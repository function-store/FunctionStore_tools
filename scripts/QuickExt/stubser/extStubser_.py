'''Info Header Start
Name : extStubser
Author : Wieland@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2022.32660
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
	
	def _placeTyping(self, stubsString:str, name:str):
		"""Export the given stubs string in to a file and add it as a builtins!"""
		debug("Placing Typings", name)
		interpreterPath = app.pythonExecutable
		interpreterFolder = Path(interpreterPath).parent
		typings_dir = interpreterFolder if self.ownerComp.par.Tointerpreter.eval() else Path("typings")
		builtins_path = typings_dir / "__builtins__.pyi" if self.ownerComp.par.Tointerpreter.eval() else None
		
		if builtins_path and builtins_path.exists():
			builtinsFile = builtins_path
			stubsFile = (typings_dir / f"{name}.pyi")
		else:
			if builtins_path:
				debug("Warning: __builtins__.pyi not found in interpreter folder")
			builtinsFile = Path("typings", "__builtins__.pyi")
			stubsFile = Path("typings", name).with_suffix(".pyi")
		builtinsFile.parent.mkdir( exist_ok=True, parents=True)
		builtinsFile.touch(exist_ok=True)

		debug("Placing Typings", name)
		debug("Typings File", stubsFile)
		debug("Builtins File", builtinsFile)	

		currentBuiltinsText = builtinsFile.read_text()
		if not re.search(f"from {name} import *", currentBuiltinsText): 
			with builtinsFile.open("t+a") as builtinsFileHandler:
				builtinsFileHandler.write(f"\nfrom { name} import *")
		
		
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
	