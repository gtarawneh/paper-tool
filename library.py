import os
import json

class Library:

	libDir = None
	pdfDir = None
	metaFile = None
	bibDir = None
	txtDir = None
	senDir = None
	metaDir = None
	senFile = None
	indFile = None

	def __init__(self, libDir):
		self.libDir = libDir
		self.pdfDir = Library._getAbsolutePath(libDir, "pdfs")
		self.bibDir = Library._getAbsolutePath(libDir, "bibtex")
		self.txtDir = Library._getAbsolutePath(libDir, "text")
		self.senDir = Library._getAbsolutePath(libDir, "sentences")
		self.metaDir = Library._getAbsolutePath(libDir, "meta")
		self.metaFile = Library._getAbsolutePath(self.metaDir, "meta.json")
		self.senFile = Library._getAbsolutePath(self.senDir, "sentences.txt")
		self.indFile = Library._getAbsolutePath(self.senDir, "index.json")

	@staticmethod
	def _getAbsolutePath(directory, file):
		if directory and file:
			return os.path.join(directory, file)
		else:
			return ""

	def getFullFilePath(self, fileName, fileType):
		"""
		Return full path of a library file of a given type
		"""
		subDirs = {
			"pdf" : self.pdfDir,
			"bibtex" : self.bibDir,
			"text" : self.txtDir
		}
		subDir = subDirs.get(fileType, None)
		if subDir:
			return Library._getAbsolutePath(subDir, fileName)
		else:
			raise Exception("Incorrect file type: %s" % fileType)

	def checkLibrary(self):
		"""
		Return tuple (result, msg) where `result` is a Boolean indicating
		whether library exists and msg is an optional accompanying error
		message.
		"""
		if not self.libDir:
			return (False, "invalid library directory")
		if not os.path.exists(self.libDir):
			return (False, 'directory \'%s\' does not exist' % self.libDir)
		libFiles = [self.metaFile, self.senFile, self.indFile]
		for file in libFiles:
			if not os.path.isfile(file):
				return (False, 'library file \'%s\' does not exist' % file)
		return (True, None)

	def create(self):
		# create directory structure:
		libDirs = [
			self.libDir,
			self.metaDir,
			self.pdfDir,
			self.bibDir,
			self.txtDir,
			self.senDir
		]
		map(os.makedirs, libDirs)
		# create empty files:
		emptyJSON = "[]"
		with open(self.metaFile, "w") as fid:
			fid.write(emptyJSON)
		with open(self.indFile, "w") as fid:
			fid.write(emptyJSON)
		with open(self.senFile, "w") as fid:
			pass

	def getMeta(self):
		return Library._loadJSON(self.metaFile)

	def getIndex(self):
		return Library._loadJSON(self.indFile)

	def getSentences(self):
		with open(self.senFile) as fid:
			content = fid.read().splitlines()
		return content

	def getPaperTitles(self):
		libMeta = self.getMeta()
		getTitle = lambda entry : entry.get("title", "(unidentifier paper)")
		titles = map(getTitle, libMeta)
		return titles

	@staticmethod
	def _loadJSON(file):
		try:
			with open(file) as f:
				return json.load(f)
		except ValueError as e:
			print(e)
			raise Exception('Error encountered while parsing %s' % file)
