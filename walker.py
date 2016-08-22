#!/usr/bin/python

import os
import parser
import json
import sys

senFile = 'sentences.txt'
infoFile = 'paper-info.json'
indexFile = 'index.json'

fileList = []

for root, dirs, files in os.walk("./text"):
	path = root.split('/')
	for file in files:
		textFile = os.path.abspath(os.path.join(root, file))
		fileList.append(textFile)

content = []
infoList = []
indexList = []

metaFileCount = 0
yearFail = 0
titleFail = 0

for ind, textFile in enumerate(fileList):
	with open(textFile) as f:
		fileContent = f.read().splitlines()
		content += fileContent
		indexList += [ind] * len(fileContent)
		metaFile = textFile.replace('/text/', '/meta/')
		meta = parser.parseMetaFile(metaFile)
		meta['_file'] = metaFile
		infoList.append(meta)
		yearFail += 1 if meta['year'] == None else 0
		titleFail += 1 if meta['title'] == None else 0
		metaFileCount += 1 if os.path.exists(metaFile) else 0

with open(infoFile, 'w') as f:
	json.dump(infoList, f, sort_keys = True, indent = 4, ensure_ascii=True)

with open(indexFile, 'w') as f:
	json.dump(indexList, f, sort_keys = True, indent = 4, ensure_ascii=True)

with open(senFile, 'w') as f:
	for line in content:
		f.write("%s\n" % line)

print("meta & text files = %d (%1.1f%%)" % (metaFileCount, float(metaFileCount) / len(fileList) * 100))
print("year fail = %d (%1.1f%%)" % (yearFail, float(yearFail) / len(fileList) * 100))
print("title fail = %d (%1.1f%%)" % (titleFail, float(titleFail) / len(fileList) * 100))
print("lines = %d" % len(content))
