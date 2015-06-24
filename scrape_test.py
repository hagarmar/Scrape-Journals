from bs4 import BeautifulSoup
import requests 
import re
import pymongo
from pymongo import MongoClient
import time
import datetime

# consts
ARTICLE_TYPES = ['ResearchArticles', 'Reports'] # which authors to look for
SCIENCE_MAIN_PAGE = "http://www.sciencemag.org/"
VOLUME_NOTATION = "Vol. "
ISSUE_NOTATION = "#"
MONTHS = {"January":1, "February":2, "March":3, "April": 4, "May":5, "June":6, "July":7, 
		  "August":8, "September":9, "October":10, "November":11, "December":12}

# returns soup object for website_url or None if doesn't work
def get_soup_webpage(website_url):
	page = requests.get(website_url)
	time.sleep(1) # pause 1 sec between pages
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

	return int(vol_number), int(issue_number)

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

# gets the author names and their affiliations from the abstract page of the article
# returns a list of dicts of authors and affiliations
def get_affs_and_authors(website_url):
	soup = get_soup_webpage(website_url)
	if not soup:
		return None

	# make dict of aff number and aff name
	all_affiliations = soup.select("li.aff")
	all_affs_and_numbers = {}

	for aff in all_affiliations:
	    # clean the affiliations text: /n, trailing whitespaces, trailing "."
	    aff_text = " ".join([x.strip() for x in aff.address.text[1:].strip().strip('.').split('\n')])    
	    
	    #create dict with aff # and name for use with author affiliation numbers
	    all_affs_and_numbers[aff.a["name"]] = aff_text

	# get author names and affiliations
	# then compare to aff numbers found before
	all_authors = soup.select("li.contributor")
	all_authors_and_affs = []

	for author in all_authors:
	    author_name = author.find(class_="name-search").text.strip()
	    author_aff_numbers = [x.get("href")[1:] for x in author.find_all(class_="xref-aff")]
	    
	    author_affs_and_numbers = []
	    
	    for aff_number in author_aff_numbers:
	        author_affs_and_numbers.append(all_affs_and_numbers[aff_number])

	    single_author = {"name":author_name, "affiliation":author_affs_and_numbers}
	    all_authors_and_affs.append(single_author)

	return all_authors_and_affs


def get_all_data_issue_view(website_url, issue_number, vol_number):
	soup = get_soup_webpage(website_url)
	if not soup:
		return None

	all_articles_in_view = []
	
	# for our article_types return what we need:
	for article_type in ARTICLE_TYPES:

		# list with all articles of specific type in this issue
		all_articles_of_type = soup.select("div.pub-section-%s li.toc-cit" % article_type)

		for article in all_articles_of_type:

		    # get article title
		    title_raw=article.select("h4")
		    p=re.compile('>.*?<') # get all elements of the title, between > and <
		    title_matches = p.findall(str(title_raw))

		    full_title = []
		    for part in title_matches:
		        full_title.append(part[1:-2]) # get without < and >
		    # get all article authors
		    #all_article_authors = ([x.string for x in article.select("span.cit-auth-type-author")])

		    # get author affiliations??
		    first_page = article.find("div", {"class":"cit-extra"}).a.get("href")

		    abstract_website_url = SCIENCE_MAIN_PAGE[:-1] + first_page
		    all_affiliations_and_authors = get_affs_and_authors(abstract_website_url)

		    # get article date
		    article_date_raw = article.find("span", {"class":"cit-print-date"}).get_text().replace(":", "").strip().split()
		    date_format = datetime.datetime(int(article_date_raw[2]), MONTHS[article_date_raw[1]], int(article_date_raw[0]))

		    # get journal name
		    journal_name = article.find("abbr").string

		    # put all in list of dicts
		    all_articles_in_view.append({"title": str(full_title[0]), 
		                                 "type": article_type, 
		                                 "authors": all_affiliations_and_authors, #all_article_authors, 
		                                 "date": date_format,
		                                 "journal": journal_name,
		                                 "issue number": issue_number,
		                                 "volume number": vol_number,
		                                 "url" : abstract_website_url})


	return all_articles_in_view

# scrape author names from n_issues
# returns list with all author names
def scrape_Science_simple(n_of_issues):

	# get curr issue and vol from main page
	vol_number, issue_number = get_latest_issue_Science()
	all_issue_authors = []	

	while n_of_issues>0:
		
		website_url = SCIENCE_MAIN_PAGE + "content/" + str(vol_number) + "/" + str(issue_number) + ".toc"
		response = get_authors_Science(website_url, True)

		if not response:
			vol_number = vol_number - 1
			continue
		else:
			all_issue_authors.append(get_authors_Science(website_url, True))
			issue_number = issue_number - 1
			n_of_issues = n_of_issues - 1
			time.sleep(1) # pause for 1 sec between pages

	return all_issue_authors

# scrape article data from science journal
# returns list of dicts from each issue and enter to MongoDB
def scrape_Science_db(n_of_issues):

	# init response with None
	response = None

	# connect to mongoDB
	connection = MongoClient('localhost', 27017)
	db = connection.journals
	collection = db.authors

	# get curr issue and vol from main page
	vol_number, issue_number = get_latest_issue_Science()

	while n_of_issues>0:
		
		# check if in db before scrape
		vol_issue_in_db = collection.find({"issue number": issue_number, "volume number": vol_number})

		if not vol_issue_in_db.count(): # if not in db: get data
			website_url = SCIENCE_MAIN_PAGE + "content/" + str(vol_number) + "/" + str(issue_number) + ".toc"
			response = get_all_data_issue_view(website_url, issue_number, vol_number)

			#time.sleep(1) # pause for 1 sec between pages

			if not response: # if the vol num should be changed: query issue num again with diff vol num
				vol_number = vol_number - 1
			else: # if got a response, decrease n_of_issues and issue number
				collection.insert(response)
				n_of_issues = n_of_issues - 1
				issue_number = issue_number - 1

		else: # if was in db: decrease issue num and n_of_issues 
			issue_number = issue_number - 1
			n_of_issues = n_of_issues - 1

	connection.close()

	return response


#print get_authors_Science("http://www.sciencemag.org/content/346/6215.toc", True)
#print get_latest_issue_Science()
