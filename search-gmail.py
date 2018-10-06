#! /usr/bin/env python

from httplib2 import Http
from apiclient import discovery
from oauth2client import file, client, tools

import logging
logging.basicConfig(level=logging.ERROR)


config = {
	'service': None,
	'user': 'me',
	'query': 'from:me',
	'maxResults': 1
}

class GmailSearch:
	def __init__(self, user='me', query='from:me', maxResults=1):
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