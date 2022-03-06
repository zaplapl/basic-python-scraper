# Basic Page Scraper

This project contains a module that:

- Scrapes the index webpage hosted at `cfcunderwriting.com`
- Writes a list of _all externally loaded resources_ (e.g. images/scripts/fonts not hosted
  on cfcunderwriting.com) to a JSON output file.
- Enumerates the page's hyperlinks and identifies the location of the "Privacy Policy"
  page
- Uses the privacy policy URL identified in step 3 and scrapes the pages content.
- Produces JSON file output of a case-insentitive word frequency count for all of the visible text on that page.

## Running instructiong

This project was written using Python version 3.6 and is designed to be forwards-compatible.

We recommend using pyenv, and include a .gitignore file for convenience.

The requirements.txt contains a list of dependencies that should be available in your environment.

The module itself is pretty straightforward, and imports modules from well known libraries.

It is designed to be run from the command line. Although we prompt you to provide an alternative URL, this is an 'edge' feature that has not been tested to any great extent.
