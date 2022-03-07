"""Scrapes  https://www.cfcunderwriting.com/en-gb/ by default.

Outputs a JSON representation of external resources.

Follows a link to a 'Privacy Policy' and reads the content at that page.

Outputs a word-frequency count of the visible text on that page. """

from typing import Any, Dict, List
from string import punctuation
import json
import re
import requests
import click

from requests import Response
from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement


URL = "https://www.cfcunderwriting.com/en-gb/"
PATH = "./external_resources.json"


def descendant_loads_external_resource(
    descendant: PageElement, domain: str = "cfcunderwriting.com"
) -> bool or Exception:
    """
    Return True if PageElement 'loads an external resource'. False if not.

    An element 'loads and external resource' iff:
        - it it a Tag
        - and it's not an <a> tag
        - and its attributes dict includes 'src' or 'href' as a key
        - and the value of the attribute at that key startsWith 'http'
        - and the attribute links to a different domain.

    Exceptions:
    - Raised if function is invoked with an instance of Beautiful Soup.
    """
    if isinstance(descendant, Tag):
        uri = descendant.get("src", descendant.get("href"))
        if not descendant.name == "a" and (
            (
                (
                    "src" in descendant.attrs.keys()
                    and descendant["src"].startswith("http")
                )
                or (
                    "href" in descendant.attrs.keys()
                    and descendant["href"].startswith("http")
                )
                # dns labels are at most 63 characters long
                and re.search(f"^http.{{0,1}}://\w{{0,63}}\.{domain}", uri)
                is None
            )
        ):

            return True
    elif isinstance(descendant, BeautifulSoup):
        # Just in case
        raise RuntimeError(
            "Invoked with BeautifulSoup. Try using .descendants() attribute."
        )
    else:
        return False


def enumerate_external_resources(page_soup: BeautifulSoup) -> List[str]:
    """Return a list of page elements that load external resources."""

    external_resource_elements = [
        descendant
        for descendant in page_soup.descendants
        if descendant_loads_external_resource(descendant)
    ]

    def element_to_uri(element):
        return str(element.attrs.get("href", element.attrs.get("src", "err")))

    return [element_to_uri(element) for element in external_resource_elements]


def output_to_file(output: Any, path: str) -> None:
    """Output object to file"""
    with open(path, "w+", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            default=lambda x: x.__dict__,
        )


def output_resources_to_file(
    resources: List[str],
    resource_path: str,
    url: str = URL,
) -> None:
    """Output JSON representation to file."""
    page_external_resources = {"url": url, "external_resources": resources}
    output_to_file(page_external_resources, resource_path)


def get_page_links(page_soup: BeautifulSoup) -> List[PageElement]:
    """List comprehension for anchor tag elements in BeautifulSoup"""
    return [
        descendant
        for descendant in page_soup.descendants
        if (descendant.name == "a")
    ]


def get_privacy_policy_content(
    page_links: List[PageElement],
    base_url: str = "https://www.cfcunderwriting.com/en-gb/",
) -> Response or Exception:
    """Iterate over page to find Privacy Policy url. Returns its content."""
    # built-in enumerate is available, but the link index does no work
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

    content_url = (
        possible_links[0]
        if str(possible_links[0]).startswith("http")
        else base_url + possible_links[0]
    )

    return requests.get(content_url).content


def count_words(text: str) -> Dict[str, int]:
    """Return a dictionary with words as keys, and frequencies as values."""
    counter = {}
    for word in text.split(" "):
        # if a 'word' consists only of punctuation or non-ascii chars, ignore it
        if all(char in punctuation or char.encode("ascii", "ignore") == b'' for char in word):
            continue
        # this is technically case-insensitive, but not subtle
        counter_key = word.upper()
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


@click.command()
@click.option("--url", default=URL, help="The URL")
@click.option("--path", default=PATH, help="File output path")
def main(url: str = URL, path: str = PATH):
    """Run scan an output artefacts."""
    content = requests.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    external_resources = enumerate_external_resources(soup)

    output_resources_to_file(external_resources, path)

    # soup.find_all('a', string=re.compile('privacy.+policy', 'i'))'
    # for brevity but the task says 'enumerates the links'
    links = get_page_links(soup)
    contents = get_privacy_policy_content(links)
    output_case_insensitive_word_frequency(contents)


if __name__ == "__main__":
    # TODO test branch coverage, exceptions, HTTPError handling
    # TODO handle URL & PATH intelligently
    main()
