#! /usr/bin/env python

from httplib2 import Http
from apiclient import discovery
from oauth2client import file, client, tools

config = {
	'user': 'me',
	'query': 'from:me',
	'maxResults': 1
}

def authenticate():
	# Set the scope we'll be using in our search; since we're only searching we only need readonly
	SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

	# Grab our stored credentials, running the OAuth flow if we don't have them already
	store = file.Storage('storage.json') 
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
		creds = tools.run_flow(flow, store)

	# Create the GMAIL service object with our credentials
	GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))
	return GMAIL

service = authenticate()