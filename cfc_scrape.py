"""Scrapes  https://www.cfcunderwriting.com/en-gb/ by default.

Outputs a JSON representation of external resources.

Follows a link to a 'Privacy Policy' and reads the content at that page.

Outputs a word-frequency count of the visible text on that page. """

from typing import Any, Dict, NamedTuple
from string import punctuation
import json
import re
import requests
from requests import Response
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, PageElement


def get_page_content(
    url: str = "https://www.cfcunderwriting.com/en-gb/",
) -> Response:
    """Uses requests to get a webpage, takes a single 'url' param."""
    page = requests.get(url)

    return page.content


def descendant_loads_external_resource(
    descendant: PageElement, domain: str = "cfcunderwriting.com"
) -> bool or Exception:
    """
    Return True if the PageElement 'loads an external resource'. Return False if not.

    Raise and Exception if function is invoked with an instance of Beautiful Soup.
    It is not implemented to handle recursion.

    An element 'loads and external resource' iff:
        - it it a Tag
        - and it's not an <a> tag
        - and its attributes dict includes 'src' or 'href' as a key
        - and the value of the attribute at that key startsWith 'http'.
    """
    if isinstance(descendant, Tag):
        uri = descendant.get("src", descendant.get("href"))
        if not descendant.name == "a" and (
            (
                "src" in descendant.attrs.keys()
                and descendant["src"].startswith("http")
            )
            or (
                "href" in descendant.attrs.keys()
                and descendant["href"].startswith("http")
            )
            and not re.search("http.{1,2}://" + f"{domain}.+", uri) is None
        ):

            return True
    elif isinstance(descendant, BeautifulSoup):
        # Just in case
        raise Exception(
            "Invoked with BeautifulSoup. Try using .descendants() attribute."
        )
    else:
        return False


def element_to_resource(
    element: Tag,
) -> PageElement:
    """Return external resource URI"""
    return (str(element.attrs.get("href", element.attrs.get("src", "error"))),)


def get_external_resources_from_elements(
    elements: list[PageElement],
) -> NamedTuple("PageResources", [("url", str), ("web_resources", list)]):
    """List external resource URIs"""
    return [element_to_resource(element)[0] for element in elements]


def enumerate_external_resources(page_soup: BeautifulSoup) -> list[str]:
    """Return a list of page elements that load external resources."""

    external_resource_elements = [
        descendant
        for descendant in page_soup.descendants
        if descendant_loads_external_resource(descendant)
    ]

    return get_external_resources_from_elements(external_resource_elements)


def output_to_file(output: Any, path: str = "./external_resources.json"):
    """Output object to file"""
    with open(path, "w+", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            default=lambda x: x.__dict__,
        )


def output_resources_to_file(
    resources: list[str],
    path: str = "./external_resources.json",
    url: str = "https://www.cfcunderwriting.com/en-gb/",
) -> None:
    """Output JSON representation to file."""
    page_external_resources = {"url": url, "external_resources": resources}
    output_to_file(page_external_resources, path)


def is_link(descendant: BeautifulSoup or Tag or NavigableString):
    """Returns True if given an anchor tag from a BeautifulSoup"""
    if descendant.name == "a":
        return True
    return False


def get_page_links(page_soup: BeautifulSoup) -> list[PageElement]:
    """List comprehension for anchor tag elements in BeautifulSoup

    We could have written a lambda expression, but chose to pass in
    a function in case it might be re-used later."""
    return [
        descendant
        for descendant in page_soup.descendants
        if (is_link(descendant))
    ]


def get_privacy_policy_content(
    page_links: list[PageElement],
    base_url: str = "https://www.cfcunderwriting.com/en-gb/",
) -> Response or Exception:
    """Iterate through page to guess a single Privacy Policy url. Returns its content."""
    # could have 'enumerated' list elements, but wouldn't have used the index from the tuple for anything
    possible_links = list(
        set(
            [
                link.attrs["href"]
                for link in page_links
                if re.search("privacy.+policy", link.text, re.I) is not None
            ]
        )
    )
    if len(possible_links) > 1:
        raise Exception(
            "we found more than 1 suitable link for the Privacy Policy"
        )
        # cast to str() not strictly necessary
    return get_page_content(
        possible_links[0]
        if str(possible_links[0]).startswith("http")
        else base_url + possible_links[0]
    )


def count_words(text: str) -> Dict[str, int]:
    """Return a dictionary with words as keys, and frequencies as values."""
    counter = {}
    for word in text.split(" "):
        # if a 'word' consists only of punctuation, ignore it
        if all(char in punctuation for char in word):
            continue
        # this is technically case-insensitive, but not subtle, words that include punctuation are not well counted
        counter_key = str(word).upper()
        # inelegant casting, open to alternative suggestions
        if counter.get(counter_key):
            counter[counter_key] += 1
        else:
            counter[counter_key] = 1
    return counter


def output_case_insensitive_word_frequency(
    page_content: Response, output_path: str = "./word_frequencies.json"
) -> None:
    """Output case-insensitive word frequency to file"""
    visible_page_text = BeautifulSoup(page_content, "html.parser").get_text(
        " ", strip=True
    )

    freq = count_words(visible_page_text)
    output_to_file(freq, output_path)


if __name__ == "__main__":
    # currently no user input, although it could be pointed at a different page
    index_page_content = get_page_content()
    index_page_soup = BeautifulSoup(index_page_content, "html.parser")
    external_resources = enumerate_external_resources(index_page_soup)
    output_resources_to_file(external_resources)
    # I would have prefered something like privacy_policy = page_soup.find_all('a', string=re.compile('privacy.+policy', 'i'))
    # for brevity but the task says 'enumerates the links' so opted for consistent code style
    links = get_page_links(index_page_soup)
    privacy_policy_content = get_privacy_policy_content(links)
    output_case_insensitive_word_frequency(privacy_policy_content)
