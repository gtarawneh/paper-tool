
import curses
import math
import time
import subprocess
import os

class Console:

	query = ''
	cache = {}
	suggestions = []
	keys = []
	searchedLines = 0
	selected = 0
	page = 0
	pages = 0
	absSelected = 0
	querLine = 0
	W = 0
	H = 0
	scr = None

	def init(self):
		self.scr = curses.initscr()
		curses.start_color()
		curses.noecho()
		curses.cbreak
		self.scr.keypad(1)
		curses.use_default_colors()
		curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
		curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
		curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
		curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_WHITE)

	def deinit(self):
		curses.nocbreak()
		self.scr.keypad(0)
		curses.echo()
		curses.endwin()

	def clearLine(self, i):
		reps = self.W-1 if (i == self.H-1) else self.W
		self.scr.addstr(i, 0, ' ' * reps)

	def writeLine(self, i, str, style):
		self.clearLine(i)
		self.scr.addstr(i, 0, str, style)

	def getOnScreenSuggestions(self):
		start = len(self.suggestionLines) * self.page
		lastPageEntryIndex = start + len(self.suggestionLines)
		end = min(lastPageEntryIndex, len(self.suggestions))
		return self.suggestions[start:end]

	def displaySuggestions(self, content, keys, indexList, infoList):
		currSuggestions = self.getOnScreenSuggestions()
		for i, sugInd in enumerate(currSuggestions):
			if i not in self.suggestionLines:
				break
			sug = content[sugInd][0:self.W]
			isHighlight = i == self.selected
			self.clearLine(i)
			lineStyle = curses.color_pair(3 if isHighlight else 0)
			self.scr.addstr(i, 0, sug, lineStyle)
			remChars = self.W - len(sug) - 1
			if remChars > 0:
				# display line info
				info = infoList[indexList[sugInd]]
				infoStr = self.getInfoStr(info)
				self.scr.addstr(i, len(sug)+1, infoStr[:remChars], curses.color_pair(4))
			if not isHighlight:
				for keyword in keys:
					k = sug.lower().find(keyword)
					if k > -1:
						keywordCase = content[sugInd][k:k+len(keyword)]
						self.scr.addstr(i, k, keywordCase, curses.color_pair(1) + curses.A_BOLD)
		for i in range(len(currSuggestions), len(self.suggestionLines)):
			self.clearLine(i)

	def displaySuggestionsModeB(self, content, keys, indexList, infoList):
		currSuggestions = self.getOnScreenSuggestions()
		for i, sugInd in enumerate(currSuggestions):
			if i not in self.suggestionLines:
				break
			sug = content[sugInd]
			isHighlight = i == self.selected
			self.clearLine(i)
			lineStyle = curses.color_pair(3 if isHighlight else 0)

			if keys:
				k = sug.lower().find(keys[0])
				centerPos = (self.W - len(keys[0])) / 2
				delta = centerPos - k
			else:
				delta = 0

			if delta>=0:
				l = min(len(sug), self.W - delta)
				self.scr.addstr(i, delta, sug[:l], lineStyle)
			else:
				l = min(len(sug) + delta, self.W)
				self.scr.addstr(i, 0, sug[-delta:-delta+l], lineStyle)

			if not isHighlight:
				for keyword in keys:
					k = sug.lower().find(keyword)
					if k > -1:
						keywordCase = content[sugInd][k:k+len(keyword)]
						# self.scr.addstr(i, k, keywordCase, curses.color_pair(1) + curses.A_BOLD)

		for i in range(len(currSuggestions), len(self.suggestionLines)):
			self.clearLine(i)

	def getInfoStr(self, info):
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

	def displayWebPage(self, info):
		if 'message' in info:
			item0 = info['message']['items'][0]
			url = item0['URL']
			self.runProcess(["chrome", url])

	def displayPDF(self, info):
		f = info['_file']
		self.runProcess(['evince', '-f', f])

	def runProcess(self, p):
		FNULL = open(os.devnull, 'w')
		subprocess.Popen(p, stderr = FNULL)

	def writeQueryLine(self):
		queryStyle = curses.color_pair(2) + curses.A_BOLD
		statusStyle = curses.color_pair(2) + curses.A_BOLD
		self.clearLine(self.queryLine)
		rightSide = "(%d/%d) [page %d/%d]" % (self.absSelected + 1, len(self.suggestions), self.page + 1, self.pages)
		rightInd = self.W - 1 - len(rightSide)
		self.scr.addstr(self.queryLine, rightInd, rightSide, statusStyle)
		self.scr.addstr(self.queryLine, 0, '> ' + self.query, queryStyle)

	def resizeWindow(self):
		self.H, self.W = self.scr.getmaxyx()
		self.suggestionLines = range(0, self.H - 2)
		self.queryLine = self.H - 1
		maxSuggestions = len(self.suggestionLines)
		# work out new page and selected values of current highligh
		self.page = int(math.floor(float(self.absSelected) / len(self.suggestionLines)))
		self.selected = self.absSelected % len(self.suggestionLines)
		self.scr.hline(self.H-2, 0, "-", self.W)

	def getKeys(self, query):
		# splits an input query into `keys` (terms)
		#
		# query is first split into `parts` separated by double-
		# quotations. Even parts as split further by spaces
		# while odd ones are added to keys as whole
		#
		# for example, for a query of: foo "bar foo" bar
		# foo is key #1
		# bar foo is key #2
		# bar is key #3
		keys = []
		parts = [p.lower() for p in query.split('"')]
		for i in xrange(0, len(parts), 2):
			keys += parts[i].split(' ')
		for i in xrange(1, len(parts), 2):
			keys.append(parts[i])
		return keys

	# content is an array of sentences
	# indexList is a corresponding array of entries in infoList
	# infoList is a list of tupes (title, authors, year)
	def loopConsole(self, content, indexList, infoList):
		self.resizeWindow()
		self.lastDispTime = time.time() - 5
		searchIndex = len(content)
		lcontent = [s.lower() for s in content]
		keys = []
		self.absSelected = 0
		self.suggestions = range(0, len(content))
		# main loop
		while True:
			# search (if necessary)
			blockEnd = min(searchIndex + 10000, len(content))
			for i in range(searchIndex, blockEnd):
				line = lcontent[i]
				matches = [line.find(k) for k in self.keys]
				if not -1 in matches:
					self.suggestions.append(i)
			searchIndex = blockEnd
			# update display content:
			currTime = time.time()
			if (currTime - self.lastDispTime > 0.25) or \
				len(self.suggestions) >= len(self.suggestionLines) or \
				searchIndex == blockEnd:
				self.displaySuggestions(content, self.keys, indexList, infoList)
				self.lastDispTime = currTime
				self.pages = math.ceil(float(len(self.suggestions)) / len(self.suggestionLines))
				self.absSelected = len(self.suggestionLines) * self.page + self.selected
			self.scr.leaveok(True)
			self.writeQueryLine()
			self.scr.leaveok(False)
			self.scr.refresh()
			# set input as blocking (only) when search completes
			self.scr.timeout(-1 if searchIndex == len(content) else 0)
			# grab input
			c = self.scr.getch()
			# process input
			if c == 10:
				return
			elif c == -1:
				continue
			elif c == curses.KEY_RESIZE:
				self.resizeWindow()
			elif c == curses.KEY_DOWN:
				if self.absSelected < len(self.suggestions)-1:
					self.absSelected += 1
					self.resizeWindow()
			elif c == curses.KEY_UP:
				if self.absSelected > 0:
					self.absSelected -= 1
					self.resizeWindow()
			elif c == curses.KEY_NPAGE:
				if self.selected < len(self.suggestionLines)-1:
					# not at end of current page
					prevLines = len(self.suggestionLines) * self.page
					remainingLines = len(self.suggestions) - prevLines
					self.selected = min(len(self.suggestionLines)-1, remainingLines-1)
				elif self.page < self.pages-1:
					# end of current page (and further page exists)
					self.absSelected += len(self.suggestionLines)
					self.absSelected = min(self.absSelected, len(self.suggestions)-1)
					self.resizeWindow()
			elif c == curses.KEY_END:
				self.absSelected = len(self.suggestions) - 1
				self.resizeWindow()
			elif c == curses.KEY_HOME:
				self.absSelected = 0
				self.resizeWindow()
			elif c == curses.KEY_PPAGE:
				if self.selected > 0:
					# not on top of current page
					self.absSelected -= self.selected
					self.resizeWindow()
				elif self.page > 0:
					# on top of current page (and previous page exists)
					self.absSelected -= len(self.suggestionLines)
					self.resizeWindow()
			elif c == 23:
				# ctrl-w
				selSug = self.suggestions[self.absSelected]
				papInd = indexList[selSug]
				self.displayWebPage(infoList[papInd])
			elif c == 16:
				# ctrl-p
				selSug = self.suggestions[self.absSelected]
				papInd = indexList[selSug]
				self.displayPDF(infoList[papInd])
			elif c == curses.KEY_DC:
				self.query = ''
				self.keys = []
				self.absSelected = 0
				self.page = 0
				self.selected = 0
				self.suggestions = []
				searchIndex = 0
			elif c in [curses.KEY_LEFT, curses.KEY_RIGHT]:
				pass
			elif c in range(256):
				self.query = self.query[:-1] if (c == 127) else self.query + unichr(c)
				self.keys = self.getKeys(self.query)
				self.suggestions = []
				self.scr.timeout(0) # non-blocking
				self.absSelected = 0
				self.page = 0
				self.selected = 0
				searchIndex = 0
			else:
				raise Exception('unsupported key: %d' % c)
