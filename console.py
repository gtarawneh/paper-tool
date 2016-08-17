
import curses
import math

class Console:

	query = 'motion vision'
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

	def displaySuggestions(self, content, keys):
		for i in self.suggestionLines:
			self.clearLine(i)
		startIndex = len(self.suggestionLines) * self.page
		for i, sugInd in enumerate(self.suggestions[startIndex:]):
			if i not in self.suggestionLines:
				break
			sug = content[sugInd][0:self.W]
			self.scr.addstr(i, 0, sug)
			for keyword in keys:
				k = sug.lower().find(keyword.lower())
				if k > -1:
					keywordCase = content[sugInd][k:k+len(keyword)]
					self.scr.addstr(i, k, keywordCase, curses.color_pair(1) + curses.A_BOLD)

	def highlightSuggestion(self, content):
		if self.suggestions:
			absSelected = len(self.suggestionLines) * self.page + self.selected
			self.clearLine(self.selected)
			line = content[self.suggestions[self.absSelected]][0:self.W]
			self.scr.addstr(self.selected, 0, line, curses.color_pair(3))

	def writeQueryLine(self):
		queryStyle = curses.color_pair(2) + curses.A_BOLD
		statusStyle = curses.color_pair(2) + curses.A_BOLD
		self.clearLine(self.queryLine)
		rightSide = "(%d / %d) [%d / %d]" % (self.absSelected + 1, len(self.suggestions), self.page + 1, self.pages)
		rightInd = self.W - 1 - len(rightSide)
		self.scr.addstr(self.queryLine, rightInd, rightSide, statusStyle)
		self.scr.addstr(self.queryLine, 0, '> ' + self.query, queryStyle)

	def loopConsole(self, content, getSuggestionFunc):
		initScreen = True
		self.absSelected = 0
		# main loop
		while True:
			if initScreen:
				# self.scr.clear()
				self.H, self.W = self.scr.getmaxyx()
				self.suggestionLines = range(0, self.H - 2)
				self.queryLine = self.H - 1
				maxSuggestions = len(self.suggestionLines)
				initScreen = False
				# work out new page and selected values of current highligh
				self.page = int(math.floor(float(self.absSelected) / len(self.suggestionLines)))
				self.selected = self.absSelected % len(self.suggestionLines)
			# update display content:
			self.scr.hline(self.H-2, 0, "-", self.W)
			self.scr.refresh()
			self.displaySuggestions(content, self.keys)
			self.pages = math.ceil(float(len(self.suggestions)) / len(self.suggestionLines))
			self.absSelected = len(self.suggestionLines) * self.page + self.selected
			self.writeQueryLine()
			self.highlightSuggestion(content)
			# grab and process input:
			c = self.scr.getch()
			if c == 10:
				return
			elif c == curses.KEY_RESIZE:
				initScreen = True
			elif c == curses.KEY_DOWN:
				if self.absSelected < len(self.suggestions)-1:
					self.absSelected += 1
					initScreen = True
			elif c == curses.KEY_UP:
				if self.absSelected > 0:
					self.absSelected -= 1
					initScreen = True
			elif c == curses.KEY_NPAGE:
				if self.page < self.pages-1:
					self.absSelected += len(self.suggestionLines)
					self.absSelected = min(self.absSelected, len(self.suggestions)-1)
					initScreen = True
			elif c == curses.KEY_END:
				prevLines = len(self.suggestionLines) * self.page
				remainingLines = len(self.suggestions) - prevLines
				self.selected = min(len(self.suggestionLines)-1, remainingLines-1)
			elif c == curses.KEY_HOME:
				self.selected = 0
			elif c == curses.KEY_PPAGE:
				if self.page > 0:
					self.absSelected -= len(self.suggestionLines)
					initScreen = True
			else:
				self.query = self.query[:-1] if (c == 127) else self.query + unichr(c)
				# run query:
				if len(self.query) > 4:
					self.keys = self.query.split(' ')
					subList = self.cache.get(self.query[:-1], range(0, len(content)))
					self.suggestions = getSuggestionFunc(content, subList, self.keys, 1000000)
					self.cache[self.query] = self.suggestions
