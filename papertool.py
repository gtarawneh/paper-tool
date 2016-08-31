#!/bin/python

import sys
import traceback
import math
import json

from console import *

senFile = 'sentences.txt'
infoFile = 'paper-crossref.json'
indexFile = 'index.json'

def getContent():
	with open(getAbsolutePath(senFile)) as f:
		content = f.read().splitlines()
	with open(getAbsolutePath(infoFile)) as f:
		infoList = json.load(f)
	with open(getAbsolutePath(indexFile)) as f:
		indexList = json.load(f)
	return (content, indexList, infoList)

def getAbsolutePath(file):
	scriptPath = os.path.dirname(os.path.realpath(sys.argv[0]))
	return os.path.join(scriptPath, file)

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
	return results

def main():
	content, indexList, infoList =  getContent()
	searcher = Searcher(content, indexList, infoList)
	getSuggestionFunc = getSuggestions
	try:
		con1 = Console(searcher)
		con1.loopConsole()
	except Exception as err:
		con1.deinit()
		traceback.print_exc(file=sys.stdout)
		return
	con1.deinit()

main()
