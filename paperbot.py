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

def main():
	homeDir = os.getenv("HOME")
	libDir = getAbsolutePath(homeDir, "pdfs")
	libFile = getAbsolutePath(homeDir, "pdfs.json")
	dic = readJSON(libFile)
	hmap = {entry["sha256"]:entry for entry in dic}
	changes = False
	# first, loop through files in the lib directory
	fileList = []
	for root, dirs, files in os.walk(libDir):
		path = root.split('/')
		for file in files:
			fullFile = os.path.abspath(os.path.join(root, file))
			relFile = os.path.relpath(fullFile, libDir)
			fileHash = getSHA256(fullFile)
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
	# check for deleted file
	delFiles = [entry for entry in dic if entry["file"] not in fileList]
	for entry in delFiles:
		print("file deleted: %s" % entry["file"])
		changes = True
		dic.remove(entry)
	if changes:
		writeJSON(libFile, dic)
	else:
		print("no changes detected")
	print(json.dumps(dic, indent=4))

main()
