

'''Info Header Start
Name : githubRemote
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''

import re, requests

def fnsLog(*args, level='INFO'):
	"""Log via the central FNSTools logger (op.FNS 'logger'); silent no-op when
	the logger is absent (standalone installs) or its Active par is off."""
	try:
		_logger = op.FNS.op('logger')
		if _logger and _logger.par.Active.eval():
			_logger.Log(*args, level=level)
	except Exception:
		pass

class githubRemote:
	"""
	githubRemote description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		# response-check failures are warnings on the central logger
		self.log = lambda *a: fnsLog('githubRemote:', *a, level='WARNING')
	
	def checkResponse(self, response:requests.Request ):
		if not response.ok: 
			self.log("Could not resolve reques to OLIB.", response.url , response.status_code, response.reason)
			raise Exception( "Error Response. Check Logs!")
		responseData = response.json()
		if not responseData:
			self.log("Olib returned empty response!", response.url, responseData )
			raise Exception( "Empty Response. Check Logs!")
		return responseData

	def getRepoData(self):
		return [ str(value) for value in re.search(r"github\.com\/([\w,-]+)\/([\w,-]+).*", self.ownerComp.par.Repository.eval()).groups() ]
	
	@property
	def fileRegex(self):
		return self.ownerComp.par.Fileregex.eval()
	
	def searchFile(self, releaseDict:dict):
		for assetElement in releaseDict["assets"]:
			if re.match( self.fileRegex, assetElement["name"]): 
				return assetElement["browser_download_url"]
		raise Exception(f"Could not find file with regex {self.fileRegex}")

	def getAndRaise(self, url):
		response = requests.get( url )
		response.raise_for_status()
		return response
	
	def fetchLatest(self):
		owner, repoName = self.getRepoData()[0:2]
		apiEndpoint = f" https://api.github.com/repos/{owner}/{repoName}/releases/latest"
		response = self.getAndRaise( apiEndpoint )
		return self.searchFile( self.checkResponse( response ) )
	
	@property
	def tagRegex(self):
		return self.ownerComp.par.Tagregex.eval()
	
	def fetchByTag(self):
		owner, repoName = self.getRepoData()[0:2]
		apiEndpoint = f" https://api.github.com/repos/{owner}/{repoName}/releases?per_page={self.ownerComp.par.Searchdepth.eval()}"
		response = self.getAndRaise( apiEndpoint )
		for releaseDict in self.checkResponse( response ):
			if re.match( self.tagRegex , releaseDict["name"]): 
				return self.searchFile( releaseDict )
		raise Exception(f"Could not find tag with regex {self.tagRegex}")

	def ExternalData(self):
		if self.ownerComp.par.Mode.eval() == "Latest": return self.fetchLatest()
		if self.ownerComp.par.Mode.eval() == "Search Tag": return self.fetchByTag()
		raise Exception( "Invalid Mode selected", self.ownerComp.par.Mode.eval() )
	
	def PollLatestTag(self):		
		op('webclient1').par.request.pulse()

	
	def OnCheckResponse(self, location):
		def extract_github_tag(url):
			# Define the regex pattern to capture the GitHub tag
			# This pattern looks for '/releases/tag/' followed by any characters (the tag), which we capture
			pattern = r'/releases/tag/([^ ]+)$'

			# Search the URL for the pattern and capture the tag
			match = re.search(pattern, url)

			# If a match is found, return the captured group, which is the tag
			if match:
				return match.group(1)
			else:
				# If no match is found, return None or an appropriate message
				return None
		tag = extract_github_tag(location)
		parent.Updater.OnPolledLatestTag(tag)


