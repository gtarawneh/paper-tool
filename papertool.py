#!/bin/python

import os
import sys
import traceback
import math
import json

import console
import walker

senFile = 'sentences.txt'
infoFile = 'paper-crossref.json'
indexFile = 'index.json'
optionsfile = '.papertool'

def loadJSON(file):
	try:
		with open(file) as f:
			return json.load(f)
	except ValueError as e:
		print(e)
		raise Exception('Error encountered while parsing .papertool')

def loadLibrary(libDir):
	with open(getAbsolutePath(libDir, senFile)) as f:
		content = f.read().splitlines()
	infoList = loadJSON(getAbsolutePath(libDir, infoFile))
	indexList = loadJSON(getAbsolutePath(libDir, indexFile))
	return (content, indexList, infoList)

def getAbsolutePath(libDir, file):
	# scriptPath = os.path.dirname(os.path.realpath(sys.argv[0]))
	return os.path.join(libDir, file)

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

def loadOptions():
	homeDir = os.getenv("HOME")
	fullOptionsFile = getAbsolutePath(homeDir, optionsfile)
	if os.path.isfile(fullOptionsFile):
		return loadJSON(fullOptionsFile)
	else:
		return {}

def printUsage():
	print("Usage: papertool.py <library>\n")

def main():
	options = loadOptions()
	args = sys.argv[1:]
	nargs = len(args)
	if nargs>0:
		if args[0] in ['-b', '--build']:
			if nargs>2:
				textDir = args[1]
				libDir = args[2]
				walker.buildLibrary(textDir, libDir)
				return
	else:
		libDir = args[0] if nargs==1 else options.get("library", "").encode("ascii")
		if libDir:
			startConsole(libDir)
			return
	# otherwise, unable to process command line arguments so:
	printUsage()

def startConsole(libDir):
	content, indexList, infoList =  loadLibrary(libDir)
	searcher = console.Searcher(content, indexList, infoList)
	getSuggestionFunc = getSuggestions
	try:
		con1 = console.Console(searcher)
		con1.loopConsole()
	except Exception as err:
		con1.deinit()
		traceback.print_exc(file=sys.stdout)
		return
	con1.deinit()

main()
