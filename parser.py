#!/bin/python

from lxml import etree

import re

def parseMetaFile(metaFile):
	d = {
		'persName' : './/{http://www.tei-c.org/ns/1.0}persName',
		'surname': '{http://www.tei-c.org/ns/1.0}surname',
		'forename': '{http://www.tei-c.org/ns/1.0}forename',
		'titleStmt': './/{http://www.tei-c.org/ns/1.0}titleStmt',
		'title' : '{http://www.tei-c.org/ns/1.0}title',
		'publicationStmt' : './/{http://www.tei-c.org/ns/1.0}publicationStmt',
		'date' : '{http://www.tei-c.org/ns/1.0}date',
	}
	meta = {
		'_file' : metaFile,
		'authors' : [],
		'title': None,
		'year' : None,
	}
	try:
		q = etree.parse(metaFile)
		for persName in q.findall(d['persName']):
			forename = persName.findtext(d['forename'])
			surname = persName.findtext(d['surname'])
			meta['authors'].append('%s %s' % (forename, surname))
		for ts in q.findall(d['titleStmt']):
			meta['title'] = ts.findtext(d['title'])
		for ps in q.findall(d['publicationStmt']):
			dat = ps.findtext(d['date'])
			if dat:
				match = re.search('[0-9]{4}', dat)
				if match:
					meta['year'] = match.group(0)
	except:
		pass
	return meta

def printMetaInfo(meta):
	print 'Title: %s' % meta['title']
	print 'Year: %s' % meta['year']
	for author in meta['authors']:
		print('Author: %s' % author)

def main():
	xmlFile = '/cygdrive/d/dev/papertool/meta/A/AdelsonBergen85.txt'
	meta = parseMetaFile(xmlFile)
	printMetaInfo(meta)

# main()
