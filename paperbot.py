#!/bin/python

import os
import hashlib
import json
import datetime

def getSHA256(file):
	hasher = hashlib.sha256()
	with open(file, 'rb') as afile:
		buf = afile.read()
		hasher.update(buf)
	return hasher.hexdigest()

def getAbsolutePath(libDir, file):
	return os.path.join(libDir, file)

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

def main():
	homeDir = os.getenv("HOME")
	libDir = getAbsolutePath(homeDir, "pdfs")
	libFile = getAbsolutePath(homeDir, "pdfs.json")
	fileHash = getFileHash(libDir)
	dic = readJSON(libFile)
	hmap = {entry["sha256"]:entry for entry in dic} # sha256 -> dic entry
	changes = False
	# first, loop through files in the lib directory
	fileList = []
	for relFile, fileHash in fileHash.iteritems():
		fullFile = os.path.join(libDir, relFile)
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
	if changes:
		writeJSON(libFile, dic)
	print(json.dumps(dic, indent=4))

import urllib2
import pybtex.database

def getCitation(doi, style = "plain"):
	url = "http://dx.doi.org/" + doi
	styles = {
		"bibtex" : "text/bibliography; style=bibtex",
		"json" : "application/vnd.citationstyles.csl+json",
		"plain" : "text/x-bibliography",
	}
	selStyle = styles.get(style, styles["plain"])
	request = urllib2.Request(url, headers = {"Accept" : selStyle})
	contents = urllib2.urlopen(request).read()
	return contents

def reformatBibtex(bibStr):
	bib = pybtex.database.parse_string(bibStr, "bibtex")
	return bib.to_string('bibtex')

def searchTitle(title):
	# api doc: https://github.com/CrossRef/rest-api-doc/blob/master/rest_api.md
	escaped = urllib2.quote(title)
	url = "https://api.crossref.org/works?query.title=%s&rows=1" % escaped
	result = urllib2.urlopen(url).read()
	dic = json.loads(result)
	for item in dic["message"]["items"]:
		print "%s : %s" % (item["DOI"], item["title"][0])

bibStr = getCitation("10.1109/async.2009.8", "bibtex")

print(reformatBibtex(bibStr))

searchTitle("formal verification of clock domain crossing using gate level models")

# main()
