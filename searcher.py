class Searcher:

	# content is an array of sentences
	# indexList is a corresponding array of entries in infoList
	# infoList is a list of tupes (title, authors, year)

	content = [] # list of sentences
	lcontent = [] # same as content but lower-cased (for search)
	indexList = [] # paper indices of sentences
	infoList = [] # info indices of papers
	keys = [] # search keys
	suggestions = [] # suggested sentences (indices)
	searchIndex = 0 # index of search pointer
	searchInds = [] # sub-list of sentences to search
	cache = {} # dict for caching search results
	cachingEnabled = False
	paperFilter = [] # limit search to given paper indices
	backups  = {} # dict for search backups

	def __init__(self, content, indexList, infoList):
		self.content = content
		self.indexList = indexList
		self.infoList = infoList
		self.lcontent = [s.lower() for s in self.content]
		self.startSearch([])

	def startSearch(self, keys = []):
		n = len(self.content)
		if self.paperFilter:
			fullRange = [i for i in range(n) if self.indexList[i] in self.paperFilter]
		else:
			fullRange = range(n)
		if keys:
			query = " ".join(self.keys)[:-1]
			self.keys = keys
			self.suggestions = []
			cachedRange = self.cache.get(query, fullRange)
			self.searchInds = cachedRange if self.cachingEnabled else fullRange
			self.searchIndex = 0
		else:
			self.suggestions = fullRange
			self.keys = []
			searchIndex = len(fullRange)

	def backup(self, key):
		self.backups[key] = \
			(self.searchInds, self.searchIndex, self.suggestions, self.keys)

	def restore(self, key):
		(self.searchInds, self.searchIndex, self.suggestions, self.keys) = \
			self.backups[key]

	def areKeysPresent(self, line, pkeys, nkeys):
		# returns true when line contains all pkeys and none of nkeys, false otherwise
		for k in pkeys:
			if line.find(k) == -1:
				return False
		for k in nkeys:
			if line.find(k) != -1:
				return False
		return True

	def continueSearch(self):
		# search (if necessary)
		blockEnd = min(self.searchIndex + 10000, len(self.searchInds))
		pkeys = [k for k in self.keys if k[0] != '-']
		nkeys = [k[1:] for k in self.keys if k[0] == '-' and len(k)>1]
		for j in range(self.searchIndex, blockEnd):
			i = self.searchInds[j]
			line = self.lcontent[i]
			if self.areKeysPresent(line, pkeys, nkeys):
				self.suggestions.append(i)
		self.searchIndex = blockEnd
		if self.isSearchComplete():
			query = " ".join(self.keys)
			if len(query) > 0:
				self.cache[query] = self.suggestions

	def isSearchComplete(self):
		return self.searchIndex == len(self.searchInds)

	def getSuggestion(self, ind):
		sug = self.content[ind]
		info = self.infoList[self.indexList[ind]]
		infoStr = self._getInfoStr(info)
		return (sug, infoStr)

	def _getInfoStr(self, info):
		title = info.get("title")
		author1 = info.get("authors", [None])[0]
		if author1:
			surname = author1.split(",")[0]
			multiple_authors = len(info.get("authors", [])) > 1
			author_list = surname + " et al." if multiple_authors else surname
		else:
			author_list = None
		year = info.get("year")
		if author_list and year:
			return "(%s %s)" % (surname, year)
		elif author_list:
			return "(%s)" % author_list
		else:
			return "(n/a)"

	def _getInfoStr_old(self, info):
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

	def getPaperIndex(self, sugInd):
		senInd = self.suggestions[sugInd]
		return self.indexList[senInd]

	def _getSentenceInfo(self, sugInd):
		papInd = self.getPaperIndex(sugInd)
		return self.infoList[papInd]

	def getURL(self, ind):
		info = self._getSentenceInfo(ind)
		return info.get("url")

	def getFile(self, ind):
		info = self._getSentenceInfo(ind)
		return info['file']

	def getSuggestionCount(self):
		return len(self.suggestions)
