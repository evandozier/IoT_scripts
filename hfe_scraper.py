#!/usr/bin/env python3
'''
hfe_scraper.py is a script collects download links from the hfe website
'''

import logging
import requests
from bs4 import BeautifulSoup, SoupStrainer
import time
import smtplib
import os


_moduleLogger = logging.getLogger(__name__)

# Globals
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'}
base_url = "https://www.hifiengine.com/manual_library/marantz"
download_link_root = "https://www.hifiengine.com/hfe_downloads/index.php"


def _parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser()

    # Setup parser.
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument(
        "--url",
        required=False,
        default="https://www.hifiengine.com/manual_library/marantz.shtml",
        help="Root url to start scraping",
    )
    inputGroup.add_argument(
        "--output", "-o",
        required=False,
        help="Output file to put links",
    )
    inputGroup.add_argument(
        "--delay",
        required=False, default=5,
        help="Period of time to wait between parsing pages (seconds).",
    )
    debugGroup = parser.add_argument_group("Debug")
    debugGroup.add_argument(
        "-v", "--verbose",
        action="count", dest="verbosity", default=0,
        help="Turn on verbose output. (Useful if you really care to see what \
                the tool is doing at all times.)"
    )
    debugGroup.add_argument(
        "-q", "--quiet",
        action="count", dest="quietness", default=0,
        help="Don't print anything to the module logger."
    )
    debugGroup.add_argument(
        "--test",
        action="store_true", default=False,
        help="Run doctests then quit."
    )

    args = parser.parse_args(argv)

    # We want to default to WARNING
    # Quiet should make us only show CRITICAL
    # Verbosity gives us granularity to control past that
    verbosity = 2 + (2 * args.quietness) - args.verbosity
    loggingLevel = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.CRITICAL,
    }.get(verbosity, None)
    if loggingLevel is None:
        parser.error("Unsupported verbosity: %r" % verbosity)

    if args.test:
        return args, loggingLevel

    return args, loggingLevel


def get_links(url, visited_links=None, download_links=None):
    if visited_links is None:
        visited_links = []
    if download_links is None:
        matches = []
    
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    #print("Print Soup\\n\\n\\n", soup)
    for link in soup.find_all('a'):
        href = link['href']
        if href and base_url in href and href not in visited_links:
            _moduleLogger.info("Parsing: %s", href)
            # Sleep so we don't hurt the website
            time.sleep(2)
            visited_links.append(href)
            visited_links, download_links = get_links(visited_links, download_links, href)
        elif download_link_root in href:
            _moduleLogger.info("Found download link: %s", href)
            download_links.append(href)

    return visited_links, download_links


def _main(argv):
    args, loggingLevel = _parse_args(argv)

    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(name)s.%(funcName)s: %(message)s'
    logging.basicConfig(level=loggingLevel, format=logFormat)

    if args.test:
        import doctest
        print(doctest.testmod())
        sys.exit(0)

    _moduleLogger.info("Checking URL: %s", args.url)

    url = args.url

    visited_links, download_links = get_links(url)
    #print(links)
    with open('download_links.log', mode='wt', encoding='utf-8') as f:
        f.write("\n".join(str(item) for item in download_links))
    with open('visited_links.log', mode='wt', encoding='utf-8') as f:
        f.write('\n'.join(str(item) for item in visited_links))

    return 0

if __name__ == "__main__":
    import sys
    retCode = _main(sys.argv[1:])
    sys.exit(retCode)
