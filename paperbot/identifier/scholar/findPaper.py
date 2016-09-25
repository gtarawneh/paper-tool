#!/bin/python

from scholar import *

def findPaper(phrase):
	querier = ScholarQuerier()
	settings = ScholarSettings()
	querier.apply_settings(settings)
	query = SearchScholarQuery()
	query.set_phrase(phrase)
	query.set_num_page_results(2)
	querier.send_query(query)
	txt(querier, False)
	articles = querier.articles
	# if not articles:
	# 	print('Error, could not find any match')
	# 	return 1
	# elif len(articles) > 1:
	# 	print('Error, found more than one match')
	# 	return 1
	# else:
	for art in articles:
		print(art["title"])
		# print(art["year"])
		# print(art["url"])
		# print(art["url_pdf"])

phrase = "spatiotemporal energy models for the perception of motion"

findPaper(phrase)
