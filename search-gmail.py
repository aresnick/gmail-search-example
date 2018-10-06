#! /usr/bin/env python

# For accessing, parsing results from Gmail API
from httplib2 import Http
from apiclient import discovery
from oauth2client import file, client, tools
import base64 # For decoding responses
import email # For parsing email messages

# For parsing and cleaning up HTML
from bs4 import BeautifulSoup
import re
import quopri

# For exporting messages
import json 

# Setting up logging
import logging
logging.basicConfig(level=logging.ERROR)

defaults = {
	'user': 'me',
	'query': 'from:me',
	'maxResults': 100
}

class GmailSearch:
	def __init__(self, user=defaults['user'], query=defaults['query'], maxResults=defaults['maxResults']):
		self.user = user
		self.query = query
		self.maxResults = maxResults

		self.service = self.authenticate()
		self.results = []

	def authenticate(self):
		logging.info("Beginning authentication...")
		# Set the scope we'll be using in our search; since we're only searching we only need readonly
		SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

		# Grab our stored credentials, running the OAuth flow if we don't have them already
		logging.info("Looking for local authentication information...")
		store = file.Storage('storage.json') 
		creds = store.get()
		if not creds or creds.invalid:
			if not cred:
				logging.error("Local credentials not found.")
			elif creds.invalid:
				logging.error("Local credentials not valid.")
			logging.info("Loading authentication flow...")
			flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
			creds = tools.run_flow(flow, store)

		# Create the GMAIL service object with our credentials
		GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))
		return GMAIL

	def search(self):
		logging.info(" ".join(["Beginning search for", self.query + ',', "limiting results to", str(self.maxResults), "as", self.user + '...' ]))

		response = self.service.users().messages().list(userId=self.user, maxResults=self.maxResults, q=self.query).execute()
		if 'messages' in response:
			logging.debug(" ".join(["Received", str(len(response['messages'])), "messages..."]))
			self.results.extend(response['messages'])
		else:
			logging.info("No messages received.")

		while (len(self.results) < self.maxResults) and ('nextPageToken' in response):
			logging.debug("Retrieving next page of messages")
			page_token = response['nextPageToken']
			response = self.service.users().messages().list(userId=self.user, maxResults=self.maxResults, q=self.query, pageToken=page_token).execute()
			self.results.extend(response['messages'])

		logging.info(" ".join(["Found a total of", str(len(self.results)), "messages"]))

		return self.results

	def retrieveRawMessageById(self, message_id):
		return self.service.users().messages().get(userId=self.user, id=message_id, format='raw').execute()

class GmailMessage:
	def __init__(self, rawResponse):
		for key, value in rawResponse.items():
			if (key == 'raw'):
				b64decodedRaw = base64.urlsafe_b64decode(value.encode('ASCII'))
				setattr(self, key, b64decodedRaw)
			else:
				setattr(self, key, value)

		self.parsed = email.message_from_bytes(self.raw)

		def html_filter(part): return part.get_content_type() == "text/html"
		html_parts = list(filter(html_filter, self.parsed.walk()))
		html_parts_strings = map(lambda p: p.as_string(), html_parts)

		# Turns out we also need to strip out the `quoted-printable` encoding:  https://stackoverflow.com/questions/39691628/unicode-encoding-in-email
		html_parts_quopri_strings = map(lambda p: quopri.decodestring(p).decode('utf8'), html_parts_strings)
		
		self.raw_html = '\n'.join(html_parts_quopri_strings)
		self.pretty_html = GmailMessage.prettifyHTML(self.raw_html, removeQuoted)
		self.removeQuoted = removeQuoted

	def prettifyHTML(html, removeQuoted):
		prettifiedHTML = BeautifulSoup(html, 'html.parser').prettify()
		def generate_decomposer_for_selector(selector):
			def decomposer(html):
				bs = BeautifulSoup(html)
				toDecompose = bs.select(selector)
				for node in toDecompose:
					node.decompose()
				return str(bs.prettify())
			return decomposer

		transforms = [
		lambda h: re.sub('Content-Type: .+?\n', '', h),
		lambda h: re.sub('Content-Transfer-Encoding: .+?\n', '', h),
		]

		if (removeQuoted):
			transforms.append(generate_decomposer_for_selector('.gmail_quote'))

		for transform in transforms:
			prettifiedHTML = transform(prettifiedHTML)
		
		return prettifiedHTML

	def getDictionary(self):
		d = {}
		attrsToSave = ['id', 'threadId', 'internalDate', 'labelIds', 'snippet', 'sizeEstimate', 'raw_html', 'pretty_html']
		for attr in attrsToSave:
			d[attr] = getattr(self, attr)

		return d

	def getAsJSON(self):
		return json.dumps(self.getDictionary())

	def saveAsJSON(self, filename=None):
		if (not filename):
			filename = self.id + '.json'

		with open(filename, 'w') as outfile:
			outfile.write(self.getAsJSON())


# An example of how to use this class
print(" ".join([
	"Making the search object for", defaults['query'], "as", defaults['user'], 
	"limiting the results to", str(defaults['maxResults'])]))
search = GmailSearch() # Make the search
print("Running the search...")
results = search.search() # Run it

print("Getting the actual messages by id…")
rawMessages = []
for m in results:
	print("Retrieving" + " " + m['id'])
	rawMessages.append(search.retrieveRawMessageById(m['id']))

print("Done retrieving messages.  Now Extracting the message data...")
messages = [GmailMessage(rm).getDictionary() for rm in rawMessages]

import time
current_milli_time = lambda: int(round(time.time() * 1000))

filename = 'results-' + str(current_milli_time()) + '.json'
print("Saving" + " " + filename)
with open(filename, 'w') as outfile:
	outfile.write(json.dumps(messages))