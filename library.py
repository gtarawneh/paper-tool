import os

class Library:

	libDir = None
	pdfDir = None
	metaFile = None
	bibDir = None
	txtDir = None
	senDir = None
	senFile = None
	indFile = None

	def __init__(self, libDir):
		self.libDir = libDir
		self.pdfDir = Library.__getAbsolutePath(libDir, "pdfs")
		self.bibDir = Library.__getAbsolutePath(libDir, "bibtex")
		self.txtDir = Library.__getAbsolutePath(libDir, "text")
		self.senDir = Library.__getAbsolutePath(libDir, "sentences")
		self.metaFile = Library.__getAbsolutePath(libDir, "meta/meta.json")
		self.senFile = Library.__getAbsolutePath(self.senDir, "sentences.txt")
		self.indFile = Library.__getAbsolutePath(self.senDir, "index.json")

	@staticmethod
	def __getAbsolutePath(directory, file):
		return os.path.join(directory, file)

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
			return Library.__getAbsolutePath(subDir, fileName)
		else:
			raise Exception("Incorrect file type: %s" % fileType)
