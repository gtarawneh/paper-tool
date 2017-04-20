#!/usr/bin/env python

import sys
import os
import hashlib
import json
import datetime
import subprocess
import urllib2
import pybtex.database
import codecs
from termcolor import colored
from termcolor import cprint
from library import Library

def getSHA256(file):
	hasher = hashlib.sha256()
	with open(file, 'rb') as afile:
		buf = afile.read()
		hasher.update(buf)
	return hasher.hexdigest()

def writeJSON(file, d):
	# writes dictionary d to file
	with open(file, 'w') as f:
		json.dump(d, f, sort_keys = True, indent = 4, ensure_ascii=True)

def readJSON(file):
	# reads dictionary from file
	# returns [] if file does not exist
	if os.path.isfile(file):
		with open(file, 'r') as f:
			dic = json.loads(f.read())
		return dic
	else:
		return []

def getFileHash(libDir):
	dic = {}
	for root, dirs, files in os.walk(libDir):
		for file in files:
			fullFile = os.path.abspath(os.path.join(root, file))
			relFile = os.path.relpath(fullFile, libDir)
			dic[relFile] = getSHA256(fullFile)
	return dic

def updateLibrary(libDir, autoYes = False):
	lib = Library(libDir)
	args = sys.argv[1:]
	if "-l" in args:
		_getLibPaperTitle(metaFile)
		return
	getFileList = lambda bibDir: [f for f in os.listdir(bibDir) if
		os.path.isfile(os.path.join(bibDir, f))]
	bibFiles, textFiles = map(getFileList, [lib.bibDir, lib.txtDir])
	fileHash = getFileHash(lib.pdfDir)
	dic = readJSON(lib.metaFile)
	hmap = {entry["sha256"]:entry for entry in dic} # sha256 -> dic entry
	changes = False
	# Prepare some lambdas
	getBibFile = lambda entry : entry.get("sha256") + ".bib"
	getTextFile = lambda entry : entry.get("sha256") + ".txt"
	hasDOI = lambda entry : "DOI" in entry and entry["DOI"]
	hasBib = lambda entry : getBibFile(entry) in bibFiles
	hasText = lambda entry : getTextFile(entry) in textFiles
	# first, loop through files in the lib directory
	fileList = []
	stampDateTime = str(datetime.datetime.now())
	for relFile, fileHash in fileHash.iteritems():
		fullFile = os.path.join(lib.pdfDir, relFile)
		fileList.append(relFile)
		existingEntry = hmap.get(fileHash, None)
		if existingEntry:
			if relFile != existingEntry["file"]:
				print("file moved: %s -> %s" % (existingEntry["file"], relFile))
				existingEntry["file"] = relFile
				existingEntry["added"] = stampDateTime
				changes = True
		else:
			print("found new file %s" % relFile)
			dic.append({
				"file": relFile,
				"sha256": fileHash,
				"added": stampDateTime
			});
			changes = True
	# check for deleted files
	delFiles = [entry for entry in dic if entry["file"] not in fileList]
	for entry in delFiles:
		print("file deleted: %s" % entry["file"])
		dic.remove(entry)
		changes = True
	# check for missing DOIs/titles
	entriesMissingDOI = [entry for entry in dic if not "DOI" in entry or not "title" in entry]
	if entriesMissingDOI:
		n = len(entriesMissingDOI)
		prompt = "There are %d new paper entries, search for title and DOI [Y/n]? " % n
		selection = _promptInput(prompt, autoYes=autoYes)
		if selection.lower() in ["y", ""]:
			for entry in entriesMissingDOI:
				fullFile = lib.getFullFilePath(entry["file"], "pdf")
				papInfo = getFileDOI(fullFile)
				if papInfo:
					entry["DOI"] = papInfo["DOI"]
					entry["title"] = papInfo["title"]
					entry["added"] = stampDateTime
					writeJSON(lib.metaFile, dic)
					changes = True
			print("")
	# check for missing bibtex files
	entriesMissingBib = [entry for entry in dic if hasDOI(entry) and not hasBib(entry)]
	if entriesMissingBib:
		n = len(entriesMissingBib)
		prompt = "There are %d missing bibtex entries, attempt to fetch [Y/n]? " % n
		selection = _promptInput(prompt, autoYes=autoYes)
		if selection.lower() in ["y", ""]:
			changes = True
			for entry in entriesMissingBib:
				sys.stdout.write("Fetching bibtex record for %s ... " % entry["DOI"])
				bibStr = _getBibtex(entry["DOI"])
				if bibStr:
					bibFile = entry["sha256"] + ".bib"
					bibFileFull = lib.getFullFilePath(bibFile, "bibtex")
					with codecs.open(bibFileFull, "w", "utf8") as f:
						f.write(bibStr)
					bibInfo = _parseBibtex(bibStr)
					entry.update(bibInfo)
					writeJSON(lib.metaFile, dic)
					print("done")
				else:
					print("FAILED")
	# check for missing text files
	rebuildSentences = False
	entriesMissingText = [entry for entry in dic if not hasText(entry)]
	if entriesMissingText:
		n = len(entriesMissingText)
		prompt = "There are %d new paper pdfs, extract text [Y/n]? " % n
		selection = _promptInput(prompt, autoYes=autoYes)
		if selection.lower() in ["y", ""]:
			changes = True
			for entry in entriesMissingText:
				pFileFull = lib.getFullFilePath(entry["file"], "pdf")
				tFileFull = lib.getFullFilePath(getTextFile(entry), "text")
				print "Extracting text from %s ... " % entry["file"]
				convertPDF(pFileFull, tFileFull)
			rebuildSentences = True
	# rebuild sentences
	if rebuildSentences:
		print "Updating sentence files ..."
		indices = []
		with open(lib.senFile, "w") as f1:
			for index, entry in enumerate(dic):
				tFile = getTextFile(entry)
				tFileFull = lib.getFullFilePath(tFile, "text")
				with open(tFileFull, "r") as f2:
					content = f2.read()
					lines = content.count("\n")
					indices += [index] * lines
					f1.write(content)
		writeJSON(lib.indFile, indices)
		writeJSON(lib.metaFile, dic)
	print("Finished updating library" if changes else "Library up to date")

