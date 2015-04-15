from bs4 import BeautifulSoup
import requests 
import re

# consts
ARTICLE_TYPES = ['ResearchArticles', 'Reports'] # which authors to look for
SCIENCE_MAIN_PAGE = "http://www.sciencemag.org/"
VOLUME_NOTATION = "Vol. "
ISSUE_NOTATION = "#"

# returns soup object for website_url or None if doesn't work
def get_soup_webpage(website_url):
	page = requests.get(website_url)
	if not page.ok: # if the page was returned ok
		return None
	
	soup = BeautifulSoup(page.text)
	return soup

# from Science main page get the last issue and volume numbers
# returns vol_number: latest vol number, issue_number: latests issue number
def get_latest_issue_Science():

	soup = get_soup_webpage(SCIENCE_MAIN_PAGE)
	if not soup:
		return None

	current_issue_name = str(soup.select("div.sci-block-cn p.titler")) # get journal curr issue text
	vol_number = current_issue_name.split(VOLUME_NOTATION)[1].split(',')[0]
	issue_number = current_issue_name.split(ISSUE_NOTATION)[1].split('<')[0]

	return vol_number, issue_number

# returns list of authors from a website_url in Science magazine, certain issue + vol
# if is_all_authors=True, returns all authors
# if is_all_authors=False, returns first/last author
def get_authors_Science(website_url, is_all_authors=True):
	
	soup = get_soup_webpage(website_url)
	if not soup:
		return None

	authors = []
	# for our article_types return authors
	for article_type in ARTICLE_TYPES:
		if is_all_authors:
			authors.extend([x.string for x in soup.select("div.pub-section-%s span.cit-auth-type-author" % article_type)])
		else:
			authors.extend([x.string for x in soup.select("div.pub-section-%s li.first-item span.cit-auth-type-author" % article_type)]) # first
			authors.extend([x.string for x in soup.select("div.pub-section-%s li.last-item span.cit-auth-type-author" % article_type)]) # last

	return authors 

# scrape author names from n_issues
# returns list with all author names
def scrape_Science(n_of_issues):

	# get curr issue and vol from main page
	vol_number, issue_number = get_latest_issue_Science()
	all_issue_authors = []

	while n_of_issues>0
		
		website_url = "http://www.sciencemag.org/content/" + str(vol_number) + "/" + str(issue_number) + ".toc"
		response = get_authors_Science(website_url, True)
		
		if not response:
			vol_number = vol_number - 1
			continue
		else:
			all_issue_authors.append(get_authors_Science(website_url, True))
			issue_number = issue_number - 1
			n_of_issues = n_of_issues - 1
	return all_issue_authors

#print get_authors_Science("http://www.sciencemag.org/content/346/6215.toc", True)
print get_latest_issue_Science()
