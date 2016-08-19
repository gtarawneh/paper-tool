#!/usr/bin/python

import os
import parser

metaFileCount = 0
missingMetaCount = 0
yearFail = 0
titleFail = 0

content = []

for root, dirs, files in os.walk("./text"):
	path = root.split('/')
	for file in files:
		textFile = os.path.abspath(os.path.join(root, file))
		with open(textFile) as f:
			content += f.read().splitlines()
		metaFile = textFile.replace('/text/', '/meta/')
		# print('Parsing %s ...' % metaFile)
		meta = parser.parseMetaFile(metaFile)
		if meta['year'] == None:
			yearFail += 1
		if meta['title'] == None:
			titleFail += 1
		# parser.printMetaInfo(meta)
		# print('-' * 40)
		if os.path.exists(metaFile):
			metaFileCount += 1
		else:
			missingMetaCount += 1

content = list(set(content))

print("meta & text files = %d" % metaFileCount)
print("text files without meta = %d" % missingMetaCount)
print("year fail = %d" % yearFail)
print("title fail = %d" % titleFail)
print("lines = %d" % len(content))
