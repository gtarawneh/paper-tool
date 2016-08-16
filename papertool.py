#!/bin/python

import sys
import traceback
import curses
import math

filename = 'sentences.txt'

def getContent():
	with open(filename) as f:
		content = f.read().splitlines()
		return content

def runScreen(content, scr):
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
	query = 'motion vision'
	cache = {}
	suggestions = []
	keys = []
	searchedLines = 0
	selected = 0
	page = 0
	pages = 0
	absSelected = 0
	queryStyle = curses.color_pair(2) + curses.A_BOLD
	statusStyle = curses.color_pair(2) + curses.A_BOLD
	initScreen = True
	# inline functions
	def clearLine(i): scr.addstr(i, 0, ' ' * (W))
	def clearQueryLine(): scr.addstr(queryLine, 0, ' ' * (W-1))
	def writeLine(i, str, style):
		if (i == queryLine):
			clearQueryLine()
		else:
			clearLine(i)
		scr.addstr(i, 0, str, style)
	def displaySuggestions():
		for i in suggestionLines:
			clearLine(i)
		startIndex = len(suggestionLines) * page
		for i, sug in enumerate(suggestions[startIndex:]):
			if i not in suggestionLines:
				break
			sug = content[sug][0:W]
			scr.addstr(i, 0, sug)
			for keyword in keys:
				k = sug.lower().find(keyword.lower())
				if k > -1:
					scr.addstr(i, k, keyword, curses.color_pair(1) + curses.A_BOLD)
	def highlightSuggestion():
		if suggestions:
			absSelected = len(suggestionLines) * page + selected
			clearLine(selected)
			line = content[suggestions[absSelected]][0:W]
			scr.addstr(selected, 0, line, curses.color_pair(3))
	# main loop
	while True:
		if initScreen:
			scr.clear()
			H, W = scr.getmaxyx()
			suggestionLines = range(0, H - 5)
			queryLine = H - 1
			statusLine1 = H - 4
			statusLine2 = H - 3
			maxSuggestions = len(suggestionLines)
			initScreen = False
			# work out new page and selected values of current highligh
			page = int(math.floor(float(absSelected) / len(suggestionLines)))
			selected = absSelected % len(suggestionLines)
		# update display content:
		scr.refresh()
		displaySuggestions()
		pages = math.ceil(float(len(suggestions)) / len(suggestionLines))
		absSelected = len(suggestionLines) * page + selected
		writeLine(statusLine1, "(%d / %d) [%d / %d]" % (absSelected + 1, len(suggestions), page + 1, pages), statusStyle)
		writeLine(statusLine2, 'keyword: ' + ",".join(keys), statusStyle)
		writeLine(queryLine, '> ' + query, queryStyle)
		highlightSuggestion()
		# grab and process input:
		c = scr.getch()
		if c == 10:
			return
		elif c == curses.KEY_RESIZE:
			initScreen = True
		elif c == curses.KEY_DOWN:
			if absSelected < len(suggestions)-1:
				if selected == suggestionLines[-1]:
					page += 1
					selected = 0
					initScreen = True
				else:
					selected += 1
					highlightSuggestion()
		elif c == curses.KEY_UP:
			if selected == 0:
				if page > 0:
					page -= 1
					selected = len(suggestionLines) - 1
					initScreen = True
			else:
				selected -= 1
				highlightSuggestion()
		elif c == curses.KEY_NPAGE:
			if page < pages-1:
				page += 1
				initScreen = True
				newAbsSelected = len(suggestionLines) * page + selected
				if newAbsSelected >= len(suggestions)-1:
					selected = len(suggestions) % len(suggestionLines) - 1
		elif c == curses.KEY_END:
			prevLines = len(suggestionLines) * page
			remainingLines = len(suggestions) - prevLines
			selected = min(len(suggestionLines)-1, remainingLines-1)
		elif c == curses.KEY_HOME:
			selected = 0
		elif c == curses.KEY_PPAGE:
			if page > 0:
				page -= 1
				initScreen = True
		else:
			query = query[:-1] if (c == 127) else query + unichr(c)
			# run query:
			if len(query) > 4:
				keys = query.split(' ')
				subList = cache.get(query[:-1], range(0, len(content)))
				suggestions, searchedLines = getSuggestions(content, subList, keys, 1000000)
				cache[query] = suggestions

def getSuggestions(content, subList, keys, maxCount):
	results = []
	searchedLines = 0
	# for line in content:
	for i in subList:
		line = content[i]
		searchedLines += 1
		matches = [line.lower().find(k.lower()) for k in keys]
		if not -1 in matches:
			results.append(i)
			if len(results) >= maxCount:
				return (results, searchedLines)
	return (results, searchedLines)

def printSuggestions(content, key):
	results = getSuggestions(content, key, 1000)
	for s in results:
		print(s)

def main2():
	content =  getContent()
	scr = curses.initscr()
	curses.start_color()
	curses.noecho()
	curses.cbreak
	scr.keypad(1)
	try:
		runScreen(content, scr)
	except Exception as err:
		curses.nocbreak()
		scr.keypad(0)
		curses.echo()
		curses.endwin()
		traceback.print_exc(file=sys.stdout)
		return
	curses.nocbreak()
	scr.keypad(0)
	curses.echo()
	curses.endwin()

main2()