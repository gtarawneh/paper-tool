#!/usr/bin/python

import os
import parser
import json
import sys

def buildLibrary(textDir, libDir):
	senFile = 'sentences.txt'
	infoFile = 'paper-info.json'
	indexFile = 'index.json'
	# prepare list of text files:
	textFileList = []
	for root, dirs, files in os.walk("./text"):
		path = root.split('/')
		for file in files:
			textFile = os.path.abspath(os.path.join(root, file))
			textFileList.append(textFile)
	# process text files:
	content = []
	infoList = []
	indexList = []
	# metaFileCount = 0
	# yearFail = 0
	# titleFail = 0
	for ind, textFile in enumerate(textFileList):
		with open(textFile) as f:
			fileContent = f.read().splitlines()
			content += fileContent
			indexList += [ind] * len(fileContent)
			metaFile = textFile.replace('/text/', '/meta/')
			# meta = parser.parseMetaFile(metaFile)
			# meta['_file'] = metaFile
			meta = {'_file': textFile}
			infoList.append(meta)
			# yearFail += 1 if meta['year'] == None else 0
			# titleFail += 1 if meta['title'] == None else 0
			# metaFileCount += 1 if os.path.exists(metaFile) else 0
	# write library files:
	writeJSON(infoList, infoFile)
	writeJSON(indexList, indexFile)
	with open(senFile, 'w') as f:
		for line in content:
			f.write("%s\n" % line)

def writeJSON(d, file):
	# writes dictionary d to file
	with open(file, 'w') as f:
		json.dump(d, f, sort_keys = True, indent = 4, ensure_ascii=True)

# print("meta & text files = %d (%1.1f%%)" % (metaFileCount, float(metaFileCount) / len(textFileList) * 100))
# print("year fail = %d (%1.1f%%)" % (yearFail, float(yearFail) / len(textFileList) * 100))
# print("title fail = %d (%1.1f%%)" % (titleFail, float(titleFail) / len(textFileList) * 100))
# print("lines = %d" % len(content))
