Motivated by a project of [miriamzisook](https://github.com/orgs/powderhouse/people/miriamzisook), this is the simplest possible example of accessing the [Gmail API](https://developers.google.com/api-client-library/python/) via Python to execute a search for messages and save sanely formatted message results.

Incredibly, this minimal example didn't seem to exist at first.  Thanks to [abhishekchhibber](https://github.com/abhishekchhibber)'s [`Gmail-Api-through-Python`](https://github.com/abhishekchhibber/Gmail-Api-through-Python/blob/master/gmail_read.py) for getting us started.

**TODO**
- [x] Support download of formatted HTML messages to JSON
- [ ] Support download of attachments as base64 encoded strings in JSON

# Installation

This script requires Python 3.  I recommend you install Python 3 with [`homebrew`](https://brew.sh/) _via_ `brew install python`.

1. Clone this repository.
2. In this directory, run `python3 -m venv ~/.virtualenvs/gmail-search-cli`.  This generates a [virtual environment](https://docs.python.org/3/library/venv.html) to simplify dependencies and installation.
3. Run `source ~/.virtualenvs/gmail-search-cli/bin/activate` to activate your virtual environment.
4. Run `pip install -r requirements.txt` to install the dependencies in your virtual environment.
5. Run Step 1 of [this, Python Quickstart from Google](https://developers.google.com/gmail/api/quickstart/python) and save the resulting `credentials.json` as `client_secret.json` in the same directory as `search-gmail.py`.  When asked, you can enter whatever project name you'd like.

# Usage

At this point, you should be able to run `python search-gmail.py` from your command line in this folder and see the example run, to wit:
```
(gmail-search-cli) ➜  gmail-search-cli git:(master) python search-gmail.py
Making the search object for from:me as me limiting the results to 10
Running the search...
Getting the actual messages by id…
Retrieving 1664b44e0bffe7ee
Retrieving 1664b2773fea4379
Retrieving 1664a5c521373d91
Retrieving 1664a5727f9c4166
Retrieving 1664a570eac78835
Retrieving 1664a4982b5fd267
Retrieving 166499385ef0920b
Retrieving 166467f85fdc07c5
Retrieving 166467e24965ec21
Retrieving 1664669971ade6e6
Done retrieving messages.  Now extracting the message data...
Saving results-1538866192052.json
```