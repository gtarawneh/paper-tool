#!/bin/python

import os
import sys
import traceback
import math
import json
import console
from paperbot import updateLibrary, writeJSON
from docopt import docopt

usage = """Papertool

Usage:
  papertool [--lib=<lib>]
  papertool titles [--lib=<lib>]
  papertool update [--yes] [--lib=<lib>]
  papertool create <lib> <libdir>

Options:
  --lib=<lib>    Specify library to use
  -y --yes       Automatic yes to prompts

"""

senFile = 'sentences/sentences.txt'
infoFile = 'meta/meta.json'
indexFile = 'sentences/index.json'
optionsfile = '.papertool'

def loadJSON(file):
	try:
		with open(file) as f:
			return json.load(f)
	except ValueError as e:
		print(e)
		raise Exception('Error encountered while parsing %s' % file)

def loadLibraryContent(libDir):
	with open(getAbsolutePath(libDir, senFile)) as f:
		content = f.read().splitlines()
	infoList = loadJSON(getAbsolutePath(libDir, infoFile))
	indexList = loadJSON(getAbsolutePath(libDir, indexFile))
	return (content, indexList, infoList)

def loadLibraryTitles(libDir):
	infoList = loadJSON(getAbsolutePath(libDir, infoFile))
	indexList = loadJSON(getAbsolutePath(libDir, indexFile))
	content = [entry["title"] for entry in infoList]
	indexList = range(len(infoList))
	return (content, indexList, infoList)

def getAbsolutePath(libDir, file):
	return os.path.join(libDir, file)

def getSuggestions(content, subList, keys, maxCount):
	results = []
	searchedLines = 0
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

def createLib(libName, parentDir):
	libDir = getAbsolutePath(parentDir, libName)
	metaDir = getAbsolutePath(libDir, "meta")
	textDir = getAbsolutePath(libDir, "text")
	senDir = getAbsolutePath(libDir, "sentences")
	pdfDir = getAbsolutePath(libDir, "pdfs")
	bibDir = getAbsolutePath(libDir, "bibtex")
	# create sub-directories
	for subdir in [metaDir, textDir, senDir, pdfDir, bibDir]:
		try:
			os.makedirs(subdir)
		except:
			pass
	# create empty files
	metaFile = getAbsolutePath(metaDir, "meta.json")
	indexFile = getAbsolutePath(senDir, "index.json")
	senFile = getAbsolutePath(senDir, "sentences.txt")
	writeJSON(metaFile, [])
	writeJSON(indexFile, [])
	with open(senFile, "w") as f:
		pass

def main():
	options = loadOptions()
	args = docopt(usage, version="Papertool 0.1")
	if args["create"]:
		createLib(args["<lib>"], args["<libdir>"])
		print "Library <%s> created successfully" % args["<lib>"]
		return
	libName = args["--lib"] if args["--lib"] else options["default"]
	libDir = options.get(libName)
	if args["update"]:
		updateLibrary(libDir, args["--yes"])
	elif libDir and checkLibrary(libDir):
		mode = "titles" if args["titles"] else "content"
		startConsole(libDir, mode)
	else:
		print "Cannot find library %s" % libName

def checkLibrary(libDir):
	# returns true when libDir and necessary files exist, False otherwise
	if not os.path.exists(libDir):
		print('directory \'%s\' does not exist' % libDir)
		return False
	libFiles = [
		os.path.join(libDir, senFile),
		os.path.join(libDir, infoFile),
		os.path.join(libDir, indexFile),
	]
	for f in libFiles:
		if not os.path.isfile(f):
			print('library file \'%s\' does not exist' % f)
			return False
	return True

def startConsole(libDir, mode = "content"):
	if mode == "content":
		content, indexList, infoList =  loadLibraryContent(libDir)
	else:
		content, indexList, infoList =  loadLibraryTitles(libDir)
	searcher = console.Searcher(content, indexList, infoList)
	getSuggestionFunc = getSuggestions
	try:
		con1 = console.Console(searcher, libDir)
		con1.loopConsole()
	except Exception as err:
		con1.deinit()
		traceback.print_exc(file=sys.stdout)
		return
	con1.deinit()

main()
