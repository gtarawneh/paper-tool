import curses
import math
import time
import subprocess
import os
from searcher import Searcher

class Console:

	query = ''
	searchedLines = 0
	selected = 0
	page = 0
	pages = 0
	absSelected = 0
	querLine = 0
	W = 0
	H = 0
	scr = None
	searcher = None

	def __init__(self, searcher):
		self.searcher = searcher
		# init curses screen
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
		end = min(lastPageEntryIndex, len(self.searcher.suggestions))
		return self.searcher.suggestions[start:end]

	def displaySuggestion(self, sugInd, line, isHighlight, keys):
		# display suggestion of index `sugInd` on line `line`
		# highlighting occurrences of `keys` and, if `isHighlight`
		# all of the line
		sugText, sugInfo = self.searcher.getSuggestion(sugInd)
		sugText = sugText[0:self.W]
		lineStyle = curses.color_pair(3 if isHighlight else 0)
		self.clearLine(line)
		self.scr.addstr(line, 0, sugText, lineStyle)
		remChars = self.W - len(sugText) - 1
		if remChars > 0:
			# display line info
			self.scr.addstr(line, len(sugText)+1, sugInfo[:remChars], curses.color_pair(4))
		if not isHighlight:
			for keyword in keys:
				k = sugText.lower().find(keyword)
				if k > -1:
					keywordCase = sugText[k:k+len(keyword)]
					self.scr.addstr(line, k, keywordCase, curses.color_pair(1) + curses.A_BOLD)

	def displaySuggestions(self):
		currSuggestions = self.getOnScreenSuggestions()
		for i, sugInd in enumerate(currSuggestions):
			if i not in self.suggestionLines:
				break
			isHighlight = i == self.selected
			self.displaySuggestion(sugInd, i, isHighlight, self.searcher.keys)
		# clear unused lines
		for i in range(len(currSuggestions), len(self.suggestionLines)):
			self.clearLine(i)

	def displayWebPage(self, url):
		# open up doi link in browser
		if url != None:
			self.runProcess(['chrome', url])

	def displayPDF(self, file):
		self.runProcess(['evince', '-f', file])

	def runProcess(self, p):
		FNULL = open(os.devnull, 'w')
		subprocess.Popen(p, stderr = FNULL)

	def writeQueryLine(self):
		queryStyle = curses.color_pair(2) + curses.A_BOLD
		statusStyle = curses.color_pair(2) + curses.A_BOLD
		self.clearLine(self.queryLine)
		rightSide = "(%d/%d) [page %d/%d]" % (self.absSelected + 1, len(self.searcher.suggestions), self.page + 1, self.pages)
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

	def loopConsole(self):
		self.resizeWindow()
		self.lastDispTime = time.time() - 5
		self.absSelected = 0
		self.searcher.startSearch()
		# main loop
		while True:
			# search (if necessary)
			self.searcher.continueSearch()
			sugCount = self.searcher.getSuggestionCount()
			sugLineCount = len(self.suggestionLines)
			currTime = time.time()
			elapsed = currTime - self.lastDispTime
			if (elapsed > 0.25) or (sugCount >= sugLineCount) or self.searcher.isSearchComplete():
				self.displaySuggestions()
				self.lastDispTime = currTime
				self.pages = math.ceil(float(sugCount) / sugLineCount)
				self.absSelected = sugLineCount * self.page + self.selected
			self.scr.leaveok(True)
			self.writeQueryLine()
			self.scr.leaveok(False)
			self.scr.refresh()
			# set input as blocking (only) when search completes
			self.scr.timeout(-1 if self.searcher.isSearchComplete() else 0)
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
				if self.absSelected < sugCount-1:
					self.absSelected += 1
					self.resizeWindow()
			elif c == curses.KEY_UP:
				if self.absSelected > 0:
					self.absSelected -= 1
					self.resizeWindow()
			elif c == curses.KEY_NPAGE:
				if self.selected < sugLineCount-1:
					# not at end of current page
					prevLines = sugLineCount * self.page
					remainingLines = len(self.searcher.suggestions) - prevLines
					self.selected = min(sugLineCount-1, remainingLines-1)
				elif self.page < self.pages-1:
					# end of current page (and further page exists)
					self.absSelected += sugLineCount
					self.absSelected = min(self.absSelected, len(self.searcher.suggestions)-1)
					self.resizeWindow()
			elif c == curses.KEY_END:
				self.absSelected = len(self.searcher.suggestions) - 1
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
					self.absSelected -= sugLineCount
					self.resizeWindow()
			elif c == 23:
				# ctrl-w
				url = self.searcher.getURL(self.absSelected)
				self.displayWebPage(url)
			elif c == 16:
				# ctrl-p
				file = self.searcher.getFile(self.absSelected)
				self.displayPDF(file)
			elif c == curses.KEY_DC:
				self.query = ''
				self.absSelected = 0
				self.page = 0
				self.selected = 0
				self.searcher.startSearch()
			elif c in [curses.KEY_LEFT, curses.KEY_RIGHT]:
				pass
			elif c in range(256):
				self.query = self.query[:-1] if (c == 127) else self.query + unichr(c)
				self.searcher.startSearch(self.getKeys(self.query))
				self.scr.timeout(0) # non-blocking
				self.absSelected = 0
				self.page = 0
				self.selected = 0
			else:
				raise Exception('unsupported key: %d' % c)
