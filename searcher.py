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

	def getSuggestion(self, ind):
		sug = self.content[ind]
		info = self.infoList[self.indexList[ind]]
		infoStr = self._getInfoStr(info)
		return (sug, infoStr)

	def _getInfoStr(self, info):
		if info and 'message' in info:
			item0 = info['message']['items'][0]
			title = ''.join(item0['title'])
			if 'published-print' in item0:
				year = item0['published-print']['date-parts'][0][0]
			elif 'deposited' in item0:
				year = item0['deposited']['date-parts'][0][0]
			elif 'issued' in item0:
				year = item0['issued']['date-parts'][0][0]
			else:
				raise Exception(title)
			return '(%s, %d)' % (title, year)
		elif info:
			return '(%s)' % info['_file'].split('/')[-1].encode('utf-8')
		else:
			return ''

	def isFinished(self):
		return self.searchIndex == len(self.content)