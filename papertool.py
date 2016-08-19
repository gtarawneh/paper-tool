#!/bin/python

import sys
import traceback
import math

from console import *

filename = 'sentences.txt'

def getContent():
	with open(filename) as f:
		content = f.read().splitlines()
		return content

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
	content =  getContent()
	pinfo = [('Spatiotemporal energy models for the perception of motion', \
		'Adelson and Bergen', '1985')]
	cinds = [0 for _ in content]
	getSuggestionFunc = getSuggestions
	try:
		con1 = Console()
		con1.init()
		con1.loopConsole(content, cinds, pinfo)
	except Exception as err:
		con1.deinit()
		traceback.print_exc(file=sys.stdout)
		return
	con1.deinit()

main()
