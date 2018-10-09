#! /usr/bin/env python

# For accessing, parsing results from Gmail API
from httplib2 import Http
from apiclient import discovery
from oauth2client import file, client, tools
import base64  # For decoding responses
import email  # For parsing email messages

# For parsing and cleaning up HTML
from bs4 import BeautifulSoup
import re
import chardet
import quopri

import html2text  # For parsing HTML to Markdown

import json  # For exporting messages

import time  # For naming results files uniquely

# Setting up logging
import logging
logging.basicConfig(level=logging.ERROR)

# Configuring HTML to Markdown
html2markdown = html2text.HTML2Text()
html2markdown.body_width = 0
html2markdown.unicode_snob = True


defaults = {
    'user': 'me',
    'query': 'from:me',
    'maxResults': 10,
    'encoding': 'UTF-8'
}


def current_milli_time():
    return int(round(time.time() * 1000))


def prettyJSON(data):
    return json.dumps(data, indent=4, ensure_ascii=False)


def detectHTMLencoding(html):
    charset_re = re.search('charset="(.+?)"', html)
    charset_string = charset_re.group(1) if charset_re else None
    chardet_encoding = chardet.detect(quopri.decodestring(html))['encoding']

    if charset_string:
        return charset_string
    elif chardet_encoding:
        return chardet_encoding
    else:
        return defaults['encoding']


class GmailSearch:
    def __init__(
        self, user=defaults['user'], query=defaults['query'],
        maxResults=defaults['maxResults']
    ):
        self.user = user
        self.query = query
        self.maxResults = maxResults

        self.service = self.authenticate()  # Gmail authentication object
        self.results = []

    def authenticate(self):
        logging.info("Beginning authentication...")
        # Set the scope we'll be using in our search; since we're only
        # searching we only need readonly
        SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

        # Grab our stored credentials, running the OAuth flow if we don't have
        # them already
        logging.info("Looking for local authentication information...")
        store = file.Storage('storage.json')
        creds = store.get()
        if not creds or creds.invalid:
            if not creds:
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
        logging.info(" ".join(["Beginning search for", self.query + ',',
                               "limiting results to", str(self.maxResults),
                               "as", self.user + '...']))

        response = self.service.users().messages().list(
            userId=self.user,
            maxResults=self.maxResults,
            q=self.query).execute()

        if 'messages' in response:
            logging.info(
                " ".join([
                    "Received",
                    str(len(response['messages'])), "messages..."
                    ]))
            self.results.extend(response['messages'])
        else:
            logging.info("No messages received.")

        while (len(self.results) < self.maxResults
                and 'nextPageToken' in response):
            logging.info("Retrieving next page of messages")
            page_token = response['nextPageToken']
            response = self.service.users().messages().list(
                userId=self.user,
                maxResults=self.maxResults,
                q=self.query,
                pageToken=page_token).execute()
            self.results.extend(response['messages'])

        logging.info(
            " ".join(["Found a total of", str(len(self.results)), "messages"]))

        return self.results

    def retrieveRawMessageById(self, message_id):
        logging.info(
            "Requesting the raw message for message ID: " + message_id)
        return self.service.users().messages().get(
            userId=self.user,
            id=message_id,
            format='raw').execute()


