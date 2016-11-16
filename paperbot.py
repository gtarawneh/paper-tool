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

def getAbsolutePath(dir, file):
	return os.path.join(dir, file)

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

def getLibrary():
	homeDir = os.getenv("HOME")
	args = sys.argv[1:]
	configFile = getAbsolutePath(homeDir, ".papertool")
	conf = loadJSON(configFile)
	libName = args[0] if args else conf["default"]
	return conf[libName]

def getListBibtexFiles(bibDir):
	files = [f for f in os.listdir(bibDir) if os.path.isfile(os.path.join(bibDir, f))]
	return files

def main():
	libDir = getLibrary()
	pdfsDir = getAbsolutePath(libDir, "pdfs")
	metaFile = getAbsolutePath(libDir, "meta/meta.json")
	bibDir = getAbsolutePath(libDir, "bibtex")
	args = sys.argv[1:]
	if "-l" in args:
		_getLibPaperTitle(metaFile)
		return
	bibFiles = getListBibtexFiles(bibDir)
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
		selection = _promptInput(prompt)
		if selection.lower() in ["y", ""]:
			for entry in entriesMissingDOI:
				fullFile = os.path.join(pdfsDir, entry["file"])
				papInfo = getFileDOI(fullFile)
				if papInfo:
					entry["DOI"] = papInfo["DOI"]
					entry["title"] = papInfo["title"]
					entry["added"] = getDateTimeStamp()
					changes = True
			print("")
	# check for missing bibtex files
	entriesMissingBib = [entry for entry in dic if not entry.get("sha256") + ".bib" in bibFiles]
	if entriesMissingBib:
		n = len(entriesMissingBib)
		prompt = "There are %d missing bibtex entries, attempt to fetch [Y/n]? " % n
		selection = _promptInput(prompt)
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
					print("done")
				else:
					print("FAILED")

	if changes:
		writeJSON(metaFile, dic)
		print("Finished updating library")
	else:
		print("Library up to date")

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

def _getPaperTitle(pdf):
	subprocess.call(['./getTitle.sh', pdf])
	return _readTitleFile()

def _getLibPaperTitle(metaFile):
	subprocess.call(['./fzTitles.sh', metaFile])
	return _readTitleFile()

def _promptInput(prompt, options = ["y", "Y", "N", "n", ""]):
	# returns None or an int in [1,10]
	while True:
		inp = raw_input(prompt)
		if inp in options:
			return inp

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

main()