def _getCitation(doi, style = "plain"):
	url = "http://dx.doi.org/" + doi
	styles = {
		"bibtex" : "text/bibliography; style=bibtex",
		"json" : "application/vnd.citationstyles.csl+json",
		"plain" : "text/x-bibliography",
	}
	selStyle = styles.get(style, styles["plain"])
	request = urllib2.Request(url, headers = {"Accept" : selStyle})
	try:
		contents = urllib2.urlopen(request).read().decode("utf8")
		return contents
	except:
		return None

def _parseBibtex(bibStr):
	bib = pybtex.database.parse_string(bibStr, "bibtex")
	key1 = bib.entries.keys()[0]
	entry = bib.entries[key1].fields
	authorList = [unicode(p) for p in bib.entries[key1].persons["author"]]
	fields = {
		"journal" : entry.get("journal"),
		"year" : entry.get("year"),
		"url" : entry.get("url"),
		"authors" : authorList
	}
	# create and return dict with None values removed
	result = dict((k, v) for k, v in fields.iteritems() if v)
	return result

def _reformatBibtex(bibStr):
	bib = pybtex.database.parse_string(bibStr, "bibtex")
	return bib.to_string('bibtex')

def _getTitleDOI(title):
	# api doc: https://github.com/CrossRef/rest-api-doc/blob/master/rest_api.md
	escaped = urllib2.quote(title)
	url = "https://api.crossref.org/works?query.title=%s&rows=10" % escaped
	result = urllib2.urlopen(url).read()
	dic = json.loads(result)
	results = []
	for item in dic["message"]["items"]:
		results.append({
			"DOI": item["DOI"],
			"title": item["title"][0]
		})
	return results

def _getBibtex(DOI):
	bibStr = _getCitation(DOI, "bibtex")
	return _reformatBibtex(bibStr) if bibStr else None

def _readTitleFile():
	file = '/tmp/title.txt'
	with open(file, 'r') as f:
		lines = f.read().strip().split('\n')
		return (' '.join(lines) if len(lines)>1 else lines[0])
	return None

def getLocalPath():
	# returns path of python script
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def _getPaperTitle(pdf):
	script = "shell/getTitle.sh"
	subprocess.call([script, pdf], cwd=getLocalPath())
	return _readTitleFile()

def convertPDF(pdfFile, textFile):
	script = "shell/pdf2text.sh"
	subprocess.call([script, pdfFile, textFile], cwd=getLocalPath())

def _getLibPaperTitle(metaFile):
	script = "shell/fzTitles.sh"
	subprocess.call([scriptPath, metaFile], cwd=getLocalPath())
	return _readTitleFile()

def _promptInput(prompt, options = ["y", "Y", "N", "n", ""], autoYes = False):
	if autoYes:
		return "y"
	else:
		try:
			while True:
				inp = raw_input(prompt)
				if inp in options:
					return inp
		except KeyboardInterrupt:
			print ""
			sys.exit(1)

def getFileDOI(pdf):
	maxLength = 80
	title = _getPaperTitle(pdf)
	if not title:
		return None
	os.system('clear')
	ctitle = num = colored(title, attrs=['bold'])
	print("Query: %s\n" % ctitle)
	print("Searching title on crossref.org ...\n")
	results = _getTitleDOI(title)
	if results:
		print("Matches:\n")
		for ind, item in enumerate(results):
			numStr = "%2d." % (ind+1)
			DOI = colored(item["DOI"], color='green', attrs=[])
			title = item["title"]
			titleShort = title[:maxLength] + (title[maxLength:] and ' ..')
			num = colored(numStr, color='magenta')
			print("%s %s" % (num, titleShort))
			print("    (%s)" % DOI)
		print("")
		opts = ["s", "S", "q", "Q"] + [str(x) for x in range(1, 11)]
		selected = _promptInput('Enter number, [S]kip or [Q]uit: ', opts)
		if selected.lower() == "s":
			return None
		elif selected.lower() == "q":
			sys.exit(0)
		else:
			return results[int(selected)-1]
	else:
		print("no results were found")
