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

def main():
	dic = []
	homeDir = os.getenv("HOME")
	libDir = getAbsolutePath(homeDir, "pdfs")
	for root, dirs, files in os.walk(libDir):
		path = root.split('/')
		for file in files:
			file = os.path.abspath(os.path.join(root, file))
			dic.append({
				"file": file,
				"sha256": getSHA256(file),
				"added": str(datetime.datetime.now()),
			});
	print(json.dumps(dic, indent=4))

main()
