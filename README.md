# Installation

This script requires Python 3.  I recommend you install Python 3 with `homebrew` _via_ `brew install python`.

1. Clone this repository with `git clone TK`
2. In this directory, run `python3 -m venv ~/.virtualenvs/gmail-search-cli`.
3. Also in this directory, run `source ~/.virtualenvs/gmail-search-cli/bin/activate`
4. `pip install -r requirements.txt`
5. Run Step 1 of [this, Python Quickstart from Google](https://developers.google.com/gmail/api/quickstart/python) and save the resulting `credentials.json` as `client_secret.json` in the same directory as `search-gmail.py`.  When asked, you can enter whatever project name you'd like.