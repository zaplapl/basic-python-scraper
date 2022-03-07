# Basic Page Scraper

This project contains a module that:

- Scrapes the index webpage hosted at `cfcunderwriting.com`
- Writes a list of all externally loaded resources (e.g. images/scripts/fonts not hosted
  on cfcunderwriting.com) to a JSON output file.
- Enumerates the page's hyperlinks and identifies the location of the "Privacy Policy"
  page
- Uses the privacy policy URL identified above and scrapes the page's content.
- Produces JSON file output of a case-insentitive word frequency count for all of the visible text on that page.

## Running instructiong

This project was written using Python version 3.6 and is designed to be forwards-compatible.

We recommend using pyenv, and include a .gitignore file for convenience.

The requirements.txt contains a list of dependencies that should be available in your environment.

The module itself is pretty straightforward, and imports other modules from well known libraries.

It is designed to be run from the command line:
'''pip install -r requirements.txt
python cfc_scrape.py'''

Although we provide --url and --path as command line arguments, these are 'edge' options that probably won't work as expected.