class GmailMessage:
    def __init__(self, rawResponse, removeQuoted=True):
        # Given a raw message response, save all our data
        for key, value in rawResponse.items():
            if (key == 'raw'):
                b64decodedRaw = base64.urlsafe_b64decode(
                    value.encode('UTF-8'))  # decode the raw message data
                logging.debug(' '.join([
                        "Setting", key, "to",
                        str(b64decodedRaw)[0:100] + "..."
                        ]))
                setattr(self, key, b64decodedRaw)
            else:
                logging.debug(' '.join([
                    "Setting", key, "to", str(value)[0:100] + "..."
                    ]))
                setattr(self, key, value)

        logging.info("Parsing the email message from bytes...")
        self.parsed = email.message_from_bytes(self.raw)  # parse the email

        def is_multipart(part):  # Inline function for filtering the metadata
            return "multipart/alternative" in part['Content-Type']

        # Grab the metadata for the message (from, to, etc.)
        parsed_items = [dict(p.items()) for p in self.parsed.walk()]
        metadata = list(filter(is_multipart, parsed_items))

        # If there's no metadata
        metadata = metadata[0] if len(metadata) >= 1 else {}

        # Save the metadata in our own attributes, appending _multipart if
        # we run the risk of overwriting data pulled from the rawResponse above
        for key, value in metadata.items():
            if (hasattr(self, key)):
                log_msg = " ".join([
                    "Found pre-existing key",
                    key, "appending multipart to preserve uniqueness."
                    ])
                logging.debug(log_msg)
                key = key + "_multipart"

            logging.debug(' '.join([
                    "Setting", key, "to", str(value)[0:100] + "..."
                    ]))
            setattr(self, key, value)

        # Pull out the likely body of the message
        html_parts = list(filter(lambda p: p.get_content_type()
                                 == "text/html", self.parsed.walk()))
        html_parts_strings = map(lambda p: p.as_string(), html_parts)

        logging.info("Processing for `quoted-printable` encoding...")
        # Turns out we also need to strip out the `quoted-printable` encoding:
        # https://stackoverflow.com/questions/39691628/unicode-encoding-in-email
        html_parts_quopri_strings = map(
            lambda p: quopri.decodestring(p).decode(
                detectHTMLencoding(p),
                errors='ignore'), html_parts_strings)

        # Join the HTML parts together
        self.raw_html = '\n'.join(html_parts_quopri_strings)
        self.pretty_html = GmailMessage.prettifyHTML(
            self.raw_html, removeQuoted)  # Prettify the HTML
        self.markdown = html2markdown.handle(self.pretty_html)
        # Save whether we removed the quotes in prettifying
        self.quotesRemoved = removeQuoted

    def prettifyHTML(html, removeQuoted):
        # An array to hold functions which will transform our prettified HTML
        transforms = [
            lambda h: re.sub('Content-Type: .+?\n', '', h),
            lambda h: re.sub('Content-Transfer-Encoding: .+?\n', '', h),
            lambda h: BeautifulSoup(h, 'html.parser').prettify('UTF-8'),
        ]

        if (removeQuoted):
            # If we're going to remove the quoted sections
            def generate_decomposer_for_selector(selector):
                # Generate a function removing all nodes matching a selector
                def decomposer(html):
                    bs = BeautifulSoup(html, 'html.parser')
                    toDecompose = bs.select(selector)
                    for node in toDecompose:
                        node.decompose()
                    return str(bs.prettify())
                return decomposer

            # And add that function to our transforms list
            transforms.append(generate_decomposer_for_selector('.gmail_quote'))

        prettifiedHTML = html
        # Run all our transforms on the html
        for transform in transforms:
            prettifiedHTML = transform(prettifiedHTML)

        return prettifiedHTML

    def getDictionary(self):
        # Because we want to be able to save this object as JSON, we need to
        # export a simple dictionary (not a whole Python object)
        d = {}
        attrsToSave = [
            'Message-ID', 'In-Reply-To', 'id', 'threadId', 'internalDate',
            'labelIds', 'snippet', 'sizeEstimate', 'To', 'From', 'Subject',
            'Date', 'raw_html', 'pretty_html', 'markdown'
            ]
        for attr in attrsToSave:
            d[attr] = getattr(self, attr) if hasattr(self, attr) else None

        return d

    def getAsJSON(self):
        # Exports the JSON version of this object
        return prettyJSON(self.getDictionary())

    def save(self, filename=None):
        # Saves the JSON version of this object to a file
        if (not filename):
            filename = self.id + '.json'

        with open(filename, 'w') as outfile:
            outfile.write(self.getAsJSON())


# An example of how to use this class
print(" ".join([
    "Making the search object for", defaults['query'], "as", defaults['user'],
    "limiting the results to", str(defaults['maxResults'])]))
search = GmailSearch()  # Make the search
print("Running the search...")
results = search.search()  # Run it

print("Getting the actual messages by id...")
rawMessages = []
for m in results:
    print("Retrieving" + " " + m['id'])
    rawMessages.append(search.retrieveRawMessageById(m['id']))

print("Done retrieving messages.  Now extracting the message data...")
messages = [GmailMessage(rm).getDictionary() for rm in rawMessages]

filename = 'results-' + str(current_milli_time()) + '.json'
print("Saving" + " " + filename)
with open(filename, 'w') as outfile:
    outfile.write(prettyJSON(messages))
