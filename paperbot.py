#!/bin/python

import sys
import os
import hashlib
import json
import datetime
import subprocess
import urllib2
import pybtex.database
import codecs
from termcolor import colored, cprint

def getSHA256(file):
	hasher = hashlib.sha256()
	with open(file, 'rb') as afile:
		buf = afile.read()
		hasher.update(buf)
	return hasher.hexdigest()

def getAbsolutePath(directory, file):
	return os.path.join(directory, file)

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

def getDateTimeStamp():
	return str(datetime.datetime.now())

def getFileHash(libDir):
	dic = {}
	for root, dirs, files in os.walk(libDir):
		for file in files:
			fullFile = os.path.abspath(os.path.join(root, file))
			relFile = os.path.relpath(fullFile, libDir)
			dic[relFile] = getSHA256(fullFile)
	return dic

def loadJSON(file):
	try:
		with open(file) as f:
			return json.load(f)
	except ValueError as e:
		print(e)
		raise Exception('Error encountered while parsing %s' % file)

def getFileList(bibDir):
	files = [f for f in os.listdir(bibDir) if os.path.isfile(os.path.join(bibDir, f))]
	return files

def getTextFile(entry):
	# returns text file given a dictionary `entry` containing a pdf filename
	tFile = entry["sha256"] + ".txt"
	return tFile

def updateLibrary(libDir, autoYes = False):
	pdfsDir = getAbsolutePath(libDir, "pdfs")
	metaFile = getAbsolutePath(libDir, "meta/meta.json")
	bibDir = getAbsolutePath(libDir, "bibtex")
	textDir = getAbsolutePath(libDir, "text")
	senDir = getAbsolutePath(libDir, "sentences")
	args = sys.argv[1:]
	if "-l" in args:
		_getLibPaperTitle(metaFile)
		return
	bibFiles = getFileList(bibDir)
	textFiles = getFileList(textDir)
	fileHash = getFileHash(pdfsDir)
	dic = readJSON(metaFile)
	hmap = {entry["sha256"]:entry for entry in dic} # sha256 -> dic entry
	changes = False
	# first, loop through files in the lib directory
	fileList = []
	for relFile, fileHash in fileHash.iteritems():
		fullFile = os.path.join(pdfsDir, relFile)
		fileList.append(relFile)
		existingEntry = hmap.get(fileHash, None)
		if existingEntry:
			if relFile != existingEntry["file"]:
				print("file moved: %s -> %s" % (existingEntry["file"], relFile))
				existingEntry["file"] = relFile
				existingEntry["added"] = getDateTimeStamp()
				changes = True
		else:
			print("found new file %s" % relFile)
			dic.append({
				"file": relFile,
				"sha256": fileHash,
				"added": getDateTimeStamp(),
			});
			changes = True
	# check for deleted files
	delFiles = [entry for entry in dic if entry["file"] not in fileList]
	for entry in delFiles:
		print("file deleted: %s" % entry["file"])
		dic.remove(entry)
		changes = True
	# check for missing DOIs/titles
	entriesMissingDOI = [entry for entry in dic if not entry.get("DOI") or not entry.get("title")]
	if entriesMissingDOI:
		n = len(entriesMissingDOI)
		prompt = "There are %d new paper entries, search for title and DOI [Y/n]? " % n
		selection = _promptInput(prompt, autoYes=autoYes)
		if selection.lower() in ["y", ""]:
			for entry in entriesMissingDOI:
				fullFile = os.path.join(pdfsDir, entry["file"])
				papInfo = getFileDOI(fullFile)
				if papInfo:
					entry["DOI"] = papInfo["DOI"]
					entry["title"] = papInfo["title"]
					entry["added"] = getDateTimeStamp()
					writeJSON(metaFile, dic)
					changes = True
			print("")
	# check for missing bibtex files
	getBibFile = lambda entry : entry.get("sha256") + ".bib"
	getTextFile = lambda entry : entry.get("sha256") + ".txt"
	hasDOI = lambda entry : "DOI" in entry
	hasBib = lambda entry :  getBibFile(entry) in bibFiles
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
					bibFile = "bibtex/" + entry["sha256"] + ".bib"
					bibFileFull = getAbsolutePath(libDir, bibFile)
					with codecs.open(bibFileFull, "w", "utf8") as f:
						f.write(bibStr)
					bibInfo = _parseBibtex(bibStr)
					entry.update(bibInfo)
					writeJSON(metaFile, dic)
					print("done")
				else:
					print("FAILED")
	# check for missing text files
	rebuildSentences = False
	hasText = lambda entry : getTextFile(entry) in textFiles
	entriesMissingText = [entry for entry in dic if hasDOI(entry) and not hasText(entry)]
	if entriesMissingText:
		n = len(entriesMissingText)
		prompt = "There are %d new paper pdfs, extract text [Y/n]? " % n
		selection = _promptInput(prompt, autoYes=autoYes)
		if selection.lower() in ["y", ""]:
			changes = True
			for entry in entriesMissingText:
				pFile = entry["file"]
				tFile = getTextFile(entry)
				pFileFull = getAbsolutePath(pdfsDir, pFile)
				tFileFull = getAbsolutePath(textDir, tFile)
				print "Extracting text from %s ... " % pFile
				convertPDF(pFileFull, tFileFull)
			rebuildSentences = True
	# rebuild sentences
	if rebuildSentences:
		print "Updating sentence files ..."
		sFile = "sentences.txt"
		iFile = "index.json"
		sFileFull = getAbsolutePath(senDir, sFile)
		iFileFull = getAbsolutePath(senDir, iFile)
		indices = []
		with open(sFileFull, "w") as f1:
			for index, entry in enumerate(dic):
				tFile = getTextFile(entry)
				tFileFull = getAbsolutePath(libDir, "text/" + tFile)
				with open(tFileFull, "r") as f2:
					content = f2.read()
					lines = content.count("\n")
					indices += [index] * lines
					f1.write(content)
		writeJSON(iFileFull, indices)
		writeJSON(metaFile, dic)
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
	authorList = []
	for p in bib.entries[key1].persons["author"]:
		authorList.append(unicode(p))
	fields = {
		"journal" : entry.get("journal"),
		"year" : entry.get("year"),
		"url" : entry.get("url"),
		"authors" : " and ".join(authorList)
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
	os.system('clear')
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
		opts = ["s", "S"] + [str(x) for x in range(1, 11)]
		selected = _promptInput('Enter number or [s]kip: ', opts)
		if selected.lower() == "s":
			return None
		else:
			return results[int(selected)-1]
	else:
		print("no results were found")
