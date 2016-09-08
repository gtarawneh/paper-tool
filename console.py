import curses
import math
import time
import subprocess
import os
from searcher import Searcher

class Console:

	query = '' # contents of query line
	page = 0 # current page
	selected = 0 # highlighted suggestion index.
	W = 0 # screen width (chars)
	H = 0 # screen height (chars)
	scr = None # curses screen object
	searcher = None # searcher object
	prompt = '> ' # query line prompt
	digits = [] # buffer to hold digit key presses
	sentenceModeCache = None # tuple to backup sentence mode details

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
		curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
		curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_WHITE)
		curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_WHITE)

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
		style1 = curses.color_pair(1) + curses.A_BOLD
		style2 = curses.color_pair(3) + curses.A_BOLD
		style3 = curses.color_pair(4)
		style4 = curses.color_pair(5)
		backStyle = style2 if isHighlight else style1
		infoStyle = style2 if isHighlight else style3
		lineStyle = curses.color_pair(3 if isHighlight else 0)
		lineNumStyle = style2 if isHighlight else style4
		sugText, sugInfo = self.searcher.getSuggestion(sugInd)
		sugText += ' '
		h = 0 # horizontal index
		if h < self.W:
			lineNumStr = '%02d. ' % line
			self.scr.addstr(line, h, lineNumStr, lineNumStyle)
			h += len(lineNumStr)
		if h < self.W:
			remChars = self.W - h
			sugText = sugText[:remChars]
			self.scr.addstr(line, h, sugText, lineStyle)
			for keyword in keys:
				k = sugText.lower().find(keyword)
				if (k > -1) and (h+k < self.W):
					keywordCase = sugText[k:k+len(keyword)]
					remChars = self.W - (h + k)
					self.scr.addstr(line, h + k, keywordCase[:remChars], backStyle)
			h += len(sugText)
		if h < self.W:
			# display line info
			remChars = self.W - h
			infoCropped = sugInfo[:remChars]
			self.scr.addstr(line, h, infoCropped, infoStyle)
			h += len(infoCropped)
		if h < self.W:
			# clear remaining chars in line
			self.scr.addstr(line, h, ' ' * (self.W - h), backStyle)

	def displaySuggestions(self):
		currSuggestions = self.getOnScreenSuggestions()
		for i, sugInd in enumerate(currSuggestions):
			if i not in self.suggestionLines:
				break
			isHighlight = i == self.getRelSelected()
			self.displaySuggestion(sugInd, i, isHighlight, self.searcher.keys)
		# clear unused lines
		for i in range(len(currSuggestions), len(self.suggestionLines)):
			self.clearLine(i)

	def getRelSelected(self):
		# returns index of selection relative to top of current page
		return self.selected - self.page * len(self.suggestionLines)

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
		queryLine = self.H - 1
		self.scr.leaveok(True)
		queryStyle = curses.color_pair(2) + curses.A_BOLD
		statusStyle = curses.color_pair(2) + curses.A_BOLD
		self.clearLine(queryLine)
		sugCount = self.searcher.getSuggestionCount()
		pageCount = self.getPageCount()
		rightSide = "(%d/%d) [page %d/%d]" % (self.selected + 1, sugCount, self.page + 1, pageCount)
		rightInd = self.W - 1 - len(rightSide)
		self.scr.addstr(queryLine, rightInd, rightSide, statusStyle)
		self.scr.addstr(queryLine, 0, self.prompt + self.query, queryStyle)
		self.scr.leaveok(False)

	def resizeWindow(self):
		self.H, self.W = self.scr.getmaxyx()
		self.suggestionLines = range(0, self.H - 2)
		maxSuggestions = len(self.suggestionLines)
		# work out new page and selected values of current highligh
		self.page = int(math.floor(float(self.selected) / len(self.suggestionLines)))
		# self.getRelSelected() = self.selected % len(self.suggestionLines)
		self.scr.hline(self.H - 2, 0, "-", self.W)

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
		keys = filter(None, keys) # remove empty keys
		return keys

	def loopConsole(self):
		self.resizeWindow()
		self.lastDispTime = time.time()
		self.startSearch()
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
				self.selected = sugLineCount * self.page + self.getRelSelected()
			self.writeQueryLine()
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
				if self.selected < sugCount-1:
					self.selected += 1
					self.resizeWindow()
			elif c == curses.KEY_UP:
				if self.selected > 0:
					self.selected -= 1
					self.resizeWindow()
			elif c == curses.KEY_NPAGE:
				maxSelected = len(self.searcher.suggestions) - 1
				endPageSelected = (self.page + 1) * sugLineCount - 1
				newSelected = min(maxSelected, endPageSelected)
				if newSelected != self.selected:
					# not at end of current page
					self.selected = newSelected
				elif self.page < self.getPageCount()-1:
					# end of current page (and further page exists)
					self.selected = min(self.selected + sugLineCount, maxSelected)
					self.resizeWindow()
			elif c == curses.KEY_END:
				self.selected = len(self.searcher.suggestions) - 1
				self.resizeWindow()
			elif c == curses.KEY_HOME:
				self.selected = 0
				self.resizeWindow()
			elif c == curses.KEY_PPAGE:
				if self.getRelSelected() > 0:
					# not on top of current page
					self.selected -= self.getRelSelected()
					self.resizeWindow()
				elif self.page > 0:
					# on top of current page (and previous page exists)
					self.selected -= sugLineCount
					self.resizeWindow()
			elif c == 23:
				# ctrl-w
				url = self.searcher.getURL(self.selected)
				self.displayWebPage(url)
			elif c == 16:
				# ctrl-p
				file = self.searcher.getFile(self.selected)
				self.displayPDF(file)
			elif c == 21:
				# ctrl-u
				self.query = ''
				self.startSearch()
			elif c == curses.KEY_RIGHT:
				if not self.searcher.paperFilter:
					papInd = self.searcher.getPaperIndex(self.selected)
					self.searcher.paperFilter = [papInd]
					self.sentenceModeCache = (self.query, self.selected)
					self.searcher.backup('sentence')
					self.query = ''
					self.prompt = 'Paper> '
					self.startSearch()
			elif c == curses.KEY_LEFT:
				if self.searcher.paperFilter:
					self.searcher.paperFilter = []
					self.prompt = '> '
					self.query, self.selected = self.sentenceModeCache
					self.searcher.restore('sentence')
					self.resizeWindow()
			elif c == 127:
				# backspace
				isLastCharSpace = self.query and (self.query[-1] == ' ')
				self.query = self.query[:-1]
				if not isLastCharSpace:
					self.startSearch()
			elif c in range(48, 68):
				# digit
				digit = c - 48
				self.digits += [digit]
				if len(self.digits)>1:
					sel = self.digits[0] * 10 + self.digits[1]
					if sel < len(self.suggestionLines):
						newSel = self.page * len(self.suggestionLines) + sel
						if newSel < self.searcher.getSuggestionCount():
							self.selected = newSel
							self.resizeWindow()
					self.digits = []
			elif c == 27:
				# escape
				self.digits = []
			elif c == curses.KEY_DC:
				words = self.query.split(' ')
				self.query = ' '.join(words[:-1])
				self.startSearch()
			elif c in range(256):
				self.query += unichr(c)
				# search is ignored if c is space
				if not c in [32]:
					self.startSearch()
			else:
				raise Exception('unsupported key: %d' % c)

	def startSearch(self):
		newKeys = self.getKeys(self.query)
		self.searcher.startSearch(newKeys)
		self.scr.timeout(0) # make input non-blocking
		self.selected = 0
		self.page = 0

	def getPageCount(self):
		sugCount = len(self.searcher.suggestions)
		sugLineCount = len(self.suggestionLines)
		return math.ceil(float(sugCount) / sugLineCount)
