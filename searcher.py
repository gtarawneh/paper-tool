class Searcher:

	content = []
	lcontent = []
	indexList = []
	infoList = []
	keys = []
	suggestions = []
	searchIndex = 0

	def __init__(self, content, indexList, infoList):
		self.content = content
		self.indexList = indexList
		self.infoList = infoList
		self.lcontent = [s.lower() for s in self.content]
		self.startSearch([])

	def startSearch(self, keys = []):
		self.keys = keys
		self.searchIndex = 0
		if keys:
			self.suggestions = []
			searchIndex = len(self.content)
		else:
			self.suggestions = range(0, len(self.content))

	def continueSearch(self):
		# search (if necessary)
		blockEnd = min(self.searchIndex + 10000, len(self.lcontent))
		for i in range(self.searchIndex, blockEnd):
			line = self.lcontent[i]
			matches = [line.find(k) for k in self.keys]
			if not -1 in matches:
				self.suggestions.append(i)
		self.searchIndex = blockEnd

	def isSearchComplete(self):
		return self.searcher.searchIndex == self.blockEnd
