#! /usr/bin/env python

from httplib2 import Http
from apiclient import discovery
from oauth2client import file, client, tools

import logging
logging.basicConfig(level=logging.DEBUG)


config = {
	'service': None,
	'user': 'me',
	'query': 'from:me',
	'maxResults': 1
}

def authenticate():
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

config['service'] = authenticate()

def search(query=config['query'], maxResults=config['maxResults'], user=config['user'], service=config['service']):
	logging.info(" ".join([
		"Beginning search for",
		query + ',',
		"limiting results to",
		maxResults,
		"as",
		user + '...'
		]))
	response = GMAIL.users().messages().list(userId=user, maxResults=maxResults, q=query).execute()
	return response