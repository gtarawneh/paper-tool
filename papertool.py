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
	with open(senFile) as f:
		content = f.read().splitlines()
	with open(infoFile) as f:
		infoList = json.load(f)
	with open(indexFile) as f:
		indexList = json.load(f)
	return (content, indexList, infoList)

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
	getSuggestionFunc = getSuggestions
	try:
		con1 = Console()
		con1.init()
		con1.loopConsole(content, indexList, infoList)
	except Exception as err:
		con1.deinit()
		traceback.print_exc(file=sys.stdout)
		return
	con1.deinit()

main()
