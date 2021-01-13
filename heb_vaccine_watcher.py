#!/usr/bin/env python3
'''
heb_vaccine_watch.py is a script that monitors the heb vaccine website
    and looks for a key phrase (default is "We are currently out of vaccine
    allocation to schedule new appointments. Please check back."). It assumes
    that once that key phrase is no longer present, that the website has been
    updated with sign-up times and it sends an e-mail to notify.
    It requires selenium and chromedriver to be installed and for chromedriver
    to be added to PATH.
'''

import logging
import requests
from bs4 import BeautifulSoup
import time
import smtplib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import os


_moduleLogger = logging.getLogger(__name__)


def _parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser()

    # Setup parser.
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument(
        "--sender_email",
        required=True,
        help="E-mail address used to send the e-mail.",
    )
    inputGroup.add_argument(
        "--sender_email_password",
        required=True,
        help="Password for e-mail address.",
    )
    inputGroup.add_argument(
        "--recipient_email",
        required=True,
        help="Recipient e-mail address to receive the alert.",
    )
    inputGroup.add_argument(
        "--url",
        required=False, default="https://vaccine.heb.com/",
        help="URL to watch.",
    )
    inputGroup.add_argument(
        "--check_period",
        required=False, default=60,
        help="Period of time to wait between checks (seconds).",
    )
    inputGroup.add_argument(
        "--search_phrase",
        required=False, default="We are currently out of vaccine allocation to schedule new appointments. Please check back.",
        help="Key phrase to search iframe for. Pick a message that you think is important to detect absence of.",
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


def _main(argv):
    args, loggingLevel = _parse_args(argv)

    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(name)s.%(funcName)s: %(message)s'
    logging.basicConfig(level=loggingLevel, format=logFormat)

    if args.test:
        import doctest
        print(doctest.testmod())
        sys.exit(0)

    _moduleLogger.info("Checking URL: %s", args.url)    
    _moduleLogger.info("Search for keyphrase: %s", args.search_phrase)

    # Required because HEB uses some dynamic javascript to display the page, so without simulating a client, I see nothing.
    # This still doesn't work yet. I can't really see the actual information that is human-readable yet.
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1024x1400")

    # Loop on website and look for changes
    while True:
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(args.url)
        # Give page time to load
        time.sleep(5)
        main_iframe = driver.find_element_by_tag_name("iframe")
        _moduleLogger.debug(main_iframe)
        driver.switch_to_frame(main_iframe)
        source = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(source, "lxml")
        results = soup.body.find_all(string=args.search_phrase)
        _moduleLogger.debug("Results: %s", str(results))

        # Look for phrase in main iframe. Continue if found
        # For the default phrase, it's found 3 times on the page, lets alert if that count changes at all
        if len(results) > 3:
            _moduleLogger.info("Phrase found, continuing to loop")
            time.sleep(args.check_period)
            continue
        
        # If phrase not found, e-mail me
        else:

            # create an email message with just a subject line,
            msg = 'Subject: HEB COVID Vaccine Website has been updated! Go to https://vaccine.heb.com/ and sign up!'
            fromaddr = args.sender_email
            toaddrs  = [args.recipient_email]
        
            # setup the email server,
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            # add my account login name and password,
            server.login(args.sender_email, args.sender_email_password)
        
            # Print the email's contents
            _moduleLogger.info('From: ' + fromaddr)
            _moduleLogger.info('To: ' + str(toaddrs))
            _moduleLogger.info('Message: ' + msg)
        
            # send the email
            server.sendmail(fromaddr, toaddrs, msg)
            # disconnect from the server
            server.quit()
            break
        
    return 0

if __name__ == "__main__":
    import sys
    retCode = _main(sys.argv[1:])
    sys.exit(retCode)
