from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup as BS
import smtplib
import ssl
import getpass
import time

# The email account info for this script is:
# Username: tyler.python.email@gmail.com
# Password: See password store
# This script only seems to work in python 3.5.6.

port = 587
password = ''
addressFrom = ''
addressTo = ''
url = 'https://losangeles.craigslist.org/search/zip?postedToday=1'
keywords = []
prev_matches = [['']]


def getPage(url):
	try:
		with closing(get(url, stream=True)) as resp:
			if isGoodResp(resp):
				return resp.content
			else:
				return None

	except RequestException as e:
		log_error('Error during request to {0} : {1}'.format(url, str(e)))
		return None


def isGoodResp(resp):
	content_type = resp.headers['Content-Type'].lower()
	return (resp.status_code == 200
			and content_type is not None
			and content_type.find('html') > -1)


def log_error(e):
	fid = open('log.txt', 'w')
	fid.write(e)
	fid.close()


def fileDump(content):
	fid = open('pageData.txt', 'w')
	fid.write(content)
	fid.close()


def printTitles(results): # Prints only the titles of a results list
	N = len(results)

	if N == 0: return

	for i in range(0,N):
		string = str(i) + ': ' + results[i][0]
		print(string)


def getResults(content):
	html = BS(content, 'html.parser')
	p = html.select('p')
	results = []

	for i in range(0, len(p)):
		if str(p[i]).find('result-info'): #Found the beginning of a result section
			result_contents = [None]*4 # Title, Date, Neighborhood, Link			
			line = str(p[i]).split('\n') # Break the result section up by lines
			
			for j in range(0,len(line)):
				if line[j].find('result-hood') > -1: # Found the neighborhood data
					ind1 = line[j].find('(')+1
					ind2 = line[j].find(')')
					result_contents[2] = line[j][ind1:ind2] # Isolate neighborhood

				if line[j].find('result-date') > -1: # Found post time info
					ind1 = line[j].find('title=')+7
					ind2 = line[j].find('>')-1
					result_contents[1] = line[j][ind1:ind2] # Isolate date and time

				if line[j].find('result-title hdrlnk') > -1: # Found result title and link
					ind1 = line[j].find('>')+1
					ind2 = line[j].find('</a>')
					result_contents[0] = line[j][ind1:ind2] # Isolate title

					ind1 = line[j].find('href=')+6
					ind2 = line[j].find('>')-1
					result_contents[3] = line[j][ind1:ind2] # Isolate link

			results.append(result_contents)
			
	return results


def searchResults(results, keywords):
	n_res = len(results)
	n_keys = len(keywords)
	matching_results = []

	for i in range(0, n_res):
		for j in range(0, n_keys):
			if results[i][0].upper().find(keywords[j].upper()) > -1: # Found a matching result
				matching_results.append(results[i])

	return matching_results


def manageResults(new_matches):
	global prev_matches
	identical = []

	print('\n\n============================================')
	print('\nPREVIOUS MATCHES\n')
	printTitles(prev_matches)
	print('\nNEW MATCHES\n')
	printTitles(new_matches)

	# Compare the new and previous matching results
	for i in range(0,len(prev_matches)):
		for j in range(0,len(new_matches)):
			if prev_matches[i] == new_matches[j]: # found an identical result. Record the new_matches index so we can remove it
				identical.append(new_matches[j])

	print('\nIDENTICAL MATCHES\n')
	printTitles(identical)
	# Remove the identical results
	for i in range(0,len(identical)):
		try:
			new_matches.remove(identical[i])
		except:
			print('result error')

	# Add the remaining non-matching results to previous results
	for i in range(0,len(new_matches)):
		prev_matches.append(new_matches[i])

	print('\nUNIQUE MATCHES\n')
	printTitles(new_matches)

	return new_matches


def getAccounts():
	global addressTo
	global addressFrom
	global password

	#addressTo = input("Enter the email address to receive notifications: ")
	#addressFrom = input("Enter the email address to send notifications from: ")
	#password = getpass.getpass(prompt = 'Enter the sending account password: ')

	# For development use
	addressTo = 'tyler.slone47@gmail.com'
	addressFrom = 'tyler.python.email@gmail.com'
	password = 'txS485FI0WI&'


def getKeywords():
	global keywords

	userStr = input('Enter search keywords separated by commas: ')
	userStr = userStr.split(',')

	for i in range(0,len(userStr)):
		if userStr[i][0] == ' ': # The first character is a space. Remove the 1st character.
			userStr[i] = userStr[i][1:len(userStr[i])]

		keywords.append(userStr[i])


def makeEmail(match):
	header = '''From: Craigslist Scraper <%s>

	''' % addressFrom

	contents = '''Craigslist Scraper has identified a new result that matches your keywords: %s

	Title: %s
	Posting Time: %s
	Location: %s
	Link to Post: %s

	''' % (str(keywords).strip('[').strip(']'), match[0], match[1], match[2], match[3])

	email = header + contents

	print(email)

	return email


def sendEmail(addressFrom, addressTo, password, contents, port):
	server = 'smtp.gmail.com'

	try:
		server = smtplib.SMTP(server, port)
		server.ehlo()
		server.starttls()
		server.ehlo()
		server.login(addressFrom, password)
		
		server.sendmail(addressFrom, addressTo, contents)

	except Exception as e:
		print(e)
	finally:
		server.quit()


def report(matches):
	global addressFrom
	global addressTo
	global password
	global port

	# Iterate through the matching results and send an email for each one
	N = len(matches)

	for i in range(0,N):
		email_body = makeEmail(matches[i])
		sendEmail(addressFrom, addressTo, password, email_body, port)


def periodicScrape(period):
	getAccounts()
	getKeywords()

	while(True):
		content = getPage(url)
		results = getResults(content)
		new_matches = searchResults(results, keywords)
		unique_matches = manageResults(new_matches)
		report(unique_matches)

		time.sleep(period)


periodicScrape(60)
