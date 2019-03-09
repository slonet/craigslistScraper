from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup as BS
import smtplib
import ssl

# The email account info for this script is:
# Username: tyler.python.email@gmail.com
# Password: See password store

email_port = 587
password = ''
addressFrom = 'tyler.python.email@gmail.com'
addressTo = 'tyler.slone47@gmail.com'
url = 'https://losangeles.craigslist.org/search/zip?postedToday=1'
keywords = ['table', 'desk']
prev_matches = None

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


def grabResults(content):
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
			if results[i][0].find(keywords[j]) > -1: # Found a matching result
				matching_results.append(results[i])

	return matching_results


def getPassword():
	global password
	password = input("Enter the email account password: ")
	print(type(password))
	print(password)


def sendEmail(addressFrom, addressTo, password, contents, port):
	server = 'smtp.gmail.com'

	ctxt = ssl.create_default_context()

	try:
		server = smtplib.SMTP(server, port)
		server.ehlo()
		server.starttls(context=ctxt)
		server.ehlo()
		server.login(addressFrom, password)
		#TODO: Send an email
	except Exception as e:
		print(e)
	finally:
		server.quit()

#content = getPage(url)
#res = grabResults(content)
#matches = searchResults(res, keywords)
#print(matches)
getPassword()
sendEmail(addressFrom, addressTo, password, 'This is an email', email_port)