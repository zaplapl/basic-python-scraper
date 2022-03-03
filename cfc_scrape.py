from pydoc import getpager
import requests
from typing import Literal, List, Dict
from requests import Response
import json
import re
from string import punctuation
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, PageElement
from classes import PageResources, WebResource


def get_page_content(url: str = '') -> Response:
    """Uses requests to get a webpage, takes a single 'url' param

    If no url is provided, defaults to https://www.cfcunderwriting.com/en-gb/"""
    page = requests.get(url) if url else requests.get(
        'https://www.cfcunderwriting.com/en-gb/')
    return page.content


def descendant_loads_external_resource(descendant: BeautifulSoup or Tag or NavigableString) -> bool:
    """ Takes a Beautiful Soup 'descendant' object and returns T if it loads content hosted elsewhere

        Beautiful Soup uses four classes to represent a DOM tree: Tag, NavigableString, BeautifulSoup, and Comments

        For our current purposes we can ignore NavigableStrings, and comments (because they are essentially just strings)

        We also call this with object.descendants in our list comprehension so we expect that class attribute to flatten
        the arguments in the scope we return to - therefore we don't expect this to be called with BeautifulSoup instances
        in this module.

        Thus, an element 'loads and external resource' iff it it a Tag
                                                       and it's not an <a> tag
                                                       and its attributes dict includes 'src' or 'href' as a key
                                                       and the value of the attribute at that key startsWith 'http'

        Admittedly, this is not super finegrained since we should actually check that the domain is external to the
        page being scraped - but that would also be a bit odd & we're not aiming for perfection.

    """
    if isinstance(descendant, Tag):
        if not descendant.name == 'a' and (("src" in descendant.attrs.keys()
                                            and descendant['src'].startswith('http'))
                                           or ("href" in descendant.attrs.keys() and descendant['href'].startswith('http'))):
            return True
    elif isinstance(descendant, BeautifulSoup):
        # we don't expect this exception to be raised - I'm not even sure it's a necessary branch
        raise 'oh no - flatten your DOM representation, or implement me recursively'
    else:
        return False


def element_to_resource(resources: PageResources, element: PageElement, resource_type: Literal["web", "file"]) -> PageElement:
    """Takes a BeautifulSoup PageElement and appends it to an instance of the External Resources object

    The property accesses are chained during the WebResource instantiation because
    PageElements may have either an 'href' or a 'src' and we are interested in either. If
    we have neither, that is an error."""
    if resource_type == 'web':
        resources.add_web_resource(WebResource(
            str(element.get('rel', 'undefined')), str(
                element.attrs.get('href', element.attrs.get('src', 'error'))), str(element.name)))
    elif resource_type == 'file':
        resources.add_file_resource(WebResource(
            str(element.get('rel', 'undefined')), str(
                element.attrs.get('href', element.attrs.get('src', 'error'))), str(element.name)))
    else:
        raise f"Unknown resource_type: {resource_type}"


def get_external_resources_from_elements(elements: list[PageElement]) -> PageResources:
    """Instantiates PageResources and appends elements to its web_resources"""
    external_resources = PageResources(
        'https://www.cfcunderwriting.com/en-gb/')
    for element in elements:
        element_to_resource(external_resources, element, 'web')
    return external_resources


def enumerate_external_resources(page_soup: BeautifulSoup) -> PageResources:
    """Takes a BeatifulSoup object and enumerates external resources for the page it represents.

    For the purpose of this exercise we consider that resources in <a> HTML elements do not count as "externally
    loaded resoures". Since <link> attributes may link to style sheets or icons, they *are* included in the output from this function.

    Returns a JSON representation of those resources using the following schema:
    """

    external_resource_elements = [
        descendant for descendant in page_soup.descendants if descendant_loads_external_resource(descendant)]

    return get_external_resources_from_elements(
        external_resource_elements)


def output_resources_to_file(resources: PageResources or Dict[str, int], path: str = './external_resources.json') -> None:
    """Takes an object as JSON and writes it to file. Accepts optional path parameter."""
    with open(path, "w+") as f:
        # json doesn't know how to serialise many objects,
        # default lambda is invoked when object attribute
        # isn't straightforwardly serialisable (e.g. instance methods)
        json.dump(resources, f, indent=2,
                  default=lambda x: x.__dict__)


def is_link(descendant: BeautifulSoup or Tag or NavigableString):
    """Returns True if given an anchor tag from a BeautifulSoup"""
    if descendant.name == 'a':
        return True
    return False


def get_page_links(page_soup: BeautifulSoup) -> list[PageElement]:
    """List comprehension for anchor tag elements in BeautifulSoup

    We could have written a lambda expression, but chose to pass in
    a function in case it might be re-used later."""
    return [descendant for descendant in page_soup.descendants if (
        is_link(descendant))]


def get_privacy_policy_content(page_links: list[PageElement], base_url: str = "https://www.cfcunderwriting.com/en-gb/") -> Response:
    """Iterates through page links using regex matching to guess the Privacy Policy url. Returns page content"""
    # could have 'enumerated' list elements, but wouldn't have used the index from the tuple for anything
    possible_links = list(set([link.attrs['href'] for link in page_links if re.search(
        'privacy.+policy', link.text, re.I) != None]))
    if len(possible_links) > 1:
        raise 'we found more than 1 suitable link for the Privacy Policy'
        # cast to str() not strictly necessary
    return get_page_content(possible_links[0] if str(possible_links[0]).startswith('http') else base_url + possible_links[0])

# questionable type annotation


def count_words(text: str) -> Dict[str, int]:
    """Takes a space-separated block of text. Returns a dictionary with words as keys, and frequencies as values."""
    counter = {}
    for word in text.split(" "):
        # if a word consists only of punctuation, it counts as garbage
        if all(char in punctuation for char in word):
            continue
        # this is technically case-insensitive, but not subtle, words that include punctuation are not well counted
        counter_key = str(word).upper()
        print(counter_key)
        # inelegant casting, open to alternative suggestions
        if counter.get(counter_key):
            counter[counter_key] += 1
        else:
            counter[counter_key] = 1
    return counter


def output_case_insensitive_word_frequency(page_content: Response) -> None:
    visible_page_text = BeautifulSoup(
        page_content, 'html.parser').get_text(" ", strip=True)
    print(visible_page_text)
    freq = count_words(visible_page_text)
    output_resources_to_file(freq, './word_frequencies.json')


if __name__ == '__main__':
    url = input(
        "specify a url (defaults to'https://www.cfcunderwriting.com/en-gb/)':")
    page_content = get_page_content(url if url else'')
    page_soup = BeautifulSoup(page_content, 'html.parser')
    external_resources = enumerate_external_resources(page_soup)
    output_resources_to_file(external_resources)
    # I would have prefered something like privacy_policy = page_soup.find_all('a', string=re.compile('privacy.+policy', 'i'))
    # for brevity but the task says 'enumerates the links' so opted for consistent code style
    links = get_page_links(page_soup)
    privacy_policy_content = get_privacy_policy_content(links)
    output_case_insensitive_word_frequency(privacy_policy_content)
