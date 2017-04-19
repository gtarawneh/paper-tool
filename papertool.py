#!/usr/bin/env python

import os
import sys
import traceback
import math
import json
import console
from docopt import docopt
from library import Library

usage = """Papertool

Usage:
  papertool [--lib=<lib>]
  papertool text [--lib=<lib>]
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

def writeJSON(file, d):
	# writes dictionary d to file
	with open(file, 'w') as f:
		json.dump(d, f, sort_keys = True, indent = 4, ensure_ascii=True)

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
	lib = Library(libDir)
	if args["update"]:
		import urllib2
		from paperbot import updateLibrary
		try:
			updateLibrary(libDir, args["--yes"])
		except urllib2.HTTPError as e:
			print "http error, library update aborted"
			print "code: %d" % e.code
			print "reason: %s" % e.reason
	else:
		libExists, errMsg = lib.checkLibrary()
		if libExists:
			mode = "text" if args["text"] else "titles"
			startConsole(lib, mode)
		else:
			print errMsg

def startConsole(lib, mode = "text"):
	infoList = lib.getMeta()
	indexList = lib.getIndex() if mode == "text" else range(len(infoList))
	content = lib.getSentences() if mode == "text" else lib.getPaperTitles()
	searcher = console.Searcher(content, indexList, infoList)
	try:
		con1 = console.Console(searcher, lib.libDir)
		con1.loopConsole()
	except Exception as err:
		con1.deinit()
		traceback.print_exc(file=sys.stdout)
		return
	else:
		con1.deinit()

main()
