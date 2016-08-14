#!/bin/python

import sys
import traceback
import curses

filename = 'sentences.txt'

def getContent():
	with open(filename) as f:
		content = f.read().splitlines()
		return content

def runScreen(content, scr):
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
	query = ''
	cache = {}
	suggestions = []
	keys = []
	searchedLines = 0
	nMatches = 0
	queryStyle = curses.color_pair(2) + curses.A_BOLD
	statusStyle = curses.color_pair(2) + curses.A_BOLD
	initScreen = True
	while True:
		if initScreen:
			scr.clear()
			hw = scr.getmaxyx()
			W = hw[1]
			H = hw[0]
			suggestionLines = range(0, H - 5)
			queryLine = H - 1
			statusLine1 = H - 4
			statusLine2 = H - 3
			maxSuggestions = len(suggestionLines)
			initScreen = False
			def clearLine(i): scr.addstr(i, 0, ' ' * (W))
			def clearQueryLine(): scr.addstr(queryLine, 0, ' ' * (W-1))
			def writeLine(i, str, style):
				if (i == queryLine):
					clearQueryLine()
				else:
					clearLine(i)
				scr.addstr(i, 0, str, style)
			def displaySuggestions(suggestions, keys):
				for i in suggestionLines:
					clearLine(i)
				for i, sug in enumerate(suggestions):
					if i not in suggestionLines:
						return
					sug = content[sug][0:W]
					scr.addstr(i, 0, sug)
					for keyword in keys:
						k = sug.lower().find(keyword.lower())
						if k > -1:
							scr.addstr(i, k, keyword, curses.color_pair(1) + curses.A_BOLD)
		# update display content:
		scr.refresh()
		displaySuggestions(suggestions, keys)
		writeLine(statusLine1, "searched: %d, found %d" % (searchedLines, len(suggestions)), statusStyle)
		writeLine(statusLine2, 'keyword: ' + ",".join(keys), statusStyle)
		writeLine(queryLine, '> ' + query, queryStyle)
		# grab and process input:
		c = scr.getch()
		if c == 10:
			return
		elif c == curses.KEY_RESIZE:
			initScreen = True
			continue
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