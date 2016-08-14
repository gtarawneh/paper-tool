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
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE);
	query = '';

	hw = scr.getmaxyx();
	W = hw[1] - 5;
	H = hw[0];

	maxSuggestions = H - 10;

	cache = {}

	oldQuery = "";

	queryLine = H - 2;

	while True:

		scr.addstr(queryLine, 0, ' ' * W);
		scr.addstr(queryLine, 0, '> ' + query, curses.color_pair(1) + curses.A_BOLD)

		c = scr.getch()

		if (c == 10):
			return
		elif (c == curses.KEY_RESIZE):
			scr.clear()
			hw = scr.getmaxyx();
			W = hw[1] - 5;
			H = hw[0];
		else:
			query = query[:-1] if (c == 127) else query + unichr(c)

		for i in range(0, H - 5):
			scr.addstr(i, 0, ' ' * W)

		if (query == oldQuery) | (len(query) < 4):
			continue

		oldQuery = query

		keys = query.split(' ')

		scr.addstr(H - 3, 0, ' ' * W);
		scr.addstr(H - 3, 0, "keywords: " + ",".join(keys), curses.color_pair(1) + curses.A_BOLD)

		fullList = range(0, len(content))

		subList = cache.get(query[:-1], fullList)

		result = getSuggestions(content, subList, keys, 1000000);

		suggestions = result[0]

		searchedLines = result[1]

		cache[query] = suggestions;

		nMatches = len(suggestions)

		suggestions = suggestions[:maxSuggestions];

		n = len(suggestions);

		scr.addstr(H - 5, 0, ' ' * W);
		scr.addstr(H - 5, 0, "searched: %d, found %d" % (searchedLines, nMatches), curses.color_pair(1) + curses.A_BOLD)

		n = n if (n < maxSuggestions) else maxSuggestions

		for i in range(0, n):
			sug = content[suggestions[i]][0:W];
			scr.addstr(i, 0, sug)
			for keyword in keys:
				k = sug.lower().find(keyword.lower())
				if k > -1:
					scr.addstr(i, k, keyword, curses.color_pair(1) + curses.A_BOLD)


	scr.refresh()

def getSuggestions(content, subList, keys, maxCount):
	results = []
	searchedLines = 0
	# for line in content:
	for i in subList:
		line = content[i]
		searchedLines += 1
		# if searchedLines > 5000:
		# 	return (results, searchedLines)
		matches = [line.lower().find(k.lower()) for k in keys]
		if not -1 in matches:
			results.append(i)
			if len(results) >= maxCount:
				return (results, searchedLines)
	return (results, searchedLines)

def printSuggestions(content, key):
	results = getSuggestions(content, key, 1000);
	for s in results:
		print(s)

def main2():

	content =  getContent();
	# printSuggestions(content, "reichardt".split(' '))
	# return

	scr = curses.initscr()
	curses.start_color()
	curses.noecho()
	curses.cbreak
	scr.keypad(1)

	try:
		runScreen(content, scr);
	except Exception as err:
		curses.nocbreak();
		scr.keypad(0);
		curses.echo()
		curses.endwin()
		traceback.print_exc(file=sys.stdout)
		return

	curses.nocbreak();
	scr.keypad(0);
	curses.echo()
	curses.endwin()

main2()